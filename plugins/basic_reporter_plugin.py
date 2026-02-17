from core.plugin_manager import PluginManager
from core.reporter import HTMLReporter
import os
import time

# Global Reporter Instance
reporter = HTMLReporter("latest_report.html")
current_test = {}

def on_test_start(name, **kwargs):
    global current_test
    current_test = {
        "name": name,
        "start_time": time.time(),
        "log": [],
        "screenshot": None,
        "error": None
    }
    print(f"[Plugin] Test Started: {name}")

def on_log(message, **kwargs):
    if "log" in current_test:
        current_test["log"].append(str(message))

def on_step_failure(error, screenshot_path, **kwargs):
    current_test["error"] = str(error)
    current_test["screenshot"] = screenshot_path
    print(f"[Plugin] Failure Captured: {screenshot_path}")

def on_test_finish(status, **kwargs):
    if not current_test:
        return
        
    duration = time.time() - current_test.get("start_time", time.time())
    
    # Add to reporter
    reporter.add_result(
        test_name=current_test["name"],
        status=status,
        duration=duration,
        log="\n".join(current_test["log"]),
        error_msg=current_test["error"] or "",
        screenshot=current_test["screenshot"] or ""
    )
    
    # Generate partial report safely
    reporter.generate()
    print(f"[Plugin] Report Updated")
