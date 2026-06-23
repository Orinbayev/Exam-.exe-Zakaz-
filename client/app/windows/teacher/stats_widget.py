"""
Statistika widget - QPainter diagrammalari, reyting, umumiy ko'rsatkichlar.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QSizePolicy, QDialog, QLineEdit, QMessageBox
)
from PyQt6.QtCore import Qt, QRect, QRectF
from PyQt6.QtGui import (
    QFont, QColor, QPainter, QPen, QBrush,
    QLinearGradient, QPainterPath
)
from ...api_client import api, APIError
from ...styles import COLORS
from ...worker import ApiWorker
from ...i18n import t


# ── Bar Chart (QPainter) ──────────────────────────────────────────────────────

class BarChartWidget(QWidget):
    _PT, _PR, _PB, _PL = 48, 18, 58, 56

    def __init__(self, title: str = "", color: str = "#42A5F5", parent=None):
        super().__init__(parent)
        self.title = title
        self._color = QColor(color)
        self._labels: list = []
        self._values: list = []
        self.setMinimumHeight(200)
        self.setMaximumHeight(270)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

    def set_data(self, labels: list, values: list, color: str = None):
        self._labels = [str(l) for l in labels]
        self._values = [float(v) for v in values]
        if color:
            self._color = QColor(color)
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, w, h), 12, 12)
        p.fillPath(path, QColor("#0D2137"))

        p.setPen(QColor(COLORS["text_primary"]))
        p.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        p.drawText(QRect(0, 10, w, 26), Qt.AlignmentFlag.AlignCenter, self.title)

        if not self._values:
            p.setPen(QColor(COLORS["text_secondary"]))
            p.setFont(QFont("Segoe UI", 10))
            p.drawText(QRect(0, 0, w, h), Qt.AlignmentFlag.AlignCenter, t("stat.no_data"))
            return

        pt, pr, pb, pl = self._PT, self._PR, self._PB, self._PL
        cx, cy = pl, pt
        cw, ch = w - pl - pr, h - pt - pb
        n = len(self._values)
        max_v = max(self._values) if self._values else 1
        if max_v == 0:
            max_v = 1
        slot = cw / n if n else cw
        bar_w = max(int(slot * 0.55), 6)

        for i in range(5):
            frac = i / 4.0
            gy = int(cy + ch * (1.0 - frac))
            p.setPen(QPen(QColor("#1E3A5F"), 1, Qt.PenStyle.DashLine))
            p.drawLine(cx, gy, cx + cw, gy)
            p.setPen(QColor("#7A9CC0"))
            p.setFont(QFont("Segoe UI", 8))
            p.drawText(QRect(0, gy - 9, cx - 6, 18),
                       Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                       f"{max_v * frac:.0f}")

        for i, (lbl, val) in enumerate(zip(self._labels, self._values)):
            bh = int((val / max_v) * ch)
            bx = int(cx + i * slot + (slot - bar_w) / 2)
            by = cy + ch - bh

            if bh > 0:
                grad = QLinearGradient(bx, by, bx, by + bh)
                grad.setColorAt(0.0, self._color.lighter(145))
                grad.setColorAt(1.0, self._color)
                p.setBrush(QBrush(grad))
                p.setPen(Qt.PenStyle.NoPen)
                p.drawRoundedRect(bx, by, bar_w, bh, 4, 4)

                p.setPen(QColor(COLORS["text_primary"]))
                p.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
                p.drawText(QRect(bx - 14, by - 20, bar_w + 28, 18),
                           Qt.AlignmentFlag.AlignCenter, f"{val:.1f}")

            p.setPen(QColor("#B0BEC5"))
            p.setFont(QFont("Segoe UI", 8))
            p.drawText(QRect(int(cx + i * slot), cy + ch + 6, int(slot), 46),
                       Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, lbl)

        p.setPen(QPen(QColor("#2A5A8C"), 1))
        p.drawLine(cx, cy, cx, cy + ch)
        p.drawLine(cx, cy + ch, cx + cw, cy + ch)


# ── Pie Chart (QPainter) ──────────────────────────────────────────────────────

class PieChartWidget(QWidget):
    _COLORS = ["#42A5F5", "#66BB6A", "#FFA726", "#EF5350", "#AB47BC", "#26C6DA"]

    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self.title = title
        self._labels: list = []
        self._values: list = []
        self._colors: list = self._COLORS[:]
        self.setMinimumHeight(200)
        self.setMaximumHeight(270)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

    def set_data(self, labels: list, values: list, colors: list = None):
        self._labels = [str(l) for l in labels]
        self._values = [float(v) for v in values]
        if colors:
            self._colors = list(colors)
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, w, h), 12, 12)
        p.fillPath(path, QColor("#0D2137"))

        p.setPen(QColor(COLORS["text_primary"]))
        p.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        p.drawText(QRect(0, 10, w, 26), Qt.AlignmentFlag.AlignCenter, self.title)

        if not self._values:
            p.setPen(QColor(COLORS["text_secondary"]))
            p.setFont(QFont("Segoe UI", 10))
            p.drawText(QRect(0, 0, w, h), Qt.AlignmentFlag.AlignCenter, t("stat.no_data"))
            return

        total = sum(self._values)
        if total == 0:
            return

        # ── Pie size: max 180px, centred vertically ──────────────────────────
        avail_h  = h - 42
        pie_size = max(80, min(180, avail_h))
        pie_x    = 16
        pie_y    = 36 + (avail_h - pie_size) // 2

        pie_rect = QRect(pie_x, pie_y, pie_size, pie_size)

        start = 90 * 16
        for i, val in enumerate(self._values):
            span = int(round(val / total * 360 * 16))
            color = QColor(self._colors[i % len(self._colors)])
            p.setBrush(QBrush(color))
            p.setPen(QPen(QColor("#0A1929"), 2))
            p.drawPie(pie_rect, start, -span)
            start -= span

        # ── Legend: fixed-width columns right of pie ──────────────────────
        # Layout per row:  ● (12) + gap(6) + label(78) + gap(8) + pct(44) = 148px
        DOT   = 12
        GAP1  = 6
        LBL_W = 78
        GAP2  = 8
        PCT_W = 44
        ROW_W = DOT + GAP1 + LBL_W + GAP2 + PCT_W   # 148px total

        lx     = pie_x + pie_size + 20
        n      = max(len(self._labels), 1)
        item_h = max(28, min(36, avail_h // n))
        ly0    = pie_y + (pie_size - n * item_h) // 2

        for i, (lbl, val) in enumerate(zip(self._labels, self._values)):
            color = QColor(self._colors[i % len(self._colors)])
            pct   = val / total * 100
            ly    = ly0 + i * item_h
            cy    = ly + (item_h - DOT) // 2

            # Dot
            p.setBrush(QBrush(color))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(lx, cy, DOT, DOT)

            # Label
            p.setPen(QColor(COLORS["text_primary"]))
            p.setFont(QFont("Segoe UI", 9))
            p.drawText(
                QRect(lx + DOT + GAP1, ly, LBL_W, item_h),
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                lbl,
            )

            # Percentage — fixed position right after label
            p.setPen(color)
            p.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            p.drawText(
                QRect(lx + DOT + GAP1 + LBL_W + GAP2, ly, PCT_W, item_h),
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                f"{pct:.0f}%",
            )


# ── All Results Dialog ────────────────────────────────────────────────────────

class AllResultsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("stat.all_dlg_title"))
        self.setMinimumSize(1020, 620)
        self._all: list = []
        self._setup_ui()
        self._load()

    def _setup_ui(self):
        lay = QVBoxLayout(self)
        lay.setSpacing(10)
        lay.setContentsMargins(16, 16, 16, 16)

        hdr = QHBoxLayout()
        title = QLabel(t("stat.all_dlg_lbl"))
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))

        self._search = QLineEdit()
        self._search.setPlaceholderText(t("stat.all_search_ph"))
        self._search.setMaximumWidth(260)
        self._search.textChanged.connect(self._filter)

        close_btn = QPushButton(t("stat.all_close_btn"))
        close_btn.setObjectName("secondary")
        close_btn.clicked.connect(self.accept)

        hdr.addWidget(title)
        hdr.addStretch()
        hdr.addWidget(self._search)
        hdr.addWidget(close_btn)
        lay.addLayout(hdr)

        self._summary = QLabel("")
        self._summary.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: 12px;"
        )
        lay.addWidget(self._summary)

        self._table = QTableWidget()
        self._table.setColumnCount(9)
        self._table.setHorizontalHeaderLabels([
            t("stat.all_col_num"), t("stat.all_col_date"), t("stat.all_col_name"),
            t("stat.all_col_last"), t("stat.all_col_class"), t("stat.all_col_test"),
            t("stat.all_col_correct"), t("stat.all_col_pct"), t("stat.all_col_result"),
        ])
        hh = self._table.horizontalHeader()
        hh.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        self._table.setColumnWidth(0, 46)
        self._table.setColumnWidth(1, 130)
        self._table.setColumnWidth(2, 110)
        self._table.setColumnWidth(3, 120)
        self._table.setColumnWidth(4, 65)
        self._table.setColumnWidth(6, 80)
        self._table.setColumnWidth(7, 75)
        self._table.setColumnWidth(8, 90)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.setSortingEnabled(True)
        self._table.setAlternatingRowColors(True)
        self._table.setStyleSheet(
            "QTableWidget { alternate-background-color: rgba(255,255,255,0.03); }"
        )
        lay.addWidget(self._table)

    def _load(self):
        try:
            self._all = api.get_results()
            self._render(self._all)
            total  = len(self._all)
            passed = sum(1 for r in self._all if r.get("is_passed"))
            scores = [r.get("score_percent", 0) for r in self._all]
            avg    = sum(scores) / len(scores) if scores else 0
            self._summary.setText(
                t("stat.all_summary", total=total, passed=passed,
                  failed=total-passed, avg=avg)
            )
        except APIError as e:
            QMessageBox.warning(self, t("common.error"), str(e))

    def _filter(self):
        q = self._search.text().lower()
        if not q:
            self._render(self._all)
            return
        filtered = [
            r for r in self._all
            if q in r.get("student_name", "").lower()
            or q in r.get("student_lastname", "").lower()
            or q in r.get("test_name", "").lower()
        ]
        self._render(filtered)

    def _render(self, results: list):
        srt = sorted(results, key=lambda r: r.get("score_percent", 0), reverse=True)
        self._table.setRowCount(len(srt))
        for row, r in enumerate(srt):
            self._table.setRowHeight(row, 40)
            score = r.get("score_percent", 0)
            date  = (r.get("end_time") or r.get("start_time") or "")[:16].replace("T", " ")
            vals  = [
                str(row + 1),
                date,
                r.get("student_name", ""),
                r.get("student_lastname", ""),
                r.get("student_class", ""),
                r.get("test_name", "—"),
                f"{r.get('correct_count', 0)}/{r.get('total_questions', 0)}",
                f"{score:.1f}%",
                t("stat.all_passed") if r.get("is_passed") else t("stat.all_failed"),
            ]
            for col, val in enumerate(vals):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if col == 7:
                    item.setForeground(
                        QColor(COLORS["success_light"]) if score >= 60
                        else QColor(COLORS["danger_light"])
                    )
                elif col == 8:
                    item.setForeground(
                        QColor(COLORS["success_light"]) if r.get("is_passed")
                        else QColor(COLORS["danger_light"])
                    )
                self._table.setItem(row, col, item)


# ── StatsWidget ───────────────────────────────────────────────────────────────

class StatsWidget(QWidget):
    # Card titles now use t() so we store only the key, fetched in _setup_ui
    _CARDS_DEF = [
        ("total",     "stat.card_total",  "0",   "#0D47A1", "#42A5F5", "📋"),
        ("passed",    "stat.card_passed", "0",   "#1B5E20", "#66BB6A", "✅"),
        ("failed",    "stat.card_failed", "0",   "#B71C1C", "#EF5350", "❌"),
        ("avg",       "stat.card_avg",    "0%",  "#E65100", "#FFA726", "📊"),
        ("pass_rate", "stat.card_rate",   "0%",  "#4A148C", "#AB47BC", "🎯"),
    ]

    # Top-3 row colours
    _TOP_BG = ["#2A1D00", "#18181E", "#1A0E00"]   # gold / silver / bronze tint
    _TOP_FG = ["#FFD700", "#C0C0C0", "#CD7F32"]
    _TOP_LBL = ["1", "2", "3"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._card_labels: dict = {}
        self._setup_ui()
        self.refresh()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(14)

        # Toolbar
        toolbar = QHBoxLayout()
        title_lbl = QLabel(t("stat.title_lbl"))
        title_lbl.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        refresh_btn = QPushButton(t("stat.refresh_btn"))
        refresh_btn.setObjectName("secondary")
        refresh_btn.clicked.connect(self.refresh)
        toolbar.addWidget(title_lbl)
        toolbar.addStretch()
        toolbar.addWidget(refresh_btn)
        root.addLayout(toolbar)

        # Summary cards
        cards_row = QHBoxLayout()
        cards_row.setSpacing(10)
        for key, title_key, default, c1, c2, icon in self._CARDS_DEF:
            card, val_lbl = self._make_card(t(title_key), default, c1, c2, icon)
            self._card_labels[key] = val_lbl
            cards_row.addWidget(card)
        root.addLayout(cards_row)

        # Charts
        charts_row = QHBoxLayout()
        charts_row.setSpacing(12)
        self._pie = PieChartWidget(t("stat.chart_pie"))
        self._bar = BarChartWidget(t("stat.chart_bar"), "#42A5F5")
        charts_row.addWidget(self._pie)
        charts_row.addWidget(self._bar)
        root.addLayout(charts_row)

        # Top students header
        top_hdr = QHBoxLayout()
        top_lbl = QLabel(t("stat.top_hdr"))
        top_lbl.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))

        see_all_btn = QPushButton(t("stat.see_all_btn"))
        see_all_btn.setObjectName("secondary")
        see_all_btn.clicked.connect(self._open_all_results)

        top_hdr.addWidget(top_lbl)
        top_hdr.addStretch()
        top_hdr.addWidget(see_all_btn)
        root.addLayout(top_hdr)

        # Top students table
        self._table = QTableWidget()
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels(
            [t("stat.tbl_rank"), t("stat.tbl_name"), t("stat.tbl_last"),
             t("stat.tbl_class"), t("stat.tbl_test"), t("stat.tbl_score")]
        )
        hdr = self._table.horizontalHeader()
        hdr.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        hdr.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(0, 46)
        self._table.setColumnWidth(1, 120)
        self._table.setColumnWidth(2, 130)
        self._table.setColumnWidth(3, 72)
        self._table.setColumnWidth(5, 90)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.setMaximumHeight(300)
        self._table.setAlternatingRowColors(True)
        self._table.setStyleSheet(
            "QTableWidget { alternate-background-color: rgba(255,255,255,0.03); }"
        )
        root.addWidget(self._table)
        root.addStretch()

    def _make_card(self, title: str, value: str, c1: str, c2: str, icon: str):
        frame = QFrame()
        frame.setFixedHeight(100)
        frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {c1}, stop:1 {c2});
                border-radius: 14px;
            }}
        """)
        outer = QHBoxLayout(frame)
        outer.setContentsMargins(14, 10, 14, 10)
        outer.setSpacing(10)

        icon_lbl = QLabel(icon)
        icon_lbl.setFont(QFont("Segoe UI Emoji", 20))
        icon_lbl.setStyleSheet("background: transparent; color: rgba(255,255,255,0.9);")
        icon_lbl.setFixedWidth(32)

        col = QVBoxLayout()
        col.setSpacing(2)
        val_lbl = QLabel(value)
        val_lbl.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        val_lbl.setStyleSheet("color: white; background: transparent;")
        ttl_lbl = QLabel(title)
        ttl_lbl.setStyleSheet(
            "color: rgba(255,255,255,0.80); font-size: 10px; background: transparent;"
        )
        col.addWidget(val_lbl)
        col.addWidget(ttl_lbl)

        outer.addWidget(icon_lbl)
        outer.addLayout(col)
        outer.addStretch()
        return frame, val_lbl

    # ── Refresh ───────────────────────────────────────────────────────────────

    def refresh(self):
        self._w_ov  = ApiWorker(api.get_stats_overview);    self._w_ov.done.connect(self._apply_overview);    self._w_ov.start()
        self._w_gd  = ApiWorker(api.get_grade_distribution); self._w_gd.done.connect(self._apply_grade_chart); self._w_gd.start()
        self._w_ts  = ApiWorker(api.get_stats_by_test);      self._w_ts.done.connect(self._apply_test_chart);  self._w_ts.start()
        self._w_top = ApiWorker(api.get_top_students);       self._w_top.done.connect(self._load_top_students); self._w_top.start()

    def _apply_overview(self, ov):
        self._card_labels["total"].setText(str(ov.get("total_sessions", 0)))
        self._card_labels["passed"].setText(str(ov.get("total_passed", 0)))
        self._card_labels["failed"].setText(str(ov.get("total_failed", 0)))
        self._card_labels["avg"].setText(f"{ov.get('average_score', 0):.1f}%")
        self._card_labels["pass_rate"].setText(f"{ov.get('pass_rate', 0):.1f}%")

    def _apply_grade_chart(self, gd):
        if not gd:
            return
        grade_colors = {
            "5": "#66BB6A", "4": "#42A5F5",
            "3": "#FFA726", "2": "#EF5350", "N/A": "#9E9E9E",
        }
        grades = sorted(gd.keys())
        self._pie.set_data(
            [t("stat.grade_lbl", g=g) for g in grades],
            [gd[g] for g in grades],
            [grade_colors.get(g, "#42A5F5") for g in grades],
        )

    def _apply_test_chart(self, ts):
        if not ts:
            return
        names, avgs = [], []
        for t in ts[:8]:
            n = t["test_name"]
            names.append((n[:12] + "…") if len(n) > 12 else n)
            avgs.append(t["average_score"])
        self._bar.set_data(names, avgs, "#42A5F5")

    def _load_top_students(self, students):
        try:
            self._table.setRowCount(len(students))

            for row, s in enumerate(students):
                self._table.setRowHeight(row, 46)
                score   = s.get("score_percent", 0)
                is_top  = row < 3

                rank_text  = self._TOP_LBL[row] if is_top else str(row + 1)
                rank_color = QColor(self._TOP_FG[row]) if is_top else QColor(COLORS["text_secondary"])
                row_bg     = QColor(self._TOP_BG[row]) if is_top else None

                values = [
                    rank_text,
                    s.get("student_name", ""),
                    s.get("student_lastname", ""),
                    s.get("student_class", ""),
                    s.get("test_name", ""),
                    f"{score:.1f}%",
                ]

                for col, val in enumerate(values):
                    item = QTableWidgetItem(val)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                    if row_bg:
                        item.setBackground(row_bg)

                    if col == 0:
                        item.setForeground(rank_color)
                        if is_top:
                            item.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
                    elif col == 5:
                        item.setForeground(
                            QColor(COLORS["success_light"]) if score >= 60
                            else QColor(COLORS["danger_light"])
                        )

                    self._table.setItem(row, col, item)
        except APIError:
            pass

    def _open_all_results(self):
        AllResultsDialog(parent=self).exec()
