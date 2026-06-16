"""
O'quvchi imtihon oynasi — compact, chiroyli, fullscreen emas.
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QProgressBar, QFrame, QMessageBox, QScrollArea,
    QSizePolicy,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QRectF
from PyQt6.QtGui import QFont, QColor, QPainter, QPen, QBrush, QLinearGradient


# ── Konstantalar ──────────────────────────────────────────────────────────────

ANSWER_CFG = {
    "A": ("#C62828", "#E53935"),
    "B": ("#1565C0", "#1E88E5"),
    "C": ("#2E7D32", "#43A047"),
    "D": ("#E65100", "#FB8C00"),
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
        self.setFixedHeight(54)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        self._draw()

    def _draw(self):
        d, lt = self._dark, self._light
        if self._sel:
            bg  = f"qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {lt},stop:1 {d})"
            bdr = "3px solid white"
        else:
            bg  = f"qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {d},stop:1 {lt})"
            bdr = "2px solid rgba(255,255,255,0.12)"
        self.setStyleSheet(f"""
            QPushButton {{
                background: {bg};
                color: white;
                border: {bdr};
                border-radius: 12px;
                padding-left: 16px;
                text-align: left;
            }}
            QPushButton:hover {{ border: 2px solid rgba(255,255,255,0.65); }}
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
        self.setFixedSize(28, 28)
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
            s = "background:#FF6F00;color:white;border:2px solid #FFD740;border-radius:7px;font-weight:bold;font-size:11px;"
        elif self._ans:
            s = "background:#00C853;color:white;border:2px solid #69F0AE;border-radius:7px;font-weight:bold;font-size:11px;"
        else:
            s = "background:rgba(255,255,255,0.08);color:rgba(255,255,255,0.40);border:1px solid rgba(255,255,255,0.18);border-radius:7px;font-size:11px;"
        self.setStyleSheet(f"QPushButton{{{s}}} QPushButton:hover{{background:rgba(255,255,255,0.22);color:white;border:2px solid white;}}")


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

        # Oyna o'lchami — 960x680, markazda
        self.setWindowTitle(f"Imtihon: {self.name}")
        self.resize(960, 680)
        self.setMinimumSize(780, 560)
        scr = self.screen().availableGeometry()
        self.move((scr.width()-960)//2, (scr.height()-680)//2)
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint)

        # Fon
        root = QWidget()
        root.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 #0D1B2A, stop:0.45 #1A3A6B, stop:1 #0D1B2A);
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
        hdr.setFixedHeight(52)
        hdr.setStyleSheet("background: rgba(0,0,0,0.38);")
        hdr_lay = QHBoxLayout(hdr)
        hdr_lay.setContentsMargins(18, 0, 18, 0)
        hdr_lay.setSpacing(14)

        fan = QLabel(f"📚  {self.name}")
        fan.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        fan.setStyleSheet("color: rgba(255,255,255,0.90);")
        hdr_lay.addWidget(fan)
        hdr_lay.addStretch()

        self._cnt = QLabel(f"1 / {total}")
        self._cnt.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self._cnt.setFixedWidth(74)
        self._cnt.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._cnt.setStyleSheet(
            "background:rgba(255,255,255,0.13);border-radius:8px;padding:3px 0;"
        )
        hdr_lay.addWidget(self._cnt)

        self._tlbl = QLabel("⏱  00:00")
        self._tlbl.setFont(QFont("Arial", 15, QFont.Weight.Bold))
        self._tlbl.setFixedWidth(112)
        self._tlbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._tlbl.setStyleSheet(
            "background:rgba(255,255,255,0.13);border-radius:8px;padding:3px 0;color:#FFD740;"
        )
        hdr_lay.addWidget(self._tlbl)
        outer.addWidget(hdr)

        # PROGRESS
        self._pbar = QProgressBar()
        self._pbar.setMaximum(total)
        self._pbar.setValue(0)
        self._pbar.setTextVisible(False)
        self._pbar.setFixedHeight(4)
        self._pbar.setStyleSheet("""
            QProgressBar{background:rgba(255,255,255,0.08);border:none;}
            QProgressBar::chunk{
                background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #FFD740,stop:1 #FF6F00);
            }
        """)
        outer.addWidget(self._pbar)

        # ══════════════════════════════════════════════════════════════════════
        # NAV DOTS
        # ══════════════════════════════════════════════════════════════════════
        nav_w = QWidget()
        nav_w.setFixedHeight(44)
        nav_w.setStyleSheet("background:rgba(255,255,255,0.03);")
        nav_lay = QHBoxLayout(nav_w)
        nav_lay.setContentsMargins(16, 7, 16, 7)
        nav_lay.setSpacing(8)

        n_lbl = QLabel("Savollar:")
        n_lbl.setFont(QFont("Arial", 9))
        n_lbl.setStyleSheet("color:rgba(255,255,255,0.40);")
        nav_lay.addWidget(n_lbl)

        sc = QScrollArea()
        sc.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        sc.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        sc.setFrameShape(QFrame.Shape.NoFrame)
        sc.setStyleSheet("background:transparent;border:none;")
        sc.setFixedHeight(32)

        inner = QWidget()
        inner.setStyleSheet("background:transparent;")
        inner_lay = QHBoxLayout(inner)
        inner_lay.setContentsMargins(0,0,0,0)
        inner_lay.setSpacing(4)

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
        self._stat.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self._stat.setStyleSheet("color:rgba(255,255,255,0.55);")
        nav_lay.addWidget(self._stat)
        outer.addWidget(nav_w)

        # ══════════════════════════════════════════════════════════════════════
        # CONTENT — savol + javoblar
        # ══════════════════════════════════════════════════════════════════════
        content = QWidget()
        content.setStyleSheet("background:transparent;")
        cnt_lay = QVBoxLayout(content)
        cnt_lay.setContentsMargins(22, 14, 22, 10)
        cnt_lay.setSpacing(9)

        # Savol karta
        q_card = QFrame()
        q_card.setStyleSheet("""
            QFrame {
                background: rgba(255,255,255,0.08);
                border: 1.5px solid rgba(255,255,255,0.16);
                border-radius: 16px;
            }
        """)
        q_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        qcl = QVBoxLayout(q_card)
        qcl.setContentsMargins(20, 14, 20, 14)
        qcl.setSpacing(4)

        self._qnum = QLabel("Savol 1")
        self._qnum.setFont(QFont("Arial", 9))
        self._qnum.setStyleSheet("color:rgba(255,255,255,0.38);letter-spacing:1px;")
        qcl.addWidget(self._qnum)

        self._qtxt = QLabel("")
        self._qtxt.setFont(QFont("Arial", 14))
        self._qtxt.setWordWrap(True)
        self._qtxt.setStyleSheet("color:white;line-height:1.4;")
        self._qtxt.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        qcl.addWidget(self._qtxt)

        cnt_lay.addWidget(q_card)

        # Javob tugmalari
        self._btns: dict[str, ABtn] = {}
        for letter in ("A","B","C","D"):
            b = ABtn(letter)
            b.clicked.connect(lambda _, l=letter: self._select(l))
            cnt_lay.addWidget(b)
            self._btns[letter] = b

        # Status
        self._status = QLabel("Javob tanlang yoki keyingi savolga o'ting")
        self._status.setFont(QFont("Arial", 11))
        self._status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status.setStyleSheet("color:rgba(255,255,255,0.38);")
        cnt_lay.addWidget(self._status)
        cnt_lay.addStretch()

        outer.addWidget(content, stretch=1)

        # ══════════════════════════════════════════════════════════════════════
        # PASTKI NAVIGATSIYA — DOIM KO'RINADI
        # ══════════════════════════════════════════════════════════════════════
        bot = QWidget()
        bot.setFixedHeight(62)
        bot.setStyleSheet(
            "background:rgba(0,0,0,0.42);"
            "border-top:1px solid rgba(255,255,255,0.09);"
        )
        bot_lay = QHBoxLayout(bot)
        bot_lay.setContentsMargins(22, 8, 22, 8)
        bot_lay.setSpacing(12)

        self._prev = QPushButton("◀   Oldingi")
        self._prev.setFixedSize(140, 44)
        self._prev.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        self._prev.setCursor(Qt.CursorShape.PointingHandCursor)
        self._prev.setStyleSheet("""
            QPushButton{background:rgba(255,255,255,0.09);color:white;
                border:2px solid rgba(255,255,255,0.22);border-radius:10px;}
            QPushButton:hover{background:rgba(255,255,255,0.18);border-color:white;}
            QPushButton:disabled{color:rgba(255,255,255,0.18);
                border-color:rgba(255,255,255,0.08);background:rgba(255,255,255,0.03);}
        """)
        self._prev.clicked.connect(self._go_prev)

        hint = QLabel("[1-4] javob  ·  [←→] o'tish  ·  [Esc] chiqish")
        hint.setFont(QFont("Arial", 10))
        hint.setStyleSheet("color:rgba(255,255,255,0.28);")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._next = QPushButton("Keyingi   ▶")
        self._next.setFixedSize(170, 44)
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
            return """QPushButton{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #1B5E20,stop:1 #2E7D32);
                color:white;border:2px solid #69F0AE;border-radius:10px;}
                QPushButton:hover{background:#388E3C;}
                QPushButton:disabled{background:rgba(255,255,255,0.10);border-color:transparent;}"""
        return """QPushButton{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,
                stop:0 #E65100,stop:1 #FF8F00);
            color:white;border:none;border-radius:10px;}
            QPushButton:hover{background:#FF6F00;}
            QPushButton:disabled{background:rgba(255,255,255,0.10);}"""

    # ── Savol yuklash ─────────────────────────────────────────────────────────

    def _load(self):
        total = len(self.qs)
        q     = self.qs[self.idx]
        qid   = str(q["id"])
        sel   = self.answers.get(qid)

        self._cnt.setText(f"{self.idx+1} / {total}")
        self._pbar.setValue(self.idx+1)
        self._qnum.setText(f"Savol  {self.idx+1}  /  {total}")
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
        self._next.setText("✅   Yakunlash" if is_last else "Keyingi   ▶")
        self._next.setStyleSheet(self._next_style(last=is_last))
        self._next.setEnabled(True)

        if sel:
            self._status.setText(f"✅   {sel} variantini tanladingiz — davom eting")
            self._status.setStyleSheet("color:#69F0AE;")
        else:
            self._status.setText("Javob tanlang  ·  yoki «Keyingi» ni bosib o'tkazib yuboring")
            self._status.setStyleSheet("color:rgba(255,255,255,0.38);")

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
                "background:rgba(180,0,0,0.40);border-radius:8px;"
                "padding:3px 0;color:#FF5252;font-weight:bold;"
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
            self, "Imtihondan chiqish",
            "⚠️  Imtihondan chiqmoqchimisiz?\nJavoblaringiz yo'qoladi!",
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
            dlg.setWindowTitle("⚠️  Javobsiz savollar!")
            dlg.setText(
                f"<b>{len(unanswered)} ta savolga javob bermadingiz.</b><br><br>"
                f"Javobsiz raqamlar: <b>{nums}</b><br><br>"
                "Shunga qaramay yakunlashni tasdiqlaysizmi?"
            )
            dlg.setIcon(QMessageBox.Icon.Warning)
            yes = dlg.addButton("✅  Ha, yakunlayman",   QMessageBox.ButtonRole.YesRole)
            dlg.addButton("↩  Qaytib javob beraman", QMessageBox.ButtonRole.NoRole)
            dlg.exec()
            if dlg.clickedButton() != yes:
                return

        self._finish()

    def _finish(self, timeout: bool = False):
        self._timer.stop()
        if timeout:
            QMessageBox.information(
                self, "⏰ Vaqt tugadi",
                "Imtihon vaqti tugadi!\nNatijalar hisoblanmoqda...",
            )
        self._next.setEnabled(False)
        self._next.setText("⏳  Yuklanmoqda...")

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
        self._next.setText("✅   Yakunlash" if is_last else "Keyingi   ▶")
        self._next.setStyleSheet(self._next_style(last=is_last))
        QMessageBox.critical(self, "Xato", f"Natijalar yuborishda xato:\n{msg}")
