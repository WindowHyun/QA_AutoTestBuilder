"""
Playwright Step-by-Step 실행 엔진

Playwright API를 사용하여 단일 스텝을 직접 실행합니다.
"""

import os
import time
from typing import Dict
from utils.logger import setup_logger
from core.api_tester import APITester
from core.step_runner_selenium import StepResult

logger = setup_logger(__name__)

# 스크린샷 저장 디렉토리
TRACE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "trace_screenshots")


class PlaywrightStepRunner:
    """Playwright 단일 스텝 실행 엔진"""

    def __init__(self, browser_manager):
        self.browser_manager = browser_manager
        self._current_step = 0
        self._drag_source = None
        self._timeout = 10000  # ms (기본 대기 시간)
        self._api_tester = APITester()

    @property
    def driver(self):
        # Playwright의 리얼 Page 객체 반환
        return self.browser_manager.driver

    def reset(self):
        self._current_step = 0
        self._drag_source = None

    def execute_step(self, step_index: int, step: Dict):
        page = self.driver
        if not page:
            return StepResult(step_index, "failed", 0, "", "브라우저(Page)가 실행되지 않았습니다.")

        self._current_step = step_index
        action = step.get("action")
        locator_type = step.get("type")
        locator_value = step.get("locator")
        value = step.get("value", "")
        
        start_time = time.time()
        screenshot_path = ""

        try:
            # API 액션 처리
            if action.startswith("api_"):
                api_result = self._api_tester.execute_step(step)
                duration = (time.time() - start_time) * 1000
                screenshot_path = self._capture_screenshot(step_index, "pass" if api_result.passed else "fail")
                if api_result.passed:
                    logger.info(f"[Step {step_index + 1}] ✅ API PASSED ({duration:.0f}ms) — {api_result.status_code}")
                    return StepResult(step_index, "passed", duration, screenshot_path)
                else:
                    logger.error(f"[Step {step_index + 1}] 🔴 API FAILED: {api_result.error}")
                    return StepResult(step_index, "failed", duration, screenshot_path, api_result.error)

            # 요소 불필요 액션
            if action in ("switch_default", "accept_alert", "dismiss_alert", "comment", "check_url"):
                self._execute_no_element_action(page, action, value)
                duration = (time.time() - start_time) * 1000
                screenshot_path = self._capture_screenshot(step_index, "pass")
                return StepResult(step_index, "passed", duration, screenshot_path)

            # 요소 필요 액션
            locator = self._get_playwright_locator(page, locator_type, locator_value)
            
            # 하이라이트 효과 (Page.evaluate를 통해 테두리 그리기)
            try:
                locator.evaluate("el => { el.style.border = '3px solid red'; }")
                page.wait_for_timeout(300) # 애니메이션 디버깅 딜레이
            except Exception:
                pass

            self._execute_action(page, locator, action, value)

            page.wait_for_load_state("networkidle", timeout=self._timeout)

            duration = (time.time() - start_time) * 1000
            screenshot_path = self._capture_screenshot(step_index, "pass")
            logger.info(f"[Step {step_index + 1}] ✅ PASSED ({duration:.0f}ms)")
            return StepResult(step_index, "passed", duration, screenshot_path)

        except Exception as e:
            duration = (time.time() - start_time) * 1000
            screenshot_path = self._capture_screenshot(step_index, "fail")
            logger.error(f"[Step {step_index + 1}] 🔴 FAILED: {str(e)}")
            return StepResult(step_index, "failed", duration, screenshot_path, str(e))

    def execute_all(self, steps: list, callback=None):
        results = []
        self.reset()
        for i, step in enumerate(steps):
            result = self.execute_step(i, step)
            results.append(result)
            if callback:
                callback(result)
            if result.status == "failed":
                break
        return results

    def _get_playwright_locator(self, page, locator_type: str, locator_value: str):
        """Selenium locator를 Playwright locator 객체로 변환"""
        # Playwright는 기본적으로 CSS, XPath를 자동 판별하거나 명시할 수 있음
        import re
        
        # 만약 'xpath' 라면 강제로 xpath= 붙여주거나, '//' 시작이면 자동 인식
        if locator_type.lower() == "xpath":
            return page.locator(f"xpath={locator_value}")
        elif locator_type.lower() == "css":
            return page.locator(locator_value)
        elif locator_type.lower() == "id":
            return page.locator(f"#{locator_value}")
        elif locator_type.lower() == "name":
            return page.locator(f"[name='{locator_value}']")
        elif locator_type.lower() == "link text":
            return page.get_by_text(locator_value, exact=True)
        else:
            # Fallback
            return page.locator(locator_value)

    def _execute_action(self, page, locator, action: str, value: str):
        if action == "click":
            locator.click()
        elif action in ("input", "input_password"):
            locator.fill(value)
        elif action == "press_key":
            locator.press(value)
        elif action == "check_text":
            text = locator.text_content()
            if value not in text:
                raise AssertionError(f"텍스트 검증 실패: 기대값 '{value}', 실제 '{text}'")
        elif action == "hover":
            locator.hover()
        elif action == "switch_frame":
            # Playwright에서는 iframe을 frame_locator로 처리해야 하므로 약간 복잡함
            # 여기서는 기본 지원으로만 처리
            raise NotImplementedError("Playwright frame switching needs frame_locator implementation")
        elif action == "drag_source":
            self._drag_source = locator
        elif action == "drop_target":
            if self._drag_source:
                self._drag_source.drag_to(locator)
                self._drag_source = None
            else:
                raise ValueError("drag_source가 먼저 정의되어야 합니다.")
        else:
            raise ValueError(f"지원하지 않는 (또는 매핑되지 않은) 액션: {action}")

    def _execute_no_element_action(self, page, action: str, value: str):
        if action == "check_url":
            if value not in page.url:
                raise AssertionError(f"URL 검증 실패: 기대 '{value}', 실제 '{page.url}'")
        elif action == "switch_default":
            # Playwright에서는 page 단위이므로 기본 프레임 스위치는 main_frame()을 사용하는 식.
            pass
        elif action == "accept_alert":
            page.on("dialog", lambda dialog: dialog.accept())
        elif action == "dismiss_alert":
            page.on("dialog", lambda dialog: dialog.dismiss())
        elif action == "comment":
            logger.info(f"주석: {value}")
        else:
            pass

    def _capture_screenshot(self, step_index: int, status: str) -> str:
        if not self.driver:
            return ""
        try:
            os.makedirs(TRACE_DIR, exist_ok=True)
            filename = f"step_{step_index + 1}_{status}_{int(time.time() * 1000)}.png"
            filepath = os.path.join(TRACE_DIR, filename)
            self.driver.screenshot(path=filepath, full_page=True)
            return filepath
        except Exception as e:
            logger.warning(f"스크린샷 캡처 실패: {e}")
            return ""
