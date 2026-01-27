# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all, collect_submodules, copy_metadata

block_cipher = None

# Collect all duckdb files including metadata
duckdb_datas, duckdb_binaries, duckdb_hiddenimports = collect_all('duckdb')
duckdb_metadata = copy_metadata('duckdb')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=duckdb_binaries,
    datas=duckdb_datas + duckdb_metadata + [
        ('data', 'data'),  # Include data folder
    ],
    hiddenimports=[
        'PyQt5',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'duckdb',
        'duckdb.duckdb',
        'pandas',
        'pandas._libs',
        'pandas._libs.tslibs.timedeltas',
        'pandas._libs.tslibs.nattype',
        'pandas._libs.tslibs.np_datetime',
        'pandas._libs.skiplist',
        'openpyxl',
        'openpyxl.cell',
        'openpyxl.cell._writer',
        'xlrd',
        'pyarrow',
        'pyarrow.parquet',
        'numpy',
        'numpy.core',
        'gui',
        'gui.main_window',
        'gui.widget',
        'gui.model',
        'gui.search_window',
        'gui.highlight_delegate',
        'gui.sql_preview_widget',
        'gui.sql_to_csv_widget',
        'engine',
        'engine.database',
        'engine.ingestion',
        'engine.sql_parser',
        'engine.sql_inspector',
        'engine.sql_to_csv',
        'engine.sql_diagnostics',
        'engine.search_engine',
    ] + duckdb_hiddenimports + collect_submodules('pandas') + collect_submodules('openpyxl'),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter', 
        'matplotlib', 
        'test', 
        'tests', 
        'pytest',
        'torch',
        'torchvision',
        'scipy',
        'PIL',
        'Pillow',
        'tensorboard',
        'IPython',
        'jupyter',
        'notebook',
        'sphinx',
        'setuptools',
        'distutils',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='MonolithEngine',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # Disabled UPX for compatibility
    console=False,  # No console window for GUI app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path here if you have one: icon='icon.ico'
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='MonolithEngine',
)
