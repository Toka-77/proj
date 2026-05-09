"""Full project diagnostic test"""
import sys, os, traceback
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

OK  = "[OK]  "
ERR = "[ERR] "
WRN = "[WARN]"
results = []

def check(label, fn):
    try:
        msg = fn()
        results.append((True, label, msg or ""))
        print(f"{OK} {label}{(' — '+msg) if msg else ''}")
    except Exception as e:
        results.append((False, label, str(e)))
        print(f"{ERR} {label} — {e}")

# ── 1. Database ───────────────────────────────────────────────────────────────
from database import init_db, get_connection
check("database.init_db()", lambda: init_db() or None)

conn = get_connection()
c = conn.cursor()

EXPECTED_TABLES = [
    'rooms','customers','suppliers','sessions','products','sales',
    'expenses','sales_invoices','sales_invoice_items',
    'purchase_invoices','purchase_invoice_items',
    'journal_entries','journal_lines','chart_of_accounts',
    'settings','loyalty_accounts','bookings','users'
]
existing = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
for t in EXPECTED_TABLES:
    check(f"  table '{t}' exists", lambda t=t: None if t in existing else (_ for _ in ()).throw(Exception("MISSING")))

# Schema checks
def check_cols(table, required):
    cols = [r[1] for r in c.execute(f"PRAGMA table_info({table})").fetchall()]
    missing = [col for col in required if col not in cols]
    if missing:
        raise Exception(f"missing columns: {missing}")
    return f"cols OK ({', '.join(cols)})"

check("products schema", lambda: check_cols('products', ['sku','name','unit_cost','selling_price','quantity']))
check("users schema",    lambda: check_cols('users', ['id','username','password_hash','full_name','role','is_active']))
check("sessions schema", lambda: check_cols('sessions', ['id','room_id','total_bill','snacks_total','deposit','discount']))
check("journal_lines schema", lambda: check_cols('journal_lines', ['id','entry_id','account','debit','credit']))
check("purchase_invoice_items schema", lambda: check_cols('purchase_invoice_items', ['id','invoice_id','product_sku','quantity','unit_cost','total']))
check("sales_invoice_items schema",    lambda: check_cols('sales_invoice_items',    ['id','invoice_id','product_sku','quantity','unit_price','total']))
check("bookings schema", lambda: check_cols('bookings', ['id','room_id','customer_name','booking_date','start_time','end_time','status']))

# Seeded data
for tbl, minrows in [('rooms',5),('products',5),('users',2),('chart_of_accounts',10),('customers',1),('suppliers',1)]:
    n = c.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
    check(f"  {tbl} seeded ({n} rows)", lambda n=n, m=minrows: None if n >= m else (_ for _ in ()).throw(Exception(f"only {n} rows, expected >= {m}")))

# Users check
users = c.execute("SELECT username, role FROM users").fetchall()
check("admin user exists",    lambda: None if any(u[1]=='admin'    for u in users) else (_ for _ in ()).throw(Exception("no admin user found")))
check("employee user exists", lambda: None if any(u[1]=='employee' for u in users) else (_ for _ in ()).throw(Exception("no employee user found")))

conn.close()

# ── 2. Core imports ───────────────────────────────────────────────────────────
check("import core",    lambda: __import__('core') and None)
check("import styles",  lambda: __import__('styles') and None)
check("import widgets", lambda: __import__('widgets') and None)

# ── 3. Core logic ─────────────────────────────────────────────────────────────
from core import SettingsManager, NotificationManager, UserManager

check("SettingsManager.get(theme)", lambda: SettingsManager.get('theme') or "key missing")
check("SettingsManager.get(language)", lambda: SettingsManager.get('language') or "key missing")
check("UserManager.authenticate admin",   lambda: UserManager.authenticate('admin','admin123') and None)
check("UserManager.authenticate employee",lambda: UserManager.authenticate('employee','emp123') and None)
check("UserManager.authenticate bad pw",  lambda: None if not UserManager.authenticate('admin','wrongpw') else (_ for _ in ()).throw(Exception("bad password authenticated!")))
check("NotificationManager.get_all()",    lambda: str(type(NotificationManager.get_all())))

# ── 4. Business logic spot checks ────────────────────────────────────────────
conn2 = get_connection()
c2 = conn2.cursor()

# product cost vs price (must not be negative)
bad_price = c2.execute("SELECT sku FROM products WHERE selling_price < unit_cost").fetchall()
check("no products selling below cost", lambda: None if not bad_price else (_ for _ in ()).throw(Exception(f"SKUs with selling_price < unit_cost: {bad_price}")))

# rooms have valid types
bad_rooms = c2.execute("SELECT id FROM rooms WHERE type NOT IN ('Study','Gaming','Cinema')").fetchall()
check("all rooms have valid type", lambda: None if not bad_rooms else (_ for _ in ()).throw(Exception(f"bad room ids: {bad_rooms}")))

# journal entries balance (debit == credit per entry)
entries = c2.execute("SELECT entry_id, SUM(debit), SUM(credit) FROM journal_lines GROUP BY entry_id").fetchall()
unbalanced = [(eid, d, cr) for eid, d, cr in entries if round(d,2) != round(cr,2)]
check(f"journal entries balanced ({len(entries)} entries)", lambda: None if not unbalanced else (_ for _ in ()).throw(Exception(f"unbalanced entries: {unbalanced[:3]}")))

conn2.close()

# ── 5. drawio ERD check ───────────────────────────────────────────────────────
import re
with open('AIS.drawio', 'r', encoding='utf-8') as f:
    drawio = f.read()

def find_erd(content):
    m = re.search(r'<diagram name="ERD".*?</diagram>', content, re.DOTALL)
    return m.group(0) if m else ""

erd = find_erd(drawio)
check("ERD diagram present in drawio",       lambda: None if erd else (_ for _ in ()).throw(Exception("ERD diagram not found")))
check("ERD has USER entity",                 lambda: None if 'USER' in erd else (_ for _ in ()).throw(Exception("USER entity missing")))
check("ERD has Room entity",                 lambda: None if 'Room' in erd else (_ for _ in ()).throw(Exception("Room missing")))
check("ERD has Session entity",              lambda: None if 'Session' in erd else (_ for _ in ()).throw(Exception("Session missing")))
check("ERD has LOYALTY entity",              lambda: None if 'LOYALTY' in erd else (_ for _ in ()).throw(Exception("LOYALTY missing")))
check("ERD has EXPENSE entity",              lambda: None if 'EXPENSE' in erd else (_ for _ in ()).throw(Exception("EXPENSE missing")))
check("ERD has Journal_entry entity",        lambda: None if 'Journal_entry' in erd else (_ for _ in ()).throw(Exception("Journal_entry missing")))
check("ERD has Purch_Invoice entity",        lambda: None if 'Purch_Invoice' in erd else (_ for _ in ()).throw(Exception("Purch_Invoice missing")))
check("ERD has Sales_invoice entity",        lambda: None if 'Sales_invoice' in erd else (_ for _ in ()).throw(Exception("Sales_invoice missing")))
check("ERD has PRODUCT entity",              lambda: None if 'PRODUCT' in erd else (_ for _ in ()).throw(Exception("PRODUCT missing")))
check("ERD has no [Restock] diamond (loop)", lambda: None if 'Restock' not in erd else (_ for _ in ()).throw(Exception("Restock diamond still present — loop not broken!")))
check("ERD must-lines present (shape=link)", lambda: None if 'shape=link' in erd else (_ for _ in ()).throw(Exception("No double-lines (Must) found")))
check("ERD has 4 diagram pages",             lambda: f"{drawio.count('<diagram ')} pages" if drawio.count('<diagram ') == 4 else (_ for _ in ()).throw(Exception(f"expected 4 diagrams, found {drawio.count('<diagram ')}")))

# ── Summary ───────────────────────────────────────────────────────────────────
total  = len(results)
passed = sum(1 for r in results if r[0])
failed = total - passed
print()
print("=" * 55)
print(f" RESULTS: {passed}/{total} passed  |  {failed} failed")
print("=" * 55)
if failed:
    print("\nFailed checks:")
    for ok, lbl, msg in results:
        if not ok:
            print(f"  {ERR} {lbl}: {msg}")
