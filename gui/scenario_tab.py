"""
시나리오 디자인 탭 모듈

브라우저 제어, 요소 스캔, 스텝 테이블 관리를 담당합니다.
Inspector-Style 피커 모드 포함.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableView, QHeaderView,
    QLineEdit, QLabel, QMessageBox, QFileDialog, QFrame,
    QComboBox, QAbstractItemView
)
from PySide6.QtCore import Qt, Signal, Slot, QTimer

import config
from gui.qt_components import StepTableModel, ActionDelegate, ModernButton, COLORS


class ScenarioTab(QWidget):
    """시나리오 디자인 탭 위젯"""

    # 시그널: 외부 연동
    status_message = Signal(str, int)  # (message, timeout_ms)
    steps_changed = Signal()  # Code Preview 갱신용

    def __init__(self, browser, scanner, parent=None):
        super().__init__(parent)
        self.browser = browser
        self.scanner = scanner
        self.steps_data = []  # List[Dict] shared with model

        # Inspector 피커 모드 상태
        self._picker_active = False
        self._picker_timer = None

        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)

        # ── Left Panel (Controls) ──
        left_panel = QFrame()
        left_panel.setFixedWidth(350)
        left_panel.setStyleSheet(
            f"background-color: {COLORS['surface']}; "
            f"border-right: 1px solid {COLORS['border']};"
        )
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
        btn_scan.setShortcut("F2")
        grp_scan.layout().addWidget(btn_scan)

        # Inspector 피커 모드 버튼
        self.btn_picker = ModernButton("🔍 피커 모드 OFF", COLORS['secondary'])
        self.btn_picker.clicked.connect(self._toggle_picker_mode)
        grp_scan.layout().addWidget(self.btn_picker)

        btn_url = ModernButton("URL 검증 추가", COLORS['secondary'])
        btn_url.clicked.connect(self.cmd_add_url_check)
        grp_scan.layout().addWidget(btn_url)
        left_layout.addWidget(grp_scan)

        # Inspector 요소 정보 미리보기 패널
        self.grp_inspector = self._create_group("🔎 Inspector Preview")
        self.lbl_inspector_tag = QLabel("—")
        self.lbl_inspector_tag.setStyleSheet(f"color: {COLORS['accent']}; font-size: 13px; font-family: Consolas;")
        self.grp_inspector.layout().addWidget(self.lbl_inspector_tag)
        self.lbl_inspector_loc = QLabel("—")
        self.lbl_inspector_loc.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px; font-family: Consolas;")
        self.lbl_inspector_loc.setWordWrap(True)
        self.grp_inspector.layout().addWidget(self.lbl_inspector_loc)
        self.grp_inspector.setVisible(False)
        left_layout.addWidget(self.grp_inspector)

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

        # ── Right Panel (Table) ──
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
        self.table_view.setColumnWidth(0, 40)
        self.table_view.setColumnWidth(1, 150)
        self.table_view.setColumnWidth(2, 100)
        self.table_view.setColumnWidth(3, 150)

        # Selection Changed → Browser Highlight
        self.table_view.selectionModel().selectionChanged.connect(
            self._on_table_selection_changed
        )

        right_layout.addWidget(self.table_view)
        layout.addWidget(right_panel)

        # Connect stepsChanged for external listeners
        self.step_model.stepsChanged.connect(self.steps_changed.emit)

    # ── Actions ──

    @Slot()
    def cmd_open_browser(self):
        from gui.qt_app import BrowserThread
        url = self.url_input.text()
        b_type = self.browser_combo.currentText().lower()
        self.status_message.emit(f"Opening {b_type}...", 0)

        self.browser_thread = BrowserThread(self.browser, url, b_type)
        self.browser_thread.finished.connect(self._on_browser_opened)
        self.browser_thread.start()

        self.sender().setEnabled(False)
        self._temp_btn = self.sender()

    @Slot(bool, str)
    def _on_browser_opened(self, success, msg):
        self._temp_btn.setEnabled(True)
        if success:
            self.status_message.emit("Browser Ready", 5000)
            QMessageBox.information(self, "Success", msg)
        else:
            self.status_message.emit("Browser Failed", 0)
            QMessageBox.critical(self, "Error", msg)

    @Slot()
    def cmd_scan_element(self):
        try:
            sel_text = self.browser.get_selected_text()
            if sel_text:
                step = self.scanner.create_text_validation_step(sel_text)
                self.step_model.add_step(step)
                self.status_message.emit("Text verification added", 3000)
                return

            el = self.browser.get_selected_element()
            if not el:
                QMessageBox.warning(self, "Warning", "Select an element in the browser first!")
                return

            shadow_path = None
            if self.browser.is_in_shadow_dom(el):
                shadow_path = self.browser.get_shadow_dom_path(el)

            step = self.scanner.create_step_data(el, shadow_path=shadow_path)
            self.step_model.add_step(step)
            self.browser.highlight_element(element=el)
            self.status_message.emit("Element added", 3000)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Scan failed: {e}")

    @Slot()
    def cmd_add_url_check(self):
        if self.browser.driver:
            current = self.browser.driver.current_url
            step = self.scanner.create_url_validation_step(current)
            self.step_model.add_step(step)
            self.status_message.emit("URL check added", 3000)

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
    def cmd_save(self):
        from utils.file_manager import save_to_json
        fname, _ = QFileDialog.getSaveFileName(self, "Save Scenario", "", "JSON Files (*.json)")
        if fname:
            save_to_json(fname, self.url_input.text(), self.steps_data)
            self.status_message.emit(f"Saved to {fname}", 3000)

    @Slot()
    def cmd_load(self):
        from utils.file_manager import load_from_json
        fname, _ = QFileDialog.getOpenFileName(self, "Load Scenario", "", "JSON Files (*.json)")
        if fname:
            url, steps = load_from_json(fname)
            self.url_input.setText(url)
            self.step_model.clear()
            for s in steps:
                self.step_model.add_step(s)
            self.status_message.emit(f"Loaded {fname}", 3000)

    def _on_table_selection_changed(self, selected, deselected):
        indexes = selected.indexes()
        if indexes:
            row = indexes[0].row()
            step = self.step_model.get_step(row)
            if step:
                if self.browser.driver:
                    try:
                        self.browser.highlight_element(
                            locator_type=step['type'],
                            locator_value=step['locator']
                        )
                    except:
                        pass

    # ── Inspector 피커 모드 ──

    def _toggle_picker_mode(self):
        """피커 모드 토글"""
        if self._picker_active:
            self._disable_picker()
        else:
            self._enable_picker()

    def _enable_picker(self):
        """Inspector 피커 모드 활성화"""
        if not self.browser.driver:
            QMessageBox.warning(self, "Warning", "먼저 브라우저를 열어주세요!")
            return

        self._picker_active = True
        self.btn_picker.setText("🔍 피커 모드 ON")
        self.btn_picker.setStyleSheet(
            f"QPushButton {{ background-color: {COLORS['accent']}; color: white; "
            f"border: none; border-radius: 6px; padding: 8px 16px; font-weight: bold; }}"
        )
        self.grp_inspector.setVisible(True)

        # 브라우저에 Inspector JS 주입
        try:
            self.browser.enable_inspector_mode()
        except AttributeError:
            # inspector 모드 미구현 시 폴백 (나중에 구현)
            pass

        # 폴링 타이머 시작 (200ms)
        self._picker_timer = QTimer(self)
        self._picker_timer.timeout.connect(self._poll_picker)
        self._picker_timer.start(200)

        self.status_message.emit("🔍 피커 모드 ON — 브라우저에서 요소를 클릭하세요", 0)

    def _disable_picker(self):
        """Inspector 피커 모드 비활성화"""
        self._picker_active = False
        self.btn_picker.setText("🔍 피커 모드 OFF")
        self.btn_picker.setStyleSheet("")
        self.grp_inspector.setVisible(False)

        if self._picker_timer:
            self._picker_timer.stop()
            self._picker_timer = None

        try:
            self.browser.disable_inspector_mode()
        except AttributeError:
            pass

        self.status_message.emit("피커 모드 종료", 3000)

    def _poll_picker(self):
        """피커 모드: 주기적으로 선택된 요소 확인"""
        if not self.browser.driver:
            self._disable_picker()
            return

        try:
            # 피커로 선택된 요소 가져오기
            info = self.browser.get_picked_element_info()
            if info:
                self.lbl_inspector_tag.setText(
                    f"<{info.get('tag', '?')}> {info.get('id', '')} .{info.get('class', '')}"
                )
                self.lbl_inspector_loc.setText(f"Locator: {info.get('locator', '—')}")

                # 요소가 클릭되었으면 스텝에 추가
                if info.get('picked'):
                    el = info.get('element')
                    if el:
                        step = self.scanner.create_step_data(el)
                        self.step_model.add_step(step)
                        self.status_message.emit("✅ 요소가 스텝에 추가되었습니다", 3000)
                        # 선택 상태 초기화
                        self.browser.clear_picked_element()
        except Exception:
            pass

    # ── Helpers ──

    def _create_group(self, title):
        group = QFrame()
        group.setStyleSheet(
            f"background-color: {COLORS['background']}; border-radius: 6px; padding: 10px;"
        )
        vbox = QVBoxLayout(group)
        lbl = QLabel(title)
        lbl.setStyleSheet(
            f"font-weight: bold; color: {COLORS['primary']}; margin-bottom: 5px;"
        )
        vbox.addWidget(lbl)
        return group
