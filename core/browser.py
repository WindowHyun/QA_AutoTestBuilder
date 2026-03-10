"""
브라우저 매니저 모듈 (Proxy/Factory)

config.yaml 의 engine 설정에 따라 Selenium 또는 Playwright 백엔드를 선택하여
동일한 BrowserEngine 인터페이스를 제공하는 프록시 객체입니다.
"""

from typing import Optional, Dict, Any, List
import config
from utils.logger import setup_logger

logger = setup_logger(__name__)

class BrowserManager:
    """
    브라우저 인터페이스 프록시 클래스
    엔진(Selenium/Playwright)과 상관없이 동일한 API 제공
    """
    
    def __init__(self):
        self._engine = None
        self._engine_type = config.DEFAULT_ENGINE
        
        if self._engine_type == "playwright":
            from core.playwright_backend import PlaywrightEngine
            self._engine = PlaywrightEngine()
            logger.info("🛠️ Playwright Engine 초기화")
        else:
            from core.selenium_backend import SeleniumEngine
            self._engine = SeleniumEngine()
            logger.info("🛠️ Selenium Engine 초기화")

    @property
    def driver(self) -> Any:
        return self._engine.driver

    @property
    def is_alive(self) -> bool:
        return self._engine.is_alive

    # Context Manager 지원
    def __enter__(self):
        return self

    # Context Manager 지원 - 자동 종료
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def open_browser(self, url: str, browser_type: str = "chrome") -> tuple[bool, str]:
        return self._engine.open_browser(url, browser_type)

    def close(self):
        self._engine.close()

    def get_selected_element(self) -> Any:
        return self._engine.get_selected_element()

    def get_selected_text(self) -> str:
        return self._engine.get_selected_text()

    def highlight_element(self, element=None, locator_type=None, locator_value=None):
        return self._engine.highlight_element(element, locator_type, locator_value)

    def enable_inspector_mode(self):
        self._engine.enable_inspector_mode()

    def disable_inspector_mode(self):
        self._engine.disable_inspector_mode()

    def get_picked_element_info(self) -> Optional[Dict]:
        return self._engine.get_picked_element_info()

    def clear_picked_element(self):
        self._engine.clear_picked_element()

    # Selenium 전용 Shadow DOM 메서드 프록시 (하위 호환성)
    def find_shadow_element(self, shadow_path, final_locator):
        if hasattr(self._engine, 'find_shadow_element'):
            return self._engine.find_shadow_element(shadow_path, final_locator)
        return None

    def get_shadow_dom_path(self, element):
        if hasattr(self._engine, 'get_shadow_dom_path'):
            return self._engine.get_shadow_dom_path(element)
        return []

    def is_in_shadow_dom(self, element):
        if hasattr(self._engine, 'is_in_shadow_dom'):
            return self._engine.is_in_shadow_dom(element)
        return False

    def get_all_shadow_hosts(self):
        if hasattr(self._engine, 'get_all_shadow_hosts'):
            return self._engine.get_all_shadow_hosts()
        return []