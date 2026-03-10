"""
Step-by-Step 실행 엔진

브라우저(Selenium WebDriver)에서 단일 스텝을 직접 실행합니다.
Playwright Inspector의 Step-by-Step 디버깅과 유사한 경험을 제공.
"""

import os
import time
from typing import Dict, Optional, Tuple
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from utils.logger import setup_logger
from utils.locator_utils import get_by_type
from core.api_tester import APITester

logger = setup_logger(__name__)

# 스크린샷 저장 디렉토리
TRACE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "trace_screenshots")


class StepResult:
    """스텝 실행 결과를 담는 객체"""

    def __init__(self, step_index: int, status: str, duration_ms: float = 0,
                 screenshot_path: str = "", error: str = ""):
        self.step_index = step_index
        self.status = status          # "passed" | "failed" | "skipped"
        self.duration_ms = duration_ms
        self.screenshot_path = screenshot_path
        self.error = error

    def to_dict(self) -> Dict:
        return {
            "step_index": self.step_index,
            "status": self.status,
            "duration_ms": self.duration_ms,
            "screenshot_path": self.screenshot_path,
            "error": self.error
        }


class SeleniumStepRunner:
    """
    단일 스텝 실행 엔진

    브라우저의 WebDriver를 사용하여 스텝을 하나씩 실행.
    각 스텝 실행 후 스크린샷을 캡처하고 결과를 반환.
    """

    def __init__(self, browser_manager):
        self.browser = browser_manager
        self._current_step = 0
        self._drag_source = None  # drag&drop용
        self._timeout = 10  # 기본 대기 시간(초)
        self._api_tester = APITester()  # API 테스트용

    @property
    def driver(self):
        return self.browser.driver

    def reset(self):
        """실행 상태 초기화"""
        self._current_step = 0
        self._drag_source = None
        # 스크린샷 디렉토리 생성
        os.makedirs(TRACE_DIR, exist_ok=True)

    def execute_step(self, step_index: int, step: Dict) -> StepResult:
        """
        단일 스텝 실행

        Args:
            step_index: 스텝 인덱스 (0-based)
            step: 스텝 데이터 {'action', 'type', 'locator', 'value', 'name', ...}

        Returns:
            StepResult
        """
        if not self.driver:
            return StepResult(step_index, "failed", error="브라우저가 열려있지 않습니다")

        action = step.get("action", "").lower()
        locator_type = step.get("type", "")
        locator_value = step.get("locator", "")
        value = step.get("value", "")
        name = step.get("name", f"Step {step_index + 1}")

        logger.info(f"[Step {step_index + 1}] {name} — action={action}")

        start_time = time.time()
        screenshot_path = ""

        try:
            # API 액션은 별도 처리
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

            # 요소가 필요 없는 액션
            if action in ("switch_default", "accept_alert", "dismiss_alert", "comment", "check_url"):
                self._execute_no_element_action(action, value)
            else:
                # 요소 찾기 (Self-Healing: fallback locators)
                el = self._find_element(step)
                if el is None:
                    raise Exception(f"요소를 찾을 수 없습니다: {locator_type}={locator_value}")

                # 액션 수행
                self._execute_action(action, el, value)

            duration = (time.time() - start_time) * 1000

            # 성공 스크린샷
            screenshot_path = self._capture_screenshot(step_index, "pass")

            logger.info(f"[Step {step_index + 1}] ✅ PASSED ({duration:.0f}ms)")
            return StepResult(step_index, "passed", duration, screenshot_path)

        except Exception as e:
            duration = (time.time() - start_time) * 1000
            error_msg = str(e)

            # 실패 스크린샷
            screenshot_path = self._capture_screenshot(step_index, "fail")

            logger.error(f"[Step {step_index + 1}] 🔴 FAILED: {error_msg}")
            return StepResult(step_index, "failed", duration, screenshot_path, error_msg)

    def execute_all(self, steps: list, callback=None):
        """
        모든 스텝 순차 실행

        Args:
            steps: 스텝 목록
            callback: 각 스텝 완료 시 호출 함수 (StepResult 전달)

        Returns:
            list[StepResult]
        """
        self.reset()
        results = []

        for i, step in enumerate(steps):
            result = self.execute_step(i, step)
            results.append(result)

            if callback:
                callback(result)

            # 실패 시 중단
            if result.status == "failed":
                # 남은 스텝은 skipped
                for j in range(i + 1, len(steps)):
                    skip = StepResult(j, "skipped")
                    results.append(skip)
                    if callback:
                        callback(skip)
                break

        return results

    # ── 내부 메서드 ──

    def _find_element(self, step: Dict):
        """
        Self-Healing 방식으로 요소 찾기
        액션에 따라 적절한 대기 조건 사용:
          click/input/press_key → element_to_be_clickable
          check_text           → visibility_of_element_located
          기타                 → presence_of_element_located
        """
        wait = WebDriverWait(self.driver, self._timeout)
        action = step.get("action", "").lower()

        # 액션에 맞는 대기 조건 선택
        if action in ("click", "input", "input_password", "press_key", "hover"):
            condition = EC.element_to_be_clickable
        elif action in ("check_text",):
            condition = EC.visibility_of_element_located
        else:
            condition = EC.presence_of_element_located

        # 네트워크 유휴 대기 (짧게)
        try:
            self.driver.execute_script("""
                return new Promise((resolve) => {
                    if (document.readyState === 'complete') resolve();
                    else window.addEventListener('load', resolve);
                });
            """)
        except Exception:
            pass

        # fallback locators 있으면 사용
        fallbacks = step.get("fallback_locators", [])
        primary = {
            "type": step.get("type", "XPATH"),
            "value": step.get("locator", "")
        }
        all_locators = [primary] + fallbacks

        last_error = None
        for loc in all_locators:
            try:
                by = get_by_type(loc["type"])
                el = wait.until(condition((by, loc["value"])))

                # 요소를 화면 안에 스크롤
                try:
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView({block: 'center'});", el
                    )
                    time.sleep(0.3)  # 애니메이션 대기
                except Exception:
                    pass

                return el
            except (TimeoutException, Exception) as e:
                last_error = e
                continue

        raise last_error or Exception("모든 로케이터 시도 실패")

    def _execute_action(self, action: str, el, value: str):
        """요소 기반 액션 수행"""
        if action == "click":
            try:
                el.click()
            except Exception:
                self.driver.execute_script("arguments[0].click();", el)

        elif action in ("input", "input_password"):
            el.clear()
            el.send_keys(value)

        elif action == "press_key":
            key = getattr(Keys, value.upper(), None)
            if key:
                el.send_keys(key)
            else:
                raise Exception(f"알 수 없는 키: {value}")

        elif action == "hover":
            ActionChains(self.driver).move_to_element(el).perform()

        elif action == "check_text":
            actual = el.text
            if value not in actual:
                raise AssertionError(f"텍스트 불일치! 기대: '{value}', 실제: '{actual}'")

        elif action == "switch_frame":
            self.driver.switch_to.frame(el)

        elif action == "drag_source":
            self._drag_source = el

        elif action == "drop_target":
            if self._drag_source:
                ActionChains(self.driver).drag_and_drop(self._drag_source, el).perform()
                self._drag_source = None
            else:
                raise Exception("드래그 시작점 미설정")

        else:
            logger.warning(f"알 수 없는 액션: {action}")

    def _execute_no_element_action(self, action: str, value: str):
        """요소 불필요 액션"""
        if action == "switch_default":
            self.driver.switch_to.default_content()

        elif action == "accept_alert":
            WebDriverWait(self.driver, 5).until(EC.alert_is_present())
            self.driver.switch_to.alert.accept()

        elif action == "dismiss_alert":
            WebDriverWait(self.driver, 5).until(EC.alert_is_present())
            self.driver.switch_to.alert.dismiss()

        elif action == "check_url":
            WebDriverWait(self.driver, self._timeout).until(
                EC.url_contains(value)
            )
            if value not in self.driver.current_url:
                raise AssertionError(f"URL 불일치! 기대: '{value}', 실제: '{self.driver.current_url}'")

        elif action == "comment":
            pass  # 주석은 무시

    def _capture_screenshot(self, step_index: int, status: str) -> str:
        """스크린샷 캡처"""
        try:
            os.makedirs(TRACE_DIR, exist_ok=True)
            filename = f"step_{step_index + 1}_{status}.png"
            filepath = os.path.join(TRACE_DIR, filename)
            self.driver.save_screenshot(filepath)
            return filepath
        except Exception as e:
            logger.warning(f"스크린샷 캡처 실패: {e}")
            return ""
