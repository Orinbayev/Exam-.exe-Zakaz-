# -*- mode: python ; coding: utf-8 -*-
import sys
import os

# SPECPATH = bu spec fayli joylashgan papka (= client/)
# collect_submodules 'app' ni import qila olishi uchun path ga qo'shamiz
if SPECPATH not in sys.path:
    sys.path.insert(0, SPECPATH)

from PyInstaller.utils.hooks import collect_all, collect_submodules

qt_d, qt_b, qt_h = collect_all('PyQt6')
app_mods = collect_submodules('app')

a = Analysis(
    ['run_client.py'],
    pathex=[SPECPATH, '.'],
    binaries=qt_b,
    datas=qt_d + [
        ('app/assets', 'assets'),
        ('config.json', '.'),
    ],
    hiddenimports=qt_h + collect_submodules('PyQt6') + app_mods + [
        'pkgutil',
        'pkg_resources',
        'importlib.metadata',
        'importlib.resources',
        'requests',
        'openpyxl',
        'charset_normalizer',
        'certifi',
        'idna',
        'urllib3',
    ],
    hookspath=[],
    runtime_hooks=['pyqt6_runtime_hook.py'],
    excludes=['tkinter', 'matplotlib', 'numpy', 'pandas', 'scipy'],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='OqituvchiPanel',
    debug=False,
    strip=False,
    upx=False,
    console=False,
    uac_admin=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name='OqituvchiPanel',
)
