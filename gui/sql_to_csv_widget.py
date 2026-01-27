from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QFileDialog, QLabel, QProgressBar
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QColor
from engine.sql_to_csv import SQLToCSVConverter
from engine.sql_diagnostics import SQLFileDiagnostics
import os


class DiagnosticWorker(QThread):
    progress = pyqtSignal(str, int)
    finished = pyqtSignal(str)
    
    def __init__(self, sql_file):
        super().__init__()
        self.sql_file = sql_file
    
    def run(self):
        try:
            diagnostics = SQLFileDiagnostics()
            diagnostics.analyze_sql_file(self.sql_file, self.progress.emit)
            report = diagnostics.generate_report()
            self.finished.emit(report)
        except Exception as e:
            self.finished.emit(f"Error: {str(e)}")


class ConversionWorker(QThread):
    progress = pyqtSignal(str, int)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, sql_file, output_folder):
        super().__init__()
        self.sql_file = sql_file
        self.output_folder = output_folder
    
    def run(self):
        try:
            converter = SQLToCSVConverter()
            
            tables = converter.parse_sql_file(self.sql_file, self.progress.emit)
            
            if not tables:
                self.finished.emit(False, "No tables found in SQL file")
                return
            
            success = converter.export_to_csv(self.output_folder, self.progress.emit)
            
            if success:
                self.finished.emit(True, self.output_folder)
            else:
                self.finished.emit(False, "Export failed")
                
        except Exception as e:
            self.finished.emit(False, str(e))


class SQLToCSVWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.sql_file = None
        self.output_folder = None
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        title = QLabel("SQL to CSV Converter")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #64C8FF; padding: 10px;")
        layout.addWidget(title)
        
        file_layout = QHBoxLayout()
        
        self.file_label = QLabel("No SQL file selected")
        self.file_label.setStyleSheet("color: #DCDCDC; padding: 5px;")
        
        self.select_sql_button = QPushButton("Select SQL File")
        self.select_sql_button.setStyleSheet(self.get_button_style())
        self.select_sql_button.clicked.connect(self.select_sql_file)
        
        self.analyze_button = QPushButton("Analyze SQL")
        self.analyze_button.setStyleSheet(self.get_button_style())
        self.analyze_button.setEnabled(False)
        self.analyze_button.clicked.connect(self.analyze_sql)
        
        file_layout.addWidget(self.file_label, 1)
        file_layout.addWidget(self.select_sql_button)
        file_layout.addWidget(self.analyze_button)
        
        layout.addLayout(file_layout)
        
        folder_layout = QHBoxLayout()
        
        self.folder_label = QLabel("No output folder selected")
        self.folder_label.setStyleSheet("color: #DCDCDC; padding: 5px;")
        
        self.select_folder_button = QPushButton("Select Output Folder")
        self.select_folder_button.setStyleSheet(self.get_button_style())
        self.select_folder_button.clicked.connect(self.select_output_folder)
        
        folder_layout.addWidget(self.folder_label, 1)
        folder_layout.addWidget(self.select_folder_button)
        
        layout.addLayout(folder_layout)
        
        self.convert_button = QPushButton("Convert SQL to CSV Files")
        self.convert_button.setStyleSheet(self.get_primary_button_style())
        self.convert_button.setEnabled(False)
        self.convert_button.clicked.connect(self.start_conversion)
        layout.addWidget(self.convert_button)
        
        progress_layout = QHBoxLayout()
        
        self.progress_label = QLabel("Ready")
        self.progress_label.setStyleSheet("color: #DCDCDC; font-size: 11px;")
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
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
        
        progress_layout.addWidget(self.progress_label, 1)
        progress_layout.addWidget(self.progress_bar)
        
        layout.addLayout(progress_layout)
        
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
        self.log_widget.setText("=== SQL to CSV Converter ===\n\n1. Select SQL file to convert\n2. Choose output folder for CSV files\n3. Click 'Convert' to start\n\nEach table will be saved as a separate CSV file.")
        
        layout.addWidget(self.log_widget, 1)
        
        self.setLayout(layout)
    
    def select_sql_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select SQL File",
            "",
            "SQL Files (*.sql);;All Files (*.*)"
        )
        
        if file_path:
            self.sql_file = file_path
            file_name = os.path.basename(file_path)
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
            self.file_label.setText(f"{file_name} ({file_size_mb:.1f} MB)")
            self.log_widget.append(f"\n✓ Selected: {file_path}")
            self.analyze_button.setEnabled(True)
            self.check_ready()
    
    def analyze_sql(self):
        if not self.sql_file:
            return
        
        self.analyze_button.setEnabled(False)
        self.select_sql_button.setEnabled(False)
        self.log_widget.clear()
        self.log_widget.append("=== ANALYZING SQL FILE ===\n")
        self.log_widget.append("This will scan the entire file to show you:")
        self.log_widget.append("- How many tables exist")
        self.log_widget.append("- How many INSERT statements per table")
        self.log_widget.append("- Estimated row counts")
        self.log_widget.append("- Which tables are empty\n")
        
        self.diag_worker = DiagnosticWorker(self.sql_file)
        self.diag_worker.progress.connect(self.update_progress)
        self.diag_worker.finished.connect(self.show_diagnostic_report)
        self.diag_worker.start()
    
    def show_diagnostic_report(self, report):
        self.analyze_button.setEnabled(True)
        self.select_sql_button.setEnabled(True)
        self.log_widget.append("\n" + report)
        self.progress_label.setText("Analysis complete - Check report above")
        self.progress_bar.setValue(100)
    
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
        if self.sql_file and self.output_folder:
            self.convert_button.setEnabled(True)
    
    def start_conversion(self):
        self.convert_button.setEnabled(False)
        self.select_sql_button.setEnabled(False)
        self.select_folder_button.setEnabled(False)
        
        self.log_widget.append(f"\n{'='*60}\nStarting conversion...\n")
        
        self.worker = ConversionWorker(self.sql_file, self.output_folder)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.conversion_finished)
        self.worker.start()
    
    def update_progress(self, message, progress):
        self.progress_label.setText(message)
        self.progress_bar.setValue(progress)
        self.log_widget.append(message)
    
    def conversion_finished(self, success, message):
        self.convert_button.setEnabled(True)
        self.select_sql_button.setEnabled(True)
        self.select_folder_button.setEnabled(True)
        
        if success:
            self.log_widget.append(f"\n{'='*60}\n✓ SUCCESS!\n{'='*60}\n")
            self.log_widget.append(f"CSV files saved to: {message}")
            self.progress_label.setText("Conversion complete!")
            self.progress_bar.setValue(100)
        else:
            self.log_widget.append(f"\n{'='*60}\n✗ FAILED\n{'='*60}\n")
            self.log_widget.append(f"Error: {message}")
            self.progress_label.setText("Conversion failed")
            self.progress_bar.setValue(0)
    
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
            }
            QPushButton:hover {
                background-color: #353535;
                border: 1px solid #64C8FF;
            }
            QPushButton:pressed {
                background-color: #1E4066;
            }
            QPushButton:disabled {
                background-color: #2D2D2D;
                color: #777777;
            }
        """
    
    def get_primary_button_style(self):
        return """
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
            QPushButton:disabled {
                background-color: #2D2D2D;
                color: #777777;
            }
        """
