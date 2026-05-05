import sqlite3
import os
from datetime import datetime

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ais_hub.db')

def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()

    # ── Rooms ────────────────────────────────────────────────────────────────
    c.execute('''
        CREATE TABLE IF NOT EXISTS rooms (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            type        TEXT    NOT NULL CHECK(type IN ('Study','Gaming','Cinema')),
            status      TEXT    NOT NULL DEFAULT 'Available'
                                CHECK(status IN ('Available','Occupied')),
            base_price  REAL    NOT NULL,
            capacity    INTEGER NOT NULL DEFAULT 10,
            description TEXT    DEFAULT ''
        )
    ''')

    # ── Customers ────────────────────────────────────────────────────────────
    c.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            name  TEXT    NOT NULL,
            phone TEXT    DEFAULT '',
            email TEXT    DEFAULT '',
            notes TEXT    DEFAULT ''
        )
    ''')

    # ── Suppliers ────────────────────────────────────────────────────────────
    c.execute('''
        CREATE TABLE IF NOT EXISTS suppliers (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            name    TEXT    NOT NULL,
            phone   TEXT    DEFAULT '',
            email   TEXT    DEFAULT '',
            address TEXT    DEFAULT '',
            notes   TEXT    DEFAULT ''
        )
    ''')

    # ── Sessions ─────────────────────────────────────────────────────────────
    c.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id       INTEGER NOT NULL,
            customer_name TEXT    DEFAULT 'Walk-in',
            num_people    INTEGER NOT NULL DEFAULT 1,
            start_time    DATETIME NOT NULL,
            end_time      DATETIME,
            room_charge   REAL    DEFAULT 0.0,
            snacks_total  REAL    DEFAULT 0.0,
            discount      REAL    DEFAULT 0.0,
            promo_code    TEXT    DEFAULT '',
            total_bill    REAL    DEFAULT 0.0,
            notes         TEXT    DEFAULT '',
            FOREIGN KEY(room_id) REFERENCES rooms(id)
        )
    ''')

    # ── Products (Inventory) ─────────────────────────────────────────────────
    c.execute('''
        CREATE TABLE IF NOT EXISTS products (
            sku           TEXT PRIMARY KEY,
            name          TEXT NOT NULL,
            category      TEXT DEFAULT 'Other',
            selling_price REAL NOT NULL DEFAULT 0.0,
            quantity      INTEGER NOT NULL DEFAULT 0
        )
    ''')

    # ── Sales ───────────────────────────────────────────────────────────────
    c.execute('''
        CREATE TABLE IF NOT EXISTS sales (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            product_sku TEXT    NOT NULL,
            session_id  INTEGER,
            qty_sold    INTEGER NOT NULL DEFAULT 1,
            unit_price  REAL    NOT NULL,
            total_price REAL    NOT NULL,
            sale_time   DATETIME NOT NULL,
            FOREIGN KEY(session_id) REFERENCES sessions(id)
        )
    ''')

    # ── Expenses ─────────────────────────────────────────────────────────────
    c.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            category    TEXT    NOT NULL,
            amount      REAL    NOT NULL,
            date        DATETIME NOT NULL,
            description TEXT    DEFAULT ''
        )
    ''')

    # ── Sales Invoices ───────────────────────────────────────────────────────
    c.execute('''
        CREATE TABLE IF NOT EXISTS sales_invoices (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name  TEXT    NOT NULL DEFAULT 'Walk-in',
            invoice_date   DATETIME NOT NULL,
            total_amount   REAL    DEFAULT 0.0,
            status         TEXT    DEFAULT 'Unpaid' CHECK(status IN ('Paid','Unpaid','Partial')),
            notes          TEXT    DEFAULT ''
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS sales_invoice_items (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id  INTEGER NOT NULL,
            product_sku TEXT    NOT NULL,
            quantity    INTEGER NOT NULL DEFAULT 1,
            unit_price  REAL    NOT NULL,
            total       REAL    NOT NULL,
            FOREIGN KEY(invoice_id) REFERENCES sales_invoices(id) ON DELETE CASCADE
        )
    ''')

    # ── Purchase Invoices ────────────────────────────────────────────────────
    c.execute('''
        CREATE TABLE IF NOT EXISTS purchase_invoices (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_name   TEXT    NOT NULL DEFAULT 'Unknown',
            invoice_date    DATETIME NOT NULL,
            total_amount    REAL    DEFAULT 0.0,
            status          TEXT    DEFAULT 'Unpaid' CHECK(status IN ('Paid','Unpaid','Partial')),
            notes           TEXT    DEFAULT ''
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS purchase_invoice_items (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id  INTEGER NOT NULL,
            product_sku TEXT    NOT NULL,
            quantity    INTEGER NOT NULL DEFAULT 1,
            unit_cost   REAL    NOT NULL,
            total       REAL    NOT NULL,
            FOREIGN KEY(invoice_id) REFERENCES purchase_invoices(id) ON DELETE CASCADE
        )
    ''')

    # ── Journal Entries ──────────────────────────────────────────────────────
    c.execute('''
        CREATE TABLE IF NOT EXISTS journal_entries (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_date  DATETIME NOT NULL,
            description TEXT    DEFAULT '',
            reference   TEXT    DEFAULT '',
            entity      TEXT    DEFAULT ''
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS journal_lines (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_id    INTEGER NOT NULL,
            account     TEXT    NOT NULL,
            debit       REAL    DEFAULT 0.0,
            credit      REAL    DEFAULT 0.0,
            FOREIGN KEY(entry_id) REFERENCES journal_entries(id) ON DELETE CASCADE
        )
    ''')

    # ── Chart of Accounts ────────────────────────────────────────────────────
    c.execute('''
        CREATE TABLE IF NOT EXISTS chart_of_accounts (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            account_code TEXT    NOT NULL UNIQUE,
            account_name TEXT    NOT NULL,
            account_type TEXT    NOT NULL CHECK(account_type IN ('Asset','Liability','Equity','Revenue','Expense')),
            parent_code  TEXT    DEFAULT ''
        )
    ''')


    # ── App Settings ─────────────────────────────────────────────────────────
    c.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key   TEXT PRIMARY KEY,
            value TEXT NOT NULL DEFAULT ''
        )
    ''')

    # ── Loyalty Accounts ─────────────────────────────────────────────────────
    c.execute('''
        CREATE TABLE IF NOT EXISTS loyalty_accounts (
            customer_name TEXT PRIMARY KEY,
            points        INTEGER NOT NULL DEFAULT 0,
            tier          TEXT    NOT NULL DEFAULT 'Bronze',
            total_spent   REAL    NOT NULL DEFAULT 0.0
        )
    ''')

    # ── Bookings (Reservations) ───────────────────────────────────────────────
    c.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id       INTEGER NOT NULL,
            customer_name TEXT    NOT NULL DEFAULT 'Walk-in',
            booking_date  TEXT    NOT NULL,
            start_time    TEXT    NOT NULL,
            end_time      TEXT    NOT NULL,
            num_people    INTEGER NOT NULL DEFAULT 1,
            status        TEXT    NOT NULL DEFAULT 'Confirmed'
                          CHECK(status IN ('Confirmed','Cancelled','Completed')),
            notes         TEXT    DEFAULT '',
            FOREIGN KEY(room_id) REFERENCES rooms(id)
        )
    ''')

    conn.commit()

    # ── Full schema migration if needed ────────────────────────────────
    _migrate_to_sku_schema(c, conn)

    # Seed default data only once
    c.execute('SELECT COUNT(*) FROM rooms')
    if c.fetchone()[0] == 0:
        _seed_data(c)
        conn.commit()

    # Seed chart of accounts if empty
    c.execute('SELECT COUNT(*) FROM chart_of_accounts')
    if c.fetchone()[0] == 0:
        _seed_accounts(c)
        conn.commit()

    # Seed default customers if empty
    c.execute('SELECT COUNT(*) FROM customers')
    if c.fetchone()[0] == 0:
        _seed_customers(c)
        conn.commit()

    # Seed default suppliers if empty
    c.execute('SELECT COUNT(*) FROM suppliers')
    if c.fetchone()[0] == 0:
        _seed_suppliers(c)
        conn.commit()


    # Seed default settings if empty
    c.execute('SELECT COUNT(*) FROM settings')
    if c.fetchone()[0] == 0:
        _seed_settings(c)
        conn.commit()

    # Seed products if empty
    c.execute('SELECT COUNT(*) FROM products')
    if c.fetchone()[0] == 0:
        _seed_products(c)
        conn.commit()

    conn.close()


def _migrate_to_sku_schema(c, conn):
    """One-time migration: rebuild products/sales/invoice_items with SKU as PK."""
    cols = [r[1] for r in c.execute("PRAGMA table_info(products)").fetchall()]
    if 'id' not in cols:
        return  # Already on new schema

    # Build old_id → sku map
    old = c.execute("SELECT id, name, category, quantity, price, sku FROM products").fetchall()
    id_to_sku = {}
    used_nums = set()
    for (oid, name, cat, qty, price, sku) in old:
        if sku and sku.startswith('P') and sku[1:].isdigit():
            num = int(sku[1:]); used_nums.add(num)
        else:
            sku = None
        id_to_sku[oid] = (name, cat or 'Other', qty or 0, price or 0.0, sku)

    # Assign SKUs to those without
    counter = 1
    for oid in id_to_sku:
        name, cat, qty, price, sku = id_to_sku[oid]
        if not sku:
            while counter in used_nums: counter += 1
            sku = f"P{counter:03d}"; used_nums.add(counter); counter += 1
            id_to_sku[oid] = (name, cat, qty, price, sku)

    # Migrate related tables
    def _remap(table, old_col, new_col, extra_cols, old_price_col):
        t_cols = [r[1] for r in c.execute(f"PRAGMA table_info({table})").fetchall()]
        if old_col not in t_cols: return
        rows = c.execute(f"SELECT id, invoice_id, {old_col}, quantity, {old_price_col}, total FROM {table}").fetchall()
        c.execute(f"DROP TABLE IF EXISTS _{table}_new")
        c.execute(f"""CREATE TABLE _{table}_new AS SELECT * FROM {table} WHERE 0""")
        # Faster: just drop and recreate
        c.execute(f"DROP TABLE {table}")

    sales_cols = [r[1] for r in c.execute("PRAGMA table_info(sales)").fetchall()]
    if 'product_id' in sales_cols:
        rows = c.execute("SELECT id, product_id, session_id, qty_sold, unit_price, total_price, sale_time FROM sales").fetchall()
        c.execute("DROP TABLE sales")
        c.execute('''CREATE TABLE sales (id INTEGER PRIMARY KEY AUTOINCREMENT, product_sku TEXT NOT NULL,
            session_id INTEGER, qty_sold INTEGER NOT NULL DEFAULT 1,
            unit_price REAL NOT NULL, total_price REAL NOT NULL, sale_time DATETIME NOT NULL,
            FOREIGN KEY(session_id) REFERENCES sessions(id))''')
        for (sid, pid, sess, qty, up, tp, st) in rows:
            psku = id_to_sku.get(pid, (None,None,None,None,f"P{pid:03d}"))[4]
            c.execute("INSERT INTO sales VALUES (?,?,?,?,?,?,?)", (sid, psku, sess, qty, up, tp, st))

    sii_cols = [r[1] for r in c.execute("PRAGMA table_info(sales_invoice_items)").fetchall()]
    if 'product_id' in sii_cols:
        rows = c.execute("SELECT id, invoice_id, product_id, quantity, unit_price, total FROM sales_invoice_items").fetchall()
        c.execute("DROP TABLE sales_invoice_items")
        c.execute('''CREATE TABLE sales_invoice_items (id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER NOT NULL, product_sku TEXT NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 1, unit_price REAL NOT NULL, total REAL NOT NULL,
            FOREIGN KEY(invoice_id) REFERENCES sales_invoices(id) ON DELETE CASCADE)''')
        for (siid, invid, pid, qty, up, tot) in rows:
            psku = id_to_sku.get(pid, (None,None,None,None,f"P{pid:03d}"))[4]
            c.execute("INSERT INTO sales_invoice_items VALUES (?,?,?,?,?,?)", (siid, invid, psku, qty, up, tot))

    pii_cols = [r[1] for r in c.execute("PRAGMA table_info(purchase_invoice_items)").fetchall()]
    if 'product_id' in pii_cols:
        rows = c.execute("SELECT id, invoice_id, product_id, quantity, unit_price, total FROM purchase_invoice_items").fetchall()
        c.execute("DROP TABLE purchase_invoice_items")
        c.execute('''CREATE TABLE purchase_invoice_items (id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER NOT NULL, product_sku TEXT NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 1, unit_cost REAL NOT NULL, total REAL NOT NULL,
            FOREIGN KEY(invoice_id) REFERENCES purchase_invoices(id) ON DELETE CASCADE)''')
        for (piid, invid, pid, qty, up, tot) in rows:
            psku = id_to_sku.get(pid, (None,None,None,None,f"P{pid:03d}"))[4]
            c.execute("INSERT INTO purchase_invoice_items VALUES (?,?,?,?,?,?)", (piid, invid, psku, qty, up, tot))

    # Rebuild products table
    c.execute("DROP TABLE products")
    c.execute('''CREATE TABLE products (sku TEXT PRIMARY KEY, name TEXT NOT NULL,
        category TEXT DEFAULT 'Other', selling_price REAL NOT NULL DEFAULT 0.0,
        quantity INTEGER NOT NULL DEFAULT 0)''')
    for oid, (name, cat, qty, price, sku) in id_to_sku.items():
        c.execute("INSERT OR IGNORE INTO products VALUES (?,?,?,?,?)", (sku, name, cat, price, qty))
    conn.commit()


def _seed_data(c):
    rooms = [
        ('Study Room A',  'Study',  20.0, 6,  'Quiet study environment, 6 seats'),
        ('Study Room B',  'Study',  20.0, 8,  'Large study room, 8 seats'),
        ('Gaming Room 1', 'Gaming', 50.0, 4,  'PS5, Xbox, 4 stations'),
        ('Gaming VIP',    'Gaming', 80.0, 2,  'VIP gaming pod, 2 stations'),
        ('Cinema Hall',   'Cinema', 35.0, 20, 'Full cinema experience, 20 seats'),
    ]
    c.executemany(
        'INSERT INTO rooms (name, type, base_price, capacity, description) VALUES (?,?,?,?,?)',
        rooms
    )

    expenses = [
        ('Rent',        5000.0, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'Monthly rent'),
        ('Electricity',  800.0, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'Monthly electricity bill'),
        ('Internet',     300.0, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'Monthly internet'),
    ]
    c.executemany(
        'INSERT INTO expenses (category, amount, date, description) VALUES (?,?,?,?)',
        expenses
    )


def _seed_products(c):
    """Seed default products with new schema (sku PK)."""
    products = [
        ('P001', 'Pepsi Can',    'Drinks',  15.0, 50),
        ('P002', 'Mirinda',      'Drinks',  15.0, 40),
        ('P003', 'Water Bottle', 'Drinks',   5.0, 100),
        ('P004', 'Lays Classic', 'Snacks',  12.0, 30),
        ('P005', 'Doritos',      'Snacks',  15.0, 25),
        ('P006', 'Kit-Kat',      'Snacks',  10.0, 40),
        ('P007', 'Coffee',       'Hot',     30.0, 100),
        ('P008', 'Tea',          'Hot',     20.0, 80),
        ('P009', 'Cappuccino',   'Hot',     40.0, 60),
        ('P010', 'Popcorn',      'Snacks',  20.0, 50),
    ]
    c.executemany(
        'INSERT INTO products (sku, name, category, selling_price, quantity) VALUES (?,?,?,?,?)',
        products
    )


def _seed_accounts(c):
    """Seed a default chart of accounts."""
    accounts = [
        ('1000', 'Cash',                'Asset'),
        ('1100', 'Accounts Receivable', 'Asset'),
        ('1200', 'Inventory',           'Asset'),
        ('1300', 'Prepaid Expenses',    'Asset'),
        ('2000', 'Accounts Payable',    'Liability'),
        ('2100', 'Accrued Expenses',    'Liability'),
        ('2200', 'Unearned Revenue',    'Liability'),
        ('3000', 'Owner Equity',        'Equity'),
        ('3100', 'Retained Earnings',   'Equity'),
        ('4000', 'Sales Revenue',       'Revenue'),
        ('4100', 'Service Revenue',     'Revenue'),
        ('4200', 'Room Revenue',        'Revenue'),
        ('5000', 'Cost of Goods Sold',  'Expense'),
        ('5100', 'Rent Expense',        'Expense'),
        ('5200', 'Salaries Expense',    'Expense'),
        ('5300', 'Utilities Expense',   'Expense'),
        ('5400', 'Supplies Expense',    'Expense'),
        ('5500', 'Depreciation',        'Expense'),
        ('5600', 'Other Expenses',      'Expense'),
    ]
    c.executemany(
        'INSERT INTO chart_of_accounts (account_code, account_name, account_type) VALUES (?,?,?)',
        accounts
    )


def _seed_customers(c):
    """Seed default customers."""
    customers = [
        ('Paula Samy',  '01012345678', 'paula@email.com', 'Regular customer'),
        ('Toka Khaled', '01090000000', 'toka@email.com', 'VIP member'),
        ('Sara Mohamed', '01055566677', 'sara@email.com', ''),
    ]
    c.executemany(
        'INSERT INTO customers (name, phone, email, notes) VALUES (?,?,?,?)',
        customers
    )


def _seed_suppliers(c):
    """Seed default suppliers."""
    suppliers = [
        ('Fresh Foods Co.',  '0223456789', 'info@freshfoods.com', 'Cairo, Egypt', 'Main food supplier'),
        ('Beverage World',   '0234567890', 'sales@bevworld.com',  'Giza, Egypt',  'Drinks supplier'),
        ('Office Supplies',  '0245678901', 'office@supplies.com', 'Alex, Egypt',  'Stationery & misc'),
    ]
    c.executemany(
        'INSERT INTO suppliers (name, phone, email, address, notes) VALUES (?,?,?,?,?)',
        suppliers
    )

def _seed_settings(c):
    """Seed default application settings."""
    defaults = [
        ('theme',                  'dark'),
        ('language',               'en'),
        ('daily_revenue_target',   '2000'),
        ('low_stock_threshold',    '5'),
        ('session_alert_hours',    '5'),
        ('unpaid_invoice_alert',   '3'),
        ('loyalty_points_rate',    '1'),   # points per EGP
        ('loyalty_redeem_rate',    '100'), # points needed per 1 EGP discount
    ]
    c.executemany("INSERT OR IGNORE INTO settings (key, value) VALUES (?,?)", defaults)

