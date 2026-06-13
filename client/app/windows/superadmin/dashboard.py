"""
Super Admin maxsus widgetlari: Foydalanuvchilar, Sozlamalar, Loglar.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QDialog,
    QFormLayout, QLineEdit, QComboBox, QMessageBox, QDialogButtonBox,
    QCheckBox, QGroupBox, QTextEdit, QFrame, QSpinBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor
from ...api_client import api, APIError
from ...styles import COLORS


# ── Users Widget ──────────────────────────────────────────────────────────────

class UserDialog(QDialog):
    def __init__(self, user: dict = None, parent=None):
        super().__init__(parent)
        self.user = user
        self.setWindowTitle("Foydalanuvchi qo'shish" if not user else "Foydalanuvchini tahrirlash")
        self.setMinimumWidth(420)
        self._setup_ui()
        if user:
            self._fill_data(user)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        form = QFormLayout()
        form.setSpacing(10)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("username (lotin harflar, raqamlar)")
        form.addRow("Username *:", self.username_input)

        self.fullname_input = QLineEdit()
        self.fullname_input.setPlaceholderText("Ism Familiya")
        form.addRow("To'liq ism *:", self.fullname_input)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Parol kiriting")
        form.addRow("Parol *:", self.password_input)

        self.role_combo = QComboBox()
        self.role_combo.addItem("O'qituvchi", "teacher")
        self.role_combo.addItem("Super Admin", "superadmin")
        form.addRow("Rol:", self.role_combo)

        self.telegram_input = QLineEdit()
        self.telegram_input.setPlaceholderText("Telegram chat ID (ixtiyoriy)")
        form.addRow("Telegram ID:", self.telegram_input)

        self.active_check = QCheckBox("Faol")
        self.active_check.setChecked(True)
        form.addRow("Holat:", self.active_check)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        if self.user:
            self.username_input.setEnabled(False)
            self.password_input.setPlaceholderText("Bo'sh qoldirsa parol o'zgarmaydi")

    def _fill_data(self, user: dict):
        self.username_input.setText(user.get("username", ""))
        self.fullname_input.setText(user.get("full_name", ""))
        idx = 1 if user.get("role") == "superadmin" else 0
        self.role_combo.setCurrentIndex(idx)
        self.telegram_input.setText(user.get("telegram_chat_id") or "")
        self.active_check.setChecked(user.get("is_active", True))

    def _validate_and_accept(self):
        if not self.user and not self.username_input.text().strip():
            QMessageBox.warning(self, "Xato", "Username bo'sh bo'lishi mumkin emas!")
            return
        if not self.fullname_input.text().strip():
            QMessageBox.warning(self, "Xato", "To'liq ism bo'sh bo'lishi mumkin emas!")
            return
        if not self.user and not self.password_input.text():
            QMessageBox.warning(self, "Xato", "Parol bo'sh bo'lishi mumkin emas!")
            return
        self.accept()

    def get_data(self) -> dict:
        data = {
            "full_name": self.fullname_input.text().strip(),
            "role": self.role_combo.currentData(),
            "is_active": self.active_check.isChecked(),
            "telegram_chat_id": self.telegram_input.text().strip() or None,
        }
        if not self.user:
            data["username"] = self.username_input.text().strip()
        if self.password_input.text():
            data["password"] = self.password_input.text()
        return data


class UsersWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.users = []
        self._setup_ui()
        self.refresh()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        toolbar = QHBoxLayout()
        title = QLabel("👥 Foydalanuvchilar")
        title.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))

        add_btn = QPushButton("+ Qo'shish")
        add_btn.setObjectName("success")
        add_btn.clicked.connect(self._add_user)

        refresh_btn = QPushButton("🔄")
        refresh_btn.setMaximumWidth(38)
        refresh_btn.setObjectName("secondary")
        refresh_btn.clicked.connect(self.refresh)

        toolbar.addWidget(title)
        toolbar.addStretch()
        toolbar.addWidget(add_btn)
        toolbar.addWidget(refresh_btn)
        layout.addLayout(toolbar)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Username", "To'liq ism", "Rol", "Telegram", "Holat", "Amallar"]
        )
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(0, 45)
        self.table.setColumnWidth(1, 130)
        self.table.setColumnWidth(3, 100)
        self.table.setColumnWidth(4, 130)
        self.table.setColumnWidth(5, 80)
        self.table.setColumnWidth(6, 120)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

    def refresh(self):
        try:
            self.users = api.get_users()
            self._render_table()
        except APIError as e:
            QMessageBox.warning(self, "Xato", str(e))

    def _render_table(self):
        self.table.setRowCount(len(self.users))
        role_labels = {"superadmin": "🔑 Super Admin", "teacher": "👨‍🏫 O'qituvchi"}
        for row, u in enumerate(self.users):
            self.table.setRowHeight(row, 44)
            self.table.setItem(row, 0, QTableWidgetItem(str(u["id"])))
            self.table.setItem(row, 1, QTableWidgetItem(u["username"]))
            self.table.setItem(row, 2, QTableWidgetItem(u["full_name"]))

            role_item = QTableWidgetItem(role_labels.get(u["role"], u["role"]))
            if u["role"] == "superadmin":
                role_item.setForeground(QColor(COLORS["accent_light"]))
            self.table.setItem(row, 3, role_item)

            self.table.setItem(row, 4, QTableWidgetItem(u.get("telegram_chat_id") or "—"))

            status = QTableWidgetItem("✅ Faol" if u["is_active"] else "🚫 Blok")
            status.setForeground(
                QColor(COLORS["success_light"]) if u["is_active"] else QColor(COLORS["danger_light"])
            )
            self.table.setItem(row, 5, status)

            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(4, 2, 4, 2)
            btn_layout.setSpacing(4)

            edit_btn = QPushButton("✏️")
            edit_btn.setFixedSize(30, 28)
            edit_btn.clicked.connect(lambda _, uid=u["id"]: self._edit_user(uid))

            del_btn = QPushButton("🗑️")
            del_btn.setFixedSize(30, 28)
            del_btn.setObjectName("danger")
            del_btn.clicked.connect(lambda _, uid=u["id"]: self._delete_user(uid))

            btn_layout.addWidget(edit_btn)
            btn_layout.addWidget(del_btn)
            self.table.setCellWidget(row, 6, btn_widget)

    def _add_user(self):
        dlg = UserDialog(parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                api.create_user(dlg.get_data())
                self.refresh()
            except APIError as e:
                QMessageBox.critical(self, "Xato", str(e))

    def _edit_user(self, user_id: int):
        user = next((u for u in self.users if u["id"] == user_id), None)
        if not user:
            return
        dlg = UserDialog(user=user, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                api.update_user(user_id, dlg.get_data())
                self.refresh()
            except APIError as e:
                QMessageBox.critical(self, "Xato", str(e))

    def _delete_user(self, user_id: int):
        reply = QMessageBox.question(self, "O'chirish",
                                     "Bu foydalanuvchini o'chirishni tasdiqlaysizmi?\n"
                                     "Uning barcha savollar va testlari ham o'chiriladi!",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                api.delete_user(user_id)
                self.refresh()
            except APIError as e:
                QMessageBox.critical(self, "Xato", str(e))


# ── Settings Widget ───────────────────────────────────────────────────────────

class SettingsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.refresh()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        title = QLabel("⚙️ Tizim sozlamalari")
        title.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        layout.addWidget(title)

        # Telegram sozlamalari
        tg_group = QGroupBox("🤖 Telegram Bot Sozlamalari")
        tg_layout = QFormLayout(tg_group)
        tg_layout.setSpacing(10)

        self.bot_token_input = QLineEdit()
        self.bot_token_input.setPlaceholderText("Bot token (BotFather'dan oling)")
        self.bot_token_input.setEchoMode(QLineEdit.EchoMode.Password)
        tg_layout.addRow("Bot Token:", self.bot_token_input)

        self.notify_check = QCheckBox("O'qituvchiga natijalarni yuborish")
        self.notify_check.setChecked(True)
        tg_layout.addRow("", self.notify_check)

        tg_help = QLabel(
            "ℹ️ @BotFather orqali bot yarating, tokenni kiriting.\n"
            "O'qituvchi Telegram chat ID'sini profil sozlamalarida kiriting."
        )
        tg_help.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px;")
        tg_help.setWordWrap(True)
        tg_layout.addRow("", tg_help)

        test_tg_btn = QPushButton("🔔 Telegram test xabari yuborish")
        test_tg_btn.setObjectName("secondary")
        test_tg_btn.clicked.connect(self._test_telegram)
        tg_layout.addRow("", test_tg_btn)

        layout.addWidget(tg_group)

        # Save button
        save_btn = QPushButton("💾 Sozlamalarni saqlash")
        save_btn.setObjectName("success")
        save_btn.clicked.connect(self._save_settings)
        layout.addWidget(save_btn)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet(f"color: {COLORS['success_light']};")
        layout.addWidget(self.status_label)

        layout.addStretch()

    def refresh(self):
        try:
            settings = api.get_settings()
            token = settings.get("telegram_bot_token", "")
            if token:
                self.bot_token_input.setText(token)
            notify = settings.get("telegram_notify_teacher", "true").lower() == "true"
            self.notify_check.setChecked(notify)
        except APIError:
            pass

    def _save_settings(self):
        try:
            token = self.bot_token_input.text().strip()
            if token:
                api.save_setting("telegram_bot_token", token)
            api.save_setting("telegram_notify_teacher", str(self.notify_check.isChecked()).lower())
            self.status_label.setText("✅ Sozlamalar saqlandi!")
        except APIError as e:
            self.status_label.setText(f"❌ Xato: {e}")

    def _test_telegram(self):
        try:
            settings = api.get_settings()
            token = settings.get("telegram_bot_token", "")
            if not token:
                QMessageBox.warning(self, "Xato", "Bot token kiritilmagan!")
                return
            QMessageBox.information(self, "Test",
                                    "Test xabari yuborilmoqda...\n"
                                    "O'qituvchi profilida Telegram ID bo'lishi kerak.")
        except APIError as e:
            QMessageBox.critical(self, "Xato", str(e))


# ── Logs Widget ───────────────────────────────────────────────────────────────

class LogsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.refresh()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        toolbar = QHBoxLayout()
        title = QLabel("📋 Audit Loglar")
        title.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))

        refresh_btn = QPushButton("🔄 Yangilash")
        refresh_btn.setObjectName("secondary")
        refresh_btn.clicked.connect(self.refresh)

        toolbar.addWidget(title)
        toolbar.addStretch()
        toolbar.addWidget(refresh_btn)
        layout.addLayout(toolbar)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Foydalanuvchi", "Harakat", "Tafsilot", "IP", "Vaqt"]
        )
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(0, 45)
        self.table.setColumnWidth(1, 120)
        self.table.setColumnWidth(2, 130)
        self.table.setColumnWidth(4, 120)
        self.table.setColumnWidth(5, 150)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

    def refresh(self):
        try:
            logs = api.get_audit_logs()
            self.table.setRowCount(len(logs))
            for row, log in enumerate(logs):
                self.table.setRowHeight(row, 38)
                items = [
                    str(log.get("id", "")),
                    str(log.get("user_id") or "—"),
                    log.get("action", ""),
                    log.get("details") or "—",
                    log.get("ip_address") or "—",
                    log.get("timestamp", "")[:19].replace("T", " "),
                ]
                for col, val in enumerate(items):
                    item = QTableWidgetItem(val)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.table.setItem(row, col, item)
        except APIError as e:
            QMessageBox.warning(self, "Xato", str(e))
