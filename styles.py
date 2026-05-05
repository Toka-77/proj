"""
styles.py — Dark & Light themes for AIS Hub.
"""

# ── Dark Theme ────────────────────────────────────────────────
DARK = {
    "bg":       "#0b0d14",
    "sidebar":  "#111320",
    "card":     "#161929",
    "card2":    "#1a1d30",
    "accent":   "#7c5cbf",
    "accent2":  "#9b7ae0",
    "text":     "#e0e4f0",
    "sub":      "#6b7a99",
    "border":   "#252840",
    "green":    "#3ecf8e",
    "red":      "#f06292",
    "orange":   "#ffa726",
    "blue":     "#5c9cf5",
    "input_bg": "#0d0f18",
    "hover":    "#1e2138",
}

# ── Light Theme ───────────────────────────────────────────────
LIGHT = {
    "bg":       "#f0f2f8",
    "sidebar":  "#ffffff",
    "card":     "#ffffff",
    "card2":    "#f7f9ff",
    "accent":   "#7c5cbf",
    "accent2":  "#9b7ae0",
    "text":     "#1a1d2e",
    "sub":      "#7a869a",
    "border":   "#e0e4f0",
    "green":    "#1a9e65",
    "red":      "#d63060",
    "orange":   "#e67e22",
    "blue":     "#2d7dd2",
    "input_bg": "#f7f9ff",
    "hover":    "#ede9f7",
}

# Default at startup
T = DARK


def _build_qss(T):
    return f"""
/* ── Base ─────────────────────────────────────────── */
QMainWindow, QWidget#root {{ background:{T['bg']}; }}
QWidget#sidebar {{ background:{T['sidebar']}; border-right:1px solid {T['border']}; }}
QWidget#card {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 {T['card']}, stop:1 {T['card2']});
    border:1px solid {T['border']}; border-radius:14px;
}}

/* ── Labels ───────────────────────────────────────── */
QLabel {{ color:{T['text']}; font-family:'Segoe UI','Inter',sans-serif; }}
QLabel#title {{ font-size:24px; font-weight:800; color:{T['text']}; letter-spacing:0.5px; }}
QLabel#subtitle {{ font-size:13px; color:{T['sub']}; }}
QLabel#stat_val {{ font-size:28px; font-weight:800; }}
QLabel#stat_lbl {{ font-size:11px; color:{T['sub']}; text-transform:uppercase; letter-spacing:1px; }}
QLabel#sec_title {{ font-size:15px; font-weight:700; color:{T['text']}; }}

/* ── Nav Buttons ──────────────────────────────────── */
QPushButton#nav_btn {{
    background:transparent; color:{T['sub']}; border:none; border-radius:10px;
    padding:12px 18px; font-size:14px; font-family:'Segoe UI'; text-align:left;
}}
QPushButton#nav_btn:hover {{ background:{T['hover']}; color:{T['text']}; }}
QPushButton#nav_btn:checked {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 {T['accent']}, stop:1 #6a4aad);
    color:#ffffff; font-weight:600;
}}

/* ── Icon/Util Buttons ────────────────────────────── */
QPushButton#icon_btn {{
    background:transparent; color:{T['sub']}; border:1px solid {T['border']};
    border-radius:8px; padding:6px 12px; font-size:13px;
}}
QPushButton#icon_btn:hover {{ background:{T['hover']}; color:{T['text']}; }}

/* ── Action Buttons ───────────────────────────────── */
QPushButton#primary {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 {T['accent']}, stop:1 {T['accent2']});
    color:#fff; border:none; border-radius:9px;
    padding:10px 24px; font-size:13px; font-weight:600; font-family:'Segoe UI';
}}
QPushButton#primary:hover {{ background:{T['accent2']}; }}
QPushButton#danger {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #a0234a, stop:1 #c0345a);
    color:#fff; border:none; border-radius:9px;
    padding:10px 24px; font-size:13px; font-weight:600;
}}
QPushButton#danger:hover {{ background:{T['red']}; }}
QPushButton#secondary {{
    background:transparent; color:{T['accent']}; border:1px solid {T['accent']};
    border-radius:9px; padding:9px 20px; font-size:13px; font-weight:600;
}}
QPushButton#secondary:hover {{ background:{T['accent']}; color:#fff; }}

/* ── Inputs ───────────────────────────────────────── */
QLineEdit, QSpinBox, QDoubleSpinBox {{
    background:{T['input_bg']}; color:{T['text']}; border:1px solid {T['border']};
    border-radius:8px; padding:9px 14px; font-size:13px; font-family:'Segoe UI';
}}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
    border:1px solid {T['accent']};
}}
QComboBox {{
    background:{T['input_bg']}; color:{T['text']}; border:1px solid {T['border']};
    border-radius:8px; padding:9px 14px; font-size:13px; font-family:'Segoe UI';
}}
QComboBox:focus {{ border:1px solid {T['accent']}; }}
QComboBox::drop-down {{ border:none; width:24px; }}
QComboBox QAbstractItemView {{
    background:{T['card']}; color:{T['text']}; border:1px solid {T['border']};
    selection-background-color:{T['accent']}; selection-color:#fff;
    outline:none; padding:4px;
}}

/* ── Date / Time Inputs ───────────────────────────── */
QDateEdit, QTimeEdit {{
    background:{T['input_bg']}; color:{T['text']}; border:1px solid {T['border']};
    border-radius:8px; padding:9px 14px; font-size:13px; font-family:'Segoe UI';
}}
QDateEdit:focus, QTimeEdit:focus {{ border:1px solid {T['accent']}; }}
QDateEdit::drop-down, QTimeEdit::drop-down {{ border:none; width:24px; }}
QCalendarWidget QAbstractItemView {{
    background:{T['card']}; color:{T['text']};
    selection-background-color:{T['accent']}; selection-color:#fff;
}}
QCalendarWidget QWidget {{ background:{T['sidebar']}; color:{T['text']}; }}
QCalendarWidget QToolButton {{ color:{T['text']}; background:{T['sidebar']}; border:none; }}

/* ── Progress Bar ─────────────────────────────────── */
QProgressBar {{
    border:none; border-radius:4px;
    background:{T['border']}; max-height:10px;
}}
QProgressBar::chunk {{ background:{T['accent']}; border-radius:4px; }}

/* ── Tables ───────────────────────────────────────── */
QTableWidget {{
    background:{T['card']}; color:{T['text']}; border:none;
    gridline-color:{T['border']}; font-family:'Segoe UI'; font-size:13px;
}}
QTableWidget::item {{ padding:8px; border-bottom:1px solid {T['border']}; }}
QTableWidget::item:selected {{ background:{T['accent']}; color:#fff; }}
QHeaderView::section {{
    background:{T['sidebar']}; color:{T['sub']}; border:none;
    border-bottom:2px solid {T['border']};
    padding:10px; font-size:11px; font-weight:700; text-transform:uppercase;
    letter-spacing:0.5px; font-family:'Segoe UI';
}}

/* ── Scrollbars ───────────────────────────────────── */
QScrollBar:vertical {{ background:{T['bg']}; width:6px; border-radius:3px; }}
QScrollBar::handle:vertical {{ background:{T['border']}; border-radius:3px; min-height:30px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height:0; }}
QScrollBar:horizontal {{ background:{T['bg']}; height:6px; border-radius:3px; }}
QScrollBar::handle:horizontal {{ background:{T['border']}; border-radius:3px; }}

/* ── Misc ─────────────────────────────────────────── */
QFrame#divider {{ background:{T['border']}; max-height:1px; }}
QTabWidget::pane {{ border:none; background:{T['card']}; border-radius:10px; }}
QTabBar::tab {{
    background:{T['sidebar']}; color:{T['sub']}; border:none;
    padding:10px 20px; font-size:12px; font-weight:600; border-radius:8px 8px 0 0;
}}
QTabBar::tab:selected {{ background:{T['card']}; color:{T['text']}; }}
QTabBar::tab:hover {{ color:{T['text']}; }}

/* ── Message Boxes ────────────────────────────────── */
QMessageBox {{
    background:{T['card']}; color:{T['text']}; font-family:'Segoe UI';
}}
QMessageBox QLabel {{
    color:{T['text']}; font-size:13px; min-width:280px;
}}
QMessageBox QPushButton {{
    background:{T['accent']}; color:#fff; border:none; border-radius:7px;
    padding:8px 24px; font-size:12px; font-weight:600; min-width:80px;
}}
QMessageBox QPushButton:hover {{
    background:{T['accent2']};
}}

/* ── Toast Notification ───────────────────────────── */
QWidget#toast {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 {T['card']}, stop:1 {T['card2']});
    border-radius:12px; border:1px solid {T['border']};
}}
QLabel#toast_title {{ font-size:13px; font-weight:700; color:{T['text']}; }}
QLabel#toast_msg   {{ font-size:12px; color:{T['sub']}; }}
"""


APP_QSS = _build_qss(DARK)


def get_qss(theme='dark'):
    return _build_qss(DARK if theme == 'dark' else LIGHT)


def get_theme_colors(theme='dark'):
    return DARK if theme == 'dark' else LIGHT
