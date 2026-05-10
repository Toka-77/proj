"""pages.py — All page builders for AIS Hub (unified)."""
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QDoubleSpinBox, QSpinBox, QFormLayout,
    QFrame, QMessageBox, QGridLayout, QScrollArea, QTabWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QDateEdit,
    QTimeEdit, QProgressBar, QCheckBox
)
from PyQt5.QtCore import Qt, QDate, QTime
from PyQt5.QtGui import QColor
from widgets import StatCard, RoomStatusCard, make_table, set_row, make_divider
from core import (
    RoomManager, SessionManager, InventoryManager, ExpenseManager, ReportManager,
    SalesInvoiceManager, PurchaseInvoiceManager,
    AccountingManager, AccountStatementManager,
    LoyaltyManager, SettingsManager, BookingManager, PDFGenerator,
)
import database
from datetime import datetime


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
        self.s_prof.update_value(f"{abs(p):.0f} EGP", "#3ecf8e" if p >= 0 else "#f06292")
        self.s_prof.update_title("Net Profit" if p >= 0 else "Net Loss")

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

        left = QWidget(); left.setObjectName("card")
        ll = QVBoxLayout(left); ll.setContentsMargins(16,16,16,16)
        ll.addWidget(QLabel("All Rooms", objectName="sec_title"))
        self.rooms_tbl = make_table(["#","Name","Type","Status","Price/hr","Capacity"])
        self.rooms_tbl.itemSelectionChanged.connect(self._on_room_select)
        ll.addWidget(self.rooms_tbl)
        
        edit_btn = QPushButton("✏️ Edit Selected Room Price")
        edit_btn.setObjectName("secondary")
        edit_btn.setCursor(Qt.PointingHandCursor)
        edit_btn.clicked.connect(self.handle_edit_room)
        ll.addWidget(edit_btn)
        add_room_btn = QPushButton("➕ Add New Room")
        add_room_btn.setObjectName("primary")
        add_room_btn.setCursor(Qt.PointingHandCursor)
        add_room_btn.clicked.connect(self.handle_add_room)
        ll.addWidget(add_room_btn)
        
        grid.addWidget(left, 3)

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

        lay.addWidget(QLabel("📋  Session History", objectName="sec_title"))
        self.hist_tbl = make_table(["#","Room","Type","Customer","People","Start","End","Room $","Snacks","Disc","Total"])
        self.hist_tbl.setMaximumHeight(200)
        lay.addWidget(self.hist_tbl)
        
        pdf_btn = QPushButton("📄 Export Session Invoice (PDF)")
        pdf_btn.setObjectName("secondary")
        pdf_btn.setCursor(Qt.PointingHandCursor)
        pdf_btn.clicked.connect(self.handle_pdf)
        lay.addWidget(pdf_btn)

        self._refresh_cb = None

    def _on_room_select(self):
        row = self.rooms_tbl.currentRow()
        if row < 0 or row >= len(getattr(self, '_room_ids', [])): return
        rid = self._room_ids[row]
        for i in range(self.start_room.count()):
            if self.start_room.itemData(i) == rid:
                self.start_room.setCurrentIndex(i)
                break

    def refresh(self):
        rooms = RoomManager.get_all_rooms()
        self._room_ids = [r[0] for r in rooms]
        self.rooms_tbl.setRowCount(len(rooms))
        self.start_room.clear()
        for i, r in enumerate(rooms):
            set_row(self.rooms_tbl, i, [i+1, r[1], r[2], r[3], f"{r[4]:.0f}", r[5]])
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
        self._hist_ids = [h[0] for h in hist]
        self.hist_tbl.setRowCount(len(hist))
        for i, h in enumerate(hist):
            set_row(self.hist_tbl, i, [i+1,h[1],h[2],h[3],h[4],h[5],h[6] or "Active",
                    f"{h[7]:.1f}",f"{h[8]:.1f}",f"{h[9]:.1f}",f"{h[10]:.1f}"])

    def handle_start(self):
        rid = self.start_room.currentData()
        if not rid:
            return QMessageBox.warning(self.page, "Error", "No available room.")
            
        cname = self.start_cust.text().strip()
        if not cname:
            return QMessageBox.warning(self.page, "Required", "Enter customer name.")
        num = self.start_ppl.value()

        rooms = RoomManager.get_all_rooms()
        cap = next((r[5] for r in rooms if r[0] == rid), None)
        if cap and num > cap:
            reply = QMessageBox.question(
                self.page, "⚠️ Over Capacity",
                f"This room fits {cap} people but you entered {num}.\nProceed anyway?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return

        sid, msg = SessionManager.start_session(rid, cname, num)
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
            cust = res.get('customer_name', 'Walk-in')
            total = res.get('total_bill', 0)
            if cust and cust != 'Walk-in' and total > 0:
                try:
                    new_pts, tier = LoyaltyManager.add_points(cust, total)
                    pts_note = f"\n{'─'*30}\n🎯 Loyalty: +{int(total)} pts  → {new_pts:,} pts ({tier})"
                except Exception:
                    pts_note = ""
            else:
                pts_note = ""

            msg = (f"Session #{res['session_id']} Closed\n\n"
                   f"Duration:     {res['duration_hours']:.2f} hrs\n"
                   f"Room Charge:  {res['room_charge']:.2f} EGP\n"
                   f"Snacks:       {res['snacks_total']:.2f} EGP\n"
                   f"Discount:    -{res['discount']:.2f} EGP\n"
                   f"Deposit:     -{res.get('deposit', 0.0):.2f} EGP\n"
                   f"{'─'*30}\n"
                   f"TOTAL:        {res['total_bill']:.2f} EGP"
                   + pts_note)
            QMessageBox.information(self.page, "💰 Final Bill", msg)
            self.end_disc.setValue(0)
            if self._refresh_cb: self._refresh_cb()
        else:
            QMessageBox.warning(self.page, "Error", res)

    def handle_edit_room(self):
        from PyQt5.QtWidgets import QInputDialog
        row = self.rooms_tbl.currentRow()
        if row < 0 or row >= len(self._room_ids):
            return QMessageBox.warning(self.page, "Error", "Select a room from the table first.")
        rid = self._room_ids[row]
        rname = self.rooms_tbl.item(row, 1).text()
        curr_price = float(self.rooms_tbl.item(row, 4).text())
        
        new_price, ok = QInputDialog.getDouble(self.page, "Edit Room Price", f"Enter new hourly price for {rname}:", curr_price, 0, 10000, 2)
        if ok:
            RoomManager.update_price(rid, new_price)
            self.refresh()

    def handle_pdf(self):
        row = self.hist_tbl.currentRow()
        if row < 0 or row >= len(getattr(self, '_hist_ids', [])):
            return QMessageBox.warning(self.page, "Error", "Select a session from the history table.")
        sid = self._hist_ids[row]
        from core import PDFGenerator
        ok, result = PDFGenerator.generate_session_invoice(sid)
        if ok:
            QMessageBox.information(self.page, "✅ PDF Generated", f"Invoice saved at:\n{result}")
            import os
            os.startfile(result)
        else:
            QMessageBox.warning(self.page, "Error", result)


    def handle_add_room(self):
        from PyQt5.QtWidgets import QDialog, QDialogButtonBox
        dlg = QDialog(self.page)
        dlg.setWindowTitle("Add New Room")
        dlg.setMinimumWidth(320)
        fl = QFormLayout(dlg); fl.setSpacing(10); fl.setContentsMargins(16,16,16,16)
        name_e = QLineEdit(); name_e.setPlaceholderText("e.g. Study Room C")
        type_cb = QComboBox(); type_cb.addItems(["Study", "Gaming", "Cinema"])
        price_e = QDoubleSpinBox(); price_e.setMaximum(9999); price_e.setDecimals(2); price_e.setPrefix("EGP ")
        cap_e   = QSpinBox(); cap_e.setMinimum(1); cap_e.setMaximum(100); cap_e.setValue(10)
        desc_e  = QLineEdit(); desc_e.setPlaceholderText("Optional description")
        fl.addRow("Name:", name_e)
        fl.addRow("Type:", type_cb)
        fl.addRow("Price/hr:", price_e)
        fl.addRow("Capacity:", cap_e)
        fl.addRow("Description:", desc_e)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(dlg.accept); btns.rejected.connect(dlg.reject)
        fl.addRow(btns)
        if dlg.exec_() == QDialog.Accepted:
            name = name_e.text().strip()
            if not name:
                return QMessageBox.warning(self.page, "Error", "Room name is required.")
            ok, msg = RoomManager.add_room(name, type_cb.currentText(), price_e.value(), cap_e.value(), desc_e.text().strip())
            QMessageBox.information(self.page, "✅", msg) if ok else QMessageBox.warning(self.page, "Error", msg)
            self.refresh()

    # ═══ INVENTORY ═══
class InventoryPage:
    def __init__(self):
        self.page, lay = page_container("Snacks & Inventory")
        grid = QHBoxLayout(); grid.setSpacing(20)

        left = QWidget(); left.setObjectName("card")
        ll = QVBoxLayout(left); ll.setContentsMargins(16,16,16,16)
        hdr_layout = QHBoxLayout()
        hdr_layout.addWidget(QLabel("📦  Products Catalogue", objectName="sec_title"))
        hdr_layout.addStretch()
        self.inv_val_lbl = QLabel("Total Value: 0.00 EGP")
        self.inv_val_lbl.setStyleSheet("font-weight:bold; color:#3ecf8e; font-size:14px;")
        hdr_layout.addWidget(self.inv_val_lbl)
        ll.addLayout(hdr_layout)
        self.prod_tbl = make_table(["SKU","Name","Category","Cost","Selling Price","Stock"])
        ll.addWidget(self.prod_tbl)

        ll.addWidget(QLabel("⚠️  Low Stock Alerts", objectName="sec_title"))
        self.low_tbl = make_table(["SKU","Product","Stock"])
        self.low_tbl.setMaximumHeight(120)
        ll.addWidget(self.low_tbl)

        grid.addWidget(left, 3)

        right = QWidget(); right.setObjectName("card")
        rl = QVBoxLayout(right); rl.setContentsMargins(16,16,20,20); rl.setSpacing(14)

        rl.addWidget(QLabel("✏️  Edit Price & Cost", objectName="sec_title"))
        note = QLabel("Select a product row, then update its selling price and cost.")
        note.setStyleSheet("color:#6a7a9a; font-size:11px;"); note.setWordWrap(True)
        rl.addWidget(note)

        f = QFormLayout(); f.setSpacing(10)
        self.sel_sku  = QLineEdit(); self.sel_sku.setReadOnly(True)
        self.sel_sku.setPlaceholderText("Auto-filled on row select")
        self.sel_name = QLineEdit()
        self.sel_name.setPlaceholderText("Product name (editable)")
        self.new_cost = QDoubleSpinBox(); self.new_cost.setMaximum(99999); self.new_cost.setPrefix("EGP ")
        self.new_price = QDoubleSpinBox(); self.new_price.setMaximum(99999); self.new_price.setPrefix("EGP ")
        f.addRow("SKU:",       self.sel_sku)
        f.addRow("Name:",      self.sel_name)
        f.addRow("Unit Cost:", self.new_cost)
        f.addRow("Sale Price:", self.new_price)
        rl.addLayout(f)

        btn_row = QHBoxLayout(); btn_row.setSpacing(8)
        self.upd_btn = QPushButton("💾  Update Price"); self.upd_btn.setObjectName("primary")
        self.upd_btn.setCursor(Qt.PointingHandCursor); self.upd_btn.clicked.connect(self.handle_update_price)
        self.del_btn = QPushButton("🗑  Delete Product"); self.del_btn.setObjectName("danger")
        self.del_btn.setCursor(Qt.PointingHandCursor); self.del_btn.clicked.connect(self.handle_delete_product)
        btn_row.addWidget(self.upd_btn); btn_row.addWidget(self.del_btn)
        rl.addLayout(btn_row)
        rl.addStretch()
        grid.addWidget(right, 2)
        lay.addLayout(grid)
        self._refresh_cb = None
        self.prod_tbl.itemSelectionChanged.connect(self._on_row_select)

    def _on_row_select(self):
        row = self.prod_tbl.currentRow()
        if row < 0: return
        self.sel_sku.setText(self.prod_tbl.item(row, 0).text())
        self.sel_name.setText(self.prod_tbl.item(row, 1).text())
        try:    self.new_cost.setValue(float(self.prod_tbl.item(row, 3).text()))
        except: pass
        try:    self.new_price.setValue(float(self.prod_tbl.item(row, 4).text()))
        except: pass

    def refresh(self):
        total_val = InventoryManager.get_total_inventory_value()
        self.inv_val_lbl.setText(f"Total Value: {total_val:,.2f} EGP")
        
        prods = InventoryManager.get_all_products()
        self.prod_tbl.setRowCount(len(prods))
        for i, p in enumerate(prods):
            set_row(self.prod_tbl, i, [p[0], p[1], p[2], f"{p[3]:.2f}", f"{p[4]:.2f}", p[5]])
            si = self.prod_tbl.item(i, 5)
            if si and p[5] <= 5: si.setForeground(QColor("#f06292"))

        low = InventoryManager.get_low_stock(threshold=5)
        self.low_tbl.setRowCount(len(low))
        for i, l in enumerate(low):
            set_row(self.low_tbl, i, [l[0], l[1], l[3]])

    def handle_update_price(self):
        sku = self.sel_sku.text().strip()
        if not sku: return QMessageBox.warning(self.page, "Select Product", "Click a row first.")
        if self.new_price.value() <= 0: return QMessageBox.warning(self.page, "Invalid", "Price must be > 0.")
        # Update name if changed
        new_name = self.sel_name.text().strip()
        if new_name:
            conn = __import__('database').get_connection()
            conn.execute("UPDATE products SET name=? WHERE sku=?", (new_name, sku))
            conn.commit(); conn.close()
        ok, msg = InventoryManager.update_selling_price(sku, self.new_price.value())
        # Also update cost
        conn2 = __import__('database').get_connection()
        conn2.execute("UPDATE products SET unit_cost=? WHERE sku=?", (self.new_cost.value(), sku))
        conn2.commit(); conn2.close()
        if ok:
            QMessageBox.information(self.page, "✅", "Product updated.")
            self.refresh()
            if self._refresh_cb: self._refresh_cb()
        else:
            QMessageBox.warning(self.page, "Error", msg)

    def handle_delete_product(self):
        sku = self.sel_sku.text().strip()
        name = self.sel_name.text().strip()
        if not sku: return QMessageBox.warning(self.page, "Select Product", "Click a row first.")
        reply = QMessageBox.question(
            self.page, "🗑  Delete Product",
            f"Delete '{name}' ({sku}) permanently?\nThis cannot be undone.",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            ok, msg = InventoryManager.delete_product(sku)
            if ok:
                QMessageBox.information(self.page, "✅", msg)
                self.sel_sku.clear(); self.sel_name.clear()
                self.new_price.setValue(0)
                self.refresh()
                if self._refresh_cb: self._refresh_cb()
            else:
                QMessageBox.warning(self.page, "Error", msg)

    def set_readonly(self, readonly: bool):
        self.upd_btn.setEnabled(not readonly)
        self.del_btn.setEnabled(not readonly)
        self.new_price.setEnabled(not readonly)
        self.new_cost.setEnabled(not readonly)
        if readonly:
            self.upd_btn.setToolTip("🔒 Admin only")
            self.del_btn.setToolTip("🔒 Admin only")
            self.new_price.setToolTip("🔒 Admin only — price editing restricted")
            self.new_cost.setToolTip("🔒 Admin only — cost editing restricted")


# ═══════════════════════════════════════════════════════════════
#  EXPENSES
# ═══════════════════════════════════════════════════════════════
class ExpensesPage:
    def __init__(self):
        self.page, lay = page_container("Expenses")
        grid = QHBoxLayout(); grid.setSpacing(20)

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

        self._exp_ids = []
        self._refresh_cb = None

    def refresh(self):
        exps = ExpenseManager.get_all_expenses()
        self._exp_ids = [e[0] for e in exps]
        self.exp_tbl.setRowCount(len(exps))
        for i, e in enumerate(exps):
            set_row(self.exp_tbl, i, [i+1, e[1], f"{e[2]:.2f}", e[3], e[4]])
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
        eid = self._exp_ids[row] if hasattr(self, "_exp_ids") and row < len(self._exp_ids) else -1
        reply = QMessageBox.question(self.page, "Confirm", f"Delete expense #{row+1}?",
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

        row2 = QHBoxLayout(); row2.setSpacing(14)
        self.r_sess   = StatCard("🎫", "Total Sessions",  "—", "#7c5cbf")
        self.r_active = StatCard("⏱", "Active Sessions",  "—", "#ffa726")
        self.r_inv    = StatCard("📦", "Inventory Value",  "—", "#5c9cf5")
        self.r_today  = StatCard("🧃", "Snacks Today",    "—", "#3ecf8e")
        for c in [self.r_sess, self.r_active, self.r_inv, self.r_today]:
            row2.addWidget(c)
        lay.addLayout(row2)

        lay.addWidget(QLabel("📊  Revenue per Room Type (Segment Reporting)", objectName="sec_title"))
        self.type_tbl = make_table(["Room Type","Revenue (EGP)","% of Total"])
        self.type_tbl.setMaximumHeight(150)
        lay.addWidget(self.type_tbl)

        lay.addWidget(QLabel("🏠  Revenue per Room", objectName="sec_title"))
        self.room_tbl = make_table(["Room","Revenue (EGP)"])
        self.room_tbl.setMaximumHeight(200)
        lay.addWidget(self.room_tbl)

    def refresh(self):
        rep = ReportManager.generate_report()
        self.r_rev.update_value(f"{rep['total_revenue']:,.2f} EGP")
        self.r_exp.update_value(f"{rep['total_expenses']:,.2f} EGP")
        p = rep['profit']
        self.r_prof.update_value(f"{abs(p):,.2f} EGP", "#3ecf8e" if p >= 0 else "#f06292")
        self.r_prof.update_title("Net Profit" if p >= 0 else "Net Loss")
        top_room = rep['most_used_room']
        top_count = rep['most_used_count']
        if top_room == 'No Data':
            self.r_top.update_value("0 sessions")
        else:
            self.r_top.update_value(f"{top_room} ({top_count})")
        self.r_sess.update_value(rep['total_sessions'])
        self.r_active.update_value(rep['active_sessions'])
        from core import InventoryManager
        self.r_inv.update_value(f"{InventoryManager.get_total_inventory_value():,.2f} EGP")
        self.r_today.update_value(f"{rep['snacks_today']:,.0f} EGP")

        rev_type = rep['revenue_per_type']
        total_r = max(sum(rev_type.values()), 1)
        types = ['Study', 'Gaming', 'Cinema']
        self.type_tbl.setRowCount(len(types))
        for i, t in enumerate(types):
            amt = rev_type.get(t, 0)
            pct = (amt / total_r) * 100
            set_row(self.type_tbl, i, [f"{'📚' if t=='Study' else '🎮' if t=='Gaming' else '🎬'}  {t}",
                                        f"{amt:,.2f}", f"{pct:.1f}%"])

        rev_room = rep['revenue_per_room']
        self.room_tbl.setRowCount(len(rev_room))
        for i, (rn, amt) in enumerate(rev_room.items()):
            set_row(self.room_tbl, i, [rn, f"{amt:,.2f}"])


# ═══════════════════════════════════════════════════════════════
#  SALES INVOICE PAGE
# ═══════════════════════════════════════════════════════════════
class SalesInvoicePage:
    def __init__(self):
        self.page, lay = page_container("Sales", "Sales Invoices")
        grid = QHBoxLayout(); grid.setSpacing(20)

        left = QWidget(); left.setObjectName("card")
        ll = QVBoxLayout(left); ll.setContentsMargins(16,16,16,16)
        ll.addWidget(QLabel("📋  Sales Invoices", objectName="sec_title"))
        self.inv_tbl = make_table(["#","Customer","Date","Total","Status"])
        self.inv_tbl.itemSelectionChanged.connect(self._on_inv_select)
        ll.addWidget(self.inv_tbl)
        
        self.detail_card = QWidget()
        dl = QVBoxLayout(self.detail_card)
        dl.setContentsMargins(0,10,0,0)
        self.detail_title = QLabel("Invoice Details")
        self.detail_title.setObjectName("sec_title")
        self.detail_info = QLabel("")
        self.detail_info.setStyleSheet("color:#6a7a9a; font-size:12px; margin-bottom:4px;")
        self.detail_tbl = make_table(["Product","Qty","Price","Total"])
        self.detail_tbl.setMaximumHeight(100)
        dl.addWidget(self.detail_title)
        dl.addWidget(self.detail_info)
        dl.addWidget(self.detail_tbl)
        ll.addWidget(self.detail_card)
        self.detail_card.hide()

        row = QHBoxLayout()
        del_btn = QPushButton("🗑 Delete"); del_btn.setObjectName("danger")
        del_btn.setCursor(Qt.PointingHandCursor); del_btn.clicked.connect(self.handle_delete)
        paid_btn = QPushButton("✅ Mark Paid"); paid_btn.setObjectName("primary")
        paid_btn.setCursor(Qt.PointingHandCursor); paid_btn.clicked.connect(self.handle_paid)
        pdf_btn = QPushButton("📄 Export PDF"); pdf_btn.setObjectName("secondary")
        pdf_btn.setCursor(Qt.PointingHandCursor); pdf_btn.clicked.connect(self.handle_pdf)
        row.addWidget(del_btn); row.addWidget(paid_btn); row.addWidget(pdf_btn); row.addStretch()
        ll.addLayout(row)
        grid.addWidget(left, 3)

        right = QWidget(); right.setObjectName("card")
        rl = QVBoxLayout(right); rl.setContentsMargins(16,16,16,20); rl.setSpacing(12)
        rl.addWidget(QLabel("🧾  Sales Invoice", objectName="sec_title"))
        f = QFormLayout(); f.setSpacing(8)
        self.cust_edit = QLineEdit(); self.cust_edit.setPlaceholderText("Enter customer name…")
        self.sess_combo = QComboBox()
        f.addRow("Customer:",        self.cust_edit)
        f.addRow("Link to Session:", self.sess_combo)
        rl.addLayout(f)

        rl.addWidget(QLabel("Products:", objectName="sec_title"))
        self.item_rows = []
        self.items_layout = QVBoxLayout()
        rl.addLayout(self.items_layout)

        ab = QPushButton("➕ Add Line"); ab.setObjectName("secondary")
        ab.setCursor(Qt.PointingHandCursor); ab.clicked.connect(self._add_item_row)
        rl.addWidget(ab)

        self.total_lbl = QLabel("Total: 0.00 EGP")
        self.total_lbl.setStyleSheet("font-size:16px; font-weight:700; color:#3ecf8e;")
        rl.addWidget(self.total_lbl)
        self._add_item_row()
        
        self.paid_check = QCheckBox("Paid immediately (Cash)")
        self.paid_check.setChecked(True)
        rl.addWidget(self.paid_check)

        save = QPushButton("💾  Save Invoice"); save.setObjectName("primary")
        save.setCursor(Qt.PointingHandCursor); save.clicked.connect(self.handle_save)
        rl.addWidget(save); rl.addStretch()
        grid.addWidget(right, 2)
        lay.addLayout(grid)
        self._inv_ids = []
        self._refresh_cb = None

    def _add_item_row(self):
        row_w = QWidget()
        hl = QHBoxLayout(row_w); hl.setContentsMargins(0,0,0,0); hl.setSpacing(6)
        prod = QComboBox(); prod.setMinimumWidth(120)
        qty = QSpinBox(); qty.setMinimum(1); qty.setMaximum(9999)
        price = QDoubleSpinBox(); price.setMaximum(99999); price.setDecimals(2); price.setPrefix("EGP ")
        if getattr(self, '_is_readonly', False):
            price.setReadOnly(True)
        rm = QPushButton("✕"); rm.setFixedWidth(30); rm.setObjectName("danger")

        def on_prod_change(idx, p=prod, pr=price):
            data = p.currentData()
            if data and isinstance(data, tuple) and len(data) > 1:
                pr.setValue(data[1])

        prod.currentIndexChanged.connect(on_prod_change)
        qty.valueChanged.connect(lambda: self._update_total())
        price.valueChanged.connect(lambda: self._update_total())

        hl.addWidget(prod, 3); hl.addWidget(qty, 1); hl.addWidget(price, 2); hl.addWidget(rm)
        entry = {'widget': row_w, 'prod': prod, 'qty': qty, 'price': price}
        self.item_rows.append(entry)
        self.items_layout.addWidget(row_w)

        def remove(checked=False, e=entry):
            if len(self.item_rows) > 1:
                if e in self.item_rows:
                    self.item_rows.remove(e)
                    e['widget'].deleteLater()
                    self._update_total()
        rm.clicked.connect(remove)
        self._populate_products()

    def _populate_products(self):
        prods = InventoryManager.get_all_products()
        for entry in self.item_rows:
            cb = entry['prod']
            if cb.count() == 0:
                cb.blockSignals(True)
                for p in prods:
                    # p = (sku, name, category, unit_cost, selling_price, quantity)
                    cb.addItem(f"{p[1]}  [stock: {p[5]}]", (p[0], p[4], p[3]))
                cb.blockSignals(False)
                if cb.count() > 0:
                    data = cb.currentData()
                    if data and isinstance(data, tuple) and len(data) > 1:
                        entry['price'].setValue(data[1])

    def _update_total(self):
        total = sum(e['qty'].value() * e['price'].value() for e in self.item_rows)
        self.total_lbl.setText(f"Total: {total:.2f} EGP")

    def _on_inv_select(self):
        row = self.inv_tbl.currentRow()
        if row < 0 or row >= len(self._inv_ids):
            self.detail_card.hide(); return
        iid = self._inv_ids[row]
        cust = self.inv_tbl.item(row, 1).text()
        date = self.inv_tbl.item(row, 2).text()
        tot  = self.inv_tbl.item(row, 3).text()
        stat = self.inv_tbl.item(row, 4).text()
        self.detail_title.setText(f"Invoice #{row+1}  —  {cust}")
        self.detail_info.setText(f"Date: {date}   Total: {tot} EGP   Status: {stat}")
        items = SalesInvoiceManager.get_invoice_items(iid)
        self.detail_tbl.setRowCount(len(items))
        for i, (name, qty, price, total) in enumerate(items):
            set_row(self.detail_tbl, i, [name, qty, f"{price:.2f}", f"{total:.2f}"])
        self.detail_card.show()

    def refresh(self):
        self.sess_combo.clear()
        self.sess_combo.addItem("None (no session)", None)
        for s in SessionManager.get_active_sessions():
            self.sess_combo.addItem(f"#{s[0]}  {s[1]}  —  {s[2]}", s[0])

        invs = SalesInvoiceManager.get_all_invoices()
        self._inv_ids = [inv[0] for inv in invs]
        self.inv_tbl.setRowCount(len(invs))
        for i, inv in enumerate(invs):
            set_row(self.inv_tbl, i, [f"#{i+1}", inv[1], inv[2], f"{inv[3]:.2f}", inv[4]])
            si = self.inv_tbl.item(i, 4)
            if si: si.setForeground(QColor("#3ecf8e") if inv[4]=="Paid" else QColor("#ffa726"))
        self.detail_card.hide()

        for entry in self.item_rows:
            entry['prod'].clear()
        self._populate_products()

    def handle_save(self):
        cust = self.cust_edit.text().strip()
        if not cust: return QMessageBox.warning(self.page, "Error", "Enter customer name.")
        session_id = self.sess_combo.currentData()
        items = []
        requires_override = False
        override_msg = ""
        for e in self.item_rows:
            data = e['prod'].currentData()
            if not data: continue
            
            sku = data[0]
            unit_cost = data[2] if len(data) > 2 else 0.0
            price = e['price'].value()

            if price <= 0:
                return QMessageBox.warning(self.page, "Invalid Price",
                    f"Price for '{e['prod'].currentText().split('[')[0].strip()}' must be > 0 EGP.")
            
            if price < unit_cost:
                requires_override = True
                override_msg += f"\n- {e['prod'].currentText().split('[')[0].strip()} (Cost: {unit_cost:.2f}, Price: {price:.2f})"
                
            items.append((sku, e['qty'].value(), price))

        if requires_override:
            reply = QMessageBox.warning(self.page, "Warning - Below Cost", 
                f"The following items are priced below their cost:{override_msg}\n\nDo you want to proceed?", 
                QMessageBox.Yes | QMessageBox.No)
            if reply != QMessageBox.Yes: return

            main_win = self.page.window()
            is_admin = False
            if hasattr(main_win, 'current_user') and main_win.current_user:
                if main_win.current_user['role'] == 'admin':
                    is_admin = True
            
            if not is_admin:
                from PyQt5.QtWidgets import QInputDialog, QLineEdit
                pwd, ok = QInputDialog.getText(self.page, "Manager Override", "Enter Admin Password to authorize selling below cost:", QLineEdit.Password)
                if not ok or not pwd: return
                
                import hashlib
                pw_hash = hashlib.sha256(pwd.encode()).hexdigest()
                conn = database.get_connection()
                admin_user = conn.execute("SELECT id FROM users WHERE role='admin' AND password_hash=?", (pw_hash,)).fetchone()
                conn.close()
                if not admin_user:
                    return QMessageBox.warning(self.page, "Error", "Invalid admin password! Transaction blocked.")
                    
        if not items: return QMessageBox.warning(self.page, "Error", "Add at least one product.")
        ok, msg = SalesInvoiceManager.create_invoice(cust, items, session_id=session_id, paid=self.paid_check.isChecked())
        if ok:
            try:
                total = sum(qty * price for _, qty, price in items)
                if cust and cust.lower() != 'walk-in' and total > 0:
                    LoyaltyManager.add_points(cust, total)
            except Exception:
                pass
            QMessageBox.information(self.page, "✅", msg)
            self.cust_edit.clear()
            for e in self.item_rows: e['widget'].deleteLater()
            self.item_rows.clear()
            self._add_item_row()
            self._update_total()
            self.refresh()
            if self._refresh_cb: self._refresh_cb()
        else:
            QMessageBox.warning(self.page, "Error", msg)

    def handle_delete(self):
        row = self.inv_tbl.currentRow()
        if row < 0 or row >= len(self._inv_ids): return QMessageBox.warning(self.page, "Error", "Select an invoice.")
        iid = self._inv_ids[row]
        reply = QMessageBox.question(self.page, "Confirm", f"Delete invoice #{row+1}?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            SalesInvoiceManager.delete_invoice(iid); self.refresh()

    def handle_paid(self):
        row = self.inv_tbl.currentRow()
        if row < 0 or row >= len(self._inv_ids): return QMessageBox.warning(self.page, "Error", "Select an invoice.")
        iid = self._inv_ids[row]
        SalesInvoiceManager.mark_paid(iid); self.refresh()

    def handle_pdf(self):
        row = self.inv_tbl.currentRow()
        if row < 0 or row >= len(self._inv_ids): return QMessageBox.warning(self.page, "Error", "Select an invoice.")
        iid = self._inv_ids[row]
        ok, result = PDFGenerator.generate_sales_invoice(iid)
        if ok:
            QMessageBox.information(self.page, "✅ PDF", f"Invoice saved:\n{result}")
            os.startfile(result)
        else:
            QMessageBox.warning(self.page, "Error", result)

    def set_readonly(self, readonly: bool):
        self._is_readonly = readonly
        for entry in self.item_rows:
            entry['price'].setReadOnly(readonly)


# ═══════════════════════════════════════════════════════════════
#  PURCHASE INVOICE PAGE
# ═══════════════════════════════════════════════════════════════
class PurchaseInvoicePage:
    def __init__(self):
        self.page, lay = page_container("Purchase", "Purchase Invoices")
        self._inv_ids = []
        grid = QHBoxLayout(); grid.setSpacing(20)

        left = QWidget(); left.setObjectName("card")
        ll = QVBoxLayout(left); ll.setContentsMargins(16,16,16,16); ll.setSpacing(10)

        ll.addWidget(QLabel("📋  Purchase History", objectName="sec_title"))
        self.inv_tbl = make_table(["#","Supplier","Date","Total EGP","Status"])
        self.inv_tbl.itemSelectionChanged.connect(self._on_inv_select)
        ll.addWidget(self.inv_tbl)

        btn_row = QHBoxLayout()
        del_btn  = QPushButton("🗑  Delete");    del_btn.setObjectName("danger")
        paid_btn = QPushButton("✅  Mark Paid"); paid_btn.setObjectName("primary")
        pdf_btn  = QPushButton("📄  Export PDF"); pdf_btn.setObjectName("secondary")
        del_btn.setCursor(Qt.PointingHandCursor);  del_btn.clicked.connect(self.handle_delete)
        paid_btn.setCursor(Qt.PointingHandCursor); paid_btn.clicked.connect(self.handle_paid)
        pdf_btn.setCursor(Qt.PointingHandCursor);  pdf_btn.clicked.connect(self.handle_pdf)
        btn_row.addWidget(del_btn); btn_row.addWidget(paid_btn); btn_row.addWidget(pdf_btn); btn_row.addStretch()
        ll.addLayout(btn_row)

        self.detail_card = QWidget(); self.detail_card.setObjectName("card")
        self.detail_card.setStyleSheet("background:#141e33; border:1px solid #2a3a5a; border-radius:8px;")
        dl = QVBoxLayout(self.detail_card); dl.setContentsMargins(14,12,14,12); dl.setSpacing(6)
        self.detail_title = QLabel("Invoice Details"); self.detail_title.setObjectName("sec_title")
        dl.addWidget(self.detail_title)
        self.detail_info = QLabel(""); self.detail_info.setStyleSheet("color:#8a9cc8; font-size:11px;")
        dl.addWidget(self.detail_info)
        self.detail_tbl = make_table(["Product","Qty","Unit Cost","Total"])
        self.detail_tbl.setMaximumHeight(160)
        dl.addWidget(self.detail_tbl)
        self.detail_card.hide()
        ll.addWidget(self.detail_card)

        grid.addWidget(left, 3)

        right = QWidget(); right.setObjectName("card")
        rl = QVBoxLayout(right); rl.setContentsMargins(18,18,18,20); rl.setSpacing(14)

        hdr = QHBoxLayout()
        hdr.addWidget(QLabel("➕  Add Purchase Invoice", objectName="sec_title"))
        hdr.addStretch()
        self.inv_val_lbl = QLabel("Total Inventory Value: 0.00 EGP")
        self.inv_val_lbl.setStyleSheet("font-weight:bold; color:#3ecf8e; font-size:14px;")
        hdr.addWidget(self.inv_val_lbl)
        rl.addLayout(hdr)

        sup_lbl = QLabel("Supplier"); sup_lbl.setStyleSheet("color:#8a9cc8; font-size:10px; font-weight:600; letter-spacing:1px;")
        rl.addWidget(sup_lbl)
        self.sup_combo = QComboBox(); self.sup_combo.setEditable(True)
        rl.addWidget(self.sup_combo)

        rl.addWidget(make_divider())
        rl.addWidget(QLabel("Products", objectName="sec_title"))

        hdr = QWidget()
        hdr_l = QHBoxLayout(hdr); hdr_l.setContentsMargins(0,0,26,0); hdr_l.setSpacing(4)
        def _hdr(text, stretch=0, width=0):
            lbl = QLabel(text)
            lbl.setStyleSheet("color:#5a6a8a; font-size:10px; font-weight:600; letter-spacing:0.5px;")
            if width: lbl.setFixedWidth(width)
            hdr_l.addWidget(lbl, stretch)
        _hdr("Product Name", stretch=2)
        _hdr("Category",  width=90)
        _hdr("Qty",       width=72)
        _hdr("Cost (EGP)",width=130)
        _hdr("Sale (EGP)",width=130)
        rl.addWidget(hdr)

        self.item_rows = []
        self.items_layout = QVBoxLayout(); self.items_layout.setSpacing(6)
        rl.addLayout(self.items_layout)

        ab = QPushButton("➕  Add Line"); ab.setObjectName("secondary")
        ab.setCursor(Qt.PointingHandCursor); ab.clicked.connect(self._add_item_row)
        rl.addWidget(ab)

        rl.addWidget(make_divider())

        self.total_lbl = QLabel("Total: 0.00 EGP")
        self.total_lbl.setStyleSheet("font-size:16px; font-weight:700; color:#f06292;")
        rl.addWidget(self.total_lbl)

        self._add_item_row()

        self.paid_check = QCheckBox("Paid immediately (Cash)")
        self.paid_check.setChecked(True)
        rl.addWidget(self.paid_check)

        save = QPushButton("💾  Save Invoice"); save.setObjectName("primary")
        save.setMinimumHeight(38); save.setCursor(Qt.PointingHandCursor)
        save.clicked.connect(self.handle_save)
        rl.addWidget(save); rl.addStretch()
        grid.addWidget(right, 2)
        lay.addLayout(grid)
        self._refresh_cb = None

    def _add_item_row(self):
        row_w = QWidget()
        hl = QHBoxLayout(row_w); hl.setContentsMargins(0, 0, 0, 0); hl.setSpacing(4)

        name_fld  = QLineEdit();      name_fld.setMinimumWidth(120); name_fld.setMinimumHeight(34); name_fld.setPlaceholderText("Type product name…")
        cat_combo = QComboBox();      cat_combo.addItems(["Drinks","Snacks","Hot","Other"]); cat_combo.setFixedWidth(90); cat_combo.setMinimumHeight(34)
        qty_spin  = QSpinBox();       qty_spin.setMinimum(1); qty_spin.setMaximum(9999); qty_spin.setFixedWidth(72); qty_spin.setMinimumHeight(34)
        cost_spin = QDoubleSpinBox(); cost_spin.setMaximum(99999); cost_spin.setDecimals(2); cost_spin.setPrefix("EGP "); cost_spin.setFixedWidth(130); cost_spin.setMinimumHeight(34)
        sale_spin = QDoubleSpinBox(); sale_spin.setMaximum(99999); sale_spin.setDecimals(2); sale_spin.setPrefix("EGP "); sale_spin.setFixedWidth(130); sale_spin.setMinimumHeight(34)
        rm_btn    = QPushButton("✕"); rm_btn.setFixedWidth(30); rm_btn.setMinimumHeight(34); rm_btn.setObjectName("danger")

        sale_spin.hide()

        info_cat  = QLabel(""); info_cat.setFixedWidth(72); info_cat.setStyleSheet("color:#5a9cf5; font-size:10px;"); info_cat.hide()
        info_sale = QLabel(""); info_sale.setFixedWidth(110); info_sale.setStyleSheet("color:#3ecf8e; font-size:10px;"); info_sale.hide()

        entry = {
            'widget': row_w, 'name_fld': name_fld,
            'cat_combo': cat_combo, 'qty': qty_spin, 'cost': cost_spin,
            'sale': sale_spin, 'info_cat': info_cat, 'info_sale': info_sale,
            'is_new': True,
        }
        cat_combo.show(); sale_spin.show()

        def _lookup(e=entry):
            name = e['name_fld'].text().strip()
            prod = InventoryManager.get_product_by_name(name) if name else None
            if prod:
                e['is_new'] = False
                e['prod_data'] = prod
                e['name_fld'].setStyleSheet("color:#3ecf8e;")
                e['cat_combo'].hide(); e['sale'].hide()
                e['info_cat'].setText(prod[2])
                e['info_sale'].setText(f"Stock: {prod[5]}")
                e['info_cat'].show(); e['info_sale'].show()
            else:
                e['is_new'] = True
                e['prod_data'] = None
                e['name_fld'].setStyleSheet("")
                e['info_cat'].hide(); e['info_sale'].hide()
                e['cat_combo'].show(); e['sale'].show()

        name_fld.editingFinished.connect(lambda e=entry: _lookup(e))
        qty_spin.valueChanged.connect(self._update_total)
        cost_spin.valueChanged.connect(self._update_total)

        hl.addWidget(name_fld, 2)
        hl.addWidget(cat_combo); hl.addWidget(info_cat)
        hl.addWidget(qty_spin); hl.addWidget(cost_spin)
        hl.addWidget(sale_spin); hl.addWidget(info_sale)
        hl.addWidget(rm_btn)
        self.item_rows.append(entry)
        self.items_layout.addWidget(row_w)

        def _remove(checked=False, e=entry):
            if len(self.item_rows) > 1:
                if e in self.item_rows:
                    self.item_rows.remove(e); e['widget'].deleteLater(); self._update_total()
        rm_btn.clicked.connect(_remove)

    def _update_total(self):
        total = sum(e['qty'].value() * e['cost'].value() for e in self.item_rows)
        self.total_lbl.setText(f"Total: {total:.2f} EGP")

    def _on_inv_select(self):
        row = self.inv_tbl.currentRow()
        if row < 0 or row >= len(self._inv_ids):
            self.detail_card.hide(); return
        iid = self._inv_ids[row]
        sup  = self.inv_tbl.item(row, 1).text()
        date = self.inv_tbl.item(row, 2).text()
        tot  = self.inv_tbl.item(row, 3).text()
        stat = self.inv_tbl.item(row, 4).text()
        self.detail_title.setText(f"Invoice #{row+1}  —  {sup}")
        self.detail_info.setText(f"Date: {date}   Total: {tot} EGP   Status: {stat}")
        items = PurchaseInvoiceManager.get_invoice_items(iid)
        self.detail_tbl.setRowCount(len(items))
        for i, (name, qty, cost, total) in enumerate(items):
            set_row(self.detail_tbl, i, [name, qty, f"{cost:.2f}", f"{total:.2f}"])
        self.detail_card.show()

    def refresh(self):
        total_val = InventoryManager.get_total_inventory_value()
        self.inv_val_lbl.setText(f"Total Inventory Value: {total_val:,.2f} EGP")
        
        sups = PurchaseInvoiceManager.get_suppliers()
        self.sup_combo.clear()
        for s in sups: self.sup_combo.addItem(s[1])

        invs = PurchaseInvoiceManager.get_all_invoices()
        self._inv_ids = [inv[0] for inv in invs]
        self.inv_tbl.setRowCount(len(invs))
        for i, inv in enumerate(invs):
            set_row(self.inv_tbl, i, [f"#{i+1}", inv[1], inv[2], f"{inv[3]:.2f}", inv[4]])
            si = self.inv_tbl.item(i, 4)
            if si: si.setForeground(QColor("#3ecf8e") if inv[4] == "Paid" else QColor("#ffa726"))
        self.detail_card.hide()

    def handle_save(self):
        sup = self.sup_combo.currentText().strip()
        if not sup: return QMessageBox.warning(self.page, "Error", "Select a supplier.")
        errors = []; items = []
        for e in self.item_rows:
            name = e['name_fld'].text().strip()
            qty  = e['qty'].value()
            cost = e['cost'].value()
            if not name: continue

            prod_check = InventoryManager.get_product_by_name(name)
            if prod_check:
                e['is_new'] = False
                e['prod_data'] = prod_check

            item = {'name': name, 'qty': qty, 'unit_cost': cost}
            if e['is_new']:
                sale = e['sale'].value()
                if sale <= 0: errors.append(f"Enter selling price for new product '{name}'."); continue
                if sale < cost: errors.append(f"Selling price for '{name}' ({sale}) cannot be less than purchase cost ({cost})."); continue
                item['selling_price'] = sale
                item['category']      = e['cat_combo'].currentText()
            else:
                existing_sale = e['prod_data'][4]
                if existing_sale < cost:
                    errors.append(f"Cost ({cost}) for '{name}' exceeds its current selling price ({existing_sale}). Update its price in Inventory first.")
                    continue
            items.append(item)
        if errors:    return QMessageBox.warning(self.page, "Validation Error", "\n".join(errors))
        if not items: return QMessageBox.warning(self.page, "Error", "Add at least one product.")
        ok, msg = PurchaseInvoiceManager.create_invoice(sup, items, paid=self.paid_check.isChecked())
        if ok:
            QMessageBox.information(self.page, "✅", msg)
            for e in self.item_rows: e['widget'].deleteLater()
            self.item_rows.clear()
            self._add_item_row()
            self._update_total()
            self.refresh()
            if self._refresh_cb: self._refresh_cb()
        else:
            QMessageBox.warning(self.page, "Error", msg)

    def handle_delete(self):
        row = self.inv_tbl.currentRow()
        if row < 0 or row >= len(self._inv_ids):
            return QMessageBox.warning(self.page, "Error", "Select an invoice.")
        iid = self._inv_ids[row]
        reply = QMessageBox.question(self.page, "Confirm", f"Delete invoice #{row+1}?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            PurchaseInvoiceManager.delete_invoice(iid); self.refresh()

    def handle_paid(self):
        row = self.inv_tbl.currentRow()
        if row < 0 or row >= len(self._inv_ids):
            return QMessageBox.warning(self.page, "Error", "Select an invoice.")
        iid = self._inv_ids[row]
        PurchaseInvoiceManager.mark_paid(iid); self.refresh()

    def handle_pdf(self):
        row = self.inv_tbl.currentRow()
        if row < 0 or row >= len(self._inv_ids):
            return QMessageBox.warning(self.page, "Error", "Select an invoice.")
        iid = self._inv_ids[row]
        ok, result = PDFGenerator.generate_purchase_invoice(iid)
        if ok:
            QMessageBox.information(self.page, "✅ PDF", f"Invoice saved:\n{result}")
            os.startfile(result)
        else:
            QMessageBox.warning(self.page, "Error", result)


# ═══════════════════════════════════════════════════════════════
#  ACCOUNTING PAGE
# ═══════════════════════════════════════════════════════════════
class AccountingPage:
    def __init__(self):
        self.page = QWidget(); self.page.setObjectName("root")
        main_lay = QVBoxLayout(self.page)
        main_lay.setContentsMargins(30, 24, 30, 24); main_lay.setSpacing(16)
        h = QHBoxLayout()
        t = QLabel("Accounting"); t.setObjectName("title"); h.addWidget(t)
        h.addStretch()
        main_lay.addLayout(h)
        main_lay.addWidget(make_divider())

        self.tabs = QTabWidget()
        main_lay.addWidget(self.tabs)

        # ── Tab 1: Journal Entries ─────────────────────────────────────────
        self.je_tab = QWidget()
        jl = QVBoxLayout(self.je_tab); jl.setContentsMargins(16,16,16,16)
        jl.addWidget(QLabel("📒  Journal Entries", objectName="sec_title"))
        self.je_tbl = make_table(["#","Date","Description","Entity","Reference","Total Debit"])
        self.je_tbl.setMaximumHeight(180)
        self.je_tbl.itemSelectionChanged.connect(self._on_je_select)
        jl.addWidget(self.je_tbl)

        jl.addWidget(QLabel("📝  Entry Detail Lines (select entry above)", objectName="sec_title"))
        self.je_detail_tbl = make_table(["Account","Debit","Credit"])
        self.je_detail_tbl.setMaximumHeight(120)
        jl.addWidget(self.je_detail_tbl)

        jl.addWidget(make_divider())
        jl.addWidget(QLabel("➕  New Journal Entry", objectName="sec_title"))
        f = QFormLayout(); f.setSpacing(8)
        self.je_desc   = QLineEdit(); self.je_desc.setPlaceholderText("Description...")
        self.je_entity = QLineEdit(); self.je_entity.setPlaceholderText("Entity (customer/supplier name)...")
        self.je_ref    = QLineEdit(); self.je_ref.setPlaceholderText("Reference (invoice#, etc.)...")
        self.je_acc1   = QComboBox()
        self.je_dr     = QDoubleSpinBox(); self.je_dr.setMaximum(999999); self.je_dr.setPrefix("DR ")
        self.je_acc2   = QComboBox()
        self.je_cr     = QDoubleSpinBox(); self.je_cr.setMaximum(999999); self.je_cr.setPrefix("CR ")
        f.addRow("Description:",   self.je_desc)
        f.addRow("Entity:",        self.je_entity)
        f.addRow("Reference:",     self.je_ref)
        f.addRow("Debit Account:", self.je_acc1)
        f.addRow("Debit Amount:",  self.je_dr)
        f.addRow("Credit Account:",self.je_acc2)
        f.addRow("Credit Amount:", self.je_cr)
        jl.addLayout(f)
        btn_row = QHBoxLayout()
        btn = QPushButton("💾 Save Entry"); btn.setObjectName("primary")
        btn.setCursor(Qt.PointingHandCursor); btn.clicked.connect(self.handle_add_je)
        add_acc_btn = QPushButton("➕ Add Account"); add_acc_btn.setObjectName("secondary")
        add_acc_btn.setCursor(Qt.PointingHandCursor); add_acc_btn.clicked.connect(self.handle_add_account)
        btn_row.addWidget(btn); btn_row.addStretch(); btn_row.addWidget(add_acc_btn)
        jl.addLayout(btn_row)
        self.tabs.addTab(self.je_tab, "📒 Journal Entries")

        # ── Tab 2: General Ledger ──────────────────────────────────────────
        self.gl_tab = QWidget()
        gl = QVBoxLayout(self.gl_tab); gl.setContentsMargins(16,16,16,16)
        gl.addWidget(QLabel("📖  General Ledger", objectName="sec_title"))

        # Filter bar
        filter_row = QHBoxLayout(); filter_row.setSpacing(8)
        filter_lbl = QLabel("Filter:")
        filter_lbl.setStyleSheet("color:#6a7a9a; font-size:12px; font-weight:600;")
        filter_row.addWidget(filter_lbl)

        self._gl_filter = "All"
        self._gl_data   = []

        FILTER_OPTIONS = [
            ("All",                 "🔘 All Accounts"),
            ("Accounts Payable",    "📤 Accounts Payable"),
            ("Accounts Receivable", "📥 Accounts Receivable"),
            ("Sales Revenue",       "💰 Sales Revenue"),
            ("Inventory",           "📦 Inventory"),
        ]
        self._gl_filter_btns = {}
        for key, label in FILTER_OPTIONS:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setChecked(key == "All")
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: #7c5cbf;
                    border: 1px solid #7c5cbf;
                    border-radius: 8px;
                    padding: 5px 14px;
                    font-size: 12px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background: #7c5cbf;
                    color: white;
                }
                QPushButton:checked {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #7c5cbf, stop:1 #9b7ae0);
                    color: white;
                    border: none;
                }
            """)
            btn.clicked.connect(lambda checked, k=key: self._apply_gl_filter(k))
            self._gl_filter_btns[key] = btn
            filter_row.addWidget(btn)

        filter_row.addStretch()
        gl.addLayout(filter_row)

        self.gl_tbl = make_table(["Entry#","Account","Date","Description","Entity","Debit","Credit","Reference"])
        gl.addWidget(self.gl_tbl)
        self.tabs.addTab(self.gl_tab, "📖 General Ledger")

        # ── Tab 3: Income Statement ────────────────────────────────────────
        self.is_tab = QWidget()
        il = QVBoxLayout(self.is_tab); il.setContentsMargins(16,16,16,16)
        il.addWidget(QLabel("💰  Income Statement", objectName="sec_title"))
        sr = QHBoxLayout(); sr.setSpacing(14)
        self.is_rev = StatCard("💰","Total Revenue","0 EGP","#3ecf8e")
        self.is_exp = StatCard("💸","Total Expenses","0 EGP","#f06292")
        self.is_net = StatCard("📈","Net Income","0 EGP","#5c9cf5")
        sr.addWidget(self.is_rev); sr.addWidget(self.is_exp); sr.addWidget(self.is_net)
        il.addLayout(sr)
        is_cols = QHBoxLayout(); is_cols.setSpacing(14)
        rev_w = QWidget(); rev_w.setObjectName("card")
        rv = QVBoxLayout(rev_w); rv.setContentsMargins(10,8,10,8)
        rv.addWidget(QLabel("🟢  Revenues", objectName="sec_title"))
        self.is_rev_tbl = make_table(["Account","Amount (EGP)"])
        rv.addWidget(self.is_rev_tbl)
        self.is_rev_total = QLabel("Total: 0.00")
        self.is_rev_total.setStyleSheet("font-weight:700;color:#3ecf8e;")
        rv.addWidget(self.is_rev_total)
        is_cols.addWidget(rev_w)
        exp_w = QWidget(); exp_w.setObjectName("card")
        ev = QVBoxLayout(exp_w); ev.setContentsMargins(10,8,10,8)
        ev.addWidget(QLabel("🔴  Expenses", objectName="sec_title"))
        self.is_exp_tbl = make_table(["Account","Amount (EGP)"])
        ev.addWidget(self.is_exp_tbl)
        self.is_exp_total = QLabel("Total: 0.00")
        self.is_exp_total.setStyleSheet("font-weight:700;color:#f06292;")
        ev.addWidget(self.is_exp_total)
        is_cols.addWidget(exp_w)
        il.addLayout(is_cols)
        self.is_net_lbl = QLabel(""); self.is_net_lbl.setAlignment(Qt.AlignCenter)
        self.is_net_lbl.setStyleSheet("font-size:15px;font-weight:800;padding:6px;")
        il.addWidget(self.is_net_lbl)
        self.tabs.addTab(self.is_tab, "💰 Income Statement")

        # ── Tab 4: Balance Sheet ───────────────────────────────────────────
        self.bs_tab = QWidget()
        bl = QVBoxLayout(self.bs_tab); bl.setContentsMargins(16,16,16,16)
        bl.addWidget(QLabel("📊  Balance Sheet", objectName="sec_title"))
        sr2 = QHBoxLayout(); sr2.setSpacing(14)
        self.bs_asset = StatCard("🏦","Total Assets","0 EGP","#3ecf8e")
        self.bs_liab  = StatCard("📋","Total Liabilities","0 EGP","#f06292")
        self.bs_eq    = StatCard("💎","Total Equity","0 EGP","#5c9cf5")
        sr2.addWidget(self.bs_asset); sr2.addWidget(self.bs_liab); sr2.addWidget(self.bs_eq)
        bl.addLayout(sr2)
        bs_cols = QHBoxLayout(); bs_cols.setSpacing(14)
        a_w = QWidget(); a_w.setObjectName("card")
        av = QVBoxLayout(a_w); av.setContentsMargins(10,8,10,8)
        av.addWidget(QLabel("🟢  Assets", objectName="sec_title"))
        self.bs_a_tbl = make_table(["Account","Balance (EGP)"])
        av.addWidget(self.bs_a_tbl)
        self.bs_a_total = QLabel("Total: 0.00")
        self.bs_a_total.setStyleSheet("font-weight:700;color:#3ecf8e;")
        av.addWidget(self.bs_a_total)
        bs_cols.addWidget(a_w)
        le_w = QWidget(); le_w.setObjectName("card")
        lv = QVBoxLayout(le_w); lv.setContentsMargins(10,8,10,8)
        
        lv.addWidget(QLabel("💎  Equity", objectName="sec_title"))
        self.bs_e_tbl = make_table(["Account","Balance (EGP)"])
        lv.addWidget(self.bs_e_tbl)
        self.bs_e_total = QLabel("Total: 0.00")
        self.bs_e_total.setStyleSheet("font-weight:700;color:#5c9cf5;")
        lv.addWidget(self.bs_e_total)
        
        lv.addWidget(make_divider())
        
        lv.addWidget(QLabel("🔴  Liabilities", objectName="sec_title"))
        self.bs_l_tbl = make_table(["Account","Balance (EGP)"])
        lv.addWidget(self.bs_l_tbl)
        self.bs_l_total = QLabel("Total: 0.00")
        self.bs_l_total.setStyleSheet("font-weight:700;color:#f06292;")
        lv.addWidget(self.bs_l_total)
        
        bs_cols.addWidget(le_w)
        bl.addLayout(bs_cols)
        self.tabs.addTab(self.bs_tab, "📊 Balance Sheet")

        # ── Tab 5: Trial Balance ───────────────────────────────────────────
        self.tb_tab = QWidget()
        tl = QVBoxLayout(self.tb_tab); tl.setContentsMargins(16,16,16,16)
        tl.addWidget(QLabel("⚖️  Trial Balance", objectName="sec_title"))
        self.tb_tbl = make_table(["Account","Total Debit","Total Credit"])
        tl.addWidget(self.tb_tbl)
        sr3 = QHBoxLayout()
        self.tb_dr_lbl = QLabel("Total Debit: 0.00")
        self.tb_dr_lbl.setStyleSheet("font-size:14px; font-weight:700; color:#3ecf8e;")
        self.tb_cr_lbl = QLabel("Total Credit: 0.00")
        self.tb_cr_lbl.setStyleSheet("font-size:14px; font-weight:700; color:#f06292;")
        sr3.addWidget(self.tb_dr_lbl); sr3.addStretch(); sr3.addWidget(self.tb_cr_lbl)
        tl.addLayout(sr3)
        self.tabs.addTab(self.tb_tab, "⚖️ Trial Balance")

        self._je_ids = []

    # ── GL Filter ──────────────────────────────────────────────────────────
    def _apply_gl_filter(self, key):
        """Filter the General Ledger table by account name."""
        self._gl_filter = key
        for k, btn in self._gl_filter_btns.items():
            btn.setChecked(k == key)

        rows = self._gl_data if key == "All" else [g for g in self._gl_data if g[1] == key]

        self.gl_tbl.setRowCount(len(rows))
        for i, g in enumerate(rows):
            set_row(self.gl_tbl, i, [g[0], g[1], g[2], g[3], g[4],
                                      f"{g[5]:.2f}", f"{g[6]:.2f}", g[7]])

    # ── Journal Entry Selection ────────────────────────────────────────────
    def _on_je_select(self):
        row = self.je_tbl.currentRow()
        if row < 0 or row >= len(self._je_ids):
            self.je_detail_tbl.setRowCount(0); return
        eid = self._je_ids[row]
        lines = AccountingManager.get_journal_lines(eid)
        self.je_detail_tbl.setRowCount(len(lines))
        for i, (acc, dr, cr) in enumerate(lines):
            set_row(self.je_detail_tbl, i, [acc, f"{dr:,.2f}", f"{cr:,.2f}"])

    # ── Refresh ────────────────────────────────────────────────────────────
    def refresh(self):
        accs = AccountingManager.get_accounts()
        self.je_acc1.clear(); self.je_acc2.clear()
        for a in accs:
            self.je_acc1.addItem(f"{a[0]} - {a[1]}", a[1])
            self.je_acc2.addItem(f"{a[0]} - {a[1]}", a[1])

        # Journal entries
        jes = AccountingManager.get_journal_entries()
        self._je_ids = [j[0] for j in jes]
        self.je_tbl.setRowCount(len(jes))
        for i, j in enumerate(jes):
            set_row(self.je_tbl, i, [i+1, j[1], j[2], j[4], j[3], f"{j[5]:.2f}"])
        self.je_detail_tbl.setRowCount(0)

        # General ledger — store data then apply current filter
        self._gl_data = AccountingManager.get_general_ledger()
        self._apply_gl_filter(self._gl_filter)

        # Income statement
        inc = AccountingManager.get_income_statement()
        tr_val = inc['total_revenue']; te_val = inc['total_expenses']; ni = inc['net_income']
        self.is_rev.update_value(f"{tr_val:,.2f} EGP")
        self.is_exp.update_value(f"{te_val:,.2f} EGP")
        self.is_net.update_value(f"{abs(ni):,.2f} EGP", "#3ecf8e" if ni >= 0 else "#f06292")
        self.is_net.update_title("Net Profit" if ni >= 0 else "Net Loss")
        self.is_rev_tbl.setRowCount(len(inc['revenues']))
        for i, r in enumerate(inc['revenues']):
            set_row(self.is_rev_tbl, i, [r[0], f"{r[1]:,.2f}"])
        self.is_rev_total.setText(f"Total Revenue: {tr_val:,.2f} EGP")
        exp_rows = list(inc['expenses'])
        if inc['system_expenses'] > 0:
            exp_rows.append(('System Expenses (Rent/Utils)', inc['system_expenses']))
        self.is_exp_tbl.setRowCount(len(exp_rows))
        for i, e in enumerate(exp_rows):
            set_row(self.is_exp_tbl, i, [e[0], f"{e[1]:,.2f}"])
        self.is_exp_total.setText(f"Total Expenses: {te_val:,.2f} EGP")
        color = "#3ecf8e" if ni >= 0 else "#f06292"
        sign  = "Profit" if ni >= 0 else "Loss"
        self.is_net_lbl.setText(f"Net {sign}: {abs(ni):,.2f} EGP")
        self.is_net_lbl.setStyleSheet(f"font-size:15px;font-weight:800;padding:6px;color:{color};")

        # Balance sheet
        bs = AccountingManager.get_balance_sheet()
        asset_rows = list(bs.get('Asset', []))
        if bs['cash_balance'] != 0:
            asset_rows.append(('Cash & Cash Equivalents', bs['cash_balance']))
        ta = sum(a[1] for a in asset_rows)
        self.bs_asset.update_value(f"{ta:,.2f} EGP")
        self.bs_a_tbl.setRowCount(len(asset_rows))
        for i, a in enumerate(asset_rows):
            set_row(self.bs_a_tbl, i, [a[0], f"{a[1]:,.2f}"])
        self.bs_a_total.setText(f"Total Assets: {ta:,.2f} EGP")

        liab_rows = list(bs.get('Liability', []))
        unpaid_purchase = bs.get('accounts_payable', 0)
        if unpaid_purchase > 0:
            liab_rows.append(('Accounts Payable', unpaid_purchase))
        tl_val = sum(abs(l[1]) for l in liab_rows)
        self.bs_liab.update_value(f"{tl_val:,.2f} EGP")
        self.bs_l_tbl.setRowCount(len(liab_rows))
        for i, l in enumerate(liab_rows):
            set_row(self.bs_l_tbl, i, [l[0], f"{abs(l[1]):,.2f}"])
        self.bs_l_total.setText(f"Total Liabilities: {tl_val:,.2f} EGP")

        eq_rows = list(bs.get('Equity', []))
        eq_rows.append(('Current Year Net Income', ni))
        te = sum(e[1] for e in eq_rows)
        self.bs_eq.update_value(f"{te:,.2f} EGP")
        self.bs_e_tbl.setRowCount(len(eq_rows))
        for i, e in enumerate(eq_rows):
            set_row(self.bs_e_tbl, i, [e[0], f"{e[1]:,.2f}"])
        self.bs_e_total.setText(f"Total Equity: {te:,.2f} EGP")

        # Trial balance
        tb = AccountingManager.get_trial_balance()
        self.tb_tbl.setRowCount(len(tb))
        td, tc = 0, 0
        for i, t in enumerate(tb):
            set_row(self.tb_tbl, i, [t[0], f"{t[1]:,.2f}", f"{t[2]:,.2f}"])
            td += t[1]; tc += t[2]
        self.tb_dr_lbl.setText(f"Total Debit: {td:,.2f}")
        self.tb_cr_lbl.setText(f"Total Credit: {tc:,.2f}")

    # ── Add Journal Entry ──────────────────────────────────────────────────
    def handle_add_je(self):
        desc = self.je_desc.text().strip()
        if not desc: return QMessageBox.warning(self.page, "Error", "Enter description.")
        dr_acc = self.je_acc1.currentData()
        cr_acc = self.je_acc2.currentData()
        dr_amt = self.je_dr.value()
        cr_amt = self.je_cr.value()
        if dr_amt <= 0 or cr_amt <= 0:
            return QMessageBox.warning(self.page, "Error", "Enter valid amounts.")
        if dr_amt != cr_amt:
            return QMessageBox.warning(self.page, "Error", "Total Debit must equal Total Credit.")
        lines = [(dr_acc, dr_amt, 0), (cr_acc, 0, cr_amt)]
        entity = self.je_entity.text().strip()
        ok, msg = AccountingManager.create_journal_entry(desc, lines, self.je_ref.text(), entity)
        if ok:
            QMessageBox.information(self.page, "✅", msg)
            self.je_desc.clear(); self.je_entity.clear(); self.je_ref.clear()
            self.je_dr.setValue(0); self.je_cr.setValue(0)
            self.refresh()

    # ── Add New Account ────────────────────────────────────────────────────
    def handle_add_account(self):
        from PyQt5.QtWidgets import QDialog, QFormLayout, QLineEdit, QComboBox, QDialogButtonBox
        dlg = QDialog(self.page)
        dlg.setWindowTitle("Add New Account")
        dlg.setMinimumWidth(300)
        lay = QFormLayout(dlg)
        
        name_edit = QLineEdit()
        type_combo = QComboBox()
        type_combo.addItems(["Asset", "Liability", "Equity", "Revenue", "Expense"])
        
        lay.addRow("Account Name:", name_edit)
        lay.addRow("Account Type:", type_combo)
        
        bbox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bbox.accepted.connect(dlg.accept)
        bbox.rejected.connect(dlg.reject)
        lay.addRow(bbox)
        
        if dlg.exec_() == QDialog.Accepted:
            name = name_edit.text().strip()
            atype = type_combo.currentText()
            if not name:
                return QMessageBox.warning(self.page, "Error", "Account name cannot be empty.")
                
            ok, msg = AccountingManager.add_account(name, atype)
            if ok:
                QMessageBox.information(self.page, "✅ Success", msg)
                self.refresh()
            else:
                QMessageBox.warning(self.page, "Error", msg)


# ═══════════════════════════════════════════════════════════════
#  ACCOUNT STATEMENT PAGE
# ═══════════════════════════════════════════════════════════════
class AccountStatementPage:
    def __init__(self):
        self.page = QWidget(); self.page.setObjectName("root")
        main_lay = QVBoxLayout(self.page)
        main_lay.setContentsMargins(30, 24, 30, 24); main_lay.setSpacing(16)
        h = QHBoxLayout()
        t = QLabel("Account Statements"); t.setObjectName("title"); h.addWidget(t)
        h.addStretch()
        main_lay.addLayout(h)
        main_lay.addWidget(make_divider())

        self.tabs = QTabWidget()
        main_lay.addWidget(self.tabs)

        # Tab 1: Customer Statement
        self.cs_tab = QWidget()
        cl = QVBoxLayout(self.cs_tab); cl.setContentsMargins(16,16,16,16)
        fr = QHBoxLayout()
        fr.addWidget(QLabel("👤 Customer:"))
        self.cs_combo = QComboBox(); self.cs_combo.setMinimumWidth(200)
        self.cs_combo.currentIndexChanged.connect(self._load_customer)
        fr.addWidget(self.cs_combo); fr.addStretch()
        cl.addLayout(fr)

        sr = QHBoxLayout(); sr.setSpacing(14)
        self.cs_total = StatCard("💰","Total","0 EGP","#5c9cf5")
        self.cs_paid  = StatCard("✅","Paid","0 EGP","#3ecf8e")
        self.cs_out   = StatCard("⏳","Outstanding","0 EGP","#ffa726")
        sr.addWidget(self.cs_total); sr.addWidget(self.cs_paid); sr.addWidget(self.cs_out)
        cl.addLayout(sr)

        self.cs_tbl = make_table(["#","Customer","Date","Amount","Status"])
        cl.addWidget(self.cs_tbl)
        self.tabs.addTab(self.cs_tab, "👤 Customer Statement")

        # Tab 2: Supplier Statement
        self.ss_tab = QWidget()
        sl = QVBoxLayout(self.ss_tab); sl.setContentsMargins(16,16,16,16)
        fr2 = QHBoxLayout()
        fr2.addWidget(QLabel("🏭 Supplier:"))
        self.ss_combo = QComboBox(); self.ss_combo.setMinimumWidth(200)
        self.ss_combo.currentIndexChanged.connect(self._load_supplier)
        fr2.addWidget(self.ss_combo); fr2.addStretch()
        sl.addLayout(fr2)

        sr2 = QHBoxLayout(); sr2.setSpacing(14)
        self.ss_total = StatCard("💰","Total","0 EGP","#5c9cf5")
        self.ss_paid  = StatCard("✅","Paid","0 EGP","#3ecf8e")
        self.ss_out   = StatCard("⏳","Outstanding","0 EGP","#ffa726")
        sr2.addWidget(self.ss_total); sr2.addWidget(self.ss_paid); sr2.addWidget(self.ss_out)
        sl.addLayout(sr2)

        self.ss_tbl = make_table(["#","Supplier","Date","Amount","Status"])
        sl.addWidget(self.ss_tbl)
        self.tabs.addTab(self.ss_tab, "🏭 Supplier Statement")

    def refresh(self):
        self.cs_combo.blockSignals(True)
        self.ss_combo.blockSignals(True)
        self.cs_combo.clear(); self.ss_combo.clear()
        self.cs_combo.addItem("All Customers")
        for n in AccountStatementManager.get_all_customer_names():
            self.cs_combo.addItem(n)
        self.ss_combo.addItem("All Suppliers")
        for n in AccountStatementManager.get_all_supplier_names():
            self.ss_combo.addItem(n)
        self.cs_combo.blockSignals(False)
        self.ss_combo.blockSignals(False)
        self._load_customer()
        self._load_supplier()

    def _load_customer(self):
        name = self.cs_combo.currentText()
        if name == "All Customers" or not name:
            rows = AccountStatementManager.get_customer_statement()
            bal  = AccountStatementManager.get_all_customer_balance()
        else:
            rows = AccountStatementManager.get_customer_statement(name)
            bal  = AccountStatementManager.get_customer_balance(name)
        self.cs_total.update_value(f"{bal['total']:,.2f} EGP")
        self.cs_paid.update_value(f"{bal['paid']:,.2f} EGP")
        self.cs_out.update_value(f"{bal['outstanding']:,.2f} EGP")
        self.cs_tbl.setRowCount(len(rows))
        for i, r in enumerate(rows):
            set_row(self.cs_tbl, i, [i+1, r[1], r[2], f"{r[3]:,.2f}", r[4]])
            si = self.cs_tbl.item(i, 4)
            if si: si.setForeground(QColor("#3ecf8e") if r[4]=="Paid" else QColor("#ffa726"))

    def _load_supplier(self):
        name = self.ss_combo.currentText()
        if name == "All Suppliers" or not name:
            rows = AccountStatementManager.get_supplier_statement()
            bal  = AccountStatementManager.get_all_supplier_balance()
        else:
            rows = AccountStatementManager.get_supplier_statement(name)
            bal  = AccountStatementManager.get_supplier_balance(name)
        self.ss_total.update_value(f"{bal['total']:,.2f} EGP")
        self.ss_paid.update_value(f"{bal['paid']:,.2f} EGP")
        self.ss_out.update_value(f"{bal['outstanding']:,.2f} EGP")
        self.ss_tbl.setRowCount(len(rows))
        for i, r in enumerate(rows):
            set_row(self.ss_tbl, i, [i+1, r[1], r[2], f"{r[3]:,.2f}", r[4]])
            si = self.ss_tbl.item(i, 4)
            if si: si.setForeground(QColor("#3ecf8e") if r[4]=="Paid" else QColor("#ffa726"))


# ═══════════════════════════════════════════════════════════════
#  LOYALTY PAGE
# ═══════════════════════════════════════════════════════════════
class LoyaltyPage:
    TIER_COLORS = {'Bronze': '#cd7f32', 'Silver': '#a8a9ad', 'Gold': '#ffd700', 'Platinum': '#b9f2ff'}
    TIER_ICONS  = {'Bronze': '🥉', 'Silver': '🥈', 'Gold': '🥇', 'Platinum': '💎'}

    def __init__(self):
        self.page, lay = page_container("🎯  Loyalty Program", "Points & Rewards")
        grid = QHBoxLayout(); grid.setSpacing(20)

        left = QWidget(); left.setObjectName("card")
        ll = QVBoxLayout(left); ll.setContentsMargins(16, 16, 16, 16)
        ll.addWidget(QLabel("🏆  Leaderboard", objectName="sec_title"))
        self.tbl = make_table(["#", "Customer", "Points", "Tier", "Total Spent"])
        ll.addWidget(self.tbl)
        grid.addWidget(left, 3)

        right = QWidget(); right.setObjectName("card")
        rl = QVBoxLayout(right); rl.setContentsMargins(16, 16, 16, 16); rl.setSpacing(12)
        rl.addWidget(QLabel("🔍  Customer Lookup", objectName="sec_title"))

        self.search = QLineEdit(); self.search.setPlaceholderText("Customer name...")
        self.search.returnPressed.connect(self._lookup)
        rl.addWidget(self.search)
        srch_btn = QPushButton("🔍  Look Up"); srch_btn.setObjectName("primary")
        srch_btn.setCursor(Qt.PointingHandCursor); srch_btn.clicked.connect(self._lookup)
        rl.addWidget(srch_btn)

        rl.addWidget(make_divider())

        self.cust_name_lbl = QLabel("—"); self.cust_name_lbl.setStyleSheet("font-size:16px; font-weight:700;")
        self.tier_lbl  = QLabel("—"); self.tier_lbl.setStyleSheet("font-size:13px;")
        self.pts_lbl   = QLabel("Points: —"); self.pts_lbl.setStyleSheet("font-size:13px;")
        self.spent_lbl = QLabel("Spent: —"); self.spent_lbl.setStyleSheet("font-size:11px; color:#6b7a99;")
        self.progress  = QProgressBar()
        self.progress.setMaximumHeight(8)
        self.progress.setTextVisible(False)
        self.progress.setStyleSheet("QProgressBar{border:none; border-radius:4px; background:#252840;}"
                                    "QProgressBar::chunk{background:#7c5cbf; border-radius:4px;}")
        self.next_lbl = QLabel("")
        self.next_lbl.setStyleSheet("font-size:10px; color:#6b7a99;")
        rl.addWidget(self.cust_name_lbl)
        rl.addWidget(self.tier_lbl)
        rl.addWidget(self.pts_lbl)
        rl.addWidget(self.spent_lbl)
        rl.addWidget(self.progress)
        rl.addWidget(self.next_lbl)

        rl.addWidget(make_divider())
        rl.addWidget(QLabel("🎁  Redeem Points", objectName="sec_title"))
        f = QFormLayout(); f.setSpacing(8)
        self.redeem_pts = QSpinBox(); self.redeem_pts.setMaximum(999999)
        f.addRow("Points to Redeem:", self.redeem_pts)
        rl.addLayout(f)
        self.redeem_info = QLabel("100 pts = 1.00 EGP discount")
        self.redeem_info.setStyleSheet("font-size:10px; color:#6b7a99;")
        rl.addWidget(self.redeem_info)
        rdm_btn = QPushButton("💳  Redeem"); rdm_btn.setObjectName("primary")
        rdm_btn.setCursor(Qt.PointingHandCursor); rdm_btn.clicked.connect(self._redeem)
        rl.addWidget(rdm_btn)
        rl.addStretch()
        grid.addWidget(right, 2)
        lay.addLayout(grid)

        tg_row = QHBoxLayout(); tg_row.setSpacing(12)
        for name, pts, disc in LoyaltyManager.TIERS:
            c  = self.TIER_COLORS[name]
            ic = self.TIER_ICONS[name]
            card = QWidget(); card.setObjectName("card")
            card.setStyleSheet(f"background:#161929; border:2px solid {c}; border-radius:10px;")
            cl = QVBoxLayout(card); cl.setContentsMargins(10, 8, 10, 8); cl.setAlignment(Qt.AlignCenter)
            cl.addWidget(QLabel(ic, alignment=Qt.AlignCenter))
            cl.addWidget(QLabel(name, alignment=Qt.AlignCenter,
                                styleSheet=f"font-weight:700; color:{c}; font-size:12px;"))
            cl.addWidget(QLabel(f"{pts:,}+ pts", alignment=Qt.AlignCenter,
                                styleSheet="font-size:10px; color:#6b7a99;"))
            cl.addWidget(QLabel(f"{disc}% off", alignment=Qt.AlignCenter,
                                styleSheet=f"font-size:11px; color:{c}; font-weight:600;"))
            tg_row.addWidget(card)
        lay.addLayout(tg_row)

        self._cur_customer = None

    def refresh(self):
        rows = LoyaltyManager.get_all_accounts()
        self.tbl.setRowCount(len(rows))
        for i, (name, pts, tier, spent) in enumerate(rows):
            c  = self.TIER_COLORS.get(tier, '#ffffff')
            ic = self.TIER_ICONS.get(tier, '')
            set_row(self.tbl, i, [i+1, name, f"{pts:,}", f"{ic} {tier}", f"{spent:,.2f} EGP"])
            ti = self.tbl.item(i, 3)
            if ti: ti.setForeground(QColor(c))

    def _lookup(self):
        name = self.search.text().strip()
        if not name:
            return QMessageBox.warning(self.page, "Error", "Enter a customer name.")
        acc = LoyaltyManager.get_account(name)
        if not acc:
            self.cust_name_lbl.setText(f"{name} (new)")
            self.tier_lbl.setText("🥉 Bronze")
            self.pts_lbl.setText("Points: 0")
            self.spent_lbl.setText("Spent: 0.00 EGP")
            self.progress.setValue(0)
            self.next_lbl.setText("1,000 pts to Silver")
            self._cur_customer = name
            return
        cname, pts, tier, spent = acc
        self._cur_customer = cname
        _, _, next_tier, pts_next = LoyaltyManager.get_tier_info(pts)
        color = self.TIER_COLORS.get(tier, '#7c5cbf')
        icon  = self.TIER_ICONS.get(tier, '')
        self.cust_name_lbl.setText(cname)
        self.cust_name_lbl.setStyleSheet(f"font-size:16px; font-weight:700; color:{color};")
        self.tier_lbl.setText(f"{icon} {tier}")
        self.tier_lbl.setStyleSheet(f"font-size:13px; color:{color};")
        self.pts_lbl.setText(f"Points: {pts:,}")
        self.spent_lbl.setText(f"Total Spent: {spent:,.2f} EGP")
        if next_tier:
            next_threshold = next((t for _, t, _ in LoyaltyManager.TIERS if _ and t > pts), pts)
            prev_threshold = pts - pts_next if pts_next > 0 else pts
            total_range = max(next_threshold - prev_threshold, 1)
            pct = min(int(((pts - prev_threshold) / total_range) * 100), 100)
            self.progress.setValue(pct)
            self.next_lbl.setText(f"{pts_next:,} pts to {next_tier}")
        else:
            self.progress.setValue(100)
            self.next_lbl.setText("✨ Platinum — Max Tier!")
        rate = int(SettingsManager.get('loyalty_redeem_rate', '100') or 100)
        self.redeem_info.setText(f"{rate} pts = 1.00 EGP discount")

    def _redeem(self):
        if not self._cur_customer:
            return QMessageBox.warning(self.page, "Error", "Look up a customer first.")
        pts = self.redeem_pts.value()
        if pts <= 0:
            return QMessageBox.warning(self.page, "Error", "Enter points to redeem.")
        ok, result = LoyaltyManager.redeem_points(self._cur_customer, pts)
        if ok:
            QMessageBox.information(self.page, "✅ Redeemed",
                f"{pts:,} points redeemed → {result:.2f} EGP discount for {self._cur_customer}")
            self._lookup()
            self.refresh()
        else:
            QMessageBox.warning(self.page, "Error", str(result))


# ═══════════════════════════════════════════════════════════════
#  SETTINGS PAGE
# ═══════════════════════════════════════════════════════════════
class SettingsPage:
    def __init__(self):
        self.page, lay = page_container("⚙️  Settings", "System Configuration")
        grid = QHBoxLayout(); grid.setSpacing(20)

        left = QWidget(); left.setObjectName("card")
        ll = QVBoxLayout(left); ll.setContentsMargins(16, 16, 16, 16); ll.setSpacing(12)
        ll.addWidget(QLabel("🔔  Notification Thresholds", objectName="sec_title"))

        f = QFormLayout(); f.setSpacing(10)
        self.rev_target  = QDoubleSpinBox(); self.rev_target.setMaximum(999999); self.rev_target.setPrefix("EGP ")
        self.low_stock_t = QSpinBox(); self.low_stock_t.setMaximum(999)
        self.sess_hrs    = QDoubleSpinBox(); self.sess_hrs.setMaximum(24); self.sess_hrs.setSuffix(" hrs")
        self.unpaid_cnt  = QSpinBox(); self.unpaid_cnt.setMaximum(999)
        f.addRow("Daily Revenue Target:", self.rev_target)
        f.addRow("Low Stock Threshold:",  self.low_stock_t)
        f.addRow("Session Alert (hrs):",  self.sess_hrs)
        f.addRow("Unpaid Invoice Alert:", self.unpaid_cnt)
        ll.addLayout(f)

        ll.addWidget(make_divider())
        ll.addWidget(QLabel("🎯  Loyalty Settings", objectName="sec_title"))
        f2 = QFormLayout(); f2.setSpacing(10)
        self.pts_rate    = QSpinBox(); self.pts_rate.setMinimum(1); self.pts_rate.setMaximum(100)
        self.pts_rate.setSuffix(" pts / EGP")
        self.redeem_rate = QSpinBox(); self.redeem_rate.setMinimum(1); self.redeem_rate.setMaximum(1000)
        self.redeem_rate.setSuffix(" pts = 1 EGP")
        f2.addRow("Points Earn Rate:", self.pts_rate)
        f2.addRow("Redeem Rate:",      self.redeem_rate)
        ll.addLayout(f2)

        save_btn = QPushButton("💾  Save Settings"); save_btn.setObjectName("primary")
        save_btn.setCursor(Qt.PointingHandCursor); save_btn.clicked.connect(self.handle_save)
        ll.addWidget(save_btn)
        ll.addStretch()
        grid.addWidget(left, 2)

        right = QWidget(); right.setObjectName("card")
        rl = QVBoxLayout(right); rl.setContentsMargins(16, 16, 16, 16); rl.setSpacing(12)
        rl.addWidget(QLabel("ℹ️  About AIS Hub", objectName="sec_title"))
        for line in [
            ("📦", "Version",    "3.0.0"),
            ("🐍", "Python",     "3.12+"),
            ("🖼️", "Framework",  "PyQt5"),
            ("🗄️", "Database",   "SQLite 3"),
            ("📄", "PDF Engine", "fpdf2"),
            ("🏢", "System",     "AIS Hub Co-Working Space"),
        ]:
            row = QHBoxLayout(); row.setSpacing(10)
            row.addWidget(QLabel(f"{line[0]}  {line[1]}:",
                                 styleSheet="color:#6b7a99; font-size:12px;"))
            row.addStretch()
            row.addWidget(QLabel(line[2], styleSheet="font-weight:600; font-size:12px;"))
            rl.addLayout(row)

        rl.addWidget(make_divider())
        rl.addWidget(QLabel("⚠️  Danger Zone", objectName="sec_title"))
        
        rst_lbl = QLabel("Clears the notification dedup cache\nso alerts can show again.")
        rst_lbl.setStyleSheet("font-size:11px; color:#6b7a99;"); rst_lbl.setWordWrap(True)
        rl.addWidget(rst_lbl)
        rst_btn = QPushButton("🔄  Reset Alerts"); rst_btn.setObjectName("secondary")
        rst_btn.setCursor(Qt.PointingHandCursor)
        rst_btn.clicked.connect(lambda: (self._reset_alerts(), None))
        rl.addWidget(rst_btn)

        db_lbl = QLabel("Clears all transactional history (sessions, sales, expenses, invoices) to start a new year. Keeps master data like rooms, products, and customers.")
        db_lbl.setStyleSheet("font-size:11px; color:#f06292;"); db_lbl.setWordWrap(True)
        rl.addWidget(db_lbl)
        reset_db_btn = QPushButton("📅  Start New Financial Year"); reset_db_btn.setObjectName("danger")
        reset_db_btn.setCursor(Qt.PointingHandCursor)
        reset_db_btn.clicked.connect(self._start_new_financial_year)
        rl.addWidget(reset_db_btn)

        rl.addStretch()
        grid.addWidget(right, 2)
        lay.addLayout(grid)

    def _reset_alerts(self):
        from core import NotificationManager
        NotificationManager.reset()
        QMessageBox.information(self.page, "✅", "Alert history cleared.")

    def _start_new_financial_year(self):
        reply = QMessageBox.question(
            self.page, "⚠️ Start New Financial Year",
            "Are you sure you want to close the current financial year?\n\nThis will generate a Closing Journal Entry to zero out all Revenue and Expense accounts into Equity (Current Year Earnings).\n\nHistorical data and master data will be preserved.",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            import database
            ok, msg = database.start_new_financial_year()
            if ok:
                QMessageBox.information(self.page, "✅ Year Closed Successfully", msg)
            else:
                QMessageBox.warning(self.page, "⚠️ Notice", msg)
            if hasattr(self, '_refresh_cb') and self._refresh_cb:
                self._refresh_cb()

    def refresh(self):
        s = SettingsManager.get_all()
        try:    self.rev_target.setValue(float(s.get('daily_revenue_target', 2000)))
        except: pass
        try:    self.low_stock_t.setValue(int(s.get('low_stock_threshold', 5)))
        except: pass
        try:    self.sess_hrs.setValue(float(s.get('session_alert_hours', 5)))
        except: pass
        try:    self.unpaid_cnt.setValue(int(s.get('unpaid_invoice_alert', 3)))
        except: pass
        try:    self.pts_rate.setValue(int(s.get('loyalty_points_rate', 1)))
        except: pass
        try:    self.redeem_rate.setValue(int(s.get('loyalty_redeem_rate', 100)))
        except: pass

    def handle_save(self):
        SettingsManager.set('daily_revenue_target', self.rev_target.value())
        SettingsManager.set('low_stock_threshold',  self.low_stock_t.value())
        SettingsManager.set('session_alert_hours',  self.sess_hrs.value())
        SettingsManager.set('unpaid_invoice_alert', self.unpaid_cnt.value())
        SettingsManager.set('loyalty_points_rate',  self.pts_rate.value())
        SettingsManager.set('loyalty_redeem_rate',  self.redeem_rate.value())
        QMessageBox.information(self.page, "✅", "Settings saved successfully.")


# ═══════════════════════════════════════════════════════════════
#  BOOKING PAGE
# ═══════════════════════════════════════════════════════════════
class BookingPage:
    def __init__(self):
        self.page, lay = page_container("📅  Reservations & Bookings")
        grid = QHBoxLayout(); grid.setSpacing(20)

        left = QWidget(); left.setObjectName("card")
        ll = QVBoxLayout(left); ll.setContentsMargins(16, 16, 16, 16)
        ll.addWidget(QLabel("📋  All Bookings", objectName="sec_title"))

        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("Date:"))
        self.date_filter = QDateEdit(QDate.currentDate())
        self.date_filter.setCalendarPopup(True)
        self.date_filter.setDisplayFormat("yyyy-MM-dd")
        self.date_filter.dateChanged.connect(self.refresh)
        filter_row.addWidget(self.date_filter)
        filter_row.addStretch()
        clr_btn = QPushButton("Show All"); clr_btn.setObjectName("secondary")
        clr_btn.setCursor(Qt.PointingHandCursor)
        clr_btn.clicked.connect(lambda: (self.date_filter.setDate(QDate(2000,1,1)), self.refresh()))
        filter_row.addWidget(clr_btn)
        ll.addLayout(filter_row)

        self.book_tbl = make_table(["#","Room","Customer","Date","From","To","People","Deposit","Status"])
        ll.addWidget(self.book_tbl)

        btn_row = QHBoxLayout()
        cancel_btn = QPushButton("❌  Cancel Booking"); cancel_btn.setObjectName("danger")
        cancel_btn.setCursor(Qt.PointingHandCursor); cancel_btn.clicked.connect(self.handle_cancel)
        edit_bk_btn = QPushButton("✏️  Edit Booking"); edit_bk_btn.setObjectName("secondary")
        edit_bk_btn.setCursor(Qt.PointingHandCursor); edit_bk_btn.clicked.connect(self.handle_edit_booking)
        to_sess_btn = QPushButton("▶  Convert to Session"); to_sess_btn.setObjectName("primary")
        to_sess_btn.setCursor(Qt.PointingHandCursor); to_sess_btn.clicked.connect(self.handle_to_session)
        btn_row.addWidget(cancel_btn); btn_row.addWidget(edit_bk_btn); btn_row.addStretch(); btn_row.addWidget(to_sess_btn)
        ll.addLayout(btn_row)
        grid.addWidget(left, 3)

        right = QWidget(); right.setObjectName("card")
        rl = QVBoxLayout(right); rl.setContentsMargins(16, 16, 16, 16); rl.setSpacing(12)
        rl.addWidget(QLabel("➕  New Booking", objectName="sec_title"))

        f = QFormLayout(); f.setSpacing(10)
        self.bk_room  = QComboBox()
        self.bk_cust  = QLineEdit(); self.bk_cust.setPlaceholderText("Customer name...")
        self.bk_date  = QDateEdit(QDate.currentDate())
        self.bk_date.setCalendarPopup(True); self.bk_date.setDisplayFormat("yyyy-MM-dd")
        self.bk_start = QTimeEdit(QTime(9, 0)); self.bk_start.setDisplayFormat("HH:mm")
        self.bk_end   = QTimeEdit(QTime(11, 0)); self.bk_end.setDisplayFormat("HH:mm")
        self.bk_ppl   = QSpinBox(); self.bk_ppl.setMinimum(1); self.bk_ppl.setMaximum(50)
        self.bk_dep   = QDoubleSpinBox(); self.bk_dep.setMaximum(99999); self.bk_dep.setDecimals(2); self.bk_dep.setPrefix("EGP ")
        self.bk_notes = QLineEdit(); self.bk_notes.setPlaceholderText("Notes...")
        f.addRow("Room:",     self.bk_room)
        f.addRow("Customer:", self.bk_cust)
        f.addRow("Date:",     self.bk_date)
        f.addRow("From:",     self.bk_start)
        f.addRow("To:",       self.bk_end)
        f.addRow("People:",   self.bk_ppl)
        f.addRow("Deposit:",  self.bk_dep)
        f.addRow("Notes:",    self.bk_notes)
        rl.addLayout(f)
        book_btn = QPushButton("📅  Confirm Booking"); book_btn.setObjectName("primary")
        book_btn.setCursor(Qt.PointingHandCursor); book_btn.clicked.connect(self.handle_book)
        rl.addWidget(book_btn)
        rl.addStretch()
        grid.addWidget(right, 2)
        lay.addLayout(grid)

        self._booking_ids = []
        self._refresh_cb  = None

    def refresh(self):
        rooms = RoomManager.get_all_rooms()
        self.bk_room.clear()
        for r in rooms:
            self.bk_room.addItem(f"{r[1]}  ({r[2]})", r[0])

        date_str = self.date_filter.date().toString("yyyy-MM-dd")
        use_date = None if date_str == "2000-01-01" else date_str
        rows = BookingManager.get_bookings(date=use_date)
        self._booking_ids = [r[0] for r in rows]
        self.book_tbl.setRowCount(len(rows))
        for i, r in enumerate(rows):
            set_row(self.book_tbl, i, [i+1, r[1], r[2], r[3], r[4], r[5], r[6], f"{r[10]:.2f}", r[7]])
            si = self.book_tbl.item(i, 8)
            if si:
                c = {'Confirmed': '#3ecf8e', 'Cancelled': '#f06292', 'Completed': '#5c9cf5'}.get(r[7], '#fff')
                si.setForeground(QColor(c))

    def handle_book(self):
        rid  = self.bk_room.currentData()
        cust = self.bk_cust.text().strip()
        if not cust:
            return QMessageBox.warning(self.page, "Error", "Enter customer name.")
        date  = self.bk_date.date().toString("yyyy-MM-dd")
        start = self.bk_start.time().toString("HH:mm")
        end   = self.bk_end.time().toString("HH:mm")
        if start >= end:
            return QMessageBox.warning(self.page, "Error", "End time must be after start time.")
        from datetime import datetime as dt
        now      = dt.now()
        bk_date  = self.bk_date.date()
        today    = QDate.currentDate()
        if bk_date < today:
            return QMessageBox.warning(self.page, "Error", "Cannot book a past date.")
        if bk_date == today:
            cur_time = QTime(now.hour, now.minute)
            if self.bk_start.time() < cur_time:
                return QMessageBox.warning(self.page, "Error", "Cannot book a past time slot.")
        ok, msg = BookingManager.create_booking(rid, cust, date, start, end, self.bk_ppl.value(), self.bk_dep.value(), self.bk_notes.text())
        if ok:
            QMessageBox.information(self.page, "✅ Booked", msg)
            self.bk_cust.clear(); self.bk_notes.clear(); self.bk_dep.setValue(0); self.refresh()
        else:
            QMessageBox.warning(self.page, "Error", msg)

    def handle_cancel(self):
        row = self.book_tbl.currentRow()
        if row < 0 or row >= len(self._booking_ids):
            return QMessageBox.warning(self.page, "Error", "Select a booking.")
        bid = self._booking_ids[row]
        reply = QMessageBox.question(self.page, "Confirm", "Cancel this booking?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            BookingManager.cancel_booking(bid); self.refresh()

    def handle_to_session(self):
        row = self.book_tbl.currentRow()
        if row < 0 or row >= len(self._booking_ids):
            return QMessageBox.warning(self.page, "Error", "Select a booking.")
        bid = self._booking_ids[row]
        ok, msg = BookingManager.convert_to_session(bid)
        if ok:
            QMessageBox.information(self.page, "✅", msg)
            self.refresh()
            if self._refresh_cb: self._refresh_cb()
        else:
            QMessageBox.warning(self.page, "Error", msg)

    def handle_edit_booking(self):
        from PyQt5.QtWidgets import QDialog, QDialogButtonBox
        row = self.book_tbl.currentRow()
        if row < 0 or row >= len(self._booking_ids):
            return QMessageBox.warning(self.page, "Error", "Select a booking to edit.")
        bid = self._booking_ids[row]
        # Get current booking data from DB
        import database
        conn = database.get_connection()
        bk = conn.execute(
            "SELECT room_id, customer_name, booking_date, start_time, end_time, num_people, notes FROM bookings WHERE id=?",
            (bid,)
        ).fetchone()
        conn.close()
        if not bk:
            return QMessageBox.warning(self.page, "Error", "Booking not found.")

        dlg = QDialog(self.page)
        dlg.setWindowTitle(f"Edit Booking #{bid}")
        dlg.setMinimumWidth(340)
        fl = QFormLayout(dlg); fl.setSpacing(10); fl.setContentsMargins(16,16,16,16)

        rooms = RoomManager.get_all_rooms()
        room_cb = QComboBox()
        for r in rooms:
            room_cb.addItem(f"{r[1]}  ({r[2]})", r[0])
        idx = room_cb.findData(bk[0])
        if idx >= 0: room_cb.setCurrentIndex(idx)

        cust_e  = QLineEdit(bk[1])
        date_e  = QDateEdit(QDate.fromString(bk[2], "yyyy-MM-dd"))
        date_e.setCalendarPopup(True); date_e.setDisplayFormat("yyyy-MM-dd")
        start_e = QTimeEdit(QTime.fromString(bk[3], "HH:mm"))
        start_e.setDisplayFormat("HH:mm")
        end_e   = QTimeEdit(QTime.fromString(bk[4], "HH:mm"))
        end_e.setDisplayFormat("HH:mm")
        ppl_e   = QSpinBox(); ppl_e.setMinimum(1); ppl_e.setMaximum(50); ppl_e.setValue(bk[5])
        notes_e = QLineEdit(bk[6] or "")

        fl.addRow("Room:", room_cb)
        fl.addRow("Customer:", cust_e)
        fl.addRow("Date:", date_e)
        fl.addRow("From:", start_e)
        fl.addRow("To:", end_e)
        fl.addRow("People:", ppl_e)
        fl.addRow("Notes:", notes_e)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(dlg.accept); btns.rejected.connect(dlg.reject)
        fl.addRow(btns)

        if dlg.exec_() == QDialog.Accepted:
            conn2 = database.get_connection()
            conn2.execute(
                "UPDATE bookings SET room_id=?, customer_name=?, booking_date=?, start_time=?, end_time=?, num_people=?, notes=? WHERE id=?",
                (room_cb.currentData(), cust_e.text().strip(),
                 date_e.date().toString("yyyy-MM-dd"),
                 start_e.time().toString("HH:mm"),
                 end_e.time().toString("HH:mm"),
                 ppl_e.value(), notes_e.text(), bid)
            )
            conn2.commit(); conn2.close()
            QMessageBox.information(self.page, "✅", "Booking updated successfully.")
            self.refresh()