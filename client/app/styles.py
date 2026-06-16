"""
QSS stillari - zamonaviy, rang-barang dizayn.
"""
import os as _os

_ASSETS_DIR = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "assets")
_CHECK_SVG = _os.path.join(_ASSETS_DIR, "check.svg").replace("\\", "/")

# Asosiy ranglar
COLORS = {
    "primary": "#1565C0",
    "primary_dark": "#0D47A1",
    "primary_light": "#42A5F5",
    "accent": "#FF6F00",
    "accent_light": "#FFB300",
    "success": "#2E7D32",
    "success_light": "#4CAF50",
    "danger": "#C62828",
    "danger_light": "#EF5350",
    "warning": "#F57F17",
    "bg_dark": "#0A1929",
    "bg_medium": "#132F4C",
    "bg_light": "#173A5E",
    "text_primary": "#FFFFFF",
    "text_secondary": "#B0BEC5",
    "card_bg": "#1E3A5F",
    "border": "#2A5A8C",

    # O'quvchi interfeysi uchun yorqin ranglar
    "btn_a": "#E53935",     # Qizil
    "btn_b": "#1E88E5",     # Ko'k
    "btn_c": "#43A047",     # Yashil
    "btn_d": "#FB8C00",     # To'q sariq
}

MAIN_STYLE = f"""
QMainWindow, QDialog, QWidget {{
    background-color: {COLORS['bg_dark']};
    color: {COLORS['text_primary']};
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
}}

QLabel {{
    color: {COLORS['text_primary']};
    background: transparent;
}}

QLabel#subtitle {{
    color: {COLORS['text_secondary']};
    font-size: 12px;
}}

/* --- Tugmalar --- */
QPushButton {{
    background-color: {COLORS['primary']};
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-size: 13px;
    font-weight: bold;
    min-height: 36px;
}}

QPushButton:hover {{
    background-color: {COLORS['primary_light']};
}}

QPushButton:pressed {{
    background-color: {COLORS['primary_dark']};
}}

QPushButton:disabled {{
    background-color: #2A3A4A;
    color: #5A6A7A;
}}

QPushButton#danger {{
    background-color: {COLORS['danger']};
}}
QPushButton#danger:hover {{
    background-color: {COLORS['danger_light']};
}}

QPushButton#success {{
    background-color: {COLORS['success']};
}}
QPushButton#success:hover {{
    background-color: {COLORS['success_light']};
}}

QPushButton#secondary {{
    background-color: {COLORS['bg_light']};
    border: 1px solid {COLORS['border']};
}}
QPushButton#secondary:hover {{
    background-color: {COLORS['bg_medium']};
}}

/* --- Input --- */
QLineEdit, QTextEdit, QPlainTextEdit {{
    background-color: {COLORS['bg_medium']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 13px;
    min-height: 34px;
    selection-background-color: {COLORS['primary']};
}}

QLineEdit:focus, QTextEdit:focus {{
    border: 2px solid {COLORS['primary_light']};
}}

/* --- ComboBox --- */
QComboBox {{
    background-color: {COLORS['bg_medium']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 8px 12px;
    min-height: 34px;
    font-size: 13px;
}}

QComboBox::drop-down {{
    border: none;
    width: 30px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid {COLORS['text_secondary']};
    margin-right: 8px;
}}

QComboBox QAbstractItemView {{
    background-color: {COLORS['bg_medium']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    selection-background-color: {COLORS['primary']};
}}

/* --- TableWidget --- */
QTableWidget {{
    background-color: {COLORS['bg_medium']};
    color: {COLORS['text_primary']};
    gridline-color: {COLORS['border']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    font-size: 13px;
}}

QTableWidget::item {{
    padding: 8px 10px;
    border-bottom: 1px solid {COLORS['border']};
}}

QTableWidget::item:selected {{
    background-color: {COLORS['primary']};
    color: white;
}}

QHeaderView::section {{
    background-color: {COLORS['bg_light']};
    color: {COLORS['text_primary']};
    padding: 10px;
    border: none;
    border-right: 1px solid {COLORS['border']};
    font-weight: bold;
    font-size: 12px;
}}

/* --- TabWidget --- */
QTabWidget::pane {{
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    background-color: {COLORS['bg_medium']};
}}

QTabBar::tab {{
    background-color: {COLORS['bg_dark']};
    color: {COLORS['text_secondary']};
    padding: 10px 20px;
    border: 1px solid {COLORS['border']};
    border-bottom: none;
    border-radius: 6px 6px 0 0;
    font-size: 13px;
    min-width: 100px;
}}

QTabBar::tab:selected {{
    background-color: {COLORS['primary']};
    color: white;
    font-weight: bold;
}}

QTabBar::tab:hover:!selected {{
    background-color: {COLORS['bg_light']};
    color: {COLORS['text_primary']};
}}

/* --- ScrollBar --- */
QScrollBar:vertical {{
    background: {COLORS['bg_dark']};
    width: 10px;
    border-radius: 5px;
}}

QScrollBar::handle:vertical {{
    background: {COLORS['border']};
    border-radius: 5px;
    min-height: 30px;
}}

QScrollBar::handle:vertical:hover {{
    background: {COLORS['primary_light']};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

/* --- Sidebar tugmalari --- */
QPushButton#sidebar_btn {{
    background-color: transparent;
    color: {COLORS['text_secondary']};
    text-align: left;
    padding: 12px 20px;
    border-radius: 8px;
    font-size: 14px;
    font-weight: normal;
    min-height: 44px;
}}

QPushButton#sidebar_btn:hover {{
    background-color: {COLORS['bg_light']};
    color: {COLORS['text_primary']};
}}

QPushButton#sidebar_btn:checked {{
    background-color: {COLORS['primary']};
    color: white;
    font-weight: bold;
}}

/* --- Card --- */
QFrame#card {{
    background-color: {COLORS['card_bg']};
    border: 1px solid {COLORS['border']};
    border-radius: 12px;
}}

/* --- SpinBox --- */
QSpinBox, QDoubleSpinBox {{
    background-color: {COLORS['bg_medium']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 6px 10px;
    min-height: 34px;
}}

/* --- CheckBox --- */
QCheckBox {{
    color: {COLORS['text_primary']};
    spacing: 10px;
    font-size: 13px;
}}

QCheckBox::indicator {{
    width: 20px;
    height: 20px;
    border-radius: 5px;
    border: 2px solid {COLORS['border']};
    background: {COLORS['bg_medium']};
}}

QCheckBox::indicator:hover {{
    border-color: {COLORS['primary_light']};
    background: {COLORS['bg_light']};
}}

QCheckBox::indicator:checked {{
    background-color: {COLORS['primary']};
    border: 2px solid {COLORS['primary_light']};
    image: url("{_CHECK_SVG}");
}}

/* --- Table action buttons --- */
QPushButton#table_action {{
    background-color: {COLORS['bg_light']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    font-size: 15px;
    padding: 0px;
    min-height: 0px;
    min-width: 0px;
}}

QPushButton#table_action:hover {{
    background-color: {COLORS['primary']};
    border-color: {COLORS['primary_light']};
}}

QPushButton#table_action:pressed {{
    background-color: {COLORS['primary_dark']};
}}

QPushButton#table_action_danger {{
    background-color: {COLORS['bg_light']};
    color: {COLORS['danger_light']};
    border: 1px solid {COLORS['danger']};
    border-radius: 6px;
    font-size: 15px;
    padding: 0px;
    min-height: 0px;
    min-width: 0px;
}}

QPushButton#table_action_danger:hover {{
    background-color: {COLORS['danger']};
    color: white;
    border-color: {COLORS['danger_light']};
}}

QPushButton#table_action_danger:pressed {{
    background-color: #8B0000;
}}

/* --- MessageBox --- */
QMessageBox {{
    background-color: {COLORS['bg_medium']};
    color: {COLORS['text_primary']};
}}

/* --- ProgressBar --- */
QProgressBar {{
    background-color: {COLORS['bg_dark']};
    border-radius: 6px;
    height: 12px;
    text-align: center;
    color: white;
    font-size: 11px;
    border: 1px solid {COLORS['border']};
}}

QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {COLORS['primary']}, stop:1 {COLORS['primary_light']});
    border-radius: 6px;
}}

/* --- Tooltip --- */
QToolTip {{
    background-color: {COLORS['bg_medium']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    padding: 5px 8px;
    border-radius: 4px;
}}

/* --- Dialog Header / Footer --- */
QFrame#dialog_header {{
    background-color: {COLORS['bg_light']};
    border-bottom: 1px solid {COLORS['border']};
}}

QFrame#dialog_footer {{
    background-color: {COLORS['bg_medium']};
    border-top: 1px solid {COLORS['border']};
}}

/* --- GroupBox --- */
QGroupBox {{
    background-color: transparent;
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    margin-top: 10px;
    padding-top: 8px;
    font-size: 13px;
    font-weight: bold;
    color: {COLORS['primary_light']};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    color: {COLORS['primary_light']};
    left: 12px;
}}

/* --- ScrollArea --- */
QScrollArea {{
    background-color: {COLORS['bg_dark']};
    border: none;
}}

QScrollArea > QWidget > QWidget {{
    background-color: {COLORS['bg_dark']};
}}
"""

# O'quvchi ekrani uchun maxsus stil
STUDENT_STYLE = f"""
QMainWindow, QDialog, QWidget {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #0D47A1, stop:0.5 #1565C0, stop:1 #0277BD);
    color: white;
    font-family: 'Segoe UI', Arial, sans-serif;
}}

QLabel {{
    color: white;
    background: transparent;
}}
"""

# Login oynasi stili
LOGIN_STYLE = f"""
QWidget {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #0A1929, stop:0.6 #132F4C, stop:1 #0A1929);
    color: white;
    font-family: 'Segoe UI', Arial, sans-serif;
}}

QLineEdit {{
    background-color: rgba(255,255,255,0.1);
    color: white;
    border: 1px solid rgba(255,255,255,0.3);
    border-radius: 10px;
    padding: 12px 16px;
    font-size: 14px;
    min-height: 44px;
}}

QLineEdit:focus {{
    border: 2px solid {COLORS['primary_light']};
    background-color: rgba(255,255,255,0.15);
}}

QPushButton#login_btn {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {COLORS['primary']}, stop:1 {COLORS['primary_light']});
    color: white;
    border: none;
    border-radius: 10px;
    padding: 14px;
    font-size: 16px;
    font-weight: bold;
    min-height: 50px;
}}

QPushButton#login_btn:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {COLORS['primary_light']}, stop:1 {COLORS['accent_light']});
}}
"""
