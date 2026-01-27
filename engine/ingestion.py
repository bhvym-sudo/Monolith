import os
import pandas as pd
from pathlib import Path
from .database import DatabaseManager


class DataIngestionEngine:
    def __init__(self, database_manager, data_folder='data'):
        self.db_manager = database_manager
        self.data_folder = data_folder
        self.supported_formats = ['.csv', '.xlsx', '.xls', '.txt', '.tsv', '.json', '.parquet']

    def scan_data_folder(self):
        if not os.path.exists(self.data_folder):
            os.makedirs(self.data_folder)
            return []

        files = []
        for file in os.listdir(self.data_folder):
            file_path = os.path.join(self.data_folder, file)
            if os.path.isfile(file_path):
                ext = Path(file).suffix.lower()
                if ext in self.supported_formats:
                    files.append((file, file_path))
        return files

    def ingest_file(self, file_path, table_name, progress_callback=None):
        try:
            # Check if file already ingested
            if self.db_manager.is_file_ingested(file_path):
                if progress_callback:
                    progress_callback(f"⏭️ Skipping (already ingested): {os.path.basename(file_path)}", 100)
                return True
            
            ext = Path(file_path).suffix.lower()
            
            if ext == '.csv':
                df = pd.read_csv(file_path)
            elif ext in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
            elif ext == '.txt':
                df = pd.read_csv(file_path, delimiter='\t', on_bad_lines='skip')
            elif ext == '.tsv':
                df = pd.read_csv(file_path, delimiter='\t')
            elif ext == '.json':
                df = pd.read_json(file_path)
            elif ext == '.parquet':
                df = pd.read_parquet(file_path)
            else:
                return False

            clean_table_name = self._sanitize_table_name(table_name)
            
            if self.db_manager.table_exists(clean_table_name):
                self.db_manager.drop_table(clean_table_name)

            self.db_manager.get_connection().execute(f"CREATE TABLE {clean_table_name} AS SELECT * FROM df")
            
            # Mark file as ingested
            self.db_manager.mark_file_ingested(file_path, clean_table_name)
            
            return True
        except Exception as e:
            print(f"Error ingesting {file_path}: {str(e)}")
            return False

    def ingest_all_files(self):
        files = self.scan_data_folder()
        for file_name, file_path in files:
            table_name = Path(file_name).stem
            self.ingest_file(file_path, table_name)

    def _sanitize_table_name(self, name):
        name = Path(name).stem
        name = name.replace('-', '_').replace(' ', '_')
        name = ''.join(c for c in name if c.isalnum() or c == '_')
        if name[0].isdigit():
            name = '_' + name
        return name.lower()
