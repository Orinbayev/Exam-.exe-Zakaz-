"""
Login oynasi — professional, zamonaviy dizayn.
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFrame,
    QGraphicsDropShadowEffect, QToolButton
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QRect, QRectF, QPoint
from PyQt6.QtGui import (
    QFont, QColor, QGuiApplication, QPainter,
    QLinearGradient, QRadialGradient, QBrush, QPen
)
from ..api_client import api, APIError
from ..config import Config
from ..styles import COLORS


# ─────────────────────────────────────────────────────────────────────────────
# Login thread
# ─────────────────────────────────────────────────────────────────────────────

class LoginThread(QThread):
    success = pyqtSignal(dict)
    error   = pyqtSignal(str)

    def __init__(self, server_url, username, password):
        super().__init__()
        self.server_url = server_url
        self.username   = username
        self.password   = password

    def run(self):
        try:
            Config.set("server_url", self.server_url)
            self.success.emit(api.login(self.username, self.password))
        except APIError as e:
            self.error.emit(str(e))
        except Exception as e:
            self.error.emit(f"Kutilmagan xato: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# Dekorativ fon (painted background)
# ─────────────────────────────────────────────────────────────────────────────

class _BgWidget(QWidget):
    """Gradient fon + yaltiroq aylana dekoratsiyalari."""

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        # Asosiy gradient
        g = QLinearGradient(0, 0, w, h)
        g.setColorAt(0.00, QColor("#060E1A"))
        g.setColorAt(0.45, QColor("#0B1E35"))
        g.setColorAt(1.00, QColor("#07131F"))
        p.fillRect(self.rect(), QBrush(g))

        # Yuqori-chap yaltiroq doira
        def _glow(cx, cy, r, color_hex, alpha=55):
            rg = QRadialGradient(cx, cy, r)
            c = QColor(color_hex)
            c.setAlpha(alpha)
            rg.setColorAt(0.0, c)
            c2 = QColor(color_hex); c2.setAlpha(0)
            rg.setColorAt(1.0, c2)
            p.setBrush(QBrush(rg))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(int(cx - r), int(cy - r), int(r * 2), int(r * 2))

        _glow(-30,  -30,  200, "#1565C0", 70)
        _glow(w+30,  h+30, 220, "#0D47A1", 60)
        _glow(w-40,  60,   130, "#42A5F5", 35)
        _glow(60,   h-60,  160, "#1976D2", 40)

        # Nozik grid nuqtalari
        p.setPen(QPen(QColor(255, 255, 255, 8), 1))
        for x in range(0, w, 32):
            for y in range(0, h, 32):
                p.drawPoint(x, y)


# ─────────────────────────────────────────────────────────────────────────────
# Input wrapper (label + maydon)
# ─────────────────────────────────────────────────────────────────────────────

_INPUT_STYLE = """
QLineEdit {
    background: rgba(255, 255, 255, 0.06);
    color: white;
    border: 1.5px solid rgba(255, 255, 255, 0.13);
    border-radius: 10px;
    padding: 0px 14px;
    font-size: 13px;
    min-height: 44px;
}
QLineEdit:focus {
    border: 1.5px solid #42A5F5;
    background: rgba(66, 165, 245, 0.08);
}
"""

_LABEL_STYLE = "color: #78909C; font-size: 10px; font-weight: 600; letter-spacing: 1px;"

def _input_block(label_text: str) -> tuple:
    """(wrapper QWidget, QLineEdit) qaytaradi."""
    w = QWidget()
    w.setStyleSheet("background: transparent;")
    lay = QVBoxLayout(w)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(6)
    lbl = QLabel(label_text.upper())
    lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
    lbl.setStyleSheet(_LABEL_STYLE)
    inp = QLineEdit()
    inp.setStyleSheet(_INPUT_STYLE)
    inp.setFont(QFont("Segoe UI", 13))
    lay.addWidget(lbl)
    lay.addWidget(inp)
    return w, inp


# ─────────────────────────────────────────────────────────────────────────────
# Asosiy oyna
# ─────────────────────────────────────────────────────────────────────────────

class LoginWindow(QMainWindow):
    login_success = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Smart Exam System — Kirish")
        self.setFixedSize(460, 620)
        self._thread = None
        self._build()
        self._center()

    def _center(self):
        sc = QGuiApplication.primaryScreen().geometry()
        self.move(
            (sc.width()  - self.width())  // 2,
            (sc.height() - self.height()) // 2,
        )

    # ── UI qurilishi ──────────────────────────────────────────────────────────

    def _build(self):
        bg = _BgWidget()
        self.setCentralWidget(bg)

        root = QVBoxLayout(bg)
        root.setContentsMargins(40, 38, 40, 28)
        root.setSpacing(0)
        root.setAlignment(Qt.AlignmentFlag.AlignTop)

        # ── Logo badge ────────────────────────────────────────────────────────
        badge_row = QHBoxLayout()
        badge = QWidget()
        badge.setFixedSize(76, 76)
        badge.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 #1E88E5, stop:1 #0D47A1);
                border-radius: 22px;
            }
        """)
        sh = QGraphicsDropShadowEffect()
        sh.setBlurRadius(32)
        sh.setColor(QColor(21, 101, 192, 160))
        sh.setOffset(0, 8)
        badge.setGraphicsEffect(sh)

        b_lay = QVBoxLayout(badge)
        b_lay.setContentsMargins(0, 0, 0, 0)
        ico = QLabel("🎓")
        ico.setFont(QFont("Segoe UI Emoji", 32))
        ico.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ico.setStyleSheet("background: transparent;")
        b_lay.addWidget(ico)

        badge_row.addStretch()
        badge_row.addWidget(badge)
        badge_row.addStretch()
        root.addLayout(badge_row)
        root.addSpacing(20)

        # ── Sarlavha ──────────────────────────────────────────────────────────
        title = QLabel("Smart Exam System")
        title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: white; background: transparent;")
        root.addWidget(title)

        sub = QLabel("Tizimga kirish")
        sub.setFont(QFont("Segoe UI", 11))
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet("color: #546E7A; background: transparent; margin-top: 2px;")
        root.addWidget(sub)
        root.addSpacing(28)

        # ── Karta ─────────────────────────────────────────────────────────────
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.055);
                border: 1px solid rgba(255, 255, 255, 0.10);
                border-radius: 18px;
            }
        """)
        card_sh = QGraphicsDropShadowEffect()
        card_sh.setBlurRadius(50)
        card_sh.setColor(QColor(0, 0, 0, 160))
        card_sh.setOffset(0, 14)
        card.setGraphicsEffect(card_sh)

        cl = QVBoxLayout(card)
        cl.setContentsMargins(28, 28, 28, 28)
        cl.setSpacing(14)

        # Server IP
        srv_w, self.server_input = _input_block("🌐  Server IP manzili")
        self.server_input.setPlaceholderText("https://exam-exe-zakaz-production.up.railway.app")
        self.server_input.setText(Config.server_url())
        cl.addWidget(srv_w)

        # Username
        usr_w, self.username_input = _input_block("👤  Foydalanuvchi nomi")
        self.username_input.setPlaceholderText("username kiriting")
        cl.addWidget(usr_w)

        # Password + ko'rsatish tugmasi
        pwd_w, self.password_input = _input_block("🔒  Parol")
        self.password_input.setPlaceholderText("••••••••")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.returnPressed.connect(self._do_login)

        self._eye = QToolButton(self.password_input)
        self._eye.setCursor(Qt.CursorShape.PointingHandCursor)
        self._eye.setCheckable(True)
        self._eye.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
        self._eye.setText("Ko'rsat")
        self._eye.setStyleSheet("""
            QToolButton {
                background: transparent;
                border: none;
                color: #546E7A;
                font-size: 9px;
                font-weight: 700;
                padding: 0 10px;
                letter-spacing: 0.3px;
            }
            QToolButton:hover { color: #90CAF9; }
            QToolButton:checked { color: #42A5F5; }
        """)
        self._eye.toggled.connect(self._toggle_eye)
        cl.addWidget(pwd_w)

        # Xato banner
        self.err_frame = QFrame()
        self.err_frame.setStyleSheet("""
            QFrame {
                background: rgba(239,83,80,0.12);
                border: 1px solid rgba(239,83,80,0.40);
                border-radius: 8px;
            }
        """)
        ef = QHBoxLayout(self.err_frame)
        ef.setContentsMargins(12, 8, 12, 8)
        self.err_lbl = QLabel()
        self.err_lbl.setFont(QFont("Segoe UI", 10))
        self.err_lbl.setStyleSheet("color: #FF8A80; background: transparent;")
        self.err_lbl.setWordWrap(True)
        ef.addWidget(self.err_lbl)
        self.err_frame.setVisible(False)
        cl.addWidget(self.err_frame)

        # Kirish tugmasi
        self.login_btn = QPushButton("Kirish")
        self.login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_btn.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        self.login_btn.setMinimumHeight(48)
        self.login_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1565C0, stop:1 #1E88E5);
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 14px;
                font-weight: bold;
                letter-spacing: 0.5px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1976D2, stop:1 #42A5F5);
            }
            QPushButton:pressed {
                background: #0D47A1;
            }
            QPushButton:disabled {
                background: rgba(255,255,255,0.10);
                color: rgba(255,255,255,0.35);
            }
        """)
        self.login_btn.clicked.connect(self._do_login)
        cl.addWidget(self.login_btn)

        root.addWidget(card)
        root.addStretch()

        # ── Separator chiziq ──────────────────────────────────────────────────
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("background: rgba(255,255,255,0.07); border: none; min-height: 1px; max-height: 1px;")
        root.addWidget(line)
        root.addSpacing(12)

        # ── Footer ────────────────────────────────────────────────────────────
        footer = QLabel("Smart Exam System  •  v1.0.0")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setFont(QFont("Segoe UI", 9))
        footer.setStyleSheet("color: rgba(255,255,255,0.22); background: transparent;")
        root.addWidget(footer)

    # ── Eye button joylashtirish ──────────────────────────────────────────────

    def _place_eye(self):
        h = self.password_input.height() or 44
        self._eye.adjustSize()
        bw = self._eye.width() + 4
        self._eye.move(self.password_input.width() - bw - 4,
                       (h - self._eye.height()) // 2)
        self.password_input.setTextMargins(0, 0, bw + 8, 0)

    def showEvent(self, e):
        super().showEvent(e)
        self._place_eye()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._place_eye()

    def _toggle_eye(self, checked):
        self.password_input.setEchoMode(
            QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
        )
        self._eye.setText("Yashir" if checked else "Ko'rsat")
        self._place_eye()

    # ── Login mantiq ──────────────────────────────────────────────────────────

    def _do_login(self):
        server = self.server_input.text().strip()
        user   = self.username_input.text().strip()
        passw  = self.password_input.text()

        if not server:
            return self._err("Server IP manzilini kiriting!")
        if not user:
            return self._err("Foydalanuvchi nomini kiriting!")
        if not passw:
            return self._err("Parolni kiriting!")

        if not server.startswith("http"):
            server = f"http://{server}"

        self.login_btn.setEnabled(False)
        self.login_btn.setText("Kirilmoqda…")
        self.err_frame.setVisible(False)

        self._thread = LoginThread(server, user, passw)
        self._thread.success.connect(self._on_success)
        self._thread.error.connect(self._on_error)
        self._thread.start()

    def _on_success(self, result: dict):
        self.login_btn.setEnabled(True)
        self.login_btn.setText("Kirish")
        self.login_success.emit(result.get("role", ""))

    def _on_error(self, msg: str):
        self.login_btn.setEnabled(True)
        self.login_btn.setText("Kirish")
        self._err(msg)

    def _err(self, msg: str):
        self.err_lbl.setText(f"⚠  {msg}")
        self.err_frame.setVisible(True)
