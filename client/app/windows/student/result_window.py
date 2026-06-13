"""
Natija oynasi:
  Baho 5 → konfetti + salyut animatsiyasi + "AJOYIB!"
  Baho 4 → yashil + "YAXSHI!"
  Baho 3 → sariq + "QONIQARLI"
  Baho 2 → ko'k + "QONIQARSIZ"
"""
import random, math
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
)
from PyQt6.QtCore import Qt, QTimer, QPoint, QRectF
from PyQt6.QtGui import (
    QFont, QColor, QPainter, QBrush, QPen, QGuiApplication,
    QLinearGradient, QRadialGradient
)

# ── Rang palitralari ──────────────────────────────────────────────────────────
CONFETTI_COLORS = [
    "#FF6B6B","#4ECDC4","#45B7D1","#FFA07A","#FFD93D",
    "#6BCB77","#FF6B9D","#45AAF2","#FD9644","#A55EEA"
]

GRADE_CONFIG = {
    "5": {
        "bg":      "qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #1B5E20,stop:1 #2E7D32)",
        "accent":  "#FFD740",
        "title":   "🏆  AJOYIB!",
        "sub":     "Siz 5-baho oldingiz! Zo'r natija!",
        "fireworks": True,
    },
    "4": {
        "bg":      "qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #0D47A1,stop:1 #1565C0)",
        "accent":  "#69F0AE",
        "title":   "⭐  YAXSHI!",
        "sub":     "Yaxshi natija! Davom eting!",
        "fireworks": False,
    },
    "3": {
        "bg":      "qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #E65100,stop:1 #F57F17)",
        "accent":  "#FFE082",
        "title":   "✅  QONIQARLI",
        "sub":     "Yaxshi harakat. Ko'proq mashq qiling!",
        "fireworks": False,
    },
    "2": {
        "bg":      "qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #1A237E,stop:1 #283593)",
        "accent":  "#90CAF9",
        "title":   "📚  QONIQARSIZ",
        "sub":     "Xavotir olmang! Qayta urinib ko'ring!",
        "fireworks": False,
    },
}

def _cfg(grade):
    return GRADE_CONFIG.get(str(grade), GRADE_CONFIG["2"])


# ── Konfetti zarrasi ──────────────────────────────────────────────────────────
class _Particle:
    def __init__(self, w, h):
        self.x  = random.randint(0, w)
        self.y  = random.uniform(-120, -5)
        self.vx = random.uniform(-2.5, 2.5)
        self.vy = random.uniform(2.5, 7)
        self.g  = 0.09
        self.c  = QColor(random.choice(CONFETTI_COLORS))
        self.pw = random.randint(7, 15)
        self.ph = random.randint(4, 9)
        self.rot= random.uniform(0, 360)
        self.rs = random.uniform(-6, 6)
        self.alive = True
        self._max_y = h + 20

    def step(self):
        self.x += self.vx; self.y += self.vy
        self.vy += self.g; self.rot += self.rs
        self.alive = self.y < self._max_y


# ── Salyut zarrasi ────────────────────────────────────────────────────────────
class _Rocket:
    def __init__(self, w, h):
        self.cx = random.randint(w//5, w*4//5)
        self.cy = random.randint(h//5, h*3//5)
        self.color = QColor(random.choice(CONFETTI_COLORS))
        n = random.randint(28, 40)
        self.sparks = []
        for _ in range(n):
            angle = random.uniform(0, 2*math.pi)
            speed = random.uniform(2, 7)
            self.sparks.append([
                self.cx, self.cy,
                math.cos(angle)*speed, math.sin(angle)*speed,
                random.randint(3, 6), 255
            ])
        self.done = False

    def step(self):
        alive = False
        for s in self.sparks:
            s[0] += s[2]; s[1] += s[3]
            s[3] += 0.15  # gravity
            s[4] = max(1, s[4]-0.05)
            s[5] = max(0, s[5]-4)
            if s[5] > 0: alive = True
        self.done = not alive


# ── Animatsiya widget ─────────────────────────────────────────────────────────
class FXWidget(QWidget):
    def __init__(self, grade: str, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.particles = []
        self.rockets   = []
        self._grade5   = (str(grade) == "5")
        self._burst    = 0
        self._timer    = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(16)
        self._add_burst()

    def _add_burst(self):
        w, h = self.width() or 800, self.height() or 600
        if self._grade5:
            # Konfetti + salyut
            for _ in range(40): self.particles.append(_Particle(w, h))
            self.rockets.append(_Rocket(w, h))
        else:
            # Faqat yengilroq konfetti
            for _ in range(20): self.particles.append(_Particle(w, h))
        self._burst += 1

    def _tick(self):
        for p in self.particles: p.step()
        self.particles = [p for p in self.particles if p.alive]
        for r in self.rockets: r.step()
        self.rockets = [r for r in self.rockets if not r.done]

        # Yangi burst
        if self._grade5 and self._burst < 8:
            if len(self.particles) < 80:
                QTimer.singleShot(random.randint(300, 700), self._add_burst)
                self._burst += 1  # debounce

        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Konfetti
        for pt in self.particles:
            p.save()
            p.translate(pt.x, pt.y)
            p.rotate(pt.rot)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(pt.c))
            p.drawRect(-pt.pw//2, -pt.ph//2, pt.pw, pt.ph)
            p.restore()

        # Salyut ucqunlari
        for rk in self.rockets:
            for s in rk.sparks:
                if s[5] <= 0: continue
                c = QColor(rk.color)
                c.setAlpha(s[5])
                p.setPen(QPen(c, s[4], Qt.PenStyle.SolidLine,
                              Qt.PenCapStyle.RoundCap))
                p.drawPoint(int(s[0]), int(s[1]))

    def stop(self):
        self._timer.stop()


# ── Ball halqasi ──────────────────────────────────────────────────────────────
class ScoreRing(QWidget):
    def __init__(self, score: float, color: str, parent=None):
        super().__init__(parent)
        self.score   = score
        self.current = 0.0
        self.color   = QColor(color)
        self.setFixedSize(160, 160)
        self._t = QTimer(self)
        self._t.timeout.connect(self._anim)
        self._t.start(14)

    def _anim(self):
        if self.current < self.score:
            self.current = min(self.current + 1.8, self.score)
            self.update()
        else:
            self._t.stop()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        m = 16
        r = QRectF(m, m, self.width()-2*m, self.height()-2*m)
        p.setPen(QPen(QColor(255,255,255,40), 10))
        p.drawArc(r, 90*16, -360*16)
        p.setPen(QPen(self.color, 10, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        span = int(-self.current/100*360*16)
        p.drawArc(r, 90*16, span)
        p.setPen(QPen(QColor("white")))
        p.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, f"{self.current:.0f}%")


# ── Asosiy oyna ───────────────────────────────────────────────────────────────
class ResultWindow(QMainWindow):
    def __init__(self, result: dict):
        super().__init__()
        self.result = result
        self.grade  = str(result.get("grade", "2"))
        self.cfg    = _cfg(self.grade)
        self.setWindowTitle("Test natijasi")
        self.setMinimumSize(660, 560)
        self._setup_ui()
        self._center()

    def _center(self):
        sc = QGuiApplication.primaryScreen().geometry()
        self.move((sc.width()-self.width())//2, (sc.height()-self.height())//2)
        self.showMaximized()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if hasattr(self, "_fx"):
            self._fx.setGeometry(self.centralWidget().rect())
            self._fx.raise_()

    def _setup_ui(self):
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{
                background: {self.cfg['bg']};
                color: white;
                font-family: 'Segoe UI', Arial;
            }}
            QLabel  {{ background: transparent; color: white; }}
            QFrame  {{ background: transparent; }}
        """)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(50, 28, 50, 28)
        root.setSpacing(12)
        root.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # ── Sarlavha ──────────────────────────────────────────────────────────
        title = QLabel(self.cfg["title"])
        title.setFont(QFont("Segoe UI", 30, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"color: {self.cfg['accent']}; background: transparent;")
        root.addWidget(title)

        sub = QLabel(self.cfg["sub"])
        sub.setFont(QFont("Segoe UI", 13))
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet("color: rgba(255,255,255,0.80); background: transparent;")
        root.addWidget(sub)
        root.addSpacing(6)

        # ── O'quvchi info ─────────────────────────────────────────────────────
        info_card = QFrame()
        info_card.setStyleSheet("""
            QFrame {
                background: rgba(255,255,255,0.10);
                border-radius: 14px;
                border: 1px solid rgba(255,255,255,0.18);
            }
        """)
        ilay = QHBoxLayout(info_card)
        ilay.setContentsMargins(20, 12, 20, 12)
        ilay.setSpacing(20)

        def _info(icon, val):
            lbl = QLabel(f"{icon}  {val}")
            lbl.setFont(QFont("Segoe UI", 13))
            lbl.setStyleSheet("background: transparent; color: rgba(255,255,255,0.90);")
            return lbl

        ilay.addWidget(_info("👤", f"{self.result.get('student_name','')} {self.result.get('student_lastname','')}"))
        ilay.addWidget(QLabel("·"))
        ilay.addWidget(_info("🏫", self.result.get("student_class", "")))
        ilay.addWidget(QLabel("·"))
        ilay.addWidget(_info("📝", self.result.get("test_name", "")))
        root.addWidget(info_card)
        root.addSpacing(4)

        # ── Markaziy blok: halqa + statistika ────────────────────────────────
        center = QHBoxLayout()
        center.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center.setSpacing(50)

        ring = ScoreRing(self.result.get("score_percent", 0), self.cfg["accent"])
        center.addWidget(ring)

        stats = QVBoxLayout()
        stats.setSpacing(10)

        grade_lbl = QLabel(f"Baho: {self.grade}")
        grade_lbl.setFont(QFont("Segoe UI", 26, QFont.Weight.Bold))
        grade_lbl.setStyleSheet(f"color: {self.cfg['accent']}; background: transparent;")
        stats.addWidget(grade_lbl)

        total = self.result.get("total_questions", 0)
        correct = self.result.get("correct_count", 0)
        wrong   = self.result.get("wrong_count", 0)

        for ico, txt, clr in [
            ("✅", f"To'g'ri javoblar:  {correct} / {total}", "#69F0AE"),
            ("❌", f"Noto'g'ri javoblar: {wrong} / {total}", "#FF5252"),
        ]:
            l = QLabel(f"{ico}  {txt}")
            l.setFont(QFont("Segoe UI", 14))
            l.setStyleSheet(f"color: {clr}; background: transparent;")
            stats.addWidget(l)

        ts = self.result.get("time_spent")
        if ts:
            tl = QLabel(f"⏱  Vaqt: {ts//60} daq {ts%60} son")
            tl.setFont(QFont("Segoe UI", 13))
            tl.setStyleSheet("color: rgba(255,255,255,0.70); background: transparent;")
            stats.addWidget(tl)

        center.addLayout(stats)
        root.addLayout(center)
        root.addStretch()

        # ── Tugmalar ──────────────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.setSpacing(18)
        btn_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        def _btn(txt, style, cb):
            b = QPushButton(txt)
            b.setFixedSize(190, 50)
            b.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
            b.setStyleSheet(style)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.clicked.connect(cb)
            return b

        OUTLINE = """
            QPushButton {
                background: rgba(255,255,255,0.12);
                color: white;
                border: 2px solid rgba(255,255,255,0.35);
                border-radius: 12px;
            }
            QPushButton:hover { background: rgba(255,255,255,0.22); }
        """
        ORANGE = """
            QPushButton {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #FF6F00,stop:1 #FFA000);
                color: white; border: none; border-radius: 12px;
            }
            QPushButton:hover { background: #FFB300; }
        """
        btn_row.addWidget(_btn("🔄  Qayta urinish", OUTLINE, self._retry))
        btn_row.addWidget(_btn("🏠  Bosh sahifa",   ORANGE,  self._home))
        root.addLayout(btn_row)

        # ── FX overlay ────────────────────────────────────────────────────────
        self._fx = FXWidget(self.grade, central)
        self._fx.setGeometry(central.rect())
        self._fx.show()
        self._fx.raise_()

    def _retry(self):
        from ..student.info_window import StudentInfoWindow
        self._info = StudentInfoWindow(); self._info.show(); self.close()

    def _home(self):
        from ..student.info_window import StudentInfoWindow
        self._info = StudentInfoWindow(); self._info.show(); self.close()
