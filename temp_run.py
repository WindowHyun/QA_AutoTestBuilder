
import pytest
import allure
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import os
from datetime import datetime



# [Helper] Safe String Formatter
class SafeData(dict):
    def __missing__(self, key):
        print(f"[WARN] 데이터에 변수 '{key}'가 없습니다. 빈 값으로 처리합니다.")
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
                if (document.getAnimations) {
                    let animations = document.getAnimations();
                    for (let anim of animations) {
                        if (anim.playState === 'running' && anim.effect.getComputedTiming().progress < 1) {
                            return false;
                        }
                    }
                }
                
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
    filename = f"{name}_{timestamp}.png" if name else f"screenshot_{timestamp}.png"
    filepath = os.path.join(SCREENSHOT_DIR, filename)
    try:
        driver.save_screenshot(filepath)
        print(f"[Screenshot] {filepath}")
    except Exception as e:
        print(f"[Screenshot Error] {e}")

# [Helper] Retry decorator (Self-Healing)
def retry_on_failure(max_retries=1):
    def decorator(func):
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        print(f"\n[RETRY] 테스트 실패 (시도 {attempt+1}/{max_retries+1}): {e}")
                        print(f"[RETRY] {max_retries - attempt}회 재시도 남음...")
                    else:
                        print(f"\n[FAIL] 모든 재시도 소진 ({max_retries+1}회 시도): {e}")
            raise last_exception
        return wrapper
    return decorator


@pytest.fixture
def driver():
    service = ChromeService(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--incognito")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-notifications")
    prefs = {"credentials_enable_service": False, "profile.password_manager_enabled": False}
    options.add_experimental_option("prefs", prefs)
    options.add_experimental_option("excludeSwitches", ['enable-automation'])
    options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(service=service, options=options)
    driver.get("https://www.saucedemo.com/")
    yield driver
    try:
        driver.quit()
    except:
        pass


@allure.feature("자동 생성된 테스트 시나리오")

@retry_on_failure(max_retries=1)
def test_scenario(driver):
    wait = WebDriverWait(driver, 30)
    actions = ActionChains(driver)
    drag_source_el = None

    try:

        with allure.step("Step 1: INPUT - [input] data-test: username"):
            # [Self-Healing] 요소 찾기 시도
            el = None
            last_error = None
            found_locator = None

            # [Smart Wait] 네트워크 유휴 상태 대기
            wait_for_network_idle(driver)

            locators_to_try = [(By.CSS_SELECTOR, '[data-test=\'username\']', 'Primary'), (By.ID, 'user-name', 'ID: user-name'), (By.NAME, 'user-name', 'Name: user-name'), (By.XPATH, '//input[@placeholder=\'Username\']', 'Placeholder: Username'), (By.CSS_SELECTOR, '.input_error.form_input', 'Class: .input_error.form_input')]
            
            for l_type, l_val, l_desc in locators_to_try:
                try:
                    # 가시성 확보 대기 (Self-Healing 시에는 약간 더 짧게 시도 가능하지만 안전하게 유지)
                    el = wait.until(EC.visibility_of_element_located((l_type, l_val)))
                    found_locator = l_desc
                    # print(f"   -> 성공: {l_desc}") # 디버그용
                    break
                except TimeoutException as e:
                    last_error = e
                    continue
                except Exception as e:
                    last_error = e
                    continue
            
            if not el:
                raise last_error or Exception("모든 로케이터 시도 실패")
            
            if found_locator != 'Primary':
                 print(f"\n[INFO] Self-Healing 동작: Primary 실패 -> {found_locator} 로 성공")
            el.clear(); el.send_keys('standard_user')

        with allure.step("Step 2: INPUT_PASSWORD - [input] data-test: password"):
            # [Self-Healing] 요소 찾기 시도
            el = None
            last_error = None
            found_locator = None

            # [Smart Wait] 네트워크 유휴 상태 대기
            wait_for_network_idle(driver)

            locators_to_try = [(By.CSS_SELECTOR, '[data-test=\'password\']', 'Primary'), (By.ID, 'password', 'ID: password'), (By.NAME, 'password', 'Name: password'), (By.XPATH, '//input[@placeholder=\'Password\']', 'Placeholder: Password'), (By.CSS_SELECTOR, '.input_error.form_input', 'Class: .input_error.form_input')]
            
            for l_type, l_val, l_desc in locators_to_try:
                try:
                    # 가시성 확보 대기 (Self-Healing 시에는 약간 더 짧게 시도 가능하지만 안전하게 유지)
                    el = wait.until(EC.visibility_of_element_located((l_type, l_val)))
                    found_locator = l_desc
                    # print(f"   -> 성공: {l_desc}") # 디버그용
                    break
                except TimeoutException as e:
                    last_error = e
                    continue
                except Exception as e:
                    last_error = e
                    continue
            
            if not el:
                raise last_error or Exception("모든 로케이터 시도 실패")
            
            if found_locator != 'Primary':
                 print(f"\n[INFO] Self-Healing 동작: Primary 실패 -> {found_locator} 로 성공")
            el.clear(); el.send_keys('secret_sauce')

        with allure.step("Step 3: CLICK - [input] data-test: login-button"):
            # [Self-Healing] 요소 찾기 시도
            el = None
            last_error = None
            found_locator = None

            # [Smart Wait] 네트워크 유휴 상태 대기
            wait_for_network_idle(driver)

            locators_to_try = [(By.CSS_SELECTOR, '[data-test=\'login-button\']', 'Primary'), (By.ID, 'login-button', 'ID: login-button'), (By.NAME, 'login-button', 'Name: login-button'), (By.CSS_SELECTOR, '.submit-button.btn_action', 'Class: .submit-button.btn_action')]
            
            for l_type, l_val, l_desc in locators_to_try:
                try:
                    # 가시성 확보 대기 (Self-Healing 시에는 약간 더 짧게 시도 가능하지만 안전하게 유지)
                    el = wait.until(EC.element_to_be_clickable((l_type, l_val)))
                    found_locator = l_desc
                    # print(f"   -> 성공: {l_desc}") # 디버그용
                    break
                except TimeoutException as e:
                    last_error = e
                    continue
                except Exception as e:
                    last_error = e
                    continue
            
            if not el:
                raise last_error or Exception("모든 로케이터 시도 실패")
            
            if found_locator != 'Primary':
                 print(f"\n[INFO] Self-Healing 동작: Primary 실패 -> {found_locator} 로 성공")
            try:
                el.click()
            except Exception:
                driver.execute_script("arguments[0].click();", el)

    except Exception as e:
        take_screenshot(driver, "error")
        allure.attach(driver.get_screenshot_as_png(), name="Error_Screenshot", attachment_type=allure.attachment_type.PNG)
        raise e
