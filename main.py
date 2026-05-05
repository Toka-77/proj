"""
main.py — AIS Hub entry point with:
  • Toast notification system
  • Dark / Light theme toggle
  • AR / EN language toggle
  • Settings integration
"""
import sys, os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QStackedWidget, QGraphicsOpacityEffect
)
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont

from database import init_db
from styles import get_qss
from widgets import NavButton
from core import SettingsManager, NotificationManager

# Page imports — all in pages.py now
from pages import (
    DashboardPage, RoomsPage, InventoryPage, ExpensesPage, ReportsPage,
    SalesInvoicePage, PurchaseInvoicePage,
    AccountingPage, AccountStatementPage,
    LoyaltyPage, SettingsPage, BookingPage,
)


# ────────────────────────────────────────────────────────────────────────────
#  Toast Notification Widget
# ────────────────────────────────────────────────────────────────────────────
class Toast(QWidget):
    COLORS = {
        'success': ('#1a9e65', '🟢'),
        'warning': ('#e67e22', '🟡'),
        'danger':  ('#d63060', '🔴'),
        'info':    ('#2d7dd2', '🔵'),
    }

    def __init__(self, level, title, message, parent=None):
        super().__init__(parent)
        self.setObjectName("toast")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedWidth(320)

        color, icon = self.COLORS.get(level, ('#2d7dd2', 'ℹ️'))

        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(4)

        # Accent line
        bar = QWidget(); bar.setFixedHeight(3)
        bar.setStyleSheet(f"background:{color}; border-radius:2px;")
        lay.addWidget(bar)

        h = QHBoxLayout(); h.setSpacing(8)
        ic = QLabel(icon); ic.setStyleSheet("font-size:16px;")
        h.addWidget(ic)
        ttl = QLabel(title); ttl.setObjectName("toast_title")
        ttl.setStyleSheet(f"font-weight:700; font-size:13px; color:{color};")
        h.addWidget(ttl); h.addStretch()
        lay.addLayout(h)

        msg_lbl = QLabel(message)
        msg_lbl.setObjectName("toast_msg")
        msg_lbl.setWordWrap(True)
        msg_lbl.setStyleSheet("font-size:11px; color:#9aa0b8;")
        lay.addWidget(msg_lbl)

        self.adjustSize()

        # Opacity animation
        self._effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._effect)
        self._anim = QPropertyAnimation(self._effect, b"opacity")
        self._anim.setDuration(400)
        self._anim.setEasingCurve(QEasingCurve.InOutQuad)

        # Auto-close after 4.5s
        QTimer.singleShot(4500, self._fade_out)

    def show_at(self, x, y):
        self.move(x, y)
        self.show()
        self._effect.setOpacity(0)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.start()

    def _fade_out(self):
        self._anim.setStartValue(1.0)
        self._anim.setEndValue(0.0)
        self._anim.start()
        self._anim.finished.connect(self.close)


# ────────────────────────────────────────────────────────────────────────────
#  Main Application Window
# ────────────────────────────────────────────────────────────────────────────
class AISApp(QMainWindow):

    NAV_KEYS = [
        ("📊", "Dashboard"),
        ("🏠", "Rooms & Sessions"),
        ("📅", "Reservations"),
        ("🧃", "Inventory"),
        ("💸", "Expenses"),
        ("📈", "Reports"),
        ("🧾", "Sales"),
        ("📦", "Purchase"),
        ("📒", "Accounting"),
        ("📄", "Statements"),
        ("🎯", "Loyalty"),
        ("⚙️", "Settings"),
    ]

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Co-Working Space AIS — Accounting Information System")
        self.resize(1300, 800)
        self.setMinimumSize(950, 650)

        init_db()

        # Load saved theme
        self._theme = SettingsManager.get('theme', 'dark') or 'dark'

        self._toast_y_offset = 0  # stack toasts

        self._build_ui()
        self._apply_theme()

    # ── UI construction ────────────────────────────────────────────────────
    def _build_ui(self):
        root = QWidget(); root.setObjectName("root")
        self.setCentralWidget(root)
        main_h = QHBoxLayout(root)
        main_h.setContentsMargins(0, 0, 0, 0)
        main_h.setSpacing(0)

        # ── Sidebar ──────────────────────────────────────────────────────
        self.sidebar = QWidget(); self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(230)
        sb = QVBoxLayout(self.sidebar)
        sb.setContentsMargins(14, 22, 14, 14); sb.setSpacing(4)

        self.logo_lbl = QLabel("AIS Hub")
        self.logo_lbl.setStyleSheet(
            "font-size:20px; font-weight:800; padding:8px 6px 18px 6px; letter-spacing:1px;"
        )
        sb.addWidget(self.logo_lbl)

        self.nav_btns = []
        for icon, label in self.NAV_KEYS:
            btn = NavButton(icon, label)
            btn.clicked.connect(lambda _, n=len(self.nav_btns): self.switch_page(n))
            self.nav_btns.append(btn)
            sb.addWidget(btn)

        sb.addStretch()

        # Theme toggle only
        self.theme_btn = QPushButton("🌙" if self._theme == 'dark' else "☀️")
        self.theme_btn.setObjectName("icon_btn")
        self.theme_btn.setFixedSize(44, 34)
        self.theme_btn.setCursor(Qt.PointingHandCursor)
        self.theme_btn.clicked.connect(self.toggle_theme)
        self.theme_btn.setToolTip("Toggle Dark / Light mode")
        sb.addWidget(self.theme_btn)

        info = QLabel("Multi-Activity Hub\nAIS v3.0")
        info.setObjectName("subtitle")
        info.setAlignment(Qt.AlignCenter)
        info.setStyleSheet("font-size:10px; color:#4a5068; padding:8px;")
        sb.addWidget(info)

        main_h.addWidget(self.sidebar)

        # ── Content Stack ─────────────────────────────────────────────────
        self.stack = QStackedWidget()
        main_h.addWidget(self.stack)

        # Build pages
        self.pg_dash     = DashboardPage()
        self.pg_rooms    = RoomsPage()
        self.pg_booking  = BookingPage()
        self.pg_inv      = InventoryPage()
        self.pg_exp      = ExpensesPage()
        self.pg_rep      = ReportsPage()
        self.pg_sales    = SalesInvoicePage()
        self.pg_purchase = PurchaseInvoicePage()
        self.pg_acct     = AccountingPage()
        self.pg_stmt     = AccountStatementPage()
        self.pg_loyalty  = LoyaltyPage()
        self.pg_settings = SettingsPage()

        # Wire callbacks
        for pg in [self.pg_rooms, self.pg_inv, self.pg_exp,
                   self.pg_sales, self.pg_purchase, self.pg_booking]:
            pg._refresh_cb = self.refresh_all

        self._all_pages = [
            self.pg_dash, self.pg_rooms, self.pg_booking, self.pg_inv,
            self.pg_exp, self.pg_rep, self.pg_sales, self.pg_purchase,
            self.pg_acct, self.pg_stmt, self.pg_loyalty, self.pg_settings,
        ]
        for pg in self._all_pages:
            self.stack.addWidget(pg.page)

        self.switch_page(0)

        # Auto-refresh timer (every 5s — rooms, dashboard)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.auto_refresh)
        self.timer.start(5000)

        # Notification timer (every 60s)
        self.notif_timer = QTimer(self)
        self.notif_timer.timeout.connect(self.check_notifications)
        self.notif_timer.start(60000)
        # Run once after 3s on startup
        QTimer.singleShot(3000, self.check_notifications)

    # ── Navigation ─────────────────────────────────────────────────────────
    def switch_page(self, idx):
        for i, b in enumerate(self.nav_btns):
            b.setChecked(i == idx)
        self.stack.setCurrentIndex(idx)
        self.refresh_current(idx)

    def refresh_current(self, idx=None):
        if idx is None:
            idx = self.stack.currentIndex()
        if 0 <= idx < len(self._all_pages):
            try:
                self._all_pages[idx].refresh()
            except Exception:
                pass

    def refresh_all(self):
        self.pg_dash.refresh()
        self.refresh_current()

    def auto_refresh(self):
        self.pg_dash.refresh()
        idx = self.stack.currentIndex()
        if idx == 1:
            self.pg_rooms.refresh()
        elif idx == 3:
            self.pg_inv.refresh()

    # ── Theme ──────────────────────────────────────────────────────────────
    def toggle_theme(self):
        self._theme = 'light' if self._theme == 'dark' else 'dark'
        SettingsManager.set('theme', self._theme)
        self._apply_theme()
        self.theme_btn.setText("☀️" if self._theme == 'dark' else "🌙")

    def _apply_theme(self):
        QApplication.instance().setStyleSheet(get_qss(self._theme))

    # ── Notifications ──────────────────────────────────────────────────────
    def check_notifications(self):
        try:
            alerts = NotificationManager.check_alerts()
            for level, title, message in alerts:
                self._show_toast(level, title, message)
        except Exception:
            pass

    def _show_toast(self, level, title, message):
        toast = Toast(level, title, message, parent=None)
        # Position: bottom-right of window
        geo = self.geometry()
        x = geo.right() - toast.width() - 20
        y = geo.bottom() - 80 - self._toast_y_offset
        toast.show_at(x, y)
        self._toast_y_offset = (self._toast_y_offset + toast.height() + 10) % 300
        # Reset offset after toast closes
        QTimer.singleShot(5200, lambda: self._reset_toast_offset())

    def _reset_toast_offset(self):
        self._toast_y_offset = max(0, self._toast_y_offset - 100)

    def show_notification(self, level, title, message):
        """Public API — pages can call this to show a toast."""
        self._show_toast(level, title, message)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI", 10))
    window = AISApp()
    window.show()
    sys.exit(app.exec_())
