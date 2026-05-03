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

    conn.commit()

    # Seed default data only once
    c.execute('SELECT COUNT(*) FROM rooms')
    if c.fetchone()[0] == 0:
        _seed_data(c)
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
