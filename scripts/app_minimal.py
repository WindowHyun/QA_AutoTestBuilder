
import tkinter as tk
from tkinter import messagebox, filedialog, scrolledtext, ttk
import threading
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
import re
import logging
from core.browser import BrowserManager
from core.scanner import PageScanner
from core.generator import ScriptGenerator
from core.pom_generator import POMGenerator
from core.runner import TestRunner
from gui.components import StepListManager
from utils.file_manager import save_to_json, load_from_json
from utils.excel_loader import get_excel_columns
from utils.logger import setup_logger
from utils.database import TestCaseDB

# --- Modern Flat Design Colors ---
THEME = {
    'bg_main': '#F3F4F6',       # Light Gray Background
    'bg_white': '#FFFFFF',      # Card Background
    'primary': '#6366F1',       # Indigo
    'primary_hover': '#4F46E5',
    'secondary': '#E5E7EB',     # Gray 200
    'text_main': '#1F2937',     # Gray 900
    'text_sub': '#6B7280',      # Gray 500
    'accent': '#10B981',        # Emerald Green (Success)
    'danger': '#EF4444',        # Red (Error)
    'border': '#E5E7EB'
}

class FlatButton(tk.Button):
    def __init__(self, master=None, **kwargs):
        bg = kwargs.pop('bg', THEME['primary'])
        fg = kwargs.pop('fg', 'white')
        
        style = {
            'relief': tk.FLAT,
            'bd': 0,
            'padx': 15,
            'pady': 8,
            'font': ('Segoe UI', 9, 'bold'),
            'bg': bg,
            'fg': fg,
            'cursor': 'hand2',
            'activebackground': kwargs.pop('activebackground', bg), # Simple hover fix
            'activeforeground': fg
        }
        style.update(kwargs)
        super().__init__(master, **style)

class MinimalApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AutoTest Builder - Minimal")
        self.geometry("1100x750")
        self.configure(bg=THEME['bg_main'])
        
        # Resources
        self.browser = BrowserManager()
        self.scanner = PageScanner()
        self.generator = ScriptGenerator()
        self.pom_generator = POMGenerator()
        self.runner = TestRunner()
        self.db = TestCaseDB()
        self.steps_data = []
        self.excel_path = None
        
        # Setup UI
        self._init_layout()
        self._setup_logging()
        
        # Bindings
        self.bind("<F2>", lambda e: self.cmd_scan())

    def _init_layout(self):
        # 1. Top Toolbar (Global Actions)
        self._create_toolbar()
        
        # 2. Main Workspace (Split View)
        main_frame = tk.Frame(self, bg=THEME['bg_main'])
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Left: Step Editor
        self._create_editor_panel(main_frame)
        
        # Right: Tools & Info
        self._create_tools_panel(main_frame)
        
        # 3. Bottom Status/Log
        self._create_bottom_panel()

    def _create_toolbar(self):
        toolbar = tk.Frame(self, bg=THEME['bg_white'], height=60)
        toolbar.pack(fill="x", side="top")
        toolbar.pack_propagate(False)
        
        # Logo / Title
        tk.Label(toolbar, text="Builder.", font=('Segoe UI', 16, 'bold'), 
                bg=THEME['bg_white'], fg=THEME['primary']).pack(side="left", padx=20)
        
        # URL Input Area
        url_frame = tk.Frame(toolbar, bg=THEME['bg_white'])
        url_frame.pack(side="left", fill="y", padx=20)
        
        self.url_entry = tk.Entry(url_frame, width=40, font=('Segoe UI', 10), 
                                 bg=THEME['bg_main'], relief=tk.FLAT)
        self.url_entry.pack(side="left", ipady=8, pady=12)
        self.url_entry.insert(0, config.DEFAULT_URL)
        
        # Browser Control
        FlatButton(url_frame, text="Open Browser", command=self.cmd_open_browser,
                  bg=THEME['text_main'], width=12).pack(side="left", padx=5)

        # Right Side Actions
        FlatButton(toolbar, text="▶ Run Test", command=self.cmd_run,
                  bg=THEME['accent']).pack(side="right", padx=20)
        
        FlatButton(toolbar, text="📦 Export POM", command=self.cmd_export,
                  bg=THEME['primary']).pack(side="right", padx=5)

    def _create_editor_panel(self, parent):
        # Card Style for Editor
        card = tk.Frame(parent, bg=THEME['bg_white'])
        card.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # Header
        header = tk.Frame(card, bg=THEME['bg_white'])
        header.pack(fill="x", padx=15, pady=15)
        tk.Label(header, text="Test Scenario", font=('Segoe UI', 12, 'bold'),
                bg=THEME['bg_white'], fg=THEME['text_main']).pack(side="left")
        
        # Step Count
        self.lbl_count = tk.Label(header, text="0 steps", font=('Segoe UI', 9),
                                 bg=THEME['bg_white'], fg=THEME['text_sub'])
        self.lbl_count.pack(side="left", padx=10)
        
        # List Area
        list_frame = tk.Frame(card, bg="white")
        list_frame.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Canvas for scrolling
        canvas = tk.Canvas(list_frame, bg="white", highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        
        self.steps_frame = tk.Frame(canvas, bg="white")
        self.steps_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        canvas.create_window((0, 0), window=self.steps_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Manager
        self.list_manager = StepListManager(self.steps_frame, self.steps_data, None, self.cmd_highlight)

    def _create_tools_panel(self, parent):
        panel = tk.Frame(parent, bg=THEME['bg_main'], width=280)
        panel.pack(side="right", fill="y")
        panel.pack_propagate(False)
        
        # 1. Action Tools
        self._add_tool_card(panel, "Actions", [
            ("🎯 Scan Element (F2)", self.cmd_scan, THEME['primary']),
            ("✅ Verify Text", self.cmd_verify_text, THEME['secondary'], THEME['text_main']),
            ("🔗 Verify URL", self.cmd_verify_url, THEME['secondary'], THEME['text_main']),
        ])
        
        # 2. Data Tools
        self._add_tool_card(panel, "Data & File", [
            ("📁 Load Project", self.cmd_load, THEME['text_main']),
            ("💾 Save Project", self.cmd_save, THEME['text_main']),
            ("📊 Load Excel", self.cmd_excel, THEME['accent'])
        ])

    def _add_tool_card(self, parent, title, buttons):
        card = tk.Frame(parent, bg=THEME['bg_white'], pady=10)
        card.pack(fill="x", pady=(0, 15))
        
        tk.Label(card, text=title, font=('Segoe UI', 9, 'bold'),
                bg=THEME['bg_white'], fg=THEME['text_sub']).pack(anchor="w", padx=15, pady=(0, 10))
        
        for txt, cmd, bg, *fg in buttons:
            text_color = fg[0] if fg else 'white'
            FlatButton(card, text=txt, command=cmd, bg=bg, fg=text_color, width=25).pack(pady=3, padx=15)

    def _create_bottom_panel(self):
        # Collapsible Log View
        self.log_frame = tk.Frame(self, bg="#1E1E1E", height=150)
        self.log_frame.pack(fill="x", side="bottom")
        self.log_frame.pack_propagate(False)
        
        self.log_text = scrolledtext.ScrolledText(self.log_frame, bg="#1E1E1E", fg="#D4D4D4",
                                                 font=('Consolas', 9), relief=tk.FLAT)
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)

    # --- Commands ---
    def cmd_open_browser(self):
        self.browser.open_browser(self.url_entry.get())

    def cmd_scan(self):
        sel_text = self.browser.get_selected_text()
        if sel_text:
            step = self.scanner.create_text_validation_step(sel_text)
            self._add_step(step)
            return

        el = self.browser.get_selected_element()
        if not el:
            messagebox.showwarning("Warning", "Select an element first!")
            return
            
        shadow_path = None
        if self.browser.is_in_shadow_dom(el):
            shadow_path = self.browser.get_shadow_dom_path(el)

        step = self.scanner.create_step_data(el, shadow_path=shadow_path)
        self._add_step(step)
        self.browser.highlight_element(element=el)

    def cmd_verify_text(self):
        self.cmd_scan() # Reuse scan logic for text

    def cmd_verify_url(self):
        if not self.browser.driver: return
        step = self.scanner.create_url_validation_step(self.browser.driver.current_url)
        self._add_step(step)

    def _add_step(self, step):
        self.steps_data.append(step)
        self.list_manager.refresh()
        self.lbl_count.config(text=f"{len(self.steps_data)} steps")

    def cmd_highlight(self, step):
        self.browser.highlight_element(locator_type=step['type'], locator_value=step['locator'])

    def cmd_run(self):
        if not self.steps_data: return
        
        # Simple Run Logic
        script = self.generator.generate(self.url_entry.get(), self.steps_data, is_headless=False, excel_path=self.excel_path)
        with open("temp_run.py", "w", encoding="utf-8") as f: f.write(script)
        
        threading.Thread(target=self._run_thread).start()

    def _run_thread(self):
        try:
            self.log_text.insert(tk.END, "\n[INFO] Starting Test...\n")
            proc = self.runner.run_pytest()
            
            # Real-time output capturing
            while True:
                output = proc.stdout.readline()
                if output == '' and proc.poll() is not None:
                    break
                if output:
                    self.log_text.insert(tk.END, output)
                    self.log_text.see(tk.END)
            
            rc = proc.poll()
            self.log_text.insert(tk.END, f"\n[INFO] Test Finished with return code: {rc}\n")
            
            if rc == 0:
                messagebox.showinfo("Success", "Test Passed!")
            else:
                messagebox.showwarning("Finished", f"Test finished with code {rc}")
                
            # Open Report
            self.runner.open_report()
            
        except Exception as e:
            self.log_text.insert(tk.END, f"\n[ERROR] Execution Failed: {e}\n")
            messagebox.showerror("Error", f"Execution Failed: {e}")

    def cmd_export(self):
        d = filedialog.askdirectory()
        if d:
            self.pom_generator.generate_project(d, self.url_entry.get(), self.steps_data, self.excel_path)
            messagebox.showinfo("Done", "POM Project Exported!")

    def cmd_save(self):
        f = filedialog.asksaveasfilename(defaultextension=".json")
        if f: save_to_json(f, self.url_entry.get(), self.steps_data)

    def cmd_load(self):
        f = filedialog.askopenfilename()
        if f:
            u, s = load_from_json(f)
            self.url_entry.delete(0, tk.END); self.url_entry.insert(0, u)
            self.steps_data.clear(); self.steps_data.extend(s)
            self.list_manager.refresh()

    def cmd_excel(self):
        f = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx")])
        if f:
            self.excel_path = f
            messagebox.showinfo("Excel", f"Loaded: {os.path.basename(f)}")

    def _setup_logging(self):
        class TextHandler(logging.Handler):
            def __init__(self, text_widget):
                super().__init__()
                self.text_widget = text_widget

            def emit(self, record):
                msg = self.format(record) + '\n'
                def append():
                    try:
                        self.text_widget.insert(tk.END, msg)
                        self.text_widget.see(tk.END)
                    except: pass
                self.text_widget.after(0, append)

        handler = TextHandler(self.log_text)
        handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%H:%M:%S'))
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.addHandler(handler)
        root_logger.setLevel(logging.INFO)

if __name__ == "__main__":
    app = MinimalApp()
    app.mainloop()
