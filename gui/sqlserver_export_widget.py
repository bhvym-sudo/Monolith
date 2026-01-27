from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QFileDialog, QLabel, QProgressBar, QLineEdit, QComboBox
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QColor
from engine.sqlserver_exporter import SQLServerToCSVExporter
import os


class SQLServerExportWorker(QThread):
    progress = pyqtSignal(str, int)
    log_signal = pyqtSignal(str)
    finished = pyqtSignal(bool, dict)
    
    def __init__(self, server, database, output_folder):
        super().__init__()
        self.server = server
        self.database = database
        self.output_folder = output_folder
    
    def run(self):
        try:
            exporter = SQLServerToCSVExporter(self.server, self.database)
            
            self.log_signal.emit(f"Connecting to {self.server}...")
            exporter.connect()
            self.log_signal.emit("✓ Connected successfully!")
            
            def progress_callback(msg, progress):
                self.progress.emit(msg, progress)
                self.log_signal.emit(msg)
            
            results = exporter.export_all_tables(self.output_folder, progress_callback)
            
            exporter.close()
            self.finished.emit(True, results)
            
        except Exception as e:
            self.log_signal.emit(f"\n❌ Error: {str(e)}")
            self.finished.emit(False, {})


class SQLServerExportWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.output_folder = None
        self.export_worker = None
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Title
        title = QLabel("SQL Server to CSV Exporter")
        title.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #64C8FF;
            padding: 10px 0;
        """)
        layout.addWidget(title)
        
        # Description
        desc = QLabel("Export all tables from SQL Server database to CSV files")
        desc.setStyleSheet("color: #9CDCFE; font-size: 12px; padding-bottom: 10px;")
        layout.addWidget(desc)
        
        # Server input
        server_layout = QHBoxLayout()
        server_label = QLabel("Server:")
        server_label.setStyleSheet("color: #DCDCDC; min-width: 100px;")
        self.server_input = QLineEdit("localhost\\SQLEXPRESS")
        self.server_input.setStyleSheet(self.get_input_style())
        server_layout.addWidget(server_label)
        server_layout.addWidget(self.server_input)
        layout.addLayout(server_layout)
        
        # Database input
        db_layout = QHBoxLayout()
        db_label = QLabel("Database:")
        db_label.setStyleSheet("color: #DCDCDC; min-width: 100px;")
        self.database_input = QLineEdit("ShaheenDB")
        self.database_input.setStyleSheet(self.get_input_style())
        self.database_input.setPlaceholderText("Enter database name (e.g., ShaheenDB)")
        db_layout.addWidget(db_label)
        db_layout.addWidget(self.database_input)
        layout.addLayout(db_layout)
        
        # Output folder selection
        folder_layout = QHBoxLayout()
        self.folder_label = QLabel("No output folder selected")
        self.folder_label.setStyleSheet("""
            background-color: #2D2D2D;
            color: #DCDCDC;
            padding: 10px;
            border: 1px solid #404040;
            border-radius: 3px;
        """)
        
        self.select_folder_button = QPushButton("Select Output Folder")
        self.select_folder_button.setStyleSheet(self.get_button_style())
        self.select_folder_button.clicked.connect(self.select_output_folder)
        
        folder_layout.addWidget(self.folder_label, 1)
        folder_layout.addWidget(self.select_folder_button)
        layout.addLayout(folder_layout)
        
        # Export button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.export_button = QPushButton("Export All Tables")
        self.export_button.setEnabled(False)
        self.export_button.setStyleSheet("""
            QPushButton {
                background-color: #0E7A0D;
                color: #FFFFFF;
                border: 1px solid #404040;
                padding: 12px 30px;
                border-radius: 3px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #107C10;
            }
            QPushButton:pressed {
                background-color: #0A5A0A;
            }
            QPushButton:disabled {
                background-color: #2D2D2D;
                color: #777777;
            }
        """)
        self.export_button.clicked.connect(self.start_export)
        button_layout.addWidget(self.export_button)
        
        layout.addLayout(button_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #404040;
                border-radius: 3px;
                text-align: center;
                background-color: #2D2D2D;
                color: #DCDCDC;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #0E7A0D;
                border-radius: 2px;
            }
        """)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.progress_label = QLabel("Configure connection and select output folder")
        self.progress_label.setStyleSheet("color: #9CDCFE; font-size: 12px; padding: 5px;")
        layout.addWidget(self.progress_label)
        
        # Log widget
        log_label = QLabel("Export Log:")
        log_label.setStyleSheet("color: #DCDCDC; font-weight: bold; padding-top: 10px;")
        layout.addWidget(log_label)
        
        self.log_widget = QTextEdit()
        self.log_widget.setReadOnly(True)
        self.log_widget.setStyleSheet("""
            QTextEdit {
                background-color: #1E1E1E;
                color: #DCDCDC;
                border: 1px solid #404040;
                font-family: Consolas, monospace;
                font-size: 11px;
                padding: 10px;
            }
        """)
        self.log_widget.append("1. Enter SQL Server instance and database name")
        self.log_widget.append("2. Select output folder for CSV files")
        self.log_widget.append("3. Click 'Export All Tables' to begin")
        
        layout.addWidget(self.log_widget, 1)
        
        self.setLayout(layout)
    
    def select_output_folder(self):
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "Select Output Folder"
        )
        
        if folder_path:
            self.output_folder = folder_path
            self.folder_label.setText(folder_path)
            self.log_widget.append(f"\n✓ Output folder: {folder_path}")
            self.check_ready()
    
    def check_ready(self):
        if self.output_folder and self.database_input.text().strip():
            self.export_button.setEnabled(True)
    
    def start_export(self):
        server = self.server_input.text().strip()
        database = self.database_input.text().strip()
        
        if not database:
            self.log_widget.append("\n❌ Please enter a database name")
            return
        
        self.export_button.setEnabled(False)
        self.select_folder_button.setEnabled(False)
        
        self.log_widget.append(f"\n{'='*60}\nStarting export from SQL Server...\n")
        
        self.export_worker = SQLServerExportWorker(server, database, self.output_folder)
        self.export_worker.progress.connect(self.update_progress)
        self.export_worker.log_signal.connect(self.append_log)
        self.export_worker.finished.connect(self.on_export_finished)
        self.export_worker.start()
    
    def update_progress(self, message, progress):
        self.progress_label.setText(message)
        self.progress_bar.setValue(progress)
    
    def append_log(self, message):
        self.log_widget.append(message)
        sb = self.log_widget.verticalScrollBar()
        sb.setValue(sb.maximum())
    
    def on_export_finished(self, success, results):
        self.export_button.setEnabled(True)
        self.select_folder_button.setEnabled(True)
        
        if success and results:
            self.log_widget.append("\n" + "="*60)
            self.log_widget.append("EXPORT SUMMARY")
            self.log_widget.append("="*60)
            
            total_rows = 0
            for table, row_count in results.items():
                self.log_widget.append(f"✓ {table}: {row_count:,} rows")
                total_rows += row_count
            
            self.log_widget.append("\n" + "="*60)
            self.log_widget.append(f"Total: {len(results)} tables, {total_rows:,} rows")
            self.log_widget.append(f"Output: {self.output_folder}")
            self.log_widget.append("="*60)
            
            self.progress_label.setText("✓ Export completed successfully!")
            self.progress_bar.setValue(100)
        else:
            self.progress_label.setText("❌ Export failed - check log for details")
            self.progress_bar.setValue(0)
    
    def get_input_style(self):
        return """
            QLineEdit {
                background-color: #2D2D2D;
                color: #DCDCDC;
                border: 1px solid #404040;
                padding: 8px;
                border-radius: 3px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 1px solid #64C8FF;
            }
        """
    
    def get_button_style(self):
        return """
            QPushButton {
                background-color: #2D5A8C;
                color: #FFFFFF;
                border: 1px solid #404040;
                padding: 10px 20px;
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
            QPushButton:disabled {
                background-color: #2D2D2D;
                color: #777777;
            }
        """
