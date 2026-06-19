"""
Client ilovasi asosiy nuqtasi.
"""
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtCore import Qt
import sys

# Global referenslar — PyQt6 da signal ichida yaratilgan window larni
# Python Garbage Collector o'chirib yubormasligi uchun saqlaymiz.
_app_windows: dict = {}


def restart_to_login(current_window: QMainWindow = None):
    """Login oynasiga qaytish."""
    from .windows.login_window import LoginWindow
    login = LoginWindow()
    _app_windows['login'] = login
    login.login_success.connect(open_dashboard)
    login.showMaximized()
    if current_window:
        current_window.hide()
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(80, current_window.close)
    return login


def open_dashboard(role: str):
    """Rol asosida tegishli dashboard oynasini ochish."""
    from .windows.teacher.dashboard import TeacherDashboard
    is_superadmin = (role == "superadmin")
    dashboard = TeacherDashboard(is_superadmin=is_superadmin)
    # Global dict da saqlamasak, signal tugagach Python GC o'chirib yuboradi
    # va window darhol yopiladi — shu muammoning yechimi
    _app_windows['dashboard'] = dashboard
    dashboard.show()
    # Login oynasini yopish
    for widget in QApplication.topLevelWidgets():
        from .windows.login_window import LoginWindow
        if isinstance(widget, LoginWindow):
            widget.close()


def run():
    """Asosiy ilovani ishga tushirish."""
    app = QApplication(sys.argv)
    app.setApplicationName("Smart Exam System")
    app.setOrganizationName("SmartExam")

    from .windows.login_window import LoginWindow
    login = LoginWindow()
    _app_windows['login'] = login
    login.login_success.connect(open_dashboard)
    login.showMaximized()

    sys.exit(app.exec())
