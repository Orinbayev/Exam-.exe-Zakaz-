"""
Teacher/Admin asosiy boshqaruv paneli.
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QStackedWidget, QFrame, QMessageBox, QScrollArea,
    QSizePolicy, QDialog, QFormLayout, QLineEdit, QComboBox,
    QTextEdit, QDialogButtonBox, QSpinBox, QCheckBox
)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QColor, QPalette
from ...api_client import api, APIError
from ...styles import MAIN_STYLE, COLORS
from .questions_widget import QuestionsWidget
from .tests_widget import TestsWidget
from .results_widget import ResultsWidget
from .stats_widget import StatsWidget


class SidebarButton(QPushButton):
    def __init__(self, icon: str, text: str, parent=None):
        super().__init__(f"  {icon}  {text}", parent)
        self.setObjectName("sidebar_btn")
        self.setCheckable(True)
        self.setMinimumHeight(46)
        self.setFont(QFont("Segoe UI", 13))


class TeacherDashboard(QMainWindow):
    def __init__(self, is_superadmin: bool = False):
        super().__init__()
        self.is_superadmin = is_superadmin
        self.setWindowTitle(
            f"Smart Exam System - {'Super Admin' if is_superadmin else 'O\'qituvchi'} Paneli"
        )
        self.setMinimumSize(1100, 700)
        self.setStyleSheet(MAIN_STYLE)
        self._setup_ui()
        self._show_section(0)
        self._maximize()

    def _maximize(self):
        from PyQt6.QtGui import QGuiApplication
        screen = QGuiApplication.primaryScreen().geometry()
        self.setGeometry(screen)
        self.showMaximized()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Sidebar ───────────────────────────────────────────────────────────
        sidebar = QFrame()
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_medium']};
                border-right: 1px solid {COLORS['border']};
            }}
        """)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(10, 16, 10, 16)
        sidebar_layout.setSpacing(4)

        # Logo
        logo_label = QLabel("🎓 Smart Exam")
        logo_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        logo_label.setStyleSheet(f"color: {COLORS['primary_light']}; padding: 8px 10px;")
        sidebar_layout.addWidget(logo_label)

        # User info
        role_text = "Super Admin" if self.is_superadmin else "O'qituvchi"
        user_label = QLabel(f"👤 {api.user_name}\n{role_text}")
        user_label.setStyleSheet(f"""
            color: {COLORS['text_secondary']};
            font-size: 11px;
            padding: 6px 10px;
            background: rgba(255,255,255,0.05);
            border-radius: 6px;
        """)
        user_label.setWordWrap(True)
        sidebar_layout.addWidget(user_label)
        sidebar_layout.addSpacing(10)

        # Nav buttons
        self.nav_buttons = []
        nav_items = [
            ("📋", "Testlar"),
            ("📝", "Savollar"),
            ("👥", "O'quvchilar"),
            ("📊", "Natijalar"),
            ("📈", "Statistika"),
        ]
        if self.is_superadmin:
            nav_items += [
                ("👤", "Foydalanuvchilar"),
                ("⚙️", "Sozlamalar"),
                ("📋", "Audit log"),
            ]

        for i, (icon, text) in enumerate(nav_items):
            btn = SidebarButton(icon, text)
            btn.clicked.connect(lambda _, idx=i: self._show_section(idx))
            sidebar_layout.addWidget(btn)
            self.nav_buttons.append(btn)

        sidebar_layout.addStretch()

        # Student mode button
        student_btn = QPushButton("🖥️  O'quvchi rejimi")
        student_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['accent']};
                color: white;
                border-radius: 8px;
                padding: 10px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent_light']};
            }}
        """)
        student_btn.clicked.connect(self._open_student_mode)
        sidebar_layout.addWidget(student_btn)

        logout_btn = QPushButton("🚪 Chiqish")
        logout_btn.setObjectName("secondary")
        logout_btn.clicked.connect(self._logout)
        sidebar_layout.addWidget(logout_btn)

        main_layout.addWidget(sidebar)

        # ── Content area ──────────────────────────────────────────────────────
        content_frame = QFrame()
        content_frame.setStyleSheet(f"background-color: {COLORS['bg_dark']};")
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(20, 20, 20, 20)

        self.stack = QStackedWidget()

        # Pages
        from .students_widget import StudentsWidget
        self.tests_widget     = TestsWidget()
        self.questions_widget = QuestionsWidget()
        self.students_widget_tab = StudentsWidget()
        self.results_widget   = ResultsWidget()
        self.stats_widget     = StatsWidget()

        self.stack.addWidget(self.tests_widget)          # 0
        self.stack.addWidget(self.questions_widget)      # 1
        self.stack.addWidget(self.students_widget_tab)   # 2
        self.stack.addWidget(self.results_widget)        # 3
        self.stack.addWidget(self.stats_widget)          # 4

        if self.is_superadmin:
            from ..superadmin.dashboard import UsersWidget, SettingsWidget, LogsWidget
            self.users_widget_sa  = UsersWidget()
            self.settings_widget_sa = SettingsWidget()
            self.logs_widget_sa   = LogsWidget()
            self.stack.addWidget(self.users_widget_sa)    # 5
            self.stack.addWidget(self.settings_widget_sa) # 6
            self.stack.addWidget(self.logs_widget_sa)     # 7

        content_layout.addWidget(self.stack)
        main_layout.addWidget(content_frame)

    def _show_section(self, index: int):
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)
        # Auto-refresh
        current = self.stack.currentWidget()
        if hasattr(current, "refresh"):
            current.refresh()

    def _open_student_mode(self):
        from ..student.info_window import StudentInfoWindow
        self._student_win = StudentInfoWindow()
        self._student_win.show()

    def _logout(self):
        reply = QMessageBox.question(self, "Chiqish", "Tizimdan chiqmoqchimisiz?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            api.logout()
            from ...main import restart_to_login
            restart_to_login(self)
