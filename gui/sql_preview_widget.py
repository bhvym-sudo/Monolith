from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem, QPushButton, QTextEdit, QFileDialog, QSplitter
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QColor
from engine import SQLFileInspector


class SQLScanWorker(QThread):
    progress = pyqtSignal(str, int)
    finished = pyqtSignal(dict)
    
    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path
    
    def run(self):
        inspector = SQLFileInspector()
        tables = inspector.inspect_sql_file(self.file_path, self.progress.emit)
        self.finished.emit(tables)


class SQLPreviewWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.current_file = None
        self.inspector = None
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        button_layout = QHBoxLayout()
        
        self.select_button = QPushButton("Select SQL File")
        self.select_button.setStyleSheet(self.get_button_style())
        self.select_button.clicked.connect(self.select_file)
        
        button_layout.addWidget(self.select_button)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        splitter = QSplitter(Qt.Horizontal)
        
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels(["Table Structure"])
        self.tree_widget.setStyleSheet(self.get_tree_style())
        self.tree_widget.itemClicked.connect(self.on_table_selected)
        
        self.info_widget = QTextEdit()
        self.info_widget.setReadOnly(True)
        self.info_widget.setStyleSheet("""
            QTextEdit {
                background-color: #1E1E1E;
                color: #DCDCDC;
                border: 1px solid #404040;
                font-family: Consolas, monospace;
                font-size: 11px;
                padding: 10px;
            }
        """)
        self.info_widget.setText("Select a SQL file to inspect its structure...")
        
        splitter.addWidget(self.tree_widget)
        splitter.addWidget(self.info_widget)
        splitter.setStretchFactor(0, 40)
        splitter.setStretchFactor(1, 60)
        
        layout.addWidget(splitter)
        
        self.setLayout(layout)
    
    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select SQL File",
            "",
            "SQL Files (*.sql);;All Files (*.*)"
        )
        
        if file_path:
            self.current_file = file_path
            self.scan_file(file_path)
    
    def scan_file(self, file_path):
        self.tree_widget.clear()
        self.info_widget.setText(f"Scanning {file_path}...\n")
        self.select_button.setEnabled(False)
        
        self.worker = SQLScanWorker(file_path)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.display_results)
        self.worker.start()
    
    def update_progress(self, message, progress):
        self.info_widget.append(message)
    
    def display_results(self, tables):
        self.select_button.setEnabled(True)
        self.tree_widget.clear()
        
        if not tables:
            self.info_widget.append("\nNo tables found in SQL file.")
            return
        self.inspector = SQLFileInspector()
        self.inspector.tables = tables
        
        summary = f"\n{'='*60}\n"
        summary += f"SCAN COMPLETE\n"
        summary += f"{'='*60}\n"
        summary += f"Total Tables: {len(tables)}\n\n"
        
        for table_name, info in sorted(tables.items()):
            root_item = QTreeWidgetItem([f"📊 {table_name}"])
            root_item.setForeground(0, QColor(100, 200, 255))
            root_item.setData(0, Qt.UserRole, table_name)
            
            columns_item = QTreeWidgetItem([f"Columns ({len(info['columns'])})"])
            for col in info['columns']:
                col_item = QTreeWidgetItem([f"  {col['name']} ({col['type']})"])
                columns_item.addChild(col_item)
            
            root_item.addChild(columns_item)
            
            row_item = QTreeWidgetItem([f"Estimated Rows: {info['row_count_estimate']:,}"])
            root_item.addChild(row_item)
            
            self.tree_widget.addTopLevelItem(root_item)
            
            summary += f"{table_name}:\n"
            summary += f"  - Columns: {len(info['columns'])}\n"
            summary += f"  - Estimated Rows: {info['row_count_estimate']:,}\n\n"
        
        self.info_widget.append(summary)
        self.info_widget.append("\nClick on a table name to view sample data...")
        self.tree_widget.expandAll()
    
    def on_table_selected(self, item, column):
        table_name = item.data(0, Qt.UserRole)
        if not table_name or not self.inspector:
            return
        
        table_info = self.inspector.get_table_info(table_name)
        if not table_info:
            return
        
        output = f"\n{'='*80}\n"
        output += f"TABLE: {table_name}\n"
        output += f"{'='*80}\n\n"
        
        output += f"Columns ({len(table_info['columns'])}):\n"
        for idx, col in enumerate(table_info['columns'], 1):
            output += f"  {idx}. {col['name']} ({col['type']})\n"
        
        output += f"\nTotal Rows: ~{table_info['row_count_estimate']:,}\n"
        
        if table_info['sample_data']:
            output += f"\nSample Data (first {len(table_info['sample_data'])} rows):\n"
            output += f"{'-'*80}\n"
            
            col_names = [col['name'] for col in table_info['columns']]
            output += " | ".join(f"{name[:15]:15}" for name in col_names) + "\n"
            output += f"{'-'*80}\n"
            
            for row in table_info['sample_data']:
                formatted_row = []
                for val in row:
                    val_str = str(val)[:15] if val else 'NULL'
                    formatted_row.append(f"{val_str:15}")
                output += " | ".join(formatted_row) + "\n"
        else:
            output += "\nNo sample data available.\n"
        
        output += f"\n{'='*80}\n"
        
        self.info_widget.setPlainText(output)
        self.tree_widget.expandAll()
    
    def get_tree_style(self):
        return """
            QTreeWidget {
                background-color: #1E1E1E;
                color: #DCDCDC;
                border: 1px solid #404040;
                outline: 0;
            }
            QTreeWidget::item:selected {
                background-color: #2D5A8C;
            }
            QTreeWidget::item:hover {
                background-color: #2D2D2D;
            }
        """
    
    def get_button_style(self):
        return """
            QPushButton {
                background-color: #2D5A8C;
                color: #FFFFFF;
                border: 1px solid #404040;
                padding: 8px 16px;
                border-radius: 3px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #3A6BA3;
            }
            QPushButton:pressed {
                background-color: #1E4066;
            }
        """
