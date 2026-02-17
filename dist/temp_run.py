
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


import pandas as pd
import sys
import os

def get_excel_data():
    file_path = r"D:/QA/QA_AutoTestBuilder/data.xlsx"
    print(f"\n[INFO] 엑셀 로드 중: {file_path}")
    if not os.path.exists(file_path):
        print(f"[ERROR] 파일 없음: {file_path}")
        return []
    try:
        df = pd.read_excel(file_path, engine='openpyxl').fillna("")
        df.columns = [str(c).strip() for c in df.columns]
        data = df.to_dict(orient='records')
        if not data: print("[WARN] 데이터 없음")
        return data
    except Exception as e:
        print(f"\n[FATAL] 엑셀 읽기 실패: {e}")
        return []


# [Helper] Safe String Formatter
class SafeData(dict):
    def __missing__(self, key):
        print(f"[WARN] 엑셀에 변수 '{key}'가 없습니다. 빈 값으로 처리합니다.")
        return ""

# [Helper] Smart Wait
def wait_for_network_idle(driver, timeout=5):
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
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

    prefs = {
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False,
    }
    options.add_experimental_option("prefs", prefs)
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(service=service, options=options)
    driver.get("https://www.saucedemo.com/")
    yield driver
    try:
        driver.quit()
    except:
        pass

@pytest.mark.parametrize("row_data", get_excel_data())
@allure.feature("자동 생성된 테스트 시나리오")
def test_scenario(driver, row_data):
    wait = WebDriverWait(driver, 30)
    actions = ActionChains(driver)
    drag_source_el = None

    try:
        safe_value = '{ID}'.format_map(SafeData(row_data))

        with allure.step("Step 1: INPUT - [input] Data-Test: username"):
            # [Self-Healing] 요소 찾기 시도
            el = None
            last_error = None
            found_locator = None

            # [Smart Wait] 네트워크 유휴 상태 대기
            wait_for_network_idle(driver)

            locators_to_try = [(By.CSS_SELECTOR, '[data-test='username']', 'Primary')]
            
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
            el.clear(); el.send_keys(safe_value)
        safe_value = '{PW}'.format_map(SafeData(row_data))

        with allure.step("Step 2: INPUT - [input] Data-Test: password"):
            # [Self-Healing] 요소 찾기 시도
            el = None
            last_error = None
            found_locator = None

            # [Smart Wait] 네트워크 유휴 상태 대기
            wait_for_network_idle(driver)

            locators_to_try = [(By.CSS_SELECTOR, '[data-test='password']', 'Primary')]
            
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
            el.clear(); el.send_keys(safe_value)

        with allure.step("Step 3: CLICK - [input] Data-Test: login-button"):
            # [Self-Healing] 요소 찾기 시도
            el = None
            last_error = None
            found_locator = None

            # [Smart Wait] 네트워크 유휴 상태 대기
            wait_for_network_idle(driver)

            locators_to_try = [(By.CSS_SELECTOR, '[data-test='login-button']', 'Primary')]
            
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

        with allure.step("Step 4: CLICK - [button] ID: react-burger-menu-btn"):
            # [Self-Healing] 요소 찾기 시도
            el = None
            last_error = None
            found_locator = None

            # [Smart Wait] 네트워크 유휴 상태 대기
            wait_for_network_idle(driver)

            locators_to_try = [(By.ID, 'react-burger-menu-btn', 'Primary')]
            
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

        with allure.step("Step 5: CLICK - [a] Data-Test: about-sidebar-link"):
            # [Self-Healing] 요소 찾기 시도
            el = None
            last_error = None
            found_locator = None

            # [Smart Wait] 네트워크 유휴 상태 대기
            wait_for_network_idle(driver)

            locators_to_try = [(By.CSS_SELECTOR, '[data-test='about-sidebar-link']', 'Primary')]
            
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

        with allure.step("Step 6: CLICK - [div] Class: .MuiStack-root.css-3a2c0r"):
            # [Self-Healing] 요소 찾기 시도
            el = None
            last_error = None
            found_locator = None

            # [Smart Wait] 네트워크 유휴 상태 대기
            wait_for_network_idle(driver)

            locators_to_try = [(By.CSS_SELECTOR, '.MuiStack-root.css-3a2c0r', 'Primary')]
            
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

        with allure.step("Step 7: CLICK - [span] Class: .MuiTypography-root.MuiTypography-buttonLabel"):
            # [Self-Healing] 요소 찾기 시도
            el = None
            last_error = None
            found_locator = None

            # [Smart Wait] 네트워크 유휴 상태 대기
            wait_for_network_idle(driver)

            locators_to_try = [(By.CSS_SELECTOR, '.MuiTypography-root.MuiTypography-buttonLabel', 'Primary')]
            
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

        with allure.step("Step 8: CLICK - [button] Class: .MuiButtonBase-root.MuiButton-root.MuiButton-contained.MuiButton-containedDark.MuiButton-sizeMedium.MuiButton-containedSizeMedium.MuiButton-colorDark.MuiButton-disableElevation.MuiButton-root.MuiButton-contained.MuiButton-containedDark.MuiButton-sizeMedium.MuiButton-containedSizeMedium.MuiButton-colorDark.MuiButton-disableElevation"):
            # [Self-Healing] 요소 찾기 시도
            el = None
            last_error = None
            found_locator = None

            # [Smart Wait] 네트워크 유휴 상태 대기
            wait_for_network_idle(driver)

            locators_to_try = [(By.CSS_SELECTOR, '.MuiButtonBase-root.MuiButton-root.MuiButton-contained.MuiButton-containedDark.MuiButton-sizeMedium.MuiButton-containedSizeMedium.MuiButton-colorDark.MuiButton-disableElevation.MuiButton-root.MuiButton-contained.MuiButton-containedDark.MuiButton-sizeMedium.MuiButton-containedSizeMedium.MuiButton-colorDark.MuiButton-disableElevation', 'Primary')]
            
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

        with allure.step("Step 9: CLICK - [a] Title: Authenticate with Google"):
            # [Self-Healing] 요소 찾기 시도
            el = None
            last_error = None
            found_locator = None

            # [Smart Wait] 네트워크 유휴 상태 대기
            wait_for_network_idle(driver)

            locators_to_try = [(By.CSS_SELECTOR, '[title='Authenticate with Google']', 'Primary')]
            
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
        allure.attach(driver.get_screenshot_as_png(), name="Error_Screenshot", attachment_type=allure.attachment_type.PNG)
        raise e
