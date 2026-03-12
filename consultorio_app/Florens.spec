# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files

# __file__ no está definido cuando el spec se ejecuta con exec(); usamos cwd.
project_root = Path(os.getcwd())

# Recursos que necesita la app en runtime
base_datas = [
    (project_root / 'app' / 'templates', 'app/templates'),
    (project_root / 'app' / 'media', 'app/media'),
    (project_root / 'config' / 'settings.ini', 'config'),
    (project_root / 'LEEME.txt', '.'),
    (project_root / 'version.txt', '.'),
]

# Incluir data adicional de librerías (ej. flasgger static)
datas = [(str(src), dest) for src, dest in base_datas if src.exists()]
datas += collect_data_files('flasgger', include_py_files=False)

# Imports que a veces PyInstaller no detecta automáticamente
hiddenimports = [
    'flask_login',
    'flask_sqlalchemy',
    'apscheduler.schedulers.background',
    'dateutil.relativedelta',
    'dotenv',
]

block_cipher = None

a = Analysis(
    ['run.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'numpy', 'pandas', 'matplotlib'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Florens',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Cambiar a False si no quieres ventana de consola
    icon=str(project_root / 'app' / 'media' / 'Florens_icon.ico'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Florens',
)
