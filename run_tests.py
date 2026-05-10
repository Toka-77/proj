"""
run_tests.py - Comprehensive automated test suite for AIS Hub.
Tests every manager and business logic function without opening the GUI.
"""
import sys, os, traceback, shutil
sys.path.insert(0, os.path.dirname(__file__))

# ── Use a TEMP database so we don't corrupt real data ──────────────────────
import database
ORIG_DB = database.DB_PATH
TEST_DB = os.path.join(os.path.dirname(__file__), '_test_ais.db')
database.DB_PATH = TEST_DB
if os.path.exists(TEST_DB):
    os.remove(TEST_DB)
database.init_db()

from core import (
    RoomManager, SessionManager, InventoryManager, ExpenseManager,
    SalesInvoiceManager, PurchaseInvoiceManager, AccountingManager,
    ReportManager, BookingManager, LoyaltyManager, SettingsManager,
    calculate_room_charge
)

PASS = 0
FAIL = 0
ERRORS = []

def check(label, condition, detail=""):
    global PASS, FAIL
    if condition:
        print(f"  ✅  {label}")
        PASS += 1
    else:
        print(f"  ❌  {label}  {detail}")
        FAIL += 1
        ERRORS.append(f"{label}: {detail}")

def section(title):
    print(f"\n{'═'*55}")
    print(f"  {title}")
    print(f"{'═'*55}")

# ═══════════════════════════════════════════════════════
section("1. PRICING LOGIC")
# ═══════════════════════════════════════════════════════
check("Study 20 EGP/hr × 1hr × 1 ppl = 20", calculate_room_charge('Study',20,1,1)==20)
check("Study 20 EGP/hr × 2hr × 1 ppl = 40", calculate_room_charge('Study',20,2,1)==40)
check("Gaming 50 EGP/hr × 1hr × 3 ppl = 50", calculate_room_charge('Gaming',50,1,3)==50)
check("Cinema 35 EGP/hr × 1hr × 2 ppl = 70", calculate_room_charge('Cinema',35,1,2)==70)
check("Cinema 35 EGP/hr × 2hr × 3 ppl = 210", calculate_room_charge('Cinema',35,2,3)==210)

# ═══════════════════════════════════════════════════════
section("2. ROOM MANAGER")
# ═══════════════════════════════════════════════════════
rooms = RoomManager.get_all_rooms()
check("DB has rooms seeded", len(rooms) >= 5)

# Add room
ok, msg = RoomManager.add_room("Test Room X", "Study", 25.0, 8, "Test room")
check("add_room: new room created", ok, msg)
ok2, _ = RoomManager.add_room("Test Room X", "Study", 25.0, 8)
check("add_room: duplicate blocked", not ok2)

rooms2 = RoomManager.get_all_rooms()
test_room = next((r for r in rooms2 if r[1]=="Test Room X"), None)
check("add_room: appears in get_all_rooms", test_room is not None)

if test_room:
    rid = test_room[0]
    RoomManager.update_price(rid, 30.0)
    rooms3 = RoomManager.get_all_rooms()
    updated = next((r for r in rooms3 if r[0]==rid), None)
    check("update_price: price saved in DB", updated and updated[4]==30.0)

# ═══════════════════════════════════════════════════════
section("3. SESSION MANAGER — BILLING")
# ═══════════════════════════════════════════════════════
study_room = next((r for r in RoomManager.get_all_rooms() if r[2]=='Study'), None)
check("Study room available", study_room is not None)

if study_room:
    srid = study_room[0]
    sprice = study_room[4]  # base_price
    
    # Start session
    sid, msg = SessionManager.start_session(srid, "TestCustomer", 1)
    check("start_session: OK", sid is not None, msg)
    
    # Duplicate start (room occupied)
    sid2, msg2 = SessionManager.start_session(srid, "Other", 1)
    check("start_session: occupied room blocked", sid2 is None)
    
    # End session
    ok, res = SessionManager.end_session(sid, discount=0)
    check("end_session: OK", ok, str(res))
    if ok:
        # Min 1 hour billing
        check("1-hr minimum billing enforced", res['duration_hours'] >= 1.0)
        check("room_charge = base_price × hours (Study)", res['room_charge'] == round(sprice * res['duration_hours'], 2))
        check("room becomes Available again", True)  # DB check below
        rooms_after = RoomManager.get_all_rooms()
        r_after = next((r for r in rooms_after if r[0]==srid), None)
        check("Room status=Available after end", r_after and r_after[3]=='Available')

# Test Cinema per-person pricing
cinema_room = next((r for r in RoomManager.get_all_rooms() if r[2]=='Cinema'), None)
if cinema_room:
    crid = cinema_room[0]
    cprice = cinema_room[4]
    csid, _ = SessionManager.start_session(crid, "CinemaTest", 3)
    check("Cinema session started", csid is not None)
    if csid:
        ok, res = SessionManager.end_session(csid)
        expected = round(cprice * res['duration_hours'] * 3, 2)
        check("Cinema charge = price × hrs × people", ok and res['room_charge'] == expected, 
              f"got {res.get('room_charge')} expected {expected}")

# ═══════════════════════════════════════════════════════
section("4. INVENTORY MANAGER")
# ═══════════════════════════════════════════════════════
prods = InventoryManager.get_all_products()
check("Products seeded in DB", len(prods) > 0)

# sell_product session-linked (no COGS journal expected)
if prods:
    p = prods[0]
    sku = p[0]; orig_qty = p[5]
    ok, msg = InventoryManager.sell_product(sku, 1, session_id=None)
    check("sell_product direct: OK", ok, msg)
    after = InventoryManager.get_product_by_sku(sku)
    check("sell_product: stock deducted", after[5] == orig_qty - 1)
    
    # Check COGS journal was created (direct sale)
    conn = database.get_connection()
    cogs_je = conn.execute("SELECT COUNT(*) FROM journal_entries WHERE reference LIKE 'COGS-%'").fetchone()[0]
    conn.close()
    check("sell_product direct: COGS journal created", cogs_je > 0)

# sell_product with session_id (NO cogs journal for session-linked)
conn = database.get_connection()
cogs_before = conn.execute("SELECT COUNT(*) FROM journal_entries WHERE reference LIKE 'COGS-%'").fetchone()[0]
conn.close()
if prods and study_room:
    sku2 = prods[0][0]
    gsid, _ = SessionManager.start_session(study_room[0], "SnackTest", 1)
    if gsid:
        ok2, _ = InventoryManager.sell_product(sku2, 1, session_id=gsid)
        check("sell_product session-linked: OK", ok2)
        conn = database.get_connection()
        cogs_after = conn.execute("SELECT COUNT(*) FROM journal_entries WHERE reference LIKE 'COGS-%'").fetchone()[0]
        conn.close()
        check("sell_product session-linked: NO extra COGS journal", cogs_after == cogs_before)
        SessionManager.end_session(gsid)

# ═══════════════════════════════════════════════════════
section("5. EXPENSE MANAGER")
# ═══════════════════════════════════════════════════════
ok, msg = ExpenseManager.add_expense("Rent", 500.0, "Monthly rent test")
check("add_expense: OK", ok, msg)
exps = ExpenseManager.get_all_expenses()
check("expense appears in list", len(exps) > 0)
total = ExpenseManager.get_total_expenses()
check("get_total_expenses > 0", total > 0)

# Expense journal entry
conn = database.get_connection()
exp_je = conn.execute("SELECT COUNT(*) FROM journal_entries WHERE reference LIKE 'EXP-%'").fetchone()[0]
conn.close()
check("expense creates journal entry", exp_je > 0)

# Delete expense
eid = exps[0][0]
ok2, _ = ExpenseManager.delete_expense(eid)
check("delete_expense: OK", ok2)
exps2 = ExpenseManager.get_all_expenses()
check("expense removed after delete", all(e[0]!=eid for e in exps2))

# ═══════════════════════════════════════════════════════
section("6. SALES INVOICE MANAGER")
# ═══════════════════════════════════════════════════════
prods2 = InventoryManager.get_all_products()
if prods2:
    p2 = prods2[0]
    items = [(p2[0], 2, p2[4])]  # sku, qty, price
    ok, msg = SalesInvoiceManager.create_invoice("Test Customer", items, paid=True)
    check("create_invoice Paid: OK", ok, msg)
    
    invs = SalesInvoiceManager.get_all_invoices()
    check("invoice appears in list", len(invs) > 0)
    
    iid = invs[0][0]
    inv_items = SalesInvoiceManager.get_invoice_items(iid)
    check("get_invoice_items returns 4 cols (name,qty,price,total)", 
          all(len(r)==4 for r in inv_items), str(inv_items[:1]))
    
    # Journal entry created
    conn = database.get_connection()
    si_je = conn.execute("SELECT COUNT(*) FROM journal_entries WHERE reference LIKE 'SI-REV-%'").fetchone()[0]
    conn.close()
    check("sales invoice creates revenue journal", si_je > 0)

    # Unpaid invoice → mark paid
    items2 = [(p2[0], 1, p2[4])]
    ok2, msg2 = SalesInvoiceManager.create_invoice("Test Customer 2", items2, paid=False)
    check("create_invoice Unpaid: OK", ok2, msg2)
    invs2 = SalesInvoiceManager.get_all_invoices()
    iid2 = invs2[0][0]
    SalesInvoiceManager.mark_paid(iid2)
    conn = database.get_connection()
    pay_je = conn.execute("SELECT COUNT(*) FROM journal_entries WHERE reference LIKE 'PAY-SI-%'").fetchone()[0]
    conn.close()
    check("mark_paid creates A/R → Cash journal", pay_je > 0)
    
    # Delete invoice
    ok3, _ = SalesInvoiceManager.delete_invoice(iid)
    check("delete_invoice: OK", ok3)

# ═══════════════════════════════════════════════════════
section("7. PURCHASE INVOICE MANAGER")
# ═══════════════════════════════════════════════════════
items_pi = [{'name': 'Test Snack New', 'qty': 50, 'unit_cost': 5.0, 'selling_price': 10.0, 'category': 'Snacks'}]
ok, msg = PurchaseInvoiceManager.create_invoice("Test Supplier", items_pi, paid=True)
check("create_invoice Purchase Paid: OK", ok, msg)

pi_list = PurchaseInvoiceManager.get_all_invoices()
check("purchase invoice in list", len(pi_list) > 0)
piid = pi_list[0][0]
pi_items = PurchaseInvoiceManager.get_invoice_items(piid)
check("get_invoice_items: has rows", len(pi_items) > 0)

new_prod = InventoryManager.get_product_by_name("Test Snack New")
check("purchase creates new product in inventory", new_prod is not None)
check("purchase adds correct stock qty", new_prod and new_prod[5] == 50)

# Journal: Inventory debit
conn = database.get_connection()
pi_je = conn.execute("SELECT COUNT(*) FROM journal_entries WHERE reference LIKE 'PI-%'").fetchone()[0]
conn.close()
check("purchase invoice creates inventory journal", pi_je > 0)

# Unpaid purchase → mark paid
items_pi2 = [{'name': 'Test Snack 2', 'qty': 10, 'unit_cost': 3.0, 'selling_price': 6.0}]
ok2, _ = PurchaseInvoiceManager.create_invoice("Supplier B", items_pi2, paid=False)
check("create_invoice Purchase Unpaid: OK", ok2)
pi_list2 = PurchaseInvoiceManager.get_all_invoices()
piid2 = pi_list2[0][0]
PurchaseInvoiceManager.mark_paid(piid2)
conn = database.get_connection()
pay_pi = conn.execute("SELECT COUNT(*) FROM journal_entries WHERE reference LIKE 'PAY-PI-%'").fetchone()[0]
conn.close()
check("mark_paid purchase creates A/P → Cash journal", pay_pi > 0)

# ═══════════════════════════════════════════════════════
section("8. ACCOUNTING MANAGER")
# ═══════════════════════════════════════════════════════
# Income Statement
inc = AccountingManager.get_income_statement()
check("income_statement returns revenues list", 'revenues' in inc)
check("income_statement total_revenue >= 0", inc['total_revenue'] >= 0)
check("income_statement total_expenses >= 0", inc['total_expenses'] >= 0)

# Trial Balance
tb = AccountingManager.get_trial_balance()
check("trial_balance returns list", isinstance(tb, list))
# Each entry: (account, debit, credit) with net != 0
if tb:
    check("trial_balance row has 3 columns", all(len(r)==3 for r in tb))

# Balance Sheet
bs = AccountingManager.get_balance_sheet()
check("balance_sheet has Asset/Liability/Equity", 
      all(k in bs for k in ['Asset', 'Liability', 'Equity']))

# Journal Entries
jes = AccountingManager.get_journal_entries()
check("journal entries exist", len(jes) > 0)
je_lines = AccountingManager.get_journal_lines(jes[0][0])
check("journal lines retrievable", isinstance(je_lines, list))

# General Ledger
gl = AccountingManager.get_general_ledger()
check("general ledger has entries", len(gl) > 0)

# Add account
ok, msg = AccountingManager.add_account("Test Expense Account", "Expense")
check("add_account: OK", ok, msg)
ok2, _ = AccountingManager.add_account("Test Expense Account", "Expense")
check("add_account: duplicate blocked", not ok2)

# ═══════════════════════════════════════════════════════
section("9. BOOKING MANAGER")
# ═══════════════════════════════════════════════════════
avail_room = next((r for r in RoomManager.get_all_rooms() if r[3]=='Available'), None)
if avail_room:
    brid = avail_room[0]
    ok, msg = BookingManager.create_booking(brid, "BookTest", "2099-12-31", "10:00", "12:00", 2, deposit=100.0)
    check("create_booking: OK", ok, msg)
    
    bks = BookingManager.get_bookings()
    check("booking appears in list", len(bks) > 0)
    bid = bks[0][0]
    
    # Cancel booking — single connection (no DB lock)
    ok2, _ = BookingManager.cancel_booking(bid)
    check("cancel_booking: no DB lock error", ok2)
    
    bks2 = BookingManager.get_bookings()
    cancelled = next((b for b in bks2 if b[0]==bid), None)
    check("cancel_booking: status=Cancelled", cancelled and cancelled[7]=='Cancelled')
    
    # Create another and convert to session
    ok3, msg3 = BookingManager.create_booking(brid, "ConvertTest", "2099-12-30", "09:00", "11:00", 1, deposit=50.0)
    check("create_booking for conversion: OK", ok3, msg3)
    bks3 = BookingManager.get_bookings()
    bid2 = next((b[0] for b in bks3 if b[7]=='Confirmed'), None)
    if bid2:
        ok4, msg4 = BookingManager.convert_to_session(bid2)
        check("convert_to_session: OK", ok4, msg4)

# ═══════════════════════════════════════════════════════
section("10. LOYALTY MANAGER")
# ═══════════════════════════════════════════════════════
pts, tier = LoyaltyManager.add_points("TestLoyalCustomer", 500)
check("add_points: OK", pts >= 500)
check("tier=Bronze for 500pts", tier == 'Bronze')

pts2, tier2 = LoyaltyManager.add_points("TestLoyalCustomer", 600)
check("add_points cumulative: OK", pts2 >= 1100)
check("tier=Silver at 1100pts", tier2 == 'Silver')

ok_r, disc = LoyaltyManager.redeem_points("TestLoyalCustomer", 100)
check("redeem_points 100 → 1 EGP", ok_r and disc == 1.0)

# Fail redeem more than available
ok_r2, _ = LoyaltyManager.redeem_points("TestLoyalCustomer", 999999)
check("redeem_points: insufficient blocked", not ok_r2)

# ═══════════════════════════════════════════════════════
section("11. SETTINGS MANAGER")
# ═══════════════════════════════════════════════════════
SettingsManager.set("test_key", "test_val")
val = SettingsManager.get("test_key")
check("set/get setting: OK", val == "test_val")
all_s = SettingsManager.get_all()
check("get_all returns dict", isinstance(all_s, dict))

# ═══════════════════════════════════════════════════════
section("12. REPORT MANAGER")
# ═══════════════════════════════════════════════════════
rep = ReportManager.generate_report()
check("generate_report: has all keys", all(k in rep for k in [
    'revenue_per_type','revenue_per_room','total_revenue','total_expenses','profit',
    'most_used_room','total_sessions','active_sessions','snacks_today'
]))
check("report: total_revenue numeric", isinstance(rep['total_revenue'], (int,float)))

today_rev = ReportManager.get_today_revenue()
check("get_today_revenue: numeric", isinstance(today_rev, (int,float)))

month_rev = ReportManager.get_monthly_revenue()
check("get_monthly_revenue: numeric", isinstance(month_rev, (int,float)))

# ═══════════════════════════════════════════════════════
section("13. DOUBLE-ENTRY ACCOUNTING INTEGRITY")
# ═══════════════════════════════════════════════════════
# Every journal entry must have total debits == total credits
conn = database.get_connection()
entries = conn.execute("SELECT id FROM journal_entries").fetchall()
imbalanced = []
for (eid,) in entries:
    totals = conn.execute(
        "SELECT COALESCE(SUM(debit),0), COALESCE(SUM(credit),0) FROM journal_lines WHERE entry_id=?", (eid,)
    ).fetchone()
    dr, cr = totals
    if abs(dr - cr) > 0.01:
        imbalanced.append((eid, dr, cr))
conn.close()
check(f"All journal entries balanced (debit=credit)", 
      len(imbalanced)==0, 
      f"{len(imbalanced)} imbalanced: {imbalanced[:3]}")

# ═══════════════════════════════════════════════════════
section("14. FINANCIAL YEAR CLOSE")
# ═══════════════════════════════════════════════════════
# Add some data first
ExpenseManager.add_expense("Electricity", 200.0)
ok, msg = database.start_new_financial_year()
check("start_new_financial_year: OK", ok, msg)

# Expenses should be cleared
exps_after = ExpenseManager.get_all_expenses()
check("expenses cleared after year close", len(exps_after) == 0)

# Closing journal entry exists
conn = database.get_connection()
close_je = conn.execute("SELECT COUNT(*) FROM journal_entries WHERE reference='CLOSE-YR'").fetchone()[0]
conn.close()
check("CLOSE-YR journal entry created", close_je > 0)

# Revenue/Expense accounts should net to zero in Trial Balance (after close)
tb2 = AccountingManager.get_trial_balance()
rev_exp_non_zero = [(acc, dr, cr) for acc, dr, cr in tb2 
                    if any(kw in acc.lower() for kw in ['revenue','expense','cost of goods'])]
check("Revenue & Expense accounts zero after year close", 
      len(rev_exp_non_zero)==0, 
      f"Non-zero: {rev_exp_non_zero[:3]}")

# Sessions should be cleared
sess_after = SessionManager.get_all_sessions()
check("sessions cleared after year close", len(sess_after) == 0)

# ═══════════════════════════════════════════════════════
# FINAL SUMMARY
# ═══════════════════════════════════════════════════════
print(f"\n{'═'*55}")
print(f"  TEST RESULTS: {PASS} passed  /  {FAIL} failed  /  {PASS+FAIL} total")
print(f"{'═'*55}")
if ERRORS:
    print("\n  ❌ FAILED TESTS:")
    for e in ERRORS:
        print(f"     • {e}")
else:
    print("\n  🎉 ALL TESTS PASSED!")

# Cleanup test DB
os.remove(TEST_DB)
