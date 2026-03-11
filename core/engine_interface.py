"""
브라우저 엔진 인터페이스 모듈

Selenium과 Playwright의 API를 추상화하여
Hybrid QA(Dual Engine) 아키텍처를 지원합니다.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import config


class BrowserEngine(ABC):
    """
    브라우저 백엔드 공통 인터페이스
    """

    @property
    @abstractmethod
    def driver(self) -> object:
        """기본 브라우저 드라이버/페이지 객체 반환"""
        pass

    @property
    @abstractmethod
    def is_alive(self) -> bool:
        """브라우저가 열려있는지 여부"""
        ...

    @abstractmethod
    def open_browser(self, url: str, browser_type: str = "chrome") -> tuple[bool, str]:
        """
        브라우저 열기

        Args:
            url: 접속할 URL
            browser_type: chrome, firefox, edge

        Returns:
            (성공 여부, 에러 메시지)
        """
        ...

    @abstractmethod
    def close(self):
        """브라우저 닫기"""
        pass

    # ── Inspector Pick/Highlight API ──

    @abstractmethod
    def enable_inspector_mode(self):
        """Inspector 피커 모드 활성화 (JS 주입)"""
        pass

    @abstractmethod
    def disable_inspector_mode(self):
        """Inspector 피커 모드 비활성화"""
        pass

    @abstractmethod
    def get_picked_element_info(self) -> Optional[Dict]:
        """
        피커로 선택된 요소 정보 반환
        Returns: {tag, id, class, locator, picked, element, xpath, css...}
        """
        pass

    @abstractmethod
    def clear_picked_element(self):
        """피커 초기화"""
        pass

    @abstractmethod
    def highlight_element(self, element: object = None,
                          locator_type: Optional[str] = None,
                          locator_value: Optional[str] = None):
        """특정 요소 하이라이트 (빨간 테두리)"""
        pass
