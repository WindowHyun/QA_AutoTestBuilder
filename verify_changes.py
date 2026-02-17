
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from core.generator import ScriptGenerator

def verify_generation():
    generator = ScriptGenerator()
    
    # Mock Step Data with Fallback
    mock_steps = [
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
        {
            "name": "Username Input",
            "type": "NAME",
            "locator": "username",
            "action": "input",
            "value": "{USER_ID}",  # Excel Binding
        }
    ]
    
    print("Generating script...")
    script = generator.generate(
        url="https://example.com",
        steps=mock_steps,
        excel_path="test_data.xlsx"
    )
    
    print("\n" + "="*50)
    print(" [Generated Script Fragment] ")
    print("="*50)
    
    # Extract relevant parts
    if "locators_to_try =" in script:
        print("\n✅ Self-Healing Logic Found:")
        start = script.find("locators_to_try =")
        end = script.find("if not el:", start)
        print(script[start:end+50] + "...")
        
    if "SafeData(" in script:
        print("\n✅ Safe Excel Binding Found:")
        start = script.find("class SafeData(dict):")
        end = script.find("def __missing__(self, key):", start)
        print(script[start:end+100] + "...")

    if "wait_for_network_idle" in script:
        print("\n✅ Smart Wait Found")

if __name__ == "__main__":
    verify_generation()
