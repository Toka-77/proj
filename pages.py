"""pages.py — All page builders for AIS Hub."""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QDoubleSpinBox, QSpinBox, QFormLayout,
    QFrame, QMessageBox, QGridLayout, QScrollArea, QTabWidget
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from widgets import StatCard, RoomStatusCard, make_table, set_row, make_divider
from core import (RoomManager, SessionManager, InventoryManager,
                  ExpenseManager, ReportManager)


def page_container(title, subtitle=""):
    page = QWidget(); page.setObjectName("root")
    layout = QVBoxLayout(page)
    layout.setContentsMargins(30, 24, 30, 24); layout.setSpacing(16)
    header = QHBoxLayout()
    t = QLabel(title); t.setObjectName("title"); header.addWidget(t)
    header.addStretch()
    if subtitle:
        s = QLabel(subtitle); s.setObjectName("subtitle"); header.addWidget(s)
    layout.addLayout(header)
    layout.addWidget(make_divider())
    return page, layout


# ═══════════════════════════════════════════════════════════════
#  DASHBOARD
# ═══════════════════════════════════════════════════════════════
class DashboardPage:
    def __init__(self):
        self.page, lay = page_container("Dashboard", "Real-time Overview")
        row = QHBoxLayout(); row.setSpacing(14)
        self.s_rooms = StatCard("🏠", "Total Rooms", "0", "#7c5cbf")
        self.s_occ   = StatCard("🔴", "Occupied",    "0", "#f06292")
        self.s_rev   = StatCard("💰", "Revenue",  "0 EGP", "#3ecf8e")
        self.s_prof  = StatCard("📈", "Net Profit","0 EGP", "#5c9cf5")
        for c in [self.s_rooms, self.s_occ, self.s_rev, self.s_prof]:
            row.addWidget(c)
        lay.addLayout(row)

        # Live room status
        lbl = QLabel("🏠  Live Room Status"); lbl.setObjectName("sec_title")
        lay.addWidget(lbl)
        self.room_grid = QGridLayout(); self.room_grid.setSpacing(12)
        lay.addLayout(self.room_grid)

        lbl2 = QLabel("⏱  Active Sessions"); lbl2.setObjectName("sec_title")
        lay.addWidget(lbl2)
        self.table = make_table(["#", "Room", "Type", "Customer", "People", "Started", "Elapsed"])
        lay.addWidget(self.table)

    def refresh(self):
        rooms = RoomManager.get_all_rooms()
        occ = sum(1 for r in rooms if r[3] == 'Occupied')
        rep = ReportManager.generate_report()
        self.s_rooms.update_value(len(rooms))
        self.s_occ.update_value(occ)
        self.s_rev.update_value(f"{rep['total_revenue']:.0f} EGP")
        p = rep['profit']
        self.s_prof.update_value(f"{p:.0f} EGP", "#3ecf8e" if p >= 0 else "#f06292")

        # Clear old room cards
        while self.room_grid.count():
            w = self.room_grid.takeAt(0).widget()
            if w: w.deleteLater()
        for i, r in enumerate(rooms):
            card = RoomStatusCard(r[1], r[2], r[3], r[4])
            self.room_grid.addWidget(card, i // 4, i % 4)

        sessions = SessionManager.get_active_sessions()
        self.table.setRowCount(len(sessions))
        for i, s in enumerate(sessions):
            elapsed = SessionManager.get_session_elapsed(s[0])
            h, m = int(elapsed), int((elapsed % 1) * 60)
            set_row(self.table, i, [s[0], s[1], s[6], s[2] or "—", s[4], s[3], f"{h}h {m}m"])


# ═══════════════════════════════════════════════════════════════
#  ROOMS & SESSIONS
# ═══════════════════════════════════════════════════════════════
class RoomsPage:
    def __init__(self):
        self.page, lay = page_container("Rooms & Sessions")
        grid = QHBoxLayout(); grid.setSpacing(20)

        # Left: rooms table
        left = QWidget(); left.setObjectName("card")
        ll = QVBoxLayout(left); ll.setContentsMargins(16,16,16,16)
        QLabel("All Rooms", objectName="sec_title", parent=left)
        ll.addWidget(QLabel("All Rooms", objectName="sec_title"))
        self.rooms_tbl = make_table(["ID","Name","Type","Status","Price/hr","Capacity"])
        ll.addWidget(self.rooms_tbl)
        grid.addWidget(left, 3)

        # Right: start/end
        right = QWidget(); right.setObjectName("card")
        rl = QVBoxLayout(right); rl.setContentsMargins(16,16,16,20); rl.setSpacing(14)

        rl.addWidget(QLabel("▶  Start Session", objectName="sec_title"))
        f1 = QFormLayout(); f1.setSpacing(10)
        self.start_room = QComboBox()
        self.start_cust = QLineEdit(); self.start_cust.setPlaceholderText("Customer name...")
        self.start_ppl = QSpinBox(); self.start_ppl.setMinimum(1); self.start_ppl.setMaximum(50)
        f1.addRow("Room:", self.start_room)
        f1.addRow("Customer:", self.start_cust)
        f1.addRow("People:", self.start_ppl)
        rl.addLayout(f1)
        b1 = QPushButton("▶  Start Session"); b1.setObjectName("primary")
        b1.setCursor(Qt.PointingHandCursor); b1.clicked.connect(self.handle_start)
        rl.addWidget(b1)

        rl.addWidget(make_divider())

        rl.addWidget(QLabel("⏹  End Session", objectName="sec_title"))
        f2 = QFormLayout(); f2.setSpacing(10)
        self.end_sess = QComboBox()
        self.end_disc = QDoubleSpinBox(); self.end_disc.setMaximum(99999)
        self.end_disc.setPrefix("EGP "); self.end_disc.setDecimals(2)
        f2.addRow("Session:", self.end_sess)
        f2.addRow("Discount:", self.end_disc)
        rl.addLayout(f2)
        b2 = QPushButton("⏹  End & Generate Bill"); b2.setObjectName("danger")
        b2.setCursor(Qt.PointingHandCursor); b2.clicked.connect(self.handle_end)
        rl.addWidget(b2)
        rl.addStretch()
        grid.addWidget(right, 2)
        lay.addLayout(grid)

        # Session history
        lay.addWidget(QLabel("📋  Session History", objectName="sec_title"))
        self.hist_tbl = make_table(["#","Room","Type","Customer","People","Start","End","Room $","Snacks","Disc","Total"])
        self.hist_tbl.setMaximumHeight(200)
        lay.addWidget(self.hist_tbl)

        self._refresh_cb = None  # set by main app

    def refresh(self):
        rooms = RoomManager.get_all_rooms()
        self.rooms_tbl.setRowCount(len(rooms))
        self.start_room.clear()
        for i, r in enumerate(rooms):
            set_row(self.rooms_tbl, i, [r[0], r[1], r[2], r[3], f"{r[4]:.0f}", r[5]])
            si = self.rooms_tbl.item(i, 3)
            if si:
                si.setForeground(QColor("#3ecf8e") if r[3]=="Available" else QColor("#f06292"))
            if r[3] == "Available":
                self.start_room.addItem(f"{r[1]}  ({r[2]})", r[0])

        sessions = SessionManager.get_active_sessions()
        self.end_sess.clear()
        for s in sessions:
            self.end_sess.addItem(f"#{s[0]}  {s[1]}  —  {s[2]}", s[0])

        hist = SessionManager.get_all_sessions(50)
        self.hist_tbl.setRowCount(len(hist))
        for i, h in enumerate(hist):
            set_row(self.hist_tbl, i, [h[0],h[1],h[2],h[3],h[4],h[5],h[6] or "Active",
                    f"{h[7]:.1f}",f"{h[8]:.1f}",f"{h[9]:.1f}",f"{h[10]:.1f}"])

    def handle_start(self):
        rid = self.start_room.currentData()
        if not rid:
            return QMessageBox.warning(self.page, "Error", "No available room.")
        cname = self.start_cust.text().strip()
        if not cname:
            return QMessageBox.warning(self.page, "Required", "Enter customer name.")
        sid, msg = SessionManager.start_session(rid, cname, self.start_ppl.value())
        if sid:
            QMessageBox.information(self.page, "✅ Started", msg)
            self.start_cust.clear(); self.start_ppl.setValue(1)
            if self._refresh_cb: self._refresh_cb()
        else:
            QMessageBox.warning(self.page, "Error", msg)

    def handle_end(self):
        sid = self.end_sess.currentData()
        if not sid:
            return QMessageBox.warning(self.page, "Error", "No active session.")
        ok, res = SessionManager.end_session(sid, self.end_disc.value())
        if ok:
            msg = (f"Session #{res['session_id']} Closed\n\n"
                   f"Duration:     {res['duration_hours']:.2f} hrs\n"
                   f"Room Charge:  {res['room_charge']:.2f} EGP\n"
                   f"Snacks:       {res['snacks_total']:.2f} EGP\n"
                   f"Discount:    -{res['discount']:.2f} EGP\n"
                   f"{'─'*30}\n"
                   f"TOTAL:        {res['total_bill']:.2f} EGP")
            QMessageBox.information(self.page, "💰 Final Bill", msg)
            self.end_disc.setValue(0)
            if self._refresh_cb: self._refresh_cb()
        else:
            QMessageBox.warning(self.page, "Error", res)


# ═══════════════════════════════════════════════════════════════
#  INVENTORY
# ═══════════════════════════════════════════════════════════════
class InventoryPage:
    def __init__(self):
        self.page, lay = page_container("Snacks & Inventory")
        grid = QHBoxLayout(); grid.setSpacing(20)

        # Left: products
        left = QWidget(); left.setObjectName("card")
        ll = QVBoxLayout(left); ll.setContentsMargins(16,16,16,16)
        ll.addWidget(QLabel("📦  Products", objectName="sec_title"))
        self.prod_tbl = make_table(["ID","Product","Category","Stock","Price","Cost"])
        ll.addWidget(self.prod_tbl)

        # Low stock alerts
        ll.addWidget(QLabel("⚠️  Low Stock Alerts", objectName="sec_title"))
        self.low_tbl = make_table(["ID","Product","Stock","Alert Level"])
        self.low_tbl.setMaximumHeight(120)
        ll.addWidget(self.low_tbl)
        grid.addWidget(left, 3)

        # Right: sell + restock + add
        right = QWidget(); right.setObjectName("card")
        rl = QVBoxLayout(right); rl.setContentsMargins(16,16,16,20); rl.setSpacing(12)

        # Sell
        rl.addWidget(QLabel("🧃  Sell Product", objectName="sec_title"))
        f = QFormLayout(); f.setSpacing(8)
        self.sell_prod = QComboBox()
        self.sell_qty = QSpinBox(); self.sell_qty.setMinimum(1); self.sell_qty.setMaximum(999)
        self.sell_sess = QComboBox()
        f.addRow("Product:", self.sell_prod)
        f.addRow("Qty:", self.sell_qty)
        f.addRow("Session:", self.sell_sess)
        rl.addLayout(f)
        b1 = QPushButton("💲  Sell"); b1.setObjectName("primary")
        b1.setCursor(Qt.PointingHandCursor); b1.clicked.connect(self.handle_sell)
        rl.addWidget(b1)
        rl.addWidget(make_divider())

        # Restock
        rl.addWidget(QLabel("📥  Restock", objectName="sec_title"))
        f2 = QFormLayout(); f2.setSpacing(8)
        self.restock_prod = QComboBox()
        self.restock_qty = QSpinBox(); self.restock_qty.setMinimum(1); self.restock_qty.setMaximum(9999)
        f2.addRow("Product:", self.restock_prod)
        f2.addRow("Qty:", self.restock_qty)
        rl.addLayout(f2)
        b2 = QPushButton("📥  Restock"); b2.setObjectName("secondary")
        b2.setCursor(Qt.PointingHandCursor); b2.clicked.connect(self.handle_restock)
        rl.addWidget(b2)
        rl.addWidget(make_divider())

        # Add product
        rl.addWidget(QLabel("➕  Add Product", objectName="sec_title"))
        f3 = QFormLayout(); f3.setSpacing(8)
        self.add_name = QLineEdit(); self.add_name.setPlaceholderText("Product name")
        self.add_cat = QComboBox(); self.add_cat.addItems(["Drinks","Snacks","Hot","Other"])
        self.add_qty = QSpinBox(); self.add_qty.setMaximum(9999)
        self.add_price = QDoubleSpinBox(); self.add_price.setMaximum(9999); self.add_price.setPrefix("EGP ")
        self.add_cost = QDoubleSpinBox(); self.add_cost.setMaximum(9999); self.add_cost.setPrefix("EGP ")
        f3.addRow("Name:", self.add_name)
        f3.addRow("Category:", self.add_cat)
        f3.addRow("Qty:", self.add_qty)
        f3.addRow("Price:", self.add_price)
        f3.addRow("Cost:", self.add_cost)
        rl.addLayout(f3)
        b3 = QPushButton("➕  Add Product"); b3.setObjectName("primary")
        b3.setCursor(Qt.PointingHandCursor); b3.clicked.connect(self.handle_add)
        rl.addWidget(b3)
        rl.addStretch()
        grid.addWidget(right, 2)
        lay.addLayout(grid)

        self._refresh_cb = None

    def refresh(self):
        prods = InventoryManager.get_all_products()
        self.prod_tbl.setRowCount(len(prods))
        self.sell_prod.clear(); self.restock_prod.clear()
        for i, p in enumerate(prods):
            set_row(self.prod_tbl, i, [p[0], p[1], p[2], p[3], f"{p[4]:.1f}", f"{p[5]:.1f}"])
            stock_item = self.prod_tbl.item(i, 3)
            if stock_item and p[3] <= p[6]:
                stock_item.setForeground(QColor("#f06292"))
            self.restock_prod.addItem(f"{p[1]}", p[0])
            if p[3] > 0:
                self.sell_prod.addItem(f"{p[1]} (stock:{p[3]})", p[0])

        sessions = SessionManager.get_active_sessions()
        self.sell_sess.clear()
        self.sell_sess.addItem("None (direct sale)", None)
        for s in sessions:
            self.sell_sess.addItem(f"#{s[0]} {s[1]}", s[0])

        low = InventoryManager.get_low_stock()
        self.low_tbl.setRowCount(len(low))
        for i, l in enumerate(low):
            set_row(self.low_tbl, i, [l[0], l[1], l[2], l[3]])

    def handle_sell(self):
        pid = self.sell_prod.currentData()
        if not pid: return QMessageBox.warning(self.page, "Error", "No product selected.")
        ok, msg = InventoryManager.sell_product(pid, self.sell_qty.value(), self.sell_sess.currentData())
        if ok:
            QMessageBox.information(self.page, "✅", msg); self.sell_qty.setValue(1)
            if self._refresh_cb: self._refresh_cb()
        else:
            QMessageBox.warning(self.page, "Error", msg)

    def handle_restock(self):
        pid = self.restock_prod.currentData()
        if not pid: return QMessageBox.warning(self.page, "Error", "No product selected.")
        ok, msg = InventoryManager.restock(pid, self.restock_qty.value())
        if ok:
            QMessageBox.information(self.page, "✅", msg); self.restock_qty.setValue(1)
            if self._refresh_cb: self._refresh_cb()
        else:
            QMessageBox.warning(self.page, "Error", msg)

    def handle_add(self):
        name = self.add_name.text().strip()
        if not name: return QMessageBox.warning(self.page, "Required", "Enter product name.")
        if self.add_price.value() <= 0: return QMessageBox.warning(self.page, "Required", "Enter price.")
        ok, msg = InventoryManager.add_product(
            name, self.add_cat.currentText(), self.add_qty.value(),
            self.add_price.value(), self.add_cost.value())
        if ok:
            QMessageBox.information(self.page, "✅", msg)
            self.add_name.clear(); self.add_qty.setValue(0)
            self.add_price.setValue(0); self.add_cost.setValue(0)
            if self._refresh_cb: self._refresh_cb()
        else:
            QMessageBox.warning(self.page, "Error", msg)


# ═══════════════════════════════════════════════════════════════
#  EXPENSES
# ═══════════════════════════════════════════════════════════════
class ExpensesPage:
    def __init__(self):
        self.page, lay = page_container("Expenses")
        grid = QHBoxLayout(); grid.setSpacing(20)

        # Left: expense history
        left = QWidget(); left.setObjectName("card")
        ll = QVBoxLayout(left); ll.setContentsMargins(16,16,16,16)
        ll.addWidget(QLabel("📋  Expense History", objectName="sec_title"))
        self.exp_tbl = make_table(["ID","Category","Amount","Date","Description"])
        ll.addWidget(self.exp_tbl)

        row = QHBoxLayout()
        self.total_lbl = QLabel("Total: 0 EGP")
        self.total_lbl.setStyleSheet("font-size:16px; font-weight:700; color:#f06292;")
        row.addWidget(self.total_lbl); row.addStretch()
        del_btn = QPushButton("🗑  Delete Selected"); del_btn.setObjectName("danger")
        del_btn.setCursor(Qt.PointingHandCursor); del_btn.clicked.connect(self.handle_delete)
        row.addWidget(del_btn)
        ll.addLayout(row)
        grid.addWidget(left, 3)

        # Right: add expense
        right = QWidget(); right.setObjectName("card")
        rl = QVBoxLayout(right); rl.setContentsMargins(16,16,16,20); rl.setSpacing(14)
        rl.addWidget(QLabel("➕  Add Expense", objectName="sec_title"))
        f = QFormLayout(); f.setSpacing(10)
        self.exp_cat = QComboBox()
        self.exp_cat.addItems(ExpenseManager.CATEGORIES)
        self.exp_amt = QDoubleSpinBox(); self.exp_amt.setMaximum(1000000)
        self.exp_amt.setPrefix("EGP "); self.exp_amt.setDecimals(2)
        self.exp_desc = QLineEdit(); self.exp_desc.setPlaceholderText("Description...")
        f.addRow("Category:", self.exp_cat)
        f.addRow("Amount:", self.exp_amt)
        f.addRow("Description:", self.exp_desc)
        rl.addLayout(f)
        btn = QPushButton("➕  Add Expense"); btn.setObjectName("primary")
        btn.setCursor(Qt.PointingHandCursor); btn.clicked.connect(self.handle_add)
        rl.addWidget(btn); rl.addStretch()
        grid.addWidget(right, 2)
        lay.addLayout(grid)

        self._refresh_cb = None

    def refresh(self):
        exps = ExpenseManager.get_all_expenses()
        self.exp_tbl.setRowCount(len(exps))
        for i, e in enumerate(exps):
            set_row(self.exp_tbl, i, [e[0], e[1], f"{e[2]:.2f}", e[3], e[4]])
        total = ExpenseManager.get_total_expenses()
        self.total_lbl.setText(f"Total: {total:,.2f} EGP")

    def handle_add(self):
        if self.exp_amt.value() <= 0:
            return QMessageBox.warning(self.page, "Error", "Enter a valid amount.")
        ok, msg = ExpenseManager.add_expense(
            self.exp_cat.currentText(), self.exp_amt.value(), self.exp_desc.text())
        if ok:
            QMessageBox.information(self.page, "✅", msg)
            self.exp_amt.setValue(0); self.exp_desc.clear(); self.refresh()
        else:
            QMessageBox.warning(self.page, "Error", msg)

    def handle_delete(self):
        row = self.exp_tbl.currentRow()
        if row < 0: return QMessageBox.warning(self.page, "Error", "Select an expense.")
        eid = int(self.exp_tbl.item(row, 0).text())
        reply = QMessageBox.question(self.page, "Confirm", f"Delete expense #{eid}?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            ExpenseManager.delete_expense(eid); self.refresh()


# ═══════════════════════════════════════════════════════════════
#  REPORTS
# ═══════════════════════════════════════════════════════════════
class ReportsPage:
    def __init__(self):
        self.page, lay = page_container("Financial Reports", "Segment Reporting & Analytics")

        row = QHBoxLayout(); row.setSpacing(14)
        self.r_rev  = StatCard("💰", "Total Revenue",  "—", "#3ecf8e")
        self.r_exp  = StatCard("💸", "Total Expenses", "—", "#f06292")
        self.r_prof = StatCard("📈", "Net Profit",     "—", "#5c9cf5")
        self.r_top  = StatCard("🏆", "Top Room",       "—", "#ffa726")
        for c in [self.r_rev, self.r_exp, self.r_prof, self.r_top]:
            row.addWidget(c)
        lay.addLayout(row)

        # Extra stats
        row2 = QHBoxLayout(); row2.setSpacing(14)
        self.r_sess   = StatCard("🎫", "Total Sessions",  "—", "#7c5cbf")
        self.r_active = StatCard("⏱", "Active Sessions",  "—", "#ffa726")
        self.r_inv    = StatCard("📦", "Inventory Value",  "—", "#5c9cf5")
        self.r_today  = StatCard("🧃", "Snacks Today",    "—", "#3ecf8e")
        for c in [self.r_sess, self.r_active, self.r_inv, self.r_today]:
            row2.addWidget(c)
        lay.addLayout(row2)

        # Revenue per room type
        lay.addWidget(QLabel("📊  Revenue per Room Type (Segment Reporting)", objectName="sec_title"))
        self.type_tbl = make_table(["Room Type","Revenue (EGP)","% of Total"])
        self.type_tbl.setMaximumHeight(150)
        lay.addWidget(self.type_tbl)

        # Revenue per room
        lay.addWidget(QLabel("🏠  Revenue per Room", objectName="sec_title"))
        self.room_tbl = make_table(["Room","Revenue (EGP)"])
        self.room_tbl.setMaximumHeight(200)
        lay.addWidget(self.room_tbl)

        btn = QPushButton("🔄  Refresh Report"); btn.setObjectName("primary")
        btn.setCursor(Qt.PointingHandCursor); btn.clicked.connect(self.refresh)
        lay.addWidget(btn)

    def refresh(self):
        rep = ReportManager.generate_report()
        self.r_rev.update_value(f"{rep['total_revenue']:,.2f} EGP")
        self.r_exp.update_value(f"{rep['total_expenses']:,.2f} EGP")
        p = rep['profit']
        self.r_prof.update_value(f"{p:,.2f} EGP", "#3ecf8e" if p >= 0 else "#f06292")
        self.r_top.update_value(f"{rep['most_used_room']} ({rep['most_used_count']})")
        self.r_sess.update_value(rep['total_sessions'])
        self.r_active.update_value(rep['active_sessions'])
        self.r_inv.update_value(f"{rep['inventory_value']:,.0f} EGP")
        self.r_today.update_value(f"{rep['snacks_today']:,.0f} EGP")

        # Revenue per type
        rev_type = rep['revenue_per_type']
        total_r = max(sum(rev_type.values()), 1)
        types = ['Study', 'Gaming', 'Cinema']
        self.type_tbl.setRowCount(len(types))
        for i, t in enumerate(types):
            amt = rev_type.get(t, 0)
            pct = (amt / total_r) * 100
            set_row(self.type_tbl, i, [f"{'📚' if t=='Study' else '🎮' if t=='Gaming' else '🎬'}  {t}",
                                        f"{amt:,.2f}", f"{pct:.1f}%"])

        # Revenue per room
        rev_room = rep['revenue_per_room']
        self.room_tbl.setRowCount(len(rev_room))
        for i, (rn, amt) in enumerate(rev_room.items()):
            set_row(self.room_tbl, i, [rn, f"{amt:,.2f}"])
