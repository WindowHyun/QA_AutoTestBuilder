"""
Playwright 테스트 스크립트 생성기 모듈

Pytest + Playwright 기반 테스트 스크립트를 생성합니다.
"""

import config
import os
import re
from typing import List, Dict, Optional, Set
from core.plugin_manager import PluginManager

class PlaywrightScriptGenerator:
    """Pytest+Playwright 테스트 스크립트 생성기"""

    def __init__(self):
        self.plugin_manager = PluginManager()
        
    SUPPORTED_ACTIONS = {
        "click", "input", "input_password", "check_text", "check_url",
        "press_key", "hover", "switch_frame", "switch_default",
        "accept_alert", "dismiss_alert", "drag_source", "drop_target",
        "comment",
        "api_get", "api_post", "api_put", "api_delete", "api_assert"
    }

    VALUE_REQUIRED_ACTIONS = {"input", "input_password", "check_text", "check_url", "press_key"}

    def generate(self, url, steps, is_headless=False, data_path=None,
                 browser_type="chrome", use_builtin_reporter=None,
                 excel_path=None) -> str:
        """Playwright용 Pytest 스크립트 코드 생성"""

        # 기본 템플릿 (pytest-playwright 픽스처 사용 방식이 아닌, sync_playwright 직접 사용)
        code = [
            "\"\"\"",
            "자동 생성된 Playwright 테스트 스크립트",
            "\"\"\"",
            "import pytest",
            "import time",
            "from playwright.sync_api import sync_playwright, expect",
            "from core.metrics import MetricsCollector",
            "import config",
            ""
        ]

        # 데이터 파일이 있으면 DDT 관련 코드 추가 (Selenium과 유사)
        is_ddt = data_path or excel_path
        code.append("import json")
        code.append("import csv")
        code.append("")

        # 테스트 함수 시작
        if is_ddt:
            code.append("# TODO: Implement DDT parametrization for Playwright")
            code.append("def test_auto_playwright():")
            code.append("    data_row = {}  # Mock data fallback")
        else:
            code.append("def test_auto_playwright():")

        # Playwright 초기화 및 브라우저 열기 코드
        code.append("    metrics = MetricsCollector()")
        code.append("    passed_ok = True")
        code.append("")
        code.append("    with sync_playwright() as p:")
        
        b_type = browser_type.lower()
        if b_type == "firefox":
            launch_code = f"p.firefox.launch(headless={is_headless})"
        elif b_type in ["safari", "webkit"]:
            launch_code = f"p.webkit.launch(headless={is_headless})"
        elif b_type == "edge":
            launch_code = f"p.chromium.launch(headless={is_headless}, channel='msedge')"
        else:
            launch_code = f"p.chromium.launch(headless={is_headless}, channel='chrome')"

        code.append(f"        browser = {launch_code}")
        code.append("        context = browser.new_context(viewport={'width': 1280, 'height': 800})")
        code.append("        page = context.new_page()")
        
        if url:
            code.append(f"        page.goto('{url}', wait_until='networkidle')")
            code.append("        ")

        # 스텝 코드 변환
        for i, step in enumerate(steps):
            action = step.get('action')
            l_type = step.get('type')
            l_value = step.get('locator')
            value = step.get('value', '')
            desc = step.get('description', '')

            # 변수 바인딩 (간이 지원)
            if is_ddt and value and "{{" in value:
                value_repr = f"f\"{value.replace('{{', '{data_row.get(').replace('}}', ', \\'\\')}')}\""
            else:
                value_repr = repr(value)
                
            code.append(f"        # Step {i+1}: {step.get('name', '')}")
            if desc:
                code.append(f"        # {desc}")
                
            start_tracker = f"        start_time = time.time()"
            code.append(start_tracker)

            try:
                if action == "comment":
                    code.append(f"        # 주석: {value}")
                elif action == "check_url":
                    code.append(f"        assert {value_repr} in page.url")
                elif action.startswith("api_"):
                    code.append("        # API 테스트는 아직 Playwright 스크립트 생성기에서 완벽히 연동되지 않음")
                    code.append("        pass")
                else:
                    # 요소가 필요한 액션
                    if l_type.lower() == "xpath":
                        play_loc = f"page.locator(f\"xpath={l_value}\")"
                    elif l_type.lower() == "css":
                        play_loc = f"page.locator({repr(l_value)})"
                    elif l_type.lower() == "id":
                        play_loc = f"page.locator(f\"#{l_value}\")"
                    elif l_type.lower() == "link text":
                        play_loc = f"page.get_by_text({repr(l_value)}, exact=True)"
                    else:
                        play_loc = f"page.locator({repr(l_value)})"

                    if action == "click":
                        code.append(f"        {play_loc}.click()")
                    elif action in ("input", "input_password"):
                        code.append(f"        {play_loc}.fill({value_repr})")
                    elif action == "press_key":
                        code.append(f"        {play_loc}.press({value_repr})")
                    elif action == "check_text":
                        code.append(f"        expect({play_loc}).to_contain_text({value_repr})")
                    elif action == "hover":
                        code.append(f"        {play_loc}.hover()")
                    else:
                        code.append(f"        # TODO: Unsupported Playwright action: {action}")
                
                # 메트릭 기록 (성공)
                code.append(f"        metrics.add_result({i}, '{step.get('name', '')}', 'passed', (time.time()-start_time)*1000)")
                
            except Exception as e:
                code.append(f"        # 스텝 변환 에러: {e}")

            code.append("")

        # 종료 처리
        code.append("        browser.close()")
        code.append("    ")
        code.append("    metrics.finalize()")
        code.append("    if not passed_ok:")
        code.append("        pytest.fail('One or more steps failed')")

        return "\n".join(code)
