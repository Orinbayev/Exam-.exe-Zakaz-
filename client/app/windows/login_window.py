"""
Login oynasi — toza, professional dizayn.
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFrame,
    QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QGuiApplication
from ..api_client import api, APIError
from ..config import Config
from ..styles import COLORS


# ── Login thread ──────────────────────────────────────────────────────────────

class LoginThread(QThread):
    success = pyqtSignal(dict)
    error   = pyqtSignal(str)

    def __init__(self, server_url: str, username: str, password: str):
        super().__init__()
        self.server_url = server_url
        self.username   = username
        self.password   = password

    def run(self):
        try:
            Config.set("server_url", self.server_url)
            result = api.login(self.username, self.password)
            self.success.emit(result)
        except APIError as e:
            self.error.emit(str(e))
        except Exception as e:
            self.error.emit(f"Kutilmagan xato: {e}")


# ── Login oynasi ──────────────────────────────────────────────────────────────

_WIN_STYLE = f"""
QMainWindow, QWidget {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #0A1929, stop:0.55 #0D2137, stop:1 #0A1929);
    color: white;
    font-family: 'Segoe UI', Arial, sans-serif;
}}
QLabel {{
    background: transparent;
    color: white;
}}
QLineEdit {{
    background: rgba(255,255,255,0.08);
    color: white;
    border: 1.5px solid rgba(255,255,255,0.18);
    border-radius: 10px;
    padding: 10px 14px;
    font-size: 13px;
    min-height: 40px;
    selection-background-color: {COLORS['primary']};
}}
QLineEdit:focus {{
    border: 2px solid {COLORS['primary_light']};
    background: rgba(255,255,255,0.12);
}}
QLineEdit::placeholder {{
    color: rgba(255,255,255,0.35);
}}
QPushButton#login_btn {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {COLORS['primary']}, stop:1 {COLORS['primary_light']});
    color: white;
    border: none;
    border-radius: 10px;
    font-size: 14px;
    font-weight: bold;
    min-height: 46px;
}}
QPushButton#login_btn:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {COLORS['primary_light']}, stop:1 #64B5F6);
}}
QPushButton#login_btn:disabled {{
    background: rgba(255,255,255,0.12);
    color: rgba(255,255,255,0.40);
}}
"""


class LoginWindow(QMainWindow):
    login_success = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Smart Exam System — Kirish")
        self.setFixedSize(460, 540)
        self.setStyleSheet(_WIN_STYLE)
        self._thread = None
        self._build()
        self._center()

    def _center(self):
        sc = QGuiApplication.primaryScreen().geometry()
        self.move(
            (sc.width()  - self.width())  // 2,
            (sc.height() - self.height()) // 2,
        )

    def _build(self):
        root_w = QWidget()
        self.setCentralWidget(root_w)
        root = QVBoxLayout(root_w)
        root.setContentsMargins(36, 28, 36, 24)
        root.setSpacing(0)

        # ── Yuqori: logo + sarlavha ───────────────────────────────────────────
        logo = QLabel("🎓")
        logo.setFont(QFont("Segoe UI Emoji", 42))
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(logo)

        title = QLabel("Smart Exam System")
        title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: white; margin-top: 4px;")
        root.addWidget(title)

        subtitle = QLabel("Zamonaviy test tizimi")
        subtitle.setFont(QFont("Segoe UI", 11))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet(f"color: {COLORS['text_secondary']}; margin-bottom: 20px;")
        root.addWidget(subtitle)

        # ── Karta ─────────────────────────────────────────────────────────────
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: rgba(255,255,255,0.06);
                border: 1px solid rgba(255,255,255,0.12);
                border-radius: 16px;
            }
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(40)
        shadow.setColor(QColor(0, 0, 0, 140))
        shadow.setOffset(0, 10)
        card.setGraphicsEffect(shadow)

        cl = QVBoxLayout(card)
        cl.setContentsMargins(26, 22, 26, 22)
        cl.setSpacing(6)

        def _lbl(text: str) -> QLabel:
            l = QLabel(text)
            l.setFont(QFont("Segoe UI", 10))
            l.setStyleSheet(f"color: {COLORS['text_secondary']}; margin-top: 6px;")
            return l

        # Server IP
        cl.addWidget(_lbl("🌐  Server IP manzili"))
        self.server_input = QLineEdit()
        self.server_input.setPlaceholderText("http://192.168.1.100:8001")
        self.server_input.setText(Config.server_url())
        cl.addWidget(self.server_input)

        # Username
        cl.addWidget(_lbl("👤  Foydalanuvchi nomi"))
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("username")
        cl.addWidget(self.username_input)

        # Password
        cl.addWidget(_lbl("🔒  Parol"))
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("••••••••")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.returnPressed.connect(self._do_login)
        cl.addWidget(self.password_input)

        # Xato xabar
        self.status_lbl = QLabel("")
        self.status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_lbl.setWordWrap(True)
        self.status_lbl.setFont(QFont("Segoe UI", 11))
        self.status_lbl.setStyleSheet(
            "color: #EF5350; background: transparent; min-height: 18px; margin-top: 6px;"
        )
        cl.addWidget(self.status_lbl)

        # Login tugmasi
        self.login_btn = QPushButton("  Kirish")
        self.login_btn.setObjectName("login_btn")
        self.login_btn.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        self.login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_btn.clicked.connect(self._do_login)
        cl.addWidget(self.login_btn)

        root.addWidget(card)
        root.addStretch()

        # ── Footer ────────────────────────────────────────────────────────────
        footer = QLabel("v1.0.0  •  Smart Exam System")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setFont(QFont("Segoe UI", 10))
        footer.setStyleSheet(f"color: {COLORS['text_secondary']};")
        root.addWidget(footer)

    # ── Mantiq ───────────────────────────────────────────────────────────────

    def _do_login(self):
        server  = self.server_input.text().strip()
        user    = self.username_input.text().strip()
        passw   = self.password_input.text()

        if not server:
            self._err("Server IP manzilini kiriting!")
            self.server_input.setFocus()
            return
        if not user:
            self._err("Foydalanuvchi nomini kiriting!")
            self.username_input.setFocus()
            return
        if not passw:
            self._err("Parolni kiriting!")
            self.password_input.setFocus()
            return

        if not server.startswith("http"):
            server = f"http://{server}"

        self.login_btn.setEnabled(False)
        self.login_btn.setText("  Kirilmoqda…")
        self.status_lbl.setText("")

        self._thread = LoginThread(server, user, passw)
        self._thread.success.connect(self._on_success)
        self._thread.error.connect(self._on_error)
        self._thread.start()

    def _on_success(self, result: dict):
        self.login_btn.setEnabled(True)
        self.login_btn.setText("  Kirish")
        self.login_success.emit(result.get("role", ""))

    def _on_error(self, msg: str):
        self.login_btn.setEnabled(True)
        self.login_btn.setText("  Kirish")
        self._err(msg)

    def _err(self, msg: str):
        self.status_lbl.setText(f"⚠  {msg}")
