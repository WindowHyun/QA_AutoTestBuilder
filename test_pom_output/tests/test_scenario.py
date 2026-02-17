
import pytest
import allure
from pages.auto_page import AutoPage




def test_workflow(driver):
    page = AutoPage(driver)
    page.open("https://example.com")
    
    with allure.step("Run POM Scenario"):
        page.step_1_click()    page.step_2_input('testuser')
