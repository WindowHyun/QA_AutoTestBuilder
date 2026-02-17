
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
import time



# [Helper] Safe String Formatter
class SafeData(dict):
    def __missing__(self, key):
        print(f"[WARN] 엑셀에 변수 '{key}'가 없습니다. 빈 값으로 처리합니다.")
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
    driver.get("https://beta5-m.brand.naver.com/mongdies/products/11002466982?site_preference=device&NaPm=ct%3Dmlhoe7wm%7Cci%3Dshopn%7Ctr%3Dnshfum%7Chk%3Da091af30a6b47122eb680f97170b37e195610a45%7Ctrx%3Dundefined")
    yield driver
    try:
        driver.quit()
    except:
        pass


@allure.feature("자동 생성된 테스트 시나리오")
def test_scenario(driver):
    wait = WebDriverWait(driver, 30)
    actions = ActionChains(driver)
    drag_source_el = None

    try:

    except Exception as e:
        allure.attach(driver.get_screenshot_as_png(), name="Error_Screenshot", attachment_type=allure.attachment_type.PNG)
        raise e
