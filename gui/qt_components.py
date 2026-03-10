import sys
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QComboBox, QLineEdit, QHeaderView, QAbstractItemView,
    QStyledItemDelegate, QMenu, QMessageBox, QFrame, QLabel
)
from PySide6.QtCore import Qt, Signal, Slot, QAbstractTableModel, QModelIndex
from PySide6.QtGui import QColor, QFont, QAction, QBrush

# 모던 디자인 색상 팔레트
COLORS = {
    'primary': '#6366F1',       # Indigo
    'primary_hover': '#4F46E5',
    'secondary': '#4B5563',     # Gray 600 (Lighter than surface)
    'background': '#111827',    # Gray 900 (Darker)
    'surface': '#1F2937',       # Gray 800
    'text': '#F3F4F6',          # Gray 100
    'text_secondary': '#9CA3AF',# Gray 400
    'accent': '#10B981',        # Emerald
    'danger': '#EF4444',        # Red
    'input_bg': '#374151',      # Gray 700
    'border': '#6B7280',        # Gray 500
    'success': '#10B981',       # Emerald (Same as accent)
}

# 액션 옵션 정의
ACTION_OPTIONS = [
    "click", "input", "input_password", "check_text", "check_url",
    "press_key", "hover",
    "switch_frame", "switch_default",
    "accept_alert", "dismiss_alert",
    "drag_source", "drop_target",
    "comment",
    "api_get", "api_post", "api_put", "api_delete", "api_assert"
]

class ModernButton(QPushButton):
    """모던 스타일 버튼"""
    def __init__(self, text, bg_color=COLORS['primary'], hover_color=COLORS['primary_hover'], icon=None):
        super().__init__(text)
        if icon:
            self.setIcon(icon)
        
        self.bg_color = bg_color
        self.hover_color = hover_color
        
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg_color};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                font-family: 'Segoe UI';
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
            QPushButton:pressed {{
                background-color: {bg_color};
            }}
        """)
        self.setCursor(Qt.PointingHandCursor)

class StepTableModel(QAbstractTableModel):
    """테스트 스텝 데이터 모델 (최적화: 대량 데이터 렌더링)"""
    dataChangedSignal = Signal()
    stepsChanged = Signal()  # 스텝 변경 시 Code Preview 갱신용

    def __init__(self, steps_data=None):
        super().__init__()
        self._data = steps_data if steps_data is not None else []
        self._headers = ["No", "Step Name", "Action", "Value", "Locator"]

    def rowCount(self, parent=QModelIndex()):
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
        return len(self._headers)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        row = index.row()
        col = index.column()
        
        # Safe access to avoid errors if data is corrupted
        if row >= len(self._data): 
            return None
            
        step = self._data[row]

        if role == Qt.DisplayRole or role == Qt.EditRole:
            if col == 0:
                return str(row + 1)
            elif col == 1:
                return step.get("name", "")
            elif col == 2:
                return step.get("action", "click")
            elif col == 3:
                # [FIX]: Only return value if it exists, don't auto-fill defaults unless needed
                return step.get("value", "")
            elif col == 4:
                # locator가 dict나 str일 수 있음
                loc = step.get("locator", "")
                if isinstance(loc, dict):
                    return f"{loc.get('type', '')}={loc.get('value', '')}"
                return str(loc)

        elif role == Qt.TextAlignmentRole:
            if col == 0:
                return Qt.AlignCenter
            return Qt.AlignLeft | Qt.AlignVCenter

        elif role == Qt.BackgroundRole:
            action = step.get("action", "")
            if action == "comment":
                return QBrush(QColor("#374151"))  # Dark Gray
            elif action.startswith("check"):
                return QBrush(QColor("#065F46"))  # Dark Green hint
            elif action == "input_password":
                return QBrush(QColor("#7F1D1D"))  # Dark Red hint
        
        elif role == Qt.ForegroundRole:
             if col == 0:
                 return QBrush(QColor(COLORS['text_secondary']))
             return QBrush(QColor(COLORS['text']))

        elif role == Qt.ToolTipRole:
            if col == 3:
                return "엑셀 변수는 {변수명} 형식으로 입력하세요"
            elif col == 2:
                return "더블 클릭하여 액션을 변경하세요"

        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self._headers[section]
        return None

    def setData(self, index, value, role=Qt.EditRole):
        if not index.isValid() or role != Qt.EditRole:
            return False

        row = index.row()
        col = index.column()
        
        if col == 1:
            self._data[row]["name"] = value
        elif col == 2:
            self._data[row]["action"] = value
        elif col == 3:
            self._data[row]["value"] = value
        
        self.dataChanged.emit(index, index, [role])
        self.stepsChanged.emit()
        return True

    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags
        
        col = index.column()
        # No와 Locator는 수정 불가 (Locator는 스캔으로만 변경 권장)
        if col == 0 or col == 4:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable

    def add_step(self, step):
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
        self._data.append(step)
        self.endInsertRows()
        self.stepsChanged.emit()

    def remove_step(self, row):
        if 0 <= row < self.rowCount():
            self.beginRemoveRows(QModelIndex(), row, row)
            del self._data[row]
            self.endRemoveRows()
            # row 번호 재정렬을 위해 전체 갱신 신호 (No 컬럼 때문에)
            self.dataChanged.emit(self.index(row, 0), self.index(self.rowCount()-1, 0))
            self.stepsChanged.emit()

    def move_step(self, row, direction):
        new_row = row + direction
        if 0 <= new_row < self.rowCount():
            self.beginMoveRows(QModelIndex(), row, row, QModelIndex(), new_row if direction > 0 else new_row)
            self._data[row], self._data[new_row] = self._data[new_row], self._data[row]
            self.endMoveRows()
            self.stepsChanged.emit()
            return True
        return False
    
    def get_step(self, row):
        if 0 <= row < self.rowCount():
            return self._data[row]
        return None

    def clear(self):
        self.beginResetModel()
        self._data.clear()
        self.endResetModel()
        self.stepsChanged.emit()

class ActionDelegate(QStyledItemDelegate):
    """Action 컬럼을 콤보박스로 표시하기 위한 델리게이트"""
    def __init__(self, parent=None):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        if index.column() == 2:  # Action Column
            editor = QComboBox(parent)
            editor.addItems(ACTION_OPTIONS)
            return editor
        return super().createEditor(parent, option, index)

    def setEditorData(self, editor, index):
        if index.column() == 2:
            value = index.model().data(index, Qt.EditRole)
            editor.setCurrentText(value)
        else:
            super().setEditorData(editor, index)

    def setModelData(self, editor, model, index):
        if index.column() == 2:
            model.setData(index, editor.currentText(), Qt.EditRole)
        else:
            super().setModelData(editor, model, index)

