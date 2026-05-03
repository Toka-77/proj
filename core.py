"""
core.py — Business logic layer for the AIS Hub system.
Implements: RoomManager, SessionManager, InventoryManager, ExpenseManager, ReportManager
"""
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
    def start_session(room_id, customer_name, num_people=1, notes=''):
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
            "INSERT INTO sessions (room_id, customer_name, num_people, start_time, notes) VALUES (?,?,?,?,?)",
            (room_id, cname, num_people, start_time, notes)
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
            SELECT s.start_time, s.num_people, r.type, r.base_price, r.id
            FROM sessions s JOIN rooms r ON s.room_id = r.id
            WHERE s.id = ? AND s.end_time IS NULL
        ''', (session_id,)).fetchone()

        if not row:
            conn.close()
            return False, "Session not found or already closed."

        start_str, num_people, room_type, base_price, room_id = row
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

        total_bill = max(room_charge + snacks_total - discount, 0.0)
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
            'discount':       discount,
            'total_bill':     total_bill,
            'room_type':      room_type,
            'num_people':     num_people,
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
        conn = get_connection()
        rows = conn.execute(
            "SELECT id, name, category, quantity, price, cost_price, low_stock_alert FROM products ORDER BY category, name"
        ).fetchall()
        conn.close()
        return rows

    @staticmethod
    def add_product(name, category, quantity, price, cost_price=0.0, low_stock_alert=5):
        conn = get_connection()
        conn.execute(
            "INSERT INTO products (name, category, quantity, price, cost_price, low_stock_alert) VALUES (?,?,?,?,?,?)",
            (name, category, quantity, price, cost_price, low_stock_alert)
        )
        conn.commit()
        conn.close()
        return True, f"Product '{name}' added."

    @staticmethod
    def restock(product_id, qty):
        conn = get_connection()
        conn.execute("UPDATE products SET quantity = quantity + ? WHERE id=?", (qty, product_id))
        conn.commit()
        conn.close()
        return True, f"Added {qty} units."

    @staticmethod
    def sell_product(product_id, quantity, session_id=None):
        conn = get_connection()
        row = conn.execute("SELECT name, quantity, price FROM products WHERE id=?", (product_id,)).fetchone()
        if not row:
            conn.close()
            return False, "Product not found."
        name, stock, price = row
        if stock < quantity:
            conn.close()
            return False, f"Not enough stock. Available: {stock}"

        total_price = round(price * quantity, 2)
        sale_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        conn.execute("UPDATE products SET quantity = quantity - ? WHERE id=?", (quantity, product_id))
        conn.execute(
            "INSERT INTO sales (product_id, session_id, qty_sold, unit_price, total_price, sale_time) VALUES (?,?,?,?,?,?)",
            (product_id, session_id, quantity, price, total_price, sale_time)
        )
        conn.commit()
        conn.close()
        return True, f"Sold {quantity}× {name}  →  {total_price:.2f} EGP"

    @staticmethod
    def get_low_stock():
        conn = get_connection()
        rows = conn.execute(
            "SELECT id, name, quantity, low_stock_alert FROM products WHERE quantity <= low_stock_alert"
        ).fetchall()
        conn.close()
        return rows

    @staticmethod
    def get_recent_sales(limit=100):
        conn = get_connection()
        rows = conn.execute('''
            SELECT sa.id, p.name, sa.qty_sold, sa.unit_price, sa.total_price, sa.sale_time,
                   COALESCE(s.customer_name, 'Direct Sale') as customer
            FROM sales sa
            JOIN products p ON sa.product_id = p.id
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
        most_used = mu[0] if mu else '—'
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
        inv_value = conn.execute("SELECT COALESCE(SUM(quantity*price),0) FROM products").fetchone()[0]

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
    def create_invoice(customer_name, items, notes=''):
        """items = list of (product_id, quantity, unit_price)"""
        conn = get_connection()
        date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        total = sum(q * p for _, q, p in items)
        conn.execute(
            "INSERT INTO sales_invoices (customer_name, invoice_date, total_amount, notes) VALUES (?,?,?,?)",
            (customer_name, date, total, notes)
        )
        inv_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        for pid, qty, price in items:
            conn.execute(
                "INSERT INTO sales_invoice_items (invoice_id, product_id, quantity, unit_price, total) VALUES (?,?,?,?,?)",
                (inv_id, pid, qty, price, qty * price)
            )
            # Deduct stock
            conn.execute("UPDATE products SET quantity = quantity - ? WHERE id=?", (qty, pid))
        # Auto journal entry: Debit Accounts Receivable, Credit Sales Revenue
        conn.execute(
            "INSERT INTO journal_entries (entry_date, description, reference) VALUES (?,?,?)",
            (date, f"Sales Invoice #{inv_id} - {customer_name}", f"SI-{inv_id}")
        )
        je_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute("INSERT INTO journal_lines (entry_id, account, debit, credit) VALUES (?,?,?,?)",
                     (je_id, 'Accounts Receivable', total, 0))
        conn.execute("INSERT INTO journal_lines (entry_id, account, debit, credit) VALUES (?,?,?,?)",
                     (je_id, 'Sales Revenue', 0, total))
        conn.commit()
        conn.close()
        return True, f"Sales Invoice #{inv_id} created — Total: {total:.2f} EGP"

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
            FROM sales_invoice_items si JOIN products p ON si.product_id = p.id
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
        conn.execute("UPDATE sales_invoices SET status='Paid' WHERE id=?", (invoice_id,))
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
        """items = list of (product_id, quantity, unit_price)"""
        conn = get_connection()
        date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        total = sum(q * p for _, q, p in items)
        conn.execute(
            "INSERT INTO purchase_invoices (supplier_name, invoice_date, total_amount, notes) VALUES (?,?,?,?)",
            (supplier_name, date, total, notes)
        )
        inv_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        for pid, qty, price in items:
            conn.execute(
                "INSERT INTO purchase_invoice_items (invoice_id, product_id, quantity, unit_price, total) VALUES (?,?,?,?,?)",
                (inv_id, pid, qty, price, qty * price)
            )
            # Add to stock
            conn.execute("UPDATE products SET quantity = quantity + ? WHERE id=?", (qty, pid))
        # Auto journal entry: Debit Inventory, Credit Accounts Payable
        conn.execute(
            "INSERT INTO journal_entries (entry_date, description, reference) VALUES (?,?,?)",
            (date, f"Purchase Invoice #{inv_id} - {supplier_name}", f"PI-{inv_id}")
        )
        je_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute("INSERT INTO journal_lines (entry_id, account, debit, credit) VALUES (?,?,?,?)",
                     (je_id, 'Inventory', total, 0))
        conn.execute("INSERT INTO journal_lines (entry_id, account, debit, credit) VALUES (?,?,?,?)",
                     (je_id, 'Accounts Payable', 0, total))
        conn.commit()
        conn.close()
        return True, f"Purchase Invoice #{inv_id} created — Total: {total:.2f} EGP"

    @staticmethod
    def get_all_invoices():
        conn = get_connection()
        rows = conn.execute(
            "SELECT id, supplier_name, invoice_date, total_amount, status FROM purchase_invoices ORDER BY id DESC"
        ).fetchall()
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
        conn.execute("UPDATE purchase_invoices SET status='Paid' WHERE id=?", (invoice_id,))
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
    def create_journal_entry(description, lines, reference=''):
        """lines = list of (account_name, debit, credit)"""
        conn = get_connection()
        date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        conn.execute("INSERT INTO journal_entries (entry_date, description, reference) VALUES (?,?,?)",
                     (date, description, reference))
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
            SELECT je.id, je.entry_date, je.description, je.reference,
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
            SELECT jl.account, je.entry_date, je.description, jl.debit, jl.credit, je.reference
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
        # Also include system expenses
        sys_exp = conn.execute("SELECT COALESCE(SUM(amount),0) FROM expenses").fetchone()[0]
        conn.close()
        total_rev = sum(r[1] for r in rev)
        total_exp = sum(e[1] for e in exp) + sys_exp
        return {'revenues': rev, 'expenses': exp, 'system_expenses': sys_exp,
                'total_revenue': total_rev, 'total_expenses': total_exp,
                'net_income': total_rev - total_exp}

    @staticmethod
    def get_balance_sheet():
        conn = get_connection()
        result = {}
        for atype in ['Asset', 'Liability', 'Equity']:
            rows = conn.execute('''
                SELECT jl.account, SUM(jl.debit) - SUM(jl.credit) as balance
                FROM journal_lines jl
                JOIN chart_of_accounts ca ON jl.account = ca.account_name
                WHERE ca.account_type = ?
                GROUP BY jl.account
            ''', (atype,)).fetchall()
            result[atype] = rows
        # Add inventory value as asset
        inv_val = conn.execute("SELECT COALESCE(SUM(quantity*cost_price),0) FROM products").fetchone()[0]
        # Add cash from paid invoices
        cash_in = conn.execute("SELECT COALESCE(SUM(total_amount),0) FROM sales_invoices WHERE status='Paid'").fetchone()[0]
        cash_out = conn.execute("SELECT COALESCE(SUM(total_amount),0) FROM purchase_invoices WHERE status='Paid'").fetchone()[0]
        sys_exp = conn.execute("SELECT COALESCE(SUM(amount),0) FROM expenses").fetchone()[0]
        conn.close()
        result['inventory_value'] = inv_val
        result['cash_balance'] = cash_in - cash_out - sys_exp
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
