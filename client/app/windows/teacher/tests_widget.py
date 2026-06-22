"""
Testlar boshqaruvi widget - CRUD, savol qo'shish, nusxalash.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QDialog, QFormLayout,
    QLineEdit, QSpinBox, QDoubleSpinBox, QCheckBox, QTextEdit,
    QMessageBox, QHeaderView, QDialogButtonBox, QListWidget,
    QListWidgetItem, QSplitter, QFrame, QAbstractItemView,
    QGroupBox, QGridLayout, QScrollArea
)
from PyQt6.QtCore import Qt
from ...worker import ApiWorker
from PyQt6.QtGui import QFont, QColor
from ...api_client import api, APIError
from ...styles import COLORS


class GradeSettingsWidget(QWidget):
    GRADE_COLORS = {
        "5": "#4CAF50",
        "4": "#42A5F5",
        "3": "#FFB300",
        "2": "#EF5350",
    }
    DEFAULTS = {"5": 90.0, "4": 70.0, "3": 50.0, "2": 0.0}

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QGridLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(10)
        layout.setColumnMinimumWidth(0, 120)
        layout.setColumnStretch(1, 1)

        for col, text in enumerate(["Baho", "Minimum foiz (%)"]):
            hdr = QLabel(text)
            hdr.setStyleSheet(
                f"color: {COLORS['text_secondary']}; font-size: 12px; font-weight: 600;"
            )
            layout.addWidget(hdr, 0, col)

        self.grade_inputs = {}
        for i, grade in enumerate(["5", "4", "3", "2"], start=1):
            lbl = QLabel(f"  Baho {grade}")
            lbl.setStyleSheet(
                f"color: {self.GRADE_COLORS[grade]}; font-weight: bold; font-size: 13px;"
            )
            spin = QDoubleSpinBox()
            spin.setRange(0, 100)
            spin.setSuffix(" %")
            spin.setFixedHeight(34)
            spin.setValue(self.DEFAULTS[grade])
            layout.addWidget(lbl, i, 0)
            layout.addWidget(spin, i, 1)
            self.grade_inputs[grade] = spin

    def get_settings(self) -> dict:
        return {g: self.grade_inputs[g].value() for g in self.grade_inputs}

    def set_settings(self, settings: dict):
        for grade, value in settings.items():
            if grade in self.grade_inputs:
                self.grade_inputs[grade].setValue(float(value))


class TestDialog(QDialog):
    def __init__(self, test: dict = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Test yaratish" if not test else "Testni tahrirlash")
        self.setFixedWidth(560)
        self.setMinimumHeight(620)
        self.test = test
        self._setup_ui()
        if test:
            self._fill_data(test)

    # ── helpers ──────────────────────────────────────────────────────────────

    def _make_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: 13px; font-weight: 600;"
        )
        lbl.setMinimumWidth(138)
        lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        return lbl

    def _make_section_title(self, text: str) -> QLabel:
        lbl = QLabel(text.upper())
        lbl.setStyleSheet(
            f"color: {COLORS['primary_light']}; font-size: 11px; font-weight: bold; "
            f"letter-spacing: 1px;"
        )
        return lbl

    def _make_divider(self) -> QFrame:
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(f"color: {COLORS['border']}; margin: 2px 0;")
        return line

    # ── main UI ──────────────────────────────────────────────────────────────

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Header ────────────────────────────────────────────────────────
        header = QFrame()
        header.setObjectName("dialog_header")
        header.setFixedHeight(58)
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(24, 0, 24, 0)

        icon = "➕" if not self.test else "✏️"
        title_text = "Test yaratish" if not self.test else "Testni tahrirlash"
        title_lbl = QLabel(f"{icon}   {title_text}")
        title_lbl.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title_lbl.setStyleSheet(f"color: {COLORS['text_primary']};")
        h_lay.addWidget(title_lbl)
        root.addWidget(header)

        # ── Scroll area ───────────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        body = QWidget()
        body.setStyleSheet(f"background-color: {COLORS['bg_dark']};")
        body_lay = QVBoxLayout(body)
        body_lay.setContentsMargins(28, 20, 28, 20)
        body_lay.setSpacing(14)

        # ── Section 1: Asosiy ma'lumotlar ─────────────────────────────────
        body_lay.addWidget(self._make_section_title("Asosiy ma'lumotlar"))

        form1 = QFormLayout()
        form1.setSpacing(12)
        form1.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        form1.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Test nomini kiriting...")
        form1.addRow(self._make_label("Test nomi *:"), self.name_input)

        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("Test haqida qisqacha ma'lumot (ixtiyoriy)...")
        self.desc_input.setFixedHeight(68)
        form1.addRow(self._make_label("Tavsif:"), self.desc_input)

        body_lay.addLayout(form1)

        # ── Section 2: Sozlamalar ──────────────────────────────────────────
        body_lay.addWidget(self._make_divider())
        body_lay.addWidget(self._make_section_title("Sozlamalar"))

        form2 = QFormLayout()
        form2.setSpacing(12)
        form2.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.time_spin = QSpinBox()
        self.time_spin.setRange(1, 300)
        self.time_spin.setValue(30)
        self.time_spin.setSuffix(" daqiqa")
        self.time_spin.setFixedWidth(150)
        form2.addRow(self._make_label("Vaqt chegarasi:"), self.time_spin)

        self.pass_spin = QDoubleSpinBox()
        self.pass_spin.setRange(0, 100)
        self.pass_spin.setValue(60)
        self.pass_spin.setSuffix(" %")
        self.pass_spin.setFixedWidth(150)
        form2.addRow(self._make_label("O'tish foizi:"), self.pass_spin)

        body_lay.addLayout(form2)

        checks_frame = QFrame()
        checks_lay = QVBoxLayout(checks_frame)
        checks_lay.setContentsMargins(142, 4, 0, 0)
        checks_lay.setSpacing(8)
        self.shuffle_q = QCheckBox("  Savollarni aralashtirish")
        self.shuffle_a = QCheckBox("  Variantlarni aralashtirish")
        checks_lay.addWidget(self.shuffle_q)
        checks_lay.addWidget(self.shuffle_a)
        body_lay.addWidget(checks_frame)

        # ── Section 3: Baholash tizimi ────────────────────────────────────
        body_lay.addWidget(self._make_divider())
        body_lay.addWidget(self._make_section_title("Baholash tizimi"))

        grade_frame = QFrame()
        grade_frame.setStyleSheet(
            f"background-color: {COLORS['bg_medium']}; "
            f"border: 1px solid {COLORS['border']}; border-radius: 8px;"
        )
        grade_outer = QVBoxLayout(grade_frame)
        grade_outer.setContentsMargins(16, 12, 16, 12)
        self.grade_widget = GradeSettingsWidget()
        grade_outer.addWidget(self.grade_widget)
        body_lay.addWidget(grade_frame)

        body_lay.addStretch()
        scroll.setWidget(body)
        root.addWidget(scroll)

        # ── Footer ────────────────────────────────────────────────────────
        footer = QFrame()
        footer.setObjectName("dialog_footer")
        footer.setFixedHeight(60)
        f_lay = QHBoxLayout(footer)
        f_lay.setContentsMargins(24, 0, 24, 0)
        f_lay.setSpacing(10)
        f_lay.addStretch()

        cancel_btn = QPushButton("Bekor qilish")
        cancel_btn.setObjectName("secondary")
        cancel_btn.setFixedSize(130, 36)
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("  Saqlash")
        save_btn.setObjectName("success")
        save_btn.setFixedSize(130, 36)
        save_btn.clicked.connect(self._validate_and_accept)

        f_lay.addWidget(cancel_btn)
        f_lay.addWidget(save_btn)
        root.addWidget(footer)

    def _fill_data(self, test: dict):
        self.name_input.setText(test.get("name", ""))
        self.desc_input.setPlainText(test.get("description") or "")
        self.time_spin.setValue(test.get("time_limit", 30))
        self.pass_spin.setValue(test.get("pass_percent", 60))
        self.shuffle_q.setChecked(test.get("shuffle_questions", False))
        self.shuffle_a.setChecked(test.get("shuffle_answers", False))
        if test.get("grade_settings"):
            self.grade_widget.set_settings(test["grade_settings"])

    def _validate_and_accept(self):
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Xato", "Test nomi bo'sh bo'lishi mumkin emas!")
            return
        self.accept()

    def get_data(self) -> dict:
        return {
            "name": self.name_input.text().strip(),
            "description": self.desc_input.toPlainText().strip() or None,
            "time_limit": self.time_spin.value(),
            "pass_percent": self.pass_spin.value(),
            "shuffle_questions": self.shuffle_q.isChecked(),
            "shuffle_answers": self.shuffle_a.isChecked(),
            "grade_settings": self.grade_widget.get_settings(),
        }


class TestQuestionsDialog(QDialog):
    """Testga savol qo'shish dialogi."""
    def __init__(self, test: dict, parent=None):
        super().__init__(parent)
        self.test = test
        self.setWindowTitle(f"Savollarni boshqarish: {test['name']}")
        self.setMinimumSize(800, 550)
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        info = QLabel(f"📝 Test: <b>{self.test['name']}</b>  |  "
                      f"⏱ {self.test['time_limit']} daqiqa  |  "
                      f"✅ O'tish: {self.test['pass_percent']}%")
        info.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(info)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Chap: barcha savollar
        left_frame = QFrame()
        left_layout = QVBoxLayout(left_frame)
        left_layout.addWidget(QLabel("📚 Barcha savollar:"))

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Qidirish...")
        self.search_input.textChanged.connect(self._filter_all)
        left_layout.addWidget(self.search_input)

        self.all_questions_list = QListWidget()
        self.all_questions_list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        left_layout.addWidget(self.all_questions_list)

        add_btn = QPushButton("➜ Testga qo'shish")
        add_btn.setObjectName("success")
        add_btn.clicked.connect(self._add_selected)
        left_layout.addWidget(add_btn)

        splitter.addWidget(left_frame)

        # O'ng: testdagi savollar
        right_frame = QFrame()
        right_layout = QVBoxLayout(right_frame)
        right_layout.addWidget(QLabel("📋 Testdagi savollar:"))

        self.test_questions_list = QListWidget()
        right_layout.addWidget(self.test_questions_list)

        remove_btn = QPushButton("✕ Olib tashlash")
        remove_btn.setObjectName("danger")
        remove_btn.clicked.connect(self._remove_selected)
        right_layout.addWidget(remove_btn)

        splitter.addWidget(right_frame)
        splitter.setSizes([400, 380])
        layout.addWidget(splitter)

        close_btn = QPushButton("Yopish")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def _load_data(self):
        try:
            self.all_q = api.get_questions()
            test_detail = api.get_test_detail(self.test["id"])
            self.test_q_ids = {q["id"] for q in test_detail.get("questions", [])}
            self._refresh_lists()
        except APIError as e:
            QMessageBox.critical(self, "Xato", str(e))

    def _refresh_lists(self, search=""):
        self.all_questions_list.clear()
        for q in self.all_q:
            text = q["text"][:70]
            if search and search.lower() not in text.lower():
                continue
            item = QListWidgetItem(f"[{q['id']}] {text}")
            item.setData(Qt.ItemDataRole.UserRole, q["id"])
            if q["id"] in self.test_q_ids:
                item.setForeground(QColor(COLORS["success_light"]))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
            self.all_questions_list.addItem(item)

        self.test_questions_list.clear()
        test_detail = api.get_test_detail(self.test["id"])
        for q in test_detail.get("questions", []):
            item = QListWidgetItem(f"[{q['id']}] {q['text'][:60]}")
            item.setData(Qt.ItemDataRole.UserRole, q["id"])
            self.test_questions_list.addItem(item)

    def _filter_all(self):
        self._refresh_lists(search=self.search_input.text())

    def _add_selected(self):
        selected_ids = []
        for item in self.all_questions_list.selectedItems():
            q_id = item.data(Qt.ItemDataRole.UserRole)
            if q_id not in self.test_q_ids:
                selected_ids.append(q_id)
        if not selected_ids:
            return
        try:
            api.add_questions_to_test(self.test["id"], selected_ids)
            self.test_q_ids.update(selected_ids)
            self._refresh_lists()
        except APIError as e:
            QMessageBox.critical(self, "Xato", str(e))

    def _remove_selected(self):
        for item in self.test_questions_list.selectedItems():
            q_id = item.data(Qt.ItemDataRole.UserRole)
            try:
                api.remove_question_from_test(self.test["id"], q_id)
                self.test_q_ids.discard(q_id)
            except APIError as e:
                QMessageBox.critical(self, "Xato", str(e))
        self._refresh_lists()


class TestsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tests = []
        self._setup_ui()
        self.refresh()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        toolbar = QHBoxLayout()
        title = QLabel("📋 Testlar")
        title.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))

        add_btn = QPushButton("+ Test yaratish")
        add_btn.setObjectName("success")
        add_btn.clicked.connect(self._add_test)

        refresh_btn = QPushButton("🔄")
        refresh_btn.setMaximumWidth(38)
        refresh_btn.setObjectName("secondary")
        refresh_btn.clicked.connect(self.refresh)

        toolbar.addWidget(title)
        toolbar.addStretch()
        toolbar.addWidget(add_btn)
        toolbar.addWidget(refresh_btn)
        layout.addLayout(toolbar)

        self.stats_label = QLabel("")
        self.stats_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        layout.addWidget(self.stats_label)

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Test nomi", "Savollar", "Vaqt", "O'tish %", "Holat", "Sana", "Amallar"]
        )
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(2, 80)
        self.table.setColumnWidth(3, 90)
        self.table.setColumnWidth(4, 80)
        self.table.setColumnWidth(5, 80)
        self.table.setColumnWidth(6, 110)
        self.table.setColumnWidth(7, 210)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

    def refresh(self):
        self.stats_label.setText("Yuklanmoqda…")
        self._w_tests = ApiWorker(api.get_tests)
        self._w_tests.done.connect(self._apply_tests)
        self._w_tests.error.connect(lambda e: self.stats_label.setText(f"Xato: {e}"))
        self._w_tests.start()

    def _apply_tests(self, tests):
        self.tests = tests
        self._render_table()
        self.stats_label.setText(f"Jami: {len(self.tests)} ta test")

    def _render_table(self):
        self.table.setRowCount(len(self.tests))
        for row, t in enumerate(self.tests):
            self.table.setRowHeight(row, 50)
            self.table.setItem(row, 0, QTableWidgetItem(str(t["id"])))
            self.table.setItem(row, 1, QTableWidgetItem(t["name"]))
            self.table.setItem(row, 2, QTableWidgetItem(str(t.get("question_count", 0))))
            self.table.setItem(row, 3, QTableWidgetItem(f"{t['time_limit']} daq"))
            self.table.setItem(row, 4, QTableWidgetItem(f"{t['pass_percent']}%"))

            status_item = QTableWidgetItem("✅ Faol" if t["is_active"] else "⏸ Nofaol")
            status_item.setForeground(
                QColor(COLORS["success_light"]) if t["is_active"] else QColor(COLORS["danger_light"])
            )
            self.table.setItem(row, 5, status_item)
            self.table.setItem(row, 6, QTableWidgetItem(t.get("created_at", "")[:10]))

            btn_widget = QWidget()
            btn_widget.setStyleSheet("background: transparent;")
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(6, 5, 6, 5)
            btn_layout.setSpacing(5)
            btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            q_btn = QPushButton("📝")
            q_btn.setFixedSize(38, 32)
            q_btn.setObjectName("table_action")
            q_btn.setToolTip("Savollarni boshqarish")
            q_btn.clicked.connect(lambda _, tid=t["id"]: self._manage_questions(tid))

            edit_btn = QPushButton("✏️")
            edit_btn.setFixedSize(38, 32)
            edit_btn.setObjectName("table_action")
            edit_btn.setToolTip("Tahrirlash")
            edit_btn.clicked.connect(lambda _, tid=t["id"]: self._edit_test(tid))

            copy_btn = QPushButton("📋")
            copy_btn.setFixedSize(38, 32)
            copy_btn.setObjectName("table_action")
            copy_btn.setToolTip("Nusxalash")
            copy_btn.clicked.connect(lambda _, tid=t["id"]: self._copy_test(tid))

            del_btn = QPushButton("🗑️")
            del_btn.setFixedSize(38, 32)
            del_btn.setObjectName("table_action_danger")
            del_btn.setToolTip("O'chirish")
            del_btn.clicked.connect(lambda _, tid=t["id"]: self._delete_test(tid))

            btn_layout.addWidget(q_btn)
            btn_layout.addWidget(edit_btn)
            btn_layout.addWidget(copy_btn)
            btn_layout.addWidget(del_btn)
            self.table.setCellWidget(row, 7, btn_widget)

    def _add_test(self):
        dlg = TestDialog(parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                api.create_test(dlg.get_data())
                self.refresh()
            except APIError as e:
                QMessageBox.critical(self, "Xato", str(e))

    def _edit_test(self, test_id: int):
        test = next((t for t in self.tests if t["id"] == test_id), None)
        if not test:
            return
        dlg = TestDialog(test=test, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                api.update_test(test_id, dlg.get_data())
                self.refresh()
            except APIError as e:
                QMessageBox.critical(self, "Xato", str(e))

    def _manage_questions(self, test_id: int):
        test = next((t for t in self.tests if t["id"] == test_id), None)
        if not test:
            return
        dlg = TestQuestionsDialog(test=test, parent=self)
        dlg.exec()
        self.refresh()

    def _copy_test(self, test_id: int):
        test = next((t for t in self.tests if t["id"] == test_id), None)
        name = test["name"] if test else f"#{test_id}"
        reply = QMessageBox.question(
            self, "Nusxalash",
            f"'{name}' testini nusxalashni tasdiqlaysizmi?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            api.copy_test(test_id)
            self.refresh()
        except APIError as e:
            QMessageBox.critical(self, "Xato", str(e))

    def _delete_test(self, test_id: int):
        reply = QMessageBox.question(self, "O'chirish",
                                     "Bu testni o'chirishni tasdiqlaysizmi?\n"
                                     "Barcha natijalar ham o'chiriladi!",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                api.delete_test(test_id)
                self.refresh()
            except APIError as e:
                QMessageBox.critical(self, "Xato", str(e))
