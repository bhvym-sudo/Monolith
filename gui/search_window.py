from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QLabel, QFileDialog, QApplication
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QColor, QTextCharFormat, QTextDocument, QTextCursor
from engine.database import DatabaseManager
from .highlight_delegate import HighlightDelegate
import csv


class SearchWorker(QThread):
    results_ready = pyqtSignal(list)
    
    def __init__(self, db_manager, search_term):
        super().__init__()
        self.db_manager = db_manager
        self.search_term = search_term
    
    def run(self):
        results = []
        tables = self.db_manager.get_tables()
        
        for table in tables:
            if table.endswith('_filtered'):
                continue
            
            try:
                # Get all data from table
                query = f"SELECT * FROM {table}"
                data = self.db_manager.execute_query(query)
                
                if not data:
                    continue
                
                # Get column names
                columns_result = self.db_manager.execute_query(f"PRAGMA table_info({table})")
                columns = [col[1] for col in columns_result]
                
                # Search through all rows and columns
                seen_rows = set()  # Track rows already added
                for row_idx, row in enumerate(data):
                    row_has_match = False
                    matched_column = None
                    
                    for col_idx, cell_value in enumerate(row):
                        if cell_value is None:
                            continue
                        
                        cell_str = str(cell_value).lower()
                        search_lower = self.search_term.lower()
                        
                        # Check if search term is contained in cell value
                        if search_lower in cell_str:
                            row_has_match = True
                            matched_column = columns[col_idx]
                            break  # Found match in this row
                    
                    # Add row only once if it has a match
                    if row_has_match:
                        row_key = (table, row_idx)
                        if row_key not in seen_rows:
                            seen_rows.add(row_key)
                            results.append({
                                'table': table,
                                'matched_column': matched_column,
                                'row': row,
                                'columns': columns,
                                'match_term': self.search_term
                            })
            except Exception as e:
                continue
        
        self.results_ready.emit(results)


class SearchWindow(QDialog):
    def __init__(self, database_manager, parent=None):
        super().__init__(parent)
        self.db_manager = database_manager
        self.search_worker = None
        self.highlight_delegate = HighlightDelegate()
        self.current_results = []  # Store current search results
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Database Search - Full Row Display")
        # Much larger window size for full row display
        self.setGeometry(100, 50, 1800, 950)
        self.setStyleSheet("""
            QDialog {
                background-color: #1E1E1E;
                color: #DCDCDC;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Search bar at top
        search_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter search term (e.g., 'nazz' to find 'nazzan')...")
        self.search_input.returnPressed.connect(self.perform_search)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #2D2D2D;
                color: #DCDCDC;
                border: 1px solid #404040;
                padding: 10px;
                border-radius: 3px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #64C8FF;
            }
        """)
        
        self.search_btn = QPushButton("Search")
        self.search_btn.clicked.connect(self.perform_search)
        self.search_btn.setStyleSheet(self.get_button_style())
        
        self.export_btn = QPushButton("Export Results")
        self.export_btn.clicked.connect(self.export_results)
        self.export_btn.setEnabled(False)
        self.export_btn.setStyleSheet(self.get_button_style())
        
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_btn)
        search_layout.addWidget(self.export_btn)
        
        layout.addLayout(search_layout)
        
        # Status label
        self.status_label = QLabel("Enter a search term to begin...")
        self.status_label.setStyleSheet("color: #9CDCFE; padding: 5px; font-size: 12px;")
        layout.addWidget(self.status_label)
        
        # Results table at bottom
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(2)
        self.results_table.setHorizontalHeaderLabels(["Table/File", "Full Row Data"])
        
        # Force scrollbars and disable word wrap
        self.results_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.results_table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.results_table.setWordWrap(False)
        self.results_table.setTextElideMode(Qt.ElideNone)
        
        self.results_table.setStyleSheet("""
            QTableWidget {
                background-color: #1E1E1E;
                alternate-background-color: #252525;
                color: #DCDCDC;
                border: 1px solid #404040;
                gridline-color: #2D2D2D;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QTableWidget::item:selected {
                background-color: #2D5A8C;
            }
            QHeaderView::section {
                background-color: #2D2D2D;
                color: #64C8FF;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
            QScrollBar:vertical {
                background-color: #2D2D2D;
                width: 16px;
                border: 1px solid #404040;
            }
            QScrollBar::handle:vertical {
                background-color: #505050;
                border-radius: 4px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #606060;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar:horizontal {
                background-color: #2D2D2D;
                height: 16px;
                border: 1px solid #404040;
            }
            QScrollBar::handle:horizontal {
                background-color: #505050;
                border-radius: 4px;
                min-width: 30px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: #606060;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
        """)
        self.results_table.horizontalHeader().setStretchLastSection(False)
        self.results_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.results_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        
        # Set custom delegate for highlighting on column 1 (value column)
        self.results_table.setItemDelegateForColumn(1, self.highlight_delegate)
        self.results_table.setAlternatingRowColors(True)
        
        # Connect double-click to copy function
        self.results_table.cellDoubleClicked.connect(self.copy_row_data)
        
        layout.addWidget(self.results_table, 1)
        
        self.setLayout(layout)
    
    def perform_search(self):
        search_term = self.search_input.text().strip()
        if not search_term:
            self.status_label.setText("Please enter a search term")
            return
        
        self.status_label.setText(f"Searching for '{search_term}'...")
        # Update highlight delegate with search term
        self.highlight_delegate.set_search_term(search_term)
        
        self.search_btn.setEnabled(False)
        self.results_table.setRowCount(0)
        
        # Start background search
        self.search_worker = SearchWorker(self.db_manager, search_term)
        self.search_worker.results_ready.connect(self.display_results)
        self.search_worker.start()
    
    def display_results(self, results):
        self.search_btn.setEnabled(True)
        self.current_results = results  # Store for export
        
        if not results:
            self.status_label.setText(f"No matches found")
            self.results_table.setRowCount(0)
            self.export_btn.setEnabled(False)
            return
        
        self.export_btn.setEnabled(True)
        self.status_label.setText(f"Found {len(results)} matching rows")
        self.results_table.setRowCount(len(results))
        
        for idx, result in enumerate(results):
            # Column 0: Table name
            table_item = QTableWidgetItem(result['table'])
            table_item.setForeground(QColor("#9CDCFE"))
            self.results_table.setItem(idx, 0, table_item)
            
            # Column 1: Full row data formatted as "Column: Value"
            row_data = result['row']
            columns = result['columns']
            
            # Format as multi-line or single line with separators
            row_display = []
            for col_name, col_value in zip(columns, row_data):
                if col_value is not None and str(col_value).strip():
                    row_display.append(f"{col_name}: {col_value}")
            
            full_row_text = "  |  ".join(row_display)
            
            value_item = QTableWidgetItem(full_row_text)
            value_item.setForeground(QColor("#DCDCDC"))
            self.results_table.setItem(idx, 1, value_item)
    
    def copy_row_data(self, row, column):
        """Copy full row data to clipboard on double-click"""
        if row < len(self.current_results):
            result = self.current_results[row]
            row_data = result['row']
            columns = result['columns']
            
            # Format row data
            row_text = []
            for col_name, col_value in zip(columns, row_data):
                if col_value is not None:
                    row_text.append(f"{col_name}: {col_value}")
            
            full_text = "\n".join(row_text)
            
            # Copy to clipboard
            clipboard = QApplication.clipboard()
            clipboard.setText(full_text)
            
            self.status_label.setText(f"Row data copied to clipboard!")
    
    def export_results(self):
        """Export search results to CSV file"""
        if not self.current_results:
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Search Results",
            "search_results.csv",
            "CSV Files (*.csv)"
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                # Get all unique columns from all results
                all_columns = set(['Table', 'Matched_Column'])
                for result in self.current_results:
                    all_columns.update(result['columns'])
                
                all_columns = ['Table', 'Matched_Column'] + sorted([c for c in all_columns if c not in ['Table', 'Matched_Column']])
                
                writer = csv.writer(csvfile)
                writer.writerow(all_columns)
                
                # Write each result row
                for result in self.current_results:
                    row_dict = {col: val for col, val in zip(result['columns'], result['row'])}
                    row_dict['Table'] = result['table']
                    row_dict['Matched_Column'] = result.get('matched_column', '')
                    
                    csv_row = [row_dict.get(col, '') for col in all_columns]
                    writer.writerow(csv_row)
            
            self.status_label.setText(f"Exported {len(self.current_results)} rows to {file_path}")
            
        except Exception as e:
            self.status_label.setText(f"Export failed: {str(e)}")
    
    def get_button_style(self):
        return """
            QPushButton {
                background-color: #2D5A8C;
                color: #FFFFFF;
                border: 1px solid #404040;
                padding: 10px 20px;
                border-radius: 3px;
                font-weight: bold;
                font-size: 13px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #3A6BA3;
            }
            QPushButton:pressed {
                background-color: #1E4066;
            }
            QPushButton:disabled {
                background-color: #2D2D2D;
                color: #777777;
            }
        """
