from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QProgressBar, QLabel, QHBoxLayout, QTabWidget, QTextEdit, QPushButton
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QCoreApplication
from PyQt5.QtGui import QIcon, QFont, QColor
from .widget import NexusEngineWidget
from .sql_preview_widget import SQLPreviewWidget
from .sql_to_csv_widget import SQLToCSVWidget
from engine import DatabaseManager, DataIngestionEngine
import os
import sys


class IngestionWorker(QThread):
    progress = pyqtSignal(str, int)
    log_signal = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, database_manager, data_folder):
        super().__init__()
        self.db_manager = database_manager
        self.data_folder = data_folder

    def run(self):
        engine = DataIngestionEngine(self.db_manager, self.data_folder)
        files = engine.scan_data_folder()
        total_files = len(files)
        
        self.log_signal.emit(f"Found {total_files} files to ingest")
        
        for idx, (file_name, file_path) in enumerate(files):
            table_name = file_name.split('.')[0]
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
            
            self.log_signal.emit(f"\n[{idx+1}/{total_files}] Processing: {file_name} ({file_size_mb:.1f} MB)")
            self.progress.emit(f"[{idx+1}/{total_files}] {file_name} ({file_size_mb:.1f} MB)", 0)
            
            def sql_progress_callback(msg, progress):
                self.progress.emit(f"[{idx+1}/{total_files}] {msg}", progress)
            
            success = engine.ingest_file(file_path, table_name, sql_progress_callback)
            
            if success:
                self.log_signal.emit(f"  ✓ Successfully ingested {file_name}")
            else:
                self.log_signal.emit(f"  ✗ Failed to ingest {file_name}")
        
        self.log_signal.emit(f"\n{'='*60}\nIngestion complete! Processed {total_files} files")
        self.progress.emit("All files ingested successfully!", 100)
        self.finished.emit()


class NexusEngineMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db_manager = DatabaseManager('master_database.duckdb')
        self.init_ui()
        self.setWindowTitle("Monolith Engine")
        self.showMaximized()  # Start maximized
        self.apply_dark_stylesheet()
        self.load_existing_tables()

    def load_existing_tables(self):
        self.status_label.setText("Scanning data folder...")
        self.progress_bar.setValue(0)
        self.nexus_widget.load_tables()
        # Auto-start ingestion on startup
        self.ingest_data()

    def init_ui(self):
        central_widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(self.get_tab_style())

        self.nexus_widget = NexusEngineWidget(self.db_manager)
        self.tab_widget.addTab(self.nexus_widget, "Data Browser")

        self.sql_preview_widget = SQLPreviewWidget()
        self.tab_widget.addTab(self.sql_preview_widget, "SQL File Inspector")

        self.sql_to_csv_widget = SQLToCSVWidget()
        self.tab_widget.addTab(self.sql_to_csv_widget, "SQL to CSV")

        self.log_widget = QTextEdit()
        self.log_widget.setReadOnly(True)
        self.log_widget.setStyleSheet("""
            QTextEdit {
                background-color: #1E1E1E;
                color: #DCDCDC;
                border: none;
                font-family: Consolas, monospace;
                font-size: 11px;
                padding: 10px;
            }
        """)
        self.log_widget.append("=== Monolith Engine Logs ===\n")
        self.tab_widget.addTab(self.log_widget, "Logs")

        layout.addWidget(self.tab_widget)

        bottom_container = QWidget()
        bottom_container.setStyleSheet("background-color: #1E1E1E;")
        bottom_layout = QVBoxLayout()
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(5)

        status_container = QWidget()
        status_container.setStyleSheet("background-color: #1E1E1E; border-top: 1px solid #404040;")
        status_layout = QHBoxLayout()
        status_layout.setContentsMargins(10, 5, 10, 5)
        
        self.status_label = QLabel("Initializing...")
        self.status_label.setStyleSheet("color: #DCDCDC; font-size: 11px;")
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFixedWidth(200)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #404040;
                border-radius: 3px;
                text-align: center;
                background-color: #2D2D2D;
                color: #DCDCDC;
                font-size: 10px;
            }
            QProgressBar::chunk {
                background-color: #64C8FF;
                border-radius: 2px;
            }
        """)
        
        status_layout.addWidget(self.status_label, 1)
        status_layout.addWidget(self.progress_bar, 0)
        status_container.setLayout(status_layout)
        
        bottom_layout.addWidget(status_container)
        bottom_container.setLayout(bottom_layout)
        
        layout.addWidget(bottom_container)

        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def ingest_data(self):
        self.log_widget.clear()
        self.log_widget.append("=== Starting Data Ingestion ===\n")
        self.ingestion_worker = IngestionWorker(self.db_manager, 'data')
        self.ingestion_worker.progress.connect(self.update_status)
        self.ingestion_worker.log_signal.connect(self.append_log)
        self.ingestion_worker.finished.connect(self.on_ingestion_finished)
        self.ingestion_worker.start()

    def update_status(self, message, progress):
        self.status_label.setText(message)
        self.progress_bar.setValue(progress)

    def append_log(self, message):
        self.log_widget.append(message)
        sb = self.log_widget.verticalScrollBar()
        sb.setValue(sb.maximum())

    def on_ingestion_finished(self):
        self.status_label.setText("Ready - All files processed")
        self.progress_bar.setValue(100)
        self.nexus_widget.load_tables()

    def get_tab_style(self):
        return """
            QTabWidget::pane {
                border: 1px solid #404040;
                background-color: #1E1E1E;
            }
            QTabBar::tab {
                background-color: #2D2D2D;
                color: #DCDCDC;
                padding: 8px 16px;
                margin-right: 2px;
                border: 1px solid #404040;
            }
            QTabBar::tab:selected {
                background-color: #1E1E1E;
                border-bottom: 2px solid #64C8FF;
            }
            QTabBar::tab:hover {
                background-color: #353535;
            }
        """

    def apply_dark_stylesheet(self):
        stylesheet = """
            QMainWindow {
                background-color: #1E1E1E;
                color: #DCDCDC;
            }
            QWidget {
                background-color: #1E1E1E;
                color: #DCDCDC;
            }
            QLabel {
                color: #DCDCDC;
            }
            QLineEdit {
                background-color: #2D2D2D;
                color: #DCDCDC;
                border: 1px solid #404040;
                padding: 5px;
                border-radius: 3px;
            }
            QLineEdit:focus {
                border: 1px solid #6BA3D4;
            }
            QPushButton {
                background-color: #2D2D2D;
                color: #DCDCDC;
                border: 1px solid #404040;
                padding: 6px 12px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #353535;
                border: 1px solid #64C8FF;
            }
            QPushButton:pressed {
                background-color: #1E1E1E;
            }
            QMenuBar {
                background-color: #2D2D2D;
                color: #DCDCDC;
                border-bottom: 1px solid #404040;
            }
            QMenuBar::item:selected {
                background-color: #353535;
            }
            QMenu {
                background-color: #2D2D2D;
                color: #DCDCDC;
                border: 1px solid #404040;
            }
            QMenu::item:selected {
                background-color: #2D5A8C;
            }
        """
        self.setStyleSheet(stylesheet)

    def closeEvent(self, event):
        self.db_manager.close()
        event.accept()
