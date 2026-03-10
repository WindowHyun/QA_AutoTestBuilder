"""
데이터 관리 탭 모듈

DDT(Data-Driven Testing) 데이터 파일 로드/편집/저장을 담당합니다.
JSON, CSV, Excel 지원.
"""

import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableView, QHeaderView,
    QLabel, QFrame, QMessageBox, QFileDialog
)
from PySide6.QtCore import Signal, Slot
import pandas as pd

from gui.qt_components import ModernButton, COLORS
from gui.data_model import DataFrameModel


class DataTab(QWidget):
    """데이터 관리 탭 위젯"""

    status_message = Signal(str, int)
    data_path_changed = Signal(str)  # DDT 파일 경로 변경 알림

    def __init__(self, parent=None):
        super().__init__(parent)
        self.data_path = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Data Load Card
        card = QFrame()
        card.setStyleSheet(
            f"background-color: {COLORS['surface']}; padding: 15px; border-radius: 8px;"
        )
        vbox = QVBoxLayout(card)

        lbl_title = QLabel("📊 Data-Driven Testing (DDT)")
        lbl_title.setStyleSheet(
            f"font-size: 14px; font-weight: bold; color: {COLORS['primary']};"
        )
        vbox.addWidget(lbl_title)

        lbl_desc = QLabel(
            "Load a JSON, CSV, or Excel file to parameterize your test values.\n"
            "Use {ColumnName} in the 'Value' field of your test steps."
        )
        lbl_desc.setStyleSheet(f"color: {COLORS['text_secondary']}; margin-bottom: 10px;")
        vbox.addWidget(lbl_desc)

        hbox = QHBoxLayout()
        btn_data = ModernButton("데이터 파일 로드", COLORS['accent'])
        btn_data.clicked.connect(self.cmd_load_data)
        hbox.addWidget(btn_data)

        self.lbl_data_status = QLabel("No file loaded")
        self.lbl_data_status.setStyleSheet(
            f"color: {COLORS['text_secondary']}; margin-left: 10px;"
        )
        hbox.addWidget(self.lbl_data_status)
        hbox.addStretch()
        vbox.addLayout(hbox)
        layout.addWidget(card)

        # DataFrame Viewer
        self.df_model = DataFrameModel()
        self.df_view = QTableView()
        self.df_view.setModel(self.df_model)
        self.df_view.setStyleSheet(
            f"background-color: {COLORS['surface']}; gridline-color: {COLORS['border']};"
        )
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

    # ── Actions ──

    @Slot()
    def cmd_load_data(self):
        """JSON/CSV/Excel 데이터 파일 로드"""
        fname, _ = QFileDialog.getOpenFileName(
            self, "Select Data File", "",
            "Data Files (*.json *.csv *.xlsx *.xls);;"
            "JSON Files (*.json);;CSV Files (*.csv);;Excel Files (*.xlsx *.xls)"
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
                self.lbl_data_status.setStyleSheet("color: #10B981; margin-left: 10px;")
                self.status_message.emit(f"Data loaded: {fname}", 3000)
                self.data_path_changed.emit(fname)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load data file: {e}")

    @Slot()
    def cmd_save_data(self):
        """데이터 파일 저장"""
        if not self.data_path:
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

            QMessageBox.information(
                self, "Success", f"Data saved: {os.path.basename(self.data_path)}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save data: {e}")

    @Slot()
    def cmd_add_row(self):
        idx = self.df_view.currentIndex()
        row = idx.row() if idx.isValid() else self.df_model.rowCount()
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
