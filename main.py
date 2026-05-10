"""
main.py — AIS Hub entry point with:
  • Login System (Admin / Employee roles)
  • Role-Based Access Control (RBAC)
  • Toast notification system
  • Dark / Light theme toggle
  • Settings integration
"""
import sys, os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QStackedWidget, QGraphicsOpacityEffect,
    QDialog, QFormLayout, QLineEdit, QSpinBox, QDoubleSpinBox
)
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont

from database import init_db
from styles import get_qss
from widgets import NavButton
from core import SettingsManager, NotificationManager, UserManager
from translations import tr, set_lang, current_lang, is_arabic

from pages import (
    DashboardPage, RoomsPage, InventoryPage, ExpensesPage, ReportsPage,
    SalesInvoicePage, PurchaseInvoicePage,
    AccountingPage, AccountStatementPage,
    LoyaltyPage, SettingsPage, BookingPage,
)


# ────────────────────────────────────────────────────────────────────────────
#  Login Dialog
# ────────────────────────────────────────────────────────────────────────────
class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(tr("AIS Hub — Login"))
        self.setFixedSize(480, 420)
        self.current_user = None
        self._build()

    def _build(self):
        # ── Outer background ──────────────────────────────────────────────
        self.setStyleSheet("""
            QDialog { background-color: #0f1628; }

            QLabel#lbl_title {
                font-size: 28px; font-weight: 800;
                color: #a78bfa; letter-spacing: 1px;
            }
            QLabel#lbl_sub {
                font-size: 11px; color: #6a7a9a;
            }
            QLabel#lbl_field {
                font-size: 12px; font-weight: 600; color: #c0cae0;
            }
            QLabel#lbl_error {
                font-size: 11px; color: #f06292; font-weight: 600;
            }
            QLabel#lbl_hint {
                font-size: 10px; color: #2e3a55;
            }
            QLineEdit {
                background-color: #1a2340;
                border: 1px solid #2e3f6a;
                border-radius: 8px;
                color: #e0e8ff;
                font-size: 13px;
                padding: 6px 12px;
            }
            QLineEdit:focus {
                border: 1px solid #7c5cbf;
                background-color: #1e2a4a;
            }
            QPushButton#btn_login {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #7c5cbf, stop:1 #5c9cf5);
                color: white;
                font-size: 14px; font-weight: 700;
                border-radius: 10px;
                border: none;
                padding: 10px;
            }
            QPushButton#btn_login:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #9b7fd4, stop:1 #78b0ff);
            }
            QPushButton#btn_login:pressed { opacity: 0.85; }
        """)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(50, 40, 50, 36)
        lay.setSpacing(0)

        # ── Logo / Title ──────────────────────────────────────────────────
        title = QLabel("🏢  AIS Hub")
        title.setObjectName("lbl_title")
        title.setAlignment(Qt.AlignCenter)
        lay.addWidget(title)

        lay.addSpacing(6)

        sub = QLabel("Co-Working Space — Accounting Information System")
        sub.setObjectName("lbl_sub")
        sub.setAlignment(Qt.AlignCenter)
        lay.addWidget(sub)

        lay.addSpacing(28)

        # ── Username ──────────────────────────────────────────────────────
        u_lbl = QLabel("Username")
        u_lbl.setObjectName("lbl_field")
        lay.addWidget(u_lbl)
        lay.addSpacing(6)
        self.user_edit = QLineEdit()
        self.user_edit.setPlaceholderText("Enter your username…")
        self.user_edit.setFixedHeight(40)
        lay.addWidget(self.user_edit)

        lay.addSpacing(16)

        # ── Password ──────────────────────────────────────────────────────
        p_lbl = QLabel("Password")
        p_lbl.setObjectName("lbl_field")
        lay.addWidget(p_lbl)
        lay.addSpacing(6)
        self.pass_edit = QLineEdit()
        self.pass_edit.setPlaceholderText("Enter your password…")
        self.pass_edit.setEchoMode(QLineEdit.Password)
        self.pass_edit.setFixedHeight(40)
        lay.addWidget(self.pass_edit)

        lay.addSpacing(12)

        # ── Error label ───────────────────────────────────────────────────
        self.error_lbl = QLabel("")
        self.error_lbl.setObjectName("lbl_error")
        self.error_lbl.setAlignment(Qt.AlignCenter)
        self.error_lbl.setFixedHeight(18)
        lay.addWidget(self.error_lbl)

        lay.addSpacing(16)

        # ── Login button ──────────────────────────────────────────────────
        btn = QPushButton("  🔓   Login")
        btn.setObjectName("btn_login")
        btn.setFixedHeight(44)
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(self._do_login)
        lay.addWidget(btn)

        lay.addSpacing(14)

        # ── Hint ──────────────────────────────────────────────────────────
        hint = QLabel("admin / admin123     •     employee / emp123")
        hint.setObjectName("lbl_hint")
        hint.setAlignment(Qt.AlignCenter)
        lay.addWidget(hint)

        lay.addStretch()

        self.user_edit.returnPressed.connect(lambda: self.pass_edit.setFocus())
        self.pass_edit.returnPressed.connect(self._do_login)

    def _do_login(self):
        username = self.user_edit.text().strip()
        password = self.pass_edit.text()
        if not username or not password:
            self.error_lbl.setText("⚠  Please enter both username and password.")
            return
        user = UserManager.login(username, password)
        if user:
            self.current_user = user
            self.accept()
        else:
            self.error_lbl.setText("❌  Invalid username or password.")
            self.pass_edit.clear()
            self.pass_edit.setFocus()


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

        self._effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._effect)
        self._anim = QPropertyAnimation(self._effect, b"opacity")
        self._anim.setDuration(400)
        self._anim.setEasingCurve(QEasingCurve.InOutQuad)
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
        ("📊", "Dashboard"),        # 0
        ("🏠", "Rooms & Sessions"), # 1
        ("📅", "Reservations"),     # 2
        ("🧃", "Inventory"),        # 3
        ("💸", "Expenses"),         # 4  ← Admin only
        ("📈", "Reports"),          # 5  ← Admin only
        ("🧾", "Sales"),            # 6
        ("📦", "Purchase"),         # 7  ← Admin only
        ("📒", "Accounting"),       # 8  ← Admin only
        ("📄", "Statements"),       # 9  ← Admin only
        ("🎯", "Loyalty"),          # 10
        ("⚙️", "Settings"),        # 11 ← Admin only
    ]

    # Pages hidden from Employee role
    EMPLOYEE_HIDDEN = {4, 5, 7, 8, 9, 11}

    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self._logout_requested = False

        self.setWindowTitle(tr("Co-Working Space AIS — Accounting Information System"))
        self.resize(1300, 800)
        self.setMinimumSize(950, 650)

        init_db()

        self._theme = SettingsManager.get('theme', 'dark') or 'dark'
        self._toast_y_offset = 0

        saved_lang = SettingsManager.get('language', 'ar') or 'ar'
        set_lang(saved_lang)

        self._build_ui()
        self._apply_theme()
        self._apply_lang_direction()
        self._apply_role_restrictions()

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
            btn = NavButton(icon, tr(label))
            btn.clicked.connect(lambda _, n=len(self.nav_btns): self.switch_page(n))
            self.nav_btns.append(btn)
            sb.addWidget(btn)

        sb.addStretch()

        # Theme toggle
        self.theme_btn = QPushButton("🌙" if self._theme == 'dark' else "☀️")
        self.theme_btn.setObjectName("icon_btn")
        self.theme_btn.setFixedSize(44, 34)
        self.theme_btn.setCursor(Qt.PointingHandCursor)
        self.theme_btn.clicked.connect(self.toggle_theme)
        self.theme_btn.setToolTip(tr("Toggle Dark / Light mode"))
        
        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)
        btn_row.addWidget(self.theme_btn)
        
        self.lang_btn = QPushButton("🌐 EN" if is_arabic() else "🌐 AR")
        self.lang_btn.setObjectName("icon_btn")
        self.lang_btn.setFixedHeight(34)
        self.lang_btn.setCursor(Qt.PointingHandCursor)
        self.lang_btn.clicked.connect(self.toggle_lang)
        self.lang_btn.setToolTip(tr("Switch language / تغيير اللغة"))
        btn_row.addWidget(self.lang_btn)
        
        sb.addLayout(btn_row)

        # ── User info + Logout ────────────────────────────────────────────
        role = self.current_user['role']
        role_icon = "🔴 Admin" if role == 'admin' else "🎫 Employee"

        user_lbl = QLabel(f"👤 {self.current_user['full_name']}")
        user_lbl.setStyleSheet("font-size:11px; font-weight:700; color:#9aa0b8; padding-top:8px;")
        user_lbl.setAlignment(Qt.AlignCenter)
        sb.addWidget(user_lbl)

        role_lbl = QLabel(role_icon)
        role_lbl.setStyleSheet("font-size:10px; color:#5a6a8a;")
        role_lbl.setAlignment(Qt.AlignCenter)
        sb.addWidget(role_lbl)

        logout_btn = QPushButton(tr("🚪 Logout"))
        logout_btn.setObjectName("danger")
        logout_btn.setFixedHeight(30)
        logout_btn.setCursor(Qt.PointingHandCursor)
        logout_btn.clicked.connect(self.logout)
        sb.addWidget(logout_btn)

        info = QLabel("Multi-Activity Hub\nAIS v3.0")
        info.setObjectName("subtitle")
        info.setAlignment(Qt.AlignCenter)
        info.setStyleSheet("font-size:10px; color:#4a5068; padding:4px;")
        sb.addWidget(info)

        main_h.addWidget(self.sidebar)

        # ── Content Stack ─────────────────────────────────────────────────
        self.stack = QStackedWidget()
        main_h.addWidget(self.stack)

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

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.auto_refresh)
        self.timer.start(5000)

        self.notif_timer = QTimer(self)
        self.notif_timer.timeout.connect(self.check_notifications)
        self.notif_timer.start(60000)
        QTimer.singleShot(3000, self.check_notifications)

    # ── Role Restrictions ──────────────────────────────────────────────────
    def _apply_role_restrictions(self):
        """Hide nav buttons and disable actions for 'employee' role."""
        if self.current_user['role'] == 'admin':
            return  # Full access

        # Hide restricted nav buttons
        for idx in self.EMPLOYEE_HIDDEN:
            self.nav_btns[idx].hide()

        # Inventory: view only — no price edit or delete
        self.pg_inv.set_readonly(True)

        # Sales: price cannot be edited by employees
        self.pg_sales.set_readonly(True)

        # If somehow on a hidden page, go to dashboard
        if self.stack.currentIndex() in self.EMPLOYEE_HIDDEN:
            self.switch_page(0)

    # ── Navigation ─────────────────────────────────────────────────────────
    def switch_page(self, idx):
        # Block employee from accessing restricted pages
        if self.current_user['role'] == 'employee' and idx in self.EMPLOYEE_HIDDEN:
            return
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

    def toggle_lang(self):
        new_lang = 'ar' if current_lang() == 'en' else 'en'
        set_lang(new_lang)
        SettingsManager.set('language', new_lang)
        self.lang_btn.setText("🌐 EN" if new_lang == 'ar' else "🌐 AR")
        
        for i, (icon, label) in enumerate(self.NAV_KEYS):
            self.nav_btns[i].setText(f"{icon}  {tr(label)}")
            
        self._apply_lang_direction()
        self.refresh_all()

    def _apply_lang_direction(self):
        app = QApplication.instance()
        if is_arabic():
            app.setLayoutDirection(Qt.RightToLeft)
            app.setFont(QFont("Arial", 10))
        else:
            app.setLayoutDirection(Qt.LeftToRight)
            app.setFont(QFont("Segoe UI", 10))

    # ── Logout ─────────────────────────────────────────────────────────────
    def logout(self):
        self._logout_requested = True
        self.close()

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
        geo = self.geometry()
        x = geo.right() - toast.width() - 20
        y = geo.bottom() - 80 - self._toast_y_offset
        toast.show_at(x, y)
        self._toast_y_offset = (self._toast_y_offset + toast.height() + 10) % 300
        QTimer.singleShot(5200, lambda: self._reset_toast_offset())

    def _reset_toast_offset(self):
        self._toast_y_offset = max(0, self._toast_y_offset - 100)

    def show_notification(self, level, title, message):
        """Public API — pages can call this to show a toast."""
        self._show_toast(level, title, message)

def _auto_select_focus(self, event):
    type(self).__bases__[0].focusInEvent(self, event)
    QTimer.singleShot(0, self.selectAll)

QSpinBox.focusInEvent = _auto_select_focus
QDoubleSpinBox.focusInEvent = _auto_select_focus


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI", 10))

    # Apply theme before showing login
    app.setStyleSheet(get_qss('dark'))
    
    # Initialize DB tables
    init_db()

    while True:
        login = LoginDialog()
        if login.exec_() != QDialog.Accepted:
            break

        window = AISApp(login.current_user)
        window.show()
        app.exec_()

        # If user clicked Logout → loop back to login
        # If user closed the window normally → exit
        if not window._logout_requested:
            break

    sys.exit(0)
