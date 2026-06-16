# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

block_cipher = None

# PyQt6 ni to'liq yig'ish
qt_datas, qt_binaries, qt_hidden = collect_all('PyQt6')

a = Analysis(
    ['run_student.py'],
    pathex=['.'],
    binaries=qt_binaries,
    datas=[
        ('app/assets', 'assets'),
        ('config.json', '.'),
    ] + qt_datas,
    hiddenimports=qt_hidden + [
        'pkgutil',
        'pkg_resources',
        'importlib.metadata',
        'importlib.resources',
        'app.sound_player',
        'app.api_client',
        'app.config',
        'app.windows.student.info_window',
        'app.windows.student.exam_window',
        'app.windows.student.result_window',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'pandas'],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='OquvchiPanel',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='OquvchiPanel',
)
