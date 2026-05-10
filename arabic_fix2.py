# -*- coding: utf-8 -*-
"""arabic_fix2.py — Second pass: remaining English strings in pages.py + main.py"""

# ═══ Fix pages.py ══════════════════════════════════════════════════════════
with open('pages.py', 'r', encoding='utf-8') as f:
    p = f.read()

def rep(old, new):
    global p
    p = p.replace(old, new)

# Page titles
rep('page_container("Purchase"',         'page_container("المشتريات"')
rep('page_container("Accounting"',       'page_container("المحاسبة"')
rep('page_container("المحاسبة والتمويل"','page_container("المحاسبة والتمويل"')

# Section labels still in English
rep('"Invoice Details"',                 '"تفاصيل الفاتورة"')
rep('"Supplier"',                        '"المورد"')
rep('"Products"',                        '"المنتجات"')
rep('"Product Name"',                    '"اسم المنتج"')
rep('"Category"',                        '"الفئة"')

# Table headers still English
rep('["#","Supplier","Date","Total EGP","Status"]',
    '["#","المورد","التاريخ","الإجمالي ج.م","الحالة"]')
rep('["Product","Qty","Unit Cost","Total"]',
    '["المنتج","الكمية","تكلفة الوحدة","الإجمالي"]')
rep('["#","Date","Description","Entity","Reference","Total Debit","Total Credit"]',
    '["#","التاريخ","الوصف","الجهة","المرجع","إجمالي المدين","إجمالي الدائن"]')
rep('["#","Date","Description","Entity","Reference","Total D',
    '["#","التاريخ","الوصف","الجهة","المرجع","إجمالي المدين')
rep('["Account","Debit","Credit"]',
    '["الحساب","مدين","دائن"]')
rep('["Entry#","Account","Date","Description","Entity","Debit","Credit","Reference"]',
    '["قيد#","الحساب","التاريخ","الوصف","الجهة","مدين","دائن","المرجع"]')
rep('["Entry#","Account","Date","Description","Entity","Debi',
    '["قيد#","الحساب","التاريخ","الوصف","الجهة","مدي')
rep('["Account","Amount (EGP)"]',
    '["الحساب","المبلغ (ج.م)"]')
rep('["#","Customer","Date","Amount","Status"]',
    '["#","العميل","التاريخ","المبلغ","الحالة"]')
rep('["#","Supplier","Date","Amount","Status"]',
    '["#","المورد","التاريخ","المبلغ","الحالة"]')
rep('["#", "Customer", "Points", "Tier", "Total Spent"]',
    '["#","العميل","النقاط","المستوى","الإجمالي المنفق"]')

# Form labels
rep('"Entity:"',          '"الجهة:"')
rep('"Reference:"',       '"المرجع:"')
rep('"Debit Account:"',   '"حساب المدين:"')
rep('"Debit Amount:"',    '"مبلغ المدين:"')
rep('"Credit Account:"',  '"حساب الدائن:"')
rep('"Credit Amount:"',   '"مبلغ الدائن:"')
rep('"Filter:"',          '"تصفية:"')
rep('"Points to Redeem:"','"النقاط للاستبدال:"')

# Placeholder texts
rep('"Description..."',                       '"الوصف..."')
rep('"Entity (customer/supplier name)..."',   '"الجهة (اسم عميل/مورد)..."')
rep('"Reference (invoice#, etc.)..."',        '"المرجع (رقم فاتورة...)..."')

# Category combobox items
rep('["Drinks","Snacks","Hot","Other"]',  '["مشروبات","سناكس","مشروبات ساخنة","أخرى"]')
rep('cat_combo.addItems(["Drinks","Snacks","Hot","Other"])',
    'cat_combo.addItems(["مشروبات","سناكس","مشروبات ساخنة","أخرى"])')

# GL filter accounts
rep('("Accounts Payable",    "?? Accounts Payable")',
    '("ذمم دائنة",    "ذمم دائنة")')
rep('("Accounts Receivable", "?? Accounts Receivable")',
    '("ذمم مدينة",    "ذمم مدينة")')
rep('("Inventory",           "?? Inventory")',
    '("المخزون",             "المخزون")')
rep('"Accounts Payable"',    '"ذمم دائنة"')
rep('"Accounts Receivable"', '"ذمم مدينة"')

# StatCards
rep('"Net Income"',      '"صافي الدخل"')
rep('"Total"',           '"الإجمالي"')
rep('"Outstanding"',     '"غير مسدد"')

# Net profit/loss logic
rep('"Net Profit" if ni >= 0 else "Net Loss"',
    '"صافي الربح" if ni >= 0 else "صافي الخسارة"')
rep('"Profit" if ni >= 0 else "Loss"',
    '"ربح" if ni >= 0 else "خسارة"')

# Loyalty page
rep('page_container("??  Loyalty Program"', 'page_container("🎯  برنامج الولاء"')
rep('"Points & Rewards"',    '"النقاط والمكافآت"')
rep('"Points: 0"',           '"النقاط: 0"')
rep('"All Customers"',       '"جميع العملاء"')
rep('"All Suppliers"',       '"جميع الموردين"')
rep('"Total Spent"',         '"الإجمالي المنفق"')
rep('"pts = 1 EGP discount"','"نقطة = 1 ج.م خصم"')
rep('" pts = 1 EGP"',        '"نقطة = 1 ج.م"')
rep('" pts / EGP"',          '"نقطة / ج.م"')

# MessageBox messages
rep('"Select a supplier."',           '"اختر مورداً."')
rep('"Validation Error"',             '"خطأ في البيانات"')
rep('"Add at least one product."',    '"أضف منتجاً واحداً على الأقل."')
rep('"Enter description."',           '"أدخل الوصف."')
rep('"Enter valid amounts."',         '"أدخل مبالغ صحيحة."')
rep('"Total Debit must equal Total Credit."',
    '"إجمالي المدين يجب أن يساوي إجمالي الدائن."')
rep('"Account name cannot be empty."','"اسم الحساب لا يمكن أن يكون فارغاً."')
rep('"Enter a customer name."',       '"أدخل اسم العميل."')
rep('"Look up a customer first."',    '"ابحث عن عميل أولاً."')
rep('"Enter points to redeem."',      '"أدخل عدد النقاط للاستبدال."')
rep('"Alert history cleared."',       '"تم مسح سجل التنبيهات."')
rep('"Settings saved successfully."', '"تم حفظ الإعدادات بنجاح."')

# Dialog titles
rep('"Add New Account"',    '"إضافة حساب جديد"')
rep('"Add New Room"',       '"إضافة غرفة جديدة"')

# Misc labels
rep('"Supplier"',    '"المورد"')  # remaining standalone
rep('"Total Spent"', '"الإجمالي المنفق"')

# Accounting page - remaining hardcoded title
rep('t = QLabel("Accounting"); t.setObjectName("title")',
    't = QLabel("المحاسبة"); t.setObjectName("title")')

# "Not enough points" message
rep('"Not enough points. Available: "',  '"النقاط غير كافية. المتاح: "')

# Journal "???" in QMessageBox titles
p = p.replace('QMessageBox.warning(self.page, "???",',
              'QMessageBox.warning(self.page, "خطأ",')
p = p.replace('QMessageBox.information(self.page, "?",',
              'QMessageBox.information(self.page, "✅",')
p = p.replace('QMessageBox.warning(self.page, "?\",',
              'QMessageBox.warning(self.page, "خطأ",')
p = p.replace('QMessageBox.warning(self.page, "?\",',
              'QMessageBox.warning(self.page, "خطأ",')

# Fix broken Arabic from earlier pass
import re
p = re.sub(r'page_container\("Purchase", "([^"]+)"\)',
           r'page_container("المشتريات", "\1")', p)

with open('pages.py', 'w', encoding='utf-8') as f:
    f.write(p)
print('pages.py done')

# ═══ Fix main.py ════════════════════════════════════════════════════════════
with open('main.py', 'r', encoding='utf-8') as f:
    m = f.read()

def repm(old, new):
    global m
    m = m.replace(old, new)

repm('"🔴 Admin"',      '"🔴 مدير"')
repm('"🎫 Employee"',   '"🎫 موظف"')
repm('"🚪 Logout"',     '"🚪 تسجيل الخروج"')
repm('"Multi-Activity Hub\\nAIS v3.0"', '"نظام محاسبة\\nAIS v3.0"')
repm('"Toggle Dark / Light mode"',     '"تبديل الوضع الداكن/الفاتح"')
repm('"Switch language / تغيير اللغة"', '"تغيير اللغة"')
repm('"Co-Working Space AIS — Accounting Information System"',
     '"نظام المعلومات المحاسبية — AIS Hub"')
repm('"AIS Hub — Login"', '"نظام AIS Hub — تسجيل الدخول"')
repm('"Real-time Overview"', '"نظرة عامة فورية"')

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(m)
print('main.py done')
print('All done!')
