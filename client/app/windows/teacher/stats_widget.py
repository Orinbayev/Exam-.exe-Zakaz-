"""
Statistika widget - diagrammalar, reyting, umumiy ko'rsatkichlar.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor
from ...api_client import api, APIError
from ...styles import COLORS

try:
    import matplotlib
    matplotlib.use("QtAgg")
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    import matplotlib.pyplot as plt
    MATPLOTLIB_OK = True
except Exception:
    MATPLOTLIB_OK = False


class ChartWidget(QWidget):
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(260)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        if MATPLOTLIB_OK:
            self.fig = Figure(figsize=(5, 3.5), facecolor="#132F4C")
            self.canvas = FigureCanvas(self.fig)
            self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            layout.addWidget(self.canvas)
        else:
            label = QLabel("📊 Diagrammalar uchun matplotlib kerak:\npip install matplotlib")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet(f"color: {COLORS['text_secondary']};")
            layout.addWidget(label)

    def draw_bar(self, labels, values, title, color="#42A5F5"):
        if not MATPLOTLIB_OK:
            return
        self.fig.clear()
        ax = self.fig.add_subplot(111, facecolor="#0A1929")
        bars = ax.bar(labels, values, color=color, alpha=0.85, edgecolor="#FFFFFF", linewidth=0.5)
        ax.set_title(title, color="white", fontsize=11, pad=10)
        ax.tick_params(colors="white", labelsize=9)
        ax.spines[:].set_color("#2A5A8C")
        ax.set_facecolor("#0A1929")
        for bar, val in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                    f"{val:.1f}", ha="center", va="bottom", color="white", fontsize=9)
        self.fig.tight_layout(pad=1.5)
        self.canvas.draw()

    def draw_pie(self, labels, values, title, colors=None):
        if not MATPLOTLIB_OK:
            return
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        colors = colors or ["#42A5F5", "#EF5350", "#66BB6A", "#FFA726"]
        wedges, texts, autotexts = ax.pie(
            values, labels=labels, colors=colors[:len(values)],
            autopct="%1.1f%%", startangle=90,
            textprops={"color": "white", "fontsize": 9}
        )
        ax.set_title(title, color="white", fontsize=11, pad=10)
        self.fig.set_facecolor("#132F4C")
        self.fig.tight_layout(pad=1.5)
        self.canvas.draw()


class StatsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.refresh()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        toolbar = QHBoxLayout()
        title = QLabel("📈 Statistika")
        title.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))

        refresh_btn = QPushButton("🔄 Yangilash")
        refresh_btn.setObjectName("secondary")
        refresh_btn.clicked.connect(self.refresh)

        toolbar.addWidget(title)
        toolbar.addStretch()
        toolbar.addWidget(refresh_btn)
        layout.addLayout(toolbar)

        # Summary cards
        self.cards_layout = QHBoxLayout()
        self.card_widgets = {}
        card_defs = [
            ("total", "Jami urinishlar", "0", COLORS["primary"]),
            ("passed", "O'tdi", "0", COLORS["success"]),
            ("failed", "Yiqildi", "0", COLORS["danger"]),
            ("avg", "O'rtacha ball", "0%", COLORS["accent"]),
            ("pass_rate", "O'tish darajasi", "0%", "#7B1FA2"),
        ]
        for key, title_text, default, color in card_defs:
            card = self._make_stat_card(title_text, default, color)
            self.card_widgets[key] = card
            self.cards_layout.addWidget(card["frame"])
        layout.addLayout(self.cards_layout)

        # Charts row
        charts_layout = QHBoxLayout()
        self.grade_chart = ChartWidget("Baholar taqsimoti")
        self.test_chart = ChartWidget("Testlar bo'yicha")
        charts_layout.addWidget(self.grade_chart)
        charts_layout.addWidget(self.test_chart)
        layout.addLayout(charts_layout)

        # Top students
        top_label = QLabel("🏆 Top 10 O'quvchilar")
        top_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        layout.addWidget(top_label)

        self.top_table = QTableWidget()
        self.top_table.setColumnCount(6)
        self.top_table.setHorizontalHeaderLabels(
            ["#", "Ism", "Familiya", "Sinf", "Test", "Ball"]
        )
        self.top_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.top_table.setColumnWidth(0, 40)
        self.top_table.setColumnWidth(1, 120)
        self.top_table.setColumnWidth(2, 120)
        self.top_table.setColumnWidth(3, 70)
        self.top_table.setColumnWidth(5, 80)
        self.top_table.setMaximumHeight(250)
        self.top_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.top_table.verticalHeader().setVisible(False)
        layout.addWidget(self.top_table)

    def _make_stat_card(self, title: str, value: str, color: str) -> dict:
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {color}, stop:1 {color}CC);
                border-radius: 12px;
            }}
        """)
        frame.setMinimumHeight(75)
        inner = QVBoxLayout(frame)
        inner.setContentsMargins(14, 10, 14, 10)

        val_label = QLabel(value)
        val_label.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        val_label.setStyleSheet("color: white; background: transparent;")

        title_label = QLabel(title)
        title_label.setStyleSheet("color: rgba(255,255,255,0.85); font-size: 11px; background: transparent;")

        inner.addWidget(val_label)
        inner.addWidget(title_label)
        return {"frame": frame, "value": val_label}

    def refresh(self):
        try:
            overview = api.get_stats_overview()
            self.card_widgets["total"]["value"].setText(str(overview.get("total_sessions", 0)))
            self.card_widgets["passed"]["value"].setText(str(overview.get("total_passed", 0)))
            self.card_widgets["failed"]["value"].setText(str(overview.get("total_failed", 0)))
            self.card_widgets["avg"]["value"].setText(f"{overview.get('average_score', 0):.1f}%")
            self.card_widgets["pass_rate"]["value"].setText(f"{overview.get('pass_rate', 0):.1f}%")
        except APIError:
            pass

        try:
            grade_dist = api.get_grade_distribution()
            if grade_dist:
                grades = sorted(grade_dist.keys())
                counts = [grade_dist[g] for g in grades]
                colors_map = {"5": "#66BB6A", "4": "#42A5F5", "3": "#FFA726", "2": "#EF5350", "N/A": "#9E9E9E"}
                chart_colors = [colors_map.get(g, "#42A5F5") for g in grades]
                self.grade_chart.draw_pie(
                    [f"Baho {g}" for g in grades], counts, "Baholar taqsimoti", chart_colors
                )
        except APIError:
            pass

        try:
            test_stats = api.get_stats_by_test()
            if test_stats:
                names = [t["test_name"][:15] + "..." if len(t["test_name"]) > 15 else t["test_name"]
                         for t in test_stats[:6]]
                avgs = [t["average_score"] for t in test_stats[:6]]
                self.test_chart.draw_bar(names, avgs, "Testlar o'rtacha bali (%)", "#42A5F5")
        except APIError:
            pass

        try:
            top_students = api.get_top_students()
            self.top_table.setRowCount(len(top_students))
            for row, s in enumerate(top_students):
                self.top_table.setRowHeight(row, 38)
                medal = ["🥇", "🥈", "🥉"][row] if row < 3 else str(row + 1)
                for col, val in enumerate([
                    medal,
                    s.get("student_name", ""),
                    s.get("student_lastname", ""),
                    s.get("student_class", ""),
                    s.get("test_name", ""),
                    f"{s.get('score_percent', 0):.1f}%"
                ]):
                    item = QTableWidgetItem(val)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    if col == 5:
                        item.setForeground(QColor(COLORS["success_light"]))
                    self.top_table.setItem(row, col, item)
        except APIError:
            pass
