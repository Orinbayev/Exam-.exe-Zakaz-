"""
Barcha o'quvchilar — umumiy ko'rinish (sinf + fan bo'yicha filter).
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QComboBox, QFrame, QMessageBox, QDialog,
)
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QFont, QColor, QIcon

from ...api_client import api, APIError
from ...styles import COLORS
from ...i18n import t
from ...worker import ApiWorker
from .students_widget import StudentDialog   # re-use existing dialog


# ─────────────────────────────────────────────────────────────────────────────
# Yordamchi: qidiruv/filter satri
# ─────────────────────────────────────────────────────────────────────────────

_COMBO_STYLE = f"""
QComboBox {{
    background: {COLORS['bg_medium']};
    color: white;
    border: 1.5px solid {COLORS['border']};
    border-radius: 8px;
    padding: 6px 10px;
    font-size: 12px;
    min-width: 160px;
}}
QComboBox:focus {{ border-color: {COLORS['primary_light']}; }}
QComboBox::drop-down {{
    border: none;
    padding-right: 8px;
}}
QComboBox QAbstractItemView {{
    background: {COLORS['bg_medium']};
    color: white;
    border: 1px solid {COLORS['border']};
    selection-background-color: {COLORS['primary']};
    font-size: 12px;
}}
"""

_SEARCH_STYLE = f"""
QLineEdit {{
    background: {COLORS['bg_medium']};
    color: white;
    border: 1.5px solid {COLORS['border']};
    border-radius: 8px;
    padding: 6px 14px;
    font-size: 13px;
    min-width: 220px;
}}
QLineEdit:focus {{ border-color: {COLORS['primary_light']}; }}
"""

_TABLE_STYLE = f"""
QTableWidget {{
    background: {COLORS['bg_dark']};
    color: white;
    border: 1px solid {COLORS['border']};
    border-radius: 10px;
    gridline-color: {COLORS['border']};
    font-size: 13px;
    outline: none;
}}
QTableWidget::item {{
    padding: 8px 12px;
    border-bottom: 1px solid rgba(42,90,140,0.4);
}}
QTableWidget::item:selected {{
    background: {COLORS['primary']};
    color: white;
}}
QTableWidget::item:alternate {{
    background: rgba(255,255,255,0.025);
}}
QHeaderView::section {{
    background: {COLORS['bg_light']};
    color: {COLORS['text_secondary']};
    padding: 10px 12px;
    border: none;
    border-right: 1px solid {COLORS['border']};
    border-bottom: 2px solid {COLORS['primary']};
    font-weight: bold;
    font-size: 12px;
}}
"""


class AllStudentsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._students: list = []
        self._classes:  list = []
        self._fans:     list = []
        self._debounce  = QTimer()
        self._debounce.setSingleShot(True)
        self._debounce.timeout.connect(self._load)
        self._setup_ui()
        self._load_filters()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(16)

        # ── Sarlavha ──────────────────────────────────────────────────────────
        hdr = QHBoxLayout()
        title = QLabel(t("as.title"))
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: white;")
        hdr.addWidget(title)
        hdr.addStretch()

        self._count_lbl = QLabel("")
        self._count_lbl.setFont(QFont("Segoe UI", 11))
        self._count_lbl.setStyleSheet(f"color: {COLORS['text_secondary']};")
        hdr.addWidget(self._count_lbl)
        root.addLayout(hdr)

        # ── Filter paneli ─────────────────────────────────────────────────────
        filter_frame = QFrame()
        filter_frame.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['bg_medium']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
            }}
        """)
        fl = QHBoxLayout(filter_frame)
        fl.setContentsMargins(16, 12, 16, 12)
        fl.setSpacing(12)

        # Qidiruv
        srch_lbl = QLabel("🔍")
        srch_lbl.setFont(QFont("Segoe UI Emoji", 14))
        srch_lbl.setStyleSheet("background: transparent;")
        fl.addWidget(srch_lbl)

        self._search = QLineEdit()
        self._search.setPlaceholderText(t("as.search_ph"))
        self._search.setFixedHeight(38)
        self._search.setStyleSheet(_SEARCH_STYLE)
        self._search.textChanged.connect(lambda: self._debounce.start(350))
        fl.addWidget(self._search, stretch=1)

        # Sinf filter
        cls_lbl = QLabel(t("as.filter_class"))
        cls_lbl.setFont(QFont("Segoe UI", 11))
        cls_lbl.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent;")
        fl.addWidget(cls_lbl)

        self._cls_combo = QComboBox()
        self._cls_combo.setFixedHeight(38)
        self._cls_combo.setStyleSheet(_COMBO_STYLE)
        self._cls_combo.currentIndexChanged.connect(self._load)
        fl.addWidget(self._cls_combo)

        # Fan filter
        fan_lbl = QLabel(t("as.filter_fan"))
        fan_lbl.setFont(QFont("Segoe UI", 11))
        fan_lbl.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent;")
        fl.addWidget(fan_lbl)

        self._fan_combo = QComboBox()
        self._fan_combo.setFixedHeight(38)
        self._fan_combo.setStyleSheet(_COMBO_STYLE)
        self._fan_combo.currentIndexChanged.connect(self._load)
        fl.addWidget(self._fan_combo)

        fl.addSpacing(8)

        # Yangilash
        ref_btn = QPushButton("🔄")
        ref_btn.setFixedSize(38, 38)
        ref_btn.setToolTip("Yangilash")
        ref_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['bg_light']};
                color: white; border: 1px solid {COLORS['border']};
                border-radius: 8px; font-size: 14px;
            }}
            QPushButton:hover {{ background: {COLORS['primary']}; border-color: {COLORS['primary']}; }}
        """)
        ref_btn.clicked.connect(self._load)
        fl.addWidget(ref_btn)

        root.addWidget(filter_frame)

        # ── Jadval ────────────────────────────────────────────────────────────
        self._tbl = QTableWidget()
        self._tbl.setColumnCount(5)
        self._tbl.setHorizontalHeaderLabels([
            t("as.col_last"),
            t("as.col_first"),
            t("as.col_class"),
            t("as.col_tg"),
            t("as.col_actions"),
        ])
        hh = self._tbl.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self._tbl.setColumnWidth(4, 110)
        self._tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._tbl.verticalHeader().setVisible(False)
        self._tbl.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._tbl.setAlternatingRowColors(True)
        self._tbl.setShowGrid(False)
        self._tbl.setStyleSheet(_TABLE_STYLE)
        root.addWidget(self._tbl, stretch=1)

        # ── Pastki panel ──────────────────────────────────────────────────────
        bottom = QHBoxLayout()
        bottom.setSpacing(10)

        self._add_btn = QPushButton(t("as.add_btn"))
        self._add_btn.setFixedHeight(40)
        self._add_btn.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self._add_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {COLORS['success']}, stop:1 #388E3C);
                color: white; border: none; border-radius: 10px;
                padding: 0 22px; font-size: 13px; font-weight: bold;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #388E3C, stop:1 {COLORS['success_light']});
            }}
        """)
        self._add_btn.clicked.connect(self._add_student)
        bottom.addWidget(self._add_btn)
        bottom.addStretch()

        # Hint
        hint_lbl = QLabel("💡  O'quvchini qo'shish uchun sinf filtridan sinf tanlang")
        hint_lbl.setFont(QFont("Segoe UI", 10))
        hint_lbl.setStyleSheet(f"color: {COLORS['text_secondary']};")
        bottom.addWidget(hint_lbl)

        root.addLayout(bottom)

    # ── Filterlarni yuklash ───────────────────────────────────────────────────

    def _load_filters(self):
        try:
            self._classes = api.get_classes()
        except APIError:
            self._classes = []
        try:
            self._fans = api.get_categories()
        except APIError:
            self._fans = []

        self._cls_combo.blockSignals(True)
        self._fan_combo.blockSignals(True)

        self._cls_combo.clear()
        self._cls_combo.addItem(t("as.all_classes"), None)
        for c in self._classes:
            icon = "🟢" if c.get("is_active") else "⚫"
            self._cls_combo.addItem(f"{icon} {c['name']}", c["id"])

        self._fan_combo.clear()
        self._fan_combo.addItem(t("as.all_fans"), None)
        for f in self._fans:
            self._fan_combo.addItem(f"📚 {f['name']}", f["id"])

        self._cls_combo.blockSignals(False)
        self._fan_combo.blockSignals(False)

        self._load()

    # ── Ma'lumot yuklash ──────────────────────────────────────────────────────

    def _load(self):
        class_id = self._cls_combo.currentData()
        fan_id   = self._fan_combo.currentData()
        search   = self._search.text().strip() or None

        self._count_lbl.setText(t("as.loading"))
        self._w = ApiWorker(api.get_all_students, class_id=class_id,
                            fan_id=fan_id, search=search)
        self._w.done.connect(self._render)
        self._w.error.connect(lambda e: self._count_lbl.setText(f"Xato: {e}"))
        self._w.start()

    def _render(self, students: list):
        self._students = students
        n = len(students)
        self._count_lbl.setText(t("as.count", n=n))
        self._tbl.setRowCount(n)

        if n == 0:
            self._tbl.setRowCount(1)
            empty = QTableWidgetItem(t("as.empty"))
            empty.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setForeground(QColor(COLORS["text_secondary"]))
            self._tbl.setSpan(0, 0, 1, 5)
            self._tbl.setItem(0, 0, empty)
            return
        self._tbl.clearSpans()

        for row, s in enumerate(students):
            self._tbl.setRowHeight(row, 46)

            # Familiya
            last_item = QTableWidgetItem(s["last_name"])
            last_item.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
            self._tbl.setItem(row, 0, last_item)

            # Ism
            first_item = QTableWidgetItem(s["first_name"])
            first_item.setFont(QFont("Segoe UI", 12))
            self._tbl.setItem(row, 1, first_item)

            # Sinf — rangli badge
            cls_item = QTableWidgetItem(f"  {s['class_name']}  ")
            cls_item.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
            cls_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            cls_item.setForeground(QColor(COLORS["accent_light"]))
            self._tbl.setItem(row, 2, cls_item)

            # Telegram
            tg = s.get("parent_telegram_id") or ""
            tg_item = QTableWidgetItem("✅ " + tg if tg else t("as.tg_empty"))
            tg_item.setFont(QFont("Segoe UI", 11))
            tg_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            tg_item.setForeground(
                QColor(COLORS["success_light"]) if tg
                else QColor(COLORS["text_secondary"])
            )
            self._tbl.setItem(row, 3, tg_item)

            # Amallar
            cell_w = QWidget()
            cell_w.setStyleSheet("background: transparent;")
            cly = QHBoxLayout(cell_w)
            cly.setContentsMargins(6, 4, 6, 4)
            cly.setSpacing(6)
            cly.setAlignment(Qt.AlignmentFlag.AlignCenter)

            ed = QPushButton("✏️")
            ed.setFixedSize(38, 34)
            ed.setObjectName("table_action")
            ed.setToolTip("Tahrirlash")
            ed.clicked.connect(lambda _, sid=s["id"]: self._edit_student(sid))

            dl = QPushButton("🗑️")
            dl.setFixedSize(38, 34)
            dl.setObjectName("table_action_danger")
            dl.setToolTip("O'chirish")
            dl.clicked.connect(lambda _, sid=s["id"]: self._delete_student(sid))

            cly.addWidget(ed)
            cly.addWidget(dl)
            self._tbl.setCellWidget(row, 4, cell_w)

    # ── CRUD ──────────────────────────────────────────────────────────────────

    def _add_student(self):
        class_id = self._cls_combo.currentData()
        if not class_id:
            QMessageBox.information(self, "Sinf tanlang", t("as.no_class_warn"))
            return
        class_name = self._cls_combo.currentText().strip().lstrip("🟢⚫").strip()

        from .students_widget import StudentDialog
        dlg = StudentDialog(parent=self)
        dlg.setWindowTitle(f"O'quvchi qo'shish — {class_name}")
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                api.add_student(class_id, dlg.get_data())
                self._load()
            except APIError as e:
                QMessageBox.critical(self, "Xato", str(e))

    def _edit_student(self, sid: int):
        s = next((x for x in self._students if x["id"] == sid), None)
        if not s:
            return
        dlg = StudentDialog(student=s, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                api.update_student(sid, dlg.get_data())
                self._load()
            except APIError as e:
                QMessageBox.critical(self, "Xato", str(e))

    def _delete_student(self, sid: int):
        s = next((x for x in self._students if x["id"] == sid), None)
        if not s:
            return
        r = QMessageBox.question(
            self, "Tasdiqlash",
            t("as.del_confirm", last=s["last_name"], first=s["first_name"]),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if r == QMessageBox.StandardButton.Yes:
            try:
                api.delete_student(sid)
                self._load()
            except APIError as e:
                QMessageBox.critical(self, "Xato", str(e))

    # Tashqi refresh uchun
    def refresh(self):
        self._load_filters()
