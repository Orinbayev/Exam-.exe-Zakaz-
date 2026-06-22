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


# ── Javob ranglari — yorqin, to'yingan ───────────────────────────────────────

ANSWER_CFG = {
    "A": ("#B71C1C", "#FF1744"),   # yorqin qizil
    "B": ("#0D47A1", "#2979FF"),   # yorqin ko'k
    "C": ("#1B5E20", "#00E676"),   # yorqin yashil
    "D": ("#BF360C", "#FF6D00"),   # yorqin to'q sariq-to'q
}

KB = {
    Qt.Key.Key_1: "A", Qt.Key.Key_F1: "A",
    Qt.Key.Key_2: "B", Qt.Key.Key_F2: "B",
    Qt.Key.Key_3: "C", Qt.Key.Key_F3: "C",
    Qt.Key.Key_4: "D", Qt.Key.Key_F4: "D",
}


# ── Javob tugmasi ─────────────────────────────────────────────────────────────

class ABtn(QPushButton):
    def __init__(self, letter: str, parent=None):
        super().__init__(parent)
        self.letter = letter
        self._dark, self._light = ANSWER_CFG[letter]
        self._sel = False
        self.setFixedHeight(56)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self._draw()

    def _draw(self):
        d, lt = self._dark, self._light
        if self._sel:
            bg  = f"qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {lt},stop:1 {d})"
            bdr = "3px solid #FFD740"
            glow = f"background:{lt}22;"
        else:
            bg  = f"qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {d},stop:1 {lt})"
            bdr = "2px solid rgba(255,255,255,0.20)"
        self.setStyleSheet(f"""
            QPushButton {{
                background: {bg};
                color: white;
                border: {bdr};
                border-radius: 14px;
                padding-left: 18px;
                text-align: left;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                border: 2.5px solid rgba(255,255,255,0.75);
            }}
        """)

    def set_text(self, txt: str):
        self.setText(f"  {self.letter}    {txt}")

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
        self.resize(980, 700)
        self.setMinimumSize(800, 580)
        scr = self.screen().availableGeometry()
        self.move((scr.width()-980)//2, (scr.height()-700)//2)
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint)

        # Yorqin, rang-barang fon — binafsha → ko'k-violet
        root = QWidget()
        root.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 #0F0C29,
                    stop:0.45 #302B63,
                    stop:1 #24243E);
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
        # HEADER — rangli
        # ══════════════════════════════════════════════════════════════════════
        hdr = QWidget()
        hdr.setFixedHeight(56)
        hdr.setStyleSheet("""
            background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                stop:0 rgba(58,12,163,0.85),
                stop:1 rgba(0,119,182,0.85));
            border-bottom: 1.5px solid rgba(255,255,255,0.18);
        """)
        hdr_lay = QHBoxLayout(hdr)
        hdr_lay.setContentsMargins(20, 0, 20, 0)
        hdr_lay.setSpacing(14)

        fan = QLabel(f"📚  {self.name}")
        fan.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        fan.setStyleSheet("color: white;")
        hdr_lay.addWidget(fan)
        hdr_lay.addStretch()

        self._cnt = QLabel(f"1 / {total}")
        self._cnt.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self._cnt.setFixedWidth(80)
        self._cnt.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._cnt.setStyleSheet(
            "background:rgba(255,255,255,0.20);border-radius:10px;"
            "padding:4px 0;color:white;"
        )
        hdr_lay.addWidget(self._cnt)

        self._tlbl = QLabel("⏱  00:00")
        self._tlbl.setFont(QFont("Arial", 15, QFont.Weight.Bold))
        self._tlbl.setFixedWidth(120)
        self._tlbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._tlbl.setStyleSheet(
            "background:rgba(255,215,0,0.25);border-radius:10px;"
            "padding:4px 0;color:#FFD740;border:1.5px solid rgba(255,215,0,0.40);"
        )
        hdr_lay.addWidget(self._tlbl)
        outer.addWidget(hdr)

        # PROGRESS — uchta rang: binafsha→ko'k→yashil
        self._pbar = QProgressBar()
        self._pbar.setMaximum(total)
        self._pbar.setValue(0)
        self._pbar.setTextVisible(False)
        self._pbar.setFixedHeight(5)
        self._pbar.setStyleSheet("""
            QProgressBar{background:rgba(255,255,255,0.10);border:none;}
            QProgressBar::chunk{
                background:qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #F72585, stop:0.5 #7209B7, stop:1 #4CC9F0);
                border-radius:2px;
            }
        """)
        outer.addWidget(self._pbar)

        # ══════════════════════════════════════════════════════════════════════
        # NAV DOTS — raqamli yo'riqnoma
        # ══════════════════════════════════════════════════════════════════════
        nav_w = QWidget()
        nav_w.setFixedHeight(46)
        nav_w.setStyleSheet("background:rgba(255,255,255,0.05);")
        nav_lay = QHBoxLayout(nav_w)
        nav_lay.setContentsMargins(18, 7, 18, 7)
        nav_lay.setSpacing(8)

        n_lbl = QLabel(ts("exam.questions"))
        n_lbl.setFont(QFont("Arial", 9))
        n_lbl.setStyleSheet("color:rgba(255,255,255,0.50);")
        nav_lay.addWidget(n_lbl)

        sc = QScrollArea()
        sc.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        sc.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        sc.setFrameShape(QFrame.Shape.NoFrame)
        sc.setStyleSheet("background:transparent;border:none;")
        sc.setFixedHeight(34)

        inner = QWidget()
        inner.setStyleSheet("background:transparent;")
        inner_lay = QHBoxLayout(inner)
        inner_lay.setContentsMargins(0,0,0,0)
        inner_lay.setSpacing(5)

        self._dots: list[Dot] = []
        for i in range(total):
            d = Dot(i + 1)
            d.clicked.connect(lambda _, x=i: self._jump(x))
            inner_lay.addWidget(d)
            self._dots.append(d)
        inner_lay.addStretch()
        sc.setWidget(inner)
        nav_lay.addWidget(sc, stretch=1)

        self._stat = QLabel("✅ 0  ⬜ 0")
        self._stat.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self._stat.setStyleSheet("color:rgba(255,255,255,0.70);")
        nav_lay.addWidget(self._stat)
        outer.addWidget(nav_w)

        # ══════════════════════════════════════════════════════════════════════
        # CONTENT — savol + javoblar
        # ══════════════════════════════════════════════════════════════════════
        content = QWidget()
        content.setStyleSheet("background:transparent;")
        cnt_lay = QVBoxLayout(content)
        cnt_lay.setContentsMargins(24, 16, 24, 10)
        cnt_lay.setSpacing(10)

        # Savol karta — oq shisha effekt
        q_card = QFrame()
        q_card.setStyleSheet("""
            QFrame {
                background: rgba(255,255,255,0.12);
                border: 2px solid rgba(255,255,255,0.28);
                border-radius: 18px;
            }
        """)
        q_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        qcl = QVBoxLayout(q_card)
        qcl.setContentsMargins(22, 16, 22, 16)
        qcl.setSpacing(6)

        self._qnum = QLabel("Savol 1")
        self._qnum.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self._qnum.setStyleSheet(
            "color:rgba(255,255,255,0.55);letter-spacing:1.5px;"
            "background:transparent;"
        )
        qcl.addWidget(self._qnum)

        self._qtxt = QLabel("")
        self._qtxt.setFont(QFont("Arial", 15))
        self._qtxt.setWordWrap(True)
        self._qtxt.setStyleSheet("color:white;line-height:1.5;background:transparent;")
        self._qtxt.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        qcl.addWidget(self._qtxt)

        cnt_lay.addWidget(q_card)

        # Javob tugmalari — 4 ta yorqin rang
        self._btns: dict[str, ABtn] = {}
        for letter in ("A","B","C","D"):
            b = ABtn(letter)
            b.clicked.connect(lambda _, l=letter: self._select(l))
            cnt_lay.addWidget(b)
            self._btns[letter] = b

        # Status matni
        self._status = QLabel("Javob tanlang yoki keyingi savolga o'ting")
        self._status.setFont(QFont("Arial", 11))
        self._status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status.setStyleSheet(
            "color:rgba(255,255,255,0.45);background:transparent;"
        )
        cnt_lay.addWidget(self._status)
        cnt_lay.addStretch()

        outer.addWidget(content, stretch=1)

        # ══════════════════════════════════════════════════════════════════════
        # PASTKI NAVIGATSIYA
        # ══════════════════════════════════════════════════════════════════════
        bot = QWidget()
        bot.setFixedHeight(64)
        bot.setStyleSheet("""
            background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                stop:0 rgba(58,12,163,0.75),
                stop:1 rgba(0,119,182,0.75));
            border-top: 1.5px solid rgba(255,255,255,0.15);
        """)
        bot_lay = QHBoxLayout(bot)
        bot_lay.setContentsMargins(22, 9, 22, 9)
        bot_lay.setSpacing(12)

        self._prev = QPushButton(ts("exam.prev"))
        self._prev.setFixedSize(150, 46)
        self._prev.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        self._prev.setCursor(Qt.CursorShape.PointingHandCursor)
        self._prev.setStyleSheet("""
            QPushButton{background:rgba(255,255,255,0.15);color:white;
                border:2px solid rgba(255,255,255,0.35);border-radius:12px;}
            QPushButton:hover{background:rgba(255,255,255,0.28);border-color:white;}
            QPushButton:disabled{color:rgba(255,255,255,0.20);
                border-color:rgba(255,255,255,0.10);background:rgba(255,255,255,0.05);}
        """)
        self._prev.clicked.connect(self._go_prev)

        hint = QLabel(ts("exam.hint"))
        hint.setFont(QFont("Arial", 10))
        hint.setStyleSheet("color:rgba(255,255,255,0.40);")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._next = QPushButton(ts("exam.next"))
        self._next.setFixedSize(180, 46)
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
                QPushButton{
                    background:qlineargradient(x1:0,y1:0,x2:1,y2:0,
                        stop:0 #00BFA5,stop:1 #00E676);
                    color:white;border:2px solid #69F0AE;border-radius:12px;
                    font-size:14px;font-weight:bold;
                }
                QPushButton:hover{background:#00E676;border-color:white;}
                QPushButton:disabled{background:rgba(255,255,255,0.10);border-color:transparent;}
            """
        return """
            QPushButton{
                background:qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #F72585,stop:1 #7209B7);
                color:white;border:none;border-radius:12px;
                font-size:14px;font-weight:bold;
            }
            QPushButton:hover{background:#F72585;}
            QPushButton:disabled{background:rgba(255,255,255,0.10);}
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
            self._status.setStyleSheet("color:#00E676;background:transparent;font-weight:bold;")
        else:
            self._status.setText(ts("exam.status_none"))
            self._status.setStyleSheet("color:rgba(255,255,255,0.45);background:transparent;")

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
