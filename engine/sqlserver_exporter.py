import pyodbc
import csv
import os


class SQLServerToCSVExporter:
    def __init__(self, server='localhost\\SQLEXPRESS', database='master'):
        self.server = server
        self.database = database
        self.conn = None
    
    def connect(self):
        """Connect to SQL Server"""
        try:
            conn_string = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={self.server};DATABASE={self.database};Trusted_Connection=yes;'
            self.conn = pyodbc.connect(conn_string)
            return True
        except Exception as e:
            try:
                # Try older driver
                conn_string = f'DRIVER={{SQL Server}};SERVER={self.server};DATABASE={self.database};Trusted_Connection=yes;'
                self.conn = pyodbc.connect(conn_string)
                return True
            except Exception as e2:
                raise Exception(f"Connection failed: {str(e2)}")
    
    def get_tables(self):
        """Get list of all user tables"""
        cursor = self.conn.cursor()
        query = """
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_TYPE = 'BASE TABLE' 
            AND TABLE_CATALOG = ?
            ORDER BY TABLE_NAME
        """
        cursor.execute(query, self.database)
        tables = [row[0] for row in cursor.fetchall()]
        cursor.close()
        return tables
    
    def export_table_to_csv(self, table_name, output_folder, progress_callback=None):
        """Export single table to CSV"""
        try:
            cursor = self.conn.cursor()
            
            # Get data
            query = f"SELECT * FROM [{table_name}]"
            cursor.execute(query)
            
            # Get column names
            columns = [column[0] for column in cursor.description]
            
            # Fetch all rows
            rows = cursor.fetchall()
            
            # Write to CSV
            csv_path = os.path.join(output_folder, f"{table_name}.csv")
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(columns)
                
                for row in rows:
                    # Convert row to list and handle None values
                    row_data = [str(cell) if cell is not None else '' for cell in row]
                    writer.writerow(row_data)
            
            cursor.close()
            
            if progress_callback:
                progress_callback(f"✓ {table_name}: {len(rows)} rows exported", len(rows))
            
            return len(rows)
            
        except Exception as e:
            if progress_callback:
                progress_callback(f"✗ Error exporting {table_name}: {str(e)[:80]}", 0)
            return 0
    
    def export_all_tables(self, output_folder, progress_callback=None):
        """Export all tables to CSV"""
        os.makedirs(output_folder, exist_ok=True)
        
        tables = self.get_tables()
        total_tables = len(tables)
        
        if progress_callback:
            progress_callback(f"Found {total_tables} tables to export", 0)
        
        results = {}
        for idx, table in enumerate(tables):
            if progress_callback:
                progress = int((idx / total_tables) * 100)
                progress_callback(f"[{idx+1}/{total_tables}] Exporting {table}...", progress)
            
            row_count = self.export_table_to_csv(table, output_folder, progress_callback)
            results[table] = row_count
        
        if progress_callback:
            progress_callback(f"Export complete! {total_tables} tables exported", 100)
        
        return results
    
    def close(self):
        """Close connection"""
        if self.conn:
            self.conn.close()
