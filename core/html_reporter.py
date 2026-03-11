"""
내장 HTML 리포터 모듈

Allure 의존성 없이 독립적으로 동작하는 HTML 테스트 리포트 생성기입니다.
"""

import os
import json
import base64
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, field, asdict
import config


@dataclass
class StepResult:
    """테스트 스텝 결과"""
    name: str
    status: str  # passed, failed, skipped
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    screenshot: Optional[str] = None  # Base64 encoded

    @property
    def duration_ms(self) -> int:
        if self.end_time:
            return int((self.end_time - self.start_time).total_seconds() * 1000)
        return 0


@dataclass
class TestResult:
    """테스트 케이스 결과"""
    name: str
    status: str  # passed, failed, skipped, error
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    steps: List[StepResult] = field(default_factory=list)
    error_message: Optional[str] = None
    screenshot: Optional[str] = None
    parameters: Dict[str, object] = field(default_factory=dict)

    @property
    def duration_ms(self) -> int:
        if self.end_time:
            return int((self.end_time - self.start_time).total_seconds() * 1000)
        return 0

    @property
    def passed_steps(self) -> int:
        return sum(1 for s in self.steps if s.status == "passed")

    @property
    def failed_steps(self) -> int:
        return sum(1 for s in self.steps if s.status == "failed")


class HTMLReporter:
    """HTML 테스트 리포트 생성기"""

    def __init__(self, output_dir: Optional[str] = None):
        """
        초기화

        Args:
            output_dir: 리포트 출력 디렉토리 (기본: reports/)
        """
        self.output_dir = Path(output_dir) if output_dir else Path(config.PROJECT_ROOT) / "reports"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.test_results: List[TestResult] = []
        self.suite_name = "QA Auto Test"
        self.suite_start_time = datetime.now()
        self.environment: Dict[str, str] = {}
        self.metrics_html: str = ""

    def set_metrics_html(self, html: str):
        """MetricsCollector가 생성한 HTML 섹션 설정"""
        self.metrics_html = html

    def set_suite_name(self, name: str):
        """테스트 스위트 이름 설정"""
        self.suite_name = name

    def set_environment(self, env: Dict[str, str]):
        """환경 정보 설정"""
        self.environment = env

    def add_test_result(self, result: TestResult):
        """테스트 결과 추가"""
        self.test_results.append(result)

    def create_test_result(self, name: str, parameters: Optional[Dict] = None) -> TestResult:
        """새 테스트 결과 생성"""
        result = TestResult(
            name=name,
            status="running",
            parameters=parameters or {}
        )
        self.test_results.append(result)
        return result

    @staticmethod
    def encode_screenshot(screenshot_path: str) -> Optional[str]:
        """스크린샷 파일을 Base64로 인코딩"""
        try:
            with open(screenshot_path, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
        except Exception:
            return None

    @staticmethod
    def encode_screenshot_bytes(screenshot_bytes: bytes) -> str:
        """스크린샷 바이트를 Base64로 인코딩"""
        return base64.b64encode(screenshot_bytes).decode("utf-8")

    def generate_report(self, filename: str = "report.html") -> str:
        """
        HTML 리포트 생성

        Args:
            filename: 출력 파일명

        Returns:
            str: 생성된 리포트 파일 경로
        """
        report_path = self.output_dir / filename

        # 통계 계산
        total = len(self.test_results)
        passed = sum(1 for t in self.test_results if t.status == "passed")
        failed = sum(1 for t in self.test_results if t.status == "failed")
        skipped = sum(1 for t in self.test_results if t.status == "skipped")
        error = sum(1 for t in self.test_results if t.status == "error")

        total_duration = sum(t.duration_ms for t in self.test_results)
        pass_rate = (passed / total * 100) if total > 0 else 0

        # HTML 생성
        html = self._generate_html(
            total=total,
            passed=passed,
            failed=failed,
            skipped=skipped,
            error=error,
            total_duration=total_duration,
            pass_rate=pass_rate,
            metrics_html=self.metrics_html
        )

        with open(report_path, "w", encoding="utf-8") as f:
            f.write(html)

        return str(report_path)

    def _generate_html(self, **stats) -> str:
        """HTML 문자열 생성"""
        tests_html = self._generate_tests_html()
        env_html = self._generate_environment_html()

        return f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.suite_name} - Test Report</title>
    <style>
        {self._get_css()}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <header class="header">
            <h1>{self.suite_name}</h1>
            <p class="subtitle">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </header>

        <!-- Summary Cards -->
        <div class="summary-cards">
            <div class="card total">
                <div class="card-value">{stats['total']}</div>
                <div class="card-label">Total Tests</div>
            </div>
            <div class="card passed">
                <div class="card-value">{stats['passed']}</div>
                <div class="card-label">Passed</div>
            </div>
            <div class="card failed">
                <div class="card-value">{stats['failed']}</div>
                <div class="card-label">Failed</div>
            </div>
            <div class="card skipped">
                <div class="card-value">{stats['skipped']}</div>
                <div class="card-label">Skipped</div>
            </div>
            <div class="card duration">
                <div class="card-value">{self._format_duration(stats['total_duration'])}</div>
                <div class="card-label">Duration</div>
            </div>
            <div class="card rate">
                <div class="card-value">{stats['pass_rate']:.1f}%</div>
                <div class="card-label">Pass Rate</div>
            </div>
        </div>

        <!-- Progress Bar -->
        <div class="progress-container">
            <div class="progress-bar">
                <div class="progress passed" style="width: {stats['passed']/stats['total']*100 if stats['total'] > 0 else 0}%"></div>
                <div class="progress failed" style="width: {stats['failed']/stats['total']*100 if stats['total'] > 0 else 0}%"></div>
                <div class="progress skipped" style="width: {stats['skipped']/stats['total']*100 if stats['total'] > 0 else 0}%"></div>
            </div>
        </div>

        <!-- Environment Info -->
        {env_html}

        <!-- Quality Metrics Section -->
        {stats.get('metrics_html', '')}

        <!-- Test Results -->
        <section class="test-results">
            <h2>Test Results</h2>
            {tests_html}
        </section>
    </div>

    <script>
        {self._get_javascript()}
    </script>
</body>
</html>"""

    def _generate_tests_html(self) -> str:
        """테스트 결과 HTML 생성"""
        html_parts = []

        for i, test in enumerate(self.test_results):
            status_class = test.status
            status_icon = {
                "passed": "&#10004;",
                "failed": "&#10008;",
                "skipped": "&#8722;",
                "error": "&#9888;",
                "running": "&#9654;"
            }.get(test.status, "?")

            # 파라미터 표시
            params_html = ""
            if test.parameters:
                params_str = ", ".join(f"{k}={v}" for k, v in test.parameters.items())
                params_html = f'<span class="params">[{params_str}]</span>'

            # 스텝 HTML
            steps_html = self._generate_steps_html(test.steps)

            # 에러 메시지
            error_html = ""
            if test.error_message:
                error_html = f'<div class="error-message"><pre>{test.error_message}</pre></div>'

            # 스크린샷
            screenshot_html = ""
            if test.screenshot:
                screenshot_html = f'''
                <div class="screenshot">
                    <img src="data:image/png;base64,{test.screenshot}" alt="Screenshot" onclick="openModal(this.src)">
                </div>'''

            html_parts.append(f"""
            <div class="test-item {status_class}" data-test-id="{i}">
                <div class="test-header" onclick="toggleTest({i})">
                    <span class="status-icon {status_class}">{status_icon}</span>
                    <span class="test-name">{test.name}</span>
                    {params_html}
                    <span class="duration">{self._format_duration(test.duration_ms)}</span>
                    <span class="expand-icon">&#9660;</span>
                </div>
                <div class="test-content" id="test-content-{i}">
                    {steps_html}
                    {error_html}
                    {screenshot_html}
                </div>
            </div>""")

        return "\n".join(html_parts)

    def _generate_steps_html(self, steps: List[StepResult]) -> str:
        """스텝 결과 HTML 생성"""
        if not steps:
            return ""

        html_parts = ['<div class="steps">']
        for step in steps:
            status_class = step.status
            status_icon = "&#10004;" if step.status == "passed" else "&#10008;"

            error_html = ""
            if step.error_message:
                error_html = f'<div class="step-error">{step.error_message}</div>'

            screenshot_html = ""
            if step.screenshot:
                screenshot_html = f'''
                <img class="step-screenshot" src="data:image/png;base64,{step.screenshot}"
                     alt="Step Screenshot" onclick="openModal(this.src)">'''

            html_parts.append(f"""
            <div class="step {status_class}">
                <span class="step-icon {status_class}">{status_icon}</span>
                <span class="step-name">{step.name}</span>
                <span class="step-duration">{step.duration_ms}ms</span>
                {error_html}
                {screenshot_html}
            </div>""")

        html_parts.append('</div>')
        return "\n".join(html_parts)

    def _generate_environment_html(self) -> str:
        """환경 정보 HTML 생성"""
        if not self.environment:
            return ""

        rows = "\n".join(
            f"<tr><td>{k}</td><td>{v}</td></tr>"
            for k, v in self.environment.items()
        )

        return f"""
        <section class="environment">
            <h2>Environment</h2>
            <table>
                <thead><tr><th>Key</th><th>Value</th></tr></thead>
                <tbody>{rows}</tbody>
            </table>
        </section>"""

    def _format_duration(self, ms: int) -> str:
        """시간 포맷팅"""
        if ms < 1000:
            return f"{ms}ms"
        elif ms < 60000:
            return f"{ms/1000:.1f}s"
        else:
            minutes = ms // 60000
            seconds = (ms % 60000) / 1000
            return f"{minutes}m {seconds:.0f}s"

    def _get_css(self) -> str:
        """CSS 스타일"""
        return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }

        .header {
            background: linear-gradient(135deg, #2196F3, #1976D2);
            color: white;
            padding: 30px;
            text-align: center;
        }

        .header h1 {
            font-size: 2em;
            margin-bottom: 5px;
        }

        .subtitle {
            opacity: 0.8;
            font-size: 0.9em;
        }

        .summary-cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            padding: 20px;
            background: #f5f5f5;
        }

        .card {
            background: white;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }

        .card:hover {
            transform: translateY(-3px);
        }

        .card-value {
            font-size: 2em;
            font-weight: bold;
            margin-bottom: 5px;
        }

        .card-label {
            color: #666;
            font-size: 0.85em;
            text-transform: uppercase;
        }

        .card.passed .card-value { color: #4CAF50; }
        .card.failed .card-value { color: #F44336; }
        .card.skipped .card-value { color: #FF9800; }
        .card.total .card-value { color: #2196F3; }
        .card.duration .card-value { color: #9C27B0; }
        .card.rate .card-value { color: #009688; }

        .progress-container {
            padding: 0 20px 20px;
            background: #f5f5f5;
        }

        .progress-bar {
            height: 8px;
            background: #e0e0e0;
            border-radius: 4px;
            overflow: hidden;
            display: flex;
        }

        .progress {
            height: 100%;
            transition: width 0.5s ease;
        }

        .progress.passed { background: #4CAF50; }
        .progress.failed { background: #F44336; }
        .progress.skipped { background: #FF9800; }

        .environment, .test-results {
            padding: 20px;
        }

        .environment h2, .test-results h2 {
            color: #333;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e0e0e0;
        }

        .environment table {
            width: 100%;
            border-collapse: collapse;
        }

        .environment th, .environment td {
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }

        .environment th {
            background: #f5f5f5;
            font-weight: 600;
        }

        .test-item {
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            margin-bottom: 10px;
            overflow: hidden;
        }

        .test-header {
            display: flex;
            align-items: center;
            padding: 15px;
            cursor: pointer;
            background: #fafafa;
            transition: background 0.2s;
        }

        .test-header:hover {
            background: #f0f0f0;
        }

        .test-item.passed .test-header { border-left: 4px solid #4CAF50; }
        .test-item.failed .test-header { border-left: 4px solid #F44336; }
        .test-item.skipped .test-header { border-left: 4px solid #FF9800; }
        .test-item.error .test-header { border-left: 4px solid #9C27B0; }

        .status-icon {
            width: 24px;
            height: 24px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-right: 10px;
            font-size: 14px;
            color: white;
        }

        .status-icon.passed { background: #4CAF50; }
        .status-icon.failed { background: #F44336; }
        .status-icon.skipped { background: #FF9800; }
        .status-icon.error { background: #9C27B0; }

        .test-name {
            flex: 1;
            font-weight: 500;
        }

        .params {
            color: #666;
            font-size: 0.85em;
            margin-left: 10px;
        }

        .duration {
            color: #666;
            font-size: 0.85em;
            margin: 0 15px;
        }

        .expand-icon {
            color: #666;
            transition: transform 0.2s;
        }

        .test-item.expanded .expand-icon {
            transform: rotate(180deg);
        }

        .test-content {
            display: none;
            padding: 15px;
            background: white;
            border-top: 1px solid #e0e0e0;
        }

        .test-item.expanded .test-content {
            display: block;
        }

        .steps {
            margin-bottom: 15px;
        }

        .step {
            display: flex;
            align-items: flex-start;
            padding: 10px;
            border-radius: 6px;
            margin-bottom: 5px;
            background: #f9f9f9;
        }

        .step.passed { background: #E8F5E9; }
        .step.failed { background: #FFEBEE; }

        .step-icon {
            width: 20px;
            height: 20px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-right: 10px;
            font-size: 12px;
            color: white;
            flex-shrink: 0;
        }

        .step-icon.passed { background: #4CAF50; }
        .step-icon.failed { background: #F44336; }

        .step-name {
            flex: 1;
        }

        .step-duration {
            color: #666;
            font-size: 0.8em;
        }

        .step-error {
            color: #F44336;
            font-size: 0.85em;
            margin-top: 5px;
            padding: 5px;
            background: #fff;
            border-radius: 4px;
        }

        .error-message {
            background: #FFEBEE;
            border: 1px solid #FFCDD2;
            border-radius: 6px;
            padding: 15px;
            margin-bottom: 15px;
        }

        .error-message pre {
            white-space: pre-wrap;
            word-break: break-all;
            color: #C62828;
            font-size: 0.85em;
        }

        .screenshot img, .step-screenshot {
            max-width: 100%;
            border-radius: 8px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            cursor: pointer;
            transition: transform 0.2s;
        }

        .screenshot img:hover, .step-screenshot:hover {
            transform: scale(1.02);
        }

        /* Modal */
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.9);
            z-index: 1000;
            justify-content: center;
            align-items: center;
        }

        .modal.active {
            display: flex;
        }

        .modal img {
            max-width: 90%;
            max-height: 90%;
            border-radius: 8px;
        }

        .modal-close {
            position: absolute;
            top: 20px;
            right: 30px;
            color: white;
            font-size: 40px;
            cursor: pointer;
        }

        @media (max-width: 768px) {
            .summary-cards {
                grid-template-columns: repeat(2, 1fr);
            }
        }
        """

    def _get_javascript(self) -> str:
        """JavaScript 코드"""
        return """
        function toggleTest(id) {
            const item = document.querySelector(`[data-test-id="${id}"]`);
            item.classList.toggle('expanded');
        }

        // Modal functionality
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.innerHTML = '<span class="modal-close">&times;</span><img src="" alt="Screenshot">';
        document.body.appendChild(modal);

        modal.querySelector('.modal-close').onclick = function() {
            modal.classList.remove('active');
        };

        modal.onclick = function(e) {
            if (e.target === modal) {
                modal.classList.remove('active');
            }
        };

        function openModal(src) {
            modal.querySelector('img').src = src;
            modal.classList.add('active');
        }

        // Keyboard shortcut
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                modal.classList.remove('active');
            }
        });

        // Auto-expand failed tests
        document.querySelectorAll('.test-item.failed, .test-item.error').forEach(function(item) {
            item.classList.add('expanded');
        });
        """


# pytest 플러그인 연동용 헬퍼 함수
def create_pytest_reporter(output_dir: Optional[str] = None) -> HTMLReporter:
    """pytest에서 사용할 리포터 생성"""
    reporter = HTMLReporter(output_dir)
    reporter.set_environment({
        "Python": __import__("sys").version.split()[0],
        "Platform": __import__("platform").platform(),
        "Framework": "pytest"
    })
    return reporter
