"""
Super Admin maxsus widgetlari: Foydalanuvchilar, Sozlamalar, Loglar.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QDialog,
    QFormLayout, QLineEdit, QComboBox, QMessageBox, QDialogButtonBox,
    QCheckBox, QGroupBox, QTextEdit, QFrame, QSpinBox, QToolButton
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor
from ...api_client import api, APIError
from ...styles import COLORS
from ...i18n import t, get_lang, set_lang


# ── Users Widget ──────────────────────────────────────────────────────────────

class UserDialog(QDialog):
    def __init__(self, user: dict = None, parent=None, default_role: str = "teacher"):
        super().__init__(parent)
        self.user = user
        self._default_role = default_role
        is_edit = bool(user)
        if is_edit:
            role_name = t("udlg.role_teacher") if (user or {}).get("role", default_role) == "teacher" else t("udlg.role_admin")
            self.setWindowTitle(t("udlg.title_edit", role=role_name))
        else:
            self.setWindowTitle(t("udlg.title_teacher") if default_role == "teacher"
                                else t("udlg.title_user"))
        self.setMinimumWidth(460)
        self._setup_ui()
        if user:
            self._fill_data(user)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(24, 20, 24, 20)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText(t("udlg.ph_login"))
        self.username_input.setFixedHeight(36)
        form.addRow(t("udlg.lbl_login"), self.username_input)

        self.fullname_input = QLineEdit()
        self.fullname_input.setPlaceholderText(t("udlg.ph_fullname"))
        self.fullname_input.setFixedHeight(36)
        form.addRow(t("udlg.lbl_fullname"), self.fullname_input)

        pwd_row = QHBoxLayout()
        pwd_row.setSpacing(6)
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText(t("udlg.ph_password"))
        self.password_input.setFixedHeight(36)
        eye_btn = QToolButton()
        eye_btn.setText("👁")
        eye_btn.setFixedSize(36, 36)
        eye_btn.setCheckable(True)
        eye_btn.setToolTip(t("udlg.tip_eye"))
        eye_btn.toggled.connect(
            lambda on: self.password_input.setEchoMode(
                QLineEdit.EchoMode.Normal if on else QLineEdit.EchoMode.Password
            )
        )
        pwd_row.addWidget(self.password_input)
        pwd_row.addWidget(eye_btn)
        form.addRow(t("udlg.lbl_password"), pwd_row)

        pwd2_row = QHBoxLayout()
        pwd2_row.setSpacing(6)
        self.password2_input = QLineEdit()
        self.password2_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password2_input.setPlaceholderText(t("udlg.ph_pwd2"))
        self.password2_input.setFixedHeight(36)
        eye_btn2 = QToolButton()
        eye_btn2.setText("👁")
        eye_btn2.setFixedSize(36, 36)
        eye_btn2.setCheckable(True)
        eye_btn2.toggled.connect(
            lambda on: self.password2_input.setEchoMode(
                QLineEdit.EchoMode.Normal if on else QLineEdit.EchoMode.Password
            )
        )
        pwd2_row.addWidget(self.password2_input)
        pwd2_row.addWidget(eye_btn2)
        form.addRow(t("udlg.lbl_pwd2"), pwd2_row)

        self.role_combo = QComboBox()
        self.role_combo.addItem(t("udlg.combo_teacher"), "teacher")
        self.role_combo.addItem(t("udlg.combo_admin"), "superadmin")
        self.role_combo.setFixedHeight(36)
        if self._default_role == "superadmin":
            self.role_combo.setCurrentIndex(1)
        form.addRow(t("udlg.lbl_role"), self.role_combo)

        self.telegram_input = QLineEdit()
        self.telegram_input.setPlaceholderText(t("udlg.ph_telegram"))
        self.telegram_input.setFixedHeight(36)
        form.addRow(t("udlg.lbl_telegram"), self.telegram_input)

        self.active_check = QCheckBox(t("udlg.chk_active"))
        self.active_check.setChecked(True)
        form.addRow(t("udlg.lbl_active"), self.active_check)

        layout.addLayout(form)

        if self.user:
            self.username_input.setEnabled(False)
            self.password_input.setPlaceholderText(t("udlg.ph_pwd_edit"))
            self.password2_input.setPlaceholderText(t("udlg.ph_pwd_edit"))

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText(t("common.save"))
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(t("common.cancel"))
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _fill_data(self, user: dict):
        self.username_input.setText(user.get("username", ""))
        self.fullname_input.setText(user.get("full_name", ""))
        idx = 1 if user.get("role") == "superadmin" else 0
        self.role_combo.setCurrentIndex(idx)
        self.telegram_input.setText(user.get("telegram_chat_id") or "")
        self.active_check.setChecked(user.get("is_active", True))

    def _validate_and_accept(self):
        warn_title = "⚠ " + t("common.warning")
        if not self.user and not self.username_input.text().strip():
            QMessageBox.warning(self, warn_title, t("udlg.err_login"))
            self.username_input.setFocus()
            return
        if not self.fullname_input.text().strip():
            QMessageBox.warning(self, warn_title, t("udlg.err_fullname"))
            self.fullname_input.setFocus()
            return
        pwd = self.password_input.text()
        pwd2 = self.password2_input.text()
        if not self.user and not pwd:
            QMessageBox.warning(self, warn_title, t("udlg.err_pwd_req"))
            self.password_input.setFocus()
            return
        if pwd and len(pwd) < 4:
            QMessageBox.warning(self, warn_title, t("udlg.err_pwd_short"))
            self.password_input.setFocus()
            return
        if pwd and pwd != pwd2:
            QMessageBox.warning(self, warn_title, t("udlg.err_pwd_mismatch"))
            self.password2_input.setFocus()
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
        title = QLabel(t("usr.title"))
        title.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))

        add_teacher_btn = QPushButton(t("usr.add_teacher"))
        add_teacher_btn.setObjectName("success")
        add_teacher_btn.setFixedHeight(36)
        add_teacher_btn.clicked.connect(self._add_teacher)

        add_admin_btn = QPushButton(t("usr.add_admin"))
        add_admin_btn.setObjectName("secondary")
        add_admin_btn.setFixedHeight(36)
        add_admin_btn.clicked.connect(self._add_user)

        refresh_btn = QPushButton("🔄")
        refresh_btn.setMaximumWidth(38)
        refresh_btn.setFixedHeight(36)
        refresh_btn.setObjectName("secondary")
        refresh_btn.clicked.connect(self.refresh)

        toolbar.addWidget(title)
        toolbar.addStretch()
        toolbar.addWidget(add_teacher_btn)
        toolbar.addWidget(add_admin_btn)
        toolbar.addWidget(refresh_btn)
        layout.addLayout(toolbar)

        hint = QLabel(t("usr.hint"))
        hint.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px;")
        layout.addWidget(hint)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            t("usr.col_id"), t("usr.col_username"), t("usr.col_fullname"),
            t("usr.col_role"), t("usr.col_telegram"), t("usr.col_status"), t("usr.col_actions")
        ])
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(0, 45)
        self.table.setColumnWidth(1, 130)
        self.table.setColumnWidth(3, 100)
        self.table.setColumnWidth(4, 130)
        self.table.setColumnWidth(5, 80)
        self.table.setColumnWidth(6, 110)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

    def refresh(self):
        try:
            self.users = api.get_users()
            self._render_table()
        except APIError as e:
            QMessageBox.warning(self, t("common.error"), str(e))

    def _render_table(self):
        self.table.setRowCount(len(self.users))
        role_labels = {"superadmin": t("usr.role_admin"), "teacher": t("usr.role_teacher")}
        for row, u in enumerate(self.users):
            self.table.setRowHeight(row, 50)
            self.table.setItem(row, 0, QTableWidgetItem(str(u["id"])))
            self.table.setItem(row, 1, QTableWidgetItem(u["username"]))
            self.table.setItem(row, 2, QTableWidgetItem(u["full_name"]))

            role_item = QTableWidgetItem(role_labels.get(u["role"], u["role"]))
            if u["role"] == "superadmin":
                role_item.setForeground(QColor(COLORS["accent_light"]))
            self.table.setItem(row, 3, role_item)

            self.table.setItem(row, 4, QTableWidgetItem(u.get("telegram_chat_id") or "—"))

            status = QTableWidgetItem(t("usr.status_active") if u["is_active"] else t("usr.status_blocked"))
            status.setForeground(
                QColor(COLORS["success_light"]) if u["is_active"] else QColor(COLORS["danger_light"])
            )
            self.table.setItem(row, 5, status)

            btn_widget = QWidget()
            btn_widget.setStyleSheet("background: transparent;")
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(6, 5, 6, 5)
            btn_layout.setSpacing(6)
            btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            edit_btn = QPushButton("✏️")
            edit_btn.setFixedSize(38, 32)
            edit_btn.setObjectName("table_action")
            edit_btn.setToolTip(t("usr.tip_edit"))
            edit_btn.clicked.connect(lambda _, uid=u["id"]: self._edit_user(uid))

            del_btn = QPushButton("🗑️")
            del_btn.setFixedSize(38, 32)
            del_btn.setObjectName("table_action_danger")
            del_btn.setToolTip(t("usr.tip_del"))
            del_btn.clicked.connect(lambda _, uid=u["id"]: self._delete_user(uid))

            btn_layout.addWidget(edit_btn)
            btn_layout.addWidget(del_btn)
            self.table.setCellWidget(row, 6, btn_widget)

    def _add_teacher(self):
        dlg = UserDialog(parent=self, default_role="teacher")
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                data = dlg.get_data()
                api.create_user(data)
                self.refresh()
                QMessageBox.information(
                    self, t("usr.created_title"),
                    t("usr.created_msg", username=data.get("username", ""))
                )
            except APIError as e:
                QMessageBox.critical(self, t("common.error"), str(e))

    def _add_user(self):
        dlg = UserDialog(parent=self, default_role="superadmin")
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                api.create_user(dlg.get_data())
                self.refresh()
            except APIError as e:
                QMessageBox.critical(self, t("common.error"), str(e))

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
                QMessageBox.critical(self, t("common.error"), str(e))

    def _delete_user(self, user_id: int):
        reply = QMessageBox.question(
            self, t("usr.del_title"), t("usr.del_q"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                api.delete_user(user_id)
                self.refresh()
            except APIError as e:
                QMessageBox.critical(self, t("common.error"), str(e))


# ── Settings Widget ───────────────────────────────────────────────────────────

def _settings_card(header_icon: str, header_text: str, header_color: str) -> tuple:
    """Returns (outer_frame, inner_layout) for a settings section card."""
    frame = QFrame()
    frame.setStyleSheet(f"""
        QFrame#settings_card {{
            background: {COLORS['card_bg']};
            border: 1px solid {COLORS['border']};
            border-radius: 14px;
        }}
    """)
    frame.setObjectName("settings_card")

    outer = QVBoxLayout(frame)
    outer.setContentsMargins(22, 16, 22, 18)
    outer.setSpacing(12)

    hdr = QHBoxLayout()
    icon_lbl = QLabel(header_icon)
    icon_lbl.setFont(QFont("Segoe UI Emoji", 17))
    icon_lbl.setStyleSheet("background: transparent; min-width: 0;")
    icon_lbl.setFixedWidth(28)

    title_lbl = QLabel(header_text)
    title_lbl.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
    title_lbl.setStyleSheet(
        f"color: {header_color}; background: transparent;"
    )

    hdr.addWidget(icon_lbl)
    hdr.addWidget(title_lbl)
    hdr.addStretch()
    outer.addLayout(hdr)

    div = QFrame()
    div.setFrameShape(QFrame.Shape.HLine)
    div.setStyleSheet(f"color: {COLORS['border']}; max-height: 1px;")
    outer.addWidget(div)

    return frame, outer


class SettingsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.refresh()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(16)

        # Page title + refresh button
        hdr = QHBoxLayout()
        title = QLabel(t("set.title"))
        title.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        refresh_btn = QPushButton(t("set.refresh"))
        refresh_btn.setObjectName("secondary")
        refresh_btn.clicked.connect(self.refresh)
        hdr.addWidget(title)
        hdr.addStretch()
        hdr.addWidget(refresh_btn)
        root.addLayout(hdr)

        # ── Card 1: Telegram Bot ─────────────────────────────────────────────
        tg_frame, tg_lay = _settings_card(
            "🤖", t("set.tg_card"), COLORS["primary_light"]
        )

        # Token row
        token_row = QHBoxLayout()
        token_lbl = QLabel(t("set.token_lbl"))
        token_lbl.setFixedWidth(100)
        token_lbl.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: 12px;"
            f" font-weight: 600; background: transparent;"
        )
        self.bot_token_input = QLineEdit()
        self.bot_token_input.setPlaceholderText(t("set.token_ph"))
        self.bot_token_input.setEchoMode(QLineEdit.EchoMode.Password)

        show_btn = QPushButton("👁")
        show_btn.setFixedSize(36, 36)
        show_btn.setObjectName("secondary")
        show_btn.setCheckable(True)
        show_btn.setToolTip(t("set.token_tip"))
        show_btn.toggled.connect(
            lambda on: self.bot_token_input.setEchoMode(
                QLineEdit.EchoMode.Normal if on else QLineEdit.EchoMode.Password
            )
        )
        token_row.addWidget(token_lbl)
        token_row.addWidget(self.bot_token_input)
        token_row.addWidget(show_btn)
        tg_lay.addLayout(token_row)

        # Notify teacher row
        notif_row = QHBoxLayout()
        notif_lbl = QLabel(t("set.notif_lbl"))
        notif_lbl.setFixedWidth(100)
        notif_lbl.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: 12px;"
            f" font-weight: 600; background: transparent;"
        )
        self.notify_check = QCheckBox(t("set.notif_chk"))
        self.notify_check.setChecked(True)
        notif_row.addWidget(notif_lbl)
        notif_row.addWidget(self.notify_check)
        notif_row.addStretch()
        tg_lay.addLayout(notif_row)

        hint = QLabel(t("set.tg_hint"))
        hint.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: 11px; background: transparent;"
        )
        hint.setWordWrap(True)
        tg_lay.addWidget(hint)

        test_btn_row = QHBoxLayout()
        test_btn = QPushButton(t("set.tg_test_btn"))
        test_btn.setObjectName("secondary")
        test_btn.clicked.connect(self._test_telegram)
        test_btn_row.addWidget(test_btn)
        test_btn_row.addStretch()
        tg_lay.addLayout(test_btn_row)

        root.addWidget(tg_frame)

        # ── Card 2: Parent Telegram Guide ────────────────────────────────────
        par_frame, par_lay = _settings_card(
            "👨‍👩‍👧", t("set.parent_card"), COLORS["accent_light"]
        )

        info_box = QFrame()
        info_box.setStyleSheet("""
            QFrame {
                background: rgba(255, 183, 0, 0.07);
                border: 1px solid rgba(255, 183, 0, 0.22);
                border-radius: 10px;
            }
        """)
        info_lay = QVBoxLayout(info_box)
        info_lay.setContentsMargins(14, 12, 14, 12)
        info_lay.setSpacing(8)

        guide_title = QLabel(t("set.guide_title"))
        guide_title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        guide_title.setStyleSheet(
            f"color: {COLORS['accent_light']}; background: transparent;"
        )
        info_lay.addWidget(guide_title)

        _steps = [
            ("1", t("set.step1")),
            ("2", t("set.step2")),
            ("3", t("set.step3")),
            ("4", t("set.step4")),
        ]
        for num, step_txt in _steps:
            row = QHBoxLayout()
            row.setSpacing(10)

            badge = QLabel(num)
            badge.setFixedSize(24, 24)
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            badge.setStyleSheet(f"""
                background: {COLORS['accent']};
                color: white;
                border-radius: 12px;
                font-size: 11px;
                font-weight: bold;
            """)

            txt = QLabel(step_txt)
            txt.setStyleSheet(
                f"color: {COLORS['text_primary']}; font-size: 12px; background: transparent;"
            )
            txt.setWordWrap(True)

            row.addWidget(badge)
            row.addWidget(txt, stretch=1)
            info_lay.addLayout(row)

        par_lay.addWidget(info_box)

        note = QLabel(t("set.parent_note"))
        note.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: 11px; background: transparent;"
        )
        note.setWordWrap(True)
        par_lay.addWidget(note)

        root.addWidget(par_frame)

        # ── Card 3: Til / Язык ────────────────────────────────────────────────
        lang_frame, lang_lay = _settings_card("🌐", t("lang.title"), COLORS["success_light"])

        lang_row = QHBoxLayout()
        lang_lbl = QLabel(t("lang.label"))
        lang_lbl.setFixedWidth(160)
        lang_lbl.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: 12px;"
            f" font-weight: 600; background: transparent;"
        )
        self._lang_combo = QComboBox()
        self._lang_combo.addItem(t("lang.uz"), "uz")
        self._lang_combo.addItem(t("lang.ru"), "ru")
        cur = get_lang()
        self._lang_combo.setCurrentIndex(0 if cur == "uz" else 1)
        lang_row.addWidget(lang_lbl)
        lang_row.addWidget(self._lang_combo)
        lang_row.addStretch()
        lang_lay.addLayout(lang_row)

        lang_save_btn = QPushButton("✅  " + t("common.save").replace("✅  ", ""))
        lang_save_btn.setObjectName("success")
        lang_save_btn.setFixedSize(160, 36)
        lang_save_btn.clicked.connect(self._save_lang)
        lang_lay.addWidget(lang_save_btn)

        self._lang_status = QLabel("")
        self._lang_status.setStyleSheet(
            f"color: {COLORS['success_light']}; font-size: 11px; background: transparent;"
        )
        lang_lay.addWidget(self._lang_status)

        root.addWidget(lang_frame)

        # ── Save row ─────────────────────────────────────────────────────────
        save_row = QHBoxLayout()
        save_row.addStretch()
        save_btn = QPushButton(t("set.save_btn"))
        save_btn.setObjectName("success")
        save_btn.setFixedSize(230, 40)
        save_btn.clicked.connect(self._save_settings)
        save_row.addWidget(save_btn)
        root.addLayout(save_row)

        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        root.addWidget(self.status_label)

        root.addStretch()

    # ── Data ──────────────────────────────────────────────────────────────────

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
            api.save_setting(
                "telegram_notify_teacher",
                str(self.notify_check.isChecked()).lower(),
            )
            self.status_label.setText(t("set.saved_ok"))
            self.status_label.setStyleSheet(f"color: {COLORS['success_light']}; font-size: 12px;")
        except APIError as e:
            self.status_label.setText(t("set.saved_err", e=e))
            self.status_label.setStyleSheet(f"color: {COLORS['danger_light']}; font-size: 12px;")

    def _save_lang(self):
        from PyQt6.QtCore import QTimer
        from PyQt6.QtWidgets import QApplication
        from ...main import open_dashboard
        from ..teacher.dashboard import TeacherDashboard

        lang = self._lang_combo.currentData()
        set_lang(lang)
        self._lang_status.setText(t("lang.saved"))

        def _reload():
            for w in list(QApplication.topLevelWidgets()):
                if isinstance(w, TeacherDashboard):
                    w.close()
                    break
            open_dashboard("superadmin")

        QTimer.singleShot(600, _reload)

    def _test_telegram(self):
        try:
            settings = api.get_settings()
            token = settings.get("telegram_bot_token", "")
            if not token:
                QMessageBox.warning(self, t("common.error"), t("set.tg_no_token"))
                return
            QMessageBox.information(self, t("set.tg_test_title"), t("set.tg_test_msg"))
        except APIError as e:
            QMessageBox.critical(self, t("common.error"), str(e))


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
        title = QLabel(t("log.title"))
        title.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))

        refresh_btn = QPushButton(t("log.refresh"))
        refresh_btn.setObjectName("secondary")
        refresh_btn.clicked.connect(self.refresh)

        toolbar.addWidget(title)
        toolbar.addStretch()
        toolbar.addWidget(refresh_btn)
        layout.addLayout(toolbar)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            t("log.col_id"), t("log.col_user"), t("log.col_action"),
            t("log.col_detail"), t("log.col_ip"), t("log.col_time")
        ])
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
            QMessageBox.warning(self, t("common.error"), str(e))
