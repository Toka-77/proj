import os
import database
from core import AccountingManager, ExpenseManager, PurchaseInvoiceManager, SalesInvoiceManager

print("--- Initializing Test DB ---")
if os.path.exists('ais_hub.db'):
    os.remove('ais_hub.db')
database.init_db()

# 1. Capital Investment: Debit Cash 100,000, Credit Owner Equity 100,000
lines = [
    ('Cash', 100000.0, 0.0),
    ('Owner Equity', 0.0, 100000.0)
]
AccountingManager.create_journal_entry("Initial Capital", lines, "CAP-01", "Owner")
print("1. Capital invested: 100,000")

# 2. Pay Rent Expense: 10,000
ExpenseManager.add_expense('Rent', 10000.0, 'Monthly Rent')
print("2. Rent paid: 10,000")

# 3. Purchase Inventory: 500 (Initially unpaid)
pi_items = [
    {'name': 'Test Item 1', 'qty': 50, 'unit_cost': 10.0, 'selling_price': 15.0, 'category': 'Snacks'}
]
PurchaseInvoiceManager.create_invoice('Test Supplier', pi_items)
print("3. Inventory purchased (unpaid): 500")

conn = database.get_connection()
pi_id = conn.execute("SELECT MAX(id) FROM purchase_invoices").fetchone()[0]
conn.close()

# 4. Pay for the purchased inventory
PurchaseInvoiceManager.mark_paid(pi_id)
print("4. Purchase invoice paid: 500")

# 5. Sell Inventory: 600 (Initially unpaid)
conn = database.get_connection()
sku = conn.execute("SELECT sku FROM products WHERE name='Test Item 1'").fetchone()[0]
conn.close()

si_items = [
    (sku, 40, 15.0)
]
SalesInvoiceManager.create_invoice('Test Customer', si_items)
print("5. Inventory sold (unpaid): 600")

conn = database.get_connection()
si_id = conn.execute("SELECT MAX(id) FROM sales_invoices").fetchone()[0]
conn.close()

# 6. Receive payment for sold inventory
SalesInvoiceManager.mark_paid(si_id)
print("6. Sales invoice paid: 600")


# --- Print Reports ---
print("\n--- Trial Balance ---")
tb = AccountingManager.get_trial_balance()
total_dr = sum(r[1] for r in tb)
total_cr = sum(r[2] for r in tb)
for row in tb:
    if row[1] == 0 and row[2] == 0: continue
    print(f"Account: {row[0]:<20} | Dr: {row[1]:<10.2f} | Cr: {row[2]:<10.2f}")
print(f"Total Dr: {total_dr:.2f} | Total Cr: {total_cr:.2f}")

print("\n--- Income Statement ---")
inc = AccountingManager.get_income_statement()
print("Revenues:")
for r in inc['revenues']:
    if r[1] != 0: print(f"  {r[0]}: {r[1]:.2f}")
print("Expenses:")
for e in inc['expenses']:
    if e[1] != 0: print(f"  {e[0]}: {e[1]:.2f}")
print(f"Net Income: {inc['net_income']:.2f}")

print("\n--- Balance Sheet ---")
bs = AccountingManager.get_balance_sheet()
total_a = sum(a[1] for a in bs.get('Asset', []))
total_l = sum(l[1] for l in bs.get('Liability', []))
total_e = sum(e[1] for e in bs.get('Equity', []))
ni = inc['net_income']

print("Assets:")
for a in bs.get('Asset', []):
    if a[1] != 0: print(f"  {a[0]}: {a[1]:.2f}")
print(f"Total Assets: {total_a:.2f}")

print("Liabilities:")
for l in bs.get('Liability', []):
    if l[1] != 0: print(f"  {l[0]}: {l[1]:.2f}")
print(f"Total Liabilities: {total_l:.2f}")

print("Equity:")
for e in bs.get('Equity', []):
    if e[1] != 0: print(f"  {e[0]}: {e[1]:.2f}")
print(f"  Current Year Net Income: {ni:.2f}")
print(f"Total Equity + Liabilities: {total_l + total_e + ni:.2f}")

if abs(total_a - (total_l + total_e + ni)) < 0.01:
    print("SUCCESS: Balance Sheet balances correctly!")
else:
    print("WARNING: Balance Sheet does NOT balance!")
