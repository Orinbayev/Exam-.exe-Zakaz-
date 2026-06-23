"""
O'quvchi imtihon oynasi — yorqin ranglar, bolalarga mos dizayn.
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QProgressBar, QFrame, QMessageBox, QScrollArea,
    QSizePolicy,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QRectF
from PyQt6.QtGui import QFont, QColor, QPainter, QPen, QBrush, QLinearGradient
from ...i18n import ts


# ── Javob ranglari ────────────────────────────────────────────────────────────

ANSWER_CFG = {
    "A": ("#7B1520", "#C0392B"),   # chuqur qizil
    "B": ("#0D3B6E", "#1565C0"),   # chuqur ko'k
    "C": ("#155724", "#1E8449"),   # chuqur yashil
    "D": ("#7D3C00", "#D35400"),   # chuqur to'q sariq
}

KB = {
    Qt.Key.Key_1: "A", Qt.Key.Key_F1: "A",
    Qt.Key.Key_2: "B", Qt.Key.Key_F2: "B",
    Qt.Key.Key_3: "C", Qt.Key.Key_F3: "C",
    Qt.Key.Key_4: "D", Qt.Key.Key_F4: "D",
}


# ── Javob tugmasi — badge + matn ──────────────────────────────────────────────

class ABtn(QPushButton):
    def __init__(self, letter: str, parent=None):
        super().__init__(parent)
        self.letter = letter
        self._dark, self._light = ANSWER_CFG[letter]
        self._sel = False
        self.setFixedHeight(68)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setText("")  # layout ichida ko'rsatiladi

        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 10, 20, 10)
        lay.setSpacing(16)

        # Doira badge — harf
        self._badge = QLabel(letter)
        self._badge.setFixedSize(44, 44)
        self._badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._badge.setFont(QFont("Arial", 17, QFont.Weight.Bold))
        self._badge.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        # Javob matni
        self._lbl = QLabel("")
        self._lbl.setFont(QFont("Arial", 13))
        self._lbl.setWordWrap(False)
        self._lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        lay.addWidget(self._badge)
        lay.addWidget(self._lbl, stretch=1)
        self._draw()

    def _draw(self):
        d, lt = self._dark, self._light
        if self._sel:
            btn_bg  = (f"qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                       f"stop:0 {lt}, stop:1 {lt}CC)")
            btn_bdr = "3px solid #FFD740"
            badge_s = ("background: rgba(255,255,255,0.30);"
                       "color: white; border-radius: 22px;"
                       "font-size: 17px; font-weight: bold;")
            txt_s   = ("color: white; background: transparent;"
                       "font-size: 13px; font-weight: bold;")
        else:
            btn_bg  = (f"qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                       f"stop:0 {d}, stop:0.55 {d}, stop:1 {lt})")
            btn_bdr = "1.5px solid rgba(255,255,255,0.18)"
            badge_s = ("background: rgba(255,255,255,0.20);"
                       "color: rgba(255,255,255,0.95);"
                       "border-radius: 22px;"
                       "font-size: 17px; font-weight: bold;")
            txt_s   = ("color: rgba(255,255,255,0.90);"
                       "background: transparent; font-size: 13px;")

        self.setStyleSheet(f"""
            QPushButton {{
                background: {btn_bg};
                border: {btn_bdr};
                border-radius: 18px;
            }}
            QPushButton:hover {{
                border: 2.5px solid rgba(255,255,255,0.60);
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {d}, stop:1 {lt});
            }}
        """)
        self._badge.setStyleSheet(badge_s)
        self._lbl.setStyleSheet(txt_s)

    def set_text(self, txt: str):
        self._lbl.setText(txt)

    def set_sel(self, yes: bool):
        if self._sel != yes:
            self._sel = yes
            self._draw()


# ── Nav dot ───────────────────────────────────────────────────────────────────

class Dot(QPushButton):
    def __init__(self, num: int, parent=None):
        super().__init__(str(num), parent)
        self.setFixedSize(30, 30)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._ans = False
        self._cur = False
        self._draw()

    def set_state(self, answered: bool, current: bool):
        if self._ans != answered or self._cur != current:
            self._ans = answered
            self._cur = current
            self._draw()

    def _draw(self):
        if self._cur:
            s = ("background:qlineargradient(x1:0,y1:0,x2:1,y2:1,"
                 "stop:0 #FF6D00,stop:1 #FFD740);"
                 "color:white;border:2.5px solid #FFD740;border-radius:8px;"
                 "font-weight:bold;font-size:11px;")
        elif self._ans:
            s = ("background:qlineargradient(x1:0,y1:0,x2:1,y2:1,"
                 "stop:0 #00BFA5,stop:1 #00E676);"
                 "color:white;border:2px solid #69F0AE;border-radius:8px;"
                 "font-weight:bold;font-size:11px;")
        else:
            s = ("background:rgba(255,255,255,0.13);color:rgba(255,255,255,0.55);"
                 "border:1.5px solid rgba(255,255,255,0.25);border-radius:8px;font-size:11px;")
        self.setStyleSheet(
            f"QPushButton{{{s}}}"
            " QPushButton:hover{background:rgba(255,255,255,0.28);color:white;"
            "border:2px solid white;}"
        )


# ── Finish thread ─────────────────────────────────────────────────────────────

class FinishThread(QThread):
    ok  = pyqtSignal(dict)
    err = pyqtSignal(str)

    def __init__(self, sid: int, answers: dict):
        super().__init__()
        self.sid     = sid
        self.answers = answers

    def run(self):
        from ...api_client import api, APIError
        try:
            self.ok.emit(api.finish_exam(self.sid, self.answers))
        except APIError as e:
            self.err.emit(str(e))


# ── Asosiy oyna ───────────────────────────────────────────────────────────────

class ExamWindow(QMainWindow):
    def __init__(self, session_data: dict, pre_select: dict = None):
        super().__init__()
        self.sid         = session_data["session_id"]
        self.name        = session_data["test_name"]
        self.qs          = session_data["questions"]
        self.remaining   = session_data["time_limit"] * 60
        self.idx         = 0
        self.answers     = {}
        self._thread     = None
        self._pre_select = pre_select or {}

        self._build()
        self._load()
        self._start_timer()

    # ── Oyna ──────────────────────────────────────────────────────────────────

    def _build(self):
        total = len(self.qs)

        self.setWindowTitle(ts("exam.window_title", name=self.name))
        self.resize(1020, 720)
        self.setMinimumSize(820, 600)
        scr = self.screen().availableGeometry()
        self.move((scr.width() - 1020) // 2, (scr.height() - 720) // 2)
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint)

        # Asosiy fon — chuqur to'q ko'k
        root = QWidget()
        root.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 #0A0F2E,
                    stop:0.50 #101843,
                    stop:1 #0A1029);
                font-family: 'Arial', 'Helvetica', sans-serif;
                color: white;
            }
            QLabel { background: transparent; color: white; }
        """)
        self.setCentralWidget(root)

        outer = QVBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ══════════════════════════════════════════════════════════════════════
        # HEADER
        # ══════════════════════════════════════════════════════════════════════
        hdr = QWidget()
        hdr.setFixedHeight(62)
        hdr.setStyleSheet("""
            background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                stop:0 #1a1060,
                stop:0.55 #1a3a6e,
                stop:1 #0d2b52);
            border-bottom: 2px solid rgba(100,140,255,0.22);
        """)
        hdr_lay = QHBoxLayout(hdr)
        hdr_lay.setContentsMargins(24, 0, 24, 0)
        hdr_lay.setSpacing(16)

        fan_ico = QLabel("📚")
        fan_ico.setFont(QFont("Segoe UI Emoji", 18))
        fan_ico.setStyleSheet("color:white;")
        hdr_lay.addWidget(fan_ico)

        fan = QLabel(self.name)
        fan.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        fan.setStyleSheet("color:white;")
        hdr_lay.addWidget(fan)
        hdr_lay.addStretch()

        self._cnt = QLabel(f"1 / {total}")
        self._cnt.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self._cnt.setFixedSize(90, 36)
        self._cnt.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._cnt.setStyleSheet(
            "background:rgba(255,255,255,0.12);"
            "border:1.5px solid rgba(255,255,255,0.22);"
            "border-radius:10px;color:white;"
        )
        hdr_lay.addWidget(self._cnt)

        self._tlbl = QLabel("⏱  00:00")
        self._tlbl.setFont(QFont("Arial", 15, QFont.Weight.Bold))
        self._tlbl.setFixedSize(130, 36)
        self._tlbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._tlbl.setStyleSheet(
            "background:rgba(255,215,0,0.18);"
            "border:1.5px solid rgba(255,215,0,0.35);"
            "border-radius:10px;color:#FFD740;"
        )
        hdr_lay.addWidget(self._tlbl)
        outer.addWidget(hdr)

        # Progress bar
        self._pbar = QProgressBar()
        self._pbar.setMaximum(total)
        self._pbar.setValue(0)
        self._pbar.setTextVisible(False)
        self._pbar.setFixedHeight(4)
        self._pbar.setStyleSheet("""
            QProgressBar { background:rgba(255,255,255,0.08); border:none; }
            QProgressBar::chunk {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #7C4DFF, stop:0.5 #536DFE, stop:1 #40C4FF);
            }
        """)
        outer.addWidget(self._pbar)

        # ══════════════════════════════════════════════════════════════════════
        # SAVOLLAR NAV DOTS
        # ══════════════════════════════════════════════════════════════════════
        nav_w = QWidget()
        nav_w.setFixedHeight(50)
        nav_w.setStyleSheet("background:rgba(255,255,255,0.04);")
        nav_lay = QHBoxLayout(nav_w)
        nav_lay.setContentsMargins(20, 8, 20, 8)
        nav_lay.setSpacing(10)

        n_lbl = QLabel(ts("exam.questions"))
        n_lbl.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        n_lbl.setStyleSheet(
            "color:rgba(255,255,255,0.40);"
            "letter-spacing:1px;"
        )
        nav_lay.addWidget(n_lbl)

        sc = QScrollArea()
        sc.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        sc.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        sc.setFrameShape(QFrame.Shape.NoFrame)
        sc.setStyleSheet("background:transparent;border:none;")
        sc.setFixedHeight(36)

        dots_w = QWidget()
        dots_w.setStyleSheet("background:transparent;")
        dots_lay = QHBoxLayout(dots_w)
        dots_lay.setContentsMargins(0, 0, 0, 0)
        dots_lay.setSpacing(5)

        self._dots: list[Dot] = []
        for i in range(total):
            d = Dot(i + 1)
            d.clicked.connect(lambda _, x=i: self._jump(x))
            dots_lay.addWidget(d)
            self._dots.append(d)
        dots_lay.addStretch()
        sc.setWidget(dots_w)
        nav_lay.addWidget(sc, stretch=1)

        # Javob statistikasi
        self._stat = QLabel("✅ 0  ⬜ 0")
        self._stat.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self._stat.setFixedHeight(30)
        self._stat.setStyleSheet(
            "color:rgba(255,255,255,0.65);"
            "background:rgba(255,255,255,0.07);"
            "border-radius:8px;"
            "padding: 0 10px;"
        )
        nav_lay.addWidget(self._stat)
        outer.addWidget(nav_w)

        # ══════════════════════════════════════════════════════════════════════
        # CONTENT — savol + javoblar
        # ══════════════════════════════════════════════════════════════════════
        content = QWidget()
        content.setStyleSheet("background:transparent;")
        cnt_lay = QVBoxLayout(content)
        cnt_lay.setContentsMargins(32, 18, 32, 12)
        cnt_lay.setSpacing(11)

        # Savol karta — glassmorphism
        q_card = QFrame()
        q_card.setStyleSheet("""
            QFrame {
                background: rgba(255,255,255,0.08);
                border: 1.5px solid rgba(120,160,255,0.25);
                border-left: 4px solid #536DFE;
                border-radius: 18px;
            }
        """)
        q_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        qcl = QVBoxLayout(q_card)
        qcl.setContentsMargins(24, 14, 24, 14)
        qcl.setSpacing(8)

        # Savol raqami — small badge
        self._qnum = QLabel()
        self._qnum.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        self._qnum.setFixedHeight(22)
        self._qnum.setStyleSheet(
            "color:rgba(120,160,255,0.90);"
            "letter-spacing:2px;"
            "background:transparent;"
        )
        qcl.addWidget(self._qnum)

        # Savol matni
        self._qtxt = QLabel("")
        self._qtxt.setFont(QFont("Arial", 15))
        self._qtxt.setWordWrap(True)
        self._qtxt.setStyleSheet(
            "color:white;"
            "background:transparent;"
            "line-height: 1.5;"
        )
        self._qtxt.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        qcl.addWidget(self._qtxt)

        cnt_lay.addWidget(q_card)

        # Javob tugmalari — 4 ta
        self._btns: dict[str, ABtn] = {}
        for letter in ("A", "B", "C", "D"):
            b = ABtn(letter)
            b.clicked.connect(lambda _, l=letter: self._select(l))
            cnt_lay.addWidget(b)
            self._btns[letter] = b

        # Status pill
        self._status = QLabel(ts("exam.status_none") if False else "")
        self._status.setFixedHeight(34)
        self._status.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self._status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status.setStyleSheet(
            "color:rgba(255,255,255,0.35);"
            "background:rgba(255,255,255,0.06);"
            "border-radius:17px;"
        )
        cnt_lay.addWidget(self._status)
        cnt_lay.addStretch()

        outer.addWidget(content, stretch=1)

        # ══════════════════════════════════════════════════════════════════════
        # PASTKI NAVIGATSIYA
        # ══════════════════════════════════════════════════════════════════════
        bot = QWidget()
        bot.setFixedHeight(68)
        bot.setStyleSheet("""
            background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                stop:0 #0f0c35, stop:1 #0a1a38);
            border-top: 1.5px solid rgba(100,140,255,0.18);
        """)
        bot_lay = QHBoxLayout(bot)
        bot_lay.setContentsMargins(24, 10, 24, 10)
        bot_lay.setSpacing(14)

        self._prev = QPushButton(ts("exam.prev"))
        self._prev.setFixedSize(160, 48)
        self._prev.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        self._prev.setCursor(Qt.CursorShape.PointingHandCursor)
        self._prev.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.10);
                color: rgba(255,255,255,0.80);
                border: 1.5px solid rgba(255,255,255,0.22);
                border-radius: 14px;
                font-size: 13px;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.20);
                color: white;
                border-color: rgba(255,255,255,0.55);
            }
            QPushButton:disabled {
                color: rgba(255,255,255,0.18);
                border-color: rgba(255,255,255,0.08);
                background: rgba(255,255,255,0.03);
            }
        """)
        self._prev.clicked.connect(self._go_prev)

        hint = QLabel(ts("exam.hint"))
        hint.setFont(QFont("Arial", 9))
        hint.setStyleSheet("color:rgba(255,255,255,0.28);")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._next = QPushButton(ts("exam.next"))
        self._next.setFixedSize(190, 48)
        self._next.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self._next.setCursor(Qt.CursorShape.PointingHandCursor)
        self._next.setStyleSheet(self._next_style(last=False))
        self._next.clicked.connect(self._go_next)

        bot_lay.addWidget(self._prev)
        bot_lay.addStretch()
        bot_lay.addWidget(hint)
        bot_lay.addStretch()
        bot_lay.addWidget(self._next)
        outer.addWidget(bot)

    def _next_style(self, last: bool) -> str:
        if last:
            return """
                QPushButton {
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                        stop:0 #00897B, stop:1 #00C853);
                    color: white;
                    border: 2px solid rgba(0,200,83,0.50);
                    border-radius: 14px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                        stop:0 #00A693, stop:1 #00E676);
                    border-color: #69F0AE;
                }
                QPushButton:disabled {
                    background: rgba(255,255,255,0.10);
                    border-color: transparent;
                    color: rgba(255,255,255,0.30);
                }
            """
        return """
            QPushButton {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #3949AB, stop:1 #536DFE);
                color: white;
                border: none;
                border-radius: 14px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #536DFE, stop:1 #82B1FF);
            }
            QPushButton:disabled {
                background: rgba(255,255,255,0.10);
                color: rgba(255,255,255,0.30);
            }
        """

    # ── Savol yuklash ─────────────────────────────────────────────────────────

    def _load(self):
        total = len(self.qs)
        q     = self.qs[self.idx]
        qid   = str(q["id"])
        sel   = self.answers.get(qid)

        self._cnt.setText(f"{self.idx+1} / {total}")
        self._pbar.setValue(self.idx+1)
        self._qnum.setText(ts("exam.question_lbl", i=self.idx+1, total=total))
        self._qtxt.setText(q["text"])

        for l, b in self._btns.items():
            b.set_text(q.get(f"option_{l.lower()}", ""))
            b.set_sel(l == sel)

        answered = len(self.answers)
        self._stat.setText(f"✅ {answered}  ⬜ {total-answered}")
        for i, d in enumerate(self._dots):
            d.set_state(
                answered=str(self.qs[i]["id"]) in self.answers,
                current=(i == self.idx),
            )

        is_last = (self.idx == total - 1)
        self._prev.setEnabled(self.idx > 0)
        self._next.setText(ts("exam.finish") if is_last else ts("exam.next"))
        self._next.setStyleSheet(self._next_style(last=is_last))
        self._next.setEnabled(True)

        if sel:
            self._status.setText(ts("exam.status_sel", l=sel))
            self._status.setStyleSheet(
                "color:#00E676;"
                "background:rgba(0,230,118,0.12);"
                "border:1px solid rgba(0,230,118,0.30);"
                "border-radius:17px;"
                "font-weight:bold;"
            )
        else:
            self._status.setText(ts("exam.status_none"))
            self._status.setStyleSheet(
                "color:rgba(255,255,255,0.35);"
                "background:rgba(255,255,255,0.06);"
                "border-radius:17px;"
            )

    # ── Javob ─────────────────────────────────────────────────────────────────

    def _select(self, letter: str):
        qid = str(self.qs[self.idx]["id"])
        self.answers[qid] = letter
        for l, b in self._btns.items():
            b.set_sel(l == letter)
        try:
            from ...sound_player import play
            play("click", volume=0.60)
        except Exception:
            pass
        self._load()

    # ── Navigatsiya ───────────────────────────────────────────────────────────

    def _go_next(self):
        if self.idx < len(self.qs) - 1:
            self.idx += 1
            self._load()
        else:
            self._try_finish()

    def _go_prev(self):
        if self.idx > 0:
            self.idx -= 1
            self._load()

    def _jump(self, i: int):
        self.idx = i
        self._load()

    # ── Timer ─────────────────────────────────────────────────────────────────

    def _start_timer(self):
        self._timer = QTimer()
        self._timer.timeout.connect(self._tick)
        self._timer.start(1000)

    def _tick(self):
        self.remaining -= 1
        m, s = divmod(self.remaining, 60)
        self._tlbl.setText(f"⏱  {m:02d}:{s:02d}")
        if self.remaining <= 60:
            self._tlbl.setStyleSheet(
                "background:rgba(255,50,50,0.45);border-radius:10px;"
                "padding:4px 0;color:#FF5252;font-weight:bold;"
                "border:1.5px solid rgba(255,82,82,0.60);"
            )
        if self.remaining <= 0:
            self._timer.stop()
            self._finish(timeout=True)

    # ── Klaviatura ────────────────────────────────────────────────────────────

    def keyPressEvent(self, e):
        k = e.key()
        if k in KB:
            self._select(KB[k])
        elif k in (Qt.Key.Key_Right, Qt.Key.Key_Space):
            self._go_next()
        elif k == Qt.Key.Key_Left:
            self._go_prev()
        elif k == Qt.Key.Key_Escape:
            self._exit()
        else:
            super().keyPressEvent(e)

    def _exit(self):
        r = QMessageBox.question(
            self, ts("exam.exit_title"), ts("exam.exit_msg"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if r == QMessageBox.StandardButton.Yes:
            self._timer.stop()
            self.close()
            from ..student.info_window import StudentInfoWindow
            self._info = StudentInfoWindow()
            self._info.show()

    # ── Yakunlash ─────────────────────────────────────────────────────────────

    def _try_finish(self):
        unanswered = [
            str(i+1)
            for i, q in enumerate(self.qs)
            if str(q["id"]) not in self.answers
        ]
        if unanswered:
            nums = ", ".join(unanswered[:15])
            if len(unanswered) > 15:
                nums += " ..."
            dlg = QMessageBox(self)
            dlg.setWindowTitle(ts("exam.unanswered_title"))
            dlg.setText(ts("exam.unanswered", n=len(unanswered), nums=nums))
            dlg.setIcon(QMessageBox.Icon.Warning)
            yes = dlg.addButton(ts("exam.btn_finish"), QMessageBox.ButtonRole.YesRole)
            dlg.addButton(ts("exam.btn_back"), QMessageBox.ButtonRole.NoRole)
            dlg.exec()
            if dlg.clickedButton() != yes:
                return

        self._finish()

    def _finish(self, timeout: bool = False):
        self._timer.stop()
        if timeout:
            QMessageBox.information(
                self, ts("exam.timeout_title"), ts("exam.timeout_msg"),
            )
        self._next.setEnabled(False)
        self._next.setText(ts("exam.loading"))

        self._thread = FinishThread(self.sid, self.answers)
        self._thread.ok.connect(self._done)
        self._thread.err.connect(self._fail)
        self._thread.start()

    def _done(self, result: dict):
        from .result_window import ResultWindow
        self._rw = ResultWindow(result, pre_select=self._pre_select)
        self._rw.show()
        self.close()

    def _fail(self, msg: str):
        is_last = (self.idx == len(self.qs) - 1)
        self._next.setEnabled(True)
        self._next.setText(ts("exam.finish") if is_last else ts("exam.next"))
        self._next.setStyleSheet(self._next_style(last=is_last))
        QMessageBox.critical(self, ts("common.error") if False else "Ошибка", ts("exam.err_send", msg=msg))
