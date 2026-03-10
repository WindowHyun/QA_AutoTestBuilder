from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException, TimeoutException
from typing import Optional, List, Dict, Any
import config
from utils.logger import setup_logger
from utils.locator_utils import get_by_type
from core.browser_config import BrowserConfig
from core.engine_interface import BrowserEngine

logger = setup_logger(__name__)


class SeleniumEngine(BrowserEngine):
    def __init__(self):
        self._driver = None
        self._browser_type = None

    @property
    def driver(self) -> Any:
        return self._driver

    def __enter__(self):
        """Context Manager 지원"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context Manager 지원 - 자동 종료"""
        self.close()
        return False

    @property
    def is_alive(self) -> bool:
        """드라이버가 살아있는지 확인"""
        if not self._driver:
            return False
        try:
            self._driver.current_url
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
            self._driver = BrowserConfig.create_driver(browser_type, headless=False)
            self._browser_type = browser_type
            self._driver.get(url)
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
        if not self._driver:
            return
        try:
            js_code = """
            document.addEventListener('mousedown', function(event) {
                window.lastClickedElement = event.target;
            }, true);
            """
            self._driver.execute_script(js_code)
            logger.debug("클릭 추적 스크립트 주입 완료")
        except Exception as e:
            logger.warning(f"클릭 추적 스크립트 주입 실패: {e}")

    def get_selected_element(self):
        """마지막 클릭된 요소 또는 포커스된 요소 반환"""
        if not self._driver:
            return None
        try:
            last_el = self._driver.execute_script("return window.lastClickedElement;")
            if last_el:
                return last_el
            return self._driver.switch_to.active_element
        except Exception as e:
            logger.warning(f"요소 가져오기 실패, active_element 반환: {e}")
            try:
                return self._driver.switch_to.active_element
            except Exception as e2:
                logger.error(f"active_element도 가져오기 실패: {e2}")
                return None

    def get_selected_text(self):
        """드래그하여 선택된 텍스트 반환"""
        if not self._driver:
            return ""
        try:
            text = self._driver.execute_script("return window.getSelection().toString();")
            return text.strip() if text else ""
        except Exception as e:
            logger.warning(f"선택된 텍스트 가져오기 실패: {e}")
            return ""

    def highlight_element(self, element=None, locator_type=None, locator_value=None):
        """요소를 하이라이트 표시 (빨간 테두리)"""
        if not self._driver:
            return
        try:
            target = element
            if not target and locator_type and locator_value:
                by = get_by_type(locator_type)
                target = self._driver.find_element(by, locator_value)

            if target:
                self._driver.execute_script(
                    f"arguments[0].style.border='{config.HIGHLIGHT_BORDER} solid {config.HIGHLIGHT_COLOR}';",
                    target
                )
                self._driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", target)
                logger.debug(f"요소 하이라이트 완료: {locator_type}={locator_value}")
        except Exception as e:
            logger.warning(f"요소 하이라이트 실패: {e}")

    def close(self):
        """브라우저 종료"""
        if self._driver:
            try:
                self._driver.quit()
                logger.info("브라우저 정상 종료")
            except Exception as e:
                logger.error(f"브라우저 종료 중 에러: {e}")
            finally:
                self._driver = None

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
        if not self._driver:
            return None

        try:
            # JavaScript로 Shadow DOM 탐색
            js_code = self._build_shadow_finder_js(shadow_path, final_locator)
            element = self._driver.execute_script(js_code)
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
        if not self._driver or not element:
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
            return self._driver.execute_script(js_code, element)
        except Exception as e:
            logger.warning(f"Shadow DOM 경로 추출 실패: {e}")
            return []

    def is_in_shadow_dom(self, element) -> bool:
        """요소가 Shadow DOM 내부에 있는지 확인"""
        if not self._driver or not element:
            return False

        try:
            js_code = """
            let root = arguments[0].getRootNode();
            return root instanceof ShadowRoot;
            """
            return self._driver.execute_script(js_code, element)
        except Exception as e:
            logger.warning(f"Shadow DOM 확인 실패: {e}")
            return False

    def get_all_shadow_hosts(self) -> List[Any]:
        """
        페이지 내 모든 Shadow DOM 호스트 요소 찾기

        Returns:
            Shadow host WebElement 리스트
        """
        if not self._driver:
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
            return self._driver.execute_script(js_code)
        except Exception as e:
            logger.warning(f"Shadow host 검색 실패: {e}")
            return []

    def highlight_shadow_element(self, shadow_path: List[Dict], final_locator: Dict):
        """Shadow DOM 내부 요소 하이라이트"""
        element = self.find_shadow_element(shadow_path, final_locator)
        if element:
            self.highlight_element(element=element)

    # ============================================================
    # Inspector 피커 모드 (Playwright Inspector 스타일)
    # ============================================================

    def enable_inspector_mode(self):
        """
        Inspector 피커 모드 활성화

        브라우저에 JS 오버레이를 주입하여:
        - 마우스 호버 시 요소 하이라이트 (빨간 테두리 + 정보 박스)
        - 클릭 시 요소를 window.__ATB_PICKED_ELEMENT에 저장
        """
        if not self._driver:
            return

        try:
            js_code = """
            (function() {
                // 이미 주입된 경우 무시
                if (window.__ATB_INSPECTOR_ACTIVE) return;
                window.__ATB_INSPECTOR_ACTIVE = true;
                window.__ATB_PICKED_ELEMENT = null;
                window.__ATB_HOVERED_INFO = null;

                // 오버레이 레이어 생성
                let overlay = document.createElement('div');
                overlay.id = '__atb_overlay';
                overlay.style.cssText = 'position:fixed;pointer-events:none;border:2px solid #EF4444;' +
                    'background:rgba(239,68,68,0.08);z-index:999999;transition:all 0.1s ease;display:none;';
                document.body.appendChild(overlay);

                // 정보 박스
                let infoBox = document.createElement('div');
                infoBox.id = '__atb_info';
                infoBox.style.cssText = 'position:fixed;pointer-events:none;z-index:999999;' +
                    'background:#1F2937;color:#F3F4F6;font-family:Consolas,monospace;font-size:11px;' +
                    'padding:4px 8px;border-radius:4px;border:1px solid #6366F1;display:none;' +
                    'max-width:400px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;';
                document.body.appendChild(infoBox);

                // 호버 이벤트
                document.addEventListener('mousemove', function __atb_move(e) {
                    if (!window.__ATB_INSPECTOR_ACTIVE) {
                        document.removeEventListener('mousemove', __atb_move);
                        return;
                    }
                    let el = e.target;
                    if (el.id === '__atb_overlay' || el.id === '__atb_info') return;

                    let rect = el.getBoundingClientRect();
                    overlay.style.top = rect.top + 'px';
                    overlay.style.left = rect.left + 'px';
                    overlay.style.width = rect.width + 'px';
                    overlay.style.height = rect.height + 'px';
                    overlay.style.display = 'block';

                    let tag = el.tagName.toLowerCase();
                    let id = el.id ? '#' + el.id : '';
                    let cls = el.className && typeof el.className === 'string' ?
                        '.' + el.className.trim().split(/\\s+/).slice(0,2).join('.') : '';
                    let text = (el.textContent || '').trim().substring(0, 30);

                    infoBox.textContent = '<' + tag + '>' + id + ' ' + cls + (text ? ' "' + text + '"' : '');
                    infoBox.style.top = Math.max(0, rect.top - 28) + 'px';
                    infoBox.style.left = rect.left + 'px';
                    infoBox.style.display = 'block';

                    window.__ATB_HOVERED_INFO = {
                        tag: tag, id: el.id || '', class: el.className || '',
                        text: text, locator: id || cls || tag
                    };
                }, true);

                // 클릭 이벤트 (요소 선택)
                document.addEventListener('click', function __atb_click(e) {
                    if (!window.__ATB_INSPECTOR_ACTIVE) {
                        document.removeEventListener('click', __atb_click, true);
                        return;
                    }
                    let el = e.target;
                    if (el.id === '__atb_overlay' || el.id === '__atb_info') return;

                    e.preventDefault();
                    e.stopPropagation();
                    e.stopImmediatePropagation();

                    window.__ATB_PICKED_ELEMENT = el;

                    // 선택 피드백 (초록색 테두리)
                    overlay.style.borderColor = '#10B981';
                    overlay.style.background = 'rgba(16,185,129,0.15)';
                    setTimeout(() => {
                        overlay.style.borderColor = '#EF4444';
                        overlay.style.background = 'rgba(239,68,68,0.08)';
                    }, 500);
                }, true);
            })();
            """
            self._driver.execute_script(js_code)
            logger.info("Inspector 피커 모드 활성화")
        except Exception as e:
            logger.warning(f"Inspector 모드 활성화 실패: {e}")

    def disable_inspector_mode(self):
        """Inspector 피커 모드 비활성화"""
        if not self._driver:
            return
        try:
            js_code = """
            window.__ATB_INSPECTOR_ACTIVE = false;
            window.__ATB_PICKED_ELEMENT = null;
            window.__ATB_HOVERED_INFO = null;
            let overlay = document.getElementById('__atb_overlay');
            let info = document.getElementById('__atb_info');
            if (overlay) overlay.remove();
            if (info) info.remove();
            """
            self._driver.execute_script(js_code)
            logger.info("Inspector 피커 모드 비활성화")
        except Exception as e:
            logger.warning(f"Inspector 모드 비활성화 실패: {e}")

    def get_picked_element_info(self) -> Optional[Dict]:
        """
        피커로 선택/호버된 요소 정보 반환

        Returns:
            dict: {tag, id, class, locator, picked, element} 또는 None
        """
        if not self._driver:
            return None
        try:
            result = self._driver.execute_script("""
            let info = window.__ATB_HOVERED_INFO || {};
            let picked = window.__ATB_PICKED_ELEMENT;
            return {
                tag: info.tag || '',
                id: info.id || '',
                class: info['class'] || '',
                locator: info.locator || '',
                text: info.text || '',
                picked: !!picked
            };
            """)

            if result and result.get('picked'):
                # picked element를 WebElement로 가져오기
                element = self._driver.execute_script("return window.__ATB_PICKED_ELEMENT;")
                result['element'] = element

            return result
        except Exception:
            return None

    def clear_picked_element(self):
        """선택된 요소 초기화 (스텝 추가 후 호출)"""
        if not self._driver:
            return
        try:
            self.driver.execute_script("window.__ATB_PICKED_ELEMENT = null;")
        except Exception:
            pass