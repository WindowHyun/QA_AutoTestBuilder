"""
POM (Page Object Model) Project Generator
Generates a structured test automation project with BasePage, PageObjects, and Test Scripts.

Phase 1 Redesign:
- BasePage: Explicit Wait only (no time.sleep), Self-Healing, Screenshot-on-failure
- conftest.py: Retry hook (1회 재시도), Screenshot attachment
- AutoPage: Page Object methods using BasePage common methods

Phase 2 Enhancements:
- DDT: JSON/CSV/Excel 통합 지원 (DataLoader 기반)
- Allure: 실패 시 스크린샷 자동 첨부, 단계별 설명 강화
"""

import os
import shutil
import config
from utils.locator_utils import get_by_string
from core.ci_generator import CIGenerator
from core.data_loader import DataLoader


class POMGenerator:
    def __init__(self):
        self.output_dir = "output_pom_project"
        self.ci_generator = CIGenerator()

    def generate_project(self, output_path, url, steps, data_path=None, browser_type="chrome",
                         excel_path=None):  # excel_path: backward compat alias
        """
        Generate the full POM project structure

        Args:
            output_path: 출력 디렉토리 경로
            url: 테스트 URL
            steps: 테스트 스텝 리스트
            data_path: 데이터 파일 경로 (JSON/CSV/Excel)
            browser_type: 브라우저 종류
            excel_path: (하위호환) data_path의 별칭
        """
        # 하위호환: excel_path → data_path
        if data_path is None and excel_path is not None:
            data_path = excel_path

        self.output_dir = output_path

        # 1. Create Directories
        pages_dir = os.path.join(output_path, "pages")
        tests_dir = os.path.join(output_path, "tests")
        workflow_dir = os.path.join(output_path, ".github", "workflows")

        if os.path.exists(output_path):
            shutil.rmtree(output_path)

        os.makedirs(pages_dir)
        os.makedirs(tests_dir)
        os.makedirs(workflow_dir)

        # 2. Generate BasePage (Common Logic: Explicit Wait, Self-Healing, Screenshot)
        self._write_file(os.path.join(pages_dir, "__init__.py"), "")
        self._write_file(os.path.join(pages_dir, "base_page.py"), self._generate_base_page_code())

        # 3. Generate AutoPage (The Page Object)
        self._write_file(os.path.join(pages_dir, "auto_page.py"), self._generate_auto_page_code(steps))

        # 4. Generate Test Script
        self._write_file(os.path.join(tests_dir, "__init__.py"), "")
        self._write_file(os.path.join(tests_dir, "conftest.py"), self._generate_conftest_code(browser_type))
        self._write_file(os.path.join(tests_dir, "test_scenario.py"), self._generate_test_script_code(url, steps, data_path))

        # 5. Generate CI/CD Workflow
        self._write_file(os.path.join(workflow_dir, "main.yml"), self.ci_generator.generate_github_actions(browser_type))
        self._write_file(os.path.join(output_path, "requirements.txt"), "selenium\npytest\nallure-pytest\nwebdriver-manager\npandas\nopenpyxl")

        return True, f"Project generated at: {output_path}"

    def _write_file(self, path, content):
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    def _generate_base_page_code(self):
        return f'''"""
BasePage: 모든 Page Object의 부모 클래스

기능:
- Explicit Wait 기반 요소 탐색 (time.sleep 사용하지 않음)
- Self-Healing: 다중 로케이터 Fallback
- Shadow DOM 요소 탐색
- 실패 시 자동 스크린샷 저장
"""

import os
import logging
from datetime import datetime
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, StaleElementReferenceException,
    ElementClickInterceptedException, ElementNotInteractableException
)
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

logger = logging.getLogger(__name__)


class BasePage:
    """
    모든 Page Object의 기본 클래스.
    Explicit Wait + Self-Healing + Screenshot-on-failure 패턴을 제공합니다.
    """

    SCREENSHOT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "screenshots")

    def __init__(self, driver, timeout={config.EXPLICIT_WAIT}):
        self.driver = driver
        self.timeout = timeout
        self.wait = WebDriverWait(
            driver, timeout,
            ignored_exceptions=[StaleElementReferenceException]
        )
        self.actions = ActionChains(driver)

    # ================================================================
    # 페이지 네비게이션
    # ================================================================

    def open(self, url):
        """URL로 이동 후 페이지 로드 완료 대기"""
        self.driver.get(url)
        self.wait_for_page_load()

    def wait_for_page_load(self, timeout=None):
        """document.readyState == 'complete' 대기"""
        t = timeout or self.timeout
        try:
            WebDriverWait(self.driver, t).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
        except TimeoutException:
            logger.warning("페이지 로드 대기 타임아웃")

    def wait_for_network_idle(self, timeout=5):
        """
        지능형 네트워크 유휴 대기:
        1. document.readyState == 'complete'
        2. jQuery.active == 0 (jQuery 사용 시)
        3. 실행 중인 애니메이션 없음
        """
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.execute_script("""
                    if (document.readyState !== 'complete') return false;
                    if (window.jQuery && window.jQuery.active > 0) return false;
                    if (document.getAnimations) {{
                        let animations = document.getAnimations();
                        for (let anim of animations) {{
                            if (anim.playState === 'running' &&
                                anim.effect.getComputedTiming().progress < 1) {{
                                return false;
                            }}
                        }}
                    }}
                    return true;
                """)
            )
        except TimeoutException:
            pass  # 타임아웃이어도 진행

    # ================================================================
    # 요소 탐색 (Explicit Wait + Self-Healing)
    # ================================================================

    def find_element(self, locator, fallback_locators=None, shadow_path=None,
                     condition="visibility", timeout=None):
        """
        Explicit Wait 기반 요소 탐색 (Self-Healing 지원)

        Args:
            locator: (By.TYPE, "value", "description") 튜플
            fallback_locators: 대체 로케이터 리스트
            shadow_path: Shadow DOM 경로
            condition: "visibility" | "clickable" | "presence"
            timeout: 개별 타임아웃

        Returns:
            WebElement

        Raises:
            TimeoutException: 모든 로케이터 실패 시
        """
        self.wait_for_network_idle()

        # Shadow DOM 요소는 별도 처리
        if shadow_path:
            return self._find_shadow_element(shadow_path, locator, timeout)

        all_locators = [locator] + (fallback_locators or [])
        t = timeout or self.timeout
        wait = WebDriverWait(self.driver, t, ignored_exceptions=[StaleElementReferenceException])

        # EC 조건 선택
        ec_map = {{
            "visibility": EC.visibility_of_element_located,
            "clickable": EC.element_to_be_clickable,
            "presence": EC.presence_of_element_located,
        }}
        ec_condition = ec_map.get(condition, EC.visibility_of_element_located)

        last_error = None
        primary_desc = all_locators[0][2] if len(all_locators[0]) > 2 else "Primary"

        for l_type, l_val, *rest in all_locators:
            l_desc = rest[0] if rest else "Unknown"
            try:
                el = wait.until(ec_condition((l_type, l_val)))
                if l_desc != primary_desc:
                    logger.info(f"[Self-Healing] Primary 실패 → '{{l_desc}}' 로케이터로 성공")
                return el
            except (TimeoutException, NoSuchElementException) as e:
                last_error = e
                logger.debug(f"로케이터 실패: {{l_desc}} ({{l_type}}={{l_val}})")
                continue

        # 모든 로케이터 실패
        error_msg = f"모든 로케이터 시도 실패: {{primary_desc}}"
        logger.error(error_msg)
        raise last_error or TimeoutException(error_msg)

    def _find_shadow_element(self, shadow_path, final_locator, timeout=None):
        """
        Shadow DOM 내부 요소 탐색 (Explicit Wait 기반, time.sleep 사용하지 않음)
        """
        t = timeout or self.timeout
        l_type, l_val, *rest = final_locator

        # Shadow DOM 탐색 JavaScript 생성
        js_parts = ["let root = document;"]
        for i, host in enumerate(shadow_path):
            if isinstance(host, dict):
                selector = host.get("value", "").replace("'", "\\\\'")
            else:
                selector = str(host).replace("'", "\\\\'")
            js_parts.append(f"let host{{i}} = root.querySelector('{{selector}}');")
            js_parts.append(f"if (!host{{i}} || !host{{i}}.shadowRoot) return null;")
            js_parts.append(f"root = host{{i}}.shadowRoot;")

        escaped_val = l_val.replace("'", "\\\\'")
        if l_type == By.CSS_SELECTOR:
            js_parts.append(f"return root.querySelector('{{escaped_val}}');")
        else:
            js_parts.append(f"""
                let result = document.evaluate(
                    '{{escaped_val}}', root, null,
                    XPathResult.FIRST_ORDERED_NODE_TYPE, null
                );
                return result.singleNodeValue;
            """)

        js_code = "\\n".join(js_parts)

        # Explicit Wait로 Shadow DOM 요소 대기 (time.sleep 대신)
        try:
            element = WebDriverWait(self.driver, t).until(
                lambda d: d.execute_script(js_code)
            )
            if element:
                return element
            raise NoSuchElementException("Shadow DOM 요소를 찾을 수 없습니다")
        except TimeoutException:
            raise NoSuchElementException(
                f"Shadow DOM 요소 대기 타임아웃 ({{t}}초): {{l_val}}"
            )

    # ================================================================
    # 스크린샷
    # ================================================================

    def take_screenshot(self, name=None):
        """
        스크린샷 저장

        Args:
            name: 파일명 (없으면 타임스탬프 사용)

        Returns:
            str: 저장된 파일 경로
        """
        os.makedirs(self.SCREENSHOT_DIR, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{{name}}_{{timestamp}}.png" if name else f"screenshot_{{timestamp}}.png"
        filepath = os.path.join(self.SCREENSHOT_DIR, filename)

        try:
            self.driver.save_screenshot(filepath)
            logger.info(f"스크린샷 저장: {{filepath}}")
            return filepath
        except Exception as e:
            logger.error(f"스크린샷 저장 실패: {{e}}")
            return None

    # ================================================================
    # 액션 메서드 (Explicit Wait 내장)
    # ================================================================

    def click(self, locator, fallback_locators=None, shadow_path=None):
        """클릭 (Explicit Wait + JS Fallback)"""
        el = self.find_element(locator, fallback_locators=fallback_locators,
                               shadow_path=shadow_path, condition="clickable")
        try:
            el.click()
        except (ElementClickInterceptedException, ElementNotInteractableException):
            logger.warning("일반 클릭 실패 → JavaScript 클릭으로 재시도")
            self.driver.execute_script("arguments[0].click();", el)

    def type_text(self, locator, text, fallback_locators=None, shadow_path=None):
        """텍스트 입력 (clear + send_keys)"""
        el = self.find_element(locator, fallback_locators=fallback_locators,
                               shadow_path=shadow_path, condition="visibility")
        el.clear()
        el.send_keys(text)

    def hover(self, locator, fallback_locators=None, shadow_path=None):
        """마우스 호버"""
        el = self.find_element(locator, fallback_locators=fallback_locators,
                               shadow_path=shadow_path, condition="visibility")
        self.actions.move_to_element(el).perform()

    def press_key(self, locator, key_name, fallback_locators=None, shadow_path=None):
        """키보드 키 입력"""
        el = self.find_element(locator, fallback_locators=fallback_locators,
                               shadow_path=shadow_path, condition="visibility")
        key = getattr(Keys, key_name.upper(), None)
        if key:
            el.send_keys(key)
        else:
            logger.warning(f"알 수 없는 키: {{key_name}}")

    def check_text(self, locator, expected_text, fallback_locators=None, shadow_path=None):
        """요소 텍스트 검증"""
        el = self.find_element(locator, fallback_locators=fallback_locators,
                               shadow_path=shadow_path, condition="visibility")
        actual = el.text
        assert expected_text in actual, (
            f"텍스트 불일치! 기대: '{{expected_text}}', 실제: '{{actual}}'"
        )

    def check_url(self, expected_url):
        """현재 URL 검증"""
        self.wait.until(EC.url_contains(expected_url))
        assert expected_url in self.driver.current_url, (
            f"URL 불일치! 기대: '{{expected_url}}', 실제: '{{self.driver.current_url}}'"
        )

    def switch_to_frame(self, locator, fallback_locators=None):
        """iframe 전환"""
        el = self.find_element(locator, fallback_locators=fallback_locators,
                               condition="presence")
        self.driver.switch_to.frame(el)

    def switch_to_default(self):
        """기본 프레임으로 복귀"""
        self.driver.switch_to.default_content()

    def accept_alert(self):
        """Alert 수락"""
        WebDriverWait(self.driver, self.timeout).until(EC.alert_is_present())
        self.driver.switch_to.alert.accept()

    def dismiss_alert(self):
        """Alert 취소"""
        WebDriverWait(self.driver, self.timeout).until(EC.alert_is_present())
        self.driver.switch_to.alert.dismiss()

    def drag_and_drop(self, source_locator, target_locator,
                      source_fallbacks=None, target_fallbacks=None):
        """드래그 앤 드롭"""
        source_el = self.find_element(source_locator, fallback_locators=source_fallbacks)
        target_el = self.find_element(target_locator, fallback_locators=target_fallbacks)
        self.actions.drag_and_drop(source_el, target_el).perform()
'''

    def _generate_auto_page_code(self, steps):
        methods = []
        drag_source = None

        for i, step in enumerate(steps):
            name = f"step_{i+1}_{step['action']}"
            l_type = get_by_string(step["type"])
            l_val = step["locator"]
            l_desc = step["name"].replace("'", "\\'")

            # Shadow DOM & Fallbacks
            shadow_path = step.get("_shadow_path")
            shadow_str = repr(shadow_path) if shadow_path else "None"

            fallbacks = []
            for fb in step.get("_fallback_locators", []):
                fb_type = get_by_string(fb["type"])
                fallbacks.append(f"({fb_type}, '{fb['value']}', '{fb.get('description', 'Fallback').replace(chr(39), chr(92)+chr(39))}')")
            fb_str = f"[{', '.join(fallbacks)}]" if fallbacks else "None"

            loc_tuple = f"({l_type}, '{l_val}', '{l_desc}')"

            method_code = ""
            if step["action"] == "click":
                method_code = f"""
    def {name}(self):
        # {l_desc}
        self.click({loc_tuple}, fallback_locators={fb_str}, shadow_path={shadow_str})"""

            elif step["action"] in ["input", "input_password"]:
                method_code = f"""
    def {name}(self, value):
        # {l_desc}
        self.type_text({loc_tuple}, value, fallback_locators={fb_str}, shadow_path={shadow_str})"""

            elif step["action"] == "hover":
                method_code = f"""
    def {name}(self):
        # {l_desc}
        self.hover({loc_tuple}, fallback_locators={fb_str}, shadow_path={shadow_str})"""

            elif step["action"] == "press_key":
                method_code = f"""
    def {name}(self, key_name):
        # {l_desc}
        self.press_key({loc_tuple}, key_name, fallback_locators={fb_str}, shadow_path={shadow_str})"""

            elif step["action"] == "check_text":
                method_code = f"""
    def {name}(self, expected_text):
        # {l_desc}
        self.check_text({loc_tuple}, expected_text, fallback_locators={fb_str}, shadow_path={shadow_str})"""

            elif step["action"] == "check_url":
                method_code = f"""
    def {name}(self, expected_url):
        # {l_desc}
        self.check_url(expected_url)"""

            elif step["action"] == "switch_frame":
                method_code = f"""
    def {name}(self):
        # {l_desc}
        self.switch_to_frame({loc_tuple}, fallback_locators={fb_str})"""

            elif step["action"] == "switch_default":
                method_code = f"""
    def {name}(self):
        self.switch_to_default()"""

            elif step["action"] == "accept_alert":
                method_code = f"""
    def {name}(self):
        self.accept_alert()"""

            elif step["action"] == "dismiss_alert":
                method_code = f"""
    def {name}(self):
        self.dismiss_alert()"""

            elif step["action"] == "drag_source":
                drag_source = (loc_tuple, fb_str, i+1)
                continue

            elif step["action"] == "drop_target" and drag_source:
                src_loc, src_fb, src_idx = drag_source
                method_code = f"""
    def step_{src_idx}_{i+1}_drag_drop(self):
        # Drag-Drop Step
        self.drag_and_drop({src_loc}, {loc_tuple}, source_fallbacks={src_fb}, target_fallbacks={fb_str})"""
                drag_source = None

            elif step["action"] == "comment":
                method_code = f"""
    def {name}(self):
        # 💬 {l_desc}
        pass"""

            if method_code:
                methods.append(method_code)

        return f"""
from selenium.webdriver.common.by import By
from .base_page import BasePage

class AutoPage(BasePage):
    {"".join(methods) if methods else "    pass"}
"""

    def _generate_conftest_code(self, browser_type):
        from core.browser_config import BrowserConfig
        driver_code = BrowserConfig.generate_driver_code(browser_type, headless=False)

        return f'''
import pytest
import allure
import os
import logging
from datetime import datetime
from selenium import webdriver
{driver_code['imports']}

logger = logging.getLogger(__name__)

# ================================================================
# 스크린샷 및 재시도 설정
# ================================================================
SCREENSHOT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "screenshots")
MAX_RETRIES = {config.RETRY_COUNT}


# ================================================================
# Fixture: WebDriver
# ================================================================
@pytest.fixture
def driver():
    {driver_code['init']}
    {driver_code['options']}
    {driver_code['driver']}
    yield driver
    driver.quit()


# ================================================================
# Self-Healing: 실패 시 스크린샷 + 로그 + Allure 첨부 + 자동 재시도
# ================================================================
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    테스트 실패 시:
    1. 스크린샷 자동 저장
    2. Allure 리포트에 스크린샷 자동 첨부
    3. 에러 로그 기록
    4. 재시도 여부 판단
    """
    outcome = yield
    report = outcome.get_result()

    if report.when == "call" and report.failed:
        # 스크린샷 저장 시도
        driver = item.funcargs.get("driver", None)
        if driver:
            os.makedirs(SCREENSHOT_DIR, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            test_name = item.name.replace("[", "_").replace("]", "_")
            filepath = os.path.join(SCREENSHOT_DIR, f"FAIL_{{test_name}}_{{timestamp}}.png")
            try:
                driver.save_screenshot(filepath)
                logger.error(f"[FAIL Screenshot] {{filepath}}")

                # Allure 리포트에 스크린샷 자동 첨부
                allure.attach(
                    driver.get_screenshot_as_png(),
                    name=f"Failure_{{test_name}}",
                    attachment_type=allure.attachment_type.PNG
                )
            except Exception as e:
                logger.error(f"스크린샷 저장 실패: {{e}}")

        # 에러 로그
        logger.error(f"[FAIL] {{item.name}}: {{call.excinfo.typename}} - {{call.excinfo.value}}")


def pytest_collection_modifyitems(items):
    """모든 테스트에 자동 재시도 마커 추가"""
    for item in items:
        # flaky 마커가 없으면 자동 추가
        if not item.get_closest_marker("flaky"):
            item.add_marker(pytest.mark.flaky(reruns=MAX_RETRIES, reruns_delay=1))
'''

    def _generate_test_script_code(self, url, steps, data_path):
        # Generate Test Script with DDT support (JSON/CSV/Excel)
        calls = []
        for i, step in enumerate(steps):
            name = f"step_{i+1}_{step['action']}"
            value = step.get("value", "")
            safe_step_name = step.get('name', name).replace('"', "'").replace('\\', '\\\\\\\\')

            # Allure step wrapper for each action
            step_desc = f"Step {i+1}: {step['action'].upper()} - {safe_step_name}"

            if step["action"] == "click":
                calls.append(f'        with allure.step("{step_desc}"):\n')
                calls.append(f"            page.{name}()\n")
            elif step["action"] in ["input", "input_password"]:
                val_str = f"'{value}'"
                if data_path and "{" in value:
                    val_str = f"'{value}'.format_map(SafeData(row_data))"
                calls.append(f'        with allure.step("{step_desc}"):\n')
                calls.append(f"            page.{name}({val_str})\n")
            elif step["action"] == "check_text":
                val_str = f"'{value}'"
                if data_path and "{" in value:
                    val_str = f"'{value}'.format_map(SafeData(row_data))"
                calls.append(f'        with allure.step("{step_desc}"):\n')
                calls.append(f"            page.{name}({val_str})\n")
            elif step["action"] == "check_url":
                calls.append(f'        with allure.step("{step_desc}"):\n')
                calls.append(f"            page.{name}('{value}')\n")
            elif step["action"] == "press_key":
                calls.append(f'        with allure.step("{step_desc}"):\n')
                calls.append(f"            page.{name}('{value}')\n")
            elif step["action"] == "comment":
                calls.append(f'        with allure.step("💬 {safe_step_name}"):\n')
                calls.append(f"            page.{name}()\n")
            elif step["action"] in ["hover", "switch_frame", "switch_default",
                                     "accept_alert", "dismiss_alert"]:
                calls.append(f'        with allure.step("{step_desc}"):\n')
                calls.append(f"            page.{name}()\n")

        data_loader = ""
        param_deco = ""
        test_args = "driver"
        allure_title_deco = ""

        if data_path:
            loader = DataLoader()
            data_loader_code = loader.generate_loader_code(data_path)
            test_args = "driver, row_data"

            data_loader = f"""
import sys
import os

class SafeData(dict):
    def __missing__(self, key):
        print(f"[WARN] 데이터에 변수 '{{key}}'가 없습니다. 빈 값으로 처리합니다.")
        return ""

{data_loader_code}
"""
            param_deco = '@pytest.mark.parametrize("row_data", get_test_data())'
            allure_title_deco = '@allure.title("테스트 워크플로우 [{row_data}]")'

        return f"""
import pytest
import allure
from pages.auto_page import AutoPage

{data_loader}

{param_deco}
@allure.feature("POM 자동 생성 테스트")
{allure_title_deco}
def test_workflow({test_args}):
    page = AutoPage(driver)
    page.open("{url}")

{"".join(calls) if calls else "    pass"}
"""
