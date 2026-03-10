"""
QA Auto Test Builder — 메인 GUI 애플리케이션

각 탭 위젯을 조립하고 시그널/슬롯으로 연동합니다.
v7.1 Pro — Playwright-Style Refactoring
"""

import sys
import os
import threading
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QMessageBox, QFrame
)
from PySide6.QtCore import Qt, QThread, Signal, Slot, QTimer
from PySide6.QtGui import QColor, QPalette

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from core.browser import BrowserManager
from core.scanner import PageScanner
from core.generator import ScriptGenerator
from core.pom_generator import POMGenerator
from core.runner import TestRunner
from utils.database import TestCaseDB
from core.plugin_manager import PluginManager
from core.step_runner import StepRunner
from core.metrics import MetricsCollector
from core.api_tester import APITester
from core.visual_compare import VisualCompare

from gui.qt_components import ModernButton, COLORS
from gui.scenario_tab import ScenarioTab
from gui.execution_tab import ExecutionTab
from gui.data_tab import DataTab
from gui.code_tab import CodeTab
from gui.trace_tab import TraceTab


# --- Worker Threads ---
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
        self.plugin_manager.hook("on_test_start", name=self.script_path, script=self.script_path)
        try:
            import subprocess
            process = subprocess.Popen(
                [sys.executable, "-u", self.script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                cwd=os.path.dirname(os.path.abspath(self.script_path)) or "."
            )
            self.runner.process = process

            for line in process.stdout:
                if self._stop_event.is_set():
                    process.terminate()
                    break
                self.log_signal.emit(line)

            rc = process.wait()
            self.plugin_manager.hook("on_test_finish", status="PASSED" if rc == 0 else "FAILED", return_code=rc, script=self.script_path)
            self.finished.emit(rc)
        except Exception as e:
            self.log_signal.emit(f"[ERROR] {str(e)}")
            self.finished.emit(1)

    def stop(self):
        self._stop_event.set()


class AutoTestAppQt(QMainWindow):
    """메인 애플리케이션 윈도우 — 탭 조립 및 시그널 연동"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("🚀 QA Auto Test Builder v7.1 Pro")
        self.resize(1280, 850)

        # Core Resources (공유)
        self.browser = BrowserManager()
        self.scanner = PageScanner()
        self.generator = ScriptGenerator()
        self.pom_generator = POMGenerator()
        self.runner = TestRunner()
        self.step_runner = StepRunner(self.browser)
        self.metrics = MetricsCollector()
        self.api_tester = APITester()
        self.visual_compare = VisualCompare()
        self.db = TestCaseDB()

        # UI
        self._setup_theme()
        self._init_ui()
        self._connect_signals()

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

        # Header
        header = QFrame()
        header.setFixedHeight(60)
        header.setStyleSheet(
            f"background-color: {COLORS['surface']}; border-bottom: 1px solid {COLORS['border']};"
        )
        header_layout = QHBoxLayout(header)

        title = QLabel("🚀 QA Auto Test Builder")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {COLORS['text']};")
        subtitle = QLabel("No-Code Automation Platform")
        subtitle.setStyleSheet(f"font-size: 12px; color: {COLORS['text_secondary']}; margin-left: 10px;")
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        header_layout.addStretch()

        btn_pom = ModernButton("📦 POM 내보내기", COLORS['secondary'])
        btn_pom.clicked.connect(self.cmd_export_pom)
        header_layout.addWidget(btn_pom)
        main_layout.addWidget(header)

        # Tabs — 각 탭 위젯 인스턴스 조립
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        self.tab_scenario = ScenarioTab(self.browser, self.scanner)
        self.tab_execution = ExecutionTab(self.runner, self.generator)
        self.tab_data = DataTab()
        self.tab_code = CodeTab(self.generator)
        self.tab_trace = TraceTab()

        self.tabs.addTab(self.tab_scenario, "🎯 Scenario Design")
        self.tabs.addTab(self.tab_execution, "▶ Execution & Logs")
        self.tabs.addTab(self.tab_data, "📊 Data Management")
        self.tabs.addTab(self.tab_code, "💻 Code Preview")
        self.tabs.addTab(self.tab_trace, "🕐 Trace Timeline")

        # Code Tab에 데이터 소스 연결
        self.tab_code.set_data_sources(
            steps_data=self.tab_scenario.steps_data,
            url_getter=lambda: self.tab_scenario.url_input.text(),
            browser_getter=lambda: self.tab_scenario.browser_combo.currentText().lower(),
            data_path_getter=lambda: self.tab_data.data_path
        )

    def _connect_signals(self):
        """탭 간 시그널/슬롯 연동"""

        # Status messages → Status bar
        self.tab_scenario.status_message.connect(
            lambda msg, t: self.status_bar.showMessage(msg, t)
        )
        self.tab_execution.status_message.connect(
            lambda msg, t: self.status_bar.showMessage(msg, t)
        )
        self.tab_data.status_message.connect(
            lambda msg, t: self.status_bar.showMessage(msg, t)
        )
        self.tab_code.status_message.connect(
            lambda msg, t: self.status_bar.showMessage(msg, t)
        )
        self.tab_trace.status_message.connect(
            lambda msg, t: self.status_bar.showMessage(msg, t)
        )

        # Steps changed → Code Preview 갱신
        self.tab_scenario.steps_changed.connect(self.tab_code.schedule_update)

        # Table selection → Code scroll
        self.tab_scenario.table_view.selectionModel().selectionChanged.connect(
            self._on_step_selected
        )

        # Execution 버튼 → 테스트 실행
        self.tab_execution.btn_run.clicked.connect(self.cmd_run_test)
        self.tab_execution.btn_step.clicked.connect(self.cmd_step_execute)
        self.tab_execution.btn_stop.clicked.connect(self._cmd_stop_test)

        # Step-by-Step 상태
        self._step_index = 0

    def _on_step_selected(self, selected, deselected):
        """스텝 선택 시 Code Preview에서 해당 코드로 스크롤"""
        indexes = selected.indexes()
        if indexes:
            self.tab_code.scroll_to_step(indexes[0].row())

    # ── Commands ──

    @Slot()
    def cmd_export_pom(self):
        from PySide6.QtWidgets import QFileDialog
        dname = QFileDialog.getExistingDirectory(self, "Select Export Directory")
        if dname:
            try:
                success, msg = self.pom_generator.generate_project(
                    dname,
                    self.tab_scenario.url_input.text(),
                    self.tab_scenario.steps_data,
                    data_path=self.tab_data.data_path,
                    browser_type=self.tab_scenario.browser_combo.currentText().lower()
                )
                if success:
                    QMessageBox.information(self, "Success", f"Project exported to:\n{dname}")
                else:
                    QMessageBox.warning(self, "Failed", msg)
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    @Slot()
    def cmd_run_test(self):
        """테스트 전체 실행"""
        steps_data = self.tab_scenario.steps_data
        if not steps_data:
            QMessageBox.warning(self, "Warning", "실행할 스텝이 없습니다!")
            return

        # 스크립트 생성
        script = self.generator.generate(
            self.tab_scenario.url_input.text(),
            steps_data,
            False,
            data_path=self.tab_data.data_path,
            browser_type=self.tab_scenario.browser_combo.currentText().lower()
        )
        with open("temp_run.py", "w", encoding="utf-8") as f:
            f.write(script)

        # UI 초기화
        self.tabs.setCurrentWidget(self.tab_execution)
        self.tab_execution.clear_logs()
        self.tab_execution.setup_steps(steps_data)
        self.tab_trace.setup_timeline(steps_data)

        # 실행
        self.runner_thread = RunnerThread(self.runner, "temp_run.py")
        self.runner_thread.log_signal.connect(self.tab_execution.append_log)
        self.runner_thread.finished.connect(self._on_run_finished)
        self.runner_thread.start()

    @Slot()
    def _cmd_stop_test(self):
        if hasattr(self, 'runner_thread') and self.runner_thread.isRunning():
            self.runner_thread.stop()
            self.runner.stop()
            self.tab_execution.on_run_finished(1)

    @Slot(int)
    def _on_run_finished(self, rc):
        self.tab_execution.on_run_finished(rc)
        if rc == 0:
            QMessageBox.information(self, "Result", "✅ Test Passed!")
        else:
            QMessageBox.warning(self, "Result", "🔴 Test Failed or Stopped.")

    # ── Step-by-Step 실행 ──

    @Slot()
    def cmd_step_execute(self):
        """다음 스텝 1개 실행 (Step-by-Step 디버깅)"""
        steps_data = self.tab_scenario.steps_data
        if not steps_data:
            QMessageBox.warning(self, "Warning", "실행할 스텝이 없습니다!")
            return

        if not self.browser.is_alive:
            QMessageBox.warning(self, "Warning", "브라우저가 열려있지 않습니다!\n먼저 Scenario 탭에서 브라우저를 열어주세요.")
            return

        # 첫 실행이면 UI 초기화
        if self._step_index == 0:
            self.tabs.setCurrentWidget(self.tab_execution)
            self.tab_execution.clear_logs()
            self.tab_execution.setup_steps(steps_data)
            self.tab_trace.setup_timeline(steps_data)
            self.step_runner.reset()
            self.metrics.reset()
            self.visual_compare.reset()

        if self._step_index >= len(steps_data):
            QMessageBox.information(self, "Done", "모든 스텝이 완료되었습니다!")
            self._step_index = 0
            return

        # 현재 스텝을 running으로 표시
        self.tab_execution.mark_step(self._step_index, "running")
        self.tab_execution.append_log(f"▶ Step {self._step_index + 1}: {steps_data[self._step_index].get('name', '')}...")

        # 실행 (별도 쓰레드가 아닌 즉시 실행 — 한 스텝이라 빠름)
        step = steps_data[self._step_index]
        result = self.step_runner.execute_step(self._step_index, step)

        # UI 업데이트
        self.tab_execution.mark_step(
            result.step_index, result.status,
            result.duration_ms, result.error
        )
        self.tab_trace.update_step(
            result.step_index, result.status,
            result.duration_ms, result.screenshot_path, result.error
        )

        if result.status == "passed":
            self.tab_execution.append_log(f"   ✅ PASSED ({result.duration_ms:.0f}ms)")
        else:
            self.tab_execution.append_log(f"   🔴 FAILED: {result.error}")

        # 비주얼 리그레션 비교 (스크린샷이 있으면)
        if result.screenshot_path:
            step_name = steps_data[result.step_index].get('name', f'Step_{result.step_index + 1}')
            vr = self.visual_compare.compare(result.screenshot_path, step_name)
            if not vr.baseline_exists:
                self.tab_execution.append_log(f"   🆕 Visual baseline 저장됨")
            elif not vr.passed:
                self.tab_execution.append_log(f"   🖼️ Visual 변경 감지: {vr.match_percent:.1f}% 일치")

        self._step_index += 1

        # 메트릭 수집
        self.metrics.add_result(
            result.step_index,
            steps_data[result.step_index].get('name', ''),
            result.status, result.duration_ms, result.error
        )

        # 마지막 스텝 완료 시 finalize
        if self._step_index >= len(steps_data) or result.status == "failed":
            self.metrics.finalize()
            self.tab_trace.finalize()

            # 품질 메트릭 요약 표시
            summary = self.metrics.format_summary()
            self.tab_execution.append_log(summary)

            # 비주얼 리그레션 요약 표시
            vr_summary = self.visual_compare.format_summary()
            if vr_summary:
                self.tab_execution.append_log(vr_summary)

            if result.status == "failed":
                self.tab_execution.on_run_finished(1)
            else:
                self.tab_execution.on_run_finished(0)
            self._step_index = 0


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AutoTestAppQt()
    window.show()
    sys.exit(app.exec())
