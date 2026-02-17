
import sys
import os
import shutil

# Add project root to path
sys.path.append(os.getcwd())

from core.pom_generator import POMGenerator

def verify_ci_generation():
    generator = POMGenerator()
    output_dir = "test_ci_output"
    
    # Mock Step Data
    mock_steps = [
        {"name": "Test", "type": "ID", "locator": "test", "action": "click", "value": ""}
    ]
    
    print(f"Generating POM project with CI to {output_dir}...")
    success, msg = generator.generate_project(
        output_dir,
        "https://example.com",
        mock_steps,
        browser_type="chrome"
    )
    
    if success:
        print("✅ Generation Successful")
        
        # Verify CI Files
        ci_path = os.path.join(output_dir, ".github", "workflows", "main.yml")
        req_path = os.path.join(output_dir, "requirements.txt")
        
        if os.path.exists(ci_path):
            print(f"  ✅ Verified: {ci_path}")
            with open(ci_path, "r") as f:
                content = f.read()
                if "runs-on: ubuntu-latest" in content and "pytest" in content:
                     print("    ✅ Content looks like a valid GitHub Action")
        else:
            print(f"  ❌ Missing: {ci_path}")
            
        if os.path.exists(req_path):
            print(f"  ✅ Verified: {req_path}")
            
        # Clean up
        # shutil.rmtree(output_dir)
        print("\nCI/CD Verification Complete.")
    else:
        print(f"❌ Generation Failed: {msg}")

if __name__ == "__main__":
    verify_ci_generation()
