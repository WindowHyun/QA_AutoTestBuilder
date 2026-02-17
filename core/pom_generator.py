"""
POM (Page Object Model) Project Generator
Generates a structured test automation project with BasePage, PageObjects, and Test Scripts.
"""

import os
import shutil
import config
from utils.locator_utils import get_by_string
from core.ci_generator import CIGenerator

class POMGenerator:
    def __init__(self):
        self.output_dir = "output_pom_project"
        self.ci_generator = CIGenerator()

    def generate_project(self, output_path, url, steps, excel_path=None, browser_type="chrome"):
        """
        Generate the full POM project structure
        """
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
        
        # 2. Generate BasePage (Common Logic: Smart Wait, Self-Healing)
        self._write_file(os.path.join(pages_dir, "__init__.py"), "")
        self._write_file(os.path.join(pages_dir, "base_page.py"), self._generate_base_page_code())
        
        # 3. Generate AutoPage (The Page Object)
        self._write_file(os.path.join(pages_dir, "auto_page.py"), self._generate_auto_page_code(steps))
        
        # 4. Generate Test Script
        self._write_file(os.path.join(tests_dir, "__init__.py"), "")
        self._write_file(os.path.join(tests_dir, "conftest.py"), self._generate_conftest_code(browser_type))
        self._write_file(os.path.join(tests_dir, "test_scenario.py"), self._generate_test_script_code(url, steps, excel_path))
        
        # 5. Generate CI/CD Workflow
        self._write_file(os.path.join(workflow_dir, "main.yml"), self.ci_generator.generate_github_actions(browser_type))
        self._write_file(os.path.join(output_path, "requirements.txt"), "selenium\npytest\nallure-pytest\nwebdriver-manager\npandas\nopenpyxl")
        
        return True, f"Project generated at: {output_path}"

    def _write_file(self, path, content):
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    def _generate_base_page_code(self):
        return f"""
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
import time

class BasePage:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, {config.EXPLICIT_WAIT})
        self.actions = ActionChains(driver)

    def open(self, url):
        self.driver.get(url)

    def wait_for_network_idle(self, timeout=5):
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.execute_script('''
                if (document.readyState !== 'complete') return false;
                if (window.jQuery && window.jQuery.active > 0) return false;
                if (document.getAnimations) {{
                    let animations = document.getAnimations();
                    for (let anim of animations) {{
                        if (anim.playState === 'running' && anim.effect.getComputedTiming().progress < 1) {{
                            return false;
                        }}
                    }}
                }}
                return true;
                ''')
            )
        except:
            pass

    def find_element(self, locator, timeout={config.EXPLICIT_WAIT}, fallback_locators=None, shadow_path=None):
        \"\"\"
        Find element with Self-Healing and Shadow DOM capabilities
        \"\"\"
        self.wait_for_network_idle()
        
        if shadow_path:
            return self._find_shadow_element(shadow_path, locator)

        all_locators = [locator] + (fallback_locators or [])
        
        last_error = None
        for l_type, l_val, l_desc in all_locators:
            try:
                el = self.wait.until(EC.presence_of_element_located((l_type, l_val)))
                return el
            except Exception as e:
                last_error = e
                continue
                
        raise last_error or NoSuchElementException(f"Element not found: {{locator}}")

    def _find_shadow_element(self, shadow_path, final_locator):
        js_parts = ["let root = document;"]
        for i, host in enumerate(shadow_path):
            selector = host.get("value", "").replace("'", "\\\\'")
            js_parts.append(f"let host{i} = root.querySelector('{{selector}}');")
            js_parts.append(f"if (!host{i} || !host{i}.shadowRoot) return null;")
            js_parts.append(f"root = host{i}.shadowRoot;")
        
        l_type, l_val, _ = final_locator
        escaped_val = l_val.replace("'", "\\\\'")
        if l_type == By.CSS_SELECTOR:
            js_parts.append(f"return root.querySelector('{{escaped_val}}');")
        else:
            js_parts.append(f\"\"\"
                let result = document.evaluate('{{escaped_val}}', root, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null);
                return result.singleNodeValue;
            \"\"\")
        
        js_code = "\\n".join(js_parts)
        for _ in range(int({config.EXPLICIT_WAIT})):
            el = self.driver.execute_script(js_code)
            if el: return el
            time.sleep(1)
        raise NoSuchElementException(f"Shadow DOM element not found: {{final_locator}}")

    def click(self, locator, fallback_locators=None, shadow_path=None):
        el = self.find_element(locator, fallback_locators=fallback_locators, shadow_path=shadow_path)
        try:
            self.wait.until(EC.element_to_be_clickable(el)).click()
        except:
            self.driver.execute_script("arguments[0].click();", el)

    def type(self, locator, text, fallback_locators=None, shadow_path=None):
        el = self.find_element(locator, fallback_locators=fallback_locators, shadow_path=shadow_path)
        el.clear()
        el.send_keys(text)

    def hover(self, locator, fallback_locators=None, shadow_path=None):
        el = self.find_element(locator, fallback_locators=fallback_locators, shadow_path=shadow_path)
        self.actions.move_to_element(el).perform()

    def press_key(self, locator, key_name, fallback_locators=None, shadow_path=None):
        from selenium.webdriver.common.keys import Keys
        el = self.find_element(locator, fallback_locators=fallback_locators, shadow_path=shadow_path)
        key = getattr(Keys, key_name.upper(), None)
        if key: el.send_keys(key)

    def switch_to_frame(self, locator, fallback_locators=None):
        el = self.find_element(locator, fallback_locators=fallback_locators)
        self.driver.switch_to.frame(el)

    def drag_and_drop(self, source_locator, target_locator, source_fallbacks=None, target_fallbacks=None):
        source_el = self.find_element(source_locator, fallback_locators=source_fallbacks)
        target_el = self.find_element(target_locator, fallback_locators=target_fallbacks)
        self.actions.drag_and_drop(source_el, target_el).perform()
"""

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
        self.type({loc_tuple}, value, fallback_locators={fb_str}, shadow_path={shadow_str})"""

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
        el = self.find_element({loc_tuple}, fallback_locators={fb_str}, shadow_path={shadow_str})
        assert expected_text in el.text, f"Text mismatch: {{expected_text}} not in {{el.text}}" """

            elif step["action"] == "switch_frame":
                method_code = f"""
    def {name}(self):
        # {l_desc}
        self.switch_to_frame({loc_tuple}, fallback_locators={fb_str})"""

            elif step["action"] == "drag_source":
                drag_source = (loc_tuple, fb_str, i+1)
                continue # No method yet, wait for target

            elif step["action"] == "drop_target" and drag_source:
                src_loc, src_fb, src_idx = drag_source
                method_code = f"""
    def step_{src_idx}_{i+1}_drag_drop(self):
        # Drag-Drop Step
        self.drag_and_drop({src_loc}, {loc_tuple}, source_fallbacks={src_fb}, target_fallbacks={fb_str})"""
                drag_source = None

            if method_code:
                methods.append(method_code)

        return f"""
from selenium.webdriver.common.by import By
from .base_page import BasePage

class AutoPage(BasePage):
    {"".join(methods)}
"""

    def _generate_conftest_code(self, browser_type):
        from core.browser_config import BrowserConfig
        driver_code = BrowserConfig.generate_driver_code(browser_type, headless=False)
        
        return f"""
import pytest
import allure
from selenium import webdriver
{driver_code['imports']}

@pytest.fixture
def driver():
    {driver_code['init']}
    {driver_code['options']}
    {driver_code['driver']}
    yield driver
    driver.quit()
"""

    def _generate_test_script_code(self, url, steps, excel_path):
        # Generate Test Script with full Excel support
        calls = []
        for i, step in enumerate(steps):
            name = f"step_{i+1}_{step['action']}"
            value = step.get("value", "")
            
            if step["action"] == "click":
                calls.append(f"        page.{name}()\n")
            elif step["action"] in ["input", "input_password", "check_text"]:
                 # Handle Excel binding
                 val_str = f"'{value}'"
                 if excel_path and "{" in value:
                     val_str = f"'{value}'.format_map(SafeData(row_data))"
                 calls.append(f"        page.{name}({val_str})\n")

        data_loader = ""
        param_deco = ""
        test_args = "driver"
        
        if excel_path:
            safe_excel_path = excel_path.replace("\\", "/")
            test_args = "driver, row_data"
            
            # Full Data Loader Implementation (Ported from generator.py)
            data_loader = f"""
import pandas as pd
import sys
import os

class SafeData(dict):
    def __missing__(self, key): 
        print(f"[WARN] 엑셀에 변수 '{{key}}'가 없습니다. 빈 값으로 처리합니다.")
        return ""

def get_excel_data():
    file_path = r"{safe_excel_path}"
    print(f"\\n[INFO] 엑셀 로드 중: {{file_path}}")
    if not os.path.exists(file_path):
        print(f"[ERROR] 파일 없음: {{file_path}}")
        return []
    try:
        df = pd.read_excel(file_path, engine='openpyxl').fillna("")
        df.columns = [str(c).strip() for c in df.columns]
        data = df.to_dict(orient='records')
        if not data: print("[WARN] 데이터 없음")
        return data
    except Exception as e:
        print(f"\\n[FATAL] 엑셀 읽기 실패: {{e}}")
        return []
"""
            param_deco = '@pytest.mark.parametrize("row_data", get_excel_data())'

        return f"""
import pytest
import allure
from pages.auto_page import AutoPage

{data_loader}

{param_deco}
def test_workflow({test_args}):
    page = AutoPage(driver)
    page.open("{url}")
    
    with allure.step("Run POM Scenario"):
{"".join(calls) if calls else "        pass"}
"""
