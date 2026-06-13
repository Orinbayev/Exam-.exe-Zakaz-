"""
Client ishga tushirish nuqtasi.
"""
import sys
import os

# PyInstaller frozen muhitda yo'llarni sozlash
if getattr(sys, "frozen", False):
    base_dir = os.path.dirname(sys.executable)
    sys.path.insert(0, base_dir)
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))

os.chdir(base_dir)

from app.main import run

if __name__ == "__main__":
    run()
