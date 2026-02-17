import os
import datetime
import html
from utils.logger import setup_logger

logger = setup_logger(__name__)

class HTMLReporter:
    """
    Lightweight Standalone HTML Reporter
    
    Generates a single-file report.html without external dependencies like Allure.
    """
    
    def __init__(self, output_file="report.html"):
        self.output_file = output_file
        self.results = []
        self.start_time = datetime.datetime.now()
        
    def add_result(self, test_name, status, duration, log="", error_msg="", screenshot=""):
        """
        Add a test execution result
        
        Args:
            test_name: Name of the test/scenario
            status: 'passed', 'failed', 'error'
            duration: Duration in seconds
            log: Captured stdout/logs
            error_msg: Error message or stacktrace
            screenshot: Path to screenshot file (relative or absolute)
        """
        self.results.append({
            "name": test_name,
            "status": status,
            "duration": duration,
            "log": log,
            "error": error_msg,
            "screenshot": screenshot,
            "timestamp": datetime.datetime.now().strftime("%H:%M:%S")
        })
        
    def generate(self):
        """Generate HTML Report File"""
        total = len(self.results)
        passed = len([r for r in self.results if r['status'] == 'passed'])
        failed = len([r for r in self.results if r['status'] == 'failed'])
        duration = datetime.datetime.now() - self.start_time
        
        # Simple CSS
        css = """
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; color: #333; }
        .header { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }
        .summary { display: flex; gap: 20px; font-weight: bold; margin-top: 10px; }
        .passed { color: #10b981; }
        .failed { color: #ef4444; }
        .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 15px; border-left: 5px solid #ccc; }
        .card.passed { border-left-color: #10b981; }
        .card.failed { border-left-color: #ef4444; }
        .card-header { display: flex; justify-content: space-between; align-items: center; cursor: pointer; }
        .badge { padding: 4px 8px; border-radius: 4px; font-size: 0.8em; text-transform: uppercase; color: white; }
        .badge.passed { background: #10b981; }
        .badge.failed { background: #ef4444; }
        .details { margin-top: 15px; border-top: 1px solid #eee; padding-top: 15px; display: none; }
        .log-box { background: #1e1e1e; color: #d4d4d4; padding: 10px; border-radius: 4px; overflow-x: auto; font-family: monospace; white-space: pre-wrap; font-size: 0.9em; }
        .screenshot-box { margin-top: 10px; }
        .screenshot-box img { max-width: 100%; border: 1px solid #ddd; border-radius: 4px; }
        """
        
        # JS for Toggle
        js = """
        function toggle(id) {
            let el = document.getElementById(id);
            el.style.display = el.style.display === 'block' ? 'none' : 'block';
        }
        """
        
        # Build HTML
        html_content = [
            f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>Test Report</title><style>{css}</style><script>{js}</script></head><body>",
            f"<div class='header'><h1>Test Run Report</h1>",
            f"<div class='summary'>",
            f"<div>Total: {total}</div>",
            f"<div class='passed'>Passed: {passed}</div>",
            f"<div class='failed'>Failed: {failed}</div>",
            f"<div>Duration: {duration}</div>",
            f"</div></div>",
            "<div class='results'>"
        ]
        
        for i, res in enumerate(self.results):
            status_class = "passed" if res['status'] == 'passed' else "failed"
            # Escape HTML content
            safe_log = html.escape(res['log'])
            safe_error = html.escape(res['error'])
            
            html_content.append(f"<div class='card {status_class}'>")
            html_content.append(f"<div class='card-header' onclick='toggle(\"details-{i}\")'>")
            html_content.append(f"<div><strong>{res['name']}</strong> <span style='color:#666; font-size:0.9em'>({res['duration']:.2f}s)</span></div>")
            html_content.append(f"<span class='badge {status_class}'>{res['status']}</span>")
            html_content.append("</div>")
            
            html_content.append(f"<div id='details-{i}' class='details'>")
            if res['error']:
                html_content.append(f"<div style='color: #ef4444; margin-bottom: 10px;'><strong>Error:</strong><br>{safe_error}</div>")
            
            if res['screenshot']:
                # Embed screenshot as base64 if needed, or link. Assuming local file for now.
                # For better portability, we'll try to use relative path.
                html_content.append(f"<div class='screenshot-box'><strong>Screenshot:</strong><br><img src='{res['screenshot']}' /></div>")

            if res['log']:
                html_content.append(f"<div class='log-box'>{safe_log}</div>")
                
            html_content.append("</div></div>")
            
        html_content.append("</div></body></html>")
        
        try:
            with open(self.output_file, "w", encoding="utf-8") as f:
                f.write("".join(html_content))
            logger.info(f"Report generated: {self.output_file}")
            return self.output_file
        except Exception as e:
            logger.error(f"Failed to generate report: {e}")
            return None
