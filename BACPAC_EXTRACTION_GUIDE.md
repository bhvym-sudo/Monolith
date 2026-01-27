# BACPAC Extraction Alternative Methods

## The Problem
BACPAC BCP files are often compressed/encrypted in modern versions.
Standard text parsing doesn't work.

## Solution 1: Use Microsoft SqlPackage.exe (RECOMMENDED)
SqlPackage is a free Microsoft tool that properly extracts BACPAC files.

### Steps:
1. Download SqlPackage: https://aka.ms/sqlpackage-windows
2. Extract to C:\SqlPackage\

3. Use this PowerShell command to extract:
```powershell
cd "C:\SqlPackage"
.\SqlPackage.exe /Action:Export /SourceFile:"path\to\file.bacpac" /TargetConnectionString:"Data Source=(localdb)\MSSQLLocalDB;Initial Catalog=TempDB;Integrated Security=True"
```

4. Then export to CSV using SQL Server Management Studio or bcp.exe


## Solution 2: Restore BACPAC to SQL Server, then export
If you have SQL Server installed:

1. Open SQL Server Management Studio
2. Right-click "Databases" → "Import Data-tier Application"
3. Select your .bacpac file
4. Once imported, use this query per table:

```sql
-- Export to CSV
EXEC xp_cmdshell 'bcp "SELECT * FROM YourDB.dbo.TableName" queryout "C:\output\table.csv" -c -t, -T -S localhost'
```

## Solution 3: Python with pymssql (for local SQL Server)
```python
pip install pymssql pandas

import pymssql
import pandas as pd

conn = pymssql.connect(server='localhost', database='YourDB')
df = pd.read_sql_query('SELECT * FROM TableName', conn)
df.to_csv('output.csv', index=False)
```

## Current Monolith Implementation
The BACPAC extractor currently tries to parse BCP files directly, but this only works
for older/uncompressed BACPAC files. For modern encrypted BACPAC files, use one of
the solutions above to first convert to CSV, then import those CSVs into Monolith.

## Why This Is Difficult
- BCP format is proprietary Microsoft binary format
- Modern BACPAC files use compression
- Some use encryption
- Requires DacFx libraries (C# only) for proper parsing
