"""
O'quvchi ma'lumotlari kiritish oynasi - tozalangan, aniq layout.
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QComboBox, QMessageBox, QFrame,
    QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor, QGuiApplication
from ...api_client import api, APIError


# ── Ranglar ───────────────────────────────────────────────────────────────────
BG_GRAD   = "qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #0D47A1,stop:1 #1976D2)"
CARD_BG   = "rgba(255,255,255,0.10)"
CARD_BORDER = "rgba(255,255,255,0.22)"
INPUT_BG  = "rgba(255,255,255,0.13)"
INPUT_FOCUS = "rgba(255,255,255,0.22)"
BTN_GRAD  = "qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #FF6F00,stop:1 #FFA000)"
BTN_HOVER = "qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #FFA000,stop:1 #FFD740)"

WINDOW_STYLE = f"""
QMainWindow, QWidget#root {{
    background: {BG_GRAD};
}}
"""

LABEL_STYLE   = "color: rgba(255,255,255,0.80); font-size: 12px; font-weight: 600; background: transparent;"
VALUE_LABEL   = "color: white; font-size: 21px; font-weight: 800; background: transparent;"
SUBLABEL_STYLE= "color: rgba(255,255,255,0.60); font-size: 11px; background: transparent;"

INPUT_STYLE = f"""
QLineEdit, QComboBox {{
    background: {INPUT_BG};
    color: white;
    border: 1.5px solid rgba(255,255,255,0.25);
    border-radius: 10px;
    padding: 0px 14px;
    font-size: 14px;
    font-family: 'Segoe UI', Arial;
}}
QLineEdit:focus {{
    background: {INPUT_FOCUS};
    border: 2px solid rgba(255,255,255,0.70);
}}
QComboBox::drop-down {{ border: none; width: 28px; }}
QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid rgba(255,255,255,0.7);
    margin-right: 10px;
}}
QComboBox QAbstractItemView {{
    background: #1565C0;
    color: white;
    selection-background-color: #0D47A1;
    border: none;
    font-size: 13px;
}}
"""

START_BTN_STYLE = f"""
QPushButton {{
    background: {BTN_GRAD};
    color: white;
    border: none;
    border-radius: 12px;
    font-size: 16px;
    font-weight: 700;
    font-family: 'Segoe UI', Arial;
}}
QPushButton:hover {{ background: {BTN_HOVER}; }}
QPushButton:disabled {{ background: rgba(255,255,255,0.18); color: rgba(255,255,255,0.40); }}
"""

BACK_BTN_STYLE = """
QPushButton {
    background: rgba(255,255,255,0.10);
    color: rgba(255,255,255,0.75);
    border: 1.5px solid rgba(255,255,255,0.22);
    border-radius: 10px;
    font-size: 13px;
    font-family: 'Segoe UI', Arial;
}
QPushButton:hover { background: rgba(255,255,255,0.18); color: white; }
"""


class LoadThread(QThread):
    done = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, test_id, name, lastname, cls):
        super().__init__()
        self.test_id, self.name, self.lastname, self.cls = test_id, name, lastname, cls

    def run(self):
        try:
            r = api.start_exam(self.test_id, self.name, self.lastname, self.cls)
            self.done.emit(r)
        except APIError as e:
            self.error.emit(str(e))


def _field_block(parent_layout, label_text: str, widget, fixed_height=46):
    """Label + widget qo'shuvchi yordamchi."""
    lbl = QLabel(label_text)
    lbl.setStyleSheet(LABEL_STYLE)
    lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
    widget.setFixedHeight(fixed_height)
    parent_layout.addWidget(lbl)
    parent_layout.addSpacing(3)
    parent_layout.addWidget(widget)
    parent_layout.addSpacing(10)


class StudentInfoWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Smart Exam – Test boshlash")
        self.setFixedSize(480, 680)
        self._thread = None
        self.tests = []
        self.classes = []
        self.students = []
        self._setup_ui()
        self._center()
        self._load_data()

    def _center(self):
        sc = QGuiApplication.primaryScreen().geometry()
        self.move((sc.width()-self.width())//2, (sc.height()-self.height())//2)

    # ── UI ─────────────────────────────────────────────────────────────────────

    def _setup_ui(self):
        self.setStyleSheet(WINDOW_STYLE)

        root = QWidget(objectName="root")
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── Header ─────────────────────────────────────────────────────────────
        header = QWidget()
        header.setStyleSheet("background: transparent;")
        header.setFixedHeight(140)
        hlay = QVBoxLayout(header)
        hlay.setContentsMargins(0, 22, 0, 10)
        hlay.setSpacing(4)
        hlay.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        ico = QLabel("📝")
        ico.setFont(QFont("Segoe UI Emoji", 36))
        ico.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ico.setStyleSheet("background: transparent;")

        title = QLabel("Test Boshlash")
        title.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: white; background: transparent;")

        sub = QLabel("Quyidagi maydonlarni to'ldiring")
        sub.setFont(QFont("Segoe UI", 11))
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet("color: rgba(255,255,255,0.65); background: transparent;")

        hlay.addWidget(ico)
        hlay.addWidget(title)
        hlay.addWidget(sub)
        outer.addWidget(header)

        # ── Card ───────────────────────────────────────────────────────────────
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: {CARD_BG};
                border-radius: 20px;
                border: 1.5px solid {CARD_BORDER};
            }}
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(28, 22, 28, 22)
        card_layout.setSpacing(0)

        # Sinf tanlash
        self.class_combo = QComboBox()
        self.class_combo.setStyleSheet(INPUT_STYLE)
        self.class_combo.addItem("⏳ Yuklanmoqda...", None)
        self.class_combo.currentIndexChanged.connect(self._on_class_changed)
        _field_block(card_layout, "🏫  Sinf tanlang", self.class_combo)

        # O'quvchi tanlash
        self.student_combo = QComboBox()
        self.student_combo.setStyleSheet(INPUT_STYLE)
        self.student_combo.addItem("— Avval sinfni tanlang —", None)
        self.student_combo.currentIndexChanged.connect(self._on_student_changed)
        _field_block(card_layout, "👤  O'quvchini tanlang", self.student_combo)

        # Qo'lda kiritish (agar ro'yxatda yo'q bo'lsa)
        self.manual_frame = QFrame()
        self.manual_frame.setStyleSheet("QFrame { background: transparent; border: none; }")
        mlay = QVBoxLayout(self.manual_frame)
        mlay.setContentsMargins(0, 0, 0, 0)
        mlay.setSpacing(0)

        manual_label = QLabel("— yoki qo'lda kiriting —")
        manual_label.setStyleSheet("color: rgba(255,255,255,0.50); font-size: 11px; background: transparent;")
        manual_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mlay.addWidget(manual_label)
        mlay.addSpacing(8)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Ism")
        self.name_input.setStyleSheet(INPUT_STYLE)
        _field_block(mlay, "✏️  Ism", self.name_input)

        self.lastname_input = QLineEdit()
        self.lastname_input.setPlaceholderText("Familiya")
        self.lastname_input.setStyleSheet(INPUT_STYLE)
        _field_block(mlay, "✏️  Familiya", self.lastname_input)

        card_layout.addWidget(self.manual_frame)

        # Test tanlash
        self.test_combo = QComboBox()
        self.test_combo.setStyleSheet(INPUT_STYLE)
        self.test_combo.addItem("⏳ Yuklanmoqda...", None)
        _field_block(card_layout, "📋  Test tanlang", self.test_combo)

        # Xato labeli
        self.err_label = QLabel("")
        self.err_label.setStyleSheet("color: #FF8A65; font-size: 12px; background: transparent;")
        self.err_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.err_label.setWordWrap(True)
        self.err_label.setFixedHeight(28)
        card_layout.addWidget(self.err_label)

        outer.addWidget(card, stretch=1, alignment=Qt.AlignmentFlag.AlignHCenter |
                         Qt.AlignmentFlag.AlignVCenter)
        outer.setContentsMargins(24, 0, 24, 0)

        # ── Tugmalar ───────────────────────────────────────────────────────────
        btn_area = QWidget()
        btn_area.setStyleSheet("background: transparent;")
        btn_area.setFixedHeight(90)
        blay = QVBoxLayout(btn_area)
        blay.setContentsMargins(24, 10, 24, 16)
        blay.setSpacing(8)

        self.start_btn = QPushButton("🚀   Testni Boshlash")
        self.start_btn.setFixedHeight(52)
        self.start_btn.setStyleSheet(START_BTN_STYLE)
        self.start_btn.clicked.connect(self._start)
        blay.addWidget(self.start_btn)

        outer.addWidget(btn_area)

    # ── Data loading ───────────────────────────────────────────────────────────

    def _load_data(self):
        try:
            self.tests = api.get_public_tests()
            self.test_combo.clear()
            if not self.tests:
                self.test_combo.addItem("Hech qanday test mavjud emas", None)
                self.start_btn.setEnabled(False)
            else:
                for t in self.tests:
                    label = f"{t['name']}  ({t.get('question_count',0)} savol · {t['time_limit']} daq)"
                    self.test_combo.addItem(label, t["id"])
        except APIError as e:
            self.err_label.setText(f"Testlar yuklanmadi: {e}")

        try:
            self.classes = api.get_classes()
            self.class_combo.clear()
            self.class_combo.addItem("— Sinfni tanlang —", None)
            for c in self.classes:
                self.class_combo.addItem(c["name"], c["id"])
        except APIError:
            self.class_combo.clear()
            self.class_combo.addItem("— Sinf yo'q (qo'lda kiriting) —", None)

    def _on_class_changed(self):
        class_id = self.class_combo.currentData()
        self.student_combo.clear()
        self.students = []
        if class_id is None:
            self.student_combo.addItem("— Avval sinfni tanlang —", None)
            return
        try:
            self.students = api.get_students_public(class_id)
            self.student_combo.addItem("— O'quvchini tanlang —", None)
            for s in self.students:
                self.student_combo.addItem(
                    f"{s['last_name']} {s['first_name']}",
                    {"first": s["first_name"], "last": s["last_name"]}
                )
            if not self.students:
                self.student_combo.addItem("(Bu sinfda o'quvchi yo'q)", None)
        except APIError:
            self.student_combo.addItem("— Yuklanmadi —", None)

    def _on_student_changed(self):
        data = self.student_combo.currentData()
        if isinstance(data, dict):
            self.name_input.setText(data["first"])
            self.lastname_input.setText(data["last"])

    # ── Start ──────────────────────────────────────────────────────────────────

    def _start(self):
        name    = self.name_input.text().strip()
        lastname= self.lastname_input.text().strip()
        cls_name= self.class_combo.currentText().strip()
        test_id = self.test_combo.currentData()

        # Class combo text tozalash
        if cls_name.startswith("—") or not self.class_combo.currentData():
            cls_name = ""

        if not name:
            self._err("⚠  Ism kiriting!"); return
        if not lastname:
            self._err("⚠  Familiya kiriting!"); return
        if not test_id:
            self._err("⚠  Test tanlanmagan!"); return
        if not cls_name:
            cls_name = "Noma'lum sinf"

        self.start_btn.setEnabled(False)
        self.start_btn.setText("⏳  Yuklanmoqda...")
        self.err_label.setText("")

        self._thread = LoadThread(test_id, name, lastname, cls_name)
        self._thread.done.connect(self._on_started)
        self._thread.error.connect(self._on_error)
        self._thread.start()

    def _on_started(self, data):
        from .exam_window import ExamWindow
        self._exam = ExamWindow(data)
        self._exam.show()
        self.close()

    def _on_error(self, msg):
        self.start_btn.setEnabled(True)
        self.start_btn.setText("🚀   Testni Boshlash")
        self._err(msg)

    def _err(self, msg):
        self.err_label.setText(msg)
        QTimer.singleShot(4000, lambda: self.err_label.setText(""))
