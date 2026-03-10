"""
Trace/Timeline 탭 모듈

각 스텝 실행 시 스크린샷 + 소요시간을 타임라인으로 기록/탐색합니다.
Playwright Trace Viewer 스타일.
"""

import os
import json
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QScrollArea, QSplitter, QPlainTextEdit, QFileDialog
)
from PySide6.QtCore import Signal, Slot, Qt
from PySide6.QtGui import QPixmap

from gui.qt_components import ModernButton, COLORS


class TraceStepBlock(QWidget):
    """타임라인 내 개별 스텝 블록"""

    clicked = Signal(int)  # step_index

    def __init__(self, index, step_name, status="waiting", duration_ms=0, parent=None):
        super().__init__(parent)
        self.index = index
        self.status = status
        self.duration_ms = duration_ms
        self.screenshot_path = None
        self.error_msg = ""
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(60)
        min_w = max(60, int(duration_ms / 50))  # 소요시간 비례 너비
        self.setMinimumWidth(min_w)
        self.setMaximumWidth(200)

        self._setup_ui(step_name)
        self._apply_style()

    def _setup_ui(self, step_name):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(2)

        self.lbl_step = QLabel(f"S{self.index + 1}")
        self.lbl_step.setStyleSheet("font-weight: bold; font-size: 12px;")
        self.lbl_step.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_step)

        self.lbl_name = QLabel(step_name[:15])
        self.lbl_name.setStyleSheet("font-size: 9px;")
        self.lbl_name.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_name)

        time_text = f"{self.duration_ms/1000:.1f}s" if self.duration_ms > 0 else "—"
        self.lbl_time = QLabel(time_text)
        self.lbl_time.setStyleSheet(f"font-size: 9px; color: {COLORS['text_secondary']};")
        self.lbl_time.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_time)

    def _apply_style(self):
        if self.status == "passed":
            bg = "rgba(16, 185, 129, 0.2)"
            border = "#10B981"
            icon = "✅"
        elif self.status == "failed":
            bg = "rgba(239, 68, 68, 0.2)"
            border = "#EF4444"
            icon = "🔴"
        elif self.status == "running":
            bg = "rgba(99, 102, 241, 0.2)"
            border = "#6366F1"
            icon = "▶"
        else:
            bg = "rgba(107, 114, 128, 0.1)"
            border = COLORS['border']
            icon = "⏸"

        self.setStyleSheet(
            f"background-color: {bg}; border: 1px solid {border}; border-radius: 6px;"
        )
        self.lbl_step.setText(f"{icon} S{self.index + 1}")

    def update_result(self, status, duration_ms=0, screenshot_path=None, error=""):
        self.status = status
        self.duration_ms = duration_ms
        self.screenshot_path = screenshot_path
        self.error_msg = error
        self.lbl_time.setText(f"{duration_ms/1000:.1f}s" if duration_ms > 0 else "—")
        self._apply_style()

    def mousePressEvent(self, event):
        self.clicked.emit(self.index)
        super().mousePressEvent(event)


class TraceTab(QWidget):
    """Trace/Timeline 탭 위젯"""

    status_message = Signal(str, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._blocks = []
        self._trace_data = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(5)

        # Header
        header = QFrame()
        header.setFixedHeight(50)
        header.setStyleSheet(
            f"background-color: {COLORS['surface']}; "
            f"border-bottom: 1px solid {COLORS['border']};"
        )
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(15, 0, 15, 0)

        lbl_title = QLabel("🕐 Trace Timeline")
        lbl_title.setStyleSheet(
            f"font-size: 14px; font-weight: bold; color: {COLORS['primary']};"
        )
        header_layout.addWidget(lbl_title)

        self.lbl_trace_status = QLabel("테스트 실행 후 타임라인이 표시됩니다")
        self.lbl_trace_status.setStyleSheet(
            f"color: {COLORS['text_secondary']}; margin-left: 15px;"
        )
        header_layout.addWidget(self.lbl_trace_status)
        header_layout.addStretch()

        btn_save = ModernButton("💾 저장", COLORS['secondary'])
        btn_save.setFixedWidth(80)
        btn_save.clicked.connect(self._save_trace)
        header_layout.addWidget(btn_save)

        btn_load = ModernButton("📂 로드", COLORS['secondary'])
        btn_load.setFixedWidth(80)
        btn_load.clicked.connect(self._load_trace)
        header_layout.addWidget(btn_load)

        layout.addWidget(header)

        # 타임라인 바 (가로 스크롤)
        timeline_scroll = QScrollArea()
        timeline_scroll.setFixedHeight(80)
        timeline_scroll.setWidgetResizable(True)
        timeline_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        timeline_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        timeline_scroll.setStyleSheet(
            f"background-color: {COLORS['background']}; border: 1px solid {COLORS['border']}; border-radius: 6px;"
        )

        self.timeline_container = QWidget()
        self.timeline_layout = QHBoxLayout(self.timeline_container)
        self.timeline_layout.setContentsMargins(5, 5, 5, 5)
        self.timeline_layout.setSpacing(4)
        self.timeline_layout.addStretch()

        timeline_scroll.setWidget(self.timeline_container)
        layout.addWidget(timeline_scroll)

        # 상세 정보 (스크린샷 + 에러)
        splitter = QSplitter(Qt.Horizontal)

        # 스크린샷 영역
        self.screenshot_frame = QFrame()
        self.screenshot_frame.setStyleSheet(
            f"background-color: {COLORS['surface']}; border-radius: 8px;"
        )
        ss_layout = QVBoxLayout(self.screenshot_frame)
        self.lbl_screenshot_title = QLabel("📸 Screenshot")
        self.lbl_screenshot_title.setStyleSheet(
            f"font-weight: bold; color: {COLORS['primary']};"
        )
        ss_layout.addWidget(self.lbl_screenshot_title)

        self.lbl_screenshot = QLabel("스텝 블록을 클릭하면 스크린샷이 표시됩니다")
        self.lbl_screenshot.setAlignment(Qt.AlignCenter)
        self.lbl_screenshot.setStyleSheet(f"color: {COLORS['text_secondary']};")
        self.lbl_screenshot.setMinimumHeight(300)
        ss_layout.addWidget(self.lbl_screenshot)
        splitter.addWidget(self.screenshot_frame)

        # 상세 정보 영역
        detail_frame = QFrame()
        detail_frame.setStyleSheet(
            f"background-color: {COLORS['surface']}; border-radius: 8px;"
        )
        detail_layout = QVBoxLayout(detail_frame)
        lbl_detail_title = QLabel("📋 Step Details")
        lbl_detail_title.setStyleSheet(
            f"font-weight: bold; color: {COLORS['primary']};"
        )
        detail_layout.addWidget(lbl_detail_title)

        self.detail_text = QPlainTextEdit()
        self.detail_text.setReadOnly(True)
        self.detail_text.setStyleSheet(
            f"background-color: #0D1117; color: #C9D1D9; "
            f"font-family: Consolas; font-size: 12px; border: none;"
        )
        detail_layout.addWidget(self.detail_text)
        splitter.addWidget(detail_frame)

        splitter.setSizes([500, 300])
        layout.addWidget(splitter)

    # ── Public Methods ──

    def setup_timeline(self, steps_data):
        """스텝 목록으로 타임라인 초기화"""
        # 기존 블록 제거
        for b in self._blocks:
            b.deleteLater()
        self._blocks.clear()
        self._trace_data.clear()

        # stretch 제거
        while self.timeline_layout.count():
            item = self.timeline_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 새 블록 추가
        for i, step in enumerate(steps_data):
            block = TraceStepBlock(i, step.get("name", f"Step {i+1}"))
            block.clicked.connect(self._on_block_clicked)
            self._blocks.append(block)
            self.timeline_layout.addWidget(block)

        self.timeline_layout.addStretch()
        self.lbl_trace_status.setText(f"📋 {len(steps_data)}개 스텝 대기 중")

    def update_step(self, index, status, duration_ms=0, screenshot_path=None, error=""):
        """스텝 결과 업데이트"""
        if 0 <= index < len(self._blocks):
            self._blocks[index].update_result(status, duration_ms, screenshot_path, error)

            # trace 기록
            self._trace_data.append({
                "step": index + 1,
                "status": status,
                "duration_ms": duration_ms,
                "screenshot": screenshot_path,
                "error": error,
                "timestamp": datetime.now().isoformat()
            })

    def finalize(self, total_duration_ms=0):
        """실행 완료 후 요약"""
        passed = sum(1 for b in self._blocks if b.status == "passed")
        failed = sum(1 for b in self._blocks if b.status == "failed")
        total = len(self._blocks)
        self.lbl_trace_status.setText(
            f"✅ {passed}/{total} 성공 | 🔴 {failed} 실패 | ⏱ {total_duration_ms/1000:.1f}s"
        )

    # ── Internal ──

    def _on_block_clicked(self, index):
        """타임라인 블록 클릭 → 상세 정보 표시"""
        if 0 <= index < len(self._blocks):
            block = self._blocks[index]

            # 스크린샷 표시
            if block.screenshot_path and os.path.exists(block.screenshot_path):
                pixmap = QPixmap(block.screenshot_path)
                scaled = pixmap.scaledToWidth(
                    self.lbl_screenshot.width() - 20,
                    Qt.SmoothTransformation
                )
                self.lbl_screenshot.setPixmap(scaled)
                self.lbl_screenshot_title.setText(f"📸 Step {index + 1} Screenshot")
            else:
                self.lbl_screenshot.setText("스크린샷 없음")

            # 상세 정보 표시
            details = (
                f"Step: {index + 1}\n"
                f"Status: {block.status.upper()}\n"
                f"Duration: {block.duration_ms/1000:.2f}s\n"
            )
            if block.error_msg:
                details += f"\n--- Error ---\n{block.error_msg}"
            self.detail_text.setPlainText(details)

    def _save_trace(self):
        """Trace 데이터 저장"""
        if not self._trace_data:
            self.status_message.emit("⚠️ 저장할 Trace 데이터가 없습니다", 3000)
            return
        fname, _ = QFileDialog.getSaveFileName(
            self, "Save Trace", "", "JSON Files (*.json)"
        )
        if fname:
            with open(fname, 'w', encoding='utf-8') as f:
                json.dump(self._trace_data, f, ensure_ascii=False, indent=2)
            self.status_message.emit(f"Trace 저장 완료: {fname}", 3000)

    def _load_trace(self):
        """Trace 데이터 로드"""
        fname, _ = QFileDialog.getOpenFileName(
            self, "Load Trace", "", "JSON Files (*.json)"
        )
        if fname:
            try:
                with open(fname, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self._trace_data = data
                self.status_message.emit(f"Trace 로드 완료: {fname}", 3000)
            except Exception as e:
                self.status_message.emit(f"Trace 로드 실패: {e}", 5000)
