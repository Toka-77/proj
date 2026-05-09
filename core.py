"""
core.py - Business logic layer for the AIS Hub system.
Implements: RoomManager, SessionManager, InventoryManager, ExpenseManager, ReportManager
"""
import hashlib
from database import get_connection
from datetime import datetime


# ────────────────────────────────────────────────────────────────────────────
#  Dynamic Pricing Rules
# ────────────────────────────────────────────────────────────────────────────
PRICING_RULES = {
    'Study':  {'multiplier': 1.0,  'label': 'Standard'},   # cheapest
    'Gaming': {'multiplier': 1.0,  'label': 'Standard'},   # uses base_price directly (already higher)
    'Cinema': {'multiplier': 1.0,  'label': 'Per Person'},  # base_price × num_people
}


def calculate_room_charge(room_type: str, base_price: float, duration_hours: float, num_people: int) -> float:
    """
    Dynamic pricing:
      - Study   → base_price × hours  (flat rate, affordable)
      - Gaming  → base_price × hours  (base_price is already set higher in DB)
      - Cinema  → base_price × hours × num_people  (per-person pricing)
    """
    if room_type == 'Cinema':
        return round(base_price * duration_hours * num_people, 2)
    else:
        return round(base_price * duration_hours, 2)


# ────────────────────────────────────────────────────────────────────────────
#  Room Manager
# ────────────────────────────────────────────────────────────────────────────
class RoomManager:

    @staticmethod
    def get_all_rooms():
        """Returns all rooms: (id, name, type, status, base_price, capacity, description)"""
        conn = get_connection()
        rows = conn.execute("SELECT id, name, type, status, base_price, capacity, description FROM rooms ORDER BY type, name").fetchall()
        conn.close()
        return rows

    @staticmethod
    def get_available_rooms():
        conn = get_connection()
        rows = conn.execute("SELECT id, name, type, base_price, capacity FROM rooms WHERE status='Available' ORDER BY type").fetchall()
        conn.close()
        return rows

    @staticmethod
    def get_room_by_id(room_id):
        conn = get_connection()
        row = conn.execute("SELECT * FROM rooms WHERE id=?", (room_id,)).fetchone()
        conn.close()
        return row

    @staticmethod
    def add_room(name, room_type, base_price, capacity, description=''):
        conn = get_connection()
        conn.execute(
            "INSERT INTO rooms (name, type, base_price, capacity, description) VALUES (?,?,?,?,?)",
            (name, room_type, base_price, capacity, description)
        )
        conn.commit()
        conn.close()
        return True, f"Room '{name}' added."

    @staticmethod
    def update_status(room_id, status):
        conn = get_connection()
        conn.execute("UPDATE rooms SET status=? WHERE id=?", (status, room_id))
        conn.commit()
        conn.close()

    @staticmethod
    def live_status():
        """Returns a dict mapping room_id → {'name','type','status','base_price','capacity'}"""
        rooms = RoomManager.get_all_rooms()
        return {r[0]: {'name': r[1], 'type': r[2], 'status': r[3], 'price': r[4], 'capacity': r[5]} for r in rooms}


# ────────────────────────────────────────────────────────────────────────────
#  Session Manager
# ────────────────────────────────────────────────────────────────────────────
class SessionManager:

    @staticmethod
    def start_session(room_id, customer_name, num_people=1, notes='', deposit=0.0):
        conn = get_connection()
        # Verify room is available
        row = conn.execute("SELECT status FROM rooms WHERE id=?", (room_id,)).fetchone()
        if not row:
            conn.close()
            return None, "Room not found."
        if row[0] == 'Occupied':
            conn.close()
            return None, "Room is already occupied."

        start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cname = (customer_name or '').strip() or 'Walk-in'
        conn.execute(
            "INSERT INTO sessions (room_id, customer_name, num_people, start_time, notes, deposit) VALUES (?,?,?,?,?,?)",
            (room_id, cname, num_people, start_time, notes, deposit)
        )
        conn.execute("UPDATE rooms SET status='Occupied' WHERE id=?", (room_id,))
        conn.commit()
        sid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.close()
        return sid, f"Session #{sid} started for '{cname}'."

    @staticmethod
    def get_active_sessions():
        """
        Returns: (id, room_name, customer_name, start_time, num_people, room_id, room_type, base_price)
        """
        conn = get_connection()
        rows = conn.execute('''
            SELECT s.id, r.name, s.customer_name, s.start_time, s.num_people,
                   r.id, r.type, r.base_price
            FROM sessions s
            JOIN rooms r ON s.room_id = r.id
            WHERE s.end_time IS NULL
            ORDER BY s.start_time
        ''').fetchall()
        conn.close()
        return rows

    @staticmethod
    def get_session_elapsed(session_id):
        """Returns elapsed hours for an active session."""
        conn = get_connection()
        row = conn.execute("SELECT start_time FROM sessions WHERE id=?", (session_id,)).fetchone()
        conn.close()
        if not row:
            return 0.0
        start = datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S')
        return max((datetime.now() - start).total_seconds() / 3600, 0)

    @staticmethod
    def end_session(session_id, discount=0.0, promo_code='', notes=''):
        conn = get_connection()
        row = conn.execute('''
            SELECT s.start_time, s.num_people, r.type, r.base_price, r.id, s.customer_name, s.deposit
            FROM sessions s JOIN rooms r ON s.room_id = r.id
            WHERE s.id = ? AND s.end_time IS NULL
        ''', (session_id,)).fetchone()

        if not row:
            conn.close()
            return False, "Session not found or already closed."

        start_str, num_people, room_type, base_price, room_id, customer_name, deposit = row
        start_dt = datetime.strptime(start_str, '%Y-%m-%d %H:%M:%S')
        end_dt = datetime.now()

        duration_hours = (end_dt - start_dt).total_seconds() / 3600.0
        # Minimum 30 minutes billing
        duration_hours = max(duration_hours, 0.5)

        room_charge = calculate_room_charge(room_type, base_price, duration_hours, num_people)

        # Get linked snacks
        snacks_row = conn.execute(
            "SELECT COALESCE(SUM(total_price),0) FROM sales WHERE session_id=?", (session_id,)
        ).fetchone()
        snacks_total = snacks_row[0] if snacks_row else 0.0

        total_bill = max(room_charge + snacks_total - discount - deposit, 0.0)
        end_str = end_dt.strftime('%Y-%m-%d %H:%M:%S')

        conn.execute('''
            UPDATE sessions
            SET end_time=?, room_charge=?, snacks_total=?, discount=?, promo_code=?, total_bill=?, notes=?
            WHERE id=?
        ''', (end_str, room_charge, snacks_total, discount, promo_code, total_bill, notes, session_id))
        conn.execute("UPDATE rooms SET status='Available' WHERE id=?", (room_id,))
        conn.commit()
        conn.close()

        return True, {
            'session_id':     session_id,
            'duration_hours': duration_hours,
            'room_charge':    room_charge,
            'snacks_total':   snacks_total,
            'deposit':        deposit,
            'discount':       discount,
            'total_bill':     total_bill,
            'room_type':      room_type,
            'num_people':     num_people,
            'customer_name':  customer_name or 'Walk-in',
        }

    @staticmethod
    def get_all_sessions(limit=200):
        conn = get_connection()
        rows = conn.execute('''
            SELECT s.id, r.name, r.type, s.customer_name, s.num_people,
                   s.start_time, s.end_time, s.room_charge, s.snacks_total,
                   s.discount, s.total_bill
            FROM sessions s JOIN rooms r ON s.room_id = r.id
            ORDER BY s.id DESC LIMIT ?
        ''', (limit,)).fetchall()
        conn.close()
        return rows


# ────────────────────────────────────────────────────────────────────────────
#  Inventory Manager
# ────────────────────────────────────────────────────────────────────────────
class InventoryManager:

    @staticmethod
    def get_all_products():
        """Returns (sku, name, category, selling_price, quantity)"""
        conn = get_connection()
        rows = conn.execute(
            "SELECT sku, name, category, unit_cost, selling_price, quantity FROM products ORDER BY category, name"
        ).fetchall()
        conn.close()
        return rows

    @staticmethod
    def get_product_by_sku(sku):
        """Returns (sku, name, category, selling_price, quantity) or None."""
        if not sku: return None
        conn = get_connection()
        row = conn.execute(
            "SELECT sku, name, category, unit_cost, selling_price, quantity FROM products WHERE sku=?",
            (sku.strip(),)
        ).fetchone()
        conn.close()
        return row

    @staticmethod
    def get_product_by_name(name):
        """Case-insensitive exact match by name. Returns row or None."""
        if not name: return None
        conn = get_connection()
        row = conn.execute(
            "SELECT sku, name, category, unit_cost, selling_price, quantity FROM products WHERE LOWER(name)=LOWER(?)",
            (name.strip(),)
        ).fetchone()
        conn.close()
        return row

    @staticmethod
    def search_products(query):
        """Partial name match. Returns list of (sku, name, category, selling_price, quantity)."""
        if not query: return InventoryManager.get_all_products()
        conn = get_connection()
        rows = conn.execute(
            "SELECT sku, name, category, unit_cost, selling_price, quantity FROM products "
            "WHERE LOWER(name) LIKE LOWER(?)",
            (f"%{query.strip()}%",)
        ).fetchall()
        conn.close()
        return rows

    @staticmethod
    def generate_sku():
        """Generate next available SKU in format P001, P002, ..."""
        conn = get_connection()
        rows = conn.execute("SELECT sku FROM products WHERE sku GLOB 'P[0-9]*'").fetchall()
        conn.close()
        max_num = 0
        for (sku,) in rows:
            try:
                n = int(sku[1:])
                if n > max_num: max_num = n
            except ValueError:
                pass
        return f"P{max_num + 1:03d}"

    @staticmethod
    def update_selling_price(sku, new_price):
        conn = get_connection()
        conn.execute("UPDATE products SET selling_price=? WHERE sku=?", (new_price, sku))
        conn.commit()
        conn.close()
        return True, "Price updated."

    @staticmethod
    def delete_product(sku):
        """Delete a product by SKU. Fails if it has invoice history."""
        conn = get_connection()
        # Safety check: any invoice items referencing this SKU?
        si = conn.execute("SELECT COUNT(*) FROM sales_invoice_items WHERE product_sku=?", (sku,)).fetchone()[0]
        pi = conn.execute("SELECT COUNT(*) FROM purchase_invoice_items WHERE product_sku=?", (sku,)).fetchone()[0]
        if si + pi > 0:
            conn.close()
            return False, f"Cannot delete: product has {si+pi} invoice record(s). Archive it instead."
        conn.execute("DELETE FROM products WHERE sku=?", (sku,))
        conn.commit()
        conn.close()
        return True, f"Product '{sku}' deleted."

    @staticmethod
    def get_low_stock(threshold=10):
        conn = get_connection()
        rows = conn.execute(
            "SELECT sku, name, category, quantity FROM products WHERE quantity <= ?",
            (threshold,)
        ).fetchall()
        conn.close()
        return rows

    @staticmethod
    def sell_product(product_sku, quantity, session_id=None):
        """Deduct stock and record sale. Used for session-linked snack sales."""
        conn = get_connection()
        row = conn.execute(
            "SELECT name, quantity, selling_price FROM products WHERE sku=?", (product_sku,)
        ).fetchone()
        if not row:
            conn.close(); return False, "Product not found."
        name, stock, price = row
        if stock < quantity:
            conn.close(); return False, f"Not enough stock. Available: {stock}"
        total_price = round(price * quantity, 2)
        sale_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        conn.execute("UPDATE products SET quantity = quantity - ? WHERE sku=?", (quantity, product_sku))
        conn.execute(
            "INSERT INTO sales (product_sku, session_id, qty_sold, unit_price, total_price, sale_time) "
            "VALUES (?,?,?,?,?,?)",
            (product_sku, session_id, quantity, price, total_price, sale_time)
        )
        conn.commit(); conn.close()
        return True, f"Sold {quantity}× {name} → {total_price:.2f} EGP"


    @staticmethod
    def get_recent_sales(limit=100):
        conn = get_connection()
        rows = conn.execute('''
            SELECT sa.id, p.name, sa.qty_sold, sa.unit_price, sa.total_price, sa.sale_time,
                   COALESCE(s.customer_name, 'Direct Sale') as customer
            FROM sales sa
            JOIN products p ON sa.product_sku = p.sku
            LEFT JOIN sessions s ON sa.session_id = s.id
            ORDER BY sa.sale_time DESC LIMIT ?
        ''', (limit,)).fetchall()
        conn.close()
        return rows


# ────────────────────────────────────────────────────────────────────────────
#  Expense Manager
# ────────────────────────────────────────────────────────────────────────────
class ExpenseManager:

    CATEGORIES = ['Rent', 'Electricity', 'Water', 'Internet', 'Maintenance', 'Salaries', 'Supplies', 'Other']

    @staticmethod
    def add_expense(category, amount, description=''):
        conn = get_connection()
        date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        conn.execute(
            "INSERT INTO expenses (category, amount, date, description) VALUES (?,?,?,?)",
            (category, amount, date, description)
        )
        
        # Map category to GL account
        account = 'Other Expenses'
        if category == 'Rent': account = 'Rent Expense'
        elif category in ['Electricity', 'Water', 'Internet']: account = 'Utilities Expense'
        elif category == 'Salaries': account = 'Salaries Expense'
        elif category == 'Supplies': account = 'Supplies Expense'

        conn.execute("INSERT INTO journal_entries (entry_date, description, reference) VALUES (?,?,?)",
                     (date, f"Expense: {category} - {description}", "EXP"))
        je_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute("INSERT INTO journal_lines (entry_id, account, debit, credit) VALUES (?,?,?,?)",
                     (je_id, account, amount, 0))
        conn.execute("INSERT INTO journal_lines (entry_id, account, debit, credit) VALUES (?,?,?,?)",
                     (je_id, 'Cash', 0, amount))
        
        conn.commit()
        conn.close()
        return True, f"Expense of {amount:.2f} EGP added under '{category}'."

    @staticmethod
    def get_all_expenses():
        conn = get_connection()
        rows = conn.execute(
            "SELECT id, category, amount, date, description FROM expenses ORDER BY date DESC"
        ).fetchall()
        conn.close()
        return rows

    @staticmethod
    def get_total_expenses():
        conn = get_connection()
        val = conn.execute("SELECT COALESCE(SUM(amount),0) FROM expenses").fetchone()[0]
        conn.close()
        return val

    @staticmethod
    def delete_expense(expense_id):
        conn = get_connection()
        conn.execute("DELETE FROM expenses WHERE id=?", (expense_id,))
        conn.commit()
        conn.close()
        return True, "Expense deleted."


# ────────────────────────────────────────────────────────────────────────────
#  Report Manager
# ────────────────────────────────────────────────────────────────────────────
class ReportManager:

    @staticmethod
    def generate_report():
        conn = get_connection()

        # Revenue per room type (Segment Reporting)
        rev_type = dict(conn.execute('''
            SELECT r.type, COALESCE(SUM(s.room_charge), 0)
            FROM sessions s JOIN rooms r ON s.room_id = r.id
            WHERE s.end_time IS NOT NULL
            GROUP BY r.type
        ''').fetchall())

        # Ensure all types appear
        for t in ('Study', 'Gaming', 'Cinema'):
            rev_type.setdefault(t, 0.0)

        total_room_rev = sum(rev_type.values())

        # Snacks revenue (closed sessions + direct)
        snacks_rev = conn.execute('''
            SELECT COALESCE(SUM(sa.total_price), 0)
            FROM sales sa
            WHERE sa.session_id IS NULL
               OR sa.session_id IN (SELECT id FROM sessions WHERE end_time IS NOT NULL)
        ''').fetchone()[0]

        # Total discounts
        total_disc = conn.execute(
            "SELECT COALESCE(SUM(discount), 0) FROM sessions WHERE end_time IS NOT NULL"
        ).fetchone()[0]

        total_revenue = total_room_rev + snacks_rev - total_disc

        # Expenses
        total_exp = conn.execute("SELECT COALESCE(SUM(amount), 0) FROM expenses").fetchone()[0]

        profit = total_revenue - total_exp

        # Most used room (by session count)
        mu = conn.execute('''
            SELECT r.name, COUNT(s.id) as cnt
            FROM sessions s JOIN rooms r ON s.room_id = r.id
            GROUP BY r.id ORDER BY cnt DESC LIMIT 1
        ''').fetchone()
        most_used = mu[0] if mu else 'No Data'
        most_used_count = mu[1] if mu else 0

        # Revenue per room name
        rev_room = dict(conn.execute('''
            SELECT r.name, COALESCE(SUM(s.room_charge), 0)
            FROM sessions s JOIN rooms r ON s.room_id = r.id
            WHERE s.end_time IS NOT NULL
            GROUP BY r.id ORDER BY SUM(s.room_charge) DESC
        ''').fetchall())

        # Sessions count
        total_sessions = conn.execute("SELECT COUNT(*) FROM sessions WHERE end_time IS NOT NULL").fetchone()[0]
        active_sessions = conn.execute("SELECT COUNT(*) FROM sessions WHERE end_time IS NULL").fetchone()[0]

        # Inventory value
        inv_value = conn.execute("SELECT COALESCE(SUM(quantity*selling_price),0) FROM products").fetchone()[0]

        # Products sold today
        today = datetime.now().strftime('%Y-%m-%d')
        sold_today = conn.execute(
            "SELECT COALESCE(SUM(total_price),0) FROM sales WHERE sale_time LIKE ?", (f"{today}%",)
        ).fetchone()[0]

        conn.close()

        return {
            'revenue_per_type':   rev_type,
            'revenue_per_room':   rev_room,
            'total_room_revenue': total_room_rev,
            'snacks_revenue':     snacks_rev,
            'total_discounts':    total_disc,
            'total_revenue':      total_revenue,
            'total_expenses':     total_exp,
            'profit':             profit,
            'most_used_room':     most_used,
            'most_used_count':    most_used_count,
            'total_sessions':     total_sessions,
            'active_sessions':    active_sessions,
            'inventory_value':    inv_value,
            'snacks_today':       sold_today,
        }

    @staticmethod
    def get_today_revenue():
        """Total revenue collected today (sessions + sales invoices paid)."""
        conn = get_connection()
        today = datetime.now().strftime('%Y-%m-%d')
        room_rev = conn.execute(
            "SELECT COALESCE(SUM(total_bill),0) FROM sessions WHERE end_time LIKE ?", (f"{today}%",)
        ).fetchone()[0]
        snacks_rev = conn.execute(
            "SELECT COALESCE(SUM(total_price),0) FROM sales WHERE sale_time LIKE ?", (f"{today}%",)
        ).fetchone()[0]
        inv_rev = conn.execute(
            "SELECT COALESCE(SUM(total_amount),0) FROM sales_invoices WHERE invoice_date LIKE ? AND status='Paid'",
            (f"{today}%",)
        ).fetchone()[0]
        conn.close()
        return room_rev + snacks_rev + inv_rev

    @staticmethod
    def get_monthly_revenue():
        """Total revenue for current month."""
        conn = get_connection()
        month = datetime.now().strftime('%Y-%m')
        room_rev = conn.execute(
            "SELECT COALESCE(SUM(total_bill),0) FROM sessions WHERE end_time LIKE ?", (f"{month}%",)
        ).fetchone()[0]
        snacks_rev = conn.execute(
            "SELECT COALESCE(SUM(total_price),0) FROM sales WHERE sale_time LIKE ?", (f"{month}%",)
        ).fetchone()[0]
        inv_rev = conn.execute(
            "SELECT COALESCE(SUM(total_amount),0) FROM sales_invoices WHERE invoice_date LIKE ?",
            (f"{month}%",)
        ).fetchone()[0]
        conn.close()
        return room_rev + snacks_rev + inv_rev

    @staticmethod
    def get_outstanding_receivables():
        """Total unpaid sales invoices."""
        conn = get_connection()
        val = conn.execute(
            "SELECT COALESCE(SUM(total_amount),0) FROM sales_invoices WHERE status != 'Paid'"
        ).fetchone()[0]
        conn.close()
        return val

    @staticmethod
    def get_recent_activities(limit=10):
        """Returns recent activities across sessions, sales, expenses."""
        conn = get_connection()
        rows = []
        # Closed sessions
        sessions = conn.execute('''
            SELECT s.end_time, '🏠 Session Closed', r.name || ' - ' || s.customer_name,
                   s.total_bill
            FROM sessions s JOIN rooms r ON s.room_id = r.id
            WHERE s.end_time IS NOT NULL
            ORDER BY s.end_time DESC LIMIT ?
        ''', (limit,)).fetchall()
        rows.extend(sessions)
        # Sales invoices
        invoices = conn.execute('''
            SELECT invoice_date, '🧾 Sales Invoice', customer_name, total_amount
            FROM sales_invoices ORDER BY invoice_date DESC LIMIT ?
        ''', (limit,)).fetchall()
        rows.extend(invoices)
        # Expenses
        expenses = conn.execute('''
            SELECT date, '💸 Expense', category || ' - ' || description, amount
            FROM expenses ORDER BY date DESC LIMIT ?
        ''', (limit,)).fetchall()
        rows.extend(expenses)
        conn.close()
        # Sort all by date desc, take top N
        rows.sort(key=lambda x: x[0] or '', reverse=True)
        return rows[:limit]


# ────────────────────────────────────────────────────────────────────────────
#  Sales Invoice Manager
# ────────────────────────────────────────────────────────────────────────────
class SalesInvoiceManager:

    @staticmethod
    def get_customers():
        conn = get_connection()
        rows = conn.execute("SELECT id, name FROM customers ORDER BY name").fetchall()
        conn.close()
        return rows

    @staticmethod
    def create_invoice(customer_name, items, notes='', session_id=None):
        """
        Create a sales invoice and deduct stock.
        items = list of (product_sku, quantity, unit_price)
        session_id: optional - links this sale to an active room session.
        """
        conn = get_connection()
        date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        total = sum(q * p for _, q, p in items)
        conn.execute(
            "INSERT INTO sales_invoices (customer_name, invoice_date, total_amount, notes) VALUES (?,?,?,?)",
            (customer_name, date, total, notes)
        )
        inv_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        for psku, qty, price in items:
            c_row = conn.execute("SELECT unit_cost FROM products WHERE sku=?", (psku,)).fetchone()
            unit_cost = c_row[0] if c_row else 0.0
            sold_below = bool(price < unit_cost)

            conn.execute(
                "INSERT INTO sales_invoice_items (invoice_id, product_sku, quantity, unit_price, total, sold_below_cost) VALUES (?,?,?,?,?,?)",
                (inv_id, psku, qty, price, qty * price, sold_below)
            )
            conn.execute("UPDATE products SET quantity = quantity - ? WHERE sku=?", (qty, psku))
            conn.execute(
                "INSERT INTO sales (product_sku, session_id, qty_sold, unit_price, total_price, sale_time, sold_below_cost) "
                "VALUES (?,?,?,?,?,?,?)",
                (psku, session_id, qty, price, round(qty * price, 2), date, sold_below)
            )
        conn.execute(
            "INSERT INTO journal_entries (entry_date, description, reference) VALUES (?,?,?)",
            (date, f"Sales Invoice #{inv_id} - {customer_name}", f"SI-{inv_id}")
        )
        je_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute("INSERT INTO journal_lines (entry_id, account, debit, credit) VALUES (?,?,?,?)",
                     (je_id, 'Accounts Receivable', total, 0))
        conn.execute("INSERT INTO journal_lines (entry_id, account, debit, credit) VALUES (?,?,?,?)",
                     (je_id, 'Sales Revenue', 0, total))
                     
        # Calculate Total Cost of Goods Sold
        total_cogs = 0.0
        for psku, qty, _ in items:
            c_row = conn.execute("SELECT unit_cost FROM products WHERE sku=?", (psku,)).fetchone()
            if c_row:
                total_cogs += c_row[0] * qty
                
        if total_cogs > 0:
            conn.execute("INSERT INTO journal_lines (entry_id, account, debit, credit) VALUES (?,?,?,?)",
                         (je_id, 'Cost of Goods Sold', total_cogs, 0))
            conn.execute("INSERT INTO journal_lines (entry_id, account, debit, credit) VALUES (?,?,?,?)",
                         (je_id, 'Inventory', 0, total_cogs))
                         
        conn.commit(); conn.close()
        return True, f"Sales Invoice #{inv_id} created - Total: {total:.2f} EGP"

    @staticmethod
    def get_all_invoices():
        conn = get_connection()
        rows = conn.execute(
            "SELECT id, customer_name, invoice_date, total_amount, status FROM sales_invoices ORDER BY id DESC"
        ).fetchall()
        conn.close()
        return rows

    @staticmethod
    def get_invoice_items(invoice_id):
        conn = get_connection()
        rows = conn.execute('''
            SELECT si.id, p.name, si.quantity, si.unit_price, si.total
            FROM sales_invoice_items si JOIN products p ON si.product_sku = p.sku
            WHERE si.invoice_id = ?
        ''', (invoice_id,)).fetchall()
        conn.close()
        return rows

    @staticmethod
    def delete_invoice(invoice_id):
        conn = get_connection()
        conn.execute("DELETE FROM sales_invoice_items WHERE invoice_id=?", (invoice_id,))
        conn.execute("DELETE FROM sales_invoices WHERE id=?", (invoice_id,))
        conn.commit()
        conn.close()
        return True, "Invoice deleted."

    @staticmethod
    def mark_paid(invoice_id):
        conn = get_connection()
        row = conn.execute("SELECT total_amount, customer_name, status FROM sales_invoices WHERE id=?", (invoice_id,)).fetchone()
        if row and row[2] != 'Paid':
            total, customer, _ = row
            date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            conn.execute("UPDATE sales_invoices SET status='Paid' WHERE id=?", (invoice_id,))
            conn.execute("INSERT INTO journal_entries (entry_date, description, reference) VALUES (?,?,?)",
                         (date, f"Payment received for Sales Invoice #{invoice_id} - {customer}", f"PAY-SI-{invoice_id}"))
            je_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            conn.execute("INSERT INTO journal_lines (entry_id, account, debit, credit) VALUES (?,?,?,?)",
                         (je_id, 'Cash', total, 0))
            conn.execute("INSERT INTO journal_lines (entry_id, account, debit, credit) VALUES (?,?,?,?)",
                         (je_id, 'Accounts Receivable', 0, total))
        conn.commit()
        conn.close()


# ────────────────────────────────────────────────────────────────────────────
#  Purchase Invoice Manager
# ────────────────────────────────────────────────────────────────────────────
class PurchaseInvoiceManager:

    @staticmethod
    def get_suppliers():
        conn = get_connection()
        rows = conn.execute("SELECT id, name FROM suppliers ORDER BY name").fetchall()
        conn.close()
        return rows

    @staticmethod
    def create_invoice(supplier_name, items, notes=''):
        """
        items = list of dicts:
          {'name': str, 'qty': int, 'unit_cost': float,
           'selling_price': float (new only), 'category': str (new only)}
        System resolves SKU by name. Creates product if not found.
        """
        conn = get_connection()
        date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        total = sum(it['qty'] * it['unit_cost'] for it in items)
        conn.execute(
            "INSERT INTO purchase_invoices (supplier_name, invoice_date, total_amount, notes) VALUES (?,?,?,?)",
            (supplier_name, date, total, notes)
        )
        inv_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        for it in items:
            name     = it['name'].strip()
            qty      = it['qty']
            cost     = it['unit_cost']

            # Resolve product by name (case-insensitive)
            row = conn.execute(
                "SELECT sku FROM products WHERE LOWER(name)=LOWER(?)", (name,)
            ).fetchone()

            if row:
                sku = row[0]
                conn.execute("UPDATE products SET quantity = quantity + ?, unit_cost = ? WHERE sku=?", (qty, cost, sku))
            else:
                # New product - generate SKU
                existing = conn.execute("SELECT sku FROM products WHERE sku GLOB 'P[0-9]*'").fetchall()
                max_n = max((int(s[1:]) for (s,) in existing if s[1:].isdigit()), default=0)
                sku = f"P{max_n + 1:03d}"
                sell_price = it.get('selling_price', 0.0)
                category   = it.get('category', 'Other')
                conn.execute(
                    "INSERT INTO products (sku, name, category, unit_cost, selling_price, quantity) VALUES (?,?,?,?,?,?)",
                    (sku, name, category, cost, sell_price, qty)
                )

            conn.execute(
                "INSERT INTO purchase_invoice_items "
                "(invoice_id, product_sku, quantity, unit_cost, total) VALUES (?,?,?,?,?)",
                (inv_id, sku, qty, cost, qty * cost)
            )

        conn.execute(
            "INSERT INTO journal_entries (entry_date, description, reference) VALUES (?,?,?)",
            (date, f"Purchase Invoice #{inv_id} - {supplier_name}", f"PI-{inv_id}")
        )
        je_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute("INSERT INTO journal_lines (entry_id, account, debit, credit) VALUES (?,?,?,?)",
                     (je_id, 'Inventory', total, 0))
        conn.execute("INSERT INTO journal_lines (entry_id, account, debit, credit) VALUES (?,?,?,?)",
                     (je_id, 'Accounts Payable', 0, total))
        conn.commit(); conn.close()
        return True, f"Purchase Invoice #{inv_id} created - Total: {total:.2f} EGP"

    @staticmethod
    def get_all_invoices():
        conn = get_connection()
        rows = conn.execute(
            "SELECT id, supplier_name, invoice_date, total_amount, status FROM purchase_invoices ORDER BY id DESC"
        ).fetchall()
        conn.close()
        return rows

    @staticmethod
    def get_invoice_items(invoice_id):
        """Returns (product_name, quantity, unit_cost, total) for each line."""
        conn = get_connection()
        rows = conn.execute('''
            SELECT p.name, pii.quantity, pii.unit_cost, pii.total
            FROM purchase_invoice_items pii
            JOIN products p ON pii.product_sku = p.sku
            WHERE pii.invoice_id = ?
            ORDER BY p.name
        ''', (invoice_id,)).fetchall()
        conn.close()
        return rows

    @staticmethod
    def delete_invoice(invoice_id):
        conn = get_connection()
        conn.execute("DELETE FROM purchase_invoice_items WHERE invoice_id=?", (invoice_id,))
        conn.execute("DELETE FROM purchase_invoices WHERE id=?", (invoice_id,))
        conn.commit()
        conn.close()
        return True, "Invoice deleted."

    @staticmethod
    def mark_paid(invoice_id):
        conn = get_connection()
        row = conn.execute("SELECT total_amount, supplier_name, status FROM purchase_invoices WHERE id=?", (invoice_id,)).fetchone()
        if row and row[2] != 'Paid':
            total, supplier, _ = row
            date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            conn.execute("UPDATE purchase_invoices SET status='Paid' WHERE id=?", (invoice_id,))
            conn.execute("INSERT INTO journal_entries (entry_date, description, reference) VALUES (?,?,?)",
                         (date, f"Payment made for Purchase Invoice #{invoice_id} - {supplier}", f"PAY-PI-{invoice_id}"))
            je_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            conn.execute("INSERT INTO journal_lines (entry_id, account, debit, credit) VALUES (?,?,?,?)",
                         (je_id, 'Accounts Payable', total, 0))
            conn.execute("INSERT INTO journal_lines (entry_id, account, debit, credit) VALUES (?,?,?,?)",
                         (je_id, 'Cash', 0, total))
        conn.commit()
        conn.close()


# ────────────────────────────────────────────────────────────────────────────
#  Accounting Manager
# ────────────────────────────────────────────────────────────────────────────
class AccountingManager:

    @staticmethod
    def get_accounts():
        conn = get_connection()
        rows = conn.execute("SELECT account_code, account_name, account_type FROM chart_of_accounts ORDER BY account_code").fetchall()
        conn.close()
        return rows

    @staticmethod
    def create_journal_entry(description, lines, reference='', entity=''):
        """lines = list of (account_name, debit, credit)"""
        conn = get_connection()
        date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        conn.execute("INSERT INTO journal_entries (entry_date, description, reference, entity) VALUES (?,?,?,?)",
                     (date, description, reference, entity))
        eid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        for acc, dr, cr in lines:
            conn.execute("INSERT INTO journal_lines (entry_id, account, debit, credit) VALUES (?,?,?,?)",
                         (eid, acc, dr, cr))
        conn.commit()
        conn.close()
        return True, f"Journal Entry #{eid} created."

    @staticmethod
    def get_journal_entries():
        conn = get_connection()
        rows = conn.execute('''
            SELECT je.id, je.entry_date, je.description, je.reference, je.entity,
                   COALESCE(SUM(jl.debit),0) as total_debit
            FROM journal_entries je
            LEFT JOIN journal_lines jl ON je.id = jl.entry_id
            GROUP BY je.id ORDER BY je.id DESC
        ''').fetchall()
        conn.close()
        return rows

    @staticmethod
    def get_journal_lines(entry_id):
        conn = get_connection()
        rows = conn.execute("SELECT account, debit, credit FROM journal_lines WHERE entry_id=?", (entry_id,)).fetchall()
        conn.close()
        return rows

    @staticmethod
    def get_general_ledger():
        conn = get_connection()
        rows = conn.execute('''
            SELECT jl.entry_id, jl.account, je.entry_date, je.description,
                   je.entity, jl.debit, jl.credit, je.reference
            FROM journal_lines jl JOIN journal_entries je ON jl.entry_id = je.id
            ORDER BY jl.account, je.entry_date
        ''').fetchall()
        conn.close()
        return rows

    @staticmethod
    def get_trial_balance():
        conn = get_connection()
        rows = conn.execute('''
            SELECT jl.account, SUM(jl.debit) as total_dr, SUM(jl.credit) as total_cr
            FROM journal_lines jl
            GROUP BY jl.account ORDER BY jl.account
        ''').fetchall()
        conn.close()
        return rows

    @staticmethod
    def get_income_statement():
        conn = get_connection()
        # Revenue accounts
        rev = conn.execute('''
            SELECT jl.account, SUM(jl.credit) - SUM(jl.debit) as net
            FROM journal_lines jl
            JOIN chart_of_accounts ca ON jl.account = ca.account_name
            WHERE ca.account_type = 'Revenue'
            GROUP BY jl.account
        ''').fetchall()
        # Expense accounts
        exp = conn.execute('''
            SELECT jl.account, SUM(jl.debit) - SUM(jl.credit) as net
            FROM journal_lines jl
            JOIN chart_of_accounts ca ON jl.account = ca.account_name
            WHERE ca.account_type = 'Expense'
            GROUP BY jl.account
        ''').fetchall()
        # No more manual sys_exp, expenses are handled in journal entries
        conn.close()
        total_rev = sum(r[1] for r in rev)
        total_exp = sum(e[1] for e in exp)
        return {'revenues': rev, 'expenses': exp, 'system_expenses': 0,
                'total_revenue': total_rev, 'total_expenses': total_exp,
                'net_income': total_rev - total_exp}

    @staticmethod
    def get_balance_sheet():
        conn = get_connection()
        result = {}
        for atype in ['Asset', 'Liability', 'Equity']:
            if atype == 'Asset':
                query = "SELECT jl.account, SUM(jl.debit) - SUM(jl.credit) as balance"
            else:
                query = "SELECT jl.account, SUM(jl.credit) - SUM(jl.debit) as balance"
            rows = conn.execute(f'''
                {query}
                FROM journal_lines jl
                JOIN chart_of_accounts ca ON jl.account = ca.account_name
                WHERE ca.account_type = ?
                GROUP BY jl.account
            ''', (atype,)).fetchall()
            result[atype] = rows
        conn.close()
        result['inventory_value'] = 0
        result['cash_balance'] = 0
        return result


# ────────────────────────────────────────────────────────────────────────────
#  Account Statement Manager
# ────────────────────────────────────────────────────────────────────────────
class AccountStatementManager:

    @staticmethod
    def get_customer_statement(customer_name=None):
        conn = get_connection()
        if customer_name:
            rows = conn.execute('''
                SELECT id, customer_name, invoice_date, total_amount, status
                FROM sales_invoices WHERE customer_name = ? ORDER BY invoice_date DESC
            ''', (customer_name,)).fetchall()
        else:
            rows = conn.execute('''
                SELECT id, customer_name, invoice_date, total_amount, status
                FROM sales_invoices ORDER BY customer_name, invoice_date DESC
            ''').fetchall()
        conn.close()
        return rows

    @staticmethod
    def get_customer_balance(customer_name):
        conn = get_connection()
        total = conn.execute(
            "SELECT COALESCE(SUM(total_amount),0) FROM sales_invoices WHERE customer_name=?",
            (customer_name,)).fetchone()[0]
        paid = conn.execute(
            "SELECT COALESCE(SUM(total_amount),0) FROM sales_invoices WHERE customer_name=? AND status='Paid'",
            (customer_name,)).fetchone()[0]
        conn.close()
        return {'total': total, 'paid': paid, 'outstanding': total - paid}

    @staticmethod
    def get_supplier_statement(supplier_name=None):
        conn = get_connection()
        if supplier_name:
            rows = conn.execute('''
                SELECT id, supplier_name, invoice_date, total_amount, status
                FROM purchase_invoices WHERE supplier_name = ? ORDER BY invoice_date DESC
            ''', (supplier_name,)).fetchall()
        else:
            rows = conn.execute('''
                SELECT id, supplier_name, invoice_date, total_amount, status
                FROM purchase_invoices ORDER BY supplier_name, invoice_date DESC
            ''').fetchall()
        conn.close()
        return rows

    @staticmethod
    def get_supplier_balance(supplier_name):
        conn = get_connection()
        total = conn.execute(
            "SELECT COALESCE(SUM(total_amount),0) FROM purchase_invoices WHERE supplier_name=?",
            (supplier_name,)).fetchone()[0]
        paid = conn.execute(
            "SELECT COALESCE(SUM(total_amount),0) FROM purchase_invoices WHERE supplier_name=? AND status='Paid'",
            (supplier_name,)).fetchone()[0]
        conn.close()
        return {'total': total, 'paid': paid, 'outstanding': total - paid}

    @staticmethod
    def get_all_customer_balance():
        conn = get_connection()
        total = conn.execute("SELECT COALESCE(SUM(total_amount),0) FROM sales_invoices").fetchone()[0]
        paid = conn.execute("SELECT COALESCE(SUM(total_amount),0) FROM sales_invoices WHERE status='Paid'").fetchone()[0]
        conn.close()
        return {'total': total, 'paid': paid, 'outstanding': total - paid}

    @staticmethod
    def get_all_supplier_balance():
        conn = get_connection()
        total = conn.execute("SELECT COALESCE(SUM(total_amount),0) FROM purchase_invoices").fetchone()[0]
        paid = conn.execute("SELECT COALESCE(SUM(total_amount),0) FROM purchase_invoices WHERE status='Paid'").fetchone()[0]
        conn.close()
        return {'total': total, 'paid': paid, 'outstanding': total - paid}

    @staticmethod
    def get_all_customer_names():
        conn = get_connection()
        rows = conn.execute("SELECT DISTINCT customer_name FROM sales_invoices ORDER BY customer_name").fetchall()
        names = conn.execute("SELECT name FROM customers ORDER BY name").fetchall()
        conn.close()
        all_names = list(set([r[0] for r in rows] + [n[0] for n in names]))
        all_names.sort()
        return all_names

    @staticmethod
    def get_all_supplier_names():
        conn = get_connection()
        rows = conn.execute("SELECT DISTINCT supplier_name FROM purchase_invoices ORDER BY supplier_name").fetchall()
        names = conn.execute("SELECT name FROM suppliers ORDER BY name").fetchall()
        conn.close()
        all_names = list(set([r[0] for r in rows] + [n[0] for n in names]))
        all_names.sort()
        return all_names


# ────────────────────────────────────────────────────────────────────────────
#  Settings Manager
# ────────────────────────────────────────────────────────────────────────────
class SettingsManager:

    @staticmethod
    def get(key, default=None):
        conn = get_connection()
        row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        conn.close()
        return row[0] if row else default

    @staticmethod
    def set(key, value):
        conn = get_connection()
        conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?,?)", (key, str(value)))
        conn.commit()
        conn.close()

    @staticmethod
    def get_all():
        conn = get_connection()
        rows = conn.execute("SELECT key, value FROM settings").fetchall()
        conn.close()
        return dict(rows)


# ────────────────────────────────────────────────────────────────────────────
#  Notification Manager
# ────────────────────────────────────────────────────────────────────────────
class NotificationManager:
    """Returns a list of (level, message) tuples. level = 'warning'|'danger'|'success'|'info'"""

    _shown = set()   # deduplicate within a session

    @staticmethod
    def check_alerts():
        alerts = []
        threshold = int(SettingsManager.get('low_stock_threshold', '5') or 5)

        # Low stock
        low = InventoryManager.get_low_stock(threshold)
        if low:
            key = f"low_{len(low)}"
            if key not in NotificationManager._shown:
                alerts.append(('warning', f"⚠️  Low Stock", f"{len(low)} products below {threshold} units"))
                NotificationManager._shown.add(key)

        # Long sessions (> alert_hours)
        alert_hrs = float(SettingsManager.get('session_alert_hours', '5') or 5)
        for s in SessionManager.get_active_sessions():
            elapsed = SessionManager.get_session_elapsed(s[0])
            if elapsed >= alert_hrs:
                key = f"sess_{s[0]}_{int(elapsed)}"
                if key not in NotificationManager._shown:
                    alerts.append(('danger', f"⏱  Long Session",
                                   f"{s[2] or 'Walk-in'} running {elapsed:.1f}h in {s[1]}"))
                    NotificationManager._shown.add(key)

        # Unpaid invoices
        unpaid_limit = int(SettingsManager.get('unpaid_invoice_alert', '3') or 3)
        conn = get_connection()
        unpaid = conn.execute("SELECT COUNT(*) FROM sales_invoices WHERE status!='Paid'").fetchone()[0]
        conn.close()
        if unpaid >= unpaid_limit:
            key = f"unpaid_{unpaid}"
            if key not in NotificationManager._shown:
                alerts.append(('warning', f"🧾  Unpaid Invoices", f"{unpaid} sales invoices pending payment"))
                NotificationManager._shown.add(key)

        # Daily revenue target
        target_str = SettingsManager.get('daily_revenue_target', '2000')
        try:
            target = float(target_str)
        except (ValueError, TypeError):
            target = 2000.0
        today_rev = ReportManager.get_today_revenue()
        if target > 0 and today_rev >= target:
            key = f"target_{int(today_rev // target)}"
            if key not in NotificationManager._shown:
                alerts.append(('success', f"🎯  Target Reached!", f"Daily revenue: {today_rev:,.0f} EGP"))
                NotificationManager._shown.add(key)

        return alerts

    @staticmethod
    def reset():
        NotificationManager._shown.clear()


# ────────────────────────────────────────────────────────────────────────────
#  Loyalty Manager
# ────────────────────────────────────────────────────────────────────────────
class LoyaltyManager:

    TIERS = [
        ('Bronze',   0,      0),
        ('Silver',   1000,   5),
        ('Gold',     5000,  10),
        ('Platinum', 10000, 15),
    ]
    TIER_ICONS = {'Bronze': '🥉', 'Silver': '🥈', 'Gold': '🥇', 'Platinum': '💎'}
    TIER_COLORS = {
        'Bronze':   '#cd7f32',
        'Silver':   '#a8a9ad',
        'Gold':     '#ffd700',
        'Platinum': '#b9f2ff',
    }

    @staticmethod
    def get_tier_info(points):
        """Returns (tier_name, discount_pct, next_tier, points_to_next)."""
        tier = 'Bronze'; discount = 0; next_tier = 'Silver'; pts_next = 1000
        for i, (name, threshold, disc) in enumerate(LoyaltyManager.TIERS):
            if points >= threshold:
                tier = name; discount = disc
                if i + 1 < len(LoyaltyManager.TIERS):
                    next_tier = LoyaltyManager.TIERS[i + 1][0]
                    pts_next  = LoyaltyManager.TIERS[i + 1][1] - points
                else:
                    next_tier = None; pts_next = 0
        return tier, discount, next_tier, max(pts_next, 0)

    @staticmethod
    def get_account(customer_name):
        """Returns (customer_name, points, tier, total_spent) or None."""
        conn = get_connection()
        row = conn.execute(
            "SELECT customer_name, points, tier, total_spent FROM loyalty_accounts WHERE customer_name=?",
            (customer_name,)
        ).fetchone()
        conn.close()
        return row

    @staticmethod
    def add_points(customer_name, amount_spent):
        """Award points: 1 EGP = 1 point. Returns (new_points, tier)."""
        rate = int(SettingsManager.get('loyalty_points_rate', '1') or 1)
        points_earned = int(amount_spent * rate)
        conn = get_connection()
        row = conn.execute(
            "SELECT points, total_spent FROM loyalty_accounts WHERE customer_name=?",
            (customer_name,)
        ).fetchone()
        if row:
            new_points = row[0] + points_earned
            new_spent  = row[1] + amount_spent
        else:
            new_points = points_earned
            new_spent  = amount_spent
        tier, _, _, _ = LoyaltyManager.get_tier_info(new_points)
        conn.execute(
            "INSERT OR REPLACE INTO loyalty_accounts (customer_name, points, tier, total_spent) VALUES (?,?,?,?)",
            (customer_name, new_points, tier, new_spent)
        )
        conn.commit(); conn.close()
        return new_points, tier

    @staticmethod
    def redeem_points(customer_name, points_to_redeem):
        """Redeem points for discount. 100 pts = 1 EGP. Returns (True, discount_egp) or (False, msg)."""
        rate = int(SettingsManager.get('loyalty_redeem_rate', '100') or 100)
        conn = get_connection()
        row = conn.execute(
            "SELECT points FROM loyalty_accounts WHERE customer_name=?", (customer_name,)
        ).fetchone()
        if not row or row[0] < points_to_redeem:
            conn.close()
            return False, f"Not enough points. Available: {row[0] if row else 0}"
        new_points = row[0] - points_to_redeem
        tier, _, _, _ = LoyaltyManager.get_tier_info(new_points)
        conn.execute(
            "UPDATE loyalty_accounts SET points=?, tier=? WHERE customer_name=?",
            (new_points, tier, customer_name)
        )
        conn.commit(); conn.close()
        discount_egp = round(points_to_redeem / rate, 2)
        return True, discount_egp

    @staticmethod
    def get_all_accounts():
        """Returns all loyalty accounts ordered by points DESC."""
        conn = get_connection()
        rows = conn.execute(
            "SELECT customer_name, points, tier, total_spent FROM loyalty_accounts ORDER BY points DESC"
        ).fetchall()
        conn.close()
        return rows


# ────────────────────────────────────────────────────────────────────────────
#  Booking Manager
# ────────────────────────────────────────────────────────────────────────────
class BookingManager:

    @staticmethod
    def check_conflict(room_id, date, start_time, end_time, exclude_id=None):
        """Returns True if there's a conflicting booking."""
        conn = get_connection()
        q = """
            SELECT COUNT(*) FROM bookings
            WHERE room_id=? AND booking_date=? AND status='Confirmed'
              AND NOT (end_time <= ? OR start_time >= ?)
        """
        params = [room_id, date, start_time, end_time]
        if exclude_id:
            q += " AND id != ?"
            params.append(exclude_id)
        count = conn.execute(q, params).fetchone()[0]
        conn.close()
        return count > 0

    @staticmethod
    def create_booking(room_id, customer_name, date, start_time, end_time, num_people=1, deposit=0.0, notes=''):
        if deposit <= 0:
            return False, "A deposit is required to confirm the booking."
        if BookingManager.check_conflict(room_id, date, start_time, end_time):
            return False, "Room already booked for this time slot."
        conn = get_connection()
        conn.execute(
            "INSERT INTO bookings (room_id, customer_name, booking_date, start_time, end_time, num_people, deposit, notes)"
            " VALUES (?,?,?,?,?,?,?,?)",
            (room_id, customer_name, date, start_time, end_time, num_people, deposit, notes)
        )
        bk_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.commit(); conn.close()
        
        if deposit > 0:
            lines = [('Cash', deposit, 0.0), ('Unearned Revenue', 0.0, deposit)]
            AccountingManager.create_journal_entry("Booking Deposit", lines, f"BK-{bk_id}", "Booking")
            
        return True, "Booking confirmed."

    @staticmethod
    def get_bookings(date=None, room_id=None):
        conn = get_connection()
        q = """
            SELECT b.id, r.name, b.customer_name, b.booking_date,
                   b.start_time, b.end_time, b.num_people, b.status, b.notes, r.id, b.deposit
            FROM bookings b JOIN rooms r ON b.room_id = r.id
            WHERE 1=1
        """
        params = []
        if date:    q += " AND b.booking_date=?"; params.append(date)
        if room_id: q += " AND b.room_id=?";      params.append(room_id)
        q += " ORDER BY b.booking_date, b.start_time"
        rows = conn.execute(q, params).fetchall()
        conn.close()
        return rows

    @staticmethod
    def cancel_booking(booking_id):
        conn = get_connection()
        conn.execute("UPDATE bookings SET status='Cancelled' WHERE id=?", (booking_id,))
        conn.commit(); conn.close()
        return True, "Booking cancelled."

    @staticmethod
    def convert_to_session(booking_id):
        """Convert a confirmed booking to an active session."""
        conn = get_connection()
        row = conn.execute(
            "SELECT room_id, customer_name, num_people, notes, deposit FROM bookings WHERE id=?", (booking_id,)
        ).fetchone()
        if not row:
            conn.close(); return False, "Booking not found."
        room_id, cname, num_people, notes, deposit = row
        conn.execute("UPDATE bookings SET status='Completed' WHERE id=?", (booking_id,))
        conn.commit(); conn.close()
        sid, msg = SessionManager.start_session(room_id, cname, num_people, notes, deposit)
        return (True, msg) if sid else (False, msg)


# ────────────────────────────────────────────────────────────────────────────
#  PDF Invoice Generator
# ────────────────────────────────────────────────────────────────────────────
class PDFGenerator:

    @staticmethod
    def _check_fpdf():
        try:
            import fpdf
            return True
        except ImportError:
            return False

    @staticmethod
    def generate_sales_invoice(invoice_id):
        """Generate a branded PDF for a sales invoice. Returns (True, path) or (False, msg)."""
        if not PDFGenerator._check_fpdf():
            return False, "fpdf2 not installed. Run: pip install fpdf2"

        from fpdf import FPDF
        import os

        conn = get_connection()
        inv = conn.execute(
            "SELECT id, customer_name, invoice_date, total_amount, status, notes "
            "FROM sales_invoices WHERE id=?", (invoice_id,)
        ).fetchone()
        items = conn.execute("""
            SELECT p.name, si.quantity, si.unit_price, si.total
            FROM sales_invoice_items si JOIN products p ON si.product_sku = p.sku
            WHERE si.invoice_id=?
        """, (invoice_id,)).fetchall()
        conn.close()

        if not inv:
            return False, "Invoice not found."

        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        # ── Header ──
        pdf.set_fill_color(28, 25, 55)
        pdf.rect(0, 0, 210, 40, 'F')
        pdf.set_font('Helvetica', 'B', 22)
        pdf.set_text_color(255, 255, 255)
        pdf.set_xy(10, 8)
        pdf.cell(0, 10, 'AIS HUB - CO-WORKING SPACE', align='L')
        pdf.set_font('Helvetica', '', 10)
        pdf.set_xy(10, 20)
        pdf.cell(0, 8, 'Multi-Activity Accounting Information System', align='L')
        pdf.set_xy(10, 28)
        pdf.cell(0, 8, 'Cairo, Egypt  |  info@aishub.eg  |  +20 100 000 0000', align='L')

        # ── Invoice Title ──
        pdf.set_text_color(30, 30, 60)
        pdf.set_font('Helvetica', 'B', 18)
        pdf.set_xy(130, 45)
        pdf.cell(70, 10, f'INVOICE #{invoice_id:04d}', align='R')
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(100, 100, 120)
        pdf.set_xy(130, 56)
        pdf.cell(70, 6, f'Date: {inv[2][:10]}', align='R')
        pdf.set_xy(130, 62)
        status_color = (30, 180, 100) if inv[4] == 'Paid' else (200, 50, 80)
        pdf.set_text_color(*status_color)
        pdf.set_font('Helvetica', 'B', 10)
        pdf.cell(70, 6, f'Status: {inv[4]}', align='R')

        # ── Bill To ──
        pdf.set_text_color(30, 30, 60)
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_xy(10, 50)
        pdf.cell(0, 8, 'BILL TO:')
        pdf.set_font('Helvetica', '', 11)
        pdf.set_xy(10, 58)
        pdf.cell(0, 6, inv[1])

        # ── Divider ──
        pdf.set_draw_color(180, 180, 200)
        pdf.set_line_width(0.5)
        pdf.line(10, 74, 200, 74)

        # ── Table Header ──
        pdf.set_fill_color(124, 92, 191)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Helvetica', 'B', 10)
        pdf.set_xy(10, 76)
        pdf.cell(90, 8, 'PRODUCT', fill=True)
        pdf.cell(25, 8, 'QTY', align='C', fill=True)
        pdf.cell(35, 8, 'UNIT PRICE', align='R', fill=True)
        pdf.cell(40, 8, 'TOTAL', align='R', fill=True)

        # ── Items ──
        pdf.set_text_color(40, 40, 60)
        pdf.set_font('Helvetica', '', 10)
        y = 84
        for i, (name, qty, unit, total) in enumerate(items):
            pdf.set_fill_color(245, 245, 252) if i % 2 == 0 else pdf.set_fill_color(255, 255, 255)
            pdf.set_xy(10, y)
            pdf.cell(90, 8, str(name)[:40], fill=True)
            pdf.cell(25, 8, str(qty), align='C', fill=True)
            pdf.cell(35, 8, f'{unit:.2f} EGP', align='R', fill=True)
            pdf.cell(40, 8, f'{total:.2f} EGP', align='R', fill=True)
            y += 8

        # ── Total ──
        pdf.set_line_width(0.5)
        pdf.line(10, y + 2, 200, y + 2)
        pdf.set_fill_color(28, 25, 55)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_xy(10, y + 4)
        pdf.cell(150, 10, 'TOTAL AMOUNT', fill=True)
        pdf.cell(40, 10, f'{inv[3]:,.2f} EGP', align='R', fill=True)

        # ── Notes ──
        if inv[5]:
            pdf.set_text_color(100, 100, 120)
            pdf.set_font('Helvetica', 'I', 9)
            pdf.set_xy(10, y + 20)
            pdf.cell(0, 6, f'Notes: {inv[5]}')

        # ── Footer ──
        pdf.set_text_color(150, 150, 170)
        pdf.set_font('Helvetica', 'I', 8)
        pdf.set_xy(10, 275)
        pdf.cell(0, 5, 'Thank you for choosing AIS Hub Co-Working Space!', align='C')

        # ── Save ──
        out_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(out_dir, f'invoice_SI{invoice_id:04d}.pdf')
        pdf.output(path)
        return True, path

    @staticmethod
    def generate_purchase_invoice(invoice_id):
        """Generate a branded PDF for a purchase invoice. Returns (True, path) or (False, msg)."""
        if not PDFGenerator._check_fpdf():
            return False, "fpdf2 not installed. Run: pip install fpdf2"

        from fpdf import FPDF
        import os

        conn = get_connection()
        inv = conn.execute(
            "SELECT id, supplier_name, invoice_date, total_amount, status, notes "
            "FROM purchase_invoices WHERE id=?", (invoice_id,)
        ).fetchone()
        items = conn.execute("""
            SELECT p.name, pii.quantity, pii.unit_cost, pii.total
            FROM purchase_invoice_items pii JOIN products p ON pii.product_sku = p.sku
            WHERE pii.invoice_id=?
        """, (invoice_id,)).fetchall()
        conn.close()

        if not inv:
            return False, "Invoice not found."

        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        # Header
        pdf.set_fill_color(15, 70, 130)
        pdf.rect(0, 0, 210, 40, 'F')
        pdf.set_font('Helvetica', 'B', 22)
        pdf.set_text_color(255, 255, 255)
        pdf.set_xy(10, 8)
        pdf.cell(0, 10, 'AIS HUB - PURCHASE ORDER', align='L')
        pdf.set_font('Helvetica', '', 10)
        pdf.set_xy(10, 20)
        pdf.cell(0, 8, 'Multi-Activity Accounting Information System')
        pdf.set_xy(10, 28)
        pdf.cell(0, 8, 'Cairo, Egypt  |  info@aishub.eg  |  +20 100 000 0000')

        pdf.set_text_color(30, 30, 60)
        pdf.set_font('Helvetica', 'B', 18)
        pdf.set_xy(130, 45)
        pdf.cell(70, 10, f'PO #{invoice_id:04d}', align='R')
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(100, 100, 120)
        pdf.set_xy(130, 56)
        pdf.cell(70, 6, f'Date: {inv[2][:10]}', align='R')
        pdf.set_xy(130, 62)
        status_color = (30, 180, 100) if inv[4] == 'Paid' else (200, 50, 80)
        pdf.set_text_color(*status_color)
        pdf.set_font('Helvetica', 'B', 10)
        pdf.cell(70, 6, f'Status: {inv[4]}', align='R')

        pdf.set_text_color(30, 30, 60)
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_xy(10, 50)
        pdf.cell(0, 8, 'SUPPLIER:')
        pdf.set_font('Helvetica', '', 11)
        pdf.set_xy(10, 58)
        pdf.cell(0, 6, inv[1])

        pdf.set_draw_color(180, 180, 200)
        pdf.line(10, 74, 200, 74)

        pdf.set_fill_color(15, 70, 130)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Helvetica', 'B', 10)
        pdf.set_xy(10, 76)
        pdf.cell(90, 8, 'PRODUCT', fill=True)
        pdf.cell(25, 8, 'QTY', align='C', fill=True)
        pdf.cell(35, 8, 'UNIT COST', align='R', fill=True)
        pdf.cell(40, 8, 'TOTAL', align='R', fill=True)

        pdf.set_text_color(40, 40, 60)
        pdf.set_font('Helvetica', '', 10)
        y = 84
        for i, (name, qty, cost, total) in enumerate(items):
            pdf.set_fill_color(240, 248, 255) if i % 2 == 0 else pdf.set_fill_color(255, 255, 255)
            pdf.set_xy(10, y)
            pdf.cell(90, 8, str(name)[:40], fill=True)
            pdf.cell(25, 8, str(qty), align='C', fill=True)
            pdf.cell(35, 8, f'{cost:.2f} EGP', align='R', fill=True)
            pdf.cell(40, 8, f'{total:.2f} EGP', align='R', fill=True)
            y += 8

        pdf.line(10, y + 2, 200, y + 2)
        pdf.set_fill_color(15, 70, 130)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_xy(10, y + 4)
        pdf.cell(150, 10, 'TOTAL AMOUNT', fill=True)
        pdf.cell(40, 10, f'{inv[3]:,.2f} EGP', align='R', fill=True)

        pdf.set_text_color(150, 150, 170)
        pdf.set_font('Helvetica', 'I', 8)
        pdf.set_xy(10, 275)
        pdf.cell(0, 5, 'AIS Hub -- Accounting Information System  |  Generated automatically', align='C')

        out_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(out_dir, f'invoice_PI{invoice_id:04d}.pdf')
        pdf.output(path)
        return True, path


# ────────────────────────────────────────────────────────────────────────────
#  User Manager — Login / RBAC
# ────────────────────────────────────────────────────────────────────────────
class UserManager:

    @staticmethod
    def _hash(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    @staticmethod
    def login(username: str, password: str):
        """Returns user dict {id, username, full_name, role} or None."""
        pw_hash = UserManager._hash(password)
        conn = get_connection()
        row = conn.execute(
            "SELECT id, username, full_name, role FROM users "
            "WHERE username=? AND password_hash=? AND is_active=1",
            (username, pw_hash)
        ).fetchone()
        conn.close()
        if row:
            return {'id': row[0], 'username': row[1], 'full_name': row[2], 'role': row[3]}
        return None

    @staticmethod
    def get_all_users():
        conn = get_connection()
        rows = conn.execute(
            "SELECT id, username, full_name, role, is_active FROM users ORDER BY role, username"
        ).fetchall()
        conn.close()
        return rows

    @staticmethod
    def add_user(username, password, full_name, role):
        pw_hash = UserManager._hash(password)
        conn = get_connection()
        try:
            conn.execute(
                "INSERT INTO users (username, password_hash, full_name, role) VALUES (?,?,?,?)",
                (username, pw_hash, full_name, role)
            )
            conn.commit()
            conn.close()
            return True, f"User '{username}' created."
        except Exception as e:
            conn.close()
            return False, str(e)

    @staticmethod
    def change_password(username, new_password):
        pw_hash = UserManager._hash(new_password)
        conn = get_connection()
        conn.execute("UPDATE users SET password_hash=? WHERE username=?", (pw_hash, username))
        conn.commit()
        conn.close()
        return True, "Password updated."
