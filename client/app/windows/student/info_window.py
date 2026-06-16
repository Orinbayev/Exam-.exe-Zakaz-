"""
O'quvchi — test boshlash oynasi.
Sinf tanlash → ism tanlash → test tanlash → boshlash.
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QPushButton, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QGuiApplication
from ...api_client import api, APIError


# ── Ranglar ───────────────────────────────────────────────────────────────────

BG1, BG2 = "#0D47A1", "#1976D2"
CARD_BG   = "rgba(255,255,255,0.10)"
CARD_BDR  = "rgba(255,255,255,0.20)"
INPUT_BG  = "rgba(255,255,255,0.12)"
INPUT_FOCUS = "rgba(255,255,255,0.20)"
BTN_BG    = "qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #FF6F00,stop:1 #FFA000)"
BTN_HV    = "qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #FFA000,stop:1 #FFD740)"

COMBO_STYLE = f"""
QComboBox {{
    background: {INPUT_BG};
    color: white;
    border: 1.5px solid rgba(255,255,255,0.22);
    border-radius: 12px;
    padding: 0 16px;
    font-size: 14px;
    font-family: 'Segoe UI', Arial;
    min-height: 52px;
}}
QComboBox:focus {{
    background: {INPUT_FOCUS};
    border: 2px solid rgba(255,255,255,0.60);
}}
QComboBox::drop-down {{
    border: none;
    width: 32px;
}}
QComboBox::down-arrow {{
    image: none;
    border-left: 6px solid transparent;
    border-right: 6px solid transparent;
    border-top: 7px solid rgba(255,255,255,0.75);
    margin-right: 12px;
}}
QComboBox QAbstractItemView {{
    background: #1565C0;
    color: white;
    selection-background-color: #0D47A1;
    border: none;
    font-size: 13px;
    padding: 4px;
}}
"""

START_STYLE = f"""
QPushButton {{
    background: {BTN_BG};
    color: white;
    border: none;
    border-radius: 14px;
    font-size: 17px;
    font-weight: 700;
    font-family: 'Segoe UI', Arial;
    min-height: 58px;
}}
QPushButton:hover  {{ background: {BTN_HV}; }}
QPushButton:disabled {{
    background: rgba(255,255,255,0.15);
    color: rgba(255,255,255,0.40);
}}
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
            r = api.start_exam(self._tid, self._first, self._last, self._cls)
            self.done.emit(r)
        except APIError as e:
            self.error.emit(str(e))


# ── Asosiy oyna ──────────────────────────────────────────────────────────────

class StudentInfoWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Smart Exam — Test Boshlash")
        self.setFixedSize(500, 660)
        self._thread = None
        self._classes: list = []
        self._students: list = []
        self._tests: list = []
        self._build_ui()
        self._center()
        self._load_initial()

    def _center(self):
        sc = QGuiApplication.primaryScreen().geometry()
        self.move(
            (sc.width()  - self.width())  // 2,
            (sc.height() - self.height()) // 2,
        )

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        # Gradient fon
        root_w = QWidget()
        root_w.setStyleSheet(f"""
            QWidget {{
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 {BG1}, stop:1 {BG2}
                );
            }}
        """)
        self.setCentralWidget(root_w)

        outer = QVBoxLayout(root_w)
        outer.setContentsMargins(32, 36, 32, 28)
        outer.setSpacing(0)

        # ── Header ───────────────────────────────────────────────────────────
        ico = QLabel("📝")
        ico.setFont(QFont("Segoe UI Emoji", 42))
        ico.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ico.setStyleSheet("background: transparent;")
        outer.addWidget(ico)

        ttl = QLabel("Test Boshlash")
        ttl.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        ttl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ttl.setStyleSheet("color: white; background: transparent;")
        outer.addWidget(ttl)
        outer.addSpacing(6)

        sub = QLabel("Quyidagi ma'lumotlarni to'ldiring")
        sub.setFont(QFont("Segoe UI", 11))
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet("color: rgba(255,255,255,0.60); background: transparent;")
        outer.addWidget(sub)
        outer.addSpacing(24)

        # ── Card ─────────────────────────────────────────────────────────────
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: {CARD_BG};
                border: 1.5px solid {CARD_BDR};
                border-radius: 22px;
            }}
        """)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(26, 26, 26, 26)
        cl.setSpacing(18)

        # 1) Sinf tanlang
        cl.addLayout(self._label_row("🏫", "Sinf tanlang"))
        self._cls_combo = QComboBox()
        self._cls_combo.setStyleSheet(COMBO_STYLE)
        self._cls_combo.addItem("⏳  Yuklanmoqda...", None)
        self._cls_combo.currentIndexChanged.connect(self._on_class_change)
        cl.addWidget(self._cls_combo)

        # 2) O'quvchini tanlang
        cl.addLayout(self._label_row("👤", "O'quvchini tanlang"))
        self._stu_combo = QComboBox()
        self._stu_combo.setStyleSheet(COMBO_STYLE)
        self._stu_combo.addItem("— Avval sinfni tanlang —", None)
        cl.addWidget(self._stu_combo)

        # 3) Test tanlang
        cl.addLayout(self._label_row("📋", "Test tanlang"))
        self._tst_combo = QComboBox()
        self._tst_combo.setStyleSheet(COMBO_STYLE)
        self._tst_combo.addItem("⏳  Yuklanmoqda...", None)
        cl.addWidget(self._tst_combo)

        # Xato banner
        self._err_lbl = QLabel("")
        self._err_lbl.setStyleSheet(
            "color: #FF8A65; font-size: 12px;"
            " background: rgba(239,83,80,0.12);"
            " border: 1px solid rgba(239,83,80,0.30);"
            " border-radius: 8px; padding: 8px 12px;"
        )
        self._err_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._err_lbl.setWordWrap(True)
        self._err_lbl.hide()
        cl.addWidget(self._err_lbl)

        outer.addWidget(card, stretch=1)
        outer.addSpacing(20)

        # ── Start button ─────────────────────────────────────────────────────
        self._start_btn = QPushButton("🚀   Testni Boshlash")
        self._start_btn.setStyleSheet(START_STYLE)
        self._start_btn.clicked.connect(self._start)
        outer.addWidget(self._start_btn)

    @staticmethod
    def _label_row(icon: str, text: str) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(8)
        ico = QLabel(icon)
        ico.setFont(QFont("Segoe UI Emoji", 13))
        ico.setStyleSheet("background: transparent; color: white;")
        lbl = QLabel(text)
        lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        lbl.setStyleSheet("color: rgba(255,255,255,0.80); background: transparent;")
        row.addWidget(ico)
        row.addWidget(lbl)
        row.addStretch()
        return row

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
        except APIError as e:
            self._cls_combo.clear()
            self._cls_combo.addItem("— Serverga ulanib bo'lmadi —", None)
            self._show_err(f"Server xatosi: {e}")

    def _on_class_change(self):
        cls_id = self._cls_combo.currentData()
        self._stu_combo.clear()
        self._tst_combo.clear()
        self._students = []
        self._tests = []

        if cls_id is None:
            self._stu_combo.addItem("— Avval sinfni tanlang —", None)
            self._tst_combo.addItem("— Avval sinfni tanlang —", None)
            self._start_btn.setEnabled(False)
            return

        # Load students
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

        # Load tests for this class
        try:
            self._tests = api.get_class_tests_public(cls_id)
            if not self._tests:
                self._tst_combo.addItem("— Bu sinfga test biriktirilmagan —", None)
                self._start_btn.setEnabled(False)
            else:
                self._start_btn.setEnabled(True)
                for t in self._tests:
                    q = t.get("question_count", 0)
                    self._tst_combo.addItem(f"{t['name']}  ({q} savol · {t['time_limit']} daq)", t["id"])
        except APIError:
            self._tst_combo.addItem("— Testlar yuklanmadi —", None)
            self._start_btn.setEnabled(False)

    # ── Start ─────────────────────────────────────────────────────────────────

    def _start(self):
        # Sinf
        cls_id   = self._cls_combo.currentData()
        cls_name = self._cls_combo.currentText().strip()
        if cls_id is None:
            self._show_err("⚠  Avval sinfni tanlang!")
            return

        # O'quvchi
        stu_id = self._stu_combo.currentData()
        if stu_id is None:
            self._show_err("⚠  O'quvchini tanlang!")
            return

        stu = next((s for s in self._students if s["id"] == stu_id), None)
        if not stu:
            self._show_err("⚠  O'quvchi topilmadi!")
            return

        # Test
        test_id = self._tst_combo.currentData()
        if test_id is None:
            self._show_err("⚠  Testni tanlang!")
            return

        first = stu["first_name"]
        last  = stu["last_name"]

        self._start_btn.setEnabled(False)
        self._start_btn.setText("⏳   Yuklanmoqda...")
        self._err_lbl.hide()

        self._thread = _StartThread(test_id, first, last, cls_name)
        self._thread.done.connect(self._on_started)
        self._thread.error.connect(self._on_error)
        self._thread.start()

    def _on_started(self, data: dict):
        from .exam_window import ExamWindow
        self._exam = ExamWindow(data)
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
