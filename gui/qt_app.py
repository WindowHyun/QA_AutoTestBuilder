import sys
import os
import threading
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QTableView, QHeaderView, QLineEdit, QLabel,
    QMessageBox, QFileDialog, QSplitter, QFrame, QPlainTextEdit,
    QProgressBar, QSystemTrayIcon, QMenu, QComboBox, QPushButton,
    QAbstractItemView
)
from PySide6.QtCore import Qt, QThread, Signal, Slot, QSize, QTimer
from PySide6.QtGui import QIcon, QFont, QAction, QColor, QPalette

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from core.browser import BrowserManager
from core.scanner import PageScanner
from core.generator import ScriptGenerator
from core.pom_generator import POMGenerator
from core.runner import TestRunner
from utils.file_manager import save_to_json, load_from_json
from utils.database import TestCaseDB
import pandas as pd
from gui.qt_components import StepTableModel, ActionDelegate, ModernButton, COLORS
from gui.data_model import DataFrameModel
from core.data_loader import DataLoader

# --- Worker Threads (Optimizations) ---
class BrowserThread(QThread):
    finished = Signal(bool, str)

    def __init__(self, browser_manager, url, browser_type="chrome"):
        super().__init__()
        self.browser = browser_manager
        self.url = url
        self.type = browser_type

    def run(self):
        try:
            success, msg = self.browser.open_browser(self.url, browser_type=self.type)
            self.finished.emit(success, msg)
        except Exception as e:
            self.finished.emit(False, str(e))

from core.plugin_manager import PluginManager

class RunnerThread(QThread):
    log_signal = Signal(str)
    finished = Signal(int)

    def __init__(self, runner, script_path):
        super().__init__()
        self.runner = runner
        self.script_path = script_path
        self._stop_event = threading.Event()
        self.plugin_manager = PluginManager()

    def run(self):
        try:
            self.log_signal.emit("[INFO] Starting Test Execution...\n")
            
            # Plugin Hook: Start
            self.plugin_manager.hook("on_test_start", name="Automated Scenario")
            
            proc = self.runner.run_pytest() 
            
            # Simple output capture
            # Non-blocking read loop
            while True:
                if self._stop_event.is_set():
                    proc.terminate()
                    break
                
                output = proc.stdout.readline()
                if output == '' and proc.poll() is not None:
                    break
                
                if output:
                    msg = output.strip()
                    self.log_signal.emit(msg)
                    # Plugin Hook: Log
                    self.plugin_manager.hook("on_log", message=msg)
                    
                    # Basic Failure Detection (heuristic)
                    if "FAILED" in msg or "Error:" in msg:
                        self.plugin_manager.hook("on_step_failure", error=msg, screenshot_path="")
            
            proc.wait()
            
            # Plugin Hook: Finish
            status = "passed" if proc.returncode == 0 else "failed"
            self.plugin_manager.hook("on_test_finish", status=status)
            
            # --- Auto Open Report ---
            self.log_signal.emit("\n[INFO] Generating Report...\n")
            try:
                import subprocess
                import webbrowser
                
                # 1. Clean previous report and generate new one
                # shell=True required for Windows to find executable in PATH sometimes
                gen_cmd = ["allure", "generate", "allure_results", "--clean", "-o", "allure-report"]
                subprocess.run(gen_cmd, shell=True, check=True)
                
                # 2. Serve and Open
                report_path = os.path.abspath("allure-report")
                port = serve_report(report_path)
                url = f"http://localhost:{port}"
                
                self.log_signal.emit(f"[INFO] Opening report: {url}\n")
                webbrowser.open(url)
                
            except Exception as e:
                self.log_signal.emit(f"[WARN] Failed to open report: {e}\n")

            self.finished.emit(proc.returncode)
        except Exception as e:
            self.log_signal.emit(f"[ERROR] {str(e)}\n")
            self.finished.emit(-1)

    def stop(self):
        self._stop_event.set()

def serve_report(report_dir):
    import http.server
    import socketserver
    import socket
    
    # 1. Find free port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        port = s.getsockname()[1]
        
    # 2. Handler to serve directory
    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=report_dir, **kwargs)
        
        # Suppress log
        def log_message(self, format, *args):
            pass
            
    # 3. Start Server in Thread
    def run_server():
        with socketserver.TCPServer(("", port), Handler) as httpd:
            httpd.serve_forever()
            
    t = threading.Thread(target=run_server, daemon=True)
    t.start()
    return port

class AutoTestAppQt(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🚀 QA Auto Test Builder v7.0 Pro")
        self.resize(1280, 850)
        
        # Resources
        self.browser = BrowserManager()
        self.scanner = PageScanner()
        self.generator = ScriptGenerator()
        self.pom_generator = POMGenerator()
        self.runner = TestRunner()
        self.db = TestCaseDB()
        self.steps_data = [] # List[Dict] shared with model
        self.data_path = None  # DDT 데이터 파일 경로 (JSON/CSV/Excel)
        
        # UI Setup
        self._setup_theme()
        self._init_ui()
        
        # Load Status
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")

    def _setup_theme(self):
        """다크 테마 적용"""
        app = QApplication.instance()
        app.setStyle("Fusion")
        
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(COLORS['background']))
        palette.setColor(QPalette.WindowText, QColor(COLORS['text']))
        palette.setColor(QPalette.Base, QColor(COLORS['surface']))
        palette.setColor(QPalette.AlternateBase, QColor(COLORS['background']))
        palette.setColor(QPalette.ToolTipBase, QColor(COLORS['text']))
        palette.setColor(QPalette.ToolTipText, QColor(COLORS['surface']))
        palette.setColor(QPalette.Text, QColor(COLORS['text']))
        palette.setColor(QPalette.Button, QColor(COLORS['surface']))
        palette.setColor(QPalette.ButtonText, QColor(COLORS['text']))
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.Link, QColor(COLORS['primary']))
        palette.setColor(QPalette.Highlight, QColor(COLORS['primary']))
        palette.setColor(QPalette.HighlightedText, Qt.white)
        
        app.setPalette(palette)
        
        # Global Stylesheet for specifics
        app.setStyleSheet(f"""
            QTabWidget::pane {{ border: 1px solid {COLORS['border']}; background: {COLORS['surface']}; }}
            QTabBar::tab {{ background: {COLORS['background']}; color: {COLORS['text_secondary']}; padding: 10px 20px; }}
            QTabBar::tab:selected {{ background: {COLORS['surface']}; color: {COLORS['primary']}; border-bottom: 2px solid {COLORS['primary']}; }}
            QLineEdit {{ background: {COLORS['input_bg']}; color: {COLORS['text']}; border: 1px solid {COLORS['border']}; padding: 5px; border-radius: 4px; }}
            QComboBox {{ background: {COLORS['input_bg']}; color: {COLORS['text']}; border: 1px solid {COLORS['border']}; padding: 5px; border-radius: 4px; }}
            QTableView {{ background: {COLORS['surface']}; gridline-color: {COLORS['border']}; selection-background-color: {COLORS['primary_hover']}; }}
            QHeaderView::section {{ background-color: {COLORS['background']}; color: {COLORS['text']}; padding: 5px; border: none; }}
        """)

    def _init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Header
        header = QFrame()
        header.setFixedHeight(60)
        header.setStyleSheet(f"background-color: {COLORS['surface']}; border-bottom: 1px solid {COLORS['border']};")
        header_layout = QHBoxLayout(header)
        
        title = QLabel("🚀 QA Auto Test Builder")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {COLORS['text']};")
        subtitle = QLabel("No-Code Automation Platform")
        subtitle.setStyleSheet(f"font-size: 12px; color: {COLORS['text_secondary']}; margin-left: 10px;")
        
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        header_layout.addStretch()
        
        # Header Actions
        btn_pom = ModernButton("📦 POM 내보내기", COLORS['secondary'])
        btn_pom.clicked.connect(self.cmd_export_pom)
        header_layout.addWidget(btn_pom)
        
        main_layout.addWidget(header)

        # 2. Main Content (Tabs)
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        self.tab_scenario = QWidget()
        self.tab_execution = QWidget()
        self.tab_data = QWidget()
        
        self.tabs.addTab(self.tab_scenario, "🎯 Scenario Design")
        self.tabs.addTab(self.tab_execution, "▶ Execution & Logs")
        self.tabs.addTab(self.tab_data, "📊 Data Management")
        
        self._setup_scenario_tab()
        self._setup_execution_tab()
        self._setup_data_tab()

    def _setup_scenario_tab(self):
        layout = QHBoxLayout(self.tab_scenario)
        
        # Left Panel (Controls)
        left_panel = QFrame()
        left_panel.setFixedWidth(350)
        left_panel.setStyleSheet(f"background-color: {COLORS['surface']}; border-right: 1px solid {COLORS['border']};")
        left_layout = QVBoxLayout(left_panel)
        
        # Browser Control
        grp_browser = self._create_group("🌐 Browser Setup")
        
        self.url_input = QLineEdit(config.DEFAULT_URL)
        self.url_input.setPlaceholderText("https://example.com")
        grp_browser.layout().addWidget(QLabel("Target URL:"))
        grp_browser.layout().addWidget(self.url_input)
        
        hbox = QHBoxLayout()
        self.browser_combo = QComboBox()
        self.browser_combo.addItems(["Chrome", "Firefox", "Edge"])
        hbox.addWidget(self.browser_combo)
        
        btn_open = ModernButton("브라우저 열기", COLORS['primary'])
        btn_open.clicked.connect(self.cmd_open_browser)
        hbox.addWidget(btn_open)
        grp_browser.layout().addLayout(hbox)
        
        left_layout.addWidget(grp_browser)
        
        # Scanning Tools
        grp_scan = self._create_group("🎯 Scanning Tools")
        
        btn_scan = ModernButton("요소 스캔 (F2)", COLORS['accent'])
        btn_scan.clicked.connect(self.cmd_scan_element)
        btn_scan.setShortcut("F2") # Shortcut binding
        grp_scan.layout().addWidget(btn_scan)
        
        btn_url = ModernButton("URL 검증 추가", COLORS['secondary'])
        btn_url.clicked.connect(self.cmd_add_url_check)
        grp_scan.layout().addWidget(btn_url)
        
        left_layout.addWidget(grp_scan)
        
        # File Actions
        grp_file = self._create_group("📁 File Actions")
        hbox_file = QHBoxLayout()
        btn_load = ModernButton("불러오기")
        btn_load.clicked.connect(self.cmd_load)
        btn_save = ModernButton("저장하기")
        btn_save.clicked.connect(self.cmd_save)
        hbox_file.addWidget(btn_load)
        hbox_file.addWidget(btn_save)
        grp_file.layout().addLayout(hbox_file)
        
        left_layout.addWidget(grp_file)
        left_layout.addStretch()
        
        layout.addWidget(left_panel)
        
        # Right Panel (Table)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("📋 Test Steps"))
        toolbar.addStretch()
        
        btn_del = ModernButton("삭제", COLORS['danger'])
        btn_del.clicked.connect(self.cmd_delete_step)
        toolbar.addWidget(btn_del)
        
        btn_up = ModernButton("위로 이동", COLORS['secondary'])
        btn_up.setFixedWidth(80)
        btn_up.clicked.connect(lambda: self.cmd_move_step(-1))
        toolbar.addWidget(btn_up)
        
        btn_down = ModernButton("아래로 이동", COLORS['secondary'])
        btn_down.setFixedWidth(90)
        btn_down.clicked.connect(lambda: self.cmd_move_step(1))
        toolbar.addWidget(btn_down)
        
        right_layout.addLayout(toolbar)
        
        # Table
        self.step_model = StepTableModel(self.steps_data)
        self.table_view = QTableView()
        self.table_view.setModel(self.step_model)
        self.table_view.setItemDelegate(ActionDelegate(self.table_view))
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table_view.horizontalHeader().setStretchLastSection(True)
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_view.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table_view.setColumnWidth(0, 40) # No
        self.table_view.setColumnWidth(1, 150) # Name
        self.table_view.setColumnWidth(2, 100) # Action
        self.table_view.setColumnWidth(3, 150) # Value
        
        # 하이라이트 연결 (Selection Changed)
        self.table_view.selectionModel().selectionChanged.connect(self.on_table_selection_changed)
        
        right_layout.addWidget(self.table_view)
        
        layout.addWidget(right_panel)

    def _setup_execution_tab(self):
        layout = QVBoxLayout(self.tab_execution)
        
        # Controls
        controls = QFrame()
        controls.setStyleSheet(f"background-color: {COLORS['surface']}; padding: 10px; border-radius: 8px;")
        hbox = QHBoxLayout(controls)
        
        btn_run = ModernButton("▶ 테스트 시작", COLORS['accent'])
        btn_run.clicked.connect(self.cmd_run_test)
        hbox.addWidget(btn_run)
        
        btn_stop = ModernButton("⏹ 정지", COLORS['danger'])
        hbox.addWidget(btn_stop)
        hbox.addStretch()
        
        layout.addWidget(controls)
        
        # Log View
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setStyleSheet(f"background-color: #000; color: #0F0; font-family: Consolas;")
        layout.addWidget(self.log_view)
        
        # Progress
        self.progress = QProgressBar()
        self.progress.setStyleSheet(f"QProgressBar::chunk {{ background-color: {COLORS['primary']}; }}")
        layout.addWidget(self.progress)

    def _setup_data_tab(self):
        layout = QVBoxLayout(self.tab_data)
        
        # Data Load Card
        card = QFrame()
        card.setStyleSheet(f"background-color: {COLORS['surface']}; padding: 15px; border-radius: 8px;")
        vbox = QVBoxLayout(card)
        
        lbl_title = QLabel("📊 Data-Driven Testing (DDT)")
        lbl_title.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {COLORS['primary']};")
        vbox.addWidget(lbl_title)
        
        lbl_desc = QLabel("Load a JSON, CSV, or Excel file to parameterize your test values.\nUse {ColumnName} in the 'Value' field of your test steps.")
        lbl_desc.setStyleSheet(f"color: {COLORS['text_secondary']}; margin-bottom: 10px;")
        vbox.addWidget(lbl_desc)
        
        hbox = QHBoxLayout()
        self.btn_data = ModernButton("데이터 파일 로드", COLORS['accent'])
        self.btn_data.clicked.connect(self.cmd_load_data)
        hbox.addWidget(self.btn_data)
        
        self.lbl_data_status = QLabel("No file loaded")
        self.lbl_data_status.setStyleSheet(f"color: {COLORS['text_secondary']}; margin-left: 10px;")
        hbox.addWidget(self.lbl_data_status)
        hbox.addStretch()
        
        vbox.addLayout(hbox)
        layout.addWidget(card)
        
        # DataFrame Viewer
        self.df_model = DataFrameModel()
        self.df_view = QTableView()
        self.df_view.setModel(self.df_model)
        self.df_view.setStyleSheet(f"background-color: {COLORS['surface']}; gridline-color: {COLORS['border']};")
        self.df_view.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        layout.addWidget(self.df_view)

        # Edit Tools
        hbox_tools = QHBoxLayout()
        btn_add_row = ModernButton("행 추가 (+)", COLORS['secondary'])
        btn_del_row = ModernButton("행 삭제 (-)", COLORS['danger'])
        btn_add_col = ModernButton("열 추가 (+)", COLORS['secondary'])
        btn_del_col = ModernButton("열 삭제 (-)", COLORS['danger'])

        btn_add_row.clicked.connect(self.cmd_add_row)
        btn_del_row.clicked.connect(self.cmd_del_row)
        btn_add_col.clicked.connect(self.cmd_add_col)
        btn_del_col.clicked.connect(self.cmd_del_col)

        hbox_tools.addWidget(btn_add_row)
        hbox_tools.addWidget(btn_del_row)
        hbox_tools.addWidget(btn_add_col)
        hbox_tools.addWidget(btn_del_col)
        hbox_tools.addStretch()
        layout.addLayout(hbox_tools)
        
        # Save Button
        hbox_save = QHBoxLayout()
        hbox_save.addStretch()
        btn_save_data = ModernButton("변경사항 저장", COLORS['primary'])
        btn_save_data.clicked.connect(self.cmd_save_data)
        hbox_save.addWidget(btn_save_data)
        layout.addLayout(hbox_save)

    @Slot()
    def cmd_load_data(self):
        """JSON/CSV/Excel 데이터 파일 로드"""
        fname, _ = QFileDialog.getOpenFileName(
            self, "Select Data File", "",
            "Data Files (*.json *.csv *.xlsx *.xls);;JSON Files (*.json);;CSV Files (*.csv);;Excel Files (*.xlsx *.xls)"
        )
        if fname:
            try:
                self.data_path = fname
                ext = os.path.splitext(fname)[1].lower()
                
                if ext == '.json':
                    import json
                    with open(fname, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    if isinstance(data, dict):
                        for key in ('test_cases', 'data', 'rows', 'cases'):
                            if key in data and isinstance(data[key], list):
                                data = data[key]
                                break
                        else:
                            data = [data]
                    df = pd.DataFrame(data)
                elif ext == '.csv':
                    df = pd.read_csv(fname, encoding='utf-8-sig')
                else:
                    df = pd.read_excel(fname)
                
                df = df.fillna('')
                self.df_model.set_dataframe(df)
                
                fmt_label = ext.lstrip('.').upper()
                self.lbl_data_status.setText(f"Loaded [{fmt_label}]: {os.path.basename(fname)}")
                self.lbl_data_status.setStyleSheet(f"color: #10B981; margin-left: 10px;")
                self.status_bar.showMessage(f"Data loaded: {fname}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load data file: {e}")

    @Slot()
    def cmd_save_data(self):
        """데이터 파일 저장 (JSON/CSV/Excel)"""
        if not self.data_path:
            # 새 파일로 저장
            fname, _ = QFileDialog.getSaveFileName(
                self, "Save Data File", "",
                "JSON Files (*.json);;CSV Files (*.csv);;Excel Files (*.xlsx)"
            )
            if not fname:
                return
            self.data_path = fname

        try:
            df = self.df_model.get_dataframe()
            ext = os.path.splitext(self.data_path)[1].lower()
            
            if ext == '.json':
                import json
                records = df.to_dict(orient='records')
                with open(self.data_path, 'w', encoding='utf-8') as f:
                    json.dump(records, f, ensure_ascii=False, indent=4)
            elif ext == '.csv':
                df.to_csv(self.data_path, index=False, encoding='utf-8-sig')
            else:
                df.to_excel(self.data_path, index=False)
            
            QMessageBox.information(self, "Success", f"Data saved: {os.path.basename(self.data_path)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save data: {e}")

    @Slot()
    def cmd_add_row(self):
        # 현재 선택된 행 위치 가져오기 (없으면 마지막)
        idx = self.df_view.currentIndex()
        row = idx.row() if idx.isValid() else self.df_model.rowCount()
        # insertRows(position, count, parent)
        self.df_model.insertRows(row + 1 if idx.isValid() else row, 1)

    @Slot()
    def cmd_del_row(self):
        idx = self.df_view.currentIndex()
        if idx.isValid():
            self.df_model.removeRows(idx.row(), 1)

    @Slot()
    def cmd_add_col(self):
        idx = self.df_view.currentIndex()
        col = idx.column() if idx.isValid() else self.df_model.columnCount()
        self.df_model.insertColumns(col + 1 if idx.isValid() else col, 1)

    @Slot()
    def cmd_del_col(self):
        idx = self.df_view.currentIndex()
        if idx.isValid():
            self.df_model.removeColumns(idx.column(), 1)

    def _create_group(self, title):
        group = QFrame()
        group.setStyleSheet(f"background-color: {COLORS['background']}; border-radius: 6px; padding: 10px;")
        vbox = QVBoxLayout(group)
        lbl = QLabel(title)
        lbl.setStyleSheet(f"font-weight: bold; color: {COLORS['primary']}; margin-bottom: 5px;")
        vbox.addWidget(lbl)
        return group

    # --- Actions ---
    @Slot()
    def cmd_open_browser(self):
        url = self.url_input.text()
        b_type = self.browser_combo.currentText().lower()
        
        self.status_bar.showMessage(f"Opening {b_type}...")
        
        # Threaded
        self.browser_thread = BrowserThread(self.browser, url, b_type)
        self.browser_thread.finished.connect(self._on_browser_opened)
        self.browser_thread.start()
        
        # Disable button temporarily
        self.sender().setEnabled(False)
        self._temp_btn = self.sender()

    @Slot(bool, str)
    def _on_browser_opened(self, success, msg):
        self._temp_btn.setEnabled(True)
        if success:
            self.status_bar.showMessage("Browser Ready", 5000)
            QMessageBox.information(self, "Success", msg)
        else:
            self.status_bar.showMessage("Browser Failed")
            QMessageBox.critical(self, "Error", msg)

    @Slot()
    def cmd_scan_element(self):
        try:
            # 1. 텍스트 확인
            sel_text = self.browser.get_selected_text()
            if sel_text:
                step = self.scanner.create_text_validation_step(sel_text)
                self.step_model.add_step(step)
                self.status_bar.showMessage("Text verification added")
                return

            # 2. 요소 확인
            el = self.browser.get_selected_element()
            if not el:
                QMessageBox.warning(self, "Warning", "Select an element in the browser first!")
                return
            
            shadow_path = None
            if self.browser.is_in_shadow_dom(el):
                shadow_path = self.browser.get_shadow_dom_path(el)
            
            step = self.scanner.create_step_data(el, shadow_path=shadow_path)
            self.step_model.add_step(step)
            
            # Highlight
            self.browser.highlight_element(element=el)
            self.status_bar.showMessage("Element added")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Scan failed: {e}")

    @Slot()
    def cmd_add_url_check(self):
        if self.browser.driver:
            current = self.browser.driver.current_url
            step = self.scanner.create_url_validation_step(current)
            self.step_model.add_step(step)
            self.status_bar.showMessage("URL check added")

    @Slot()
    def cmd_delete_step(self):
        idx = self.table_view.currentIndex()
        if idx.isValid():
            self.step_model.remove_step(idx.row())

    @Slot()
    def cmd_move_step(self, direction):
        idx = self.table_view.currentIndex()
        if idx.isValid():
            row = idx.row()
            if self.step_model.move_step(row, direction):
                new_idx = self.step_model.index(row + direction, 0)
                self.table_view.setCurrentIndex(new_idx)

    @Slot()
    def on_table_selection_changed(self, selected, deselected):
        indexes = selected.indexes()
        if indexes:
            row = indexes[0].row()
            step = self.step_model.get_step(row)
            if step:
                # Highlight in browser
                # (Simple check to avoid error if browser closed)
                if self.browser.driver:
                   try:
                       self.browser.highlight_element(
                           locator_type=step['type'],
                           locator_value=step['locator']
                       )
                   except:
                       pass

    @Slot()
    def cmd_save(self):
        fname, _ = QFileDialog.getSaveFileName(self, "Save Scenario", "", "JSON Files (*.json)")
        if fname:
            save_to_json(fname, self.url_input.text(), self.steps_data)
            self.status_bar.showMessage(f"Saved to {fname}")

    @Slot()
    def cmd_load(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Load Scenario", "", "JSON Files (*.json)")
        if fname:
            url, steps = load_from_json(fname)
            self.url_input.setText(url)
            self.step_model.clear()
            for s in steps:
                self.step_model.add_step(s)
            self.status_bar.showMessage(f"Loaded {fname}")

    @Slot()
    def cmd_export_pom(self):
        dname = QFileDialog.getExistingDirectory(self, "Select Export Directory")
        if dname:
            try:
                success, msg = self.pom_generator.generate_project(
                    dname, self.url_input.text(), self.steps_data,
                    data_path=self.data_path,
                    browser_type=self.browser_combo.currentText().lower()
                )
                if success:
                    QMessageBox.information(self, "Success", f"Project exported to:\n{dname}")
                else:
                    QMessageBox.warning(self, "Failed", msg)
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    @Slot()
    def cmd_run_test(self):
        # 1. Generate Script
        script = self.generator.generate(
            self.url_input.text(), self.steps_data, False,
            data_path=self.data_path,
            browser_type=self.browser_combo.currentText().lower()
        )
        with open("temp_run.py", "w", encoding="utf-8") as f:
            f.write(script)
        
        # 2. Run in Thread
        self.tabs.setCurrentWidget(self.tab_execution)
        self.log_view.clear()
        
        self.runner_thread = RunnerThread(self.runner, "temp_run.py")
        self.runner_thread.log_signal.connect(self._append_log)
        self.runner_thread.finished.connect(self._on_run_finished)
        self.runner_thread.start()

    @Slot(str)
    def _append_log(self, text):
        self.log_view.appendPlainText(text.strip())

    @Slot(int)
    def _on_run_finished(self, rc):
        if rc == 0:
            QMessageBox.information(self, "Result", "Test Passed!")
        else:
            QMessageBox.warning(self, "Result", "Test Failed or Stopped.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AutoTestAppQt()
    window.show()
    sys.exit(app.exec())
