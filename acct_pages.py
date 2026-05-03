"""acct_pages.py — Accounting & Account Statement pages."""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QDoubleSpinBox, QFormLayout,
    QMessageBox, QTabWidget
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from widgets import StatCard, make_table, set_row, make_divider
from core import AccountingManager, AccountStatementManager


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

        # Tab 1: Journal Entries
        self.je_tab = QWidget()
        jl = QVBoxLayout(self.je_tab); jl.setContentsMargins(16,16,16,16)
        jl.addWidget(QLabel("📒  Journal Entries", objectName="sec_title"))
        self.je_tbl = make_table(["#","Date","Description","Reference","Total Debit"])
        jl.addWidget(self.je_tbl)

        jl.addWidget(make_divider())
        jl.addWidget(QLabel("➕  New Journal Entry", objectName="sec_title"))
        f = QFormLayout(); f.setSpacing(8)
        self.je_desc = QLineEdit(); self.je_desc.setPlaceholderText("Description...")
        self.je_ref = QLineEdit(); self.je_ref.setPlaceholderText("Reference...")
        self.je_acc1 = QComboBox()
        self.je_dr = QDoubleSpinBox(); self.je_dr.setMaximum(999999); self.je_dr.setPrefix("DR ")
        self.je_acc2 = QComboBox()
        self.je_cr = QDoubleSpinBox(); self.je_cr.setMaximum(999999); self.je_cr.setPrefix("CR ")
        f.addRow("Description:", self.je_desc)
        f.addRow("Reference:", self.je_ref)
        f.addRow("Debit Account:", self.je_acc1)
        f.addRow("Debit Amount:", self.je_dr)
        f.addRow("Credit Account:", self.je_acc2)
        f.addRow("Credit Amount:", self.je_cr)
        jl.addLayout(f)
        btn = QPushButton("💾 Save Entry"); btn.setObjectName("primary")
        btn.setCursor(Qt.PointingHandCursor); btn.clicked.connect(self.handle_add_je)
        jl.addWidget(btn)
        self.tabs.addTab(self.je_tab, "📒 Journal Entries")

        # Tab 2: General Ledger
        self.gl_tab = QWidget()
        gl = QVBoxLayout(self.gl_tab); gl.setContentsMargins(16,16,16,16)
        gl.addWidget(QLabel("📖  General Ledger", objectName="sec_title"))
        self.gl_tbl = make_table(["Account","Date","Description","Debit","Credit","Ref"])
        gl.addWidget(self.gl_tbl)
        self.tabs.addTab(self.gl_tab, "📖 General Ledger")

        # Tab 3: Income Statement
        self.is_tab = QWidget()
        il = QVBoxLayout(self.is_tab); il.setContentsMargins(16,16,16,16)
        il.addWidget(QLabel("💰  Income Statement", objectName="sec_title"))
        sr = QHBoxLayout(); sr.setSpacing(14)
        self.is_rev = StatCard("💰","Total Revenue","0 EGP","#3ecf8e")
        self.is_exp = StatCard("💸","Total Expenses","0 EGP","#f06292")
        self.is_net = StatCard("📈","Net Income","0 EGP","#5c9cf5")
        sr.addWidget(self.is_rev); sr.addWidget(self.is_exp); sr.addWidget(self.is_net)
        il.addLayout(sr)
        il.addWidget(QLabel("Revenues:", objectName="sec_title"))
        self.is_rev_tbl = make_table(["Account","Amount"]); self.is_rev_tbl.setMaximumHeight(150)
        il.addWidget(self.is_rev_tbl)
        il.addWidget(QLabel("Expenses:", objectName="sec_title"))
        self.is_exp_tbl = make_table(["Account","Amount"]); self.is_exp_tbl.setMaximumHeight(150)
        il.addWidget(self.is_exp_tbl)
        self.tabs.addTab(self.is_tab, "💰 Income Statement")

        # Tab 4: Balance Sheet
        self.bs_tab = QWidget()
        bl = QVBoxLayout(self.bs_tab); bl.setContentsMargins(16,16,16,16)
        bl.addWidget(QLabel("📊  Balance Sheet", objectName="sec_title"))
        sr2 = QHBoxLayout(); sr2.setSpacing(14)
        self.bs_asset = StatCard("🏦","Total Assets","0 EGP","#3ecf8e")
        self.bs_liab = StatCard("📋","Total Liabilities","0 EGP","#f06292")
        self.bs_eq = StatCard("💎","Total Equity","0 EGP","#5c9cf5")
        sr2.addWidget(self.bs_asset); sr2.addWidget(self.bs_liab); sr2.addWidget(self.bs_eq)
        bl.addLayout(sr2)
        bl.addWidget(QLabel("Assets:", objectName="sec_title"))
        self.bs_a_tbl = make_table(["Account","Balance"]); self.bs_a_tbl.setMaximumHeight(120)
        bl.addWidget(self.bs_a_tbl)
        bl.addWidget(QLabel("Liabilities:", objectName="sec_title"))
        self.bs_l_tbl = make_table(["Account","Balance"]); self.bs_l_tbl.setMaximumHeight(120)
        bl.addWidget(self.bs_l_tbl)
        self.tabs.addTab(self.bs_tab, "📊 Balance Sheet")

        # Tab 5: Trial Balance
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

        ref_btn = QPushButton("🔄 Refresh All"); ref_btn.setObjectName("primary")
        ref_btn.setCursor(Qt.PointingHandCursor); ref_btn.clicked.connect(self.refresh)
        main_lay.addWidget(ref_btn)

    def refresh(self):
        # Accounts for combos
        accs = AccountingManager.get_accounts()
        self.je_acc1.clear(); self.je_acc2.clear()
        for a in accs:
            self.je_acc1.addItem(f"{a[0]} - {a[1]}", a[1])
            self.je_acc2.addItem(f"{a[0]} - {a[1]}", a[1])

        # Journal entries
        jes = AccountingManager.get_journal_entries()
        self.je_tbl.setRowCount(len(jes))
        for i, j in enumerate(jes):
            set_row(self.je_tbl, i, [j[0], j[1], j[2], j[3], f"{j[4]:.2f}"])

        # General ledger
        gl = AccountingManager.get_general_ledger()
        self.gl_tbl.setRowCount(len(gl))
        for i, g in enumerate(gl):
            set_row(self.gl_tbl, i, [g[0], g[1], g[2], f"{g[3]:.2f}", f"{g[4]:.2f}", g[5]])

        # Income statement
        inc = AccountingManager.get_income_statement()
        self.is_rev.update_value(f"{inc['total_revenue']:,.2f} EGP")
        self.is_exp.update_value(f"{inc['total_expenses']:,.2f} EGP")
        ni = inc['net_income']
        self.is_net.update_value(f"{ni:,.2f} EGP", "#3ecf8e" if ni >= 0 else "#f06292")
        self.is_rev_tbl.setRowCount(len(inc['revenues']))
        for i, r in enumerate(inc['revenues']):
            set_row(self.is_rev_tbl, i, [r[0], f"{r[1]:,.2f}"])
        exp_rows = list(inc['expenses'])
        if inc['system_expenses'] > 0:
            exp_rows.append(('System Expenses (Rent/Utils)', inc['system_expenses']))
        self.is_exp_tbl.setRowCount(len(exp_rows))
        for i, e in enumerate(exp_rows):
            set_row(self.is_exp_tbl, i, [e[0], f"{e[1]:,.2f}"])

        # Balance sheet
        bs = AccountingManager.get_balance_sheet()
        asset_rows = list(bs.get('Asset', []))
        if bs['inventory_value'] > 0:
            asset_rows.append(('Inventory (Stock)', bs['inventory_value']))
        if bs['cash_balance'] != 0:
            asset_rows.append(('Cash Balance', bs['cash_balance']))
        ta = sum(a[1] for a in asset_rows)
        self.bs_asset.update_value(f"{ta:,.2f} EGP")
        self.bs_a_tbl.setRowCount(len(asset_rows))
        for i, a in enumerate(asset_rows):
            set_row(self.bs_a_tbl, i, [a[0], f"{a[1]:,.2f}"])

        liab_rows = bs.get('Liability', [])
        tl_val = sum(abs(l[1]) for l in liab_rows)
        self.bs_liab.update_value(f"{tl_val:,.2f} EGP")
        self.bs_l_tbl.setRowCount(len(liab_rows))
        for i, l in enumerate(liab_rows):
            set_row(self.bs_l_tbl, i, [l[0], f"{abs(l[1]):,.2f}"])

        eq_rows = bs.get('Equity', [])
        te = sum(abs(e[1]) for e in eq_rows)
        self.bs_eq.update_value(f"{te:,.2f} EGP")

        # Trial balance
        tb = AccountingManager.get_trial_balance()
        self.tb_tbl.setRowCount(len(tb))
        td, tc = 0, 0
        for i, t in enumerate(tb):
            set_row(self.tb_tbl, i, [t[0], f"{t[1]:,.2f}", f"{t[2]:,.2f}"])
            td += t[1]; tc += t[2]
        self.tb_dr_lbl.setText(f"Total Debit: {td:,.2f}")
        self.tb_cr_lbl.setText(f"Total Credit: {tc:,.2f}")

    def handle_add_je(self):
        desc = self.je_desc.text().strip()
        if not desc: return QMessageBox.warning(self.page, "Error", "Enter description.")
        dr_acc = self.je_acc1.currentData()
        cr_acc = self.je_acc2.currentData()
        dr_amt = self.je_dr.value()
        cr_amt = self.je_cr.value()
        if dr_amt <= 0 or cr_amt <= 0:
            return QMessageBox.warning(self.page, "Error", "Enter valid amounts.")
        lines = [(dr_acc, dr_amt, 0), (cr_acc, 0, cr_amt)]
        ok, msg = AccountingManager.create_journal_entry(desc, lines, self.je_ref.text())
        if ok:
            QMessageBox.information(self.page, "✅", msg)
            self.je_desc.clear(); self.je_ref.clear()
            self.je_dr.setValue(0); self.je_cr.setValue(0)
            self.refresh()


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
        self.cs_paid = StatCard("✅","Paid","0 EGP","#3ecf8e")
        self.cs_out = StatCard("⏳","Outstanding","0 EGP","#ffa726")
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
        self.ss_paid = StatCard("✅","Paid","0 EGP","#3ecf8e")
        self.ss_out = StatCard("⏳","Outstanding","0 EGP","#ffa726")
        sr2.addWidget(self.ss_total); sr2.addWidget(self.ss_paid); sr2.addWidget(self.ss_out)
        sl.addLayout(sr2)

        self.ss_tbl = make_table(["#","Supplier","Date","Amount","Status"])
        sl.addWidget(self.ss_tbl)
        self.tabs.addTab(self.ss_tab, "🏭 Supplier Statement")

        ref_btn = QPushButton("🔄 Refresh"); ref_btn.setObjectName("primary")
        ref_btn.setCursor(Qt.PointingHandCursor); ref_btn.clicked.connect(self.refresh)
        main_lay.addWidget(ref_btn)

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
            self.cs_total.update_value("—"); self.cs_paid.update_value("—"); self.cs_out.update_value("—")
        else:
            rows = AccountStatementManager.get_customer_statement(name)
            bal = AccountStatementManager.get_customer_balance(name)
            self.cs_total.update_value(f"{bal['total']:,.2f} EGP")
            self.cs_paid.update_value(f"{bal['paid']:,.2f} EGP")
            self.cs_out.update_value(f"{bal['outstanding']:,.2f} EGP")
        self.cs_tbl.setRowCount(len(rows))
        for i, r in enumerate(rows):
            set_row(self.cs_tbl, i, [r[0], r[1], r[2], f"{r[3]:,.2f}", r[4]])
            si = self.cs_tbl.item(i, 4)
            if si: si.setForeground(QColor("#3ecf8e") if r[4]=="Paid" else QColor("#ffa726"))

    def _load_supplier(self):
        name = self.ss_combo.currentText()
        if name == "All Suppliers" or not name:
            rows = AccountStatementManager.get_supplier_statement()
            self.ss_total.update_value("—"); self.ss_paid.update_value("—"); self.ss_out.update_value("—")
        else:
            rows = AccountStatementManager.get_supplier_statement(name)
            bal = AccountStatementManager.get_supplier_balance(name)
            self.ss_total.update_value(f"{bal['total']:,.2f} EGP")
            self.ss_paid.update_value(f"{bal['paid']:,.2f} EGP")
            self.ss_out.update_value(f"{bal['outstanding']:,.2f} EGP")
        self.ss_tbl.setRowCount(len(rows))
        for i, r in enumerate(rows):
            set_row(self.ss_tbl, i, [r[0], r[1], r[2], f"{r[3]:,.2f}", r[4]])
            si = self.ss_tbl.item(i, 4)
            if si: si.setForeground(QColor("#3ecf8e") if r[4]=="Paid" else QColor("#ffa726"))
