import re
import os
import csv
from pathlib import Path


class SQLToCSVConverter:
    def __init__(self):
        self.tables = {}
    
    def parse_sql_file(self, file_path, progress_callback=None):
        try:
            file_size = os.path.getsize(file_path)
            file_size_mb = file_size / (1024 * 1024)
            
            if progress_callback:
                progress_callback(f"Parsing SQL file ({file_size_mb:.1f} MB)...", 10)
            
            self.tables = {}
            current_table = None
            current_insert_table = None
            lines_read = 0
            buffer = []
            
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
                            'rows': []
                        }
                        continue
                    
                    if current_table and re.match(r'\s*`?(\w+)`?\s+(\w+)', line):
                        col_match = re.match(r'\s*`?(\w+)`?\s+(\w+)', line)
                        if col_match:
                            col_name = col_match.group(1)
                            if col_name.upper() not in ['PRIMARY', 'FOREIGN', 'KEY', 'CONSTRAINT', 'INDEX', 'UNIQUE']:
                                if col_name not in self.tables[current_table]['columns']:
                                    self.tables[current_table]['columns'].append(col_name)
                    
                    if re.match(r'INSERT INTO\s+`?(\w+)`?', line, re.IGNORECASE):
                        insert_match = re.match(r'INSERT INTO\s+`?(\w+)`?', line, re.IGNORECASE)
                        current_insert_table = insert_match.group(1)
                        buffer = [line]
                        continue
                    
                    if current_insert_table:
                        buffer.append(line)
                        
                        full_statement = ' '.join(buffer)
                        
                        if ';' in line:
                            values_matches = re.findall(r'VALUES\s*\((.*?)\)(?:,|\s*;)', full_statement, re.IGNORECASE)
                            
                            if not values_matches:
                                values_match = re.search(r'VALUES\s*\((.*?)\)', full_statement, re.IGNORECASE)
                                if values_match:
                                    values_matches = [values_match.group(1)]
                            
                            if values_matches and current_insert_table in self.tables:
                                for values_str in values_matches:
                                    parsed_values = self._parse_values(values_str)
                                    self.tables[current_insert_table]['rows'].append(parsed_values)
                            
                            current_insert_table = None
                            buffer = []
                    
                    if lines_read % 10000 == 0 and progress_callback:
                        progress = 10 + min(int((lines_read / 100000) * 40), 40)
                        total_rows = sum(len(t['rows']) for t in self.tables.values())
                        progress_callback(f"Parsed {lines_read:,} lines, {total_rows:,} data rows", progress)
            
            if progress_callback:
                total_rows = sum(len(t['rows']) for t in self.tables.values())
                progress_callback(f"Parsing complete - {len(self.tables)} tables, {total_rows:,} rows", 50)
            
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
        
        for i, char in enumerate(values_str):
            if char in ('"', "'") and (i == 0 or values_str[i-1] != '\\'):
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
                values.append(val if val and val.upper() != 'NULL' else '')
                current_value = []
            else:
                current_value.append(char)
        
        if current_value:
            val = ''.join(current_value).strip()
            values.append(val if val and val.upper() != 'NULL' else '')
        
        return values
    
    def export_to_csv(self, output_folder, progress_callback=None):
        try:
            os.makedirs(output_folder, exist_ok=True)
            
            total_tables = len(self.tables)
            
            for idx, (table_name, data) in enumerate(self.tables.items()):
                csv_path = os.path.join(output_folder, f"{table_name}.csv")
                
                if progress_callback:
                    progress = 50 + int(((idx + 1) / total_tables) * 50)
                    progress_callback(f"Exporting {table_name}.csv ({len(data['rows']):,} rows)...", progress)
                
                with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    
                    if data['columns']:
                        writer.writerow(data['columns'])
                    
                    for row in data['rows']:
                        writer.writerow(row)
            
            if progress_callback:
                progress_callback(f"Export complete - {total_tables} CSV files created", 100)
            
            return True
            
        except Exception as e:
            if progress_callback:
                progress_callback(f"Export error: {str(e)[:80]}", 0)
            return False
