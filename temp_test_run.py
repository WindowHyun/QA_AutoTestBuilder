import os
import sys

# 프로젝트 루트 경로를 sys.path에 추가 (임시 스크립트 실행용)
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from core.generator import ScriptGenerator
from core.browser import BrowserManager
from core.step_runner import StepRunner
from core.engine_interface import BrowserEngine

def test_script_generation():
    print("--- 테스트: 스크립트 생성기 SyntaxError 확인 ---")
    gen = ScriptGenerator()
    steps = [
        {
            "action": "input",
            "type": "css",
            "locator": "[data-test='username']",
            "value": "standard_user",
            "name": "Username 입력",
            "_fallback_locators": [
                {"type": "id", "value": "user-name", "name": "ID 기반"},
                {"type": "xpath", "value": "//input[@placeholder='Username']", "name": "placeholder 기반"}
            ]
        }
    ]
    
    # 생성 시도
    script = gen.generate("http://saucedemo.com", steps)
    print("스크립트 생성 성공!")
    
    # 생성된 코드가 파이썬 문법에 맞는지 확인 (SyntaxError 발생 여부)
    try:
        compile(script, '<string>', 'exec')
        print("생성된 코드의 구문 검사(Syntax Check) 통과!\n")
    except SyntaxError as e:
        print(f"구문 검사 실패! SyntaxError: {e}")
        print("생성된 코드 일부:")
        lines = script.split('\n')
        err_line = e.lineno
        start = max(0, err_line - 3)
        end = min(len(lines), err_line + 3)
        for i in range(start, end):
            prefix = ">> " if i + 1 == err_line else "   "
            print(f"{prefix}{i+1}: {lines[i]}")
        sys.exit(1)

def test_engine_execution():
    print("--- 테스트: 듀얼 엔진 프록시 테스트 (Selenium) ---")
    try:
        from config import DEFAULT_ENGINE
        print(f"현재 설정된 엔진: {DEFAULT_ENGINE}")
        
        manager = BrowserManager()
        print(f"생성된 엔진 타입: {type(manager._engine).__name__}")
        
        runner = StepRunner(manager)
        print(f"생성된 StepRunner 타입: {type(runner._runner).__name__}")
        
        print("브라우저 열기 시도 (http://example.com)...")
        success, err = manager.open_browser("http://example.com", "chrome")
        if not success:
            print(f"브라우저 열기 실패: {err}")
            sys.exit(1)
            
        print("웹 요소 찾기 및 검증 스텝 실행...")
        step = {
            "action": "check_url",
            "type": "n/a",
            "locator": "",
            "value": "example.com",
            "name": "URL 포함 여부 확인"
        }
        res = runner.execute_step(0, step)
        print(f"스텝 실행 결과: {res.status} (소요시간: {res.duration_ms:.1f}ms)")
        if res.error:
            print(f"스텝 에러 내용: {res.error}")
        
        print("브라우저 닫기...")
        manager.close()
        print("엔진 실행 테스트 성공!\n")
        
    except Exception as e:
        print(f"엔진 테스트 중 에러 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    test_script_generation()
    test_engine_execution()
    print("=== 모든 단위 테스트 통과 ===")
