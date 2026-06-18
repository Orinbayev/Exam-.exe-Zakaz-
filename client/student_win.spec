# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all, collect_submodules

qt_d, qt_b, qt_h = collect_all('PyQt6')

a = Analysis(
    ['run_student.py'],
    pathex=['.'],
    binaries=qt_b,
    datas=qt_d + [
        ('app/assets', 'assets'),
        ('config.json', '.'),
    ],
    hiddenimports=qt_h + collect_submodules('PyQt6') + [
        'pkgutil',
        'pkg_resources',
        'importlib.metadata',
        'importlib.resources',
        'app',
        'app.sound_player',
        'app.api_client',
        'app.config',
        'app.styles',
        'app.windows',
        'app.windows.student',
        'app.windows.student.info_window',
        'app.windows.student.exam_window',
        'app.windows.student.result_window',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'pandas', 'scipy'],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='OquvchiPanel',
    debug=False,
    strip=False,
    upx=False,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name='OquvchiPanel',
)
