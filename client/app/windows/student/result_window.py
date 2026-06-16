"""
Natija oynasi — chiroyli, yorqin, bolalar uchun, animatsiyali.
"""
import random, math
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea, QGridLayout, QSizePolicy,
    QGraphicsOpacityEffect,
)
from PyQt6.QtCore import (
    Qt, QTimer, QRectF, QPropertyAnimation, QEasingCurve,
    QSequentialAnimationGroup, pyqtProperty,
)
from PyQt6.QtGui import (
    QFont, QColor, QPainter, QPen, QBrush,
    QLinearGradient, QRadialGradient,
)


# ── Baho konfiguratsiya ───────────────────────────────────────────────────────

GRADE_CFG = {
    5: dict(
        emoji="🏆", label="AJOYIB!",
        cr=255, cg=214, cb=0,          # gold
        bg1=(10, 0, 60), bg2=(40, 0, 120),   # purple-dark
        accent=(255, 235, 59),
    ),
    4: dict(
        emoji="⭐", label="YAXSHI!",
        cr=0, cg=200, cb=255,           # cyan
        bg1=(0, 10, 50), bg2=(0, 30, 100),
        accent=(100, 220, 255),
    ),
    3: dict(
        emoji="👍", label="QONIQARLI",
        cr=255, cg=145, cb=0,           # orange
        bg1=(40, 15, 0), bg2=(90, 35, 0),
        accent=(255, 180, 50),
    ),
    2: dict(
        emoji="📖", label="QONIQARSIZ",
        cr=255, cg=80, cb=120,          # pink-red
        bg1=(30, 0, 30), bg2=(70, 0, 60),
        accent=(255, 120, 160),
    ),
}


# ── Yulduzcha zarrachasi ──────────────────────────────────────────────────────

class Spark:
    SHAPES = ["star", "circle", "rect", "diamond"]
    PALETTE = [
        (255,215,0),(255,87,34),(0,229,255),(105,240,174),
        (234,128,252),(255,255,255),(255,193,7),(0,200,83),
    ]

    def __init__(self, w: int, h: int, init: bool = False):
        self.w, self.h = w, h
        self.reset(init)

    def reset(self, init: bool = False):
        self.x  = random.uniform(0, self.w)
        self.y  = random.uniform(-self.h, 0) if init else random.uniform(-80, -10)
        self.vx = random.uniform(-2, 2)
        self.vy = random.uniform(1.5, 5)
        r, g, b = random.choice(self.PALETTE)
        self.color = QColor(r, g, b, random.randint(190, 255))
        self.size  = random.uniform(5, 14)
        self.angle = random.uniform(0, 360)
        self.spin  = random.uniform(-9, 9)
        self.shape = random.choice(self.SHAPES)
        self.life  = 1.0
        self.decay = random.uniform(0.003, 0.008)

    def tick(self):
        self.x    += self.vx
        self.y    += self.vy
        self.angle += self.spin
        self.vy   += 0.08   # gravity
        self.life -= self.decay
        if self.life <= 0 or self.y > self.h + 20:
            self.reset()

    def draw(self, p: QPainter):
        alpha = int(self.life * self.color.alpha())
        c = QColor(self.color.red(), self.color.green(), self.color.blue(), max(0, alpha))
        p.save()
        p.translate(self.x, self.y)
        p.rotate(self.angle)
        p.setBrush(QBrush(c))
        p.setPen(Qt.PenStyle.NoPen)
        s = self.size

        if self.shape == "circle":
            p.drawEllipse(int(-s/2), int(-s/2), int(s), int(s))
        elif self.shape == "rect":
            p.drawRect(int(-s/2), int(-s/3), int(s), int(s * 0.6))
        elif self.shape == "diamond":
            from PyQt6.QtGui import QPolygonF
            from PyQt6.QtCore import QPointF
            pts = [QPointF(0,-s), QPointF(s*0.6,0), QPointF(0,s), QPointF(-s*0.6,0)]
            p.drawPolygon(QPolygonF(pts))
        else:  # star
            from PyQt6.QtGui import QPolygonF
            from PyQt6.QtCore import QPointF
            pts = []
            for i in range(10):
                angle = math.pi * i / 5 - math.pi / 2
                r = s if i % 2 == 0 else s * 0.4
                pts.append(QPointF(r * math.cos(angle), r * math.sin(angle)))
            p.drawPolygon(QPolygonF(pts))
        p.restore()


class ConfettiWidget(QWidget):
    def __init__(self, parent=None, count: int = 90):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._sparks: list[Spark] = []
        self._count = count
        self._timer = QTimer()
        self._timer.timeout.connect(self._tick)

    def burst(self):
        w, h = self.width(), self.height()
        self._sparks = [Spark(w, h, True) for _ in range(self._count)]
        self._timer.start(20)

    def stop(self):
        self._timer.stop()
        self._sparks = []

    def _tick(self):
        for s in self._sparks:
            s.tick()
        self.update()

    def paintEvent(self, _):
        if not self._sparks:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        for s in self._sparks:
            s.draw(p)
        p.end()


# ── Animatsiyali score ring ───────────────────────────────────────────────────

class ScoreRing(QWidget):
    def __init__(self, pct: int, cr: int, cg: int, cb: int, parent=None):
        super().__init__(parent)
        self._target = pct
        self._val    = 0.0
        self._cr, self._cg, self._cb = cr, cg, cb
        self._pulse  = 0.0
        self._pdelta = 0.05
        self.setFixedSize(200, 200)
        self._t = QTimer()
        self._t.timeout.connect(self._tick)
        self._t.start(16)

    def _tick(self):
        if self._val < self._target:
            self._val = min(self._val + max(self._target / 60, 0.5), self._target)
        self._pulse += self._pdelta
        if self._pulse > 1.0 or self._pulse < 0.0:
            self._pdelta *= -1
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2
        r  = min(w, h) / 2 - 18
        pw = 14

        # Glow halo
        pulse_alpha = int(30 + self._pulse * 25)
        glow = QRadialGradient(cx, cy, r + 20)
        glow.setColorAt(0, QColor(self._cr, self._cg, self._cb, pulse_alpha))
        glow.setColorAt(1, QColor(self._cr, self._cg, self._cb, 0))
        p.setBrush(QBrush(glow))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(int(cx - r - 20), int(cy - r - 20), int((r + 20) * 2), int((r + 20) * 2))

        # Track
        p.setPen(QPen(QColor(50, 50, 70), pw + 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawArc(int(cx-r), int(cy-r), int(r*2), int(r*2), 90*16, -360*16)

        # Arc
        if self._val > 0:
            gr = QLinearGradient(0, 0, w, h)
            gr.setColorAt(0.0, QColor(min(self._cr+60,255), min(self._cg+60,255), min(self._cb+60,255)))
            gr.setColorAt(1.0, QColor(self._cr, self._cg, self._cb))
            p.setPen(QPen(QBrush(gr), pw, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.drawArc(int(cx-r), int(cy-r), int(r*2), int(r*2),
                      90*16, int(-self._val / 100 * 360 * 16))

        # Inner circle
        p.setBrush(QBrush(QColor(20, 15, 40, 200)))
        p.setPen(Qt.PenStyle.NoPen)
        inner_r = r - pw // 2 - 4
        p.drawEllipse(int(cx - inner_r), int(cy - inner_r), int(inner_r*2), int(inner_r*2))

        # Percent
        p.setPen(QPen(QColor(self._cr, self._cg, self._cb)))
        p.setFont(QFont("Arial", 28, QFont.Weight.Black))
        p.drawText(QRectF(0, 0, w, h - 20), Qt.AlignmentFlag.AlignCenter, f"{int(self._val)}%")
        p.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        p.setPen(QPen(QColor(200, 200, 200)))
        p.drawText(QRectF(0, cy + 30, w, 22), Qt.AlignmentFlag.AlignCenter, "to'g'ri javoblar")
        p.end()


# ── Stat kartochka ────────────────────────────────────────────────────────────

def make_stat(icon: str, label: str, value: str,
              cr: int, cg: int, cb: int) -> QWidget:
    w = QWidget()
    w.setObjectName("StatCard")
    w.setFixedHeight(68)
    w.setStyleSheet(f"""
        QWidget#StatCard {{
            background: rgba({cr},{cg},{cb},35);
            border-radius: 14px;
            border: 2px solid rgba({cr},{cg},{cb},100);
        }}
    """)
    ly = QHBoxLayout(w)
    ly.setContentsMargins(16, 0, 16, 0)
    ly.setSpacing(10)

    ico = QLabel(icon)
    ico.setFont(QFont("Arial", 22))
    ico.setStyleSheet("background:transparent; border:none; color:white;")
    ico.setFixedWidth(32)

    col = QVBoxLayout()
    col.setSpacing(1)
    lbl = QLabel(label)
    lbl.setFont(QFont("Arial", 10))
    lbl.setStyleSheet(f"background:transparent; border:none; color:rgba({cr},{cg},{cb},200);")
    val_lbl = QLabel(value)
    val_lbl.setFont(QFont("Arial", 20, QFont.Weight.Black))
    val_lbl.setStyleSheet(f"background:transparent; border:none; color:rgb({cr},{cg},{cb});")
    col.addWidget(lbl)
    col.addWidget(val_lbl)

    ly.addWidget(ico)
    ly.addLayout(col, stretch=1)
    return w


# ── Savol natija karta ────────────────────────────────────────────────────────

def answer_cell(num: int, state: str) -> QWidget:
    """state: 'ok' | 'wrong' | 'skip'"""
    colors = {
        "ok":    (105, 240, 174),
        "wrong": (255, 82,  82),
        "skip":  (255, 214, 64),
    }
    icons = {"ok": "✓", "wrong": "✗", "skip": "—"}
    cr, cg, cb = colors[state]

    cell = QWidget()
    cell.setObjectName("AnswerCell")
    cell.setFixedSize(52, 52)
    cell.setStyleSheet(f"""
        QWidget#AnswerCell {{
            background: rgba({cr},{cg},{cb},35);
            border: 2px solid rgba({cr},{cg},{cb},160);
            border-radius: 12px;
        }}
    """)
    lay = QVBoxLayout(cell)
    lay.setContentsMargins(0, 2, 0, 0)
    lay.setSpacing(0)

    num_lbl = QLabel(str(num))
    num_lbl.setFont(QFont("Arial", 10, QFont.Weight.Bold))
    num_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    num_lbl.setStyleSheet(f"background:transparent; border:none; color:rgba({cr},{cg},{cb},200);")

    ico_lbl = QLabel(icons[state])
    ico_lbl.setFont(QFont("Arial", 14, QFont.Weight.Black))
    ico_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    ico_lbl.setStyleSheet(f"background:transparent; border:none; color:rgb({cr},{cg},{cb});")

    lay.addWidget(num_lbl)
    lay.addWidget(ico_lbl)
    return cell


# ── Asosiy oyna ───────────────────────────────────────────────────────────────

class ResultWindow(QMainWindow):
    def __init__(self, result: dict, pre_select: dict = None):
        super().__init__()
        self._r = result
        self._pre_select = pre_select or {}
        self._build()

    def _build(self):
        # grade xavfsiz
        try:
            grade = int(self._r.get("grade", 2))
        except Exception:
            grade = 2
        if grade not in GRADE_CFG:
            grade = 2

        g  = GRADE_CFG[grade]
        cr, cg, cb = g["cr"], g["cg"], g["cb"]
        b1r, b1g, b1b = g["bg1"]
        b2r, b2g, b2b = g["bg2"]
        ar, ag, ab     = g["accent"]

        # ── Oyna ──────────────────────────────────────────────────────────────
        self.setWindowTitle("🏆 Natija")
        self.resize(820, 680)
        self.setMinimumSize(640, 520)
        sc = self.screen().availableGeometry()
        self.move((sc.width() - 820) // 2, (sc.height() - 680) // 2)

        self.setStyleSheet(f"""
            QMainWindow {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 rgb({b1r},{b1g},{b1b}),
                    stop:0.5 rgb({b2r},{b2g},{b2b}),
                    stop:1 rgb({b1r},{b1g},{b1b}));
            }}
            QWidget {{ font-family:Arial,Helvetica,sans-serif; color:white; }}
            QLabel  {{ background:transparent; border:none; color:white; }}
            QScrollBar {{ background:transparent; width:0; height:0; border:none; }}
        """)

        central = QWidget()
        central.setStyleSheet("background:transparent;")
        self.setCentralWidget(central)

        # Konfetti overlay
        self._conf = ConfettiWidget(central)
        self._conf.resize(820, 680)

        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background:transparent; border:none;")
        root.addWidget(scroll)

        page = QWidget(); page.setStyleSheet("background:transparent;")
        scroll.setWidget(page)

        vl = QVBoxLayout(page)
        vl.setContentsMargins(28, 22, 28, 22)
        vl.setSpacing(14)

        # ══════════════════════════════════════════════════════════════════════
        # 1) BAHO — katta, markazda
        # ══════════════════════════════════════════════════════════════════════
        grade_card = QWidget()
        grade_card.setObjectName("GradeCard")
        grade_card.setFixedHeight(110)
        grade_card.setStyleSheet(f"""
            QWidget#GradeCard {{
                background: rgba({cr},{cg},{cb},40);
                border-radius: 20px;
                border: 2px solid rgba({cr},{cg},{cb},130);
            }}
        """)
        gc_lay = QHBoxLayout(grade_card)
        gc_lay.setContentsMargins(24, 0, 24, 0)
        gc_lay.setSpacing(18)

        # Katta raqam
        grade_num = QLabel(str(grade))
        grade_num.setFont(QFont("Arial", 64, QFont.Weight.Black))
        grade_num.setStyleSheet(f"color:rgb({cr},{cg},{cb}); background:transparent; border:none;")
        grade_num.setFixedWidth(80)
        grade_num.setAlignment(Qt.AlignmentFlag.AlignCenter)
        gc_lay.addWidget(grade_num)

        # Chiziq
        div = QWidget(); div.setFixedSize(3, 70)
        div.setStyleSheet(f"background:rgba({cr},{cg},{cb},100); border:none; border-radius:1px;")
        gc_lay.addWidget(div)

        # Matn ustun
        txt_v = QVBoxLayout(); txt_v.setSpacing(6); txt_v.setContentsMargins(0,0,0,0)
        lbl_main = QLabel(g["label"])
        lbl_main.setFont(QFont("Arial", 26, QFont.Weight.Black))
        lbl_main.setStyleSheet(f"color:rgb({cr},{cg},{cb}); letter-spacing:4px;")
        txt_v.addWidget(lbl_main)

        fan_lbl = QLabel(f"📚  {self._r.get('test_name','—')}")
        fan_lbl.setFont(QFont("Arial", 12))
        fan_lbl.setStyleSheet("color:rgba(255,255,255,160);")
        txt_v.addWidget(fan_lbl)
        gc_lay.addLayout(txt_v, stretch=1)

        # Emoji
        emo_lbl = QLabel(g["emoji"])
        emo_lbl.setFont(QFont("Arial", 44))
        emo_lbl.setFixedWidth(62)
        emo_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        emo_lbl.setStyleSheet("background:transparent; border:none;")
        gc_lay.addWidget(emo_lbl)
        vl.addWidget(grade_card)

        # ══════════════════════════════════════════════════════════════════════
        # 2) O'QUVCHI KARTA
        # ══════════════════════════════════════════════════════════════════════
        stu_card = QWidget()
        stu_card.setObjectName("StuCard")
        stu_card.setFixedHeight(60)
        stu_card.setStyleSheet(f"""
            QWidget#StuCard {{
                background: rgba(255,255,255,15);
                border-radius: 14px;
                border: 1px solid rgba({cr},{cg},{cb},70);
            }}
        """)
        sl = QHBoxLayout(stu_card)
        sl.setContentsMargins(16, 0, 16, 0)
        sl.setSpacing(14)

        first = str(self._r.get("student_name", "?"))
        last  = str(self._r.get("student_lastname", ""))
        av = QLabel((first[:1] or "?").upper())
        av.setFixedSize(40, 40)
        av.setFont(QFont("Arial", 17, QFont.Weight.Black))
        av.setAlignment(Qt.AlignmentFlag.AlignCenter)
        av.setStyleSheet(f"""
            background:rgba({cr},{cg},{cb},50);
            border:2px solid rgba({cr},{cg},{cb},200);
            border-radius:20px;
            color:rgb({cr},{cg},{cb});
        """)
        sl.addWidget(av)

        full = f"{last} {first}".strip() if last else first
        nm = QLabel(full or "—")
        nm.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        nm.setStyleSheet("color:white; background:transparent; border:none;")
        sl.addWidget(nm, stretch=1)

        cls = QLabel(f"🏫  {self._r.get('student_class','—')}")
        cls.setFont(QFont("Arial", 12))
        cls.setStyleSheet("color:rgba(255,255,255,150); background:transparent; border:none;")
        sl.addWidget(cls)
        vl.addWidget(stu_card)

        # ══════════════════════════════════════════════════════════════════════
        # 3) RING + STAT KARTOCHKALAR
        # ══════════════════════════════════════════════════════════════════════
        correct = int(self._r.get("correct_count", 0))
        wrong   = int(self._r.get("wrong_count", 0))
        total   = int(self._r.get("total_questions", correct + wrong))
        skipped = max(total - correct - wrong, 0)
        pct     = int(self._r.get("score_percent", 0))
        secs    = int(self._r.get("time_spent", 0))
        mm, ss  = divmod(secs, 60)

        mid = QHBoxLayout(); mid.setSpacing(20); mid.setContentsMargins(0,4,0,4)

        ring = ScoreRing(pct, cr, cg, cb)
        mid.addWidget(ring, alignment=Qt.AlignmentFlag.AlignVCenter)

        sc_col = QVBoxLayout(); sc_col.setSpacing(8)
        sc_col.addWidget(make_stat("✅", "To'g'ri javoblar",    str(correct), 105, 240, 174))
        sc_col.addWidget(make_stat("❌", "Noto'g'ri javoblar",  str(wrong),   255,  82,  82))
        sc_col.addWidget(make_stat("⬜", "O'tkazib yuborilgan", str(skipped), 255, 214,  64))
        sc_col.addWidget(make_stat("⏱", "Sarflangan vaqt",     f"{mm}:{ss:02d}", 66, 165, 245))
        mid.addLayout(sc_col, stretch=1)
        vl.addLayout(mid)

        # ══════════════════════════════════════════════════════════════════════
        # 4) BATAFSIL JAVOBLAR — har bir savol natijasi
        # ══════════════════════════════════════════════════════════════════════
        answers_data = self._r.get("answers", [])
        if answers_data:
            # Sarlavha
            sh_row = QHBoxLayout()
            sh_title = QLabel("📋  Har bir savol natijasi")
            sh_title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
            sh_title.setStyleSheet("color:rgba(255,255,255,200); background:transparent; border:none;")
            sh_row.addWidget(sh_title)
            sh_row.addStretch()

            leg_ok  = QLabel("  ✓ To'g'ri")
            leg_ok.setStyleSheet("color:rgb(105,240,174); background:transparent; border:none; font-size:11px;")
            leg_wr  = QLabel("  ✗ Noto'g'ri")
            leg_wr.setStyleSheet("color:rgb(255,82,82); background:transparent; border:none; font-size:11px;")
            leg_sk  = QLabel("  — O'tkazilgan")
            leg_sk.setStyleSheet("color:rgb(255,214,64); background:transparent; border:none; font-size:11px;")
            sh_row.addWidget(leg_ok); sh_row.addWidget(leg_wr); sh_row.addWidget(leg_sk)
            vl.addLayout(sh_row)

            # Grid
            grid_w = QWidget()
            grid_w.setObjectName("GridCard")
            grid_w.setStyleSheet(f"""
                QWidget#GridCard {{
                    background:rgba({cr},{cg},{cb},18);
                    border-radius:16px;
                    border:1.5px solid rgba({cr},{cg},{cb},60);
                }}
            """)
            grid = QGridLayout(grid_w)
            grid.setContentsMargins(14, 14, 14, 14)
            grid.setSpacing(7)

            COLS = 10
            for i, ans in enumerate(answers_data):
                ok    = bool(ans.get("is_correct", False))
                given = ans.get("given_answer") or ans.get("student_answer")
                if not given:
                    state = "skip"
                elif ok:
                    state = "ok"
                else:
                    state = "wrong"
                cell = answer_cell(i + 1, state)
                grid.addWidget(cell, i // COLS, i % COLS)

            # Qolgan bo'sh kataklar
            rem = COLS - (len(answers_data) % COLS)
            if rem < COLS:
                last_row = len(answers_data) // COLS
                for j in range(rem):
                    spacer = QWidget(); spacer.setFixedSize(52, 52)
                    spacer.setStyleSheet("background:transparent; border:none;")
                    grid.addWidget(spacer, last_row, (len(answers_data) % COLS) + j)

            vl.addWidget(grid_w)

            # Xulosa matn
            if correct == total:
                msg = f"🎉  Barcha {total} ta savolga to'g'ri javob berdingiz!"
                mc  = "rgb(105,240,174)"
            elif correct == 0:
                msg = f"📚  {total} ta savolning birontasiga to'g'ri javob berilmadi."
                mc  = "rgb(255,82,82)"
            else:
                msg = (f"✅ {correct} ta to'g'ri   ❌ {wrong} ta noto'g'ri"
                       + (f"   ⬜ {skipped} ta o'tkazilgan" if skipped else ""))
                mc = "rgba(255,255,255,180)"

            sum_lbl = QLabel(msg)
            sum_lbl.setFont(QFont("Arial", 12, QFont.Weight.Bold))
            sum_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            sum_lbl.setStyleSheet(f"color:{mc}; background:transparent; border:none;")
            vl.addWidget(sum_lbl)

        # ══════════════════════════════════════════════════════════════════════
        # 5) TUGMA — faqat "Bosh sahifa"
        # ══════════════════════════════════════════════════════════════════════
        text_col = "0,0,0" if grade == 5 else "255,255,255"
        home_btn = QPushButton("🏠   Bosh sahifaga qaytish")
        home_btn.setFixedHeight(58)
        home_btn.setFont(QFont("Arial", 15, QFont.Weight.Bold))
        home_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        home_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 rgb({cr},{cg},{cb}), stop:1 rgb({ar},{ag},{ab}));
                color: rgb({text_col});
                border: none;
                border-radius: 16px;
                letter-spacing: 1px;
            }}
            QPushButton:hover {{
                background: rgb({ar},{ag},{ab});
            }}
            QPushButton:pressed {{
                background: rgb({cr},{cg},{cb});
            }}
        """)
        home_btn.clicked.connect(self._home)
        vl.addWidget(home_btn)

        # Konfetti + ovoz — abadiy (oyna yopilgunicha)
        if grade >= 4:
            QTimer.singleShot(200, self._conf.burst)
        self._grade_for_sound = grade

        # Qarsak faylini oldindan yaratib qo'yish (Hero boshlanishidan oldin tayyor bo'lsin)
        if grade >= 4:
            try:
                from ...sound_player import prewarm
                prewarm()
            except Exception:
                pass

        QTimer.singleShot(300, self._play_result_sound)

    def _play_result_sound(self):
        from ...sound_player import play_grade
        play_grade(self._grade_for_sound)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if hasattr(self, "_conf"):
            self._conf.resize(self.size())

    def closeEvent(self, e):
        if hasattr(self, "_conf"):
            self._conf.stop()
        super().closeEvent(e)

    def _home(self):
        from ..student.info_window import StudentInfoWindow
        self._info = StudentInfoWindow(pre_select=self._pre_select)
        self._info.show()
        self.close()

    def keyPressEvent(self, e):
        if e.key() in (Qt.Key.Key_Escape,):
            self._home()
