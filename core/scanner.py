"""
페이지 요소 스캐너 모듈

웹 요소를 분석하여 최적의 로케이터를 결정합니다.
XPath 인젝션 방지 및 다중 로케이터 Fallback을 지원합니다.
"""

import re
from typing import Tuple, List, Dict, Optional


class PageScanner:
    """웹 페이지 요소 스캐너"""

    # 로케이터 우선순위 (낮을수록 높은 우선순위)
    LOCATOR_PRIORITY = {
        "data-testid": 1,
        "data-test": 1,
        "data-qa": 1,
        "id": 2,
        "aria-label": 3,
        "title": 4,
        "alt": 5,
        "name": 6,
        "placeholder": 7,
        "class": 8,
        "text": 9,
        "tag": 10,
    }

    def determine_locator(self, el) -> Tuple[str, str, str]:
        """
        요소 분석 및 최적 식별자 반환

        Args:
            el: Selenium WebElement

        Returns:
            tuple: (로케이터 타입, 로케이터 값, 설명)
        """
        # 모든 가능한 로케이터 수집
        candidates = self._collect_locator_candidates(el)

        # 우선순위에 따라 정렬
        candidates.sort(key=lambda x: self.LOCATOR_PRIORITY.get(x[3], 99))

        # 가장 좋은 로케이터 반환
        if candidates:
            return candidates[0][:3]

        # 최후의 수단
        tag = el.tag_name
        return "XPATH", f"//{tag}", f"Tag: {tag}"

    def determine_locators_with_fallback(self, el) -> List[Dict]:
        """
        Fallback 로케이터 목록 반환 (다중 로케이터 지원)

        Args:
            el: Selenium WebElement

        Returns:
            list: 로케이터 딕셔너리 목록 (우선순위 순)
        """
        candidates = self._collect_locator_candidates(el)
        candidates.sort(key=lambda x: self.LOCATOR_PRIORITY.get(x[3], 99))

        return [
            {"type": c[0], "value": c[1], "description": c[2], "source": c[3]}
            for c in candidates[:5]  # 상위 5개만 반환
        ]

    def _collect_locator_candidates(self, el) -> List[Tuple[str, str, str, str]]:
        """
        모든 가능한 로케이터 후보 수집

        Returns:
            list: [(타입, 값, 설명, 소스), ...]
        """
        candidates = []
        tag = el.tag_name

        # 속성 가져오기
        el_id = el.get_attribute("id")
        el_text = (el.text or "").strip()
        el_placeholder = el.get_attribute("placeholder")
        el_class = el.get_attribute("class")
        el_name = el.get_attribute("name")
        el_title = el.get_attribute("title")
        el_alt = el.get_attribute("alt")
        el_aria_label = el.get_attribute("aria-label")

        # Data-* 테스트 속성
        for attr in ["data-testid", "data-test", "data-qa", "data-cy"]:
            value = el.get_attribute(attr)
            if value:
                candidates.append((
                    "CSS",
                    f"[{attr}='{self._escape_css_value(value)}']",
                    f"{attr}: {value}",
                    attr
                ))

        # ID (동적 ID 제외)
        if el_id and not self._is_dynamic_string(el_id):
            candidates.append(("ID", el_id, f"ID: {el_id}", "id"))

        # ARIA Label (접근성 속성)
        if el_aria_label:
            safe_val = self._escape_xpath_value(el_aria_label)
            candidates.append((
                "XPATH",
                f"//*[@aria-label={safe_val}]",
                f"ARIA: {el_aria_label}",
                "aria-label"
            ))

        # Title 속성
        if el_title:
            candidates.append((
                "CSS",
                f"[title='{self._escape_css_value(el_title)}']",
                f"Title: {el_title}",
                "title"
            ))

        # Alt 속성 (이미지)
        if el_alt:
            safe_val = self._escape_xpath_value(el_alt)
            candidates.append((
                "XPATH",
                f"//*[@alt={safe_val}]",
                f"Alt: {el_alt}",
                "alt"
            ))

        # Name 속성
        if el_name:
            candidates.append(("NAME", el_name, f"Name: {el_name}", "name"))

        # Placeholder 속성
        if el_placeholder:
            safe_val = self._escape_xpath_value(el_placeholder)
            candidates.append((
                "XPATH",
                f"//{tag}[@placeholder={safe_val}]",
                f"Placeholder: {el_placeholder}",
                "placeholder"
            ))

        # Class 속성 (동적 클래스 필터링)
        if el_class:
            valid_classes = self._filter_valid_classes(el_class)
            if valid_classes:
                css_selector = "." + ".".join(valid_classes)
                candidates.append((
                    "CSS",
                    css_selector,
                    f"Class: {css_selector}",
                    "class"
                ))

        # 텍스트 기반 (XPath 인젝션 방지)
        if el_text and 3 <= len(el_text) <= 50:
            safe_text = self._escape_xpath_value(el_text)
            candidates.append((
                "XPATH",
                f"//*[contains(text(), {safe_text})]",
                f"Text: {el_text}",
                "text"
            ))

        return candidates

    def _escape_xpath_value(self, value: str) -> str:
        """
        XPath 값 안전하게 이스케이프 (인젝션 방지)

        작은따옴표와 큰따옴표가 모두 포함된 경우 concat() 사용
        """
        if "'" not in value:
            return f"'{value}'"
        elif '"' not in value:
            return f'"{value}"'
        else:
            # 둘 다 포함: concat() 함수 사용
            parts = value.split("'")
            escaped = "concat('" + "', \"'\", '".join(parts) + "')"
            return escaped

    def _escape_css_value(self, value: str) -> str:
        """CSS 셀렉터 값 이스케이프"""
        # 작은따옴표, 큰따옴표, 백슬래시 이스케이프
        return value.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"')

    def _filter_valid_classes(self, class_string: str) -> List[str]:
        """
        유효한 클래스만 필터링 (동적 클래스 제외)

        Args:
            class_string: 공백으로 구분된 클래스 문자열

        Returns:
            list: 유효한 클래스 목록
        """
        classes = class_string.split()
        valid = []

        for cls in classes:
            if not self._is_dynamic_class(cls):
                valid.append(cls)

        return valid

    def _is_dynamic_class(self, class_name: str) -> bool:
        """
        동적 클래스(난수) 판별

        - CSS-in-JS 스타일 (__, --, css-)
        - 긴 해시값 (10자 이상 + 숫자 포함)
        - 유명 프레임워크 동적 클래스 패턴
        """
        # CSS-in-JS 패턴
        if "__" in class_name or "--" in class_name:
            return True

        # 해시 패턴 (예: css-1a2b3c, sc-abcdef)
        if re.match(r'^(css|sc|emotion|styled)-[a-z0-9]+$', class_name, re.IGNORECASE):
            return True

        # 긴 문자열에 숫자 포함
        if len(class_name) > 12 and any(char.isdigit() for char in class_name):
            return True

        # 해시 형태 (연속된 영숫자)
        if re.match(r'^[a-zA-Z]{1,3}[a-zA-Z0-9]{8,}$', class_name):
            return True

        return False

    def _is_dynamic_string(self, text: str) -> bool:
        """ID가 동적인지 체크"""
        # 숫자 3개 이상 연속
        if re.search(r'\d{3,}', text):
            return True

        # UUID 패턴
        if re.match(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$', text, re.IGNORECASE):
            return True

        # 긴 해시값
        if re.match(r'^[a-f0-9]{16,}$', text, re.IGNORECASE):
            return True

        return False

    def create_step_data(self, element, shadow_path: Optional[List[Dict]] = None) -> Dict:
        """
        요소에서 스텝 데이터 생성

        Args:
            element: Selenium WebElement
            shadow_path: Shadow DOM 경로 (있으면 Shadow DOM 내부 요소)

        Returns:
            dict: 스텝 데이터
        """
        l_type, l_value, l_name = self.determine_locator(element)
        tag = element.tag_name

        # 태그에 따른 기본 액션 결정
        action = "click"
        if tag == "input":
            input_type = element.get_attribute("type") or "text"
            if input_type == "password":
                action = "input_password"
            elif input_type in ["text", "email", "search", "tel", "url", "number"]:
                action = "input"
            elif input_type in ["checkbox", "radio", "submit", "button"]:
                action = "click"
        elif tag == "textarea":
            action = "input"
        elif tag == "select":
            action = "click"
        elif tag in ["iframe", "frame"]:
            action = "switch_frame"

        # Fallback 로케이터 저장 (선택적)
        fallback_locators = self.determine_locators_with_fallback(element)

        step_data = {
            "name": f"[{tag}] {l_name}",
            "type": l_type,
            "locator": l_value,
            "action": action,
            "value": "",
            "_fallback_locators": fallback_locators[1:] if len(fallback_locators) > 1 else []
        }

        # Shadow DOM 경로 추가
        if shadow_path:
            step_data["_shadow_path"] = shadow_path
            step_data["name"] = f"[Shadow] [{tag}] {l_name}"

        return step_data

    def create_text_validation_step(self, text: str) -> Dict:
        """
        텍스트 검증 스텝 생성

        Args:
            text: 검증할 텍스트

        Returns:
            dict: 스텝 데이터
        """
        safe_text = self._escape_xpath_value(text)
        locator = f"//*[contains(text(), {safe_text})]"

        display_text = text[:15] + "..." if len(text) > 15 else text

        return {
            "name": f"[검증] {display_text}",
            "type": "XPATH",
            "locator": locator,
            "action": "check_text",
            "value": text
        }

    def create_url_validation_step(self, url: str) -> Dict:
        """
        URL 검증 스텝 생성

        Args:
            url: 검증할 URL

        Returns:
            dict: 스텝 데이터
        """
        display_url = "..." + url[-30:] if len(url) > 30 else url

        return {
            "name": f"[URL 확인] {display_url}",
            "type": "Browser",
            "locator": "Current URL",
            "action": "check_url",
            "value": url
        }
