from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException, TimeoutException
from typing import Optional, List, Dict, Any
import config
from utils.logger import setup_logger
from utils.locator_utils import get_by_type
from core.browser_config import BrowserConfig

logger = setup_logger(__name__)


class BrowserManager:
    def __init__(self):
        self.driver = None
        self._browser_type = None

    def __enter__(self):
        """Context Manager 지원"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context Manager 지원 - 자동 종료"""
        self.close()
        return False

    @property
    def is_alive(self):
        """드라이버가 살아있는지 확인"""
        if not self.driver:
            return False
        try:
            _ = self.driver.current_url
            return True
        except WebDriverException:
            return False

    def open_browser(self, url, browser_type="chrome"):
        """
        브라우저 실행

        Args:
            url (str): 접속할 URL
            browser_type (str): 브라우저 종류 (chrome, firefox, edge)

        Returns:
            tuple: (성공 여부, 메시지)
        """
        browser_type = browser_type.lower()

        # 지원 브라우저 확인
        if browser_type not in BrowserConfig.SUPPORTED_BROWSERS:
            logger.error(f"지원하지 않는 브라우저: {browser_type}")
            return False, f"지원하지 않는 브라우저: {browser_type}. 지원: {BrowserConfig.SUPPORTED_BROWSERS}"

        try:
            # 중앙화된 설정으로 드라이버 생성
            self.driver = BrowserConfig.create_driver(browser_type, headless=False)
            self._browser_type = browser_type
            self.driver.get(url)
            self._inject_click_tracker()

            logger.info(f"{browser_type.upper()} 브라우저 실행 성공: {url}")
            return True, f"{browser_type.upper()} 브라우저 실행 중"

        except WebDriverException as e:
            logger.error(f"WebDriver 오류: {e}")
            return False, f"WebDriver 오류: {str(e)[:100]}"
        except TimeoutException as e:
            logger.error(f"페이지 로딩 타임아웃: {e}")
            return False, f"페이지 로딩 타임아웃: {url}"
        except Exception as e:
            logger.error(f"브라우저 실행 실패: {e}")
            return False, f"실행 실패: {e}"

    def _inject_click_tracker(self):
        """클릭 추적 JavaScript 주입"""
        if not self.driver:
            return
        try:
            js_code = """
            document.addEventListener('mousedown', function(event) {
                window.lastClickedElement = event.target;
            }, true);
            """
            self.driver.execute_script(js_code)
            logger.debug("클릭 추적 스크립트 주입 완료")
        except Exception as e:
            logger.warning(f"클릭 추적 스크립트 주입 실패: {e}")

    def get_selected_element(self):
        """마지막 클릭된 요소 또는 포커스된 요소 반환"""
        if not self.driver:
            return None
        try:
            last_el = self.driver.execute_script("return window.lastClickedElement;")
            if last_el:
                return last_el
            return self.driver.switch_to.active_element
        except Exception as e:
            logger.warning(f"요소 가져오기 실패, active_element 반환: {e}")
            try:
                return self.driver.switch_to.active_element
            except Exception as e2:
                logger.error(f"active_element도 가져오기 실패: {e2}")
                return None

    def get_selected_text(self):
        """드래그하여 선택된 텍스트 반환"""
        if not self.driver:
            return ""
        try:
            text = self.driver.execute_script("return window.getSelection().toString();")
            return text.strip() if text else ""
        except Exception as e:
            logger.warning(f"선택된 텍스트 가져오기 실패: {e}")
            return ""

    def highlight_element(self, element=None, locator_type=None, locator_value=None):
        """요소를 하이라이트 표시 (빨간 테두리)"""
        if not self.driver:
            return
        try:
            target = element
            if not target and locator_type and locator_value:
                by = get_by_type(locator_type)
                target = self.driver.find_element(by, locator_value)

            if target:
                self.driver.execute_script(
                    f"arguments[0].style.border='{config.HIGHLIGHT_BORDER} solid {config.HIGHLIGHT_COLOR}';",
                    target
                )
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", target)
                logger.debug(f"요소 하이라이트 완료: {locator_type}={locator_value}")
        except Exception as e:
            logger.warning(f"요소 하이라이트 실패: {e}")

    def close(self):
        """브라우저 종료"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("브라우저 정상 종료")
            except Exception as e:
                logger.error(f"브라우저 종료 중 에러: {e}")
            finally:
                self.driver = None

    # ============================================================
    # Shadow DOM 지원
    # ============================================================

    def find_shadow_element(self, shadow_path: List[Dict], final_locator: Dict) -> Optional[Any]:
        """
        Shadow DOM 내부 요소 찾기

        Args:
            shadow_path: Shadow DOM 경로 [{"type": "CSS", "value": "host-selector"}, ...]
            final_locator: 최종 요소 로케이터 {"type": "CSS", "value": "selector"}

        Returns:
            WebElement 또는 None
        """
        if not self.driver:
            return None

        try:
            # JavaScript로 Shadow DOM 탐색
            js_code = self._build_shadow_finder_js(shadow_path, final_locator)
            element = self.driver.execute_script(js_code)
            return element
        except Exception as e:
            logger.warning(f"Shadow DOM 요소 찾기 실패: {e}")
            return None

    def _build_shadow_finder_js(self, shadow_path: List[Dict], final_locator: Dict) -> str:
        """Shadow DOM 탐색 JavaScript 코드 생성"""
        js_parts = ["let root = document;"]

        # Shadow DOM 경로 순회
        for i, host in enumerate(shadow_path):
            selector = host.get("value", "")
            js_parts.append(f"let host{i} = root.querySelector('{self._escape_js_string(selector)}');")
            js_parts.append(f"if (!host{i} || !host{i}.shadowRoot) return null;")
            js_parts.append(f"root = host{i}.shadowRoot;")

        # 최종 요소 찾기
        final_selector = final_locator.get("value", "")
        final_type = final_locator.get("type", "CSS")

        if final_type == "CSS":
            js_parts.append(f"return root.querySelector('{self._escape_js_string(final_selector)}');")
        elif final_type == "XPATH":
            # Shadow DOM 내에서 XPath 사용
            js_parts.append(f"""
                let result = document.evaluate(
                    '{self._escape_js_string(final_selector)}',
                    root,
                    null,
                    XPathResult.FIRST_ORDERED_NODE_TYPE,
                    null
                );
                return result.singleNodeValue;
            """)
        else:
            js_parts.append(f"return root.querySelector('{self._escape_js_string(final_selector)}');")

        return "\n".join(js_parts)

    def _escape_js_string(self, s: str) -> str:
        """JavaScript 문자열 이스케이프"""
        return s.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"').replace("\n", "\\n")

    def get_shadow_dom_path(self, element) -> List[Dict]:
        """
        요소의 Shadow DOM 경로 추출

        Args:
            element: WebElement

        Returns:
            Shadow DOM 호스트 경로 리스트
        """
        if not self.driver or not element:
            return []

        try:
            js_code = """
            function getShadowPath(el) {
                let path = [];
                let current = el;

                while (current) {
                    // Shadow root 내부인지 확인
                    let root = current.getRootNode();

                    if (root instanceof ShadowRoot) {
                        // Shadow host 찾기
                        let host = root.host;

                        // Host의 CSS 셀렉터 생성
                        let selector = getUniqueSelector(host);
                        path.unshift({
                            type: "CSS",
                            value: selector,
                            tagName: host.tagName.toLowerCase()
                        });

                        current = host;
                    } else {
                        break;
                    }
                }

                return path;
            }

            function getUniqueSelector(el) {
                // ID가 있으면 사용
                if (el.id) {
                    return '#' + CSS.escape(el.id);
                }

                // data-testid가 있으면 사용
                if (el.dataset.testid) {
                    return '[data-testid="' + el.dataset.testid + '"]';
                }

                // 태그 + nth-child 조합
                let parent = el.parentElement;
                if (!parent) {
                    return el.tagName.toLowerCase();
                }

                let siblings = Array.from(parent.children);
                let index = siblings.indexOf(el) + 1;
                let tagName = el.tagName.toLowerCase();

                return tagName + ':nth-child(' + index + ')';
            }

            return getShadowPath(arguments[0]);
            """
            return self.driver.execute_script(js_code, element)
        except Exception as e:
            logger.warning(f"Shadow DOM 경로 추출 실패: {e}")
            return []

    def is_in_shadow_dom(self, element) -> bool:
        """요소가 Shadow DOM 내부에 있는지 확인"""
        if not self.driver or not element:
            return False

        try:
            js_code = """
            let root = arguments[0].getRootNode();
            return root instanceof ShadowRoot;
            """
            return self.driver.execute_script(js_code, element)
        except Exception as e:
            logger.warning(f"Shadow DOM 확인 실패: {e}")
            return False

    def get_all_shadow_hosts(self) -> List[Any]:
        """
        페이지 내 모든 Shadow DOM 호스트 요소 찾기

        Returns:
            Shadow host WebElement 리스트
        """
        if not self.driver:
            return []

        try:
            js_code = """
            function getAllShadowHosts(root = document) {
                let hosts = [];

                // 현재 레벨의 모든 요소 순회
                let walker = document.createTreeWalker(
                    root,
                    NodeFilter.SHOW_ELEMENT,
                    null,
                    false
                );

                let node;
                while (node = walker.nextNode()) {
                    if (node.shadowRoot) {
                        hosts.push(node);
                        // 재귀적으로 Shadow DOM 내부도 탐색
                        hosts.push(...getAllShadowHosts(node.shadowRoot));
                    }
                }

                return hosts;
            }

            return getAllShadowHosts();
            """
            return self.driver.execute_script(js_code)
        except Exception as e:
            logger.warning(f"Shadow host 검색 실패: {e}")
            return []

    def highlight_shadow_element(self, shadow_path: List[Dict], final_locator: Dict):
        """Shadow DOM 내부 요소 하이라이트"""
        element = self.find_shadow_element(shadow_path, final_locator)
        if element:
            self.highlight_element(element=element)