
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
import time

class BasePage:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 30)

    def open(self, url):
        self.driver.get(url)

    def wait_for_network_idle(self, timeout=5):
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
        except:
            pass

    def find_element(self, locator, timeout=30, fallback_locators=None):
        """
        Find element with Self-Healing capabilities
        locator: tuple (By.ID, "value", "description")
        fallback_locators: list of tuples [(By.CSS, "val", "desc"), ...]
        """
        self.wait_for_network_idle()
        
        all_locators = [locator] + (fallback_locators or [])
        
        last_error = None
        for l_type, l_val, l_desc in all_locators:
            try:
                el = self.wait.until(EC.element_to_be_clickable((l_type, l_val)))
                # if l_desc != locator[2]:
                #     print(f"[Self-Healing] Primary failed, used {l_desc}")
                return el
            except Exception as e:
                last_error = e
                continue
                
        raise last_error or NoSuchElementException(f"Element not found: {locator}")

    def click(self, locator, fallback_locators=None):
        el = self.find_element(locator, fallback_locators=fallback_locators)
        try:
            el.click()
        except:
            self.driver.execute_script("arguments[0].click();", el)

    def type(self, locator, text, fallback_locators=None):
        el = self.find_element(locator, fallback_locators=fallback_locators)
        el.clear()
        el.send_keys(text)
