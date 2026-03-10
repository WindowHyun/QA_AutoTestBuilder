"""
코드 미리보기 탭 모듈

스텝 변경 시 실시간으로 Pytest 코드를 생성하여 표시합니다.
v7.1 기능을 별도 위젯으로 분리.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QPlainTextEdit, QTextEdit, QApplication
)
from PySide6.QtCore import Signal, Slot, Qt, QTimer
from PySide6.QtGui import QColor, QTextFormat

from gui.qt_components import ModernButton, COLORS
from gui.syntax_highlighter import PythonHighlighter


class CodeTab(QWidget):
    """코드 미리보기 탭 위젯"""

    status_message = Signal(str, int)

    def __init__(self, generator, parent=None):
        super().__init__(parent)
        self.generator = generator
        self._code_update_timer = None

        # 외부에서 설정 (연결 시)
        self._steps_data = None
        self._url_getter = None
        self._browser_getter = None
        self._data_path_getter = None

        self._setup_ui()

    def set_data_sources(self, steps_data, url_getter, browser_getter, data_path_getter):
        """외부 데이터 소스 연결"""
        self._steps_data = steps_data
        self._url_getter = url_getter
        self._browser_getter = browser_getter
        self._data_path_getter = data_path_getter

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QFrame()
        header.setFixedHeight(50)
        header.setStyleSheet(
            f"background-color: {COLORS['surface']}; "
            f"border-bottom: 1px solid {COLORS['border']}; padding: 0 15px;"
        )
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(15, 0, 15, 0)

        lbl_title = QLabel("💻 Generated Pytest Code")
        lbl_title.setStyleSheet(
            f"font-size: 14px; font-weight: bold; color: {COLORS['primary']};"
        )
        header_layout.addWidget(lbl_title)

        self.lbl_code_status = QLabel("스텝을 추가하면 코드가 자동 생성됩니다")
        self.lbl_code_status.setStyleSheet(
            f"color: {COLORS['text_secondary']}; margin-left: 15px;"
        )
        header_layout.addWidget(self.lbl_code_status)
        header_layout.addStretch()

        btn_copy = ModernButton("📋 복사", COLORS['secondary'])
        btn_copy.setFixedWidth(80)
        btn_copy.clicked.connect(self._copy_code_to_clipboard)
        header_layout.addWidget(btn_copy)

        layout.addWidget(header)

        # Code Editor (Line Number + Code)
        code_container = QHBoxLayout()
        code_container.setContentsMargins(0, 0, 0, 0)
        code_container.setSpacing(0)

        # Line numbers
        self.line_number_area = QPlainTextEdit()
        self.line_number_area.setReadOnly(True)
        self.line_number_area.setFixedWidth(55)
        self.line_number_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.line_number_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.line_number_area.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: {COLORS['background']};
                color: {COLORS['text_secondary']};
                border: none;
                border-right: 1px solid {COLORS['border']};
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 13px;
                padding-top: 10px;
            }}
        """)
        code_container.addWidget(self.line_number_area)

        # Code view
        self.code_view = QPlainTextEdit()
        self.code_view.setReadOnly(True)
        self.code_view.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: #1E1E1E;
                color: #D4D4D4;
                border: none;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 13px;
                padding: 10px;
                selection-background-color: #264F78;
            }}
        """)
        self.code_view.setLineWrapMode(QPlainTextEdit.NoWrap)
        code_container.addWidget(self.code_view)

        # Syntax highlighter
        self._highlighter = PythonHighlighter(self.code_view.document())

        # Scroll sync
        self.code_view.verticalScrollBar().valueChanged.connect(
            self.line_number_area.verticalScrollBar().setValue
        )

        code_wrapper = QWidget()
        code_wrapper.setLayout(code_container)
        layout.addWidget(code_wrapper)

        # Footer
        footer = QFrame()
        footer.setFixedHeight(30)
        footer.setStyleSheet(
            f"background-color: {COLORS['surface']}; "
            f"border-top: 1px solid {COLORS['border']};"
        )
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(15, 0, 15, 0)

        self.lbl_line_info = QLabel("Lines: 0 | Steps: 0")
        self.lbl_line_info.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: 11px;"
        )
        footer_layout.addWidget(self.lbl_line_info)
        footer_layout.addStretch()

        lbl_lang = QLabel("Python (Pytest)")
        lbl_lang.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: 11px;"
        )
        footer_layout.addWidget(lbl_lang)
        layout.addWidget(footer)

    # ── Public Methods ──

    def schedule_update(self):
        """코드 미리보기 갱신 (300ms 디바운싱)"""
        if self._code_update_timer is not None:
            self._code_update_timer.stop()
        self._code_update_timer = QTimer(self)
        self._code_update_timer.setSingleShot(True)
        self._code_update_timer.timeout.connect(self._update_code_preview)
        self._code_update_timer.start(300)

    def scroll_to_step(self, step_row):
        """선택된 스텝에 해당하는 코드 위치로 스크롤"""
        code = self.code_view.toPlainText()
        if not code:
            return

        step_num = step_row + 1
        search_patterns = [
            f'Step {step_num}:',
            f'Step {step_num}.',
            f'step("스텝 {step_num}',
        ]

        lines = code.split('\n')
        target_line = -1
        for line_idx, line in enumerate(lines):
            for pattern in search_patterns:
                if pattern.lower() in line.lower():
                    target_line = line_idx
                    break
            if target_line >= 0:
                break

        if target_line >= 0:
            cursor = self.code_view.textCursor()
            block = self.code_view.document().findBlockByLineNumber(target_line)
            cursor.setPosition(block.position())
            self.code_view.setTextCursor(cursor)
            self.code_view.centerCursor()

            # Highlight current line
            extra_selections = []
            selection = QTextEdit.ExtraSelection()
            selection.format.setBackground(QColor("#264F78"))
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = cursor
            extra_selections.append(selection)
            self.code_view.setExtraSelections(extra_selections)

            self.line_number_area.verticalScrollBar().setValue(
                self.code_view.verticalScrollBar().value()
            )

    # ── Internal ──

    @Slot()
    def _update_code_preview(self):
        """스텝 데이터 기반 Pytest 코드 생성"""
        steps = self._steps_data
        if not steps:
            self.code_view.setPlainText(
                "# 스텝을 추가하면 여기에 Pytest 코드가 자동 생성됩니다.\n"
                "# \n# 1. 🌐 브라우저 열기\n# 2. 🎯 요소 스캔 (F2)\n"
                "# 3. 이 탭에서 생성된 코드 확인\n"
            )
            self._update_line_numbers(5)
            self.lbl_code_status.setText("스텝을 추가하면 코드가 자동 생성됩니다")
            self.lbl_line_info.setText("Lines: 0 | Steps: 0")
            return

        try:
            url = self._url_getter() if self._url_getter else ""
            browser_type = self._browser_getter() if self._browser_getter else "chrome"
            data_path = self._data_path_getter() if self._data_path_getter else None

            code = self.generator.generate(
                url, steps, False,
                data_path=data_path,
                browser_type=browser_type
            )

            self.code_view.setPlainText(code.strip())

            line_count = code.strip().count('\n') + 1
            self._update_line_numbers(line_count)

            step_count = len(steps)
            self.lbl_code_status.setText(f"✅ {step_count}개 스텝 → {line_count}줄 코드 생성됨")
            self.lbl_line_info.setText(f"Lines: {line_count} | Steps: {step_count}")

        except Exception as e:
            self.code_view.setPlainText(f"# 코드 생성 오류:\n# {str(e)}")
            self.lbl_code_status.setText(f"❌ 코드 생성 실패: {str(e)[:50]}")

    def _update_line_numbers(self, line_count):
        numbers = "\n".join(str(i) for i in range(1, line_count + 1))
        self.line_number_area.setPlainText(numbers)

    @Slot()
    def _copy_code_to_clipboard(self):
        code = self.code_view.toPlainText()
        if code and not code.startswith("# 스텝을 추가하면"):
            QApplication.clipboard().setText(code)
            self.status_message.emit("✅ 코드가 클립보드에 복사되었습니다", 3000)
        else:
            self.status_message.emit("⚠️ 복사할 코드가 없습니다", 3000)
