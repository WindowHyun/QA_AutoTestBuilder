from PySide6.QtCore import Qt, QAbstractTableModel, Signal, QModelIndex
import pandas as pd

class DataFrameModel(QAbstractTableModel):
    """Pandas DataFrame을 QTableView에 연결하기 위한 모델"""
    
    def __init__(self, data=None):
        super().__init__()
        if data is None:
             self._df = pd.DataFrame()
        else:
            self._df = data

    def rowCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return self._df.shape[0]

    def columnCount(self, parent=QModelIndex()):
        if parent.isValid():
             return 0
        return self._df.shape[1]

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
            
        row = index.row()
        col = index.column()
        
        if role == Qt.DisplayRole or role == Qt.EditRole:
            val = self._df.iloc[row, col]
            # NaN 처리
            if pd.isna(val):
                return ""
            return str(val)
            
        return None

    def setData(self, index, value, role=Qt.EditRole):
        if not index.isValid() or role != Qt.EditRole:
             return False
        
        row = index.row()
        col = index.column()
        
        try:
            # 원래 데이터 타입 유지 노력
            self._df.iloc[row, col] = value
            self.dataChanged.emit(index, index, [role])
            return True
        except Exception:
            return False

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return str(self._df.columns[section])
            elif orientation == Qt.Vertical:
                 return str(self._df.index[section])
        return None

    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable

    def insertRows(self, position, rows, parent=QModelIndex()):
        self.beginInsertRows(parent, position, position + rows - 1)
        
        # 기본 초기값 (Empty String)
        default_row = pd.DataFrame([[""] * self._df.shape[1]], columns=self._df.columns)
        
        for _ in range(rows):
            self._df = pd.concat([self._df.iloc[:position], default_row, self._df.iloc[position:]]).reset_index(drop=True)
            
        self.endInsertRows()
        return True

    def removeRows(self, position, rows, parent=QModelIndex()):
        if self._df.shape[0] <= 0:
            return False
            
        self.beginRemoveRows(parent, position, position + rows - 1)
        self._df.drop(self._df.index[range(position, position + rows)], inplace=True)
        self._df.reset_index(drop=True, inplace=True)
        self.endRemoveRows()
        return True

    def insertColumns(self, position, columns, parent=QModelIndex()):
        self.beginInsertColumns(parent, position, position + columns - 1)
        
        for i in range(columns):
            col_name = f"New Column {self._df.shape[1] + 1}"
            self._df.insert(position + i, col_name, "")
            
        self.endInsertColumns()
        return True

    def removeColumns(self, position, columns, parent=QModelIndex()):
        if self._df.shape[1] <= 0:
            return False
            
        self.beginRemoveColumns(parent, position, position + columns - 1)
        
        cols_to_drop = self._df.columns[range(position, position + columns)]
        self._df.drop(columns=cols_to_drop, inplace=True)
        
        self.endRemoveColumns()
        return True

    def get_dataframe(self):
        return self._df

    def set_dataframe(self, df):
        self.beginResetModel()
        self._df = df
        self.endResetModel()
