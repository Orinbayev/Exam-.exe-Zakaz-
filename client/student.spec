# -*- mode: python ; coding: utf-8 -*-
import os

block_cipher = None

a = Analysis(
    ['run_student.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('app/assets', 'assets'),
    ],
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'PyQt6.QtMultimedia',
        'PyQt6.sip',
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
    name='OquvchiPanel',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,   # oyna ko'rinishi — terminal yo'q
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='OquvchiPanel',
)

# macOS uchun .app bundle
app = BUNDLE(
    coll,
    name='OquvchiPanel.app',
    icon=None,
    bundle_identifier='com.smartexam.student',
    info_plist={
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleDisplayName': 'Smart Exam — O\'quvchi',
        'NSHighResolutionCapable': True,
    },
)
