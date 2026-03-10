"""
실행 & 로그 탭 모듈

테스트 실행, Step-by-Step 디버깅, 로그 시각화를 담당합니다.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QPlainTextEdit, QProgressBar, QMessageBox, QScrollArea
)
from PySide6.QtCore import Signal, Slot, Qt
from PySide6.QtGui import QColor, QTextCharFormat, QFont

from gui.qt_components import ModernButton, COLORS
from gui.log_widget import ColoredLogWidget


class StepResultWidget(QWidget):
    """개별 스텝 실행 결과 위젯"""
    
    def __init__(self, step_num, step_name, parent=None):
        super().__init__(parent)
        self.step_num = step_num
        self._setup_ui(step_name)

    def _setup_ui(self, step_name):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 4, 10, 4)
        
        self.lbl_status = QLabel("⏸")
        self.lbl_status.setFixedWidth(25)
        layout.addWidget(self.lbl_status)
        
        self.lbl_name = QLabel(f"Step {self.step_num}: {step_name}")
        self.lbl_name.setStyleSheet(f"color: {COLORS['text']}; font-family: 'Segoe UI';")
        layout.addWidget(self.lbl_name)
        layout.addStretch()
        
        self.lbl_time = QLabel("")
        self.lbl_time.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px;")
        layout.addWidget(self.lbl_time)

    def set_running(self):
        self.lbl_status.setText("▶")
        self.lbl_status.setStyleSheet(f"color: {COLORS['primary']};")
        self.setStyleSheet(f"background-color: rgba(99, 102, 241, 0.1); border-radius: 4px;")

    def set_passed(self, duration_ms=0):
        self.lbl_status.setText("✅")
        self.lbl_time.setText(f"{duration_ms/1000:.1f}s" if duration_ms else "")
        self.setStyleSheet(f"background-color: rgba(16, 185, 129, 0.1); border-radius: 4px;")

    def set_failed(self, error=""):
        self.lbl_status.setText("🔴")
        self.lbl_name.setStyleSheet(f"color: {COLORS['danger']};")
        self.setStyleSheet(f"background-color: rgba(239, 68, 68, 0.1); border-radius: 4px;")

    def set_waiting(self):
        self.lbl_status.setText("⏸")
        self.lbl_status.setStyleSheet(f"color: {COLORS['text_secondary']};")
        self.setStyleSheet("")


class ExecutionTab(QWidget):
    """실행 & 로그 탭 위젯 (Step-by-Step 디버깅 포함)"""

    status_message = Signal(str, int)

    def __init__(self, runner, generator, parent=None):
        super().__init__(parent)
        self.runner = runner
        self.generator = generator
        self._step_widgets = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(5)

        # ── Controls Bar ──
        controls = QFrame()
        controls.setStyleSheet(
            f"background-color: {COLORS['surface']}; padding: 10px; border-radius: 8px;"
        )
        hbox = QHBoxLayout(controls)

        self.btn_run = ModernButton("▶ 전체 실행", COLORS['accent'])
        self.btn_run.clicked.connect(self._on_run_clicked)
        hbox.addWidget(self.btn_run)

        self.btn_step = ModernButton("⏭ 스텝 실행", COLORS['primary'])
        self.btn_step.clicked.connect(self._on_step_clicked)
        hbox.addWidget(self.btn_step)

        self.btn_stop = ModernButton("⏹ 정지", COLORS['danger'])
        self.btn_stop.clicked.connect(self._on_stop_clicked)
        hbox.addWidget(self.btn_stop)

        hbox.addStretch()

        self.lbl_mode = QLabel("Ready")
        self.lbl_mode.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        hbox.addWidget(self.lbl_mode)

        layout.addWidget(controls)

        # ── Step-by-Step 결과 패널 ──
        self.step_panel = QFrame()
        self.step_panel.setStyleSheet(
            f"background-color: {COLORS['surface']}; border-radius: 8px;"
        )
        self.step_panel_layout = QVBoxLayout(self.step_panel)
        self.step_panel_layout.setContentsMargins(5, 5, 5, 5)
        self.step_panel_layout.setSpacing(2)

        step_scroll = QScrollArea()
        step_scroll.setWidget(self.step_panel)
        step_scroll.setWidgetResizable(True)
        step_scroll.setMaximumHeight(200)
        step_scroll.setStyleSheet("border: none;")
        layout.addWidget(step_scroll)

        # ── Log View (색상 구분) ──
        self.log_view = ColoredLogWidget()
        layout.addWidget(self.log_view)

        # ── Progress ──
        self.progress = QProgressBar()
        self.progress.setStyleSheet(
            f"QProgressBar::chunk {{ background-color: {COLORS['primary']}; }}"
        )
        layout.addWidget(self.progress)

    # ── 외부에서 호출하는 메서드 ──

    def setup_steps(self, steps_data):
        """스텝 목록으로 디버깅 패널 초기화"""
        # 기존 위젯 정리
        for w in self._step_widgets:
            w.deleteLater()
        self._step_widgets.clear()

        for i, step in enumerate(steps_data):
            w = StepResultWidget(i + 1, step.get("name", f"Step {i+1}"))
            self._step_widgets.append(w)
            self.step_panel_layout.addWidget(w)

    def mark_step(self, index, status, duration_ms=0, error=""):
        """스텝 결과 업데이트"""
        if 0 <= index < len(self._step_widgets):
            w = self._step_widgets[index]
            if status == "running":
                w.set_running()
            elif status == "passed":
                w.set_passed(duration_ms)
            elif status == "failed":
                w.set_failed(error)
            elif status == "waiting":
                w.set_waiting()

    def append_log(self, text):
        """로그 추가"""
        self.log_view.append_log(text)

    def clear_logs(self):
        """로그 초기화"""
        self.log_view.clear()

    # ── Internal Actions ──

    def _on_run_clicked(self):
        """전체 실행 버튼 (시그널로 상위 전달)"""
        self.lbl_mode.setText("🏃 Running...")
        self.lbl_mode.setStyleSheet(f"color: {COLORS['accent']};")

    def _on_step_clicked(self):
        """스텝 실행 버튼"""
        self.lbl_mode.setText("⏭ Step Mode")
        self.lbl_mode.setStyleSheet(f"color: {COLORS['primary']};")

    def _on_stop_clicked(self):
        """정지 버튼"""
        self.lbl_mode.setText("⏹ Stopped")
        self.lbl_mode.setStyleSheet(f"color: {COLORS['danger']};")

    def on_run_finished(self, rc):
        """실행 완료 처리"""
        if rc == 0:
            self.lbl_mode.setText("✅ Passed")
            self.lbl_mode.setStyleSheet(f"color: {COLORS['accent']};")
        else:
            self.lbl_mode.setText("🔴 Failed")
            self.lbl_mode.setStyleSheet(f"color: {COLORS['danger']};")
