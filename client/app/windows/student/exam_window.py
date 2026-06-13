"""
O'quvchi test oynasi - fullscreen, timer, animatsiyalar, ovoz.
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QProgressBar, QFrame, QMessageBox, QApplication
)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtSignal, QThread
from PyQt6.QtGui import QFont, QColor, QKeySequence, QShortcut, QPainter, QLinearGradient
import random


ANSWER_COLORS = {
    "A": ("#E53935", "#EF5350"),  # Qizil
    "B": ("#1565C0", "#1E88E5"),  # Ko'k
    "C": ("#2E7D32", "#43A047"),  # Yashil
    "D": ("#E65100", "#FB8C00"),  # To'q sariq
}

ANSWER_KEYS = {
    Qt.Key.Key_1: "A", Qt.Key.Key_F1: "A",
    Qt.Key.Key_2: "B", Qt.Key.Key_F2: "B",
    Qt.Key.Key_3: "C", Qt.Key.Key_F3: "C",
    Qt.Key.Key_4: "D", Qt.Key.Key_F4: "D",
}

MOTIVATIONAL_MESSAGES = [
    "Qo'lingizdan keladi! 💪",
    "Davom eting, zo'rsiz! ⭐",
    "Keyingi savolda yaxshiroq bo'ladi! 🌟",
    "Bilim - bu kuch! 📚",
    "Harakat qiling! 🎯",
    "Vaqtni bekor ketkazmang! ⏰",
]


def play_sound(sound_type: str):
    """Windows uchun ovoz effekti."""
    try:
        import winsound
        if sound_type == "correct":
            winsound.Beep(880, 150)  # High beep
        elif sound_type == "wrong":
            winsound.Beep(280, 300)  # Low beep
        elif sound_type == "finish":
            for freq in [523, 659, 784]:
                winsound.Beep(freq, 120)
    except Exception:
        pass  # Windows bo'lmasa yoki xato bo'lsa o'tkazib yuborish


class FinishThread(QThread):
    success = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, session_id: int, answers: dict):
        super().__init__()
        self.session_id = session_id
        self.answers = answers

    def run(self):
        from ...api_client import api, APIError
        try:
            result = api.finish_exam(self.session_id, self.answers)
            self.success.emit(result)
        except APIError as e:
            self.error.emit(str(e))


class AnswerButton(QPushButton):
    def __init__(self, letter: str, text: str, parent=None):
        super().__init__(parent)
        self.letter = letter
        self.answer_text = text
        self._normal_color, self._hover_color = ANSWER_COLORS[letter]
        self._selected = False
        self._correct = None  # None | True | False
        self._update_style()
        self.setMinimumHeight(70)
        self.setFont(QFont("Segoe UI", 14))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._setup_animation()

    def _setup_animation(self):
        self._anim = QPropertyAnimation(self, b"minimumHeight")
        self._anim.setDuration(100)

    def _update_style(self):
        if self._correct is True:
            bg = "#2E7D32"
            border = "#66BB6A"
        elif self._correct is False:
            bg = "#B71C1C"
            border = "#EF5350"
        elif self._selected:
            bg = self._hover_color
            border = "white"
        else:
            bg = self._normal_color
            border = "transparent"

        letter_bg = f"rgba(0,0,0,0.3)"
        self.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {bg}, stop:1 {self._hover_color});
                color: white;
                border: 3px solid {border};
                border-radius: 14px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
                text-align: left;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {self._hover_color}, stop:1 {self._normal_color});
                border: 3px solid white;
            }}
        """)

    def set_text_and_letter(self):
        self.setText(f"   {self.letter}   {self.answer_text}")

    def set_selected(self, selected: bool):
        self._selected = selected
        self._correct = None
        self._update_style()

    def set_result(self, is_correct: bool):
        self._correct = is_correct
        self._update_style()

    def pulse_animation(self):
        self._anim.setStartValue(self.minimumHeight())
        self._anim.setEndValue(self.minimumHeight() + 6)
        self._anim.setEasingCurve(QEasingCurve.Type.OutBounce)
        self._anim.start()
        QTimer.singleShot(150, lambda: self._anim.setEndValue(self.minimumHeight() - 6))


class ExamWindow(QMainWindow):
    def __init__(self, session_data: dict):
        super().__init__()
        self.session_id = session_data["session_id"]
        self.test_name = session_data["test_name"]
        self.time_limit = session_data["time_limit"] * 60  # sekundga aylantirish
        self.questions = session_data["questions"]
        self.current_index = 0
        self.answers = {}  # {str(q_id): answer}
        self.remaining_time = self.time_limit
        self._selected_answer = None
        self._finish_thread = None
        self._answered = False

        self._setup_window()
        self._setup_ui()
        self._load_question()
        self._start_timer()
        self._block_keys()

    def _setup_window(self):
        self.setWindowTitle(f"TEST: {self.test_name}")
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0A1929, stop:0.5 #0D47A1, stop:1 #0A1929);
                color: white;
                font-family: 'Segoe UI', Arial;
            }
            QLabel { background: transparent; color: white; }
        """)
        self.showFullScreen()

    def _block_keys(self):
        """Fullscreen rejimida tizim tugmalarini bloklash."""
        # ESC tugmasini bloklash
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.showFullScreen()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(30, 15, 30, 15)
        main_layout.setSpacing(12)

        # ── Top Bar ────────────────────────────────────────────────────────────
        top_bar = QHBoxLayout()

        test_name_label = QLabel(f"📝  {self.test_name}")
        test_name_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        test_name_label.setStyleSheet("color: rgba(255,255,255,0.9);")

        self.question_counter = QLabel("0 / 0")
        self.question_counter.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        self.question_counter.setStyleSheet("""
            background: rgba(255,255,255,0.15);
            border-radius: 12px;
            padding: 6px 16px;
            color: white;
        """)
        self.question_counter.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.timer_label = QLabel("⏱  30:00")
        self.timer_label.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        self.timer_label.setStyleSheet("""
            background: rgba(255,255,255,0.15);
            border-radius: 12px;
            padding: 6px 20px;
            color: #FFD740;
        """)
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        top_bar.addWidget(test_name_label)
        top_bar.addStretch()
        top_bar.addWidget(self.question_counter)
        top_bar.addSpacing(20)
        top_bar.addWidget(self.timer_label)
        main_layout.addLayout(top_bar)

        # ── Progress Bar ───────────────────────────────────────────────────────
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(len(self.questions))
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background: rgba(255,255,255,0.15);
                border-radius: 4px;
                border: none;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #FFD740, stop:1 #FF6F00);
                border-radius: 4px;
            }
        """)
        main_layout.addWidget(self.progress_bar)

        # ── Question Card ──────────────────────────────────────────────────────
        question_card = QFrame()
        question_card.setStyleSheet("""
            QFrame {
                background: rgba(255,255,255,0.08);
                border-radius: 20px;
                border: 1px solid rgba(255,255,255,0.15);
            }
        """)
        question_card.setMinimumHeight(130)

        q_layout = QVBoxLayout(question_card)
        q_layout.setContentsMargins(28, 20, 28, 20)

        q_num_label = QLabel("SAVOL")
        q_num_label.setFont(QFont("Segoe UI", 10))
        q_num_label.setStyleSheet("color: rgba(255,255,255,0.5); letter-spacing: 2px;")
        q_layout.addWidget(q_num_label)

        self.question_label = QLabel("Savol matni bu yerda ko'rinadi...")
        self.question_label.setFont(QFont("Segoe UI", 17))
        self.question_label.setWordWrap(True)
        self.question_label.setStyleSheet("color: white; line-height: 1.5;")
        q_layout.addWidget(self.question_label)

        main_layout.addWidget(question_card)

        # ── Answer Buttons ─────────────────────────────────────────────────────
        self.answer_buttons = {}
        answers_layout = QVBoxLayout()
        answers_layout.setSpacing(10)

        for i, (letter, label_text) in enumerate([
            ("A", "Variant A"),
            ("B", "Variant B"),
            ("C", "Variant C"),
            ("D", "Variant D"),
        ]):
            btn = AnswerButton(letter, label_text)
            btn.set_text_and_letter()
            btn.clicked.connect(lambda _, l=letter: self._select_answer(l))
            answers_layout.addWidget(btn)
            self.answer_buttons[letter] = btn

        main_layout.addLayout(answers_layout)
        main_layout.addSpacing(8)

        # ── Feedback label ─────────────────────────────────────────────────────
        self.feedback_label = QLabel("")
        self.feedback_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.feedback_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.feedback_label.setMinimumHeight(36)
        main_layout.addWidget(self.feedback_label)

        # ── Navigation ─────────────────────────────────────────────────────────
        nav_layout = QHBoxLayout()

        self.prev_btn = QPushButton("← Oldingi")
        self.prev_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.1);
                color: white;
                border: 2px solid rgba(255,255,255,0.3);
                border-radius: 12px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
                min-width: 130px;
            }
            QPushButton:hover { background: rgba(255,255,255,0.2); }
            QPushButton:disabled { opacity: 0.4; }
        """)
        self.prev_btn.clicked.connect(self._prev_question)

        self.answer_info = QLabel("Javob berish: 1 2 3 4  yoki  F1 F2 F3 F4")
        self.answer_info.setStyleSheet("color: rgba(255,255,255,0.55); font-size: 12px;")
        self.answer_info.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.next_btn = QPushButton("Keyingi →")
        self.next_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #FF6F00, stop:1 #FFA000);
                color: white;
                border: none;
                border-radius: 12px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
                min-width: 130px;
            }
            QPushButton:hover { background: #FFB300; }
        """)
        self.next_btn.clicked.connect(self._next_question)

        nav_layout.addWidget(self.prev_btn)
        nav_layout.addStretch()
        nav_layout.addWidget(self.answer_info)
        nav_layout.addStretch()
        nav_layout.addWidget(self.next_btn)
        main_layout.addLayout(nav_layout)

        # Keyboard hints
        keys_label = QLabel("[1][2][3][4] — javob     [→] — keyingi     [←] — oldingi")
        keys_label.setStyleSheet("color: rgba(255,255,255,0.4); font-size: 11px;")
        keys_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(keys_label)

    def _load_question(self):
        if not self.questions:
            return

        total = len(self.questions)
        idx = self.current_index
        q = self.questions[idx]

        self.question_counter.setText(f"{idx + 1} / {total}")
        self.progress_bar.setValue(idx + 1)
        self.question_label.setText(q["text"])
        self.feedback_label.setText("")
        self._selected_answer = self.answers.get(str(q["id"]))
        self._answered = self._selected_answer is not None

        # Javob tugmalarini yangilash
        for letter, btn in self.answer_buttons.items():
            text = q[f"option_{letter.lower()}"]
            btn.answer_text = text
            btn.set_text_and_letter()
            btn._correct = None
            btn.set_selected(letter == self._selected_answer)

        self.prev_btn.setEnabled(idx > 0)
        is_last = (idx == total - 1)
        if is_last:
            self.next_btn.setText("✅  Testni Yakunlash")
        else:
            self.next_btn.setText("Keyingi →")

    def _select_answer(self, letter: str):
        if not self.questions:
            return
        q = self.questions[self.current_index]
        self._selected_answer = letter
        self.answers[str(q["id"])] = letter

        for l, btn in self.answer_buttons.items():
            btn.set_selected(l == letter)
            if l == letter:
                btn.pulse_animation()

        # Ovoz effekti (agar javob tezda tekshirilmasa shunchaki click sound)
        play_sound("correct")

        # Bir soniyadan keyin keyingiga o'tish
        if self.current_index < len(self.questions) - 1:
            QTimer.singleShot(600, self._next_question)

    def _next_question(self):
        if self.current_index < len(self.questions) - 1:
            self.current_index += 1
            self._load_question()
        else:
            self._finish_exam()

    def _prev_question(self):
        if self.current_index > 0:
            self.current_index -= 1
            self._load_question()

    def _start_timer(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self._tick)
        self.timer.start(1000)

    def _tick(self):
        self.remaining_time -= 1
        mins = self.remaining_time // 60
        secs = self.remaining_time % 60
        self.timer_label.setText(f"⏱  {mins:02d}:{secs:02d}")

        if self.remaining_time <= 60:
            self.timer_label.setStyleSheet("""
                background: rgba(180,0,0,0.5);
                border-radius: 12px;
                padding: 6px 20px;
                color: #FF5252;
                font-weight: bold;
            """)
        if self.remaining_time <= 0:
            self.timer.stop()
            self._finish_exam(timeout=True)

    def keyPressEvent(self, event):
        key = event.key()
        if key in ANSWER_KEYS:
            self._select_answer(ANSWER_KEYS[key])
        elif key in (Qt.Key.Key_Right, Qt.Key.Key_Return, Qt.Key.Key_Space):
            self._next_question()
        elif key == Qt.Key.Key_Left:
            self._prev_question()
        elif key == Qt.Key.Key_Escape:
            self._confirm_exit()
        else:
            super().keyPressEvent(event)

    def _confirm_exit(self):
        reply = QMessageBox.question(
            self, "Testdan chiqish",
            "Testdan chiqmoqchimisiz?\nBarcha javoblaringiz yo'qoladi!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.timer.stop()
            self.close()
            from ..student.info_window import StudentInfoWindow
            self._info_win = StudentInfoWindow()
            self._info_win.show()

    def _finish_exam(self, timeout: bool = False):
        self.timer.stop()

        if timeout:
            QMessageBox.information(self, "Vaqt tugadi", "⏰ Vaqt tugadi! Natijalar hisoblanmoqda...")

        answered = len(self.answers)
        total = len(self.questions)
        if answered < total and not timeout:
            unanswered = total - answered
            reply = QMessageBox.question(
                self, "Yakunlash",
                f"Hali {unanswered} ta savol javobsiz qoldi.\nTestni yakunlashni tasdiqlaysizmi?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                self.timer.start(1000)
                return

        self.next_btn.setEnabled(False)
        self.next_btn.setText("⏳ Yuklanmoqda...")

        self._finish_thread = FinishThread(self.session_id, self.answers)
        self._finish_thread.success.connect(self._on_finished)
        self._finish_thread.error.connect(self._on_finish_error)
        self._finish_thread.start()

    def _on_finished(self, result: dict):
        play_sound("finish")
        from .result_window import ResultWindow
        self._result_win = ResultWindow(result)
        self._result_win.show()
        self.close()

    def _on_finish_error(self, msg: str):
        self.next_btn.setEnabled(True)
        self.next_btn.setText("✅  Yakunlash")
        QMessageBox.critical(self, "Xato", f"Natijalar yuborishda xato:\n{msg}")
