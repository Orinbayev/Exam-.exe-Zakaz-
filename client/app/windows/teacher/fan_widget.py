"""
Fan (Subject) boshqaruvi — fanlar va ularning savollarini bir joyda.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QTableWidget, QTableWidgetItem,
    QDialog, QLineEdit, QComboBox, QTextEdit, QInputDialog,
    QMessageBox, QHeaderView, QFrame, QSizePolicy,
    QScrollArea,
)
from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtGui import QFont, QColor
from ...api_client import api, APIError
from ...styles import COLORS


# ─────────────────────────────────────────────────────────────────────────────
# Stil konstantalari
# ─────────────────────────────────────────────────────────────────────────────

_DLG_BASE = f"""
QDialog {{
    background: {COLORS['bg_medium']};
    color: white;
    font-family: 'Segoe UI', Arial;
}}
QLabel {{ color: white; background: transparent; }}
QLineEdit, QTextEdit, QComboBox {{
    background: {COLORS['bg_dark']};
    color: white;
    border: 1.5px solid {COLORS['border']};
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 13px;
}}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus {{
    border: 2px solid {COLORS['primary_light']};
}}
QComboBox::drop-down {{ border: none; width: 24px; }}
QPushButton {{
    background: {COLORS['primary']};
    color: white; border: none; border-radius: 8px;
    padding: 9px 20px; font-size: 13px; font-weight: bold;
    min-height: 36px;
}}
QPushButton:hover {{ background: {COLORS['primary_light']}; }}
QPushButton#cancel {{
    background: {COLORS['bg_light']};
    border: 1px solid {COLORS['border']};
}}
QPushButton#cancel:hover {{ background: {COLORS['bg_dark']}; }}
"""

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
        padding: 11px 14px;
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
    QTableWidget::item {{ padding: 6px 10px; }}
    QTableWidget::item:selected {{
        background: {COLORS['primary']};
        color: white;
    }}
    QHeaderView::section {{
        background: {COLORS['bg_light']};
        color: {COLORS['text_secondary']};
        padding: 9px 10px;
        border: none;
        border-right: 1px solid {COLORS['border']};
        border-bottom: 1px solid {COLORS['border']};
        font-weight: bold;
        font-size: 12px;
    }}
"""


# ─────────────────────────────────────────────────────────────────────────────
# Fan qo'shish dialogi
# ─────────────────────────────────────────────────────────────────────────────

class FanDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Yangi fan qo'shish")
        self.setFixedSize(380, 190)
        self.setStyleSheet(_DLG_BASE)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(26, 22, 26, 22)
        lay.setSpacing(14)

        ico = QLabel("📚")
        ico.setFont(QFont("Segoe UI Emoji", 28))
        ico.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(ico)

        lbl = QLabel("Fan nomini kiriting:")
        lbl.setFont(QFont("Segoe UI", 11))
        lay.addWidget(lbl)

        self.inp = QLineEdit()
        self.inp.setPlaceholderText("Masalan:  Matematika   yoki   Ona tili")
        self.inp.setFixedHeight(42)
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
            self.inp.setPlaceholderText("⚠  Fan nomini kiriting!")
            self.inp.setStyleSheet(self.inp.styleSheet() + "border:2px solid #EF5350;")
            return
        self.accept()

    def get_name(self):
        return self.inp.text().strip()


# ─────────────────────────────────────────────────────────────────────────────
# Savol qo'shish / tahrirlash dialogi
# ─────────────────────────────────────────────────────────────────────────────

class QuestionDialog(QDialog):
    def __init__(self, fan_name: str = "", question: dict = None, parent=None):
        super().__init__(parent)
        self._q = question
        _action = "Savol qo'shish" if not question else "Savolni tahrirlash"
        self.setWindowTitle(_action + (f" — {fan_name}" if fan_name else ""))
        self.setFixedWidth(540)
        self.setStyleSheet(_DLG_BASE)
        self._build()
        if question:
            self._fill(question)

    def _build(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        inner = QWidget()
        inner.setStyleSheet("background: transparent;")
        lay = QVBoxLayout(inner)
        lay.setContentsMargins(26, 20, 26, 20)
        lay.setSpacing(12)

        # Header icon
        ico = QLabel("❓" if not self._q else "✏️")
        ico.setFont(QFont("Segoe UI Emoji", 24))
        ico.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(ico)

        def _lbl(text):
            l = QLabel(text)
            l.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
            l.setStyleSheet(f"color: {COLORS['text_secondary']};")
            return l

        # Savol matni
        lay.addWidget(_lbl("Savol matni *"))
        self.txt = QTextEdit()
        self.txt.setFixedHeight(90)
        self.txt.setPlaceholderText("Savol matnini shu yerga kiriting...")
        lay.addWidget(self.txt)

        # Variantlar
        self.opts: list[QLineEdit] = []
        labels = ["A  variant *", "B  variant *", "C  variant *", "D  variant *"]
        colors = ["#66BB6A", "#42A5F5", "#FFA726", "#EF5350"]
        for lbl_txt, clr in zip(labels, colors):
            row = QHBoxLayout()
            row.setSpacing(8)
            badge = QLabel(lbl_txt[0])
            badge.setFixedSize(28, 28)
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            badge.setStyleSheet(f"""
                background: {clr}; color: white;
                border-radius: 6px; font-weight: bold; font-size: 13px;
            """)
            inp = QLineEdit()
            inp.setPlaceholderText(lbl_txt)
            inp.setFixedHeight(40)
            row.addWidget(badge)
            row.addWidget(inp, stretch=1)
            lay.addLayout(row)
            self.opts.append(inp)

        # To'g'ri javob
        lay.addWidget(_lbl("To'g'ri javob *"))
        self.answer = QComboBox()
        self.answer.addItems([
            "A  — birinchi variant",
            "B  — ikkinchi variant",
            "C  — uchinchi variant",
            "D  — to'rtinchi variant",
        ])
        self.answer.setFixedHeight(48)
        self.answer.setStyleSheet(f"""
            QComboBox {{
                background: {COLORS['bg_dark']};
                color: white;
                border: 2px solid {COLORS['primary']};
                border-radius: 10px;
                padding: 0 14px;
                font-size: 14px;
                font-weight: bold;
                font-family: 'Segoe UI', Arial;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 32px;
            }}
            QComboBox::down-arrow {{
                border-left:  6px solid transparent;
                border-right: 6px solid transparent;
                border-top:   7px solid rgba(255,255,255,0.85);
                margin-right: 10px;
            }}
            QComboBox QAbstractItemView {{
                background: {COLORS['bg_medium']};
                color: white;
                selection-background-color: {COLORS['primary']};
                border: 1px solid {COLORS['border']};
                font-size: 13px;
                padding: 4px;
                outline: none;
            }}
        """)
        lay.addWidget(self.answer)

        # Tugmalar
        lay.addSpacing(6)
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        cancel = QPushButton("Bekor qilish")
        cancel.setObjectName("cancel")
        cancel.clicked.connect(self.reject)
        save = QPushButton("✅  Saqlash")
        save.clicked.connect(self._ok)
        btn_row.addWidget(cancel)
        btn_row.addWidget(save)
        lay.addLayout(btn_row)

        scroll.setWidget(inner)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _fill(self, q: dict):
        self.txt.setPlainText(q.get("text", ""))
        self.opts[0].setText(q.get("option_a", ""))
        self.opts[1].setText(q.get("option_b", ""))
        self.opts[2].setText(q.get("option_c", ""))
        self.opts[3].setText(q.get("option_d", ""))
        ans = q.get("correct_answer", "A").upper()
        self.answer.setCurrentIndex({"A": 0, "B": 1, "C": 2, "D": 3}.get(ans, 0))

    def _ok(self):
        if not self.txt.toPlainText().strip():
            QMessageBox.warning(self, "⚠ Xato", "Savol matni bo'sh bo'lishi mumkin emas!")
            return
        for i, opt in enumerate(self.opts):
            if not opt.text().strip():
                QMessageBox.warning(self, "⚠ Xato",
                    f"{chr(65+i)} variant bo'sh bo'lishi mumkin emas!")
                return
        self.accept()

    def get_data(self, category_id: int = None) -> dict:
        # "A  — birinchi variant" dan faqat "A" ni olamiz
        ans_letter = self.answer.currentText().strip()[0].upper()
        return {
            "text":           self.txt.toPlainText().strip(),
            "option_a":       self.opts[0].text().strip(),
            "option_b":       self.opts[1].text().strip(),
            "option_c":       self.opts[2].text().strip(),
            "option_d":       self.opts[3].text().strip(),
            "correct_answer": ans_letter,
            "category_id":    category_id,
            "difficulty":     "medium",
        }


# ─────────────────────────────────────────────────────────────────────────────
# Asosiy widget
# ─────────────────────────────────────────────────────────────────────────────

class FanWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._fans: list = []
        self._questions: list = []
        self._fan_id: int | None = None
        self._fan_name: str = ""
        self._setup_ui()
        self.refresh()

    # ── UI qurilishi ──────────────────────────────────────────────────────────

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(14)

        # ── Sarlavha ──────────────────────────────────────────────────────────
        hdr = QHBoxLayout()
        title = QLabel("📚  Fanlar va Savollar")
        title.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        hdr.addWidget(title)
        hdr.addStretch()

        hint_lbl = QLabel(
            "💡  Fan yarating → savollar qo'shing → sinfga biriktiring"
        )
        hint_lbl.setFont(QFont("Segoe UI", 11))
        hint_lbl.setStyleSheet(f"color: {COLORS['text_secondary']};")
        hdr.addWidget(hint_lbl)
        root.addLayout(hdr)

        # ── Asosiy ikki panel ─────────────────────────────────────────────────
        panels = QHBoxLayout()
        panels.setSpacing(14)

        # ── CHAP: Fan ro'yxati ────────────────────────────────────────────────
        left = QFrame()
        left.setStyleSheet(_PANEL_STYLE)
        left.setFixedWidth(250)
        ll = QVBoxLayout(left)
        ll.setContentsMargins(12, 14, 12, 14)
        ll.setSpacing(10)

        l_hdr = QHBoxLayout()
        l_title = QLabel("📚  Fanlar")
        l_title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        l_hdr.addWidget(l_title)
        self._fan_count_lbl = QLabel("0 ta")
        self._fan_count_lbl.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: 11px;"
        )
        l_hdr.addStretch()
        l_hdr.addWidget(self._fan_count_lbl)
        ll.addLayout(l_hdr)

        self._fan_list = QListWidget()
        self._fan_list.setStyleSheet(_LIST_STYLE)
        self._fan_list.currentItemChanged.connect(self._on_fan_selected)
        ll.addWidget(self._fan_list)

        add_fan_btn = QPushButton("＋  Fan qo'shish")
        add_fan_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['success']};
                color: white; border: none; border-radius: 8px;
                padding: 10px; font-size: 13px; font-weight: bold;
            }}
            QPushButton:hover {{ background: {COLORS['success_light']}; }}
        """)
        add_fan_btn.clicked.connect(self._add_fan)
        ll.addWidget(add_fan_btn)

        time_btn = QPushButton("⏱  Imtihon vaqtini sozlash")
        time_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['accent']};
                color: white; border: none; border-radius: 8px;
                padding: 8px; font-size: 12px; font-weight: bold;
            }}
            QPushButton:hover {{ background: {COLORS['accent_light']}; }}
        """)
        time_btn.clicked.connect(self._set_time_limit)
        ll.addWidget(time_btn)

        del_fan_btn = QPushButton("🗑  Fan o'chirish")
        del_fan_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['bg_dark']};
                color: {COLORS['danger_light']};
                border: 1px solid {COLORS['danger']};
                border-radius: 8px; padding: 8px; font-size: 12px;
            }}
            QPushButton:hover {{
                background: {COLORS['danger']}; color: white;
            }}
        """)
        del_fan_btn.clicked.connect(self._delete_fan)
        ll.addWidget(del_fan_btn)

        panels.addWidget(left)

        # ── O'NG: Savollar ────────────────────────────────────────────────────
        right = QFrame()
        right.setStyleSheet(_PANEL_STYLE)
        rl = QVBoxLayout(right)
        rl.setContentsMargins(14, 14, 14, 14)
        rl.setSpacing(10)

        # O'ng sarlavha
        r_hdr = QHBoxLayout()
        self._q_title = QLabel("❓  Savollar")
        self._q_title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        r_hdr.addWidget(self._q_title)
        r_hdr.addStretch()
        self._q_count_lbl = QLabel("")
        self._q_count_lbl.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: 11px;"
        )
        r_hdr.addWidget(self._q_count_lbl)
        rl.addLayout(r_hdr)

        # Statistika qatori
        self._stat_row = QHBoxLayout()
        self._stat_active_lbl = QLabel("")
        self._stat_frozen_lbl = QLabel("")
        for lbl in (self._stat_active_lbl, self._stat_frozen_lbl):
            lbl.setFont(QFont("Segoe UI", 11))
            lbl.setStyleSheet("background: transparent;")
        self._stat_row.addWidget(self._stat_active_lbl)
        self._stat_row.addSpacing(16)
        self._stat_row.addWidget(self._stat_frozen_lbl)
        self._stat_row.addStretch()
        rl.addLayout(self._stat_row)

        # Bo'sh holat
        self._empty_lbl = QLabel(
            "⬅  Chapdan fan tanlang\nSo'ng savol qo'shing"
        )
        self._empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_lbl.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: 14px; background: transparent;"
        )

        # Jadval
        self._tbl = QTableWidget()
        self._tbl.setColumnCount(6)
        self._tbl.setHorizontalHeaderLabels(
            ["#", "Savol matni", "A", "B", "C", "D"]
        )
        self._tbl.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self._tbl.setColumnWidth(0, 40)
        self._tbl.setColumnWidth(2, 130)
        self._tbl.setColumnWidth(3, 130)
        self._tbl.setColumnWidth(4, 130)
        self._tbl.setColumnWidth(5, 130)
        self._tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._tbl.verticalHeader().setVisible(False)
        self._tbl.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._tbl.setAlternatingRowColors(True)
        self._tbl.setStyleSheet(_TABLE_STYLE + """
            QTableWidget { alternate-background-color: rgba(255,255,255,0.03); }
        """)
        self._tbl.hide()

        rl.addWidget(self._empty_lbl, stretch=1)
        rl.addWidget(self._tbl, stretch=1)

        # Tugmalar qatori
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self._add_q_btn = QPushButton("＋  Savol qo'shish")
        self._add_q_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['success']};
                color: white; border: none; border-radius: 8px;
                padding: 9px 16px; font-size: 13px; font-weight: bold;
            }}
            QPushButton:hover {{ background: {COLORS['success_light']}; }}
            QPushButton:disabled {{
                background: {COLORS['bg_light']};
                color: {COLORS['text_secondary']};
            }}
        """)
        self._add_q_btn.setEnabled(False)
        self._add_q_btn.clicked.connect(self._add_question)

        self._show_frozen_btn = QPushButton("❄️  Muzlatilganlarni ko'rsatish")
        self._show_frozen_btn.setObjectName("secondary")
        self._show_frozen_btn.setCheckable(True)
        self._show_frozen_btn.clicked.connect(self._toggle_show_frozen)

        btn_row.addWidget(self._add_q_btn)
        btn_row.addStretch()
        btn_row.addWidget(self._show_frozen_btn)
        rl.addLayout(btn_row)

        panels.addWidget(right, stretch=1)
        root.addLayout(panels, stretch=1)

        self._show_all_frozen = False

    # ── Fanlar ────────────────────────────────────────────────────────────────

    def refresh(self):
        try:
            self._fans = api.get_categories()
        except APIError:
            self._fans = []

        self._fan_list.blockSignals(True)
        self._fan_list.clear()
        for f in self._fans:
            q_count = f.get("question_count", 0)
            t_lim = f.get("time_limit", 30)
            badge = f"  ·  {q_count} ta savol  ·  ⏱{t_lim} daq"
            item = QListWidgetItem(f"📚  {f['name']}{badge}")
            item.setSizeHint(QSize(0, 48))
            item.setData(Qt.ItemDataRole.UserRole, f["id"])
            item.setData(Qt.ItemDataRole.UserRole + 1, f["name"])
            item.setData(Qt.ItemDataRole.UserRole + 2, t_lim)
            self._fan_list.addItem(item)
        self._fan_list.blockSignals(False)
        self._fan_count_lbl.setText(f"{len(self._fans)} ta")

        # Tanlangan fanni qayta yuklash
        if self._fan_id:
            for i in range(self._fan_list.count()):
                if self._fan_list.item(i).data(Qt.ItemDataRole.UserRole) == self._fan_id:
                    self._fan_list.setCurrentRow(i)
                    break

    def _on_fan_selected(self, item):
        if not item:
            return
        self._fan_id = item.data(Qt.ItemDataRole.UserRole)
        self._fan_name = item.data(Qt.ItemDataRole.UserRole + 1)
        self._q_title.setText(f"❓  {self._fan_name} — Savollar")
        self._add_q_btn.setEnabled(True)
        self._load_questions()

    def _add_fan(self):
        dlg = FanDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                api.create_category(dlg.get_name())
                self.refresh()
            except APIError as e:
                QMessageBox.critical(self, "Xato", str(e))

    def _set_time_limit(self):
        item = self._fan_list.currentItem()
        if not item:
            QMessageBox.information(self, "Tanlash", "Avval chapdan fan tanlang!")
            return
        fan = next((f for f in self._fans if f["id"] == self._fan_id), None)
        current_time = fan.get("time_limit", 30) if fan else 30

        from PyQt6.QtWidgets import QInputDialog
        val, ok = QInputDialog.getInt(
            self,
            "⏱  Imtihon vaqtini sozlash",
            f"«{self._fan_name}» fani uchun vaqt (daqiqada):\n"
            f"(hozir: {current_time} daqiqa)",
            current_time, 1, 300, 1
        )
        if not ok:
            return
        try:
            api.set_category_time_limit(self._fan_id, val)
            QMessageBox.information(
                self, "✅ Saqlandi",
                f"«{self._fan_name}» uchun imtihon vaqti {val} daqiqaga o'rnatildi.\n\n"
                "Diqqat: O'zgarish kuchga kirishi uchun sinfga qaytadan fan biriktiring."
            )
            self.refresh()
        except APIError as e:
            QMessageBox.critical(self, "Xato", str(e))

    def _delete_fan(self):
        item = self._fan_list.currentItem()
        if not item:
            QMessageBox.information(self, "Tanlash", "Avval chapdan fan tanlang!")
            return
        name = item.data(Qt.ItemDataRole.UserRole + 1)
        r = QMessageBox.question(
            self, "O'chirish",
            f"«{name}» fanini o'chirishni tasdiqlaysizmi?\n\n"
            "Diqqat: Ushbu fandagi barcha savollar ham o'chiriladi!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if r == QMessageBox.StandardButton.Yes:
            try:
                api.delete_category(self._fan_id)
                self._fan_id = None
                self._fan_name = ""
                self._q_title.setText("❓  Savollar")
                self._q_count_lbl.setText("")
                self._tbl.hide()
                self._empty_lbl.setText("⬅  Chapdan fan tanlang\nSo'ng savol qo'shing")
                self._empty_lbl.show()
                self._add_q_btn.setEnabled(False)
                self.refresh()
            except APIError as e:
                QMessageBox.critical(self, "Xato", str(e))

    # ── Savollar ──────────────────────────────────────────────────────────────

    def _load_questions(self):
        if not self._fan_id:
            return
        try:
            self._questions = api.get_questions(category_id=self._fan_id)
        except APIError as e:
            QMessageBox.warning(self, "Xato", str(e))
            return
        self._render_table()

    def _toggle_show_frozen(self):
        self._show_all_frozen = self._show_frozen_btn.isChecked()
        btn_text = ("❄️  Barchasini ko'rsatish" if self._show_all_frozen
                    else "❄️  Muzlatilganlarni ko'rsatish")
        self._show_frozen_btn.setText(btn_text)
        self._render_table()

    def _render_table(self):
        # Filterlash: agar "show frozen" yoqilmagan bo'lsa — faqat aktiv
        if self._show_all_frozen:
            rows = self._questions
        else:
            rows = [q for q in self._questions if q.get("is_active", True)]

        active_n = sum(1 for q in self._questions if q.get("is_active", True))
        frozen_n = len(self._questions) - active_n

        self._q_count_lbl.setText(f"{len(self._questions)} ta savol")
        self._stat_active_lbl.setText(
            f"🟢  Aktiv: {active_n}"
        )
        self._stat_active_lbl.setStyleSheet(
            f"color: {COLORS['success_light']}; background: transparent;"
        )
        self._stat_frozen_lbl.setText(f"❄️  Muzlatilgan: {frozen_n}")
        self._stat_frozen_lbl.setStyleSheet(
            f"color: {COLORS['text_secondary']}; background: transparent;"
        )

        if not rows:
            self._tbl.hide()
            if not self._questions:
                self._empty_lbl.setText(
                    f"📭  «{self._fan_name}» fanida hali savol yo'q\n"
                    "«＋ Savol qo'shish» tugmasini bosing"
                )
            else:
                self._empty_lbl.setText(
                    f"❄️  Barcha savollar muzlatilgan\n"
                    "«Muzlatilganlarni ko'rsatish» tugmasini bosing"
                )
            self._empty_lbl.show()
            return

        self._empty_lbl.hide()
        self._tbl.show()
        self._tbl.setRowCount(len(rows))

        for row_idx, q in enumerate(rows):
            self._tbl.setRowHeight(row_idx, 46)
            is_active = q.get("is_active", True)

            # # raqam
            num_item = QTableWidgetItem(str(row_idx + 1))
            num_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if not is_active:
                num_item.setForeground(QColor(COLORS["text_secondary"]))
            self._tbl.setItem(row_idx, 0, num_item)

            # Savol matni (qisqartirilgan)
            text = q.get("text", "")
            short = text[:80] + "..." if len(text) > 80 else text
            if not is_active:
                short = "❄️  " + short
            txt_item = QTableWidgetItem(short)
            txt_item.setFont(QFont("Segoe UI", 12))
            if not is_active:
                txt_item.setForeground(QColor(COLORS["text_secondary"]))
            txt_item.setToolTip(text)
            self._tbl.setItem(row_idx, 1, txt_item)

            # A B C D variantlari
            ans = q.get("correct_answer", "")
            opt_keys = ["option_a", "option_b", "option_c", "option_d"]
            opt_labels = ["A", "B", "C", "D"]
            opt_color = "#66BB6A"  # to'g'ri javob rangi

            for ci, (key, lbl) in enumerate(zip(opt_keys, opt_labels)):
                val = q.get(key, "")
                short_val = val[:22] + "…" if len(val) > 22 else val
                is_correct = (ans == lbl)
                item = QTableWidgetItem(
                    f"✔ {short_val}" if is_correct else short_val
                )
                item.setFont(QFont("Segoe UI", 11))
                item.setToolTip(val)
                if not is_active:
                    item.setForeground(QColor(COLORS["text_secondary"]))
                elif is_correct:
                    item.setForeground(QColor(opt_color))
                    item.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
                self._tbl.setItem(row_idx, 2 + ci, item)

        # Amallar ustunini alohida qo'shamiz (7-ustun)
        # Avval ustun sonini 7 ga o'rnatamiz
        self._tbl.setColumnCount(7)
        self._tbl.setHorizontalHeaderLabels(
            ["#", "Savol matni", "A", "B", "C", "D", "Amallar"]
        )
        self._tbl.setColumnWidth(6, 120)
        self._tbl.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )

        for row_idx, q in enumerate(rows):
            is_active = q.get("is_active", True)
            cell_w = QWidget()
            cell_w.setStyleSheet("background: transparent;")
            cly = QHBoxLayout(cell_w)
            cly.setContentsMargins(4, 3, 4, 3)
            cly.setSpacing(4)
            cly.setAlignment(Qt.AlignmentFlag.AlignCenter)

            ed = QPushButton("✏️")
            ed.setFixedSize(34, 30)
            ed.setObjectName("table_action")
            ed.setToolTip("Tahrirlash")
            ed.clicked.connect(lambda _, qid=q["id"]: self._edit_question(qid))

            frz = QPushButton("❄️" if is_active else "✅")
            frz.setFixedSize(34, 30)
            frz.setObjectName("table_action")
            frz.setToolTip("Muzlatish" if is_active else "Faollashtirish")
            frz.clicked.connect(lambda _, qid=q["id"]: self._toggle_question(qid))

            dl = QPushButton("🗑️")
            dl.setFixedSize(34, 30)
            dl.setObjectName("table_action_danger")
            dl.setToolTip("O'chirish")
            dl.clicked.connect(lambda _, qid=q["id"]: self._delete_question(qid))

            cly.addWidget(ed)
            cly.addWidget(frz)
            cly.addWidget(dl)
            self._tbl.setCellWidget(row_idx, 6, cell_w)

    # ── Savol CRUD ────────────────────────────────────────────────────────────

    def _add_question(self):
        dlg = QuestionDialog(fan_name=self._fan_name, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                api.create_question(dlg.get_data(category_id=self._fan_id))
                self._load_questions()
                self.refresh()
            except APIError as e:
                QMessageBox.critical(self, "Xato", str(e))

    def _edit_question(self, qid: int):
        q = next((x for x in self._questions if x["id"] == qid), None)
        if not q:
            return
        dlg = QuestionDialog(fan_name=self._fan_name, question=q, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                data = dlg.get_data(category_id=self._fan_id)
                data.pop("category_id", None)  # PUT uchun kerak emas
                api.update_question(qid, data)
                self._load_questions()
            except APIError as e:
                QMessageBox.critical(self, "Xato", str(e))

    def _toggle_question(self, qid: int):
        try:
            result = api.toggle_question_active(qid)
            q = next((x for x in self._questions if x["id"] == qid), None)
            if q:
                q["is_active"] = result.get("is_active", not q.get("is_active", True))
            self._render_table()
        except APIError as e:
            QMessageBox.critical(self, "Xato", str(e))

    def _delete_question(self, qid: int):
        q = next((x for x in self._questions if x["id"] == qid), None)
        if not q:
            return
        short = q["text"][:60] + "..." if len(q["text"]) > 60 else q["text"]
        r = QMessageBox.question(
            self, "O'chirish",
            f"Ushbu savolni o'chirishni tasdiqlaysizmi?\n\n«{short}»",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if r == QMessageBox.StandardButton.Yes:
            try:
                api.delete_question(qid)
                self._load_questions()
                self.refresh()
            except APIError as e:
                QMessageBox.critical(self, "Xato", str(e))
