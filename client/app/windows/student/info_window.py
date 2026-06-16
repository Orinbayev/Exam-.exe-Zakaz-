"""
O'quvchi — test boshlash oynasi (full-screen kiosk).
Sinf tanlash → ism tanlash → test tanlash → boshlash.
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QPushButton, QFrame, QGraphicsDropShadowEffect,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QRectF
from PyQt6.QtGui import (
    QFont, QColor, QPainter, QLinearGradient, QRadialGradient, QBrush, QPen,
)
from ...api_client import api, APIError


# ── Chiroyli gradient fon ─────────────────────────────────────────────────────

class _BgWidget(QWidget):
    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        # Asosiy gradient
        g = QLinearGradient(0, 0, w, h)
        g.setColorAt(0.00, QColor("#061236"))
        g.setColorAt(0.40, QColor("#0D2B6E"))
        g.setColorAt(0.70, QColor("#1148A0"))
        g.setColorAt(1.00, QColor("#061A50"))
        p.fillRect(self.rect(), QBrush(g))

        # Glow doiralari
        def _glow(cx, cy, r, col, alpha=55):
            rg = QRadialGradient(cx, cy, r)
            c1 = QColor(col); c1.setAlpha(alpha)
            c2 = QColor(col); c2.setAlpha(0)
            rg.setColorAt(0, c1); rg.setColorAt(1, c2)
            p.setBrush(QBrush(rg)); p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(int(cx-r), int(cy-r), int(r*2), int(r*2))

        _glow(w * 0.12, h * 0.15, 260, "#1E88E5", 60)
        _glow(w * 0.88, h * 0.85, 300, "#0D47A1", 55)
        _glow(w * 0.80, h * 0.10, 180, "#42A5F5", 35)
        _glow(w * 0.20, h * 0.88, 220, "#1565C0", 40)
        _glow(w * 0.50, h * 0.50, 350, "#1A3A8A", 25)

        # Nuqtali panjara
        p.setPen(QPen(QColor(255, 255, 255, 7), 1))
        for x in range(0, w, 36):
            for y in range(0, h, 36):
                p.drawPoint(x, y)
        p.end()


# ── Stil konstantalar ─────────────────────────────────────────────────────────

COMBO_STYLE = """
QComboBox {
    background: rgba(255,255,255,0.10);
    color: white;
    border: 1.5px solid rgba(255,255,255,0.22);
    border-radius: 14px;
    padding: 0 18px;
    font-size: 15px;
    font-family: 'Segoe UI', Arial;
    min-height: 54px;
}
QComboBox:focus {
    background: rgba(255,255,255,0.16);
    border: 2px solid rgba(255,255,255,0.60);
}
QComboBox::drop-down { border: none; width: 34px; }
QComboBox::down-arrow {
    image: none;
    border-left: 6px solid transparent;
    border-right: 6px solid transparent;
    border-top: 7px solid rgba(255,255,255,0.75);
    margin-right: 14px;
}
QComboBox QAbstractItemView {
    background: #1565C0;
    color: white;
    selection-background-color: #0D47A1;
    border: none;
    font-size: 14px;
    padding: 6px;
}
"""

START_STYLE = """
QPushButton {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #FF6F00, stop:1 #FFA000);
    color: white;
    border: none;
    border-radius: 16px;
    font-size: 18px;
    font-weight: 700;
    font-family: 'Segoe UI', Arial;
    min-height: 62px;
    letter-spacing: 0.5px;
}
QPushButton:hover {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #FFA000, stop:1 #FFD740);
}
QPushButton:pressed  { background: #E65100; }
QPushButton:disabled {
    background: rgba(255,255,255,0.15);
    color: rgba(255,255,255,0.40);
}
"""


# ── Background thread ─────────────────────────────────────────────────────────

class _StartThread(QThread):
    done  = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, test_id, first, last, cls_name):
        super().__init__()
        self._tid, self._first, self._last, self._cls = (
            test_id, first, last, cls_name
        )

    def run(self):
        try:
            self.done.emit(api.start_exam(self._tid, self._first, self._last, self._cls))
        except APIError as e:
            self.error.emit(str(e))


# ── Asosiy oyna ──────────────────────────────────────────────────────────────

class StudentInfoWindow(QMainWindow):
    def __init__(self, pre_select: dict = None):
        super().__init__()
        self.setWindowTitle("Smart Exam — Test Boshlash")
        self._thread    = None
        self._classes:  list = []
        self._students: list = []
        self._tests:    list = []
        self._pre_select  = pre_select or {}
        self._last_select: dict = {}
        self._build_ui()
        self.showMaximized()      # ← butun ekranni to'ldiradi
        self._load_initial()

    # ── UI qurilishi ──────────────────────────────────────────────────────────

    def _build_ui(self):
        bg = _BgWidget()
        self.setCentralWidget(bg)

        # To'liq ekran layout — karta markazida
        outer = QVBoxLayout(bg)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addStretch(1)

        # Gorizontal markazlash
        h_row = QHBoxLayout()
        h_row.setContentsMargins(0, 0, 0, 0)
        h_row.addStretch(1)

        # Karta konteyner (max 540px kenglik)
        panel = QWidget()
        panel.setFixedWidth(540)
        panel.setStyleSheet("background: transparent;")
        panel_lay = QVBoxLayout(panel)
        panel_lay.setContentsMargins(0, 0, 0, 0)
        panel_lay.setSpacing(0)

        # ── Logo + sarlavha ───────────────────────────────────────────────────
        ico = QLabel("🎓")
        ico.setFont(QFont("Segoe UI Emoji", 50))
        ico.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ico.setStyleSheet("background: transparent; color: white;")
        panel_lay.addWidget(ico)
        panel_lay.addSpacing(8)

        ttl = QLabel("Test Boshlash")
        ttl.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
        ttl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ttl.setStyleSheet("color: white; background: transparent;")
        panel_lay.addWidget(ttl)
        panel_lay.addSpacing(4)

        sub = QLabel("Quyidagi ma'lumotlarni to'ldiring")
        sub.setFont(QFont("Segoe UI", 12))
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet("color: rgba(255,255,255,0.55); background: transparent;")
        panel_lay.addWidget(sub)
        panel_lay.addSpacing(28)

        # ── Karta ─────────────────────────────────────────────────────────────
        card = QFrame()
        card.setObjectName("MainCard")
        card.setStyleSheet("""
            QFrame#MainCard {
                background: rgba(255,255,255,0.08);
                border: 1.5px solid rgba(255,255,255,0.18);
                border-radius: 24px;
            }
        """)
        sh = QGraphicsDropShadowEffect()
        sh.setBlurRadius(60)
        sh.setColor(QColor(0, 0, 0, 120))
        sh.setOffset(0, 16)
        card.setGraphicsEffect(sh)

        cl = QVBoxLayout(card)
        cl.setContentsMargins(30, 30, 30, 30)
        cl.setSpacing(16)

        # 1) Sinf
        cl.addLayout(_label_row("🏫", "Sinf tanlang"))
        self._cls_combo = QComboBox()
        self._cls_combo.setStyleSheet(COMBO_STYLE)
        self._cls_combo.addItem("⏳  Yuklanmoqda...", None)
        self._cls_combo.currentIndexChanged.connect(self._on_class_change)
        cl.addWidget(self._cls_combo)

        # 2) O'quvchi
        cl.addLayout(_label_row("👤", "O'quvchini tanlang"))
        self._stu_combo = QComboBox()
        self._stu_combo.setStyleSheet(COMBO_STYLE)
        self._stu_combo.addItem("— Avval sinfni tanlang —", None)
        cl.addWidget(self._stu_combo)

        # 3) Fan / test
        cl.addLayout(_label_row("📋", "Fan / Test tanlang"))
        self._tst_combo = QComboBox()
        self._tst_combo.setStyleSheet(COMBO_STYLE)
        self._tst_combo.addItem("— Avval sinfni tanlang —", None)
        cl.addWidget(self._tst_combo)

        # Xato banner
        self._err_lbl = QLabel("")
        self._err_lbl.setStyleSheet(
            "color:#FF8A65; font-size:13px;"
            " background:rgba(239,83,80,0.14);"
            " border:1px solid rgba(239,83,80,0.35);"
            " border-radius:10px; padding:10px 14px;"
        )
        self._err_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._err_lbl.setWordWrap(True)
        self._err_lbl.hide()
        cl.addWidget(self._err_lbl)

        panel_lay.addWidget(card)
        panel_lay.addSpacing(20)

        # ── Boshlash tugmasi ──────────────────────────────────────────────────
        self._start_btn = QPushButton("🚀   Testni Boshlash")
        self._start_btn.setStyleSheet(START_STYLE)
        self._start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._start_btn.clicked.connect(self._start)
        panel_lay.addWidget(self._start_btn)

        # Footer
        panel_lay.addSpacing(14)
        footer = QLabel("Smart Exam System  •  v1.0")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setFont(QFont("Segoe UI", 9))
        footer.setStyleSheet("color: rgba(255,255,255,0.20); background: transparent;")
        panel_lay.addWidget(footer)

        h_row.addWidget(panel)
        h_row.addStretch(1)
        outer.addLayout(h_row)
        outer.addStretch(1)

    # ── Data loading ──────────────────────────────────────────────────────────

    def _load_initial(self):
        self._tst_combo.clear()
        self._tst_combo.addItem("— Avval sinfni tanlang —", None)
        self._start_btn.setEnabled(False)

        try:
            self._classes = api.get_classes_public()
            self._cls_combo.clear()
            if not self._classes:
                self._cls_combo.addItem("— Aktiv sinf yo'q —", None)
            else:
                self._cls_combo.addItem("— Sinfni tanlang —", None)
                for c in self._classes:
                    self._cls_combo.addItem(f"  {c['name']}", c["id"])

            # Oldingi tanlov qayta tiklash
            pre_cls = self._pre_select.get("cls_id")
            if pre_cls:
                for i in range(self._cls_combo.count()):
                    if self._cls_combo.itemData(i) == pre_cls:
                        self._cls_combo.setCurrentIndex(i)
                        break
        except APIError as e:
            self._cls_combo.clear()
            self._cls_combo.addItem("— Serverga ulanib bo'lmadi —", None)
            self._show_err(f"Server xatosi: {e}")

    def _on_class_change(self):
        cls_id = self._cls_combo.currentData()
        self._stu_combo.clear()
        self._tst_combo.clear()
        self._students = []
        self._tests    = []

        if cls_id is None:
            self._stu_combo.addItem("— Avval sinfni tanlang —", None)
            self._tst_combo.addItem("— Avval sinfni tanlang —", None)
            self._start_btn.setEnabled(False)
            return

        try:
            self._students = api.get_students_public(cls_id)
            if not self._students:
                self._stu_combo.addItem("— Bu sinfda o'quvchi yo'q —", None)
            else:
                self._stu_combo.addItem("— O'quvchini tanlang —", None)
                for s in self._students:
                    self._stu_combo.addItem(f"  {s['last_name']} {s['first_name']}", s["id"])
        except APIError:
            self._stu_combo.addItem("— Yuklanmadi —", None)

        try:
            self._tests = api.get_class_fans(cls_id)
            if not self._tests:
                self._tst_combo.addItem("— Bu sinfga fan biriktirilmagan —", None)
                self._start_btn.setEnabled(False)
            else:
                self._start_btn.setEnabled(True)
                for f in self._tests:
                    self._tst_combo.addItem(
                        f"📚  {f['fan_name']}  ·  ⏱ {f.get('time_limit', 30)} daqiqa",
                        f["test_id"],
                    )
        except APIError:
            self._tst_combo.addItem("— Fanlar yuklanmadi —", None)
            self._start_btn.setEnabled(False)

        # Oldingi tanlovni qayta tiklash
        pre_stu  = self._pre_select.get("stu_id")
        pre_test = self._pre_select.get("test_id")
        if pre_stu:
            for i in range(self._stu_combo.count()):
                if self._stu_combo.itemData(i) == pre_stu:
                    self._stu_combo.setCurrentIndex(i)
                    break
        if pre_test:
            for i in range(self._tst_combo.count()):
                if self._tst_combo.itemData(i) == pre_test:
                    self._tst_combo.setCurrentIndex(i)
                    break

    # ── Start ─────────────────────────────────────────────────────────────────

    def _start(self):
        cls_id   = self._cls_combo.currentData()
        cls_name = self._cls_combo.currentText().strip()
        if cls_id is None:
            self._show_err("⚠  Avval sinfni tanlang!")
            return

        stu_id = self._stu_combo.currentData()
        if stu_id is None:
            self._show_err("⚠  O'quvchini tanlang!")
            return

        stu = next((s for s in self._students if s["id"] == stu_id), None)
        if not stu:
            self._show_err("⚠  O'quvchi topilmadi!")
            return

        test_id = self._tst_combo.currentData()
        if test_id is None:
            self._show_err("⚠  Testni tanlang!")
            return

        self._last_select = {"cls_id": cls_id, "stu_id": stu_id, "test_id": test_id}

        self._start_btn.setEnabled(False)
        self._start_btn.setText("⏳   Yuklanmoqda...")
        self._err_lbl.hide()

        self._thread = _StartThread(test_id, stu["first_name"], stu["last_name"], cls_name)
        self._thread.done.connect(self._on_started)
        self._thread.error.connect(self._on_error)
        self._thread.start()

    def _on_started(self, data: dict):
        from .exam_window import ExamWindow
        self._exam = ExamWindow(data, pre_select=self._last_select)
        self._exam.show()
        self.close()

    def _on_error(self, msg: str):
        self._start_btn.setEnabled(True)
        self._start_btn.setText("🚀   Testni Boshlash")
        self._show_err(msg)

    def _show_err(self, msg: str):
        self._err_lbl.setText(msg)
        self._err_lbl.show()
        QTimer.singleShot(5000, self._err_lbl.hide)


# ── Yordamchi funksiya ────────────────────────────────────────────────────────

def _label_row(icon: str, text: str) -> QHBoxLayout:
    row = QHBoxLayout()
    row.setSpacing(8)
    ico = QLabel(icon)
    ico.setFont(QFont("Segoe UI Emoji", 13))
    ico.setStyleSheet("background: transparent; color: white;")
    lbl = QLabel(text)
    lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
    lbl.setStyleSheet("color: rgba(255,255,255,0.75); background: transparent;")
    row.addWidget(ico)
    row.addWidget(lbl)
    row.addStretch()
    return row
