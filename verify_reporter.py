import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from core.generator import ScriptGenerator
import config

# Mock Data
url = "https://example.com"
steps = [
    {"name": "Check Title", "action": "check_text", "locator": "h1", "type": "TAG_NAME", "value": "Example Domain"},
    {"name": "Click Link", "action": "click", "locator": "a", "type": "TAG_NAME", "value": ""},
]

# 1. Generate Script with Built-in Reporter
print("Generating script with USE_BUILTIN_REPORTER=True...")
generator = ScriptGenerator()
script = generator.generate(url, steps, use_builtin_reporter=True)

# Verify content
if "from core.pytest_html_plugin import step" in script:
    print("PASS: Import found")
else:
    print("FAIL: Import not found")

if "with step(" in script:
    print("PASS: Step context found")
else:
    print("FAIL: Step context not found")

if "import allure" not in script:
    print("PASS: Allure import NOT found")
else:
    print("FAIL: Allure import found")

print("\nGenerated Script snippet:")
print(script[:500])
