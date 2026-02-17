"""
Pytest HTML 리포터 플러그인

pytest에서 자동으로 HTML 리포트를 생성하는 플러그인입니다.
Allure 없이도 리포트를 생성할 수 있습니다.

사용법:
    conftest.py에 다음 코드 추가:
        pytest_plugins = ["core.pytest_html_plugin"]

    또는 pytest.ini에 추가:
        addopts = -p core.pytest_html_plugin
"""

import pytest
from datetime import datetime
from typing import Dict, Optional
import platform
import sys
import traceback

from core.html_reporter import HTMLReporter, TestResult, StepResult


class HTMLReportPlugin:
    """Pytest HTML 리포트 플러그인"""

    def __init__(self, output_dir: Optional[str] = None):
        self.reporter = HTMLReporter(output_dir)
        self.current_test: Optional[TestResult] = None
        self._step_stack: list = []

    def pytest_configure(self, config):
        """pytest 설정 시 호출"""
        self.reporter.set_environment({
            "Python": sys.version.split()[0],
            "Platform": platform.platform(),
            "pytest": pytest.__version__,
            "Node": platform.node(),
        })

    def pytest_sessionstart(self, session):
        """세션 시작 시 호출"""
        self.reporter.suite_start_time = datetime.now()

    def pytest_runtest_setup(self, item):
        """테스트 셋업 시 호출"""
        # 파라미터 추출
        params = {}
        if hasattr(item, "callspec"):
            params = dict(item.callspec.params)

        self.current_test = TestResult(
            name=item.name,
            status="running",
            start_time=datetime.now(),
            parameters=params
        )
        self._step_stack = []

    def pytest_runtest_makereport(self, item, call):
        """테스트 결과 생성 시 호출"""
        if call.when == "call" and self.current_test:
            self.current_test.end_time = datetime.now()

            if call.excinfo:
                self.current_test.status = "failed"
                self.current_test.error_message = "".join(
                    traceback.format_exception(
                        call.excinfo.type,
                        call.excinfo.value,
                        call.excinfo.tb
                    )
                )
            else:
                self.current_test.status = "passed"

    def pytest_runtest_teardown(self, item, nextitem):
        """테스트 종료 시 호출"""
        if self.current_test:
            if self.current_test.status == "running":
                self.current_test.status = "passed"
            self.reporter.add_test_result(self.current_test)
            self.current_test = None

    def pytest_sessionfinish(self, session, exitstatus):
        """세션 종료 시 호출"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{timestamp}.html"
        report_path = self.reporter.generate_report(filename)
        print(f"\n\nHTML Report generated: {report_path}")

    # Step 기록 헬퍼 메서드
    def start_step(self, name: str):
        """스텝 시작"""
        if self.current_test:
            step = StepResult(name=name, status="running")
            self._step_stack.append(step)
            return step
        return None

    def end_step(self, status: str = "passed", error: Optional[str] = None,
                 screenshot: Optional[str] = None):
        """스텝 종료"""
        if self._step_stack:
            step = self._step_stack.pop()
            step.status = status
            step.end_time = datetime.now()
            step.error_message = error
            step.screenshot = screenshot

            if self.current_test:
                self.current_test.steps.append(step)
            return step
        return None

    def attach_screenshot(self, screenshot_base64: str):
        """현재 테스트에 스크린샷 첨부"""
        if self.current_test:
            self.current_test.screenshot = screenshot_base64


# 플러그인 인스턴스 (글로벌)
_plugin_instance: Optional[HTMLReportPlugin] = None


def get_reporter() -> Optional[HTMLReportPlugin]:
    """현재 리포터 인스턴스 가져오기"""
    return _plugin_instance


# Pytest 훅
def pytest_configure(config):
    """플러그인 등록"""
    global _plugin_instance

    # 기존 플러그인이 있으면 재사용
    if _plugin_instance is None:
        output_dir = config.getoption("--html-report-dir", default=None)
        _plugin_instance = HTMLReportPlugin(output_dir)

    config.pluginmanager.register(_plugin_instance, "html_report_plugin")


def pytest_addoption(parser):
    """커맨드라인 옵션 추가"""
    group = parser.getgroup("html report")
    group.addoption(
        "--html-report-dir",
        action="store",
        dest="html_report_dir",
        default=None,
        help="HTML 리포트 출력 디렉토리"
    )


# 컨텍스트 매니저 - with 문으로 스텝 기록
class step:
    """
    스텝 컨텍스트 매니저

    사용법:
        with step("로그인 버튼 클릭"):
            driver.find_element(...).click()
    """

    def __init__(self, name: str):
        self.name = name
        self.step_result = None

    def __enter__(self):
        reporter = get_reporter()
        if reporter:
            self.step_result = reporter.start_step(self.name)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        reporter = get_reporter()
        if reporter:
            if exc_type:
                reporter.end_step(
                    status="failed",
                    error=str(exc_val) if exc_val else None
                )
            else:
                reporter.end_step(status="passed")
        return False  # 예외 전파


def attach_screenshot(driver):
    """
    현재 테스트에 스크린샷 첨부

    Args:
        driver: Selenium WebDriver 인스턴스
    """
    reporter = get_reporter()
    if reporter and driver:
        try:
            screenshot_bytes = driver.get_screenshot_as_png()
            screenshot_base64 = HTMLReporter.encode_screenshot_bytes(screenshot_bytes)
            reporter.attach_screenshot(screenshot_base64)
        except Exception:
            pass
