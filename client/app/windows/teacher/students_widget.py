"""
Sinflar va O'quvchilar boshqaruvi — professional dizayn.
"""
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QTableWidget, QTableWidgetItem,
    QDialog, QLineEdit, QMessageBox,
    QHeaderView, QFrame, QFileDialog,
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QColor
from ...api_client import api, APIError
from ...styles import COLORS


# ─────────────────────────────────────────────────────────────────────────────
# Yordamchi: zamonaviy dialog bazasi
# ─────────────────────────────────────────────────────────────────────────────

_DLG_STYLE = f"""
QDialog {{
    background-color: {COLORS['bg_medium']};
    color: white;
    font-family: 'Segoe UI', Arial;
}}
QLabel  {{ color: white; background: transparent; }}
QLineEdit {{
    background: {COLORS['bg_dark']};
    color: white;
    border: 1.5px solid {COLORS['border']};
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 13px;
    min-height: 36px;
}}
QLineEdit:focus {{
    border: 2px solid {COLORS['primary_light']};
}}
QPushButton {{
    background: {COLORS['primary']};
    color: white;
    border: none;
    border-radius: 8px;
    padding: 9px 22px;
    font-size: 13px;
    font-weight: bold;
    min-height: 36px;
}}
QPushButton:hover  {{ background: {COLORS['primary_light']}; }}
QPushButton#cancel {{
    background: {COLORS['bg_light']};
    border: 1px solid {COLORS['border']};
}}
QPushButton#cancel:hover {{ background: {COLORS['bg_dark']}; }}
"""


# ─────────────────────────────────────────────────────────────────────────────
# Sinf qo'shish dialogi
# ─────────────────────────────────────────────────────────────────────────────

class ClassDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Yangi sinf qo'shish")
        self.setFixedSize(380, 200)
        self.setStyleSheet(_DLG_STYLE)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 24, 28, 24)
        lay.setSpacing(16)

        ico = QLabel("🏫")
        ico.setFont(QFont("Segoe UI Emoji", 28))
        ico.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(ico)

        lbl = QLabel("Sinf nomini kiriting:")
        lbl.setFont(QFont("Segoe UI", 11))
        lay.addWidget(lbl)

        self.inp = QLineEdit()
        self.inp.setPlaceholderText("Masalan:  9-A   yoki   11-B")
        self.inp.returnPressed.connect(self._ok)
        lay.addWidget(self.inp)

        row = QHBoxLayout()
        row.setSpacing(10)
        ok_btn = QPushButton("✅  Saqlash")
        ok_btn.clicked.connect(self._ok)
        cl_btn = QPushButton("Bekor qilish")
        cl_btn.setObjectName("cancel")
        cl_btn.clicked.connect(self.reject)
        row.addWidget(cl_btn)
        row.addWidget(ok_btn)
        lay.addLayout(row)

    def _ok(self):
        if not self.inp.text().strip():
            self.inp.setPlaceholderText("⚠  Sinf nomini kiriting!")
            self.inp.setStyleSheet(self.inp.styleSheet() +
                                   "border: 2px solid #EF5350;")
            return
        self.accept()

    def get_name(self): return self.inp.text().strip()


# ─────────────────────────────────────────────────────────────────────────────
# O'quvchi qo'shish / tahrirlash dialogi
# ─────────────────────────────────────────────────────────────────────────────

class StudentDialog(QDialog):
    def __init__(self, student=None, parent=None):
        super().__init__(parent)
        self.student = student
        self.setWindowTitle(
            "O'quvchi qo'shish" if not student else "O'quvchini tahrirlash"
        )
        self.setFixedSize(440, 370)
        self.setStyleSheet(_DLG_STYLE)
        self._build()
        if student:
            self.f_inp.setText(student.get("first_name", ""))
            self.l_inp.setText(student.get("last_name", ""))
            self.tg_inp.setText(student.get("parent_telegram_id") or "")

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 20, 28, 20)
        lay.setSpacing(14)

        ico = QLabel("🎒" if not self.student else "✏️")
        ico.setFont(QFont("Segoe UI Emoji", 26))
        ico.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(ico)

        def _row(label, placeholder, echo=None):
            lbl = QLabel(label)
            lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
            lbl.setStyleSheet(f"color: {COLORS['text_secondary']};")
            inp = QLineEdit()
            inp.setPlaceholderText(placeholder)
            if echo:
                inp.setEchoMode(echo)
            lay.addWidget(lbl)
            lay.addWidget(inp)
            return inp

        self.l_inp = _row("Familiya *", "O'quvchi familiyasi")
        self.f_inp = _row("Ism *", "O'quvchi ismi")
        self.tg_inp = _row(
            "Ota-ona Telegram Chat ID  (ixtiyoriy)",
            "Masalan: 123456789"
        )

        # Telegram yordam matni
        help_card = QFrame()
        help_card.setStyleSheet(f"""
            QFrame {{
                background: rgba(66,165,245,0.12);
                border: 1px solid rgba(66,165,245,0.30);
                border-radius: 8px;
            }}
        """)
        hlay = QHBoxLayout(help_card)
        hlay.setContentsMargins(10, 8, 10, 8)
        help_lbl = QLabel(
            "ℹ️  Chat ID ni topish:  Telegramda <b>@userinfobot</b> ga /start yuboring"
        )
        help_lbl.setFont(QFont("Segoe UI", 10))
        help_lbl.setStyleSheet(f"color: {COLORS['primary_light']}; background: transparent;")
        help_lbl.setWordWrap(True)
        hlay.addWidget(help_lbl)
        lay.addWidget(help_card)

        row = QHBoxLayout()
        row.setSpacing(10)
        cl = QPushButton("Bekor qilish")
        cl.setObjectName("cancel")
        cl.clicked.connect(self.reject)
        ok = QPushButton("✅  Saqlash")
        ok.clicked.connect(self._ok)
        row.addWidget(cl)
        row.addWidget(ok)
        lay.addLayout(row)

    def _ok(self):
        if not self.f_inp.text().strip():
            QMessageBox.warning(self, "⚠", "Ism bo'sh bo'lishi mumkin emas!")
            return
        if not self.l_inp.text().strip():
            QMessageBox.warning(self, "⚠", "Familiya bo'sh bo'lishi mumkin emas!")
            return
        self.accept()

    def get_data(self):
        return {
            "first_name": self.f_inp.text().strip(),
            "last_name":  self.l_inp.text().strip(),
            "parent_telegram_id": self.tg_inp.text().strip() or None,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Excel format ko'rsatish dialogi
# ─────────────────────────────────────────────────────────────────────────────

class ExcelFormatDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Excel import formati")
        self.setFixedSize(580, 460)
        self.setStyleSheet(_DLG_STYLE)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 20, 28, 20)
        lay.setSpacing(14)

        title = QLabel("📊  O'quvchilar Excel import formati")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(title)

        # Ustunlar tavsifi
        cols_card = QFrame()
        cols_card.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['bg_dark']};
                border: 1px solid {COLORS['border']};
                border-radius: 10px;
            }}
        """)
        clay = QVBoxLayout(cols_card)
        clay.setContentsMargins(16, 14, 16, 14)
        clay.setSpacing(8)

        hdr = QLabel("Ustunlar tartibi:")
        hdr.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        hdr.setStyleSheet(f"color: {COLORS['primary_light']};")
        clay.addWidget(hdr)

        cols_info = [
            ("A ustun", "Ism",                       "Majburiy",   "#66BB6A"),
            ("B ustun", "Familiya",                   "Majburiy",   "#66BB6A"),
            ("C ustun", "Ota-ona Telegram Chat ID",   "Ixtiyoriy",  "#FFA726"),
        ]
        for col, desc, req, color in cols_info:
            row_w = QWidget()
            row_w.setStyleSheet("background: transparent;")
            rlay = QHBoxLayout(row_w)
            rlay.setContentsMargins(0, 0, 0, 0)
            rlay.setSpacing(10)

            col_lbl = QLabel(col)
            col_lbl.setFixedWidth(72)
            col_lbl.setFont(QFont("Consolas", 11, QFont.Weight.Bold))
            col_lbl.setStyleSheet(f"color: #FFD740; background: transparent;")

            desc_lbl = QLabel(desc)
            desc_lbl.setFont(QFont("Segoe UI", 11))
            desc_lbl.setStyleSheet("background: transparent;")

            req_lbl = QLabel(req)
            req_lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            req_lbl.setStyleSheet(f"color: {color}; background: transparent;")
            req_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)

            rlay.addWidget(col_lbl)
            rlay.addWidget(desc_lbl, stretch=1)
            rlay.addWidget(req_lbl)
            clay.addWidget(row_w)

        lay.addWidget(cols_card)

        # Namuna jadval
        ex_lbl = QLabel("Namuna ko'rinish:")
        ex_lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        ex_lbl.setStyleSheet(f"color: {COLORS['text_secondary']};")
        lay.addWidget(ex_lbl)

        tbl = QTableWidget(4, 3)
        tbl.setHorizontalHeaderLabels(["A — Ism", "B — Familiya", "C — Telegram ID"])
        tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        tbl.verticalHeader().setVisible(False)
        tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        tbl.setFixedHeight(138)
        tbl.setStyleSheet(f"""
            QTableWidget {{
                background: {COLORS['bg_dark']};
                color: white;
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                gridline-color: {COLORS['border']};
                font-size: 12px;
            }}
            QHeaderView::section {{
                background: {COLORS['bg_light']};
                color: {COLORS['text_secondary']};
                padding: 6px;
                border: none;
                font-size: 11px;
                font-weight: bold;
            }}
            QTableWidget::item {{ padding: 6px 10px; }}
        """)

        sample_data = [
            ["Alisher",  "Navoiy",   "123456789"],
            ["Nodira",   "Karimova", "987654321"],
            ["Jasur",    "Toshmatov",""],
            ["Malika",   "Yusupova", "456123789"],
        ]
        colors_row = ["rgba(255,255,255,0.06)", "transparent"]
        for r, row in enumerate(sample_data):
            for c, val in enumerate(row):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if c == 2 and val:
                    item.setForeground(QColor("#FFA726"))
                tbl.setItem(r, c, item)
        lay.addWidget(tbl)

        # Eslatma
        note = QLabel(
            "⚠️  1-qator sarlavha sifatida o'tkazib yuboriladi.  "
            "C ustun bo'sh bo'lsa ham bo'ladi — Telegram xabar yuborilmaydi."
        )
        note.setFont(QFont("Segoe UI", 10))
        note.setStyleSheet(f"color: {COLORS['accent_light']}; background: transparent;")
        note.setWordWrap(True)
        lay.addWidget(note)

        # Tugmalar
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        dl_btn = QPushButton("📥  Namuna Excel yuklab olish")
        dl_btn.clicked.connect(self._download)
        cl_btn = QPushButton("Yopish")
        cl_btn.setObjectName("cancel")
        cl_btn.clicked.connect(self.accept)
        btn_row.addWidget(dl_btn)
        btn_row.addWidget(cl_btn)
        lay.addLayout(btn_row)

    def _download(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Namuna faylni saqlash",
            "oquvchilar_namuna.xlsx", "Excel (*.xlsx)"
        )
        if not path:
            return
        _generate_student_template(path)
        QMessageBox.information(
            self, "✅ Saqlandi",
            f"Namuna fayl saqlandi:\n{path}\n\n"
            "Sariq qatorlardagi ma'lumotlarni o'chirib,\n"
            "o'z o'quvchilaringizni kiriting."
        )
        if os.name == "nt":
            os.startfile(path)


def _generate_student_template(path: str):
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "O'quvchilar"

    BLU = PatternFill("solid", fgColor="1565C0")
    YEL = PatternFill("solid", fgColor="FFF9C4")
    HDR = Font(bold=True, color="FFFFFF", size=11)
    BRD = Border(*(Side(style="thin"),)*4)
    CTR = Alignment(horizontal="center", vertical="center")

    headers = [("Ism (A)", 20), ("Familiya (B)", 22), ("Ota-ona Telegram ID (C)", 28)]
    for c, (h, w) in enumerate(headers, 1):
        cell = ws.cell(1, c, h)
        cell.font, cell.fill, cell.alignment, cell.border = HDR, BLU, CTR, BRD
        ws.column_dimensions[get_column_letter(c)].width = w
    ws.row_dimensions[1].height = 26

    samples = [
        ["Alisher",  "Navoiy",    "123456789"],
        ["Nodira",   "Karimova",  "987654321"],
        ["Jasur",    "Toshmatov", ""],
        ["Malika",   "Yusupova",  "456123789"],
        ["Sanjar",   "Ergashev",  ""],
    ]
    for r, row in enumerate(samples, 2):
        for c, val in enumerate(row, 1):
            cell = ws.cell(r, c, val)
            cell.fill, cell.border = YEL, BRD
            cell.alignment = Alignment(horizontal="left", vertical="center")
        ws.row_dimensions[r].height = 22

    ws.cell(len(samples)+3, 1).value = (
        "ESLATMA: 1-qatorni o'zgartirmang (sarlavha). "
        "2-qatordan boshlab o'z o'quvchilaringizni kiriting. "
        "Telegram ID ixtiyoriy — bo'sh qoldirsangiz ham bo'ladi."
    )
    ws.cell(len(samples)+3, 1).font = Font(italic=True, color="888888", size=9)
    ws.freeze_panes = "A2"
    wb.save(path)


# ─────────────────────────────────────────────────────────────────────────────
# Asosiy widget
# ─────────────────────────────────────────────────────────────────────────────

_PANEL_STYLE = f"""
    QFrame {{
        background: {COLORS['bg_medium']};
        border: 1px solid {COLORS['border']};
        border-radius: 12px;
    }}
"""

_LIST_STYLE = f"""
    QListWidget {{
        background: {COLORS['bg_dark']};
        border: 1px solid {COLORS['border']};
        border-radius: 8px;
        color: white;
        font-size: 13px;
        outline: none;
    }}
    QListWidget::item {{
        padding: 10px 14px;
        border-bottom: 1px solid {COLORS['border']};
    }}
    QListWidget::item:selected {{
        background: {COLORS['primary']};
        color: white;
        border-radius: 6px;
    }}
    QListWidget::item:hover:!selected {{
        background: {COLORS['bg_light']};
    }}
"""

_TABLE_STYLE = f"""
    QTableWidget {{
        background: {COLORS['bg_dark']};
        color: white;
        border: 1px solid {COLORS['border']};
        border-radius: 8px;
        gridline-color: {COLORS['border']};
        font-size: 13px;
        outline: none;
    }}
    QTableWidget::item {{
        padding: 8px 12px;
    }}
    QTableWidget::item:selected {{
        background: {COLORS['primary']};
        color: white;
    }}
    QHeaderView::section {{
        background: {COLORS['bg_light']};
        color: {COLORS['text_secondary']};
        padding: 10px 12px;
        border: none;
        border-right: 1px solid {COLORS['border']};
        border-bottom: 1px solid {COLORS['border']};
        font-weight: bold;
        font-size: 12px;
    }}
"""

def _icon_btn(icon: str, tip: str, obj: str = "", size=32) -> QPushButton:
    btn = QPushButton(icon)
    btn.setFixedSize(size, size)
    btn.setToolTip(tip)
    if obj:
        btn.setObjectName(obj)
    btn.setStyleSheet(f"""
        QPushButton {{
            background: {'#C62828' if obj=='danger' else COLORS['bg_light']};
            color: white;
            border: 1px solid {COLORS['border']};
            border-radius: 7px;
            font-size: 14px;
        }}
        QPushButton:hover {{
            background: {'#EF5350' if obj=='danger' else COLORS['primary']};
            border-color: {'#EF5350' if obj=='danger' else COLORS['primary']};
        }}
    """)
    return btn


class StudentsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.classes   = []
        self.students  = []
        self._cls_id   = None
        self._cls_name = ""
        self._setup_ui()
        self.refresh()

    # ── UI qurilishi ──────────────────────────────────────────────────────────

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(14)

        # ── Sarlavha ──────────────────────────────────────────────────────────
        hdr = QHBoxLayout()
        title = QLabel("👥  Sinflar va O'quvchilar")
        title.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        hdr.addWidget(title)
        hdr.addStretch()
        fmt_btn = QPushButton("📊  Excel format ko'rsatish")
        fmt_btn.setObjectName("secondary")
        fmt_btn.clicked.connect(self._show_format)
        hdr.addWidget(fmt_btn)
        root.addLayout(hdr)

        # Qisqacha yo'riqnoma
        hint = QFrame()
        hint.setStyleSheet(f"""
            QFrame {{
                background: rgba(21,101,192,0.15);
                border: 1px solid rgba(66,165,245,0.30);
                border-radius: 8px;
            }}
        """)
        hlay = QHBoxLayout(hint)
        hlay.setContentsMargins(14, 10, 14, 10)
        hint_lbl = QLabel(
            "💡  <b>Qanday ishlaydi:</b>  "
            "1) Chapdan sinf tanlang  →  "
            "2) O'quvchi qo'shing  →  "
            "3) Ota-ona Telegram ID kiriting  →  "
            "Test natijasi avtomatik yuboriladi"
        )
        hint_lbl.setFont(QFont("Segoe UI", 11))
        hint_lbl.setStyleSheet(f"color: {COLORS['primary_light']}; background: transparent;")
        hint_lbl.setWordWrap(True)
        hlay.addWidget(hint_lbl)
        root.addWidget(hint)

        # ── Asosiy panel (chap + o'ng) ────────────────────────────────────────
        panels = QHBoxLayout()
        panels.setSpacing(14)

        # ── CHAP: Sinflar ─────────────────────────────────────────────────────
        left = QFrame()
        left.setStyleSheet(_PANEL_STYLE)
        left.setFixedWidth(240)
        ll = QVBoxLayout(left)
        ll.setContentsMargins(12, 14, 12, 14)
        ll.setSpacing(10)

        l_hdr = QHBoxLayout()
        l_title = QLabel("📚  Sinflar")
        l_title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        l_hdr.addWidget(l_title)
        self.cls_count_lbl = QLabel("0 ta")
        self.cls_count_lbl.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px;")
        l_hdr.addStretch()
        l_hdr.addWidget(self.cls_count_lbl)
        ll.addLayout(l_hdr)

        self.class_list = QListWidget()
        self.class_list.setStyleSheet(_LIST_STYLE)
        self.class_list.setAlternatingRowColors(False)
        self.class_list.currentItemChanged.connect(self._on_class_selected)
        ll.addWidget(self.class_list)

        add_cls_btn = QPushButton("＋  Sinf qo'shish")
        add_cls_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['success']};
                color: white; border: none; border-radius: 8px;
                padding: 10px; font-size: 13px; font-weight: bold;
            }}
            QPushButton:hover {{ background: {COLORS['success_light']}; }}
        """)
        add_cls_btn.clicked.connect(self._add_class)
        ll.addWidget(add_cls_btn)

        del_cls_btn = QPushButton("🗑  Sinf o'chirish")
        del_cls_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['bg_dark']};
                color: {COLORS['danger_light']};
                border: 1px solid {COLORS['danger']};
                border-radius: 8px; padding: 8px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background: {COLORS['danger']};
                color: white;
            }}
        """)
        del_cls_btn.clicked.connect(self._delete_class)
        ll.addWidget(del_cls_btn)

        panels.addWidget(left)

        # ── O'NG: O'quvchilar ─────────────────────────────────────────────────
        right = QFrame()
        right.setStyleSheet(_PANEL_STYLE)
        rl = QVBoxLayout(right)
        rl.setContentsMargins(14, 14, 14, 14)
        rl.setSpacing(10)

        # O'ng sarlavha
        r_hdr = QHBoxLayout()
        self.students_title = QLabel("👤  O'quvchilar")
        self.students_title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        r_hdr.addWidget(self.students_title)
        r_hdr.addStretch()
        self.st_count_lbl = QLabel("")
        self.st_count_lbl.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px;")
        r_hdr.addWidget(self.st_count_lbl)
        rl.addLayout(r_hdr)

        # Bo'sh holat labeli
        self.empty_lbl = QLabel(
            "⬅  Chapdan sinf tanlang\nSo'ng o'quvchi qo'shing"
        )
        self.empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_lbl.setStyleSheet(f"""
            color: {COLORS['text_secondary']};
            font-size: 14px;
            background: transparent;
        """)

        # Jadval
        self.tbl = QTableWidget()
        self.tbl.setColumnCount(4)
        self.tbl.setHorizontalHeaderLabels(
            ["Familiya", "Ism", "Ota-ona Telegram ID", "Amallar"]
        )
        self.tbl.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tbl.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tbl.setColumnWidth(2, 200)
        self.tbl.setColumnWidth(3, 90)
        self.tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tbl.verticalHeader().setVisible(False)
        self.tbl.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tbl.setAlternatingRowColors(True)
        self.tbl.setStyleSheet(_TABLE_STYLE + """
            QTableWidget { alternate-background-color: rgba(255,255,255,0.03); }
        """)
        self.tbl.hide()

        rl.addWidget(self.empty_lbl, stretch=1)
        rl.addWidget(self.tbl, stretch=1)

        # Tugmalar qatori
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self.add_st_btn = QPushButton("＋  O'quvchi qo'shish")
        self.add_st_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['success']};
                color: white; border: none; border-radius: 8px;
                padding: 9px 16px; font-size: 13px; font-weight: bold;
            }}
            QPushButton:hover {{ background: {COLORS['success_light']}; }}
            QPushButton:disabled {{ background: {COLORS['bg_light']}; color: {COLORS['text_secondary']}; }}
        """)
        self.add_st_btn.setEnabled(False)
        self.add_st_btn.clicked.connect(self._add_student)

        self.fmt_xl_btn = QPushButton("📋  Namuna Excel")
        self.fmt_xl_btn.setObjectName("secondary")
        self.fmt_xl_btn.clicked.connect(self._show_format)

        self.imp_xl_btn = QPushButton("📥  Excel import")
        self.imp_xl_btn.setObjectName("secondary")
        self.imp_xl_btn.setEnabled(False)
        self.imp_xl_btn.clicked.connect(self._import_excel)

        btn_row.addWidget(self.add_st_btn)
        btn_row.addStretch()
        btn_row.addWidget(self.fmt_xl_btn)
        btn_row.addWidget(self.imp_xl_btn)
        rl.addLayout(btn_row)

        panels.addWidget(right, stretch=1)
        root.addLayout(panels, stretch=1)

    # ── Ma'lumot yuklash ──────────────────────────────────────────────────────

    def refresh(self):
        try:
            self.classes = api.get_classes()
        except APIError:
            self.classes = []

        self.class_list.blockSignals(True)
        self.class_list.clear()
        for c in self.classes:
            n = c.get("student_count", 0)
            item = QListWidgetItem(f"  {c['name']}")
            item.setSizeHint(QSize(0, 44))
            item.setData(Qt.ItemDataRole.UserRole, c["id"])
            item.setData(Qt.ItemDataRole.UserRole + 1, n)
            self.class_list.addItem(item)
        self.class_list.blockSignals(False)
        self.cls_count_lbl.setText(f"{len(self.classes)} ta")

        # Tanlangan sinfni qayta yuklash
        if self._cls_id:
            for i in range(self.class_list.count()):
                if self.class_list.item(i).data(Qt.ItemDataRole.UserRole) == self._cls_id:
                    self.class_list.setCurrentRow(i)
                    break

    def _on_class_selected(self, item):
        if not item:
            return
        self._cls_id   = item.data(Qt.ItemDataRole.UserRole)
        self._cls_name = item.text().strip()
        self.students_title.setText(f"👤  {self._cls_name} — O'quvchilar")
        self.add_st_btn.setEnabled(True)
        self.imp_xl_btn.setEnabled(True)
        self._load_students()

    def _load_students(self):
        if not self._cls_id:
            return
        try:
            self.students = api.get_students(self._cls_id)
        except APIError as e:
            QMessageBox.warning(self, "Xato", str(e))
            return
        self._render()

    def _render(self):
        if not self.students:
            self.tbl.hide()
            self.empty_lbl.setText(
                f"📭  {self._cls_name} sinfida hali o'quvchi yo'q\n"
                "«＋ O'quvchi qo'shish» tugmasini bosing"
            )
            self.empty_lbl.show()
            self.st_count_lbl.setText("")
            return

        self.empty_lbl.hide()
        self.tbl.show()
        self.st_count_lbl.setText(f"{len(self.students)} ta o'quvchi")
        self.tbl.setRowCount(len(self.students))

        for row, s in enumerate(self.students):
            self.tbl.setRowHeight(row, 44)

            for col, val in enumerate([s["last_name"], s["first_name"]]):
                item = QTableWidgetItem(val)
                item.setFont(QFont("Segoe UI", 12))
                self.tbl.setItem(row, col, item)

            tg = s.get("parent_telegram_id") or ""
            tg_item = QTableWidgetItem("✅  " + tg if tg else "—  (kiritilmagan)")
            tg_item.setForeground(
                QColor(COLORS["success_light"]) if tg
                else QColor(COLORS["text_secondary"])
            )
            tg_item.setFont(QFont("Segoe UI", 11))
            self.tbl.setItem(row, 2, tg_item)

            # Amallar
            cell_w = QWidget()
            cell_w.setStyleSheet("background: transparent;")
            cly = QHBoxLayout(cell_w)
            cly.setContentsMargins(6, 4, 6, 4)
            cly.setSpacing(6)

            ed = _icon_btn("✏️", "Tahrirlash")
            ed.clicked.connect(lambda _, sid=s["id"]: self._edit_student(sid))

            dl = _icon_btn("🗑️", "O'chirish", "danger")
            dl.clicked.connect(lambda _, sid=s["id"]: self._delete_student(sid))

            cly.addWidget(ed)
            cly.addWidget(dl)
            self.tbl.setCellWidget(row, 3, cell_w)

    # ── Sinf CRUD ──────────────────────────────────────────────────────────────

    def _add_class(self):
        dlg = ClassDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                api.create_class(dlg.get_name())
                self.refresh()
            except APIError as e:
                QMessageBox.critical(self, "Xato", str(e))

    def _delete_class(self):
        item = self.class_list.currentItem()
        if not item:
            QMessageBox.information(self, "Tanlash", "Avval chapdan sinf tanlang!")
            return
        name = item.text().strip()
        n = item.data(Qt.ItemDataRole.UserRole + 1)
        msg = (f"«{name}» sinfini o'chirishni tasdiqlaysizmi?"
               + (f"\n\nDiqqat: Bu sinfda {n} ta o'quvchi bor, ular ham o'chiriladi!" if n else ""))
        r = QMessageBox.question(self, "O'chirish", msg,
                                 QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if r == QMessageBox.StandardButton.Yes:
            try:
                api.delete_class(item.data(Qt.ItemDataRole.UserRole))
                self._cls_id = None
                self._cls_name = ""
                self.tbl.hide()
                self.empty_lbl.setText("⬅  Chapdan sinf tanlang\nSo'ng o'quvchi qo'shing")
                self.empty_lbl.show()
                self.students_title.setText("👤  O'quvchilar")
                self.add_st_btn.setEnabled(False)
                self.imp_xl_btn.setEnabled(False)
                self.refresh()
            except APIError as e:
                QMessageBox.critical(self, "Xato", str(e))

    # ── O'quvchi CRUD ──────────────────────────────────────────────────────────

    def _add_student(self):
        dlg = StudentDialog(parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                api.add_student(self._cls_id, dlg.get_data())
                self._load_students()
                self.refresh()
            except APIError as e:
                QMessageBox.critical(self, "Xato", str(e))

    def _edit_student(self, sid):
        s = next((x for x in self.students if x["id"] == sid), None)
        if not s:
            return
        dlg = StudentDialog(student=s, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                api.update_student(sid, dlg.get_data())
                self._load_students()
            except APIError as e:
                QMessageBox.critical(self, "Xato", str(e))

    def _delete_student(self, sid):
        s = next((x for x in self.students if x["id"] == sid), None)
        if not s:
            return
        r = QMessageBox.question(
            self, "O'chirish",
            f"{s['last_name']} {s['first_name']}ni ro'yxatdan o'chirishni tasdiqlaysizmi?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if r == QMessageBox.StandardButton.Yes:
            try:
                api.delete_student(sid)
                self._load_students()
                self.refresh()
            except APIError as e:
                QMessageBox.critical(self, "Xato", str(e))

    # ── Excel ──────────────────────────────────────────────────────────────────

    def _show_format(self):
        ExcelFormatDialog(self).exec()

    def _import_excel(self):
        if not self._cls_id:
            QMessageBox.warning(self, "Xato", "Avval sinf tanlang!")
            return

        path, _ = QFileDialog.getOpenFileName(
            self, "Excel fayl tanlang", "", "Excel (*.xlsx *.xls)"
        )
        if not path:
            return

        try:
            import openpyxl
            wb = openpyxl.load_workbook(path, data_only=True)
            ws = wb.active
            added, skipped = 0, 0

            for row in ws.iter_rows(min_row=2, values_only=True):
                if not row or not row[0]:
                    continue
                first = str(row[0]).strip() if row[0] else ""
                last  = str(row[1]).strip() if len(row) > 1 and row[1] else ""
                tg    = str(row[2]).strip() if len(row) > 2 and row[2] else None

                if first and last:
                    api.add_student(self._cls_id, {
                        "first_name": first,
                        "last_name":  last,
                        "parent_telegram_id": tg or None,
                    })
                    added += 1
                else:
                    skipped += 1

            msg = f"✅  {added} ta o'quvchi muvaffaqiyatli yuklandi!"
            if skipped:
                msg += f"\n⚠️  {skipped} ta qator to'liq emas (o'tkazib yuborildi)."
            QMessageBox.information(self, "Import natijasi", msg)
            self._load_students()
            self.refresh()

        except Exception as e:
            QMessageBox.critical(self, "Fayl xatosi", f"Excel faylni o'qishda xato:\n{e}")
