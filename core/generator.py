"""
테스트 스크립트 생성기 모듈

Pytest + Allure 기반 테스트 스크립트를 생성합니다.
Phase 2: DDT(JSON/CSV/Excel) 지원 + Allure Report 강화
"""

import config
import os
import re
from typing import List, Dict, Optional, Set
from utils.locator_utils import get_by_string
from core.browser_config import BrowserConfig
from core.plugin_manager import PluginManager
from core.data_loader import DataLoader


class ScriptGenerator:
    """Pytest 테스트 스크립트 생성기"""

    def __init__(self):
        self.plugin_manager = PluginManager()

    # 지원하는 액션 목록
    SUPPORTED_ACTIONS = {
        "click", "input", "input_password", "check_text", "check_url",
        "press_key", "hover", "switch_frame", "switch_default",
        "accept_alert", "dismiss_alert", "drag_source", "drop_target",
        "comment"
    }

    # 값이 필요한 액션
    VALUE_REQUIRED_ACTIONS = {"input", "input_password", "check_text", "check_url", "press_key"}

    def _generate_shadow_dom_finder(self, shadow_path: List[Dict], final_locator: str, final_type: str) -> str:
        """
        Shadow DOM 요소 찾기 코드 생성

        Args:
            shadow_path: Shadow DOM 호스트 경로
            final_locator: 최종 요소 로케이터
            final_type: 최종 요소 로케이터 타입

        Returns:
            str: JavaScript 코드를 실행하는 Python 코드
        """
        js_parts = ["let root = document;"]

        for i, host in enumerate(shadow_path):
            if isinstance(host, dict):
                selector = host.get("value", "").replace("'", "\\'")
            else:
                selector = str(host).replace("'", "\\'")
            js_parts.append(f"let host{i} = root.querySelector('{selector}');")
            js_parts.append(f"if (!host{i} || !host{i}.shadowRoot) return null;")
            js_parts.append(f"root = host{i}.shadowRoot;")

        # 최종 요소 찾기
        escaped_locator = final_locator.replace("'", "\\'")
        if final_type in ["CSS", "CSS_SELECTOR"]:
            js_parts.append(f"return root.querySelector('{escaped_locator}');")
        else:
            # XPath의 경우
            js_parts.append(f"""
                let result = document.evaluate(
                    '{escaped_locator}',
                    root,
                    null,
                    XPathResult.FIRST_ORDERED_NODE_TYPE,
                    null
                );
                return result.singleNodeValue;
            """)

        js_code = "\\n".join(js_parts)
        return f'''driver.execute_script("""{js_code}""")'''

    def validate_steps(self, steps: List[Dict], excel_columns: Optional[List[str]] = None) -> List[str]:
        """
        스텝 데이터 검증

        Args:
            steps: 테스트 스텝 리스트
            excel_columns: 엑셀 컬럼 목록 (DDT 검증용)

        Returns:
            list: 경고/에러 메시지 목록
        """
        warnings = []

        for i, step in enumerate(steps):
            step_num = i + 1
            action = step.get("action", "")

            # 지원하지 않는 액션
            if action not in self.SUPPORTED_ACTIONS:
                warnings.append(f"Step {step_num}: 알 수 없는 액션 '{action}'")

            # 값 필수 액션 검증
            if action in self.VALUE_REQUIRED_ACTIONS:
                value = step.get("value", "")
                if not value and action != "press_key":
                    warnings.append(f"Step {step_num}: '{action}' 액션에 값이 필요합니다")

            # Excel 변수 검증
            if excel_columns:
                value = step.get("value", "")
                variables = re.findall(r"\{(.+?)\}", value)
                for var in variables:
                    if var not in excel_columns:
                        warnings.append(f"Step {step_num}: 변수 '{{{var}}}'가 엑셀에 없습니다")

            # 로케이터 검증
            if action not in ["check_url", "comment", "accept_alert", "dismiss_alert", "switch_default"]:
                if not step.get("locator"):
                    warnings.append(f"Step {step_num}: 로케이터가 비어있습니다")

        return warnings

    def get_used_variables(self, steps: List[Dict]) -> Set[str]:
        """스텝에서 사용된 Excel 변수 추출"""
        variables = set()
        for step in steps:
            value = step.get("value", "")
            matches = re.findall(r"\{(.+?)\}", value)
            variables.update(matches)
        return variables
    def generate(self, url, steps, is_headless=False, data_path=None,
                 browser_type="chrome", use_builtin_reporter=None,
                 excel_path=None):  # excel_path: backward compat alias
        """
        Pytest 스크립트 생성

        Args:
            url: 테스트 URL
            steps: 테스트 스텝 리스트
            is_headless: 헤드리스 모드 여부
            data_path: 데이터 파일 경로 (JSON/CSV/Excel)
            browser_type: 브라우저 종류
            use_builtin_reporter: 내장 HTML 리포터 사용 여부 (None=config 설정 따름)
            excel_path: (하위호환) data_path의 별칭

        Returns:
            str: 생성된 pytest 스크립트
        """
        # 하위호환: excel_path → data_path
        if data_path is None and excel_path is not None:
            data_path = excel_path

        # 설정값 우선순위 처리
        if use_builtin_reporter is None:
            use_builtin_reporter = config.USE_BUILTIN_REPORTER

        # 중앙화된 브라우저 설정 사용
        browser_code = BrowserConfig.generate_driver_code(browser_type, is_headless)
        browser_import = browser_code["imports"]
        browser_init = browser_code["init"]
        headless_setup = browser_code["headless"]
        browser_options = browser_code["options"]
        browser_driver = browser_code["driver"]

        data_loader_code = ""
        decorator_code = ""
        test_args = "driver"
        allure_title_decorator = ""
        
        # 리포터 관련 임포트 및 데코레이터 설정
        if use_builtin_reporter:
            reporter_import = "from core.pytest_html_plugin import step, attach_screenshot"
            feature_decorator = "" # 내장 리포터는 별도 데코레이터 없음 (플러그인이 처리)
        else:
            reporter_import = "import allure"
            feature_decorator = '@allure.feature("자동 생성된 테스트 시나리오")'

        if data_path:
            # DataLoader를 사용하여 포맷별 로더 코드 생성
            loader = DataLoader()
            data_loader_code = loader.generate_loader_code(data_path)
            decorator_code = '@pytest.mark.parametrize("row_data", get_test_data())'
            test_args = "driver, row_data"
            if not use_builtin_reporter:
                allure_title_decorator = '@allure.title("테스트 시나리오 [{row_data}]")'


        script = f'''
import pytest
{reporter_import}
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
{browser_import}
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import os
from datetime import datetime

{data_loader_code}

# [Helper] Safe String Formatter
class SafeData(dict):
    def __missing__(self, key):
        print(f"[WARN] 데이터에 변수 '{{key}}'가 없습니다. 빈 값으로 처리합니다.")
        return ""

# [Helper] Smart Wait
def wait_for_network_idle(driver, timeout=5):
    """
    스마트 대기:
    1. document.readyState == 'complete'
    2. jQuery.active == 0 (if present)
    3. No active animations
    """
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script("""
                // 1. Page Load
                if (document.readyState !== 'complete') return false;
                
                // 2. jQuery (Ajax)
                if (window.jQuery && window.jQuery.active > 0) return false;
                
                // 3. Animations (Web Animations API)
                if (document.getAnimations) {{
                    let animations = document.getAnimations();
                    for (let anim of animations) {{
                        if (anim.playState === 'running' && anim.effect.getComputedTiming().progress < 1) {{
                            return false;
                        }}
                    }}
                }}
                
                return true;
            """)
        )
    except:
        pass

# [Helper] Screenshot on failure
SCREENSHOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshots")

def take_screenshot(driver, name=None):
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{{name}}_{{timestamp}}.png" if name else f"screenshot_{{timestamp}}.png"
    filepath = os.path.join(SCREENSHOT_DIR, filename)
    try:
        driver.save_screenshot(filepath)
        print(f"[Screenshot] {{filepath}}")
    except Exception as e:
        print(f"[Screenshot Error] {{e}}")

# [Helper] Retry decorator (Self-Healing)
def retry_on_failure(max_retries={config.RETRY_COUNT}):
    def decorator(func):
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        print(f"\\n[RETRY] 테스트 실패 (시도 {{attempt+1}}/{{max_retries+1}}): {{e}}")
                        print(f"[RETRY] {{max_retries - attempt}}회 재시도 남음...")
                    else:
                        print(f"\\n[FAIL] 모든 재시도 소진 ({{max_retries+1}}회 시도): {{e}}")
            raise last_exception
        return wrapper
    return decorator


@pytest.fixture
def driver():
    {browser_init}
{headless_setup}
{browser_options}

    {browser_driver}
    driver.get("{url}")
    yield driver
    try:
        driver.quit()
    except:
        pass

{decorator_code}
{feature_decorator}
{allure_title_decorator}
@retry_on_failure(max_retries={config.RETRY_COUNT})
def test_scenario({test_args}):
    wait = WebDriverWait(driver, {config.EXPLICIT_WAIT})
    actions = ActionChains(driver)
    drag_source_el = None

    try:
'''

        for i, step in enumerate(steps):
            safe_name = step['name'].replace('"', "'")
            locator_val = step["locator"]
            action = step["action"]
            value = step["value"]

            # 유틸리티 함수 사용
            locator_type = get_by_string(step["type"])

            # 스텝 컨텍스트 매니저 코드 생성
            step_context = ""
            if use_builtin_reporter:
                if action == "comment":
                    step_context = f'        with step("💬 {safe_name}"):'
                elif action in ["accept_alert", "dismiss_alert", "switch_default", "check_url"]:
                    step_context = f'        with step("Step {i+1}: {safe_name} ({action})"):'
                else:
                    step_context = f'        with step("Step {i+1}: {safe_name}"):'
            else:
                if action == "comment":
                    step_context = f'        with allure.step("💬 {safe_name}"):'
                elif action in ["accept_alert", "dismiss_alert", "switch_default", "check_url"]:
                    step_context = f'        with allure.step("Step {i+1}: {action.upper()}"):'
                else:
                    step_context = f'        with allure.step("Step {i+1}: {action.upper()} - {safe_name}"):'

            script += f"""
{step_context}
"""
            
            if action == "comment":
                 script += "            pass\n"
                 continue


            value_expr = repr(value)
            if data_path and "{" in value and "}" in value:
                # [Stability] Safe Variable Binding (Prevent KeyError)
                # Use global SafeData class
                script += f"""            safe_value = '{value}'.format_map(SafeData(row_data))
"""
                value_expr = "safe_value"


            # Shadow DOM 요소 처리
            # Fallback Locator Logic (Self-Healing)
            primary_locator = {
                "type": step["type"],
                "value": step["locator"],
                "name": "Primary"
            }
            
            # 예비 로케이터 목록 구성
            fallback_locators = step.get("_fallback_locators", [])
            all_locators = [primary_locator] + fallback_locators
            
            # Shadow DOM은 현재 Primary만 지원 (복잡도 관리)
            shadow_path = step.get("_shadow_path", [])
            
            # [Fix] condition 변수 스코프 수정
            condition = "element_to_be_clickable" if action == "click" else "visibility_of_element_located"

            if shadow_path:
                # Shadow DOM 처리 (기존 로직 유지)
                shadow_finder = self._generate_shadow_dom_finder(shadow_path, locator_val, step["type"])
                script += f"""            # [Shadow DOM] 요소 찾기
            def find_shadow_element():
                return {shadow_finder}

            try:
                el = WebDriverWait(driver, {config.EXPLICIT_WAIT}).until(
                    lambda d: find_shadow_element()
                )
                if not el:
                    raise TimeoutException("Shadow DOM 요소를 찾을 수 없습니다")
            except TimeoutException:
                raise TimeoutException("Shadow DOM 요소 대기 타임아웃")
            except Exception as e:
                print(f"\\n[WARN] Shadow DOM 요소 찾기 실패: {{e}}")
                raise
"""
            else:
                # 일반 요소: Self-Healing 로직 적용
                script += f"""            # [Self-Healing] 요소 찾기 시도
            el = None
            last_error = None
            found_locator = None
"""
                
                # 로케이터 후보군 순회 코드 생성
                # Python 코드 내에서 리스트를 순회하는 것이 아니라, 생성된 Python 코드가 순회하도록 변경
                
                # 생성될 파이썬 코드의 로케이터 리스트 (문자열 리터럴로 변환)
                py_locators = []
                for loc in all_locators:
                    l_type = get_by_string(loc["type"]) # By.ID, By.XPATH 등
                    l_val = loc["value"]
                    l_desc = loc.get("description", loc.get("name", "Unknown"))
                    py_locators.append(f"({l_type}, '{l_val}', '{l_desc}')")
                
                py_locators_str = f"[{', '.join(py_locators)}]"

                script += f"""
            # [Smart Wait] 네트워크 유휴 상태 대기
            wait_for_network_idle(driver)

            locators_to_try = {py_locators_str}
            
            for l_type, l_val, l_desc in locators_to_try:
                try:
                    # 가시성 확보 대기 (Self-Healing 시에는 약간 더 짧게 시도 가능하지만 안전하게 유지)
                    el = wait.until(EC.{condition}((l_type, l_val)))
                    found_locator = l_desc
                    # print(f"   -> 성공: {{l_desc}}") # 디버그용
                    break
                except TimeoutException as e:
                    last_error = e
                    continue
                except Exception as e:
                    last_error = e
                    continue
            
            if not el:
                raise last_error or Exception("모든 로케이터 시도 실패")
            
            if found_locator != '{all_locators[0].get('description', 'Primary')}':
                 print(f"\\n[INFO] Self-Healing 동작: Primary 실패 -> {{found_locator}} 로 성공")
"""

            # --- 액션 로직 ---
            if action == "click":
                script += """            try:
                el.click()
            except Exception:
                driver.execute_script("arguments[0].click();", el)
"""
            elif action in ["input", "input_password"]:
                script += f"            el.clear(); el.send_keys({value_expr})\n"

            # [Level 4.5] 키보드 키 입력 (ENTER, TAB, ESC 등)
            elif action == "press_key":
                # value가 "ENTER"면 Keys.ENTER로 변환
                script += f"""            key_to_press = getattr(Keys, '{value.upper()}', None)
            if key_to_press:
                el.send_keys(key_to_press)
            else:
                print(f"[WARN] 알 수 없는 키: {value}")
"""

            # [Level 4.5] 마우스 호버 (Hover)
            elif action == "hover":
                script += "            actions.move_to_element(el).perform()\n"

            elif action == "check_text":
                script += f"""            actual = el.text
            expected = {value_expr}
            assert expected in actual, f"텍스트 불일치! (기대: {{expected}}, 실제: {{actual}})"
"""
            elif action == "check_url":
                script += f"""            wait.until(EC.url_contains({value_expr}))
            assert {value_expr} in driver.current_url
"""
            elif action == "switch_frame":
                script += "            driver.switch_to.frame(el)\n"
            elif action == "switch_default":
                script += "            driver.switch_to.default_content()\n"
            elif action == "accept_alert":
                script += "            driver.switch_to.alert.accept()\n"
            elif action == "dismiss_alert":
                script += "            driver.switch_to.alert.dismiss()\n"
            elif action == "drag_source":
                script += "            drag_source_el = el\n"
            elif action == "drop_target":
                script += """            if drag_source_el:
                actions.drag_and_drop(drag_source_el, el).perform()
            else:
                raise Exception("드래그 시작점 미설정")
"""

        # 에러 처리 코드 생성
        if use_builtin_reporter:
             script += """
    except Exception as e:
        take_screenshot(driver, "error")
        attach_screenshot(driver)
        raise e
"""
        else:
            script += """
    except Exception as e:
        take_screenshot(driver, "error")
        allure.attach(driver.get_screenshot_as_png(), name="Error_Screenshot", attachment_type=allure.attachment_type.PNG)
        raise e
"""

        # [Plugin Hook] 스크립트 생성 완료
        self.plugin_manager.hook("on_script_generated", script=script, excel_path=data_path)

        return script