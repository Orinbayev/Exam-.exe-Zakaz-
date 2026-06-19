# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all, collect_submodules

qt_d, qt_b, qt_h = collect_all('PyQt6')

a = Analysis(
    ['run_client.py'],
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
        'app.api_client',
        'app.config',
        'app.main',
        'app.styles',
        'app.windows',
        'app.windows.login_window',
        'app.windows.teacher',
        'app.windows.teacher.dashboard',
        'app.windows.teacher.students_widget',
        'app.windows.teacher.questions_widget',
        'app.windows.teacher.fan_widget',
        'app.windows.teacher.results_widget',
        'app.windows.teacher.stats_widget',
        'app.windows.teacher.tests_widget',
        'app.windows.superadmin',
        'app.windows.superadmin.dashboard',
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
