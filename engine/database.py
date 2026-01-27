import duckdb
import os
from pathlib import Path


class DatabaseManager:
    def __init__(self, db_path='master_database.duckdb'):
        self.db_path = db_path
        self.conn = None
        self.initialize_database()

    def initialize_database(self):
        if not os.path.exists(self.db_path):
            self.conn = duckdb.connect(self.db_path)
        else:
            self.conn = duckdb.connect(self.db_path)
        
        # Create metadata table for tracking ingested files
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS _ingestion_metadata (
                file_name TEXT PRIMARY KEY,
                file_path TEXT,
                file_size INTEGER,
                file_modified TIMESTAMP,
                ingested_at TIMESTAMP,
                table_name TEXT
            )
        """)

    def get_connection(self):
        if self.conn is None:
            self.conn = duckdb.connect(self.db_path)
        return self.conn

    def get_tables(self):
        query = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main' ORDER BY table_name"
        result = self.conn.execute(query).fetchall()
        return [row[0] for row in result]

    def get_table_data(self, table_name, offset=0, limit=50):
        query = f"SELECT * FROM {table_name} LIMIT {limit} OFFSET {offset}"
        return self.conn.execute(query).fetchall()

    def get_table_columns(self, table_name):
        query = f"PRAGMA table_info({table_name})"
        result = self.conn.execute(query).fetchall()
        return [row[1] for row in result]

    def get_row_count(self, table_name):
        query = f"SELECT COUNT(*) FROM {table_name}"
        result = self.conn.execute(query).fetchone()
        return result[0] if result else 0

    def execute_query(self, query):
        try:
            return self.conn.execute(query).fetchall()
        except Exception as e:
            return []

    def table_exists(self, table_name):
        tables = self.get_tables()
        return table_name in tables
    
    def is_file_ingested(self, file_path):
        """Check if file has already been ingested with same size and modified time"""
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        file_modified = os.path.getmtime(file_path)
        
        query = """
            SELECT COUNT(*) FROM _ingestion_metadata 
            WHERE file_name = ? AND file_size = ? AND file_modified = ?
        """
        result = self.conn.execute(query, [file_name, file_size, file_modified]).fetchone()
        return result[0] > 0 if result else False
    
    def mark_file_ingested(self, file_path, table_name):
        """Mark file as ingested in metadata table"""
        import datetime
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        file_modified = os.path.getmtime(file_path)
        
        query = """
            INSERT OR REPLACE INTO _ingestion_metadata 
            (file_name, file_path, file_size, file_modified, ingested_at, table_name)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        self.conn.execute(query, [
            file_name, 
            file_path, 
            file_size, 
            datetime.datetime.fromtimestamp(file_modified),
            datetime.datetime.now(),
            table_name
        ])

    def drop_table(self, table_name):
        if self.table_exists(table_name):
            self.conn.execute(f"DROP TABLE {table_name}")

    def close(self):
        if self.conn:
            self.conn.close()
