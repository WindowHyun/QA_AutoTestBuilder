
from selenium.webdriver.common.by import By
from .base_page import BasePage

class AutoPage(BasePage):
    
    def step_1_click(self):
        # Test
        self.click((By.ID, 'test', 'Test'), fallback_locators=[])
