
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
    print("🚀 Pre-Distribution Stability Verification (Phases 1-5)")
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
        }
    ]
    
    # ---------------------------------------------------------
    # 2. Verify Standard Script Generator (Phases 1, 2)
    # ---------------------------------------------------------
    print("\n[Testing Phase 1 & 2: Standard Script Generator]")
    script_gen = ScriptGenerator()
    script = script_gen.generate("https://example.com", mock_steps, excel_path="test.xlsx")
    
    # Check Self-Healing
    check("locators_to_try =" in script, "Self-Healing Logic Present")
    check("Primary" in script and "CSS Fallback" in script, "Fallback Locators Included")
    
    # Check Smart Wait
    check("wait_for_network_idle(driver)" in script, "Smart Wait (Network Idle) Present")
    
    # Check Safe Excel Binding
    check("class SafeData(dict):" in script, "SafeData Class Defined")
    check(".format_map(SafeData(row_data))" in script, "SafeData Used for Variable Binding")
    
    # Check Shadow DOM
    check("def find_shadow_element():" in script, "Shadow DOM Handler Present")

    # ---------------------------------------------------------
    # 3. Verify POM Generator (Phases 4, 5)
    # ---------------------------------------------------------
    print("\n[Testing Phase 4 & 5: POM & CI/CD Generator]")
    pom_gen = POMGenerator()
    output_dir = "verify_dist_output"
    
    success, msg = pom_gen.generate_project(
        output_dir,
        "https://example.com",
        mock_steps,
        excel_path="test.xlsx",
        browser_type="chrome"
    )
    
    if check(success, f"POM Project Generation ({msg})"):
        # Check Directory Structure
        check(os.path.exists(os.path.join(output_dir, "pages", "base_page.py")), "BasePage Created")
        check(os.path.exists(os.path.join(output_dir, "pages", "auto_page.py")), "AutoPage Created")
        check(os.path.exists(os.path.join(output_dir, "tests", "test_scenario.py")), "Test Script Created")
        check(os.path.exists(os.path.join(output_dir, ".github", "workflows", "main.yml")), "CI/CD Workflow Created")
        
        # Check BasePage Content (Core Logic)
        with open(os.path.join(output_dir, "pages", "base_page.py"), "r", encoding="utf-8") as f:
            base_content = f.read()
            check("def wait_for_network_idle(self" in base_content, "BasePage: Smart Wait Implemented")
            check("fallback_locators=None" in base_content, "BasePage: Self-Healing Logic Implemented")
            
        # Check AutoPage Content (Step Mapping)
        with open(os.path.join(output_dir, "pages", "auto_page.py"), "r", encoding="utf-8") as f:
            auto_content = f.read()
            check("def step_1_click(self):" in auto_content, "AutoPage: Step 1 (Click) Generated")
            check("fallback_locators=[" in auto_content, "AutoPage: Fallback Locators Passed")
            
        # Check Test Script Content (Execution Flow)
        with open(os.path.join(output_dir, "tests", "test_scenario.py"), "r", encoding="utf-8") as f:
            test_content = f.read()
            check("SafeData" in test_content, "TestScript: Safe SafeData Defined")
            check("@pytest.mark.parametrize" in test_content, "TestScript: DDT Parametrization Used")
            
    # Cleanup
    # shutil.rmtree(output_dir)

if __name__ == "__main__":
    verify_all()
