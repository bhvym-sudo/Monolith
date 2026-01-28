from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QSplitter, QTreeWidget, QTreeWidgetItem, QTableView, QHeaderView, QLabel, QMessageBox
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtGui import QIcon, QColor, QFont
from .model import LazyLoadingTableModel
from .search_window import SearchWindow


class NexusEngineWidget(QWidget):
    table_selected = pyqtSignal(str)

    def __init__(self, database_manager):
        super().__init__()
        self.db_manager = database_manager
        self.current_table = None
        self.table_model = None
        self.init_ui()
        self.load_tables()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        splitter = QSplitter(Qt.Horizontal)

        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabel("Tables")
        self.tree_widget.setStyleSheet(self.get_tree_style())
        self.tree_widget.itemClicked.connect(self.on_table_selected)
        self.tree_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_widget.customContextMenuRequested.connect(self.show_table_context_menu)

        self.table_view = QTableView()
        self.table_view.setStyleSheet(self.get_table_view_style())
        self.table_view.horizontalHeader().setStretchLastSection(True)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table_view.setAlternatingRowColors(True)

        splitter.addWidget(self.tree_widget)
        splitter.addWidget(self.table_view)
        splitter.setStretchFactor(0, 25)
        splitter.setStretchFactor(1, 75)

        main_layout.addWidget(splitter, 1)

        # Bottom buttons
        button_layout = QHBoxLayout()
        
        self.delete_table_button = QPushButton("Delete Selected Table")
        self.delete_table_button.setStyleSheet("""
            QPushButton {
                background-color: #A12525;
                color: #FFFFFF;
                border: 1px solid #404040;
                padding: 10px 20px;
                border-radius: 3px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #C92D2D;
            }
            QPushButton:pressed {
                background-color: #7A1D1D;
            }
            QPushButton:disabled {
                background-color: #2D2D2D;
                color: #777777;
            }
        """)
        self.delete_table_button.setEnabled(False)
        self.delete_table_button.clicked.connect(self.delete_selected_table)
        
        button_layout.addWidget(self.delete_table_button)
        button_layout.addStretch()
        
        self.search_window_button = QPushButton("Search Database")
        self.search_window_button.setStyleSheet("""
            QPushButton {
                background-color: #2D5A8C;
                color: #FFFFFF;
                border: 1px solid #404040;
                padding: 10px 20px;
                border-radius: 3px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #3A6BA3;
            }
            QPushButton:pressed {
                background-color: #1E4066;
            }
        """)
        self.search_window_button.clicked.connect(self.open_search_window)
        
        button_layout.addWidget(self.search_window_button)
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)

    def load_tables(self):
        self.tree_widget.clear()
        tables = self.db_manager.get_tables()
        for table in tables:
            if not table.endswith('_filtered'):
                item = QTreeWidgetItem([table])
                self.tree_widget.addTopLevelItem(item)

    def on_table_selected(self, item, column):
        table_name = item.text(0)
        if not table_name.endswith('_filtered'):
            self.current_table = table_name
            self.table_model = LazyLoadingTableModel(self.db_manager, table_name)
            self.table_view.setModel(self.table_model)
            self.delete_table_button.setEnabled(True)
    
    def show_table_context_menu(self, position):
        """Show right-click context menu on table"""
        item = self.tree_widget.itemAt(position)
        if item:
            from PyQt5.QtWidgets import QMenu
            menu = QMenu()
            delete_action = menu.addAction("Delete Table")
            action = menu.exec_(self.tree_widget.mapToGlobal(position))
            
            if action == delete_action:
                self.delete_table(item.text(0))
    
    def delete_selected_table(self):
        """Delete currently selected table"""
        if self.current_table:
            self.delete_table(self.current_table)
    
    def delete_table(self, table_name):
        """Delete a table from database"""
        if table_name.startswith('_ingestion_metadata'):
            QMessageBox.warning(self, "Cannot Delete", "System tables cannot be deleted!")
            return
        
        reply = QMessageBox.question(
            self,
            'Delete Table',
            f'Are you sure you want to delete table "{table_name}"?\\n\\nThis action cannot be undone!',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.db_manager.drop_table(table_name)
                
                # Remove from ingestion metadata
                self.db_manager.get_connection().execute(
                    "DELETE FROM _ingestion_metadata WHERE table_name = ?",
                    [table_name]
                )
                
                # Reload tables list
                self.load_tables()
                
                # Clear table view
                self.table_view.setModel(None)
                self.current_table = None
                self.delete_table_button.setEnabled(False)
                
                QMessageBox.information(self, "Success", f'Table "{table_name}" deleted successfully!')
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f'Failed to delete table:\\n{str(e)}')
    
    def open_search_window(self):
        search_window = SearchWindow(self.db_manager, self)
        search_window.exec_()

    def load_tables(self):
        self.tree_widget.clear()
        tables = self.db_manager.get_tables()
        for table in tables:
            if not table.endswith('_filtered'):
                item = QTreeWidgetItem([table])
                self.tree_widget.addTopLevelItem(item)

    def on_table_selected(self, item, column):
        table_name = item.text(0)
        if not table_name.endswith('_filtered'):
            self.current_table = table_name
            self.table_model = LazyLoadingTableModel(self.db_manager, table_name)
            self.table_view.setModel(self.table_model)
    
    def open_search_window(self):
        search_window = SearchWindow(self.db_manager, self)
        search_window.exec_()

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
            QHeaderView::section {
                background-color: #2D2D2D;
                color: #DCDCDC;
                padding: 5px;
                border: none;
            }
        """

    def get_table_view_style(self):
        return """
            QTableView {
                background-color: #1E1E1E;
                alternate-background-color: #252525;
                color: #DCDCDC;
                border: 1px solid #404040;
                gridline-color: #2D2D2D;
            }
            QTableView::item:selected {
                background-color: #2D5A8C;
            }
            QTableView::item:hover {
                background-color: #353535;
            }
            QHeaderView::section {
                background-color: #2D2D2D;
                color: #64C8FF;
                padding: 5px;
                border: none;
            }
            QTableCornerButton::section {
                background-color: #2D2D2D;
                border: none;
            }
        """

    def get_button_style(self):
        return """
            QPushButton {
                background-color: #2D2D2D;
                color: #DCDCDC;
                border: 1px solid #404040;
                padding: 8px 16px;
                border-radius: 3px;
                font-weight: bold;
                font-size: 12px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #353535;
                border: 1px solid #64C8FF;
            }
            QPushButton:pressed {
                background-color: #1E1E1E;
            }
        """
