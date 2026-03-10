"""
Playwright 페이지 요소 스캐너 모듈

Playwright 요소(Locator/ElementHandle 등)를 활용하여 최적의 로케이터를 결정합니다.
(현재는 GUI 요소 선택기에서 반환되는 데이터를 처리하는 용도에 집중)
"""

import re
from typing import Tuple, List, Dict, Optional

class PlaywrightPageScanner:
    """웹 페이지 요소 스캐너 (Playwright 전용)"""

    LOCATOR_PRIORITY = {
        "data-testid": 1,
        "data-test": 1,
        "data-qa": 1,
        "id": 2,
        "aria-label": 3,
        "title": 4,
        "alt": 5,
        "name": 6,
        "placeholder": 7
    }

    def determine_locator(self, el_dict) -> Tuple[str, str, str]:
        """
        요소 사전에서 단일 최적 식별자 반환
        Playwright 모드에서는 Inspector가 JavaScript로 요소 속성을 추출하여 
        딕셔너리 형태로 전달한다고 가정합니다.
        
        Args:
            el_dict: {tag, id, class, name, placeholder, text, attributes: {...}}
        """
        cands = self._collect_locator_candidates(el_dict)
        if not cands:
            return ("xpath", "//body", "Fallback //body")
        cands.sort(key=lambda x: x[0])
        _, loc_type, loc_value, desc = cands[0]
        return loc_type, loc_value, desc

    def determine_locators_with_fallback(self, el_dict) -> List[Dict]:
        """다중 로케이터 지원 (Fallback 목록 반환)"""
        cands = self._collect_locator_candidates(el_dict)
        cands.sort(key=lambda x: x[0])
        
        results = []
        for _, loc_type, loc_value, desc in cands[:5]:
            results.append({
                "type": loc_type,
                "value": loc_value,
                "desc": desc
            })
            
        if not results:
            results.append({"type": "xpath", "value": "//body", "desc": "Fallback //body"})
            
        return results

    def _collect_locator_candidates(self, el_dict) -> List[Tuple[int, str, str, str]]:
        cands = []
        if not isinstance(el_dict, dict):
            # PlaywrightLocator가 넘어올 경우 대비 (나중에 고도화 필요)
            return cands

        tag = el_dict.get('tag', '').lower()
        if not tag:
            return cands

        attrs = el_dict.get('attributes', {})
        
        # 1. 우선순위 속성
        for attr, priority in self.LOCATOR_PRIORITY.items():
            if attr in attrs and attrs[attr]:
                val = attrs[attr]
                # CSS Selector 방식
                cands.append((priority, "css", f"[{attr}='{val}']", f"{attr}: {val}"))
                
                # XPath는 특수문자 안전 처리 (그대로 사용하되 이스케이프)
                cands.append((priority + 0.1, "xpath", f"//{tag}[@{attr}='{val}']", f"{attr}: {val}"))

        # 2. ID (동적인지 판별)
        el_id = el_dict.get('id', '')
        if el_id and not self._is_dynamic_string(el_id):
            cands.append((2.0, "id", el_id, f"ID: {el_id}"))

        # 3. Name 속성
        el_name = el_dict.get('name', '')
        if el_name:
            cands.append((6.0, "name", el_name, f"Name: {el_name}"))

        # 4. Class Name (단일 클래스)
        el_class = el_dict.get('class', '')
        if el_class:
            valid_classes = self._filter_valid_classes(el_class)
            if valid_classes:
                primary = valid_classes[0]
                cands.append((8.0, "css_selector", f".{primary}", f"Class: .{primary}"))

        # 5. Link Text (a 태그)
        if tag == "a":
            text = el_dict.get('text', '').strip()
            if text and len(text) < 50:
                cands.append((9.0, "link text", text, f"Link Text: {text}"))

        # 6. 기본 XPath (항상 하위 옵션으로 제공)
        xpath = el_dict.get('xpath', '')
        if xpath:
            cands.append((10.0, "xpath", xpath, f"XPath: {xpath}"))

        return cands

    def _is_dynamic_string(self, text: str) -> bool:
        if not text:
            return False
        if len(text) > 15 and re.search(r'\d{4,}', text):
            return True
        if re.search(r'[0-9a-f]{8,}', text.lower()):
            return True
        import uuid
        try:
            uuid.UUID(text)
            return True
        except ValueError:
            pass
        return False

    def _filter_valid_classes(self, class_string: str) -> List[str]:
        if not class_string:
            return []
        classes = class_string.split()
        return [c for c in classes if not self._is_dynamic_class(c)]

    def _is_dynamic_class(self, class_name: str) -> bool:
        if "__" in class_name or "--" in class_name or class_name.startswith("css-"):
            return True
        if len(class_name) > 15 and re.search(r'\d{3,}', class_name):
            return True
        return False

    def create_step_data(self, element_dict, shadow_path: Optional[List[Dict]] = None) -> Dict:
        locators = self.determine_locators_with_fallback(element_dict)
        best = locators[0]
        
        tag = element_dict.get('tag', '').lower()
        if tag in ('input', 'textarea'):
            action_type = "input"
        elif tag == "select":
            action_type = "select"
        else:
            action_type = "click"

        step = {
            "action": action_type,
            "type": best["type"],
            "locator": best["value"],
            "name": f"{desc} {action_type.capitalize()}" if (desc := best.get('desc', '')) else f"Element {action_type.capitalize()}",
            "value": "",
            "description": best.get('desc', ''),
            "locators": locators
        }

        if shadow_path:
            step["shadow_path"] = shadow_path
            step["name"] = f"[Shadow] {step['name']}"

        return step

    def create_text_validation_step(self, text: str) -> Dict:
        return {
            "action": "check_text",
            "type": "n/a",
            "locator": "",
            "value": text,
            "name": f"텍스트 확인: '{text[:20]}...'",
            "description": f"화면에 '{text}' 텍스트가 존재하는지 확인합니다."
        }

    def create_url_validation_step(self, url: str) -> Dict:
        return {
            "action": "check_url",
            "type": "n/a",
            "locator": "",
            "value": url,
            "name": f"URL 확인: {url}",
            "description": f"현재 페이지 URL이 '{url}'과 일치하는지 확인합니다."
        }
