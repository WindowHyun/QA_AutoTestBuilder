"""
테스트 케이스 데이터베이스 관리 모듈

SQLite 기반으로 테스트 시나리오를 저장, 검색, 분류하는 기능을 제공합니다.
컨텍스트 매니저 패턴으로 안전한 DB 연결 관리를 지원합니다.
"""

import sqlite3
import json
import os
from datetime import datetime
from contextlib import contextmanager
from typing import Optional, List, Dict, Any
from utils.logger import setup_logger

logger = setup_logger(__name__)


class TestCaseDB:
    """테스트 케이스 DB 관리 클래스"""

    def __init__(self, db_path: str = "testcases.db"):
        """
        테스트 케이스 DB 초기화

        Args:
            db_path: DB 파일 경로
        """
        self.db_path = db_path
        self._create_tables()

    @contextmanager
    def _get_connection(self):
        """
        DB 연결 컨텍스트 매니저

        안전한 연결 생성 및 해제를 보장합니다.
        트랜잭션 실패 시 자동 롤백됩니다.

        Yields:
            tuple: (connection, cursor)
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            yield conn, cursor
            conn.commit()
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            logger.error(f"DB 오류: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def _create_tables(self):
        """테이블 생성"""
        try:
            with self._get_connection() as (conn, cursor):
                # 테스트 케이스 테이블
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS test_cases (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        url TEXT NOT NULL,
                        category TEXT DEFAULT '기타',
                        tags TEXT DEFAULT '',
                        steps_json TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        last_run_at TEXT,
                        run_count INTEGER DEFAULT 0,
                        success_count INTEGER DEFAULT 0,
                        fail_count INTEGER DEFAULT 0
                    )
                """)

                # 실행 이력 테이블
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS test_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        test_case_id INTEGER NOT NULL,
                        run_at TEXT NOT NULL,
                        status TEXT NOT NULL,
                        error_message TEXT,
                        FOREIGN KEY (test_case_id) REFERENCES test_cases(id)
                    )
                """)

                # 인덱스 생성 (검색 성능 향상)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_test_cases_category
                    ON test_cases(category)
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_test_cases_updated
                    ON test_cases(updated_at DESC)
                """)

            logger.info(f"DB 초기화 완료: {self.db_path}")

        except Exception as e:
            logger.error(f"DB 초기화 실패: {e}")
            raise

    def save_test_case(self, name: str, url: str, steps: List[Dict],
                       category: str = "기타", tags: str = "") -> Optional[int]:
        """
        테스트 케이스 저장

        Args:
            name: 테스트 케이스 이름
            url: 테스트 URL
            steps: 스텝 데이터 리스트
            category: 카테고리
            tags: 태그 (쉼표 구분)

        Returns:
            int: 저장된 테스트 케이스 ID (실패 시 None)
        """
        try:
            with self._get_connection() as (conn, cursor):
                steps_json = json.dumps(steps, ensure_ascii=False)
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                cursor.execute("""
                    INSERT INTO test_cases (name, url, category, tags, steps_json, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (name, url, category, tags, steps_json, now, now))

                test_case_id = cursor.lastrowid

            logger.info(f"테스트 케이스 저장 완료: {name} (ID: {test_case_id})")
            return test_case_id

        except Exception as e:
            logger.error(f"테스트 케이스 저장 실패: {e}")
            return None

    def update_test_case(self, test_case_id: int, name: str = None, url: str = None,
                         steps: List[Dict] = None, category: str = None,
                         tags: str = None) -> bool:
        """
        테스트 케이스 수정

        Args:
            test_case_id: 테스트 케이스 ID
            name: 새 이름 (선택)
            url: 새 URL (선택)
            steps: 새 스텝 데이터 (선택)
            category: 새 카테고리 (선택)
            tags: 새 태그 (선택)

        Returns:
            bool: 성공 여부
        """
        try:
            updates = []
            params = []

            if name is not None:
                updates.append("name = ?")
                params.append(name)
            if url is not None:
                updates.append("url = ?")
                params.append(url)
            if steps is not None:
                updates.append("steps_json = ?")
                params.append(json.dumps(steps, ensure_ascii=False))
            if category is not None:
                updates.append("category = ?")
                params.append(category)
            if tags is not None:
                updates.append("tags = ?")
                params.append(tags)

            if not updates:
                logger.warning("수정할 내용이 없습니다")
                return False

            updates.append("updated_at = ?")
            params.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            params.append(test_case_id)

            query = f"UPDATE test_cases SET {', '.join(updates)} WHERE id = ?"

            with self._get_connection() as (conn, cursor):
                cursor.execute(query, params)
                if cursor.rowcount == 0:
                    logger.warning(f"테스트 케이스를 찾을 수 없음: ID {test_case_id}")
                    return False

            logger.info(f"테스트 케이스 수정 완료: ID {test_case_id}")
            return True

        except Exception as e:
            logger.error(f"테스트 케이스 수정 실패: {e}")
            return False

    def delete_test_case(self, test_case_id: int) -> bool:
        """
        테스트 케이스 삭제

        Args:
            test_case_id: 테스트 케이스 ID

        Returns:
            bool: 성공 여부
        """
        try:
            with self._get_connection() as (conn, cursor):
                # 이력 먼저 삭제 (외래 키 제약)
                cursor.execute("DELETE FROM test_history WHERE test_case_id = ?", (test_case_id,))
                cursor.execute("DELETE FROM test_cases WHERE id = ?", (test_case_id,))

                if cursor.rowcount == 0:
                    logger.warning(f"테스트 케이스를 찾을 수 없음: ID {test_case_id}")
                    return False

            logger.info(f"테스트 케이스 삭제 완료: ID {test_case_id}")
            return True

        except Exception as e:
            logger.error(f"테스트 케이스 삭제 실패: {e}")
            return False

    def get_test_case(self, test_case_id: int) -> Optional[Dict]:
        """
        테스트 케이스 조회

        Args:
            test_case_id: 테스트 케이스 ID

        Returns:
            dict: 테스트 케이스 데이터 (없으면 None)
        """
        try:
            with self._get_connection() as (conn, cursor):
                cursor.execute("SELECT * FROM test_cases WHERE id = ?", (test_case_id,))
                row = cursor.fetchone()

                if row:
                    return {
                        "id": row["id"],
                        "name": row["name"],
                        "url": row["url"],
                        "category": row["category"],
                        "tags": row["tags"],
                        "steps": json.loads(row["steps_json"]),
                        "created_at": row["created_at"],
                        "updated_at": row["updated_at"],
                        "last_run_at": row["last_run_at"],
                        "run_count": row["run_count"],
                        "success_count": row["success_count"],
                        "fail_count": row["fail_count"]
                    }
                return None

        except Exception as e:
            logger.error(f"테스트 케이스 조회 실패: {e}")
            return None

    def search_test_cases(self, keyword: str = "", category: str = "",
                          tags: str = "", limit: int = 100) -> List[Dict]:
        """
        테스트 케이스 검색

        Args:
            keyword: 검색 키워드 (이름, URL에서 검색)
            category: 카테고리 필터
            tags: 태그 필터
            limit: 최대 결과 수

        Returns:
            list: 검색 결과 리스트
        """
        try:
            query = "SELECT * FROM test_cases WHERE 1=1"
            params = []

            if keyword:
                query += " AND (name LIKE ? OR url LIKE ?)"
                params.extend([f"%{keyword}%", f"%{keyword}%"])

            if category:
                query += " AND category = ?"
                params.append(category)

            if tags:
                query += " AND tags LIKE ?"
                params.append(f"%{tags}%")

            query += " ORDER BY updated_at DESC LIMIT ?"
            params.append(limit)

            with self._get_connection() as (conn, cursor):
                cursor.execute(query, params)
                rows = cursor.fetchall()

                results = []
                for row in rows:
                    results.append({
                        "id": row["id"],
                        "name": row["name"],
                        "url": row["url"],
                        "category": row["category"],
                        "tags": row["tags"],
                        "updated_at": row["updated_at"],
                        "run_count": row["run_count"],
                        "success_count": row["success_count"],
                        "fail_count": row["fail_count"]
                    })

                return results

        except Exception as e:
            logger.error(f"테스트 케이스 검색 실패: {e}")
            return []

    def get_all_categories(self) -> List[str]:
        """
        모든 카테고리 목록 조회

        Returns:
            list: 카테고리 리스트
        """
        try:
            with self._get_connection() as (conn, cursor):
                cursor.execute("SELECT DISTINCT category FROM test_cases ORDER BY category")
                rows = cursor.fetchall()
                return [row[0] for row in rows]

        except Exception as e:
            logger.error(f"카테고리 조회 실패: {e}")
            return []

    def record_test_run(self, test_case_id: int, status: str,
                        error_message: str = None) -> bool:
        """
        테스트 실행 이력 기록

        Args:
            test_case_id: 테스트 케이스 ID
            status: 실행 결과 (success, fail)
            error_message: 에러 메시지 (선택)

        Returns:
            bool: 성공 여부
        """
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            with self._get_connection() as (conn, cursor):
                # 이력 기록
                cursor.execute("""
                    INSERT INTO test_history (test_case_id, run_at, status, error_message)
                    VALUES (?, ?, ?, ?)
                """, (test_case_id, now, status, error_message))

                # 테스트 케이스 통계 업데이트
                if status == "success":
                    cursor.execute("""
                        UPDATE test_cases
                        SET run_count = run_count + 1,
                            success_count = success_count + 1,
                            last_run_at = ?
                        WHERE id = ?
                    """, (now, test_case_id))
                else:
                    cursor.execute("""
                        UPDATE test_cases
                        SET run_count = run_count + 1,
                            fail_count = fail_count + 1,
                            last_run_at = ?
                        WHERE id = ?
                    """, (now, test_case_id))

            logger.info(f"테스트 실행 이력 기록: ID {test_case_id}, 결과: {status}")
            return True

        except Exception as e:
            logger.error(f"테스트 실행 이력 기록 실패: {e}")
            return False

    def get_test_history(self, test_case_id: int, limit: int = 10) -> List[Dict]:
        """
        테스트 실행 이력 조회

        Args:
            test_case_id: 테스트 케이스 ID
            limit: 최대 결과 수

        Returns:
            list: 실행 이력 리스트
        """
        try:
            with self._get_connection() as (conn, cursor):
                cursor.execute("""
                    SELECT * FROM test_history
                    WHERE test_case_id = ?
                    ORDER BY run_at DESC
                    LIMIT ?
                """, (test_case_id, limit))
                rows = cursor.fetchall()

                return [
                    {
                        "id": row["id"],
                        "run_at": row["run_at"],
                        "status": row["status"],
                        "error_message": row["error_message"]
                    }
                    for row in rows
                ]

        except Exception as e:
            logger.error(f"실행 이력 조회 실패: {e}")
            return []

    def get_statistics(self) -> Dict:
        """
        전체 통계 조회

        Returns:
            dict: 통계 정보
        """
        try:
            with self._get_connection() as (conn, cursor):
                cursor.execute("""
                    SELECT
                        COUNT(*) as total_cases,
                        SUM(run_count) as total_runs,
                        SUM(success_count) as total_success,
                        SUM(fail_count) as total_fail
                    FROM test_cases
                """)
                row = cursor.fetchone()

                return {
                    "total_cases": row["total_cases"] or 0,
                    "total_runs": row["total_runs"] or 0,
                    "total_success": row["total_success"] or 0,
                    "total_fail": row["total_fail"] or 0,
                    "success_rate": (
                        round(row["total_success"] / row["total_runs"] * 100, 1)
                        if row["total_runs"] else 0
                    )
                }

        except Exception as e:
            logger.error(f"통계 조회 실패: {e}")
            return {
                "total_cases": 0,
                "total_runs": 0,
                "total_success": 0,
                "total_fail": 0,
                "success_rate": 0
            }
