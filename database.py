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
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            name           TEXT    NOT NULL,
            category       TEXT    DEFAULT 'Snack',
            quantity       INTEGER NOT NULL DEFAULT 0,
            price          REAL    NOT NULL,
            cost_price     REAL    DEFAULT 0.0,
            low_stock_alert INTEGER DEFAULT 5
        )
    ''')

    # ── Sales ────────────────────────────────────────────────────────────────
    c.execute('''
        CREATE TABLE IF NOT EXISTS sales (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id  INTEGER NOT NULL,
            session_id  INTEGER,
            qty_sold    INTEGER NOT NULL DEFAULT 1,
            unit_price  REAL    NOT NULL,
            total_price REAL    NOT NULL,
            sale_time   DATETIME NOT NULL,
            FOREIGN KEY(product_id) REFERENCES products(id),
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
            product_id  INTEGER NOT NULL,
            quantity    INTEGER NOT NULL DEFAULT 1,
            unit_price  REAL    NOT NULL,
            total       REAL    NOT NULL,
            FOREIGN KEY(invoice_id) REFERENCES sales_invoices(id) ON DELETE CASCADE,
            FOREIGN KEY(product_id) REFERENCES products(id)
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
            product_id  INTEGER NOT NULL,
            quantity    INTEGER NOT NULL DEFAULT 1,
            unit_price  REAL    NOT NULL,
            total       REAL    NOT NULL,
            FOREIGN KEY(invoice_id) REFERENCES purchase_invoices(id) ON DELETE CASCADE,
            FOREIGN KEY(product_id) REFERENCES products(id)
        )
    ''')

    # ── Journal Entries ──────────────────────────────────────────────────────
    c.execute('''
        CREATE TABLE IF NOT EXISTS journal_entries (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_date  DATETIME NOT NULL,
            description TEXT    DEFAULT '',
            reference   TEXT    DEFAULT ''
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

    conn.commit()

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

    conn.close()


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

    products = [
        ('Pepsi Can',    'Drinks',  50, 15.0,  8.0,  5),
        ('Mirinda',      'Drinks',  40, 15.0,  8.0,  5),
        ('Water Bottle', 'Drinks', 100,  5.0,  2.0, 10),
        ('Lays Classic', 'Snacks',  30, 12.0,  6.0,  5),
        ('Doritos',      'Snacks',  25, 15.0,  8.0,  5),
        ('Kit-Kat',      'Snacks',  40, 10.0,  5.0,  5),
        ('Coffee',       'Hot',    100, 30.0, 10.0, 10),
        ('Tea',          'Hot',     80, 20.0,  5.0, 10),
        ('Cappuccino',   'Hot',     60, 40.0, 15.0,  5),
        ('Popcorn',      'Snacks',  50, 20.0,  8.0, 10),
    ]
    c.executemany(
        'INSERT INTO products (name, category, quantity, price, cost_price, low_stock_alert) VALUES (?,?,?,?,?,?)',
        products
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
        ('Ahmed Hassan', '01098765432', 'ahmed@email.com', 'VIP member'),
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
