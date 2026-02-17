
from selenium.webdriver.common.by import By
from .base_page import BasePage

class AutoPage(BasePage):
    
    def step_1_click(self):
        # Login Button
        self.click((By.ID, 'login-btn', 'Login Button'), fallback_locators=[(By.CSS_SELECTOR, '#login-btn', 'CSS Fallback'), (By.XPATH, '//button[@id='login-btn']', 'XPath Fallback')])
    def step_2_input(self, value):
        # Username
        self.type((By.NAME, 'username', 'Username'), value, fallback_locators=[])
    def step_3_click(self):
        # Shadow Button
        self.click((By.CSS_SELECTOR, '#shadow-btn', 'Shadow Button'), fallback_locators=[])
