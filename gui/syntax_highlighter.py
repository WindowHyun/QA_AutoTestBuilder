"""
Python Syntax Highlighter for Code Preview

PySide6 QSyntaxHighlighter 기반 Python 코드 구문 강조.
다크 테마 최적화.
"""

import re
from PySide6.QtCore import Qt, QRegularExpression
from PySide6.QtGui import (
    QSyntaxHighlighter, QTextCharFormat, QColor, QFont
)


class PythonHighlighter(QSyntaxHighlighter):
    """Python 구문 강조기 (다크 테마)"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rules = []
        self._setup_rules()

    def _make_format(self, color, bold=False, italic=False):
        """QTextCharFormat 생성 헬퍼"""
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        if bold:
            fmt.setFontWeight(QFont.Bold)
        if italic:
            fmt.setFontItalic(True)
        return fmt

    def _setup_rules(self):
        # 색상 팔레트 (VS Code Dark+ 계열)
        KEYWORD = "#C586C0"        # 보라 (if, for, def, class, ...)
        BUILTIN = "#DCDCAA"        # 노란 (print, len, range, ...)
        STRING = "#CE9178"         # 주황 (문자열)
        NUMBER = "#B5CEA8"         # 연두 (숫자)
        COMMENT = "#6A9955"        # 초록 (주석)
        DECORATOR = "#DCDCAA"      # 노란 (@pytest.fixture)
        FUNCTION_DEF = "#DCDCAA"   # 노란 (함수명)
        CLASS_DEF = "#4EC9B0"      # 민트 (클래스명)
        SELF = "#569CD6"           # 파랑 (self)
        IMPORT = "#C586C0"         # 보라 (import, from)
        CONSTANT = "#4FC1FF"       # 하늘 (True, False, None)
        OPERATOR = "#D4D4D4"       # 회색 (=, +, -, etc)

        # 키워드
        keywords = [
            "and", "as", "assert", "async", "await", "break", "class",
            "continue", "def", "del", "elif", "else", "except", "finally",
            "for", "from", "global", "if", "import", "in", "is", "lambda",
            "nonlocal", "not", "or", "pass", "raise", "return", "try",
            "while", "with", "yield",
        ]
        keyword_fmt = self._make_format(KEYWORD, bold=True)
        for kw in keywords:
            pattern = QRegularExpression(rf"\b{kw}\b")
            self._rules.append((pattern, keyword_fmt))

        # 상수 (True, False, None)
        constant_fmt = self._make_format(CONSTANT, bold=True)
        for const in ["True", "False", "None"]:
            self._rules.append((QRegularExpression(rf"\b{const}\b"), constant_fmt))

        # 내장 함수
        builtins = [
            "print", "len", "range", "int", "str", "float", "list", "dict",
            "set", "tuple", "type", "isinstance", "hasattr", "getattr",
            "setattr", "enumerate", "zip", "map", "filter", "sorted",
            "open", "super", "property", "staticmethod", "classmethod",
            "abs", "all", "any", "bin", "bool", "bytes", "callable", "chr",
            "dir", "divmod", "format", "hex", "id", "input", "iter",
            "max", "min", "next", "oct", "ord", "pow", "repr", "reversed",
            "round", "slice", "sum", "vars",
        ]
        builtin_fmt = self._make_format(BUILTIN)
        for bi in builtins:
            self._rules.append((QRegularExpression(rf"\b{bi}\b"), builtin_fmt))

        # self
        self._rules.append((
            QRegularExpression(r"\bself\b"),
            self._make_format(SELF, italic=True)
        ))

        # 데코레이터 (@xxx)
        self._rules.append((
            QRegularExpression(r"@[\w\.]+"),
            self._make_format(DECORATOR)
        ))

        # 함수 정의 (def xxx)
        self._rules.append((
            QRegularExpression(r"\bdef\s+(\w+)"),
            self._make_format(FUNCTION_DEF)
        ))

        # 클래스 정의 (class xxx)
        self._rules.append((
            QRegularExpression(r"\bclass\s+(\w+)"),
            self._make_format(CLASS_DEF, bold=True)
        ))

        # 숫자
        self._rules.append((
            QRegularExpression(r"\b[0-9]+\.?[0-9]*\b"),
            self._make_format(NUMBER)
        ))

        # 단일 줄 문자열 (작은따옴표)
        self._rules.append((
            QRegularExpression(r"'[^'\\]*(\\.[^'\\]*)*'"),
            self._make_format(STRING)
        ))

        # 단일 줄 문자열 (큰따옴표)
        self._rules.append((
            QRegularExpression(r'"[^"\\]*(\\.[^"\\]*)*"'),
            self._make_format(STRING)
        ))

        # f-string 접두어
        self._rules.append((
            QRegularExpression(r'\bf(?=["\'])'),
            self._make_format(STRING)
        ))

        # 주석 (#)
        self._comment_format = self._make_format(COMMENT, italic=True)
        self._rules.append((
            QRegularExpression(r"#[^\n]*"),
            self._comment_format
        ))

        # 삼중 따옴표 (멀티라인) — 별도 상태 관리
        self._tri_single_fmt = self._make_format(STRING)
        self._tri_double_fmt = self._make_format(STRING)

    def highlightBlock(self, text):
        """텍스트 블록 구문 강조"""
        # 단일 줄 규칙 적용
        for pattern, fmt in self._rules:
            match_iter = pattern.globalMatch(text)
            while match_iter.hasNext():
                match = match_iter.next()
                start = match.capturedStart()
                length = match.capturedLength()
                self.setFormat(start, length, fmt)

        # 삼중 따옴표 처리 (멀티라인 문자열)
        self._handle_multiline_strings(text)

    def _handle_multiline_strings(self, text):
        """삼중 따옴표 멀티라인 문자열 처리"""
        # State: 0 = 일반, 1 = ''' 내부, 2 = \"\"\" 내부
        in_multiline = self.previousBlockState()
        if in_multiline == -1:
            in_multiline = 0

        start = 0  # 멀티라인 시작 위치 (이전 블록에서 계속될 때 0부터)
        i = 0
        while i < len(text):
            if in_multiline == 0:
                # 삼중 따옴표 시작 검색
                if text[i:i+3] == '"""':
                    start = i
                    in_multiline = 2
                    i += 3
                elif text[i:i+3] == "'''":
                    start = i
                    in_multiline = 1
                    i += 3
                else:
                    i += 1
            elif in_multiline == 1:
                # ''' 종료 검색
                if text[i:i+3] == "'''":
                    self.setFormat(start, i + 3 - start, self._tri_single_fmt)
                    in_multiline = 0
                    i += 3
                else:
                    i += 1
            elif in_multiline == 2:
                # """ 종료 검색
                if text[i:i+3] == '"""':
                    self.setFormat(start, i + 3 - start, self._tri_double_fmt)
                    in_multiline = 0
                    i += 3
                else:
                    i += 1

        # 블록 끝까지 멀티라인이 닫히지 않은 경우
        if in_multiline != 0:
            fmt = self._tri_single_fmt if in_multiline == 1 else self._tri_double_fmt
            self.setFormat(start, len(text) - start, fmt)

        self.setCurrentBlockState(in_multiline)
