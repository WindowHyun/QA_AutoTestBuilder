"""
API 테스트 모듈

REST API 호출 및 응답 검증을 지원합니다.
UI 테스트와 결합하여 Hybrid QA를 구현합니다.

지원 액션:
  api_get    — GET 요청 + 응답 검증
  api_post   — POST 요청 + 응답 검증
  api_assert — JSON 응답 필드 값 검증
"""

import json
import time
from typing import Dict, Optional, Any
from utils.logger import setup_logger

try:
    import requests
except ImportError:
    requests = None

logger = setup_logger(__name__)


class APITestResult:
    """API 테스트 결과"""

    def __init__(self, status_code: int = 0, response_body: Any = None,
                 duration_ms: float = 0, error: str = ""):
        self.status_code = status_code
        self.response_body = response_body
        self.duration_ms = duration_ms
        self.error = error
        self.passed = not bool(error)

    def to_dict(self) -> Dict:
        return {
            "status_code": self.status_code,
            "response_body": self.response_body,
            "duration_ms": self.duration_ms,
            "error": self.error,
            "passed": self.passed
        }


class APITester:
    """
    REST API 테스트 엔진

    사용 예시:
        tester = APITester()
        result = tester.get("https://api.example.com/users")
        tester.assert_field(result, "data[0].name", "John")
    """

    def __init__(self):
        if requests is None:
            logger.warning("requests 모듈 미설치. 'pip install requests' 실행 필요")
        self._session = requests.Session() if requests else None
        self._last_response = None
        self._headers = {"Content-Type": "application/json"}
        self._timeout = 30

    def set_headers(self, headers: Dict):
        """커스텀 헤더 설정"""
        self._headers.update(headers)

    def set_auth_token(self, token: str):
        """Bearer 토큰 인증 설정"""
        self._headers["Authorization"] = f"Bearer {token}"

    def get(self, url: str, params: Dict = None) -> APITestResult:
        """GET 요청"""
        return self._request("GET", url, params=params)

    def post(self, url: str, body: Any = None) -> APITestResult:
        """POST 요청"""
        return self._request("POST", url, json_body=body)

    def put(self, url: str, body: Any = None) -> APITestResult:
        """PUT 요청"""
        return self._request("PUT", url, json_body=body)

    def delete(self, url: str) -> APITestResult:
        """DELETE 요청"""
        return self._request("DELETE", url)

    def assert_status(self, result: APITestResult, expected_status: int) -> bool:
        """응답 상태 코드 검증"""
        if result.status_code != expected_status:
            raise AssertionError(
                f"API 상태 코드 불일치! 기대: {expected_status}, 실제: {result.status_code}"
            )
        return True

    def assert_field(self, result: APITestResult, field_path: str, expected_value: Any) -> bool:
        """
        JSON 응답 필드 값 검증

        Args:
            result: API 응답 결과
            field_path: 점(.) 구분 경로 또는 인덱스. 예: "data.users[0].name"
            expected_value: 기대 값
        """
        actual = self._get_nested_value(result.response_body, field_path)
        if actual is None:
            raise AssertionError(f"필드 '{field_path}'를 찾을 수 없습니다")

        if str(actual) != str(expected_value):
            raise AssertionError(
                f"API 필드 불일치! {field_path}: 기대='{expected_value}', 실제='{actual}'"
            )
        return True

    def assert_contains(self, result: APITestResult, field_path: str, substring: str) -> bool:
        """JSON 필드에 특정 문자열 포함 여부 검증"""
        actual = self._get_nested_value(result.response_body, field_path)
        if actual is None:
            raise AssertionError(f"필드 '{field_path}'를 찾을 수 없습니다")

        if substring not in str(actual):
            raise AssertionError(
                f"API 필드에 '{substring}' 미포함! {field_path}='{actual}'"
            )
        return True

    def execute_step(self, step: Dict) -> APITestResult:
        """
        스텝 데이터 기반 API 테스트 실행

        step 형식:
            action: api_get | api_post | api_put | api_delete | api_assert
            value: URL 또는 assert 표현식
            locator: POST body (JSON 문자열) 또는 assert 기대값
        """
        action = step.get("action", "").lower()
        value = step.get("value", "")
        locator = step.get("locator", "")

        if action == "api_get":
            result = self.get(value)
            logger.info(f"[API] GET {value} → {result.status_code}")
            return result

        elif action == "api_post":
            body = None
            if locator:
                try:
                    body = json.loads(locator)
                except json.JSONDecodeError:
                    body = locator
            result = self.post(value, body)
            logger.info(f"[API] POST {value} → {result.status_code}")
            return result

        elif action == "api_put":
            body = None
            if locator:
                try:
                    body = json.loads(locator)
                except json.JSONDecodeError:
                    body = locator
            result = self.put(value, body)
            return result

        elif action == "api_delete":
            result = self.delete(value)
            return result

        elif action == "api_assert":
            if not self._last_response:
                return APITestResult(error="이전 API 응답 없음")
            try:
                self.assert_field(self._last_response, value, locator)
                return APITestResult(
                    status_code=self._last_response.status_code,
                    response_body=self._last_response.response_body,
                    passed=True
                )
            except AssertionError as e:
                return APITestResult(error=str(e))

        else:
            return APITestResult(error=f"알 수 없는 API 액션: {action}")

    # ── Internal ──

    def _request(self, method: str, url: str, params: Dict = None,
                 json_body: Any = None) -> APITestResult:
        """HTTP 요청 실행"""
        if not self._session:
            return APITestResult(error="requests 모듈 미설치")

        start = time.time()
        try:
            response = self._session.request(
                method, url,
                headers=self._headers,
                params=params,
                json=json_body,
                timeout=self._timeout
            )
            duration = (time.time() - start) * 1000

            # 응답 본문 파싱
            try:
                body = response.json()
            except (json.JSONDecodeError, ValueError):
                body = response.text

            result = APITestResult(
                status_code=response.status_code,
                response_body=body,
                duration_ms=duration
            )
            self._last_response = result
            return result

        except Exception as e:
            duration = (time.time() - start) * 1000
            return APITestResult(duration_ms=duration, error=str(e))

    def _get_nested_value(self, data: Any, path: str) -> Any:
        """점(.) 구분 경로로 중첩 JSON 값 접근. 예: "data.users[0].name" """
        if data is None:
            return None

        parts = path.replace("[", ".[").split(".")
        current = data

        for part in parts:
            if not part:
                continue

            # 배열 인덱스 처리
            if part.startswith("[") and part.endswith("]"):
                try:
                    idx = int(part[1:-1])
                    if isinstance(current, (list, tuple)):
                        current = current[idx]
                    else:
                        return None
                except (ValueError, IndexError):
                    return None
            else:
                if isinstance(current, dict):
                    current = current.get(part)
                else:
                    return None

            if current is None:
                return None

        return current
