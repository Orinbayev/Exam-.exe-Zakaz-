"""
Login oynasi — to'liq ekran, gradient fon, markazda karta.
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFrame,
    QGraphicsDropShadowEffect, QToolButton
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import (
    QFont, QColor, QPainter,
    QLinearGradient, QRadialGradient, QBrush, QPen
)
from ..api_client import api, APIError
from ..config import Config
from ..i18n import t


# ─────────────────────────────────────────────────────────────────────────────
# Login thread
# ─────────────────────────────────────────────────────────────────────────────

class WarmupThread(QThread):
    done = pyqtSignal()

    def __init__(self, server_url):
        super().__init__()
        self.server_url = server_url

    def run(self):
        try:
            import requests
            requests.get(f"{self.server_url}/health", timeout=60)
        except Exception:
            pass
        self.done.emit()


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
# To'liq ekran gradient fon
# ─────────────────────────────────────────────────────────────────────────────

class _BgWidget(QWidget):
    """Butun ekranni qoplaydigan gradient fon + dekorativ doiralar."""

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

        def _glow(cx, cy, r, color_hex, alpha=55):
            rg = QRadialGradient(cx, cy, r)
            c  = QColor(color_hex); c.setAlpha(alpha)
            rg.setColorAt(0.0, c)
            c2 = QColor(color_hex); c2.setAlpha(0)
            rg.setColorAt(1.0, c2)
            p.setBrush(QBrush(rg))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(int(cx - r), int(cy - r), int(r * 2), int(r * 2))

        _glow(-30,   -30,  250, "#1565C0", 70)
        _glow(w+30,  h+30, 280, "#0D47A1", 60)
        _glow(w-40,   60,  180, "#42A5F5", 35)
        _glow(60,    h-60, 200, "#1976D2", 40)

        # Grid nuqtalari
        p.setPen(QPen(QColor(255, 255, 255, 8), 1))
        for x in range(0, w, 32):
            for y in range(0, h, 32):
                p.drawPoint(x, y)


# ─────────────────────────────────────────────────────────────────────────────
# Input blok (label + field)
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


def _input_block(label_text: str):
    """(wrapper QWidget, QLineEdit) qaytaradi."""
    w   = QWidget(); w.setStyleSheet("background: transparent;")
    lay = QVBoxLayout(w); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(6)
    lbl = QLabel(label_text.upper())
    lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
    lbl.setStyleSheet(_LABEL_STYLE)
    inp = QLineEdit()
    inp.setStyleSheet(_INPUT_STYLE)
    inp.setFont(QFont("Segoe UI", 13))
    lay.addWidget(lbl); lay.addWidget(inp)
    return w, inp


# ─────────────────────────────────────────────────────────────────────────────
# Asosiy oyna
# ─────────────────────────────────────────────────────────────────────────────

class LoginWindow(QMainWindow):
    login_success = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle(t("login.window_title"))
        self.setMinimumSize(800, 560)
        self._thread = None
        self._warmup = None
        self._slow_timer = QTimer(self)
        self._slow_timer.setSingleShot(True)
        self._slow_timer.timeout.connect(self._show_waking_msg)
        self._build()
        self._start_warmup()

    # ── UI qurilishi ──────────────────────────────────────────────────────────

    def _build(self):
        # To'liq ekran gradient fon
        bg = _BgWidget()
        self.setCentralWidget(bg)

        # ── Tashqi layout: chapdan-o'ngga, karta markazda ─────────────────────
        outer = QHBoxLayout(bg)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addStretch(1)

        # Markaziy ustun — kenglik ekran holatiga ko'ra moslashadi
        center = QWidget()
        center.setFixedWidth(480)
        center.setStyleSheet("background: transparent;")
        outer.addWidget(center)
        outer.addStretch(1)

        # ── Vertikal layout: yuqori-pastga, karta vertikal markazda ──────────
        root = QVBoxLayout(center)
        root.setContentsMargins(20, 0, 20, 0)
        root.setSpacing(0)
        root.addStretch(2)   # yuqori bo'sh joy (katta)

        # ── Logo badge ────────────────────────────────────────────────────────
        badge_row = QHBoxLayout()
        badge = QWidget(); badge.setFixedSize(76, 76)
        badge.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 #1E88E5, stop:1 #0D47A1);
                border-radius: 22px;
            }
        """)
        sh = QGraphicsDropShadowEffect()
        sh.setBlurRadius(32); sh.setColor(QColor(21, 101, 192, 160)); sh.setOffset(0, 8)
        badge.setGraphicsEffect(sh)

        b_lay = QVBoxLayout(badge); b_lay.setContentsMargins(0, 0, 0, 0)
        ico = QLabel("🎓")
        ico.setFont(QFont("Segoe UI Emoji", 32))
        ico.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ico.setStyleSheet("background: transparent;")
        b_lay.addWidget(ico)

        badge_row.addStretch(); badge_row.addWidget(badge); badge_row.addStretch()
        root.addLayout(badge_row)
        root.addSpacing(20)

        # ── Sarlavha ──────────────────────────────────────────────────────────
        title = QLabel(t("login.title"))
        title.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: white; background: transparent;")
        root.addWidget(title)

        sub = QLabel(t("login.subtitle"))
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
        card_sh.setBlurRadius(50); card_sh.setColor(QColor(0, 0, 0, 160)); card_sh.setOffset(0, 14)
        card.setGraphicsEffect(card_sh)

        cl = QVBoxLayout(card)
        cl.setContentsMargins(28, 28, 28, 28)
        cl.setSpacing(14)

        # Server IP
        srv_w, self.server_input = _input_block(t("login.server_label"))
        self.server_input.setPlaceholderText("https://exam-server-vq86.onrender.com")
        self.server_input.setText(Config.server_url())
        cl.addWidget(srv_w)

        # Username
        usr_w, self.username_input = _input_block(t("login.user_label"))
        self.username_input.setPlaceholderText("username")
        cl.addWidget(usr_w)

        # Password
        pwd_w, self.password_input = _input_block(t("login.pass_label"))
        self.password_input.setPlaceholderText("••••••••")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.returnPressed.connect(self._do_login)

        self._eye = QToolButton(self.password_input)
        self._eye.setCursor(Qt.CursorShape.PointingHandCursor)
        self._eye.setCheckable(True)
        self._eye.setText(t("login.show"))
        self._eye.setStyleSheet("""
            QToolButton {
                background: transparent; border: none;
                color: #546E7A; font-size: 9px; font-weight: 700;
                padding: 0 10px; letter-spacing: 0.3px;
            }
            QToolButton:hover  { color: #90CAF9; }
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
        self.login_btn = QPushButton(t("login.btn"))
        self.login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_btn.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        self.login_btn.setMinimumHeight(48)
        self.login_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1565C0, stop:1 #1E88E5);
                color: white; border: none; border-radius: 10px;
                font-size: 14px; font-weight: bold; letter-spacing: 0.5px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1976D2, stop:1 #42A5F5);
            }
            QPushButton:pressed  { background: #0D47A1; }
            QPushButton:disabled {
                background: rgba(255,255,255,0.10);
                color: rgba(255,255,255,0.35);
            }
        """)
        self.login_btn.clicked.connect(self._do_login)
        cl.addWidget(self.login_btn)

        root.addWidget(card)
        root.addStretch(1)   # pastki bo'sh joy (kichikroq)

        # ── Separator ─────────────────────────────────────────────────────────
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("background: rgba(255,255,255,0.07); border: none; min-height: 1px; max-height: 1px;")
        root.addWidget(line)
        root.addSpacing(12)

        # ── Footer ────────────────────────────────────────────────────────────
        footer = QLabel(t("login.footer"))
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setFont(QFont("Segoe UI", 9))
        footer.setStyleSheet("color: rgba(255,255,255,0.22); background: transparent;")
        root.addWidget(footer)
        root.addSpacing(16)

    # ── Eye tugmasi joylashuvi ────────────────────────────────────────────────

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
        self._eye.setText(t("login.hide") if checked else t("login.show"))
        self._place_eye()

    # ── Server pre-warm ───────────────────────────────────────────────────────

    def _start_warmup(self):
        server = Config.server_url()
        if not server:
            return
        self._warmup = WarmupThread(server)
        self._warmup.start()

    def _show_waking_msg(self):
        if self.login_btn.isEnabled():
            return
        self.login_btn.setText(t("login.waking"))

    # ── Login mantiq ─────────────────────────────────────────────────────────

    def _do_login(self):
        server = self.server_input.text().strip()
        user   = self.username_input.text().strip()
        passw  = self.password_input.text()

        if not server:
            return self._err(t("login.err_server"))
        if not user:
            return self._err(t("login.err_user"))
        if not passw:
            return self._err(t("login.err_pass"))

        if not server.startswith("http"):
            server = f"http://{server}"

        self.login_btn.setEnabled(False)
        self.login_btn.setText(t("login.loading"))
        self.err_frame.setVisible(False)
        self._slow_timer.start(4000)

        self._thread = LoginThread(server, user, passw)
        self._thread.success.connect(self._on_success)
        self._thread.error.connect(self._on_error)
        self._thread.start()

    def _on_success(self, result: dict):
        self._slow_timer.stop()
        self.login_btn.setEnabled(True)
        self.login_btn.setText(t("login.btn"))
        self.login_success.emit(result.get("role", ""))

    def _on_error(self, msg: str):
        self._slow_timer.stop()
        self.login_btn.setEnabled(True)
        self.login_btn.setText(t("login.btn"))
        self._err(msg)

    def _err(self, msg: str):
        self.err_lbl.setText(f"⚠  {msg}")
        self.err_frame.setVisible(True)
