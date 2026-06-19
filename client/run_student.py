"""
O'quvchi paneli — alohida ishga tushirish.
Login talab qilinmaydi. To'g'ridan-to'g'ri test tanlash oynasi ochiladi.
"""
import sys
import os

if getattr(sys, "frozen", False):
    base_dir = os.path.dirname(sys.executable)
    sys.path.insert(0, base_dir)
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))

os.chdir(base_dir)

from PyQt6.QtWidgets import QApplication
from app.config import Config

Config.load()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Smart Exam – O'quvchi")
    app.setOrganizationName("SmartExam")

    from app.windows.student.info_window import StudentInfoWindow
    window = StudentInfoWindow()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
