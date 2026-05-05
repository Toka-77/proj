"""add_new_tables.py — add settings + loyalty + bookings tables to database.py."""

with open('database.py', encoding='utf-8') as f:
    content = f.read()

NEW_TABLES = '''
    # ── App Settings ─────────────────────────────────────────────────────────
    c.execute(\'\'\'
        CREATE TABLE IF NOT EXISTS settings (
            key   TEXT PRIMARY KEY,
            value TEXT NOT NULL DEFAULT \'\'
        )
    \'\'\')

    # ── Loyalty Accounts ─────────────────────────────────────────────────────
    c.execute(\'\'\'
        CREATE TABLE IF NOT EXISTS loyalty_accounts (
            customer_name TEXT PRIMARY KEY,
            points        INTEGER NOT NULL DEFAULT 0,
            tier          TEXT    NOT NULL DEFAULT \'Bronze\',
            total_spent   REAL    NOT NULL DEFAULT 0.0
        )
    \'\'\')

    # ── Bookings (Reservations) ───────────────────────────────────────────────
    c.execute(\'\'\'
        CREATE TABLE IF NOT EXISTS bookings (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id       INTEGER NOT NULL,
            customer_name TEXT    NOT NULL DEFAULT \'Walk-in\',
            booking_date  TEXT    NOT NULL,
            start_time    TEXT    NOT NULL,
            end_time      TEXT    NOT NULL,
            num_people    INTEGER NOT NULL DEFAULT 1,
            status        TEXT    NOT NULL DEFAULT \'Confirmed\'
                          CHECK(status IN (\'Confirmed\',\'Cancelled\',\'Completed\')),
            notes         TEXT    DEFAULT \'\',
            FOREIGN KEY(room_id) REFERENCES rooms(id)
        )
    \'\'\')

'''

SEED_SETTINGS = '''
    # Seed default settings if empty
    c.execute('SELECT COUNT(*) FROM settings')
    if c.fetchone()[0] == 0:
        _seed_settings(c)
        conn.commit()

'''

# Insert new tables before conn.commit() on line 188
content = content.replace(
    '    conn.commit()\n\n    # ── Full schema migration if needed',
    NEW_TABLES + '    conn.commit()\n\n    # ── Full schema migration if needed'
)

# Insert seed call after suppliers seed
content = content.replace(
    "    # Seed products if empty\n    c.execute('SELECT COUNT(*) FROM products')",
    SEED_SETTINGS + "    # Seed products if empty\n    c.execute('SELECT COUNT(*) FROM products')"
)

# Add _seed_settings function before end of file
SEED_FN = '''

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
'''

content = content.rstrip() + SEED_FN + '\n'

with open('database.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('database.py updated')
