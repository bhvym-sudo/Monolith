import re
import os
from pathlib import Path


class SQLFileInspector:
    def __init__(self):
        self.tables = {}
        self.file_path = None
    
    def inspect_sql_file(self, file_path, progress_callback=None):
        try:
            self.file_path = file_path
            file_size = os.path.getsize(file_path)
            file_size_mb = file_size / (1024 * 1024)
            
            if progress_callback:
                progress_callback(f"Scanning SQL file ({file_size_mb:.1f} MB)...", 10)
            
            self.tables = {}
            current_table = None
            lines_read = 0
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    lines_read += 1
                    line = line.strip()
                    
                    if not line or line.startswith('--'):
                        continue
                    
                    create_match = re.match(r'CREATE TABLE\s+`?(\w+)`?\s*\(', line, re.IGNORECASE)
                    if create_match:
                        table_name = create_match.group(1)
                        current_table = table_name
                        self.tables[table_name] = {
                            'columns': [],
                            'row_count_estimate': 0,
                            'sample_data': []
                        }
                    
                    elif current_table and re.match(r'\s*`?(\w+)`?\s+(\w+)', line):
                        col_match = re.match(r'\s*`?(\w+)`?\s+(\w+)', line)
                        if col_match:
                            col_name = col_match.group(1)
                            col_type = col_match.group(2)
                            if col_name.upper() not in ['PRIMARY', 'FOREIGN', 'KEY', 'CONSTRAINT', 'INDEX']:
                                self.tables[current_table]['columns'].append({
                                    'name': col_name,
                                    'type': col_type
                                })
                    
                    elif re.match(r'INSERT INTO\s+`?(\w+)`?', line, re.IGNORECASE):
                        insert_match = re.match(r'INSERT INTO\s+`?(\w+)`?\s+.*?VALUES\s*\((.*?)\)', line, re.IGNORECASE)
                        if insert_match:
                            table_name = insert_match.group(1)
                            values = insert_match.group(2)
                            if table_name in self.tables:
                                self.tables[table_name]['row_count_estimate'] += 1
                                if len(self.tables[table_name]['sample_data']) < 50:
                                    parsed_values = self._parse_values(values)
                                    self.tables[table_name]['sample_data'].append(parsed_values)
                    
                    if lines_read % 10000 == 0 and progress_callback:
                        progress = 10 + min(int((lines_read / 100000) * 80), 80)
                        progress_callback(f"Scanned {lines_read:,} lines, found {len(self.tables)} tables", progress)
            
            if progress_callback:
                progress_callback(f"Scan complete - {len(self.tables)} tables found", 100)
            
            return self.tables
            
        except Exception as e:
            if progress_callback:
                progress_callback(f"Error: {str(e)[:80]}", 0)
            return {}
    
    def _parse_values(self, values_str):
        values = []
        current_value = []
        in_string = False
        string_char = None
        
        for char in values_str:
            if char in ('"', "'") and (not current_value or current_value[-1] != '\\'):
                if not in_string:
                    in_string = True
                    string_char = char
                elif char == string_char:
                    in_string = False
                    string_char = None
                    continue
                else:
                    current_value.append(char)
            elif char == ',' and not in_string:
                val = ''.join(current_value).strip()
                values.append(val if val else 'NULL')
                current_value = []
            else:
                current_value.append(char)
        
        if current_value:
            val = ''.join(current_value).strip()
            values.append(val if val else 'NULL')
        
        return values
    
    def get_table_info(self, table_name):
        return self.tables.get(table_name, {})
