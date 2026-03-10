"""
Playwright 백엔드 모듈

Playwright 라이브러리를 사용하여 브라우저 제어를 수행합니다.
"""

from typing import Optional, Dict, Any, List
from utils.logger import setup_logger
from core.engine_interface import BrowserEngine
import config

logger = setup_logger(__name__)

class PlaywrightEngine(BrowserEngine):
    """
    Playwright 기반 브라우저 제어 엔진
    """
    
    def __init__(self):
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None
        self._browser_type = None

    @property
    def driver(self) -> Any:
        # Playwright에서는 Page 객체가 주된 컨텍스트
        return self._page

    @property
    def is_alive(self) -> bool:
        return self._page is not None and not self._page.is_closed()

    def open_browser(self, url: str, browser_type: str = "chrome") -> tuple[bool, str]:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            return False, "playwright 패키지가 설치되어 있지 않습니다. pip install playwright 필수"

        try:
            self._playwright = sync_playwright().start()
            
            # Browser Type 매핑 (chrome -> chromium, firefox -> firefox, edge -> chromium, safari -> webkit)
            launch_options = {
                "headless": config.DEFAULT_HEADLESS
            }

            b_type = browser_type.lower()
            if b_type == "chrome":
                launch_options["channel"] = "chrome"
                browser_obj = self._playwright.chromium
            elif b_type == "edge":
                launch_options["channel"] = "msedge"
                browser_obj = self._playwright.chromium
            elif b_type == "firefox":
                browser_obj = self._playwright.firefox
            elif b_type in ["safari", "webkit"]:
                browser_obj = self._playwright.webkit
            else:
                browser_obj = self._playwright.chromium # fallback

            self._browser = browser_obj.launch(**launch_options)
            self._context = self._browser.new_context(
                ignore_https_errors=True,
                viewport={"width": 1280, "height": 800}
            )
            self._page = self._context.new_page()
            
            logger.info(f"[Playwright] 브라우저 열기: {url} ({b_type})")
            self._page.goto(url, wait_until="networkidle")
            self._browser_type = b_type
            
            return True, ""
        except Exception as e:
            logger.error(f"[Playwright] 브라우저 열기 실패: {str(e)}")
            self.close()
            return False, str(e)

    def close(self):
        """브라우저 종료"""
        try:
            if self._page: self._page.close()
            if self._context: self._context.close()
            if self._browser: self._browser.close()
            if self._playwright: self._playwright.stop()
        except:
            pass
        finally:
            self._page = None
            self._context = None
            self._browser = None
            self._playwright = None

    def get_selected_element(self) -> Any:
        return None

    def get_selected_text(self) -> str:
        return ""

    def highlight_element(self, element=None, locator_type=None, locator_value=None):
        pass

    def enable_inspector_mode(self):
        # TODO: Playwright Inspector Injection
        pass

    def disable_inspector_mode(self):
        # TODO: Playwright Inspector Cleanup
        pass

    def get_picked_element_info(self) -> Optional[Dict]:
        # TODO: Get from window.__ATB_PICKED_ELEMENT via page.evaluate
        return None

    def clear_picked_element(self):
        # TODO: Clear window.__ATB_PICKED_ELEMENT via page.evaluate
        pass
