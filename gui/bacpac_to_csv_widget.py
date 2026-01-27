from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QFileDialog, QLabel, QProgressBar
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QColor
from engine.bacpac_extractor import BacpacExtractor
import os


class BacpacConversionWorker(QThread):
    progress = pyqtSignal(str, int)
    log_signal = pyqtSignal(str)
    finished = pyqtSignal(bool)
    
    def __init__(self, bacpac_file, output_folder):
        super().__init__()
        self.bacpac_file = bacpac_file
        self.output_folder = output_folder
    
    def run(self):
        try:
            extractor = BacpacExtractor()
            
            def progress_callback(msg, progress):
                self.progress.emit(msg, progress)
                self.log_signal.emit(msg)
            
            success = extractor.extract_bacpac(
                self.bacpac_file, 
                self.output_folder, 
                progress_callback
            )
            
            if success:
                # Show summary
                summary = extractor.get_conversion_summary()
                self.log_signal.emit("\n" + "="*60)
                self.log_signal.emit("CONVERSION SUMMARY")
                self.log_signal.emit("="*60)
                
                for item in summary:
                    self.log_signal.emit(
                        f"✓ {item['table']}: {item['columns']} columns, {item['rows']} rows"
                    )
                
                self.log_signal.emit("\n" + "="*60)
                self.log_signal.emit(f"Total: {len(summary)} tables converted")
                self.log_signal.emit(f"Output folder: {self.output_folder}")
                self.log_signal.emit("="*60)
            
            self.finished.emit(success)
            
        except Exception as e:
            self.log_signal.emit(f"\n❌ Fatal error: {str(e)}")
            self.finished.emit(False)


class BacpacToCSVWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.bacpac_file = None
        self.output_folder = None
        self.conversion_worker = None
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Title
        title = QLabel("BACPAC to CSV Converter")
        title.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #64C8FF;
            padding: 10px 0;
        """)
        layout.addWidget(title)
        
        # Description
        desc = QLabel("Extract SQL Server BACPAC files and convert all tables to CSV format")
        desc.setStyleSheet("color: #9CDCFE; font-size: 12px; padding-bottom: 10px;")
        layout.addWidget(desc)
        
        # BACPAC file selection
        file_layout = QHBoxLayout()
        self.file_label = QLabel("No BACPAC file selected")
        self.file_label.setStyleSheet("""
            background-color: #2D2D2D;
            color: #DCDCDC;
            padding: 10px;
            border: 1px solid #404040;
            border-radius: 3px;
        """)
        
        self.select_bacpac_button = QPushButton("Select BACPAC File")
        self.select_bacpac_button.setStyleSheet(self.get_button_style())
        self.select_bacpac_button.clicked.connect(self.select_bacpac_file)
        
        file_layout.addWidget(self.file_label, 1)
        file_layout.addWidget(self.select_bacpac_button)
        
        layout.addLayout(file_layout)
        
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
        
        # Convert button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.convert_button = QPushButton("Convert to CSV")
        self.convert_button.setEnabled(False)
        self.convert_button.setStyleSheet("""
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
        self.convert_button.clicked.connect(self.start_conversion)
        button_layout.addWidget(self.convert_button)
        
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
        self.progress_label = QLabel("Ready to convert")
        self.progress_label.setStyleSheet("color: #9CDCFE; font-size: 12px; padding: 5px;")
        layout.addWidget(self.progress_label)
        
        # Log widget
        log_label = QLabel("Conversion Log:")
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
        self.log_widget.append("Select a BACPAC file and output folder to begin...")
        
        layout.addWidget(self.log_widget, 1)
        
        self.setLayout(layout)
    
    def select_bacpac_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select BACPAC File",
            "",
            "BACPAC Files (*.bacpac);;All Files (*.*)"
        )
        
        if file_path:
            self.bacpac_file = file_path
            file_name = os.path.basename(file_path)
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
            self.file_label.setText(f"{file_name} ({file_size_mb:.1f} MB)")
            self.log_widget.append(f"\n✓ Selected: {file_path}")
            self.check_ready()
    
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
        if self.bacpac_file and self.output_folder:
            self.convert_button.setEnabled(True)
    
    def start_conversion(self):
        self.convert_button.setEnabled(False)
        self.select_bacpac_button.setEnabled(False)
        self.select_folder_button.setEnabled(False)
        
        self.log_widget.append(f"\n{'='*60}\nStarting conversion...\n")
        
        self.conversion_worker = BacpacConversionWorker(
            self.bacpac_file,
            self.output_folder
        )
        self.conversion_worker.progress.connect(self.update_progress)
        self.conversion_worker.log_signal.connect(self.append_log)
        self.conversion_worker.finished.connect(self.on_conversion_finished)
        self.conversion_worker.start()
    
    def update_progress(self, message, progress):
        self.progress_label.setText(message)
        self.progress_bar.setValue(progress)
    
    def append_log(self, message):
        self.log_widget.append(message)
        sb = self.log_widget.verticalScrollBar()
        sb.setValue(sb.maximum())
    
    def on_conversion_finished(self, success):
        self.convert_button.setEnabled(True)
        self.select_bacpac_button.setEnabled(True)
        self.select_folder_button.setEnabled(True)
        
        if success:
            self.progress_label.setText("✓ Conversion completed successfully!")
            self.progress_bar.setValue(100)
        else:
            self.progress_label.setText("❌ Conversion failed - check log for details")
            self.progress_bar.setValue(0)
    
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
