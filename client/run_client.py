"""
O'qituvchi paneli — ishga tushirish nuqtasi.
"""
import sys
import os

if getattr(sys, "frozen", False):
    base_dir = os.path.dirname(sys.executable)
    # _MEIPASS = _internal/ papkasi, runtime hook da sys.path ga qo'shilgan
    # base_dir (exe papkasi) ham qo'shamiz — config.json shu yerda
    sys.path.insert(0, base_dir)
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))

os.chdir(base_dir)

from app.main import run

if __name__ == "__main__":
    run()


