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
        from PyQt6.QtWidgets import QScrollArea

        outer_lay = QVBoxLayout(self)
        outer_lay.setContentsMargins(0, 0, 0, 0)
        outer_lay.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        inner = QWidget()
        inner.setStyleSheet("background: transparent;")
        root = QVBoxLayout(inner)
        root.setContentsMargins(2, 2, 14, 20)
        root.setSpacing(16)

        # ── Page header ───────────────────────────────────────────────────────
        hdr = QHBoxLayout()
        title = QLabel(t("set.title"))
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet("background: transparent;")

        refresh_btn = QPushButton("🔄  " + t("set.refresh"))
        refresh_btn.setObjectName("secondary")
        refresh_btn.setFixedHeight(38)
        refresh_btn.clicked.connect(self.refresh)

        hdr.addWidget(title)
        hdr.addStretch()
        hdr.addWidget(refresh_btn)
        root.addLayout(hdr)

        # ═════════════════════════════════════════════════════════════════════
        # Card 1 — Telegram Bot
        # ═════════════════════════════════════════════════════════════════════
        tg_frame, tg_lay = _settings_card("🤖", t("set.tg_card"), COLORS["primary_light"])

        # — Token label
        token_lbl = QLabel(t("set.token_lbl"))
        token_lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        token_lbl.setStyleSheet(
            f"color: {COLORS['text_secondary']}; background: transparent;"
        )
        tg_lay.addWidget(token_lbl)

        # — Token input + show/hide eye
        token_row = QHBoxLayout()
        token_row.setSpacing(8)

        self.bot_token_input = QLineEdit()
        self.bot_token_input.setPlaceholderText(t("set.token_ph"))
        self.bot_token_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.bot_token_input.setFixedHeight(42)
        self.bot_token_input.setStyleSheet(f"""
            QLineEdit {{
                background: {COLORS['bg_dark']};
                color: white;
                border: 1.5px solid {COLORS['border']};
                border-radius: 9px;
                padding: 0 14px;
                font-size: 13px;
            }}
            QLineEdit:focus {{ border: 2px solid {COLORS['primary_light']}; }}
        """)

        show_btn = QPushButton("👁")
        show_btn.setFixedSize(42, 42)
        show_btn.setCheckable(True)
        show_btn.setToolTip(t("set.token_tip"))
        show_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['bg_light']};
                border: 1.5px solid {COLORS['border']};
                border-radius: 9px;
                font-size: 16px;
            }}
            QPushButton:hover {{ background: {COLORS['primary']}; border-color: {COLORS['primary_light']}; }}
            QPushButton:checked {{ background: {COLORS['primary']}; border-color: {COLORS['primary_light']}; }}
        """)
        show_btn.toggled.connect(
            lambda on: self.bot_token_input.setEchoMode(
                QLineEdit.EchoMode.Normal if on else QLineEdit.EchoMode.Password
            )
        )
        token_row.addWidget(self.bot_token_input)
        token_row.addWidget(show_btn)
        tg_lay.addLayout(token_row)

        # — Notification checkbox in a styled pill
        notif_pill = QFrame()
        notif_pill.setStyleSheet(f"""
            QFrame {{
                background: rgba(21, 101, 192, 0.12);
                border: 1px solid rgba(66, 165, 245, 0.28);
                border-radius: 9px;
            }}
        """)
        notif_pill_lay = QHBoxLayout(notif_pill)
        notif_pill_lay.setContentsMargins(14, 10, 14, 10)
        notif_pill_lay.setSpacing(10)

        notif_ico = QLabel("🔔")
        notif_ico.setFont(QFont("Segoe UI Emoji", 13))
        notif_ico.setStyleSheet("background: transparent;")

        self.notify_check = QCheckBox(t("set.notif_chk"))
        self.notify_check.setChecked(True)
        self.notify_check.setFont(QFont("Segoe UI", 11))
        self.notify_check.setStyleSheet("background: transparent; color: white;")

        notif_pill_lay.addWidget(notif_ico)
        notif_pill_lay.addWidget(self.notify_check)
        notif_pill_lay.addStretch()
        tg_lay.addWidget(notif_pill)

        # — Hint
        hint = QLabel("ℹ️  " + t("set.tg_hint"))
        hint.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: 11px; background: transparent;"
        )
        hint.setWordWrap(True)
        tg_lay.addWidget(hint)

        # — Test button
        test_btn = QPushButton("📨  " + t("set.tg_test_btn"))
        test_btn.setFixedHeight(38)
        test_btn.setMaximumWidth(280)
        test_btn.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        test_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['bg_light']};
                color: white;
                border: 1.5px solid {COLORS['border']};
                border-radius: 9px;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: {COLORS['primary']};
                border-color: {COLORS['primary_light']};
            }}
        """)
        test_btn.clicked.connect(self._test_telegram)
        tg_lay.addWidget(test_btn)

        root.addWidget(tg_frame)

        # ═════════════════════════════════════════════════════════════════════
        # Card 2 — Ota-onalar uchun Telegram yo'riqnoma
        # ═════════════════════════════════════════════════════════════════════
        par_frame, par_lay = _settings_card(
            "👨‍👩‍👧", t("set.parent_card"), COLORS["accent_light"]
        )

        guide_title = QLabel(t("set.guide_title"))
        guide_title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        guide_title.setStyleSheet(
            f"color: {COLORS['accent_light']}; background: transparent;"
        )
        par_lay.addWidget(guide_title)

        _steps = [
            ("1", t("set.step1")),
            ("2", t("set.step2")),
            ("3", t("set.step3")),
            ("4", t("set.step4")),
        ]
        for num, step_txt in _steps:
            step_row = QHBoxLayout()
            step_row.setSpacing(12)
            step_row.setContentsMargins(0, 2, 0, 2)

            badge = QLabel(num)
            badge.setFixedSize(26, 26)
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            badge.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
            badge.setStyleSheet(f"""
                background: {COLORS['accent']};
                color: white;
                border-radius: 13px;
            """)

            txt = QLabel(step_txt)
            txt.setFont(QFont("Segoe UI", 11))
            txt.setStyleSheet(
                f"color: {COLORS['text_primary']}; background: transparent;"
            )
            txt.setWordWrap(True)

            step_row.addWidget(badge)
            step_row.addWidget(txt, stretch=1)
            par_lay.addLayout(step_row)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {COLORS['border']}; max-height: 1px; margin: 4px 0;")
        par_lay.addWidget(sep)

        note = QLabel("💡  " + t("set.parent_note"))
        note.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: 11px; background: transparent;"
        )
        note.setWordWrap(True)
        par_lay.addWidget(note)

        root.addWidget(par_frame)

        # ═════════════════════════════════════════════════════════════════════
        # Card 3 — Til / Язык
        # ═════════════════════════════════════════════════════════════════════
        lang_frame, lang_lay = _settings_card("🌐", t("lang.title"), COLORS["success_light"])

        lang_inner = QHBoxLayout()
        lang_inner.setSpacing(12)

        lang_lbl = QLabel(t("lang.label"))
        lang_lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        lang_lbl.setStyleSheet(
            f"color: {COLORS['text_secondary']}; background: transparent;"
        )
        lang_lbl.setFixedWidth(170)

        self._lang_combo = QComboBox()
        self._lang_combo.addItem(t("lang.uz"), "uz")
        self._lang_combo.addItem(t("lang.ru"), "ru")
        cur = get_lang()
        self._lang_combo.setCurrentIndex(0 if cur == "uz" else 1)
        self._lang_combo.setFixedHeight(38)
        self._lang_combo.setFixedWidth(200)

        lang_save_btn = QPushButton("✅  " + t("common.save").replace("✅  ", ""))
        lang_save_btn.setObjectName("success")
        lang_save_btn.setFixedSize(140, 38)
        lang_save_btn.clicked.connect(self._save_lang)

        lang_inner.addWidget(lang_lbl)
        lang_inner.addWidget(self._lang_combo)
        lang_inner.addSpacing(8)
        lang_inner.addWidget(lang_save_btn)
        lang_inner.addStretch()
        lang_lay.addLayout(lang_inner)

        self._lang_status = QLabel("")
        self._lang_status.setFont(QFont("Segoe UI", 11))
        self._lang_status.setStyleSheet(
            f"color: {COLORS['success_light']}; font-size: 11px; background: transparent;"
        )
        lang_lay.addWidget(self._lang_status)

        root.addWidget(lang_frame)

        # ═════════════════════════════════════════════════════════════════════
        # Card 4 — Bot Adminlar
        # ═════════════════════════════════════════════════════════════════════
        bot_admin_frame, bot_admin_lay = _settings_card(
            "🛡️", t("set.bot_admin_card"), COLORS["primary_light"]
        )

        bot_admin_lbl = QLabel(t("set.bot_admin_lbl"))
        bot_admin_lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        bot_admin_lbl.setStyleSheet(
            f"color: {COLORS['text_secondary']}; background: transparent;"
        )
        bot_admin_lay.addWidget(bot_admin_lbl)

        self.bot_admin_input = QTextEdit()
        self.bot_admin_input.setPlaceholderText(t("set.bot_admin_ph"))
        self.bot_admin_input.setFixedHeight(88)
        self.bot_admin_input.setStyleSheet(f"""
            QTextEdit {{
                background: {COLORS['bg_dark']};
                color: white;
                border: 1.5px solid {COLORS['border']};
                border-radius: 9px;
                padding: 8px 12px;
                font-size: 13px;
            }}
            QTextEdit:focus {{ border: 2px solid {COLORS['primary_light']}; }}
        """)
        bot_admin_lay.addWidget(self.bot_admin_input)

        bot_admin_hint = QLabel("ℹ️  " + t("set.bot_admin_hint"))
        bot_admin_hint.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: 11px; background: transparent;"
        )
        bot_admin_hint.setWordWrap(True)
        bot_admin_lay.addWidget(bot_admin_hint)

        bot_admin_save_row = QHBoxLayout()
        bot_admin_save_row.setSpacing(12)

        bot_admin_save_btn = QPushButton("💾  " + t("set.bot_admin_save"))
        bot_admin_save_btn.setFixedHeight(38)
        bot_admin_save_btn.setMaximumWidth(260)
        bot_admin_save_btn.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        bot_admin_save_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['bg_light']};
                color: white;
                border: 1.5px solid {COLORS['border']};
                border-radius: 9px;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: {COLORS['primary']};
                border-color: {COLORS['primary_light']};
            }}
        """)
        bot_admin_save_btn.clicked.connect(self._save_bot_admins)

        self._bot_admin_status = QLabel("")
        self._bot_admin_status.setFont(QFont("Segoe UI", 11))
        self._bot_admin_status.setStyleSheet(
            f"color: {COLORS['success_light']}; background: transparent;"
        )

        bot_admin_save_row.addWidget(bot_admin_save_btn)
        bot_admin_save_row.addWidget(self._bot_admin_status)
        bot_admin_save_row.addStretch()
        bot_admin_lay.addLayout(bot_admin_save_row)

        root.addWidget(bot_admin_frame)

        # ═════════════════════════════════════════════════════════════════════
        # Card 5 — Parolni o'zgartirish
        # ═════════════════════════════════════════════════════════════════════
        pwd_frame, pwd_lay = _settings_card("🔐", t("pwd.card"), COLORS["primary_light"])

        def _pwd_row(lbl_key, ph_key, echo=QLineEdit.EchoMode.Password):
            lbl = QLabel(t(lbl_key))
            lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
            inp = QLineEdit()
            inp.setPlaceholderText(t(ph_key))
            inp.setEchoMode(echo)
            inp.setFixedHeight(36)
            inp.setStyleSheet(f"""
                QLineEdit {{
                    background: {COLORS['input_bg']}; border: 1px solid {COLORS['border']};
                    border-radius: 8px; padding: 0 10px; color: {COLORS['text_primary']};
                }}
                QLineEdit:focus {{ border-color: {COLORS['primary']}; }}
            """)
            pwd_lay.addWidget(lbl)
            pwd_lay.addWidget(inp)
            return inp

        self._pwd_old  = _pwd_row("pwd.old",  "pwd.ph_old")
        self._pwd_new  = _pwd_row("pwd.new",  "pwd.ph_new")
        self._pwd_new2 = _pwd_row("pwd.new2", "pwd.ph_new2")

        self._pwd_status = QLabel("")
        self._pwd_status.setFont(QFont("Segoe UI", 10))
        self._pwd_status.setWordWrap(True)

        pwd_save_btn = QPushButton("💾  " + t("pwd.btn"))
        pwd_save_btn.setObjectName("secondary")
        pwd_save_btn.setFixedHeight(38)
        pwd_save_btn.clicked.connect(self._change_password)

        pwd_btn_row = QHBoxLayout()
        pwd_btn_row.addWidget(pwd_save_btn)
        pwd_btn_row.addWidget(self._pwd_status)
        pwd_btn_row.addStretch()
        pwd_lay.addLayout(pwd_btn_row)

        root.addWidget(pwd_frame)

        # ── Bottom save row ───────────────────────────────────────────────────
        save_sep = QFrame()
        save_sep.setFrameShape(QFrame.Shape.HLine)
        save_sep.setStyleSheet(f"color: {COLORS['border']}; max-height: 1px;")
        root.addWidget(save_sep)

        save_row = QHBoxLayout()
        save_row.setContentsMargins(0, 4, 0, 0)

        self.status_label = QLabel("")
        self.status_label.setFont(QFont("Segoe UI", 11))
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        save_btn = QPushButton("💾  " + t("set.save_btn"))
        save_btn.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        save_btn.setFixedSize(240, 44)
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['success']}, stop:1 #388E3C);
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #388E3C, stop:1 {COLORS['success_light']});
            }}
            QPushButton:pressed {{ background: {COLORS['success']}; }}
        """)
        save_btn.clicked.connect(self._save_settings)

        save_row.addWidget(self.status_label, stretch=1)
        save_row.addWidget(save_btn)
        root.addLayout(save_row)

        root.addStretch()

        scroll.setWidget(inner)
        outer_lay.addWidget(scroll)

    # ── Data ──────────────────────────────────────────────────────────────────

    def refresh(self):
        try:
            settings = api.get_settings()
            token = settings.get("telegram_bot_token", "")
            if token:
                self.bot_token_input.setText(token)
            notify = settings.get("telegram_notify_teacher", "true").lower() == "true"
            self.notify_check.setChecked(notify)
            # Bot admin IDs
            import json
            bot_admin_raw = settings.get("bot_admin_ids", "")
            if bot_admin_raw:
                try:
                    ids = json.loads(bot_admin_raw)
                    self.bot_admin_input.setPlainText("\n".join(ids))
                except Exception:
                    self.bot_admin_input.setPlainText(bot_admin_raw)
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

    def _save_bot_admins(self):
        import json
        raw = self.bot_admin_input.toPlainText().strip()
        ids = [line.strip() for line in raw.splitlines() if line.strip()]
        try:
            api.save_setting("bot_admin_ids", json.dumps(ids))
            self._bot_admin_status.setText(t("set.bot_admin_saved"))
            self._bot_admin_status.setStyleSheet(
                f"color: {COLORS['success_light']}; font-size: 11px; background: transparent;"
            )
        except APIError as e:
            self._bot_admin_status.setText(str(e))
            self._bot_admin_status.setStyleSheet(
                f"color: {COLORS['danger_light']}; font-size: 11px; background: transparent;"
            )

    def _change_password(self):
        old  = self._pwd_old.text()
        new  = self._pwd_new.text()
        new2 = self._pwd_new2.text()
        if not old or not new:
            self._pwd_status.setText(t("common.fill_all"))
            self._pwd_status.setStyleSheet(f"color: {COLORS['danger_light']}; background: transparent;")
            return
        if new != new2:
            self._pwd_status.setText(t("pwd.mismatch"))
            self._pwd_status.setStyleSheet(f"color: {COLORS['danger_light']}; background: transparent;")
            return
        try:
            api.change_my_password(old, new)
            self._pwd_old.clear(); self._pwd_new.clear(); self._pwd_new2.clear()
            self._pwd_status.setText(t("pwd.saved"))
            self._pwd_status.setStyleSheet(f"color: {COLORS['success_light']}; background: transparent;")
        except APIError as e:
            err = str(e)
            if "noto'g'ri" in err or "неверен" in err or "400" in err:
                self._pwd_status.setText(t("pwd.old_wrong"))
            else:
                self._pwd_status.setText(err)
            self._pwd_status.setStyleSheet(f"color: {COLORS['danger_light']}; background: transparent;")

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

        clear_btn = QPushButton(t("log.clear"))
        clear_btn.setObjectName("danger")
        clear_btn.clicked.connect(self._clear_logs)

        toolbar.addWidget(title)
        toolbar.addStretch()
        toolbar.addWidget(refresh_btn)
        toolbar.addWidget(clear_btn)
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

    def _clear_logs(self):
        ans = QMessageBox.question(
            self, t("log.clear"), t("log.clear_confirm"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if ans != QMessageBox.StandardButton.Yes:
            return
        try:
            res = api.clear_audit_logs()
            n = res.get("deleted", 0)
            self.table.setRowCount(0)
            QMessageBox.information(self, t("log.clear"), t("log.cleared").format(n=n))
        except APIError as e:
            QMessageBox.warning(self, t("common.error"), str(e))
