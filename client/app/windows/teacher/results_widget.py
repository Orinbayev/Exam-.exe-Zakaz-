"""
Natijalar ko'rinishi - o'quvchilar natijalari jadvali va eksport.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog,
    QMessageBox, QLineEdit, QComboBox
)
from PyQt6.QtCore import Qt
from ...worker import ApiWorker
from PyQt6.QtGui import QFont, QColor
from ...api_client import api, APIError
from ...styles import COLORS
import os


class ResultsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.results = []
        self._setup_ui()
        self.refresh()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        toolbar = QHBoxLayout()
        title = QLabel("📊 Natijalar")
        title.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Ism/familiya qidirish...")
        self.search_input.setMaximumWidth(200)
        self.search_input.textChanged.connect(self._apply_filter)

        self.filter_combo = QComboBox()
        self.filter_combo.setMaximumWidth(140)
        self.filter_combo.addItems(["Barchasi", "O'tdi", "Yiqildi"])
        self.filter_combo.currentIndexChanged.connect(self._apply_filter)

        export_btn = QPushButton("📥 Excel export")
        export_btn.setObjectName("success")
        export_btn.clicked.connect(self._export_excel)

        refresh_btn = QPushButton("🔄")
        refresh_btn.setMaximumWidth(38)
        refresh_btn.setObjectName("secondary")
        refresh_btn.clicked.connect(self.refresh)

        toolbar.addWidget(title)
        toolbar.addStretch()
        toolbar.addWidget(self.search_input)
        toolbar.addWidget(self.filter_combo)
        toolbar.addWidget(export_btn)
        toolbar.addWidget(refresh_btn)
        layout.addLayout(toolbar)

        # Summary cards
        self.summary_layout = QHBoxLayout()
        self.total_label = self._make_card("Jami", "0", COLORS["primary"])
        self.pass_label = self._make_card("O'tdi", "0", COLORS["success"])
        self.fail_label = self._make_card("Yiqildi", "0", COLORS["danger"])
        self.avg_label = self._make_card("O'rtacha", "0%", COLORS["accent"])
        layout.addLayout(self.summary_layout)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "ID", "Sana", "Ism", "Familiya", "Sinf",
            "Test", "To'g'ri", "Foiz", "Baho", "Natija"
        ])
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(0, 45)
        self.table.setColumnWidth(1, 130)
        self.table.setColumnWidth(2, 100)
        self.table.setColumnWidth(3, 100)
        self.table.setColumnWidth(4, 65)
        self.table.setColumnWidth(6, 80)
        self.table.setColumnWidth(7, 75)
        self.table.setColumnWidth(8, 60)
        self.table.setColumnWidth(9, 85)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setSortingEnabled(True)
        layout.addWidget(self.table)

    def _make_card(self, title: str, value: str, color: str) -> QLabel:
        from PyQt6.QtWidgets import QFrame
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: 10px;
                padding: 12px;
            }}
        """)
        frame.setMinimumHeight(70)
        inner = QVBoxLayout(frame)
        inner.setContentsMargins(12, 8, 12, 8)

        val_label = QLabel(value)
        val_label.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        val_label.setStyleSheet("color: white; background: transparent;")

        title_label = QLabel(title)
        title_label.setStyleSheet("color: rgba(255,255,255,0.8); font-size: 12px; background: transparent;")

        inner.addWidget(val_label)
        inner.addWidget(title_label)
        self.summary_layout.addWidget(frame)
        return val_label

    def refresh(self):
        self._w_results = ApiWorker(api.get_results)
        self._w_results.done.connect(self._apply_results)
        self._w_results.error.connect(lambda e: QMessageBox.warning(self, "Xato", e))
        self._w_results.start()

    def _apply_results(self, results):
        self.results = results
        self._update_summary()
        self._apply_filter()

    def _update_summary(self):
        total = len(self.results)
        passed = sum(1 for r in self.results if r.get("is_passed"))
        failed = total - passed
        scores = [r.get("score_percent", 0) for r in self.results]
        avg = sum(scores) / len(scores) if scores else 0

        self.total_label.setText(str(total))
        self.pass_label.setText(str(passed))
        self.fail_label.setText(str(failed))
        self.avg_label.setText(f"{avg:.1f}%")

    def _apply_filter(self):
        search = self.search_input.text().lower()
        filter_val = self.filter_combo.currentText()

        filtered = self.results
        if search:
            filtered = [r for r in filtered if
                        search in r.get("student_name", "").lower() or
                        search in r.get("student_lastname", "").lower()]
        if filter_val == "O'tdi":
            filtered = [r for r in filtered if r.get("is_passed")]
        elif filter_val == "Yiqildi":
            filtered = [r for r in filtered if not r.get("is_passed")]

        self._render_table(filtered)

    def _render_table(self, results: list):
        self.table.setRowCount(len(results))
        for row, r in enumerate(results):
            self.table.setRowHeight(row, 42)
            date_str = (r.get("end_time") or r.get("start_time") or "")[:16].replace("T", " ")

            items = [
                str(r.get("id", "")),
                date_str,
                r.get("student_name", ""),
                r.get("student_lastname", ""),
                r.get("student_class", ""),
                r.get("test_name", "—"),
                f"{r.get('correct_count', 0)}/{r.get('total_questions', 0)}",
                f"{r.get('score_percent', 0):.1f}%",
                r.get("grade", "—"),
                "✅ O'tdi" if r.get("is_passed") else "❌ Yiqildi",
            ]

            for col, val in enumerate(items):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if col == 9:
                    if r.get("is_passed"):
                        item.setForeground(QColor(COLORS["success_light"]))
                    else:
                        item.setForeground(QColor(COLORS["danger_light"]))
                self.table.setItem(row, col, item)

    def _export_excel(self):
        try:
            excel_bytes = api.export_excel()
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Excel faylni saqlash", "natijalar.xlsx",
                "Excel Files (*.xlsx)"
            )
            if file_path:
                with open(file_path, "wb") as f:
                    f.write(excel_bytes)
                QMessageBox.information(self, "Tayyor", f"Excel fayl saqlandi:\n{file_path}")
                # Faylni ochish
                os.startfile(file_path) if os.name == "nt" else None
        except APIError as e:
            QMessageBox.critical(self, "Xato", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Xato", f"Saqlashda xato: {e}")
