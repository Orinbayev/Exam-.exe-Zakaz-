"""
Teacher/Admin asosiy boshqaruv paneli — yig'iladigan sidebar.
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QStackedWidget, QFrame, QMessageBox, QSizePolicy
)
from PyQt6.QtCore import (
    Qt, QPropertyAnimation, QAbstractAnimation, QEasingCurve, QSize
)
from PyQt6.QtGui import QFont, QGuiApplication
from ...api_client import api, APIError
from ...styles import MAIN_STYLE, COLORS


# ─────────────────────────────────────────────────────────────────────────────
# Konstantlar
# ─────────────────────────────────────────────────────────────────────────────

SIDEBAR_EXPANDED  = 220
SIDEBAR_COLLAPSED = 56
ANIM_MS = 220


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar tugmasi
# ─────────────────────────────────────────────────────────────────────────────

class NavButton(QPushButton):
    """Icon + text ko'rsatadigan, collapsed holatda faqat icon."""

    _BASE = f"""
        QPushButton {{
            background: transparent;
            color: {COLORS['text_secondary']};
            text-align: left;
            padding: 10px 14px;
            border-radius: 10px;
            font-size: 13px;
            font-weight: normal;
            border: none;
        }}
        QPushButton:hover {{
            background: {COLORS['bg_light']};
            color: white;
        }}
        QPushButton:checked {{
            background: {COLORS['primary']};
            color: white;
            font-weight: bold;
        }}
    """

    def __init__(self, icon: str, text: str, parent=None):
        super().__init__(parent)
        self._icon = icon
        self._text = text
        self._collapsed = False
        self.setObjectName("nav_btn")
        self.setCheckable(True)
        self.setMinimumHeight(44)
        self.setStyleSheet(self._BASE)
        self._refresh()

    def set_collapsed(self, c: bool):
        self._collapsed = c
        self._refresh()

    def _refresh(self):
        if self._collapsed:
            self.setText(self._icon)
            self.setFont(QFont("Segoe UI Emoji", 16))
            self.setToolTip(self._text)
            self.setStyleSheet(self._BASE + """
                QPushButton { text-align: center; padding: 10px 4px; }
            """)
        else:
            self.setText(f"  {self._icon}  {self._text}")
            self.setFont(QFont("Segoe UI", 13))
            self.setToolTip("")
            self.setStyleSheet(self._BASE)


# ─────────────────────────────────────────────────────────────────────────────
# Asosiy dashboard
# ─────────────────────────────────────────────────────────────────────────────

class TeacherDashboard(QMainWindow):
    def __init__(self, is_superadmin: bool = False):
        super().__init__()
        self.is_superadmin = is_superadmin
        self._collapsed = False
        _role = "Super Admin" if is_superadmin else "O'qituvchi"
        self.setWindowTitle(f"Smart Exam System — {_role} paneli")
        self.setMinimumSize(900, 600)
        self.setStyleSheet(MAIN_STYLE)
        self._setup_ui()
        self._show_section(0)
        self.showMaximized()

    # ── UI qurilishi ──────────────────────────────────────────────────────────

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── SIDEBAR ───────────────────────────────────────────────────────────
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(SIDEBAR_EXPANDED)
        self.sidebar.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['bg_medium']};
                border-right: 1px solid {COLORS['border']};
            }}
        """)

        self._sb_lay = QVBoxLayout(self.sidebar)
        self._sb_lay.setContentsMargins(8, 12, 8, 12)
        self._sb_lay.setSpacing(2)

        # ── Sidebar yuqori qismi: logo + toggle ──────────────────────────────
        top_row = QHBoxLayout()
        top_row.setContentsMargins(4, 0, 0, 0)
        top_row.setSpacing(0)

        self._logo_lbl = QLabel("🎓 Smart Exam")
        self._logo_lbl.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        self._logo_lbl.setStyleSheet(
            f"color: {COLORS['primary_light']}; padding: 6px 6px; background: transparent;"
        )
        top_row.addWidget(self._logo_lbl)
        top_row.addStretch()

        self._toggle_btn = QPushButton("◀")
        self._toggle_btn.setFixedSize(32, 32)
        self._toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._toggle_btn.setToolTip("Sidebarni yig'ish / yoyish")
        self._toggle_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['primary']};
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 11px;
                font-weight: bold;
                min-height: 0;
                padding: 0;
            }}
            QPushButton:hover {{
                background: {COLORS['primary_light']};
            }}
            QPushButton:pressed {{
                background: {COLORS['primary_dark']};
            }}
        """)
        self._toggle_btn.clicked.connect(self._toggle_sidebar)
        top_row.addWidget(self._toggle_btn)
        self._sb_lay.addLayout(top_row)
        self._sb_lay.addSpacing(4)

        # ── Foydalanuvchi info ────────────────────────────────────────────────
        role_txt = "Super Admin" if self.is_superadmin else "O'qituvchi"
        self._user_lbl = QLabel(f"👤 {api.user_name}\n{role_txt}")
        self._user_lbl.setStyleSheet(f"""
            color: {COLORS['text_secondary']};
            font-size: 11px;
            padding: 6px 8px;
            background: rgba(255,255,255,0.05);
            border-radius: 8px;
        """)
        self._user_lbl.setWordWrap(True)
        self._sb_lay.addWidget(self._user_lbl)
        self._sb_lay.addSpacing(8)

        # ── Nav tugmalari ─────────────────────────────────────────────────────
        nav_items = [
            ("📚", "Fan"),
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

        self.nav_buttons: list[NavButton] = []
        for i, (ico, txt) in enumerate(nav_items):
            btn = NavButton(ico, txt)
            btn.clicked.connect(lambda _, idx=i: self._show_section(idx))
            self._sb_lay.addWidget(btn)
            self.nav_buttons.append(btn)

        self._sb_lay.addStretch()

        # ── O'quvchi rejimi ───────────────────────────────────────────────────
        self._student_mode_btn = QPushButton("  🖥️  O'quvchi rejimi")
        self._student_mode_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['accent']};
                color: white; border: none; border-radius: 8px;
                padding: 9px 6px; font-size: 12px; font-weight: bold;
                text-align: center;
            }}
            QPushButton:hover {{ background: {COLORS['accent_light']}; }}
        """)
        self._student_mode_btn.clicked.connect(self._open_student_mode)
        self._sb_lay.addWidget(self._student_mode_btn)
        self._sb_lay.addSpacing(4)

        # ── Chiqish ───────────────────────────────────────────────────────────
        self._logout_btn = QPushButton("  🚪  Chiqish")
        self._logout_btn.setObjectName("secondary")
        self._logout_btn.clicked.connect(self._logout)
        self._sb_lay.addWidget(self._logout_btn)

        root.addWidget(self.sidebar)

        # ── KONTENT ───────────────────────────────────────────────────────────
        content = QFrame()
        content.setStyleSheet(f"background: {COLORS['bg_dark']}; border: none;")
        cl = QVBoxLayout(content)
        cl.setContentsMargins(20, 20, 20, 20)
        cl.setSpacing(0)

        self.stack = QStackedWidget()

        from .fan_widget      import FanWidget
        from .students_widget import StudentsWidget
        from .results_widget  import ResultsWidget
        from .stats_widget    import StatsWidget

        self.stack.addWidget(FanWidget())            # 0 — Fan
        self.stack.addWidget(StudentsWidget())       # 1 — O'quvchilar
        self.stack.addWidget(ResultsWidget())        # 2 — Natijalar
        self.stack.addWidget(StatsWidget())          # 3 — Statistika

        if self.is_superadmin:
            from ..superadmin.dashboard import UsersWidget, SettingsWidget, LogsWidget
            self.stack.addWidget(UsersWidget())      # 4
            self.stack.addWidget(SettingsWidget())   # 5
            self.stack.addWidget(LogsWidget())       # 6

        cl.addWidget(self.stack)
        root.addWidget(content, stretch=1)

        # ── Animatsiya ────────────────────────────────────────────────────────
        self._anim = QPropertyAnimation(self.sidebar, b"maximumWidth")
        self._anim.setDuration(ANIM_MS)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self._anim.finished.connect(self._on_sidebar_anim_done)

        self._anim2 = QPropertyAnimation(self.sidebar, b"minimumWidth")
        self._anim2.setDuration(ANIM_MS)
        self._anim2.setEasingCurve(QEasingCurve.Type.InOutCubic)

    # ── Sidebar toggle ────────────────────────────────────────────────────────

    def _toggle_sidebar(self):
        # Animatsiya davomida qayta bosishni e'tiborsiz qoldir
        if self._anim.state() == QAbstractAnimation.State.Running:
            return

        self._collapsed = not self._collapsed
        current = self.sidebar.width()
        target = SIDEBAR_COLLAPSED if self._collapsed else SIDEBAR_EXPANDED

        # maximumWidth animatsiyasi (kengayish/qisqarish uchun asosiy)
        self._anim.setStartValue(current)
        self._anim.setEndValue(target)
        self._anim.start()

        # minimumWidth animatsiyasi (bir xil tezlikda)
        self._anim2.setStartValue(current)
        self._anim2.setEndValue(target)
        self._anim2.start()

        # UI elementlarini yangilash
        for btn in self.nav_buttons:
            btn.set_collapsed(self._collapsed)

        if self._collapsed:
            self._logo_lbl.setVisible(False)
            self._user_lbl.setVisible(False)
            self._student_mode_btn.setText("🖥️")
            self._student_mode_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {COLORS['accent']};
                    color: white; border: none; border-radius: 8px;
                    padding: 9px 4px; font-size: 16px;
                    text-align: center;
                }}
                QPushButton:hover {{ background: {COLORS['accent_light']}; }}
            """)
            self._logout_btn.setText("🚪")
            self._logout_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {COLORS['bg_light']};
                    border: 1px solid {COLORS['border']};
                    border-radius: 8px;
                    color: white;
                    font-size: 16px;
                    padding: 8px 4px;
                    text-align: center;
                    min-height: 0;
                }}
                QPushButton:hover {{ background: {COLORS['primary']}; color: white; }}
            """)
            self._toggle_btn.setText("▶")
            self._toggle_btn.setToolTip("Sidebarni ochish")
        else:
            self._logo_lbl.setVisible(True)
            self._user_lbl.setVisible(True)
            self._student_mode_btn.setText("  🖥️  O'quvchi rejimi")
            self._student_mode_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {COLORS['accent']};
                    color: white; border: none; border-radius: 8px;
                    padding: 9px 6px; font-size: 12px; font-weight: bold;
                    text-align: center;
                }}
                QPushButton:hover {{ background: {COLORS['accent_light']}; }}
            """)
            self._logout_btn.setText("  🚪  Chiqish")
            self._logout_btn.setObjectName("secondary")
            self._logout_btn.setStyleSheet("")
            self._toggle_btn.setText("◀")
            self._toggle_btn.setToolTip("Sidebarni yig'ish")

    def _on_sidebar_anim_done(self):
        target = SIDEBAR_COLLAPSED if self._collapsed else SIDEBAR_EXPANDED
        self.sidebar.setFixedWidth(target)

    # ── Sahifa ko'rsatish ─────────────────────────────────────────────────────

    def _show_section(self, index: int):
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)
        w = self.stack.currentWidget()
        if hasattr(w, "refresh"):
            w.refresh()

    # ── Boshqa amallar ────────────────────────────────────────────────────────

    def _open_student_mode(self):
        from ..student.info_window import StudentInfoWindow
        self._sw = StudentInfoWindow()
        self._sw.show()

    def _logout(self):
        r = QMessageBox.question(
            self, "Chiqish", "Tizimdan chiqmoqchimisiz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if r == QMessageBox.StandardButton.Yes:
            api.logout()
            from ...main import restart_to_login
            restart_to_login(self)
