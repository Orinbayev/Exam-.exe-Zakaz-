# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['run_client.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('app/assets', 'assets'),
        ('config.json', '.'),
    ],
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'PyQt6.sip',
        'app.api_client',
        'app.config',
        'app.main',
        'app.styles',
        'app.windows.login_window',
        'app.windows.teacher.dashboard',
        'app.windows.teacher.students_widget',
        'app.windows.teacher.questions_widget',
        'app.windows.teacher.fan_widget',
        'app.windows.teacher.results_widget',
        'app.windows.teacher.stats_widget',
        'app.windows.teacher.tests_widget',
        'app.windows.superadmin.dashboard',
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
    name='OqituvchiPanel',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
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
    upx=True,
    upx_exclude=[],
    name='OqituvchiPanel',
)
