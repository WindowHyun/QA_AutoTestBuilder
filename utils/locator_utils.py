"""로케이터 타입 변환 유틸리티"""
from selenium.webdriver.common.by import By

LOCATOR_MAP = {
    "ID": By.ID,
    "CSS": By.CSS_SELECTOR,
    "NAME": By.NAME,
    "XPATH": By.XPATH
}

def get_by_type(locator_type: str):
    """
    문자열 locator_type을 Selenium By 타입으로 변환

    Args:
        locator_type: "ID", "CSS", "NAME", "XPATH" 중 하나

    Returns:
        By.ID, By.CSS_SELECTOR, By.NAME, By.XPATH 중 하나
    """
    return LOCATOR_MAP.get(locator_type, By.XPATH)

def get_by_string(locator_type: str) -> str:
    """
    코드 생성 시 사용할 By 타입 문자열 반환

    Args:
        locator_type: "ID", "CSS", "NAME", "XPATH" 중 하나

    Returns:
        "By.ID", "By.CSS_SELECTOR", "By.NAME", "By.XPATH" 중 하나
    """
    mapping = {
        "ID": "By.ID",
        "CSS": "By.CSS_SELECTOR",
        "NAME": "By.NAME",
        "XPATH": "By.XPATH"
    }
    return mapping.get(locator_type, "By.XPATH")
