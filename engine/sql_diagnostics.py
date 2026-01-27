import re
import os


class SQLFileDiagnostics:
    def __init__(self):
        self.stats = {}
    
    def analyze_sql_file(self, file_path, progress_callback=None):
        try:
            file_size = os.path.getsize(file_path)
            file_size_mb = file_size / (1024 * 1024)
            
            if progress_callback:
                progress_callback(f"Analyzing SQL file ({file_size_mb:.1f} MB)...", 10)
            
            stats = {
                'file_size_mb': file_size_mb,
                'total_lines': 0,
                'create_table_count': 0,
                'insert_statements': 0,
                'tables': {}
            }
            
            current_table = None
            in_insert = False
            insert_line_count = 0
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    stats['total_lines'] = line_num
                    stripped = line.strip()
                    
                    if not stripped or stripped.startswith('--'):
                        continue
                    
                    if re.match(r'CREATE TABLE\s+`?(\w+)`?', stripped, re.IGNORECASE):
                        match = re.match(r'CREATE TABLE\s+`?(\w+)`?', stripped, re.IGNORECASE)
                        table_name = match.group(1)
                        current_table = table_name
                        stats['create_table_count'] += 1
                        stats['tables'][table_name] = {
                            'insert_count': 0,
                            'estimated_rows': 0,
                            'insert_lines': []
                        }
                    
                    if re.match(r'INSERT INTO\s+`?(\w+)`?', stripped, re.IGNORECASE):
                        match = re.match(r'INSERT INTO\s+`?(\w+)`?', stripped, re.IGNORECASE)
                        insert_table = match.group(1)
                        stats['insert_statements'] += 1
                        in_insert = True
                        insert_line_count = 1
                        
                        if insert_table in stats['tables']:
                            stats['tables'][insert_table]['insert_count'] += 1
                            stats['tables'][insert_table]['insert_lines'].append(line_num)
                            
                            values_count = stripped.count('VALUES')
                            parentheses_pairs = stripped.count('),(')
                            stats['tables'][insert_table]['estimated_rows'] += max(1, parentheses_pairs + 1)
                    
                    elif in_insert:
                        insert_line_count += 1
                        if ';' in stripped:
                            in_insert = False
                            insert_line_count = 0
                    
                    if line_num % 50000 == 0 and progress_callback:
                        progress = 10 + min(int((line_num / 500000) * 80), 80)
                        progress_callback(f"Analyzed {line_num:,} lines...", progress)
            
            if progress_callback:
                progress_callback(f"Analysis complete!", 100)
            
            self.stats = stats
            return stats
            
        except Exception as e:
            if progress_callback:
                progress_callback(f"Error: {str(e)[:80]}", 0)
            return {}
    
    def generate_report(self):
        if not self.stats:
            return "No data analyzed yet."
        
        report = []
        report.append("=" * 80)
        report.append("SQL FILE DIAGNOSTIC REPORT")
        report.append("=" * 80)
        report.append(f"\nFile Size: {self.stats['file_size_mb']:.2f} MB")
        report.append(f"Total Lines: {self.stats['total_lines']:,}")
        report.append(f"CREATE TABLE Statements: {self.stats['create_table_count']}")
        report.append(f"INSERT Statements Found: {self.stats['insert_statements']:,}")
        report.append("\n" + "=" * 80)
        report.append("TABLE BREAKDOWN")
        report.append("=" * 80)
        
        for table_name, info in sorted(self.stats['tables'].items(), key=lambda x: x[1]['estimated_rows'], reverse=True):
            report.append(f"\n📊 {table_name}")
            report.append(f"   INSERT statements: {info['insert_count']}")
            report.append(f"   Estimated rows: {info['estimated_rows']:,}")
            if info['insert_lines']:
                sample_lines = info['insert_lines'][:3]
                report.append(f"   INSERT at lines: {', '.join(map(str, sample_lines))}...")
        
        total_rows = sum(t['estimated_rows'] for t in self.stats['tables'].values())
        report.append("\n" + "=" * 80)
        report.append(f"TOTAL ESTIMATED ROWS: {total_rows:,}")
        report.append("=" * 80)
        
        empty_tables = [name for name, info in self.stats['tables'].items() if info['insert_count'] == 0]
        if empty_tables:
            report.append(f"\nEMPTY TABLES ({len(empty_tables)}): {', '.join(empty_tables)}")
        
        return '\n'.join(report)
