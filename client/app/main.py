"""
Client ilovasi asosiy nuqtasi.
"""
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtCore import Qt
import sys


def restart_to_login(current_window: QMainWindow = None):
    """Login oynasiga qaytish."""
    from .windows.login_window import LoginWindow
    if current_window:
        current_window.close()
    login = LoginWindow()
    login.login_success.connect(open_dashboard)
    login.show()
    return login


def open_dashboard(role: str):
    """Rol asosida tegishli dashboard oynasini ochish."""
    from .windows.teacher.dashboard import TeacherDashboard
    is_superadmin = (role == "superadmin")
    dashboard = TeacherDashboard(is_superadmin=is_superadmin)
    dashboard.show()
    # Login oynasini yopish
    for widget in QApplication.topLevelWidgets():
        from .windows.login_window import LoginWindow
        if isinstance(widget, LoginWindow):
            widget.close()
    return dashboard


def run():
    """Asosiy ilovani ishga tushirish."""
    app = QApplication(sys.argv)
    app.setApplicationName("Smart Exam System")
    app.setOrganizationName("SmartExam")
    # Login oynasini ochish
    from .windows.login_window import LoginWindow
    login = LoginWindow()
    login.login_success.connect(open_dashboard)
    login.show()

    sys.exit(app.exec())
