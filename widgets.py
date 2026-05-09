"""
widgets.py — Reusable custom widgets for the AIS Hub UI.
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt5.QtGui import QColor, QFont


class StatCard(QWidget):
    """Gradient stat card with glow effect."""

    def __init__(self, icon, label, value="0", color="#7c5cbf", parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setMinimumHeight(110)
        self.setMinimumWidth(160)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(6)

        top = QHBoxLayout()
        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet(f"font-size:22px; background:transparent;")
        top.addWidget(icon_lbl)
        top.addStretch()
        layout.addLayout(top)

        self.val_lbl = QLabel(str(value))
        self.val_lbl.setObjectName("stat_val")
        self.val_lbl.setStyleSheet(f"color:{color}; font-size:28px; font-weight:800; background:transparent;")
        layout.addWidget(self.val_lbl)

        self.title_lbl = QLabel(label)
        self.title_lbl.setObjectName("stat_lbl")
        self.title_lbl.setStyleSheet("background:transparent;")
        layout.addWidget(self.title_lbl)

        # Subtle glow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(color))
        shadow.setOffset(0, 0)
        self.setGraphicsEffect(shadow)

    def update_value(self, v, color=None):
        self.val_lbl.setText(str(v))
        if color:
            self.val_lbl.setStyleSheet(f"color:{color}; font-size:28px; font-weight:800; background:transparent;")

    def update_title(self, title):
        self.title_lbl.setText(title)


class NavButton(QPushButton):
    """Sidebar navigation button."""

    def __init__(self, icon_text, text, parent=None):
        super().__init__(f"  {icon_text}  {text}", parent)
        self.setObjectName("nav_btn")
        self.setCheckable(True)
        self.setFixedHeight(46)
        self.setCursor(Qt.PointingHandCursor)


class RoomStatusCard(QWidget):
    """Visual room card showing live status."""

    def __init__(self, name, room_type, status, price, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setFixedHeight(90)
        self.setMinimumWidth(200)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)

        top = QHBoxLayout()
        name_lbl = QLabel(name)
        name_lbl.setStyleSheet("font-size:14px; font-weight:700; background:transparent;")
        top.addWidget(name_lbl)
        top.addStretch()

        type_icons = {"Study": "📚", "Gaming": "🎮", "Cinema": "🎬"}
        t_icon = QLabel(type_icons.get(room_type, "🏠"))
        t_icon.setStyleSheet("font-size:18px; background:transparent;")
        top.addWidget(t_icon)
        layout.addLayout(top)

        bot = QHBoxLayout()
        price_lbl = QLabel(f"{price:.0f} EGP/hr")
        price_lbl.setStyleSheet("font-size:11px; color:#6b7a99; background:transparent;")
        bot.addWidget(price_lbl)
        bot.addStretch()

        dot = "🟢" if status == "Available" else "🔴"
        s_color = "#3ecf8e" if status == "Available" else "#f06292"
        status_lbl = QLabel(f"{dot} {status}")
        status_lbl.setStyleSheet(f"font-size:11px; color:{s_color}; font-weight:600; background:transparent;")
        bot.addWidget(status_lbl)
        layout.addLayout(bot)


def make_table(headers):
    """Create a styled table widget."""
    t = QTableWidget()
    t.setColumnCount(len(headers))
    t.setHorizontalHeaderLabels(headers)
    t.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    t.verticalHeader().setVisible(False)
    t.setEditTriggers(QTableWidget.NoEditTriggers)
    t.setSelectionBehavior(QTableWidget.SelectRows)
    t.setAlternatingRowColors(False)
    t.setShowGrid(False)
    return t


def set_row(table, row, values):
    """Populate a table row."""
    for col, val in enumerate(values):
        item = QTableWidgetItem(str(val))
        item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        table.setItem(row, col, item)


def make_divider():
    div = QFrame()
    div.setObjectName("divider")
    return div
