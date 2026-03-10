"""
Step-by-Step 실행 엔진 (Proxy/Factory)

config.yaml 의 engine 설정에 따라 SeleniumStepRunner 또는 PlaywrightStepRunner를 반환합니다.
"""

from typing import Dict, Any, List
import config
from utils.logger import setup_logger
from core.step_runner_selenium import StepResult

logger = setup_logger(__name__)

class StepRunner:
    """
    단일 스텝 실행 엔진 프록시 클래스
    엔진(Selenium/Playwright)과 상관없이 동일한 API 제공
    """
    
    def __init__(self, browser_manager):
        self._engine_type = config.DEFAULT_ENGINE
        
        if self._engine_type == "playwright":
            from core.step_runner_playwright import PlaywrightStepRunner
            self._runner = PlaywrightStepRunner(browser_manager)
            logger.info("🛠️ Playwright StepRunner 활성화")
        else:
            from core.step_runner_selenium import SeleniumStepRunner
            self._runner = SeleniumStepRunner(browser_manager)
            logger.info("🛠️ Selenium StepRunner 활성화")

    @property
    def driver(self) -> Any:
        return self._runner.driver

    def reset(self):
        """실행 상태 초기화"""
        self._runner.reset()

    def execute_step(self, step_index: int, step: Dict):
        """단일 스텝 실행"""
        return self._runner.execute_step(step_index, step)

    def execute_all(self, steps: list, callback=None):
        """모든 스텝 순차 실행"""
        return self._runner.execute_all(steps, callback)
