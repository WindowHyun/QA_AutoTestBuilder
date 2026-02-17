
import sys
import os
import shutil

# Add project root to path
sys.path.append(os.getcwd())

from core.pom_generator import POMGenerator

def verify_pom_generation():
    generator = POMGenerator()
    output_dir = "test_pom_output"
    
    # Mock Step Data
    mock_steps = [
        {
            "name": "Login Button",
            "type": "ID",
            "locator": "login-btn",
            "action": "click",
            "value": "",
            "_fallback_locators": [
                {"type": "CSS", "value": "#login-btn", "description": "CSS Fallback"}
            ]
        },
        {
            "name": "Username",
            "type": "NAME",
            "locator": "username",
            "action": "input",
            "value": "testuser"
        }
    ]
    
    print(f"Generating POM project to {output_dir}...")
    success, msg = generator.generate_project(
        output_dir,
        "https://example.com",
        mock_steps
    )
    
    if success:
        print("✅ Generation Successful")
        
        # Verify File Structure
        expected_files = [
            "pages/base_page.py",
            "pages/auto_page.py",
            "tests/test_scenario.py",
            "tests/conftest.py"
        ]
        
        for f in expected_files:
            path = os.path.join(output_dir, f)
            if os.path.exists(path):
                print(f"  - Found: {f}")
                
                # Check BasePage for Smart Wait
                if "base_page.py" in f:
                    with open(path, "r", encoding="utf-8") as bf:
                        content = bf.read()
                        if "wait_for_network_idle" in content:
                            print("    ✅ Smart Wait Detected")
                        if "fallback_locators" in content:
                            print("    ✅ Self-Healing Logic Detected")
            else:
                print(f"  ❌ Missing: {f}")
                
        # Clean up
        # shutil.rmtree(output_dir) 
        print("\nVerification Complete.")
    else:
        print(f"❌ Generation Failed: {msg}")

if __name__ == "__main__":
    verify_pom_generation()
