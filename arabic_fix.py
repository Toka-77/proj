# -*- coding: utf-8 -*-
"""arabic_fix.py — Applies all Arabic replacements to pages.py"""
import re

with open('pages.py', 'r', encoding='utf-8') as f:
    content = f.read()

original_len = len(content)

def rep(old, new):
    global content
    content = content.replace(old, new)

# ── Remove tr() wrappers already added and replace with direct Arabic ────────
rep('tr("Dashboard")', '"لوحة التحكم"')
rep('tr("Active Sessions")', '"الجلسات النشطة"')
rep("tr(\"Today's Revenue\")", '"إيرادات اليوم"')
rep('tr("Net Profit")', '"صافي الربح"')
rep('tr("Net Loss")', '"صافي الخسارة"')
rep('tr("All Rooms")', '"جميع الغرف"')
rep('tr("EGP")', '"ج.م"')
rep('tr("Room")', '"الغرفة"')
rep('tr("Type")', '"النوع"')
rep('tr("Customer")', '"العميل"')
rep('tr("People")', '"الأشخاص"')
rep('status_tr = tr(r[3]) if is_arabic() else r[3]', '')
rep('card = RoomStatusCard(r[1], r[2], status_tr, r[4])', 'card = RoomStatusCard(r[1], r[2], r[3], r[4])')
rep('"Real-time Overview"', '"نظرة عامة فورية"')
rep('page_container("لوحة التحكم", "نظرة عامة فورية")', 'page_container("لوحة التحكم", "نظرة عامة فورية")')
rep('if is_arabic():\n        t.setAlignment(Qt.AlignRight | Qt.AlignVCenter)\n    header.addWidget(t)',
    'header.addWidget(t)')

# ── Page titles ───────────────────────────────────────────────────────────────
rep('"لوحة التحكم", "نظرة عامة فورية"',  '"لوحة التحكم", "نظرة عامة فورية"')
rep('page_container("لوحة التحكم"',        'page_container("لوحة التحكم"')
rep('"Snacks & Inventory"',     '"المخزون والسناكس"')
rep('"Rooms & Sessions"',       '"الغرف والجلسات"')
rep('"Expenses"',               '"المصروفات"')
rep('"Reports"',                '"التقارير"')
rep('"Sales Invoices"',         '"فواتير المبيعات"')
rep('"Purchase Invoices"',      '"فواتير المشتريات"')
rep('"Accounting & Finance"',   '"المحاسبة والتمويل"')
rep('"Account Statements"',     '"كشوف الحساب"')
rep('"Loyalty Program"',        '"برنامج الولاء"')
rep('"System Configuration"',   '"إعدادات النظام"')

# ── Section titles ────────────────────────────────────────────────────────────
rep('"▶  Start Session"',               '"▶  بدء جلسة"')
rep('"⏹  End Session"',                 '"⏹  إنهاء الجلسة"')
rep('"📋  Session History"',             '"📋  سجل الجلسات"')
rep('"🏠  All Rooms"',                   '"🏠  جميع الغرف"')
rep('"All Rooms"',                       '"جميع الغرف"')
rep('"Live Room Status"',                '"حالة الغرف الآن"')
rep('"Active Sessions"',                 '"الجلسات النشطة"')
rep('"📦  Products Catalogue"',          '"📦  كتالوج المنتجات"')
rep('"⚠️  Low Stock Alerts"',            '"⚠️  تنبيهات نقص المخزون"')
rep('"✏️  Edit Price & Cost"',           '"✏️  تعديل السعر والتكلفة"')
rep('"💸  Add Expense"',                  '"💸  إضافة مصروف"')
rep('"📋  Expense History"',              '"📋  سجل المصروفات"')
rep('"🧾  Sales Invoices"',               '"🧾  فواتير المبيعات"')
rep('"➕  New Sales Invoice"',            '"➕  فاتورة مبيعات جديدة"')
rep('"📦  Purchase Invoices"',            '"📦  فواتير المشتريات"')
rep('"➕  New Purchase Invoice"',         '"➕  فاتورة شراء جديدة"')
rep('"📋  Invoice Details"',              '"📋  تفاصيل الفاتورة"')
rep('"📋  All Bookings"',                 '"📋  جميع الحجوزات"')
rep('"➕  New Booking"',                  '"➕  حجز جديد"')
rep('"ℹ️  About AIS Hub"',               '"ℹ️  عن النظام"')
rep('"⚠️  Danger Zone"',                 '"⚠️  منطقة الخطر"')
rep('"🔔  Notification Thresholds"',     '"🔔  حدود التنبيهات"')
rep('"🎯  Loyalty Settings"',             '"🎯  إعدادات الولاء"')
rep('"📊  Revenue Overview"',             '"📊  نظرة على الإيرادات"')
rep('"🏆  Room Performance"',             '"🏆  أداء الغرف"')
rep('"📈  Sessions Overview"',            '"📈  نظرة على الجلسات"')
rep('"💎  Equity"',                       '"💎  حقوق الملكية"')
rep('"🔴  Liabilities"',                  '"🔴  الالتزامات"')
rep('"🟢  Assets"',                       '"🟢  الأصول"')
rep('"⚖️  Trial Balance"',               '"⚖️  ميزان المراجعة"')
rep('"📊  Balance Sheet"',               '"📊  الميزانية العمومية"')
rep('"📒  General Ledger"',              '"📒  دفتر الأستاذ"')
rep('"📓  Journal Entries"',             '"📓  قيود اليومية"')
rep('"📈  Income Statement"',            '"📈  قائمة الدخل"')
rep('"🗂️  Chart of Accounts"',          '"🗂️  دليل الحسابات"')
rep('"🎯  Loyalty Accounts"',            '"🎯  حسابات الولاء"')
rep('"🔍  Customer Lookup"',             '"🔍  بحث العملاء"')
rep('"👤  Customer Statements"',         '"👤  كشف حساب العميل"')
rep('"🏭  Supplier Statements"',         '"🏭  كشف حساب المورد"')
rep('"Total Assets"',                    '"إجمالي الأصول"')
rep('"Total Liabilities"',               '"إجمالي الالتزامات"')
rep('"Total Equity"',                    '"إجمالي حقوق الملكية"')

# ── Table headers ─────────────────────────────────────────────────────────────
rep('["#", "الغرفة", "النوع", "العميل", "الأشخاص", "البداية", "المدة"]',
    '["#", "الغرفة", "النوع", "العميل", "الأشخاص", "البداية", "المدة"]')
rep('["#", "Room", "Type", "Customer", "People", "Started", "Elapsed"]',
    '["#", "الغرفة", "النوع", "العميل", "الأشخاص", "البداية", "المدة"]')
rep('["#", "Room", "Type", "Status", "Price/hr", "Capacity"]',
    '["#", "الغرفة", "النوع", "الحالة", "السعر/ساعة", "السعة"]')
rep('["#","Room","Customer","In","Out","Duration","Room Charge","Snacks","Discount","Total"]',
    '["#","الغرفة","العميل","دخول","خروج","المدة","رسوم الغرفة","سناكس","خصم","الإجمالي"]')
rep('["SKU","Name","Category","Cost","Selling Price","Stock"]',
    '["الكود","الاسم","الفئة","التكلفة","سعر البيع","المخزون"]')
rep('["SKU","Product","Stock"]',
    '["الكود","المنتج","المخزون"]')
rep('["#","Date","Category","Amount","Description"]',
    '["#","التاريخ","الفئة","المبلغ","الوصف"]')
rep('["#","Customer","Date","Total","Status"]',
    '["#","العميل","التاريخ","الإجمالي","الحالة"]')
rep('["#","Supplier","Date","Total","Status"]',
    '["#","المورد","التاريخ","الإجمالي","الحالة"]')
rep('["Name","Qty","Price","Total"]',
    '["الاسم","الكمية","السعر","الإجمالي"]')
rep('["#","Entry Date","Description","Reference","Entity","Debit"]',
    '["#","التاريخ","الوصف","المرجع","الجهة","المدين"]')
rep('["Account","Debit","Credit","Balance","Description","Date","Ref"]',
    '["الحساب","مدين","دائن","الرصيد","الوصف","التاريخ","المرجع"]')
rep('["Account","Total Debit","Total Credit"]',
    '["الحساب","إجمالي المدين","إجمالي الدائن"]')
rep('["Account","Balance (EGP)"]',
    '["الحساب","الرصيد (ج.م)"]')
rep('["Code","Account","Type"]',
    '["الكود","الحساب","النوع"]')
rep('["#","Room","Customer","Date","From","To","People","Deposit","Status"]',
    '["#","الغرفة","العميل","التاريخ","من","إلى","الأشخاص","العربون","الحالة"]')
rep('["#","Customer","Points","Tier","Total Spent"]',
    '["#","العميل","النقاط","المستوى","الإجمالي المنفق"]')
rep('["Invoice","Date","Amount","Status"]',
    '["الفاتورة","التاريخ","المبلغ","الحالة"]')
rep('["#","Entry","Date","Description"]',
    '["#","القيد","التاريخ","الوصف"]')

# ── Buttons ───────────────────────────────────────────────────────────────────
rep('"💾  Update Price"',    '"💾  تحديث السعر"')
rep('"🗑  Delete Product"',  '"🗑  حذف المنتج"')
rep('"💾  Save Invoice"',    '"💾  حفظ الفاتورة"')
rep('"➕  Add Line"',         '"➕  إضافة سطر"')
rep('"🗑  Remove"',           '"🗑  حذف"')
rep('"🖨️  Export Invoice PDF"', '"🖨️  تصدير PDF"')
rep('"✅  Mark as Paid"',     '"✅  تأشير مدفوع"')
rep('"🗑  Delete Invoice"',   '"🗑  حذف الفاتورة"')
rep('"📅  Confirm Booking"', '"📅  تأكيد الحجز"')
rep('"❌  Cancel Booking"',  '"❌  إلغاء الحجز"')
rep('"✏️  Edit Booking"',    '"✏️  تعديل الحجز"')
rep('"▶  Convert to Session"', '"▶  تحويل لجلسة"')
rep('"💾  Save Settings"',   '"💾  حفظ الإعدادات"')
rep('"🔄  Reset Alerts"',    '"🔄  إعادة ضبط التنبيهات"')
rep('"📅  Start New Financial Year"', '"📅  بدء سنة مالية جديدة"')
rep('"➕  Add Account"',      '"➕  إضافة حساب"')
rep('"🔍  Lookup"',          '"🔍  بحث"')
rep('"💎  Redeem Points"',   '"💎  استبدال النقاط"')
rep('"Show All"',            '"عرض الكل"')
rep('"✏️ Edit Selected Room Price"', '"✏️ تعديل سعر الغرفة"')
rep('"➕ Add New Room"',      '"➕ إضافة غرفة جديدة"')
rep('"📄 Export Session Invoice (PDF)"', '"📄 تصدير فاتورة الجلسة (PDF)"')
rep('"⏹  End & Generate Bill"', '"⏹  إنهاء وإصدار الفاتورة"')
rep('"▶  Start Session")',   '"▶  بدء الجلسة")')

# ── Form labels ───────────────────────────────────────────────────────────────
rep('"Room:"',              '"الغرفة:"')
rep('"Customer:"',          '"العميل:"')
rep('"People:"',            '"الأشخاص:"')
rep('"Discount (EGP):"',    '"الخصم (ج.م):"')
rep('"Notes:"',             '"الملاحظات:"')
rep('"SKU:"',               '"الكود:"')
rep('"Name:"',              '"الاسم:"')
rep('"Unit Cost:"',         '"تكلفة الوحدة:"')
rep('"Sale Price:"',        '"سعر البيع:"')
rep('"Category:"',          '"الفئة:"')
rep('"Amount (EGP):"',      '"المبلغ (ج.م):"')
rep('"Description:"',       '"الوصف:"')
rep('"Supplier:"',          '"المورد:"')
rep('"Product Name:"',      '"اسم المنتج:"')
rep('"Qty:"',               '"الكمية:"')
rep('"Selling Price:"',     '"سعر البيع:"')
rep('"Type:"',              '"النوع:"')
rep('"Price/hr:"',          '"السعر/ساعة:"')
rep('"Capacity:"',          '"السعة:"')
rep('"Date:"',              '"التاريخ:"')
rep('"From:"',              '"من:"')
rep('"To:"',                '"إلى:"')
rep('"Deposit:"',           '"العربون:"')
rep('"Account Name:"',      '"اسم الحساب:"')
rep('"Account Type:"',      '"نوع الحساب:"')
rep('"Account:"',           '"الحساب:"')
rep('"Daily Revenue Target:"', '"هدف إيرادات اليوم:"')
rep('"Low Stock Threshold:"',  '"حد تنبيه نقص المخزون:"')
rep('"Session Alert (hrs):"',  '"تنبيه طول الجلسة:"')
rep('"Unpaid Invoice Alert:"', '"تنبيه الفواتير غير المدفوعة:"')
rep('"Points Earn Rate:"',     '"معدل كسب النقاط:"')
rep('"Redeem Rate:"',          '"معدل الاستبدال:"')
rep('"Promo Code:"',           '"كود الخصم:"')
rep('"Deposit (EGP):"',        '"العربون (ج.م):"')
rep('"Link to Session (optional):"', '"ربط بجلسة (اختياري):"')

# ── Placeholder texts ─────────────────────────────────────────────────────────
rep('"Customer name..."',         '"اسم العميل..."')
rep('"Customer name (editable)"', '"اسم العميل (قابل للتعديل)"')
rep('"Auto-filled on row select"','"يُملأ عند الاختيار"')
rep('"Product name (editable)"',  '"اسم المنتج"')
rep('"Notes..."',                 '"ملاحظات..."')
rep('"Search products..."',       '"بحث عن منتج..."')
rep('"Supplier name..."',         '"اسم المورد..."')
rep('"Search customer..."',       '"بحث عن عميل..."')
rep('"Search supplier..."',       '"بحث عن مورد..."')
rep('"Account name..."',          '"اسم الحساب..."')
rep('"e.g. Study Room C"',        '"مثال: غرفة دراسة C"')
rep('"Optional description"',     '"وصف اختياري"')

# ── Tab names ─────────────────────────────────────────────────────────────────
rep('"📓 Journal"',           '"📓 اليومية"')
rep('"📒 General Ledger"',    '"📒 دفتر الأستاذ"')
rep('"📈 Income Statement"',  '"📈 قائمة الدخل"')
rep('"📊 Balance Sheet"',     '"📊 الميزانية"')
rep('"⚖️ Trial Balance"',     '"⚖️ ميزان المراجعة"')
rep('"🗂️ Chart of Accounts"', '"🗂️ دليل الحسابات"')
rep('"👤 Customers"',         '"👤 العملاء"')
rep('"🏭 Suppliers"',         '"🏭 الموردون"')

# ── Stats and totals ──────────────────────────────────────────────────────────
rep('"Total Rooms"',        '"إجمالي الغرف"')
rep('"Total Sessions"',     '"إجمالي الجلسات"')
rep('"Snacks Today"',       '"سناكس اليوم"')
rep('"Total Debit: 0.00"',  '"إجمالي المدين: 0.00"')
rep('"Total Credit: 0.00"', '"إجمالي الدائن: 0.00"')
rep('"Total: 0.00"',        '"الإجمالي: 0.00"')
rep('"Total Value: 0.00 EGP"','"القيمة الإجمالية: 0.00 ج.م"')

# ── About section ─────────────────────────────────────────────────────────────
rep('"Version"',       '"الإصدار"')
rep('"Python"',        '"بايثون"')
rep('"Framework"',     '"الإطار"')
rep('"Database"',      '"قاعدة البيانات"')
rep('"PDF Engine"',    '"محرك PDF"')
rep('"System"',        '"النظام"')

# ── Message boxes ─────────────────────────────────────────────────────────────
rep('"Select Product"',            '"اختيار منتج"')
rep('"Click a row first."',        '"اضغط على صف أولاً."')
rep('"Price must be > 0."',        '"السعر يجب أن يكون أكبر من صفر."')
rep('"Product updated."',          '"تم تحديث المنتج."')
rep('"Select a booking."',         '"اختر حجزاً."')
rep('"Select a booking to edit."', '"اختر حجزاً للتعديل."')
rep('"Booking not found."',        '"الحجز غير موجود."')
rep('"Booking updated successfully."', '"تم تحديث الحجز بنجاح."')
rep('"Room name is required."',    '"اسم الغرفة مطلوب."')
rep('"No available room."',        '"لا توجد غرفة متاحة."')
rep('"Enter customer name."',      '"أدخل اسم العميل."')
rep('"Required"',                  '"حقل مطلوب"')
rep('"End time must be after start time."', '"وقت الانتهاء يجب أن يكون بعد وقت البداية."')
rep('"Cannot book a past date."',  '"لا يمكن الحجز في تاريخ سابق."')
rep('"Cannot book a past time slot."', '"لا يمكن الحجز في وقت سابق."')
rep('"Add product lines first."',  '"أضف منتجات أولاً."')
rep('"Enter supplier name."',      '"أدخل اسم المورد."')
rep('"Select an invoice."',        '"اختر فاتورة."')
rep('"Account name is required."', '"اسم الحساب مطلوب."')
rep('"Select Account Type"',       '"اختر نوع الحساب"')
rep('"Over Capacity"',             '"تجاوز السعة"')
rep('"✅ Started"',                 '"✅ بدأت الجلسة"')
rep('"✅ Booked"',                  '"✅ تم الحجز"')
rep('"Cancel this booking?"',      '"هل تريد إلغاء هذا الحجز؟"')
rep('"Direct Sale"',               '"بيع مباشر"')
rep('"Confirm"',                   '"تأكيد"')
rep('"Error"',                     '"خطأ"')
rep('"Select Room"',               '"اختر الغرفة"')
rep('"Select Session"',            '"اختر الجلسة"')
rep('"Add Expense"',               '"إضافة مصروف"')
rep('"Paid immediately (Cash)"',   '"مدفوع نقداً"')

# ── Misc ──────────────────────────────────────────────────────────────────────
rep('"Select a product row, then update its selling price and cost."',
    '"اختر منتجاً من الجدول لتعديل السعر والتكلفة."')
rep('"Clears the notification dedup cache\\nso alerts can show again."',
    '"مسح سجل التنبيهات لتظهر مرة أخرى."')
rep('"Clears all transactional history (sessions, sales, expenses, invoices) to start a new year. Keeps master data like rooms, products, and customers."',
    '"مسح كل البيانات المالية لبدء سنة جديدة. يتم الاحتفاظ بالغرف والمنتجات والعملاء."')
rep('"Filter by Account"', '"تصفية حسب الحساب"')
rep('"(Select from table)"', '"(اختر من الجدول)"')

# ── Report labels ─────────────────────────────────────────────────────────────
rep('"Revenue (EGP)"',      '"الإيرادات (ج.م)"')
rep('"Sessions"',           '"الجلسات"')
rep('"No sessions yet"',    '"لا توجد جلسات بعد"')
rep('"No data"',            '"لا توجد بيانات"')
rep('"Study"',              '"دراسة"')
rep('"Gaming"',             '"ألعاب"')
rep('"Cinema"',             '"سينما"')
rep('"Top Room:"',          '"أكثر غرفة استخداماً:"')
rep('"Most Used:"',         '"الأكثر استخداماً:"')
rep('"sessions"',           '"جلسة"')

# ── Loyalty page ─────────────────────────────────────────────────────────────
rep('"Points to redeem:"',  '"النقاط للاستبدال:"')
rep('"Bronze"',             '"برونز"')
rep('"Silver"',             '"فضي"')
rep('"Gold"',               '"ذهبي"')
rep('"Platinum"',           '"بلاتيني"')
rep('"pts = 1 EGP discount"', '"نقطة = 1 ج.م خصم"')
rep('" pts / EGP"',         '"نقطة / ج.م"')
rep('" pts = 1 EGP"',       '"نقطة = 1 ج.م"')

with open('pages.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done! pages.py arabized successfully.')
