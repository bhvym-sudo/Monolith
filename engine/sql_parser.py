import re
import os
from pathlib import Path
from PyQt5.QtCore import QThread


class SQLFileParser:
    def __init__(self, database_manager):
        self.db_manager = database_manager
        self.progress_callback = None

    def parse_and_ingest_sql_file(self, file_path, progress_callback=None):
        self.progress_callback = progress_callback
        try:
            file_size = os.path.getsize(file_path)
            file_size_mb = file_size / (1024 * 1024)
            
            if self.progress_callback:
                self.progress_callback(f"Streaming SQL file ({file_size_mb:.1f} MB)...", 10)
            
            conn = self.db_manager.get_connection()
            
            statement_buffer = []
            statement_count = 0
            executed_count = 0
            current_statement = []
            in_string = False
            string_char = None
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f):
                    line = line.strip()
                    
                    if not line or line.startswith('--'):
                        continue
                    
                    i = 0
                    while i < len(line):
                        char = line[i]
                        
                        if char in ('"', "'") and (i == 0 or line[i-1] != '\\'):
                            if not in_string:
                                in_string = True
                                string_char = char
                            elif char == string_char:
                                in_string = False
                                string_char = None
                        
                        current_statement.append(char)
                        
                        if char == ';' and not in_string:
                            stmt = ''.join(current_statement).strip()
                            if stmt:
                                statement_buffer.append(stmt)
                                statement_count += 1
                            current_statement = []
                            
                            if len(statement_buffer) >= 50:
                                for s in statement_buffer:
                                    try:
                                        conn.execute(s)
                                        executed_count += 1
                                    except:
                                        pass
                                
                                statement_buffer = []
                                
                                if self.progress_callback:
                                    progress = 10 + min(int((line_num / 100000) * 80), 80)
                                    self.progress_callback(f"Executed {executed_count} statements...", progress)
                                
                                QThread.msleep(1)
                        
                        i += 1
            
            if statement_buffer:
                for s in statement_buffer:
                    try:
                        conn.execute(s)
                        executed_count += 1
                    except:
                        pass
            
            if self.progress_callback:
                self.progress_callback(f"Completed - {executed_count} statements executed", 100)
            
            return True
            
        except Exception as e:
            if self.progress_callback:
                self.progress_callback(f"Error: {str(e)[:80]}", 0)
            return False

    def _remove_comments(self, sql_content):
        sql_content = re.sub(r'--.*?$', '', sql_content, flags=re.MULTILINE)
        sql_content = re.sub(r'/\*.*?\*/', '', sql_content, flags=re.DOTALL)
        return sql_content

    def _split_statements(self, sql_content):
        statements = []
        current = []
        in_string = False
        string_char = None
        
        i = 0
        while i < len(sql_content):
            char = sql_content[i]
            
            if char in ('"', "'") and (i == 0 or sql_content[i-1] != '\\'):
                if not in_string:
                    in_string = True
                    string_char = char
                elif char == string_char:
                    in_string = False
                    string_char = None
            
            if char == ';' and not in_string:
                stmt = ''.join(current).strip()
                if stmt:
                    statements.append(stmt)
                current = []
            else:
                current.append(char)
            
            i += 1
        
        if current:
            stmt = ''.join(current).strip()
            if stmt:
                statements.append(stmt)
        
        return statements
        
        lines = sql_content.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            i = 0
            while i < len(line):
                char = line[i]
                
                if char in ('"', "'") and (i == 0 or line[i-1] != '\\'):
                    if not in_string:
                        in_string = True
                        string_char = char
                    elif char == string_char:
                        in_string = False
                        string_char = None
                
                if char == ';' and not in_string:
                    current_statement.append(line[:i])
                    stmt = ' '.join(current_statement).strip()
                    if stmt:
                        statements.append(stmt)
                    current_statement = []
                    line = line[i+1:].strip()
                    i = 0
                    continue
                
                i += 1
            
            if line:
                current_statement.append(line)
        
        if current_statement:
            stmt = ' '.join(current_statement).strip()
            if stmt:
                statements.append(stmt)
        
        return statements
