"""
테스트 스크립트 생성기 모듈 (Proxy/Factory)

config.yaml 의 engine 설정에 따라 SeleniumScriptGenerator 또는 PlaywrightScriptGenerator를 반환합니다.
"""

from typing import List, Dict, Optional, Set
import config
from utils.logger import setup_logger

logger = setup_logger(__name__)

class ScriptGenerator:
    """
    테스트 스크립트 생성기 프록시 클래스
    엔진(Selenium/Playwright)과 상관없이 동일한 API 제공
    """
    
    def __init__(self):
        self._engine_type = config.DEFAULT_ENGINE
        
        if self._engine_type == "playwright":
            from core.generator_playwright import PlaywrightScriptGenerator
            self._generator = PlaywrightScriptGenerator()
        else:
            from core.generator_selenium import SeleniumScriptGenerator
            self._generator = SeleniumScriptGenerator()

    @property
    def SUPPORTED_ACTIONS(self):
        return self._generator.SUPPORTED_ACTIONS

    @property
    def VALUE_REQUIRED_ACTIONS(self):
        return self._generator.VALUE_REQUIRED_ACTIONS

    def get_used_variables(self, steps: List[Dict]) -> Set[str]:
        if hasattr(self._generator, 'get_used_variables'):
            return self._generator.get_used_variables(steps)
        # 기본 추출 로직
        import re
        variables = set()
        for step in steps:
            val = step.get("value", "")
            matches = re.findall(r"\{\{([^}]+)\}\}", val)
            variables.update(matches)
        return variables

    def validate_steps(self, steps: List[Dict], excel_columns: Optional[List[str]] = None) -> List[str]:
        if hasattr(self._generator, 'validate_steps'):
            return self._generator.validate_steps(steps, excel_columns)
        return []

    def generate(self, url, steps, is_headless=False, data_path=None,
                 browser_type="chrome", use_builtin_reporter=None,
                 excel_path=None) -> str:
        """
        엔진에 맞는 Pytest 스크립트 생성
        """
        return self._generator.generate(
            url, steps, is_headless, data_path, browser_type, use_builtin_reporter, excel_path
        )