"""new_pages.py — Sales, Purchase, Accounting, Account Statement pages."""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QDoubleSpinBox, QSpinBox, QFormLayout,
    QFrame, QMessageBox, QGridLayout, QScrollArea, QTabWidget,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from widgets import StatCard, make_table, set_row, make_divider
from core import (InventoryManager, SalesInvoiceManager, PurchaseInvoiceManager,
                  AccountingManager, AccountStatementManager, ReportManager)


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
#  SALES INVOICE PAGE
# ═══════════════════════════════════════════════════════════════
class SalesInvoicePage:
    def __init__(self):
        self.page, lay = page_container("Sales", "Sales Invoices")
        grid = QHBoxLayout(); grid.setSpacing(20)

        # Left: invoice list
        left = QWidget(); left.setObjectName("card")
        ll = QVBoxLayout(left); ll.setContentsMargins(16,16,16,16)
        ll.addWidget(QLabel("📋  Sales Invoices", objectName="sec_title"))
        self.inv_tbl = make_table(["#","Customer","Date","Total","Status"])
        ll.addWidget(self.inv_tbl)
        row = QHBoxLayout()
        del_btn = QPushButton("🗑 Delete"); del_btn.setObjectName("danger")
        del_btn.setCursor(Qt.PointingHandCursor); del_btn.clicked.connect(self.handle_delete)
        paid_btn = QPushButton("✅ Mark Paid"); paid_btn.setObjectName("primary")
        paid_btn.setCursor(Qt.PointingHandCursor); paid_btn.clicked.connect(self.handle_paid)
        row.addWidget(del_btn); row.addWidget(paid_btn); row.addStretch()
        ll.addLayout(row)
        grid.addWidget(left, 3)

        # Right: create invoice
        right = QWidget(); right.setObjectName("card")
        rl = QVBoxLayout(right); rl.setContentsMargins(16,16,16,20); rl.setSpacing(12)
        rl.addWidget(QLabel("🧾  Sales Invoice", objectName="sec_title"))
        f = QFormLayout(); f.setSpacing(8)
        self.cust_combo = QComboBox(); self.cust_combo.setEditable(True)
        f.addRow("Customer:", self.cust_combo)
        rl.addLayout(f)

        rl.addWidget(QLabel("Products:", objectName="sec_title"))
        self.item_rows = []
        self.items_layout = QVBoxLayout()
        rl.addLayout(self.items_layout)
        self._add_item_row()

        ab = QPushButton("➕ Add Line"); ab.setObjectName("secondary")
        ab.setCursor(Qt.PointingHandCursor); ab.clicked.connect(self._add_item_row)
        rl.addWidget(ab)

        self.total_lbl = QLabel("Total: 0.00 EGP")
        self.total_lbl.setStyleSheet("font-size:16px; font-weight:700; color:#3ecf8e;")
        rl.addWidget(self.total_lbl)

        save = QPushButton("💾  Save Invoice"); save.setObjectName("primary")
        save.setCursor(Qt.PointingHandCursor); save.clicked.connect(self.handle_save)
        rl.addWidget(save); rl.addStretch()
        grid.addWidget(right, 2)
        lay.addLayout(grid)
        self._refresh_cb = None

    def _add_item_row(self):
        row_w = QWidget()
        hl = QHBoxLayout(row_w); hl.setContentsMargins(0,0,0,0); hl.setSpacing(6)
        prod = QComboBox(); prod.setMinimumWidth(120)
        qty = QSpinBox(); qty.setMinimum(1); qty.setMaximum(9999)
        price = QDoubleSpinBox(); price.setMaximum(99999); price.setDecimals(2); price.setPrefix("EGP ")
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

        def remove(e=entry):
            if len(self.item_rows) > 1:
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
                    cb.addItem(f"{p[1]} (stock:{p[3]})", (p[0], p[4]))
                cb.blockSignals(False)

    def _update_total(self):
        total = sum(e['qty'].value() * e['price'].value() for e in self.item_rows)
        self.total_lbl.setText(f"Total: {total:.2f} EGP")

    def refresh(self):
        custs = SalesInvoiceManager.get_customers()
        self.cust_combo.clear()
        for c in custs: self.cust_combo.addItem(c[1])

        invs = SalesInvoiceManager.get_all_invoices()
        self.inv_tbl.setRowCount(len(invs))
        for i, inv in enumerate(invs):
            set_row(self.inv_tbl, i, [inv[0], inv[1], inv[2], f"{inv[3]:.2f}", inv[4]])
            si = self.inv_tbl.item(i, 4)
            if si: si.setForeground(QColor("#3ecf8e") if inv[4]=="Paid" else QColor("#ffa726"))

        for entry in self.item_rows:
            entry['prod'].clear()
        self._populate_products()

    def handle_save(self):
        cust = self.cust_combo.currentText().strip()
        if not cust: return QMessageBox.warning(self.page, "Error", "Select a customer.")
        items = []
        for e in self.item_rows:
            data = e['prod'].currentData()
            if not data: continue
            items.append((data[0], e['qty'].value(), e['price'].value()))
        if not items: return QMessageBox.warning(self.page, "Error", "Add at least one product.")
        ok, msg = SalesInvoiceManager.create_invoice(cust, items)
        if ok:
            QMessageBox.information(self.page, "✅", msg)
            self.refresh()
            if self._refresh_cb: self._refresh_cb()
        else:
            QMessageBox.warning(self.page, "Error", msg)

    def handle_delete(self):
        row = self.inv_tbl.currentRow()
        if row < 0: return QMessageBox.warning(self.page, "Error", "Select an invoice.")
        iid = int(self.inv_tbl.item(row, 0).text())
        reply = QMessageBox.question(self.page, "Confirm", f"Delete invoice #{iid}?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            SalesInvoiceManager.delete_invoice(iid); self.refresh()

    def handle_paid(self):
        row = self.inv_tbl.currentRow()
        if row < 0: return QMessageBox.warning(self.page, "Error", "Select an invoice.")
        iid = int(self.inv_tbl.item(row, 0).text())
        SalesInvoiceManager.mark_paid(iid); self.refresh()


# ═══════════════════════════════════════════════════════════════
#  PURCHASE INVOICE PAGE
# ═══════════════════════════════════════════════════════════════
class PurchaseInvoicePage:
    def __init__(self):
        self.page, lay = page_container("Purchase", "Purchase Invoices")
        grid = QHBoxLayout(); grid.setSpacing(20)

        left = QWidget(); left.setObjectName("card")
        ll = QVBoxLayout(left); ll.setContentsMargins(16,16,16,16)
        ll.addWidget(QLabel("📋  Purchase Invoices", objectName="sec_title"))
        self.inv_tbl = make_table(["#","Supplier","Date","Total","Status"])
        ll.addWidget(self.inv_tbl)
        row = QHBoxLayout()
        del_btn = QPushButton("🗑 Delete"); del_btn.setObjectName("danger")
        del_btn.setCursor(Qt.PointingHandCursor); del_btn.clicked.connect(self.handle_delete)
        paid_btn = QPushButton("✅ Mark Paid"); paid_btn.setObjectName("primary")
        paid_btn.setCursor(Qt.PointingHandCursor); paid_btn.clicked.connect(self.handle_paid)
        row.addWidget(del_btn); row.addWidget(paid_btn); row.addStretch()
        ll.addLayout(row)
        grid.addWidget(left, 3)

        right = QWidget(); right.setObjectName("card")
        rl = QVBoxLayout(right); rl.setContentsMargins(16,16,16,20); rl.setSpacing(12)
        rl.addWidget(QLabel("🧾  Purchase Invoice", objectName="sec_title"))
        f = QFormLayout(); f.setSpacing(8)
        self.sup_combo = QComboBox(); self.sup_combo.setEditable(True)
        f.addRow("Supplier:", self.sup_combo)
        rl.addLayout(f)

        rl.addWidget(QLabel("Products:", objectName="sec_title"))
        self.item_rows = []
        self.items_layout = QVBoxLayout()
        rl.addLayout(self.items_layout)
        self._add_item_row()

        ab = QPushButton("➕ Add Line"); ab.setObjectName("secondary")
        ab.setCursor(Qt.PointingHandCursor); ab.clicked.connect(self._add_item_row)
        rl.addWidget(ab)

        self.total_lbl = QLabel("Total: 0.00 EGP")
        self.total_lbl.setStyleSheet("font-size:16px; font-weight:700; color:#f06292;")
        rl.addWidget(self.total_lbl)

        save = QPushButton("💾  Save Invoice"); save.setObjectName("primary")
        save.setCursor(Qt.PointingHandCursor); save.clicked.connect(self.handle_save)
        rl.addWidget(save); rl.addStretch()
        grid.addWidget(right, 2)
        lay.addLayout(grid)
        self._refresh_cb = None

    def _add_item_row(self):
        row_w = QWidget()
        hl = QHBoxLayout(row_w); hl.setContentsMargins(0,0,0,0); hl.setSpacing(6)
        prod = QComboBox(); prod.setMinimumWidth(120)
        qty = QSpinBox(); qty.setMinimum(1); qty.setMaximum(9999)
        price = QDoubleSpinBox(); price.setMaximum(99999); price.setDecimals(2); price.setPrefix("EGP ")
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

        def remove(e=entry):
            if len(self.item_rows) > 1:
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
                    cb.addItem(p[1], (p[0], p[5]))
                cb.blockSignals(False)

    def _update_total(self):
        total = sum(e['qty'].value() * e['price'].value() for e in self.item_rows)
        self.total_lbl.setText(f"Total: {total:.2f} EGP")

    def refresh(self):
        sups = PurchaseInvoiceManager.get_suppliers()
        self.sup_combo.clear()
        for s in sups: self.sup_combo.addItem(s[1])

        invs = PurchaseInvoiceManager.get_all_invoices()
        self.inv_tbl.setRowCount(len(invs))
        for i, inv in enumerate(invs):
            set_row(self.inv_tbl, i, [inv[0], inv[1], inv[2], f"{inv[3]:.2f}", inv[4]])
            si = self.inv_tbl.item(i, 4)
            if si: si.setForeground(QColor("#3ecf8e") if inv[4]=="Paid" else QColor("#ffa726"))
        for entry in self.item_rows:
            entry['prod'].clear()
        self._populate_products()

    def handle_save(self):
        sup = self.sup_combo.currentText().strip()
        if not sup: return QMessageBox.warning(self.page, "Error", "Select a supplier.")
        items = []
        for e in self.item_rows:
            data = e['prod'].currentData()
            if not data: continue
            items.append((data[0], e['qty'].value(), e['price'].value()))
        if not items: return QMessageBox.warning(self.page, "Error", "Add at least one product.")
        ok, msg = PurchaseInvoiceManager.create_invoice(sup, items)
        if ok:
            QMessageBox.information(self.page, "✅", msg)
            self.refresh()
            if self._refresh_cb: self._refresh_cb()
        else:
            QMessageBox.warning(self.page, "Error", msg)

    def handle_delete(self):
        row = self.inv_tbl.currentRow()
        if row < 0: return QMessageBox.warning(self.page, "Error", "Select an invoice.")
        iid = int(self.inv_tbl.item(row, 0).text())
        reply = QMessageBox.question(self.page, "Confirm", f"Delete invoice #{iid}?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            PurchaseInvoiceManager.delete_invoice(iid); self.refresh()

    def handle_paid(self):
        row = self.inv_tbl.currentRow()
        if row < 0: return QMessageBox.warning(self.page, "Error", "Select an invoice.")
        iid = int(self.inv_tbl.item(row, 0).text())
        PurchaseInvoiceManager.mark_paid(iid); self.refresh()
