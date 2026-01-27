import zipfile
import os
import xml.etree.ElementTree as ET
import csv
import struct
from pathlib import Path


class BacpacExtractor:
    def __init__(self):
        self.tables = {}
        
    def extract_bacpac(self, bacpac_path, output_folder, progress_callback=None):
        """Extract BACPAC file and convert to CSV"""
        try:
            if not zipfile.is_zipfile(bacpac_path):
                if progress_callback:
                    progress_callback("Error: Not a valid BACPAC file", 0)
                return False
            
            if progress_callback:
                progress_callback("Extracting BACPAC archive...", 10)
            
            # Create temp extraction folder
            temp_dir = os.path.join(output_folder, '_bacpac_temp')
            os.makedirs(temp_dir, exist_ok=True)
            
            # Extract BACPAC
            with zipfile.ZipFile(bacpac_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            if progress_callback:
                progress_callback("Parsing database schema...", 20)
            
            # Parse model.xml to get table schemas
            model_path = os.path.join(temp_dir, 'model.xml')
            if not os.path.exists(model_path):
                if progress_callback:
                    progress_callback("Error: model.xml not found", 0)
                return False
            
            self._parse_model_xml(model_path, progress_callback)
            
            if progress_callback:
                progress_callback(f"Found {len(self.tables)} tables. Converting data...", 30)
            
            # Convert BCP files to CSV
            data_folder = os.path.join(temp_dir, 'Data')
            if os.path.exists(data_folder):
                self._convert_bcp_to_csv(data_folder, output_folder, progress_callback)
            else:
                if progress_callback:
                    progress_callback("Warning: No Data folder found in BACPAC", 50)
            
            # Verify CSV files were created
            csv_files = [f for f in os.listdir(output_folder) if f.endswith('.csv')]
            if progress_callback:
                progress_callback(f"Created {len(csv_files)} CSV files in output folder", 90)
            
            # Cleanup temp directory
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
            
            if progress_callback:
                progress_callback(f"✓ Conversion complete! {len(self.tables)} tables exported", 100)
            
            return True
            
        except Exception as e:
            if progress_callback:
                progress_callback(f"Error: {str(e)}", 0)
            return False
    
    def _parse_model_xml(self, model_path, progress_callback=None):
        """Parse model.xml to extract table schemas"""
        try:
            tree = ET.parse(model_path)
            root = tree.getroot()
            
            # SQL Server namespaces
            namespaces = {
                'ds': 'http://schemas.microsoft.com/sqlserver/dac/Serialization/2012/02'
            }
            
            # Find all table elements
            for element in root.findall('.//ds:Element[@Type="SqlTable"]', namespaces):
                table_name = element.get('Name')
                if table_name:
                    # Clean table name (remove schema prefix if present)
                    table_name = table_name.split('.')[-1].strip('[]')
                    
                    # Extract columns
                    columns = []
                    for rel in element.findall('.//ds:Relationship[@Name="Columns"]//ds:Entry', namespaces):
                        col_ref = rel.find('.//ds:References', namespaces)
                        if col_ref is not None:
                            col_name = col_ref.get('Name')
                            if col_name:
                                col_name = col_name.strip('[]')
                                columns.append(col_name)
                    
                    if columns:
                        self.tables[table_name] = {
                            'columns': columns,
                            'row_count': 0
                        }
            
            if progress_callback:
                progress_callback(f"Parsed schema: {len(self.tables)} tables found", 25)
                
        except Exception as e:
            if progress_callback:
                progress_callback(f"Schema parsing error: {str(e)[:100]}", 0)
    
    def _convert_bcp_to_csv(self, data_folder, output_folder, progress_callback=None):
        """Convert BCP files to CSV"""
        bcp_files = [f for f in os.listdir(data_folder) if f.endswith('.BCP')]
        total_files = len(bcp_files)
        
        if progress_callback:
            progress_callback(f"Found {total_files} BCP files to convert", 35)
        
        for idx, bcp_file in enumerate(bcp_files):
            try:
                # Extract table name from filename (format: dbo.TableName.BCP)
                table_name = bcp_file.replace('.BCP', '').split('.')[-1]
                
                if table_name not in self.tables:
                    # Try to find matching table
                    matching = [t for t in self.tables.keys() if t.lower() == table_name.lower()]
                    if matching:
                        table_name = matching[0]
                    else:
                        # No schema info, extract raw
                        table_name = bcp_file.replace('.BCP', '').replace('.', '_')
                        self.tables[table_name] = {'columns': [], 'row_count': 0}
                
                bcp_path = os.path.join(data_folder, bcp_file)
                csv_path = os.path.join(output_folder, f"{table_name}.csv")
                [{idx+1}/{total_files}] Converting {table_name}...", progress)
                
                # Try to read and convert BCP data
                rows = self._read_bcp_file(bcp_path, table_name)
                
                # Ensure output folder exists
                os.makedirs(output_folder, exist_ok=Tru}...", progress)
                
                # Try to read and convert BCP data
                rows = self._read_bcp_file(bcp_path, table_name)
                
                # Write to CSV (always create file, even if empty)
                with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    
                    # Write header
                    columns = self.tables[table_name]['columns']
                    if columns:
                        writer.writerow(columns)
                    
                    # Write data rows
                    for row in rows:
                        writer.writerow(row)
                    
                    self.tables[table_name]['row_count'] = len(rows)
                 → {csv_path}", progress)
                    else:
                        progress_callback(f"⚠ {table_name}: 0 rows (file created with headers only)", progress)
                            progress_callback(f"✓ {table_name}: {len(rows)} rows", progress)
                    else:
                        progress_callback(f"⚠ {table_name}: 0 rows (BCP data may be encrypted/compressed)", progress)
                    
            except Exception as e:
                if progress_callback:
                    progress_callback(f"⚠ Error converting {bcp_file}: {str(e)[:80]}", 0)
    
    def _read_bcp_file(self, bcp_path, table_name):
        """Read BCP file and extract rows - BCP is a binary format"""
        rows = []
        columns = self.tables[table_name]['columns']
        col_count = len(columns) if columns else 0
        
        try:
            with open(bcp_path, 'rb') as f:
                data = f.read()
                
                if len(data) == 0:
                    return rows
                
                # BACPAC BCP files are typically in a proprietary binary format
                # We'll try multiple approaches to extract data
                
                # Approach 1: Try reading as delimited text with various encodings
                for encoding in ['utf-16-le', 'utf-16-be', 'utf-8', 'latin-1']:
                    try:
                        text_data = data.decode(encoding, errors='ignore')
                        # Remove null bytes and control characters
                        text_data = text_data.replace('\x00', '').replace('\r', '\n')
                        
                        # Look for patterns that indicate row data
                        lines = []
                        for line in text_data.split('\n'):
                            line = line.strip()
                            # Skip empty lines and lines with only control chars
                            if line and len(line) > 1 and any(c.isprintable() for c in line):
                                lines.append(line)
                        
                        if lines:
                            # Try to parse lines into rows
                            for line in lines:
                                # Try various delimiters
                                for delimiter in ['\t', '|', ',', ';']:
                                    if delimiter in line:
                                        values = line.split(delimiter)
                                        # Clean up values
                                        values = [v.strip() for v in values]
                                        values = [v if v else None for v in values]
                                        
                                        # If we got reasonable number of columns, add it
                                        if col_count > 0 and len(values) == col_count:
                                            rows.append(values)
                                            break
                                        elif col_count == 0 and values:
                                            rows.append(values)
                                            break
                            
                            if rows:
                                break  # Found data with this encoding
                                
                    except:
                        continue
                
                # Approach 2: If no delimiter-based parsing worked, try binary field extraction
                if not rows and len(data) > 0:
                    # Look for readable strings in the binary data
                    extracted_values = []
                    current_string = []
                    
                    for byte in data:
                        if 32 <= byte <= 126:  # Printable ASCII
                            current_string.append(chr(byte))
                        else:
                            if current_string and len(current_string) > 1:
                                string_value = ''.join(current_string)
                                if len(string_value.strip()) > 0:
                                    extracted_values.append(string_value.strip())
                            current_string = []
                    
                    # Add last string if exists
                    if current_string and len(current_string) > 1:
                        string_value = ''.join(current_string)
                        if len(string_value.strip()) > 0:
                            extracted_values.append(string_value.strip())
                    
                    # Group extracted values into rows
                    if extracted_values and col_count > 0:
                        for i in range(0, len(extracted_values), col_count):
                            row_values = extracted_values[i:i+col_count]
                            if len(row_values) == col_count:
                                rows.append(row_values)
                    elif extracted_values:
                        # If no column count, return all values as single-column rows
                        rows = [[v] for v in extracted_values if v]
                
        except Exception as e:
            # Log error but don't crash
            pass
        
        return rows
    
    def get_conversion_summary(self):
        """Get summary of converted tables"""
        summary = []
        for table_name, info in self.tables.items():
            summary.append({
                'table': table_name,
                'columns': len(info['columns']),
                'rows': info['row_count']
            })
        return summary
