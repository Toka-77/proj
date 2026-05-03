"""
main.py — Entry point for Multi-Activity Entertainment & Study Hub AIS.
"""
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QStackedWidget
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont

from database import init_db
from styles import APP_QSS
from widgets import NavButton
from pages import DashboardPage, RoomsPage, InventoryPage, ExpensesPage, ReportsPage


class AISApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Co-Working Space AIS  —  Accounting Information System")
        self.resize(1200, 750)
        self.setMinimumSize(950, 650)
        init_db()

        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)
        main_h = QHBoxLayout(root)
        main_h.setContentsMargins(0, 0, 0, 0)
        main_h.setSpacing(0)

        # ── Sidebar ───────────────────────────────────────────────
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(230)
        sb = QVBoxLayout(sidebar)
        sb.setContentsMargins(14, 22, 14, 22)
        sb.setSpacing(6)

        logo = QLabel("🏢  AIS Hub")
        logo.setStyleSheet("font-size:20px; font-weight:800; padding:8px 6px 22px 6px; letter-spacing:1px;")
        sb.addWidget(logo)

        self.nav_btns = []
        nav_items = [
            ("📊", "Dashboard"),
            ("🏠", "Rooms & Sessions"),
            ("🧃", "Snacks & Inventory"),
            ("💸", "Expenses"),
            ("📈", "Financial Reports"),
        ]
        for icon, name in nav_items:
            btn = NavButton(icon, name)
            btn.clicked.connect(lambda checked, n=len(self.nav_btns): self.switch_page(n))
            self.nav_btns.append(btn)
            sb.addWidget(btn)

        sb.addStretch()

        info = QLabel("Multi-Activity Hub\nAccounting System v1.0")
        info.setObjectName("subtitle")
        info.setAlignment(Qt.AlignCenter)
        info.setStyleSheet("font-size:10px; color:#4a5068; padding:8px;")
        sb.addWidget(info)

        main_h.addWidget(sidebar)

        # ── Content Stack ─────────────────────────────────────────
        self.stack = QStackedWidget()
        main_h.addWidget(self.stack)

        # Build pages
        self.pg_dash = DashboardPage()
        self.pg_rooms = RoomsPage()
        self.pg_inv = InventoryPage()
        self.pg_exp = ExpensesPage()
        self.pg_rep = ReportsPage()

        # Wire refresh callbacks
        self.pg_rooms._refresh_cb = self.refresh_all
        self.pg_inv._refresh_cb = self.refresh_all
        self.pg_exp._refresh_cb = self.refresh_all

        for pg in [self.pg_dash, self.pg_rooms, self.pg_inv, self.pg_exp, self.pg_rep]:
            self.stack.addWidget(pg.page)

        self.switch_page(0)

        # Auto-refresh timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.auto_refresh)
        self.timer.start(5000)

    def switch_page(self, idx):
        for i, b in enumerate(self.nav_btns):
            b.setChecked(i == idx)
        self.stack.setCurrentIndex(idx)
        self.refresh_current(idx)

    def refresh_current(self, idx=None):
        if idx is None:
            idx = self.stack.currentIndex()
        if idx == 0:
            self.pg_dash.refresh()
        elif idx == 1:
            self.pg_rooms.refresh()
        elif idx == 2:
            self.pg_inv.refresh()
        elif idx == 3:
            self.pg_exp.refresh()
        elif idx == 4:
            self.pg_rep.refresh()

    def refresh_all(self):
        self.pg_dash.refresh()
        self.refresh_current()

    def auto_refresh(self):
        self.pg_dash.refresh()
        idx = self.stack.currentIndex()
        if idx == 1:
            self.pg_rooms.refresh()
        elif idx == 2:
            self.pg_inv.refresh()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI", 10))
    app.setStyleSheet(APP_QSS)
    window = AISApp()
    window.show()
    sys.exit(app.exec_())
