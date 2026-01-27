from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QSplitter, QTreeWidget, QTreeWidgetItem, QTableView, QHeaderView, QLabel
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

        # Bottom-right search button
        button_layout = QHBoxLayout()
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
