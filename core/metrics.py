"""
품질 메트릭 수집/계산 모듈

테스트 실행 결과로부터 메트릭을 계산합니다:
- 자동화 성공률
- 평균/최대/최소 실행 시간
- 실패 원인 분류
- 총 실행 시간
"""

import time
from typing import List, Dict, Optional
from collections import Counter
from utils.logger import setup_logger

logger = setup_logger(__name__)


class MetricsCollector:
    """테스트 실행 메트릭 수집기"""

    # 실패 원인 키워드 → 카테고리 매핑
    FAILURE_CATEGORIES = {
        "timeout": "Timeout",
        "timed out": "Timeout",
        "TimeoutException": "Timeout",
        "element": "Element Not Found",
        "no such element": "Element Not Found",
        "not found": "Element Not Found",
        "assert": "Assertion Failed",
        "AssertionError": "Assertion Failed",
        "AssertionError": "Assertion Failed",
        "api": "API Error",
        "connection": "Network Error",
        "refused": "Network Error",
        "url": "URL Mismatch",
    }

    def __init__(self):
        self.reset()

    def reset(self):
        """메트릭 초기화"""
        self._results = []
        self._start_time = time.time()
        self._end_time = None

    def add_result(self, step_index: int, name: str, status: str,
                   duration_ms: float, error: str = ""):
        """스텝 결과 추가"""
        self._results.append({
            "step": step_index + 1,
            "name": name,
            "status": status,
            "duration_ms": duration_ms,
            "error": error,
            "timestamp": time.time()
        })

    def finalize(self):
        """실행 완료 — 종료 시간 기록"""
        self._end_time = time.time()

    def compute(self) -> Dict:
        """
        전체 메트릭 계산

        Returns:
            dict: {
                total, passed, failed, skipped, success_rate,
                total_duration_ms, avg_duration_ms, max_duration_ms, min_duration_ms,
                failure_analysis, step_results
            }
        """
        if not self._results:
            return self._empty_metrics()

        total = len(self._results)
        passed = sum(1 for r in self._results if r["status"] == "passed")
        failed = sum(1 for r in self._results if r["status"] == "failed")
        skipped = sum(1 for r in self._results if r["status"] == "skipped")

        durations = [r["duration_ms"] for r in self._results if r["duration_ms"] > 0]
        total_dur = sum(durations) if durations else 0
        avg_dur = total_dur / len(durations) if durations else 0
        max_dur = max(durations) if durations else 0
        min_dur = min(durations) if durations else 0

        # 벽시계 시간 (wall clock)
        wall_time = (self._end_time - self._start_time) * 1000 if self._end_time else total_dur

        # 실패 원인 분석
        failure_analysis = self._analyze_failures()

        success_rate = (passed / total * 100) if total > 0 else 0

        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "success_rate": round(success_rate, 1),
            "total_duration_ms": round(total_dur, 1),
            "wall_time_ms": round(wall_time, 1),
            "avg_duration_ms": round(avg_dur, 1),
            "max_duration_ms": round(max_dur, 1),
            "min_duration_ms": round(min_dur, 1),
            "failure_analysis": failure_analysis,
            "step_results": self._results
        }

    def format_summary(self) -> str:
        """
        터미널/로그용 메트릭 요약 텍스트

        Returns:
            str: 포맷된 요약
        """
        m = self.compute()
        lines = [
            "",
            "═" * 50,
            "📊 Quality Metrics Summary",
            "═" * 50,
            f"  ✅ 성공률: {m['success_rate']}% ({m['passed']}/{m['total']})",
            f"  🔴 실패: {m['failed']}건 | ⏭ 스킵: {m['skipped']}건",
            f"  ⏱️  평균: {m['avg_duration_ms']/1000:.2f}s/스텝",
            f"  🏃 최소: {m['min_duration_ms']/1000:.2f}s | 최대: {m['max_duration_ms']/1000:.2f}s",
            f"  🕐 총 소요: {m['wall_time_ms']/1000:.1f}s",
        ]

        if m['failure_analysis']:
            lines.append("  ─── 실패 원인 분석 ───")
            for category, count in m['failure_analysis'].items():
                lines.append(f"    ❌ {category}: {count}건")

        lines.append("═" * 50)
        return "\n".join(lines)

    def format_html_section(self) -> str:
        """
        HTML 리포트용 메트릭 섹션

        Returns:
            str: HTML 코드
        """
        m = self.compute()

        # 성공률 색상
        rate_color = "#10B981" if m['success_rate'] >= 80 else (
            "#F59E0B" if m['success_rate'] >= 50 else "#EF4444"
        )

        html = f"""
        <div style="background:#1F2937; border-radius:12px; padding:20px; margin:20px 0; color:#F3F4F6;">
            <h2 style="margin:0 0 15px; color:#818CF8;">📊 Quality Metrics</h2>
            <div style="display:grid; grid-template-columns:repeat(4, 1fr); gap:15px;">
                <div style="background:#111827; border-radius:8px; padding:15px; text-align:center;">
                    <div style="font-size:28px; font-weight:bold; color:{rate_color};">{m['success_rate']}%</div>
                    <div style="font-size:12px; color:#9CA3AF;">성공률</div>
                </div>
                <div style="background:#111827; border-radius:8px; padding:15px; text-align:center;">
                    <div style="font-size:28px; font-weight:bold; color:#10B981;">{m['passed']}</div>
                    <div style="font-size:12px; color:#9CA3AF;">Passed</div>
                </div>
                <div style="background:#111827; border-radius:8px; padding:15px; text-align:center;">
                    <div style="font-size:28px; font-weight:bold; color:#EF4444;">{m['failed']}</div>
                    <div style="font-size:12px; color:#9CA3AF;">Failed</div>
                </div>
                <div style="background:#111827; border-radius:8px; padding:15px; text-align:center;">
                    <div style="font-size:28px; font-weight:bold; color:#60A5FA;">{m['avg_duration_ms']/1000:.2f}s</div>
                    <div style="font-size:12px; color:#9CA3AF;">평균 소요</div>
                </div>
            </div>
        """

        if m['failure_analysis']:
            html += '<div style="margin-top:15px;"><strong>❌ 실패 원인:</strong><br>'
            for cat, cnt in m['failure_analysis'].items():
                html += f'<span style="margin-right:15px;">{cat}: {cnt}건</span>'
            html += '</div>'

        html += '</div>'
        return html

    # ── Internal ──

    def _analyze_failures(self) -> Dict[str, int]:
        """실패 원인 카테고리 분류"""
        categories = Counter()
        for r in self._results:
            if r["status"] == "failed" and r.get("error"):
                error_lower = r["error"].lower()
                categorized = False
                for keyword, category in self.FAILURE_CATEGORIES.items():
                    if keyword.lower() in error_lower:
                        categories[category] += 1
                        categorized = True
                        break
                if not categorized:
                    categories["Other"] += 1
        return dict(categories)

    def _empty_metrics(self) -> Dict:
        return {
            "total": 0, "passed": 0, "failed": 0, "skipped": 0,
            "success_rate": 0, "total_duration_ms": 0, "wall_time_ms": 0,
            "avg_duration_ms": 0, "max_duration_ms": 0, "min_duration_ms": 0,
            "failure_analysis": {}, "step_results": []
        }
