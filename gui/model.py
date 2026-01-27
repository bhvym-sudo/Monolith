from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex, QRect, QTimer
from PyQt5.QtGui import QColor, QFont


class LazyLoadingTableModel(QAbstractTableModel):
    CHUNK_SIZE = 100

    def __init__(self, database_manager, table_name):
        super().__init__()
        self.db_manager = database_manager
        self.table_name = table_name
        self.rows_cache = {}
        self.columns = []
        self.total_rows = 0
        
        self._load_metadata()

    def _load_metadata(self):
        self.columns = self.db_manager.get_table_columns(self.table_name)
        self.total_rows = self.db_manager.get_row_count(self.table_name)

    def _get_rows(self, start_row, end_row):
        for row_num in range(start_row, end_row + 1):
            if row_num not in self.rows_cache:
                offset = (row_num // self.CHUNK_SIZE) * self.CHUNK_SIZE
                limit = self.CHUNK_SIZE
                rows = self.db_manager.get_table_data(self.table_name, offset, limit)
                
                for i, row in enumerate(rows):
                    self.rows_cache[offset + i] = row
                
                break

        return [self.rows_cache.get(i, [None] * len(self.columns)) for i in range(start_row, end_row + 1)]

    def rowCount(self, parent=QModelIndex()):
        return self.total_rows

    def columnCount(self, parent=QModelIndex()):
        return len(self.columns)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        if role == Qt.DisplayRole:
            row_num = index.row()
            if row_num not in self.rows_cache:
                self._get_rows(row_num, row_num)
            
            row_data = self.rows_cache.get(row_num)
            if row_data and index.column() < len(row_data):
                value = row_data[index.column()]
                if value is None:
                    return 'NULL'
                return str(value)[:200]
            return ''

        if role == Qt.BackgroundRole:
            return QColor(45, 45, 45) if index.row() % 2 == 0 else QColor(50, 50, 50)

        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                if section < len(self.columns):
                    return self.columns[section]
            else:
                return str(section + 1)
        
        return None

    def set_table(self, table_name):
        self.beginResetModel()
        self.table_name = table_name
        self.rows_cache.clear()
        self._load_metadata()
        self.endResetModel()

    def filter_table(self, where_clause):
        try:
            query = f"SELECT * FROM {self.table_name} WHERE {where_clause}"
            self.db_manager.get_connection().execute(query)
            temp_table = f"{self.table_name}_filtered"
            
            if self.db_manager.table_exists(temp_table):
                self.db_manager.drop_table(temp_table)
            
            self.db_manager.get_connection().execute(f"CREATE TABLE {temp_table} AS SELECT * FROM {self.table_name} WHERE {where_clause}")
            
            self.beginResetModel()
            self.table_name = temp_table
            self.rows_cache.clear()
            self._load_metadata()
            self.endResetModel()
            return True
        except Exception as e:
            print(f"Filter error: {str(e)}")
            return False

    def reset_filter(self, original_table_name):
        try:
            temp_table = f"{original_table_name}_filtered"
            if self.db_manager.table_exists(temp_table):
                self.db_manager.drop_table(temp_table)
            
            self.beginResetModel()
            self.table_name = original_table_name
            self.rows_cache.clear()
            self._load_metadata()
            self.endResetModel()
        except Exception as e:
            print(f"Reset filter error: {str(e)}")
