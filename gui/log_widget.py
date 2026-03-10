"""
색상 로그 위젯

로그 레벨별 색상 구분:
  PASSED/SUCCESS → 초록
  FAILED/ERROR   → 빨강
  WARNING/WARN   → 노랑
  INFO           → 회색
  스텝 헤더      → 파랑
"""

from PySide6.QtWidgets import QPlainTextEdit
from PySide6.QtGui import QColor, QTextCharFormat, QFont, QTextCursor
from PySide6.QtCore import Qt

from gui.qt_components import COLORS


class ColoredLogWidget(QPlainTextEdit):
    """레벨별 색상 구분 로그 위젯"""

    # 로그 레벨별 색상 매핑
    LEVEL_COLORS = {
        "passed": "#10B981",     # 초록
        "success": "#10B981",
        "pass": "#10B981",
        "ok": "#10B981",
        "failed": "#EF4444",     # 빨강
        "error": "#EF4444",
        "fail": "#EF4444",
        "exception": "#EF4444",
        "assert": "#EF4444",
        "warning": "#F59E0B",    # 노랑
        "warn": "#F59E0B",
        "retry": "#F59E0B",
        "info": "#9CA3AF",       # 회색
        "step": "#6366F1",       # 보라 (스텝 헤더)
        "screenshot": "#60A5FA", # 파랑
        "self-healing": "#F59E0B",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setMaximumBlockCount(5000)  # 최대 줄 수 제한
        self.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: #0D1117;
                color: #C9D1D9;
                border: none;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
                padding: 10px;
                selection-background-color: #264F78;
            }}
        """)

    def append_log(self, text):
        """로그 텍스트를 색상과 함께 추가"""
        text = text.strip()
        if not text:
            return

        color = self._detect_color(text)

        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))

        # 특수 강조: PASSED / FAILED
        text_lower = text.lower()
        if "passed" in text_lower or "success" in text_lower:
            fmt.setFontWeight(QFont.Bold)
        elif "failed" in text_lower or "error" in text_lower:
            fmt.setFontWeight(QFont.Bold)
        elif text.startswith("Step ") or text.startswith("with step("):
            fmt.setFontWeight(QFont.Bold)
            fmt.setForeground(QColor("#6366F1"))

        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(text + "\n", fmt)
        self.setTextCursor(cursor)
        self.ensureCursorVisible()

    def _detect_color(self, text):
        """텍스트 내용 기반 색상 결정"""
        lower = text.lower()
        for keyword, color in self.LEVEL_COLORS.items():
            if keyword in lower:
                return color
        return "#C9D1D9"  # 기본 회색
