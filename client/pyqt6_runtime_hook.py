"""
PyQt6 runtime hook — DLLlarni Qt yuklanishidan OLDIN to'g'ri joydan yuklash.
Bu fayl PyInstaller tomonidan dastur ishga tushganda birinchi bo'lib bajariladi.
"""
import os
import sys

if sys.platform == 'win32' and getattr(sys, 'frozen', False):
    import ctypes
    import ctypes.wintypes

    meipass = sys._MEIPASS

    # _MEIPASS ni Windows DLL qidirish ro'yxatiga qo'shish
    try:
        ctypes.windll.kernel32.AddDllDirectory(ctypes.c_wchar_p(meipass))
    except Exception:
        pass

    # Bu DLLlarni Qt yuklanishidan OLDIN _MEIPASS dan yuklash:
    # python3.dll    — PyQt6 pyd fayllar Stable ABI orqali buni ishlatadi
    # vcruntime*     — MSVC runtime (Qt6Core.dll bog'liq)
    # msvcp140*      — MSVC C++ runtime
    dlls_to_preload = [
        'python3.dll',
        'vcruntime140.dll',
        'vcruntime140_1.dll',
        'msvcp140.dll',
        'msvcp140_1.dll',
        'msvcp140_2.dll',
        'concrt140.dll',
    ]

    for dll_name in dlls_to_preload:
        dll_path = os.path.join(meipass, dll_name)
        if os.path.exists(dll_path):
            try:
                ctypes.CDLL(dll_path)
            except OSError:
                pass
