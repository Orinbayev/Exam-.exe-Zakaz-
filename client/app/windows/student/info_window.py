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
from ...i18n import ts


# ── Yorqin gradient fon ───────────────────────────────────────────────────────

class _BgWidget(QWidget):
    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        # Asosiy yorqin gradient — binafsha → ko'k-binafsha → okean ko'k
        g = QLinearGradient(0, 0, w, h)
        g.setColorAt(0.00, QColor("#10024A"))   # chuqur binafsha
        g.setColorAt(0.35, QColor("#3A0CA3"))   # yorqin violet
        g.setColorAt(0.68, QColor("#0077B6"))   # okean ko'k
        g.setColorAt(1.00, QColor("#1A0550"))   # chuqur binafsha
        p.fillRect(self.rect(), QBrush(g))

        # Rang-barang glow doiralari
        def _glow(cx, cy, r, col, alpha=55):
            rg = QRadialGradient(cx, cy, r)
            c1 = QColor(col); c1.setAlpha(alpha)
            c2 = QColor(col); c2.setAlpha(0)
            rg.setColorAt(0, c1); rg.setColorAt(1, c2)
            p.setBrush(QBrush(rg)); p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(int(cx-r), int(cy-r), int(r*2), int(r*2))

        _glow(w * 0.08,  h * 0.12, 280, "#F72585", 80)   # qizil-pushti
        _glow(w * 0.90,  h * 0.88, 320, "#7209B7", 70)   # to'q violet
        _glow(w * 0.85,  h * 0.08, 200, "#4CC9F0", 55)   # moviy
        _glow(w * 0.15,  h * 0.90, 240, "#4361EE", 65)   # ko'k
        _glow(w * 0.50,  h * 0.50, 380, "#3A0CA3", 35)   # markaz violet
        _glow(w * 0.50,  h * 0.20, 160, "#F72585", 45)   # yuqori pushti

        # Nuqtali panjara
        p.setPen(QPen(QColor(255, 255, 255, 10), 1))
        for x in range(0, w, 36):
            for y in range(0, h, 36):
                p.drawPoint(x, y)
        p.end()


# ── Stil konstantalar ─────────────────────────────────────────────────────────

COMBO_STYLE = """
QComboBox {
    background: rgba(255,255,255,0.15);
    color: white;
    border: 2px solid rgba(255,255,255,0.32);
    border-radius: 14px;
    padding: 0 18px;
    font-size: 15px;
    font-family: 'Segoe UI', Arial;
    min-height: 54px;
}
QComboBox:focus {
    background: rgba(255,255,255,0.22);
    border: 2.5px solid rgba(247,37,133,0.80);
}
QComboBox::drop-down { border: none; width: 34px; }
QComboBox::down-arrow {
    image: none;
    border-left: 6px solid transparent;
    border-right: 6px solid transparent;
    border-top: 7px solid rgba(255,255,255,0.85);
    margin-right: 14px;
}
QComboBox QAbstractItemView {
    background: #3A0CA3;
    color: white;
    selection-background-color: #7209B7;
    border: none;
    font-size: 14px;
    padding: 6px;
}
"""

START_STYLE = """
QPushButton {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #FF0080, stop:0.5 #FF6D00, stop:1 #FFD200);
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
        stop:0 #FF3399, stop:0.5 #FF8C00, stop:1 #FFE000);
}
QPushButton:pressed  { background: #CC0060; }
QPushButton:disabled {
    background: rgba(255,255,255,0.18);
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
        self.setWindowTitle(ts("stu.window_title"))
        self._thread    = None
        self._classes:  list = []
        self._students: list = []
        self._tests:    list = []
        self._pre_select  = pre_select or {}
        self._last_select: dict = {}
        self._build_ui()
        self.showMaximized()
        self._load_initial()

    # ── UI qurilishi ──────────────────────────────────────────────────────────

    def _build_ui(self):
        bg = _BgWidget()
        self.setCentralWidget(bg)

        outer = QVBoxLayout(bg)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addStretch(1)

        h_row = QHBoxLayout()
        h_row.setContentsMargins(0, 0, 0, 0)
        h_row.addStretch(1)

        panel = QWidget()
        panel.setFixedWidth(560)
        panel.setStyleSheet("background: transparent;")
        panel_lay = QVBoxLayout(panel)
        panel_lay.setContentsMargins(0, 0, 0, 0)
        panel_lay.setSpacing(0)

        # ── Logo + sarlavha ───────────────────────────────────────────────────
        ico = QLabel("🎓")
        ico.setFont(QFont("Segoe UI Emoji", 54))
        ico.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ico.setStyleSheet("background: transparent; color: white;")
        panel_lay.addWidget(ico)
        panel_lay.addSpacing(6)

        ttl = QLabel(ts("stu.start_title"))
        ttl.setFont(QFont("Segoe UI", 30, QFont.Weight.Bold))
        ttl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ttl.setStyleSheet("""
            color: white;
            background: transparent;
        """)
        panel_lay.addWidget(ttl)
        panel_lay.addSpacing(4)

        sub = QLabel(ts("stu.start_sub"))
        sub.setFont(QFont("Segoe UI", 12))
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet("color: rgba(255,255,255,0.65); background: transparent;")
        panel_lay.addWidget(sub)
        panel_lay.addSpacing(26)

        # ── Karta ─────────────────────────────────────────────────────────────
        card = QFrame()
        card.setObjectName("MainCard")
        card.setStyleSheet("""
            QFrame#MainCard {
                background: rgba(255,255,255,0.12);
                border: 2px solid rgba(255,255,255,0.28);
                border-radius: 24px;
            }
        """)
        sh = QGraphicsDropShadowEffect()
        sh.setBlurRadius(70)
        sh.setColor(QColor(247, 37, 133, 100))
        sh.setOffset(0, 16)
        card.setGraphicsEffect(sh)

        cl = QVBoxLayout(card)
        cl.setContentsMargins(30, 30, 30, 30)
        cl.setSpacing(18)

        # 1) Sinf
        cl.addLayout(_label_row("🏫", ts("stu.class_label")))
        self._cls_combo = QComboBox()
        self._cls_combo.setStyleSheet(COMBO_STYLE)
        self._cls_combo.addItem(ts("stu.class_loading"), None)
        self._cls_combo.currentIndexChanged.connect(self._on_class_change)
        cl.addWidget(self._cls_combo)

        # 2) O'quvchi
        cl.addLayout(_label_row("👤", ts("stu.student_label")))
        self._stu_combo = QComboBox()
        self._stu_combo.setStyleSheet(COMBO_STYLE)
        self._stu_combo.addItem(ts("stu.student_wait"), None)
        cl.addWidget(self._stu_combo)

        # 3) Fan / test
        cl.addLayout(_label_row("📋", ts("stu.test_label")))
        self._tst_combo = QComboBox()
        self._tst_combo.setStyleSheet(COMBO_STYLE)
        self._tst_combo.addItem(ts("stu.test_wait"), None)
        cl.addWidget(self._tst_combo)

        # Xato banner
        self._err_lbl = QLabel("")
        self._err_lbl.setStyleSheet(
            "color:#FF8A65; font-size:13px;"
            " background:rgba(239,83,80,0.18);"
            " border:1.5px solid rgba(239,83,80,0.50);"
            " border-radius:10px; padding:10px 14px;"
        )
        self._err_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._err_lbl.setWordWrap(True)
        self._err_lbl.hide()
        cl.addWidget(self._err_lbl)

        panel_lay.addWidget(card)
        panel_lay.addSpacing(20)

        # ── Boshlash tugmasi ──────────────────────────────────────────────────
        self._start_btn = QPushButton(ts("stu.start_btn"))
        self._start_btn.setStyleSheet(START_STYLE)
        self._start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._start_btn.clicked.connect(self._start)
        panel_lay.addWidget(self._start_btn)

        panel_lay.addSpacing(10)

        # ── Orqaga tugmasi ────────────────────────────────────────────────────
        self._back_btn = QPushButton(ts("stu.back_btn"))
        self._back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._back_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.10);
                color: rgba(255,255,255,0.65);
                border: 1.5px solid rgba(255,255,255,0.22);
                border-radius: 12px;
                font-size: 13px;
                font-weight: bold;
                font-family: 'Segoe UI', Arial;
                min-height: 40px;
                padding: 0 20px;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.18);
                color: white;
                border-color: rgba(255,255,255,0.45);
            }
            QPushButton:pressed {
                background: rgba(255,255,255,0.08);
            }
        """)
        self._back_btn.clicked.connect(self.close)
        panel_lay.addWidget(self._back_btn)

        panel_lay.addSpacing(10)
        footer = QLabel(ts("stu.footer"))
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setFont(QFont("Segoe UI", 9))
        footer.setStyleSheet("color: rgba(255,255,255,0.25); background: transparent;")
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
                self._cls_combo.addItem(ts("stu.class_empty"), None)
            else:
                self._cls_combo.addItem(ts("stu.class_placeholder"), None)
                for c in self._classes:
                    self._cls_combo.addItem(f"  {c['name']}", c["id"])

            pre_cls = self._pre_select.get("cls_id")
            if pre_cls:
                for i in range(self._cls_combo.count()):
                    if self._cls_combo.itemData(i) == pre_cls:
                        self._cls_combo.setCurrentIndex(i)
                        break
        except APIError as e:
            self._cls_combo.clear()
            self._cls_combo.addItem(ts("stu.class_error"), None)
            self._show_err(f"Server xatosi: {e}")

    def _on_class_change(self):
        cls_id = self._cls_combo.currentData()
        self._stu_combo.clear()
        self._tst_combo.clear()
        self._students = []
        self._tests    = []

        if cls_id is None:
            self._stu_combo.addItem(ts("stu.student_wait"), None)
            self._tst_combo.addItem(ts("stu.test_wait"), None)
            self._start_btn.setEnabled(False)
            return

        try:
            self._students = api.get_students_public(cls_id)
            if not self._students:
                self._stu_combo.addItem(ts("stu.student_empty"), None)
            else:
                self._stu_combo.addItem(ts("stu.student_ph"), None)
                for s in self._students:
                    self._stu_combo.addItem(f"  {s['last_name']} {s['first_name']}", s["id"])
        except APIError:
            self._stu_combo.addItem(ts("stu.student_wait"), None)

        try:
            self._tests = api.get_class_fans(cls_id)
            if not self._tests:
                self._tst_combo.addItem(ts("stu.test_empty"), None)
                self._start_btn.setEnabled(False)
            else:
                self._start_btn.setEnabled(True)
                for f in self._tests:
                    self._tst_combo.addItem(
                        f"📚  {f['fan_name']}  ·  ⏱ {f.get('time_limit', 30)} мин.",
                        f["test_id"],
                    )
        except APIError:
            self._tst_combo.addItem(ts("stu.test_wait"), None)
            self._start_btn.setEnabled(False)

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
            self._show_err(ts("stu.err_class"))
            return

        stu_id = self._stu_combo.currentData()
        if stu_id is None:
            self._show_err(ts("stu.err_student"))
            return

        stu = next((s for s in self._students if s["id"] == stu_id), None)
        if not stu:
            self._show_err(ts("stu.err_notfound"))
            return

        test_id = self._tst_combo.currentData()
        if test_id is None:
            self._show_err(ts("stu.err_test"))
            return

        self._last_select = {"cls_id": cls_id, "stu_id": stu_id, "test_id": test_id}

        self._start_btn.setEnabled(False)
        self._start_btn.setText(ts("stu.loading_btn"))
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
        self._start_btn.setText(ts("stu.start_btn"))
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
    lbl.setStyleSheet("color: rgba(255,255,255,0.85); background: transparent;")
    row.addWidget(ico)
    row.addWidget(lbl)
    row.addStretch()
    return row
