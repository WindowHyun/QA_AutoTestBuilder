
import sys
import os
import shutil
import re

# Add project root to path
sys.path.append(os.getcwd())

from core.generator import ScriptGenerator
from core.pom_generator import POMGenerator

def check(condition, message):
    if condition:
        print(f"✅ [PASS] {message}")
        return True
    else:
        print(f"❌ [FAIL] {message}")
        return False

def verify_all():
    print("="*60)
    print("🚀 Phase 1 Verification: POM + Explicit Wait + Self-Healing")
    print("="*60)

    # ---------------------------------------------------------
    # 1. Prepare Mock Data (Complex Scenario)
    # ---------------------------------------------------------
    mock_steps = [
        # Case 1: Standard Element with Fallback
        {
            "name": "Login Button",
            "type": "ID",
            "locator": "login-btn",
            "action": "click",
            "value": "",
            "_fallback_locators": [
                {"type": "CSS", "value": "#login-btn", "description": "CSS Fallback"},
                {"type": "XPATH", "value": "//button[@id='login-btn']", "description": "XPath Fallback"}
            ]
        },
        # Case 2: Input with Excel Variable
        {
            "name": "Username",
            "type": "NAME",
            "locator": "username",
            "action": "input",
            "value": "{USER_ID}", 
        },
        # Case 3: Shadow DOM Element
        {
            "name": "Shadow Button",
            "type": "CSS",
            "locator": "#shadow-btn",
            "action": "click",
            "value": "",
            "_shadow_path": ["#host", "#root"]
        },
        # Case 4: Comment
        {
            "name": "Step Comment",
            "type": "XPATH",
            "locator": "",
            "action": "comment",
            "value": ""
        }
    ]
    
    passed = 0
    failed = 0
    
    def track(result):
        nonlocal passed, failed
        if result:
            passed += 1
        else:
            failed += 1

    # ---------------------------------------------------------
    # 2. Verify Standard Script Generator
    # ---------------------------------------------------------
    print("\n" + "="*60)
    print("[Phase 1] Standard Script Generator")
    print("="*60)
    script_gen = ScriptGenerator()
    script = script_gen.generate("https://example.com", mock_steps, excel_path="test.xlsx")
    
    # Check time.sleep REMOVED
    track(check("time.sleep" not in script, "time.sleep 완전 제거"))
    track(check("import time" not in script, "import time 제거"))
    
    # Check Explicit Wait present
    track(check("WebDriverWait" in script, "WebDriverWait 사용"))
    
    # Check Self-Healing
    track(check("locators_to_try =" in script, "Self-Healing 다중 로케이터 순회"))
    track(check("Primary" in script and "CSS Fallback" in script, "Fallback 로케이터 포함"))
    
    # Check Smart Wait
    track(check("wait_for_network_idle(driver)" in script, "Smart Wait 네트워크 유휴 대기"))
    
    # Check Retry decorator
    track(check("retry_on_failure" in script, "retry_on_failure 데코레이터 존재"))
    track(check("@retry_on_failure" in script, "@retry_on_failure 데코레이터 적용"))
    
    # Check Screenshot on failure
    track(check("take_screenshot" in script, "take_screenshot 함수 존재"))
    track(check("SCREENSHOT_DIR" in script, "스크린샷 디렉토리 설정"))
    
    # Check Safe Excel Binding
    track(check("class SafeData(dict):" in script, "SafeData 클래스 정의"))
    track(check(".format_map(SafeData(row_data))" in script, "SafeData 변수 바인딩"))
    
    # Check Shadow DOM (no time.sleep)
    track(check("def find_shadow_element():" in script, "Shadow DOM 핸들러 존재"))

    # ---------------------------------------------------------
    # 3. Verify POM Generator
    # ---------------------------------------------------------
    print("\n" + "="*60)
    print("[Phase 1] POM Generator")
    print("="*60)
    pom_gen = POMGenerator()
    output_dir = "verify_dist_output"
    
    success, msg = pom_gen.generate_project(
        output_dir,
        "https://example.com",
        mock_steps,
        excel_path="test.xlsx",
        browser_type="chrome"
    )
    
    if check(success, f"POM 프로젝트 생성 ({msg})"):
        passed += 1
        
        # Check Directory Structure
        track(check(os.path.exists(os.path.join(output_dir, "pages", "base_page.py")), "BasePage 파일 생성"))
        track(check(os.path.exists(os.path.join(output_dir, "pages", "auto_page.py")), "AutoPage 파일 생성"))
        track(check(os.path.exists(os.path.join(output_dir, "tests", "test_scenario.py")), "테스트 스크립트 생성"))
        track(check(os.path.exists(os.path.join(output_dir, "tests", "conftest.py")), "conftest.py 생성"))
        track(check(os.path.exists(os.path.join(output_dir, ".github", "workflows", "main.yml")), "CI/CD Workflow 생성"))
        
        # ----- BasePage Content -----
        with open(os.path.join(output_dir, "pages", "base_page.py"), "r", encoding="utf-8") as f:
            base_content = f.read()
            
            # Explicit Wait (no time.sleep)
            track(check("time.sleep" not in base_content, "BasePage: time.sleep 미사용"))
            track(check("import time" not in base_content, "BasePage: import time 미사용"))
            track(check("WebDriverWait" in base_content, "BasePage: WebDriverWait 사용"))
            
            # Smart Wait
            track(check("def wait_for_network_idle(self" in base_content, "BasePage: wait_for_network_idle 메서드"))
            track(check("def wait_for_page_load(self" in base_content, "BasePage: wait_for_page_load 메서드"))
            
            # Self-Healing
            track(check("fallback_locators" in base_content, "BasePage: Self-Healing 지원"))
            track(check("Self-Healing" in base_content, "BasePage: Self-Healing 로깅"))
            
            # Screenshot
            track(check("def take_screenshot(self" in base_content, "BasePage: take_screenshot 메서드"))
            track(check("SCREENSHOT_DIR" in base_content, "BasePage: 스크린샷 디렉토리 설정"))
            
            # Shadow DOM (no time.sleep)
            track(check("def _find_shadow_element(self" in base_content, "BasePage: Shadow DOM 핸들러"))
            
            # Action methods
            track(check("def click(self" in base_content, "BasePage: click 메서드"))
            track(check("def type_text(self" in base_content, "BasePage: type_text 메서드"))
            track(check("def hover(self" in base_content, "BasePage: hover 메서드"))
            track(check("def press_key(self" in base_content, "BasePage: press_key 메서드"))
            track(check("def check_text(self" in base_content, "BasePage: check_text 메서드"))
            track(check("def accept_alert(self" in base_content, "BasePage: accept_alert 메서드"))

        # ----- conftest.py Content -----
        with open(os.path.join(output_dir, "tests", "conftest.py"), "r", encoding="utf-8") as f:
            conftest_content = f.read()
            
            # Retry Hook
            track(check("pytest_runtest_makereport" in conftest_content, "conftest: pytest 실패 감지 훅"))
            track(check("MAX_RETRIES" in conftest_content, "conftest: 최대 재시도 설정"))
            track(check("flaky" in conftest_content or "reruns" in conftest_content, "conftest: 재시도 마커"))
            
            # Screenshot on failure
            track(check("save_screenshot" in conftest_content, "conftest: 실패 시 스크린샷 저장"))
            track(check("FAIL_" in conftest_content, "conftest: 실패 스크린샷 파일명"))
            track(check("SCREENSHOT_DIR" in conftest_content, "conftest: 스크린샷 디렉토리"))

        # ----- AutoPage Content -----
        with open(os.path.join(output_dir, "pages", "auto_page.py"), "r", encoding="utf-8") as f:
            auto_content = f.read()
            track(check("class AutoPage(BasePage):" in auto_content, "AutoPage: BasePage 상속"))
            track(check("def step_1_click(self):" in auto_content, "AutoPage: step_1 (Click) 생성"))
            track(check("fallback_locators=[" in auto_content, "AutoPage: Fallback 로케이터 전달"))

        # ----- Test Script Content -----
        with open(os.path.join(output_dir, "tests", "test_scenario.py"), "r", encoding="utf-8") as f:
            test_content = f.read()
            track(check("SafeData" in test_content, "TestScript: SafeData 정의"))
            track(check("@pytest.mark.parametrize" in test_content, "TestScript: DDT 매개변수화"))
    else:
        failed += 1

    # ---------------------------------------------------------
    # 4. Config Verification
    # ---------------------------------------------------------
    print("\n" + "="*60)
    print("[Phase 1] Config 설정 검증")
    print("="*60)
    
    import config
    track(check(hasattr(config, "RETRY_COUNT"), "config: RETRY_COUNT 존재"))
    track(check(hasattr(config, "SCREENSHOT_DIR"), "config: SCREENSHOT_DIR 존재"))
    track(check(config.RETRY_COUNT >= 1, f"config: RETRY_COUNT = {config.RETRY_COUNT}"))
    track(check("screenshots" in config.SCREENSHOT_DIR, f"config: SCREENSHOT_DIR 경로 설정"))

    # ---------------------------------------------------------
    # Summary
    # ---------------------------------------------------------
    print("\n" + "="*60)
    total = passed + failed
    print(f"📊 결과: {passed}/{total} PASSED, {failed}/{total} FAILED")
    if failed == 0:
        print("🎉 모든 검증 통과!")
    else:
        print(f"⚠️  {failed}개 항목 실패!")
    print("="*60)

if __name__ == "__main__":
    verify_all()
