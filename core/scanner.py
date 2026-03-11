"""
페이지 요소 스캐너 모듈 (Proxy/Factory)

config.yaml 의 engine 설정에 따라 SeleniumPageScanner 또는 PlaywrightPageScanner를 반환합니다.
"""

from typing import Dict, List, Optional
import config
from utils.logger import setup_logger

logger = setup_logger(__name__)

class PageScanner:
    """
    페이지 요소 스캐너 프록시 클래스
    엔진(Selenium/Playwright)과 상관없이 동일한 API 제공
    """
    
    def __init__(self):
        self._engine_type = config.DEFAULT_ENGINE
        
        if self._engine_type == "playwright":
            from core.scanner_playwright import PlaywrightPageScanner
            self._scanner = PlaywrightPageScanner()
        else:
            from core.scanner_selenium import SeleniumPageScanner
            self._scanner = SeleniumPageScanner()

    def determine_locator(self, el) -> tuple[str, str, str]:
        return self._scanner.determine_locator(el)

    def determine_locators_with_fallback(self, el) -> List[Dict]:
        return self._scanner.determine_locators_with_fallback(el)

    def create_step_data(self, element, shadow_path: Optional[List[Dict]] = None) -> Dict:
        return self._scanner.create_step_data(element, shadow_path)

    def create_text_validation_step(self, text: str) -> Dict:
        return self._scanner.create_text_validation_step(text)

    def create_url_validation_step(self, url: str) -> Dict:
        return self._scanner.create_url_validation_step(url)
