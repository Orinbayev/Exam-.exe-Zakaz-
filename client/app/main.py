"""
Client ilovasi asosiy nuqtasi.
"""
import sys
import os
import traceback
import logging

from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox
from PyQt6.QtCore import Qt

# ─────────────────────────────────────────────────────────────────────────────
# Xato logini Desktop da saqlash (console=False bo'lganda xatolar ko'rinmaydi)
# ─────────────────────────────────────────────────────────────────────────────
_log_path = os.path.join(os.path.expanduser("~"), "Desktop", "SmartExam_xato.log")
try:
    logging.basicConfig(
        filename=_log_path,
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)s: %(message)s",
        encoding="utf-8",
        force=True,
    )
except Exception:
    _log_path = os.path.join(os.path.expanduser("~"), "SmartExam_xato.log")
    logging.basicConfig(
        filename=_log_path,
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)s: %(message)s",
        encoding="utf-8",
        force=True,
    )


def _excepthook(exc_type, exc_value, exc_tb):
    """Barcha tutilmagan Python xatolarini fayl ga yozish."""
    msg = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    logging.critical(f"TUTILMAGAN XATO:\n{msg}")
    sys.__excepthook__(exc_type, exc_value, exc_tb)


sys.excepthook = _excepthook

# ─────────────────────────────────────────────────────────────────────────────
# Global referenslar — GC muammosini oldini olish
# Python Garbage Collector signal ichida yaratilgan window larni o'chirib yuboradi.
# _app_windows dict da saqlab qo'yamiz.
# ─────────────────────────────────────────────────────────────────────────────
_app_windows: dict = {}


def restart_to_login(current_window: QMainWindow = None):
    """Login oynasiga qaytish."""
    try:
        from .windows.login_window import LoginWindow
        login = LoginWindow()
        _app_windows["login"] = login
        login.login_success.connect(open_dashboard)
        login.showMaximized()
        if current_window:
            current_window.hide()
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(80, current_window.close)
        return login
    except Exception:
        logging.critical(f"restart_to_login xatosi:\n{traceback.format_exc()}")
        raise


def open_dashboard(role: str):
    """Rol asosida dashboard ochish — to'liq try/except bilan."""
    logging.info(f"open_dashboard chaqirildi, role={role!r}")
    try:
        from .windows.teacher.dashboard import TeacherDashboard
        is_superadmin = (role == "superadmin")
        logging.info("TeacherDashboard yaratilmoqda...")

        dashboard = TeacherDashboard(is_superadmin=is_superadmin)

        # GC dan himoya
        _app_windows["dashboard"] = dashboard

        logging.info("Dashboard ko'rsatilmoqda...")
        if not dashboard.isVisible():
            dashboard.showMaximized()

        # Login oynasini yopish
        for widget in QApplication.topLevelWidgets():
            from .windows.login_window import LoginWindow
            if isinstance(widget, LoginWindow):
                widget.close()

        logging.info("Dashboard muvaffaqiyatli ochildi.")

    except Exception:
        err = traceback.format_exc()
        logging.critical(f"Dashboard ochilmadi:\n{err}")
        QMessageBox.critical(
            None,
            "Xato — Dashboard ochilmadi",
            f"Dasturda xato yuz berdi.\n\n"
            f"Xato tafsilotlari:\n{err[:800]}\n\n"
            f"To'liq xato fayli:\n{_log_path}",
        )


def run():
    """Asosiy ilovani ishga tushirish."""
    logging.info("=" * 60)
    logging.info("Smart Exam System ishga tushdi")
    logging.info(f"Python: {sys.version}")
    logging.info(f"Frozen: {getattr(sys, 'frozen', False)}")

    try:
        app = QApplication(sys.argv)
        app.setApplicationName("Smart Exam System")
        app.setOrganizationName("SmartExam")

        from .windows.login_window import LoginWindow
        login = LoginWindow()
        _app_windows["login"] = login
        login.login_success.connect(open_dashboard)
        login.showMaximized()

        logging.info("Login oynasi ochildi, event loop boshlanmoqda...")
        sys.exit(app.exec())

    except Exception:
        err = traceback.format_exc()
        logging.critical(f"run() xatosi:\n{err}")
        try:
            QMessageBox.critical(None, "Kritik xato", err[:600])
        except Exception:
            pass
        sys.exit(1)
