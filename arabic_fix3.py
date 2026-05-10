# -*- coding: utf-8 -*-
"""arabic_fix3.py — Final pass"""

with open('pages.py', 'r', encoding='utf-8') as f:
    p = f.read()

def rep(old, new):
    global p
    p = p.replace(old, new)

# Dashboard table
rep('"Started"', '"البداية"')
rep('"Elapsed"', '"المدة"')

# Rooms table headers
rep('["#","Name","Type","Status","Price/hr","Capacity"]',
    '["#","الغرفة","النوع","الحالة","السعر/ساعة","السعة"]')
# Session history table
rep('["#","Room","Type","Customer","People","Start","End","Duration","Room Charge","Snacks","Disc","Total"]',
    '["#","الغرفة","النوع","العميل","الأشخاص","بداية","نهاية","المدة","رسوم الغرفة","سناكس","خصم","الإجمالي"]')
rep('["#","Room","Type","Customer","People","Start","End",',
    '["#","الغرفة","النوع","العميل","الأشخاص","بداية","نهاية",')

# Remaining form labels
rep('"Session:"',   '"الجلسة:"')
rep('"Discount:"',  '"الخصم:"')
rep('"Amount:"',    '"المبلغ:"')

# Expenses table
rep('["ID","?????\","Amount","Date","Description"]',
    '["ID","الفئة","المبلغ","التاريخ","الوصف"]')
rep('["ID",',       '["ID",')  # keep ID
# match exact broken pattern
import re
p = re.sub(r'\["ID","[^"]*","Amount","Date","Description"\]',
           '["ID","الفئة","المبلغ","التاريخ","الوصف"]', p)

# Reports page
rep('page_container("Financial Reports"', 'page_container("التقارير المالية"')
rep('"Segment Reporting & Analytics"',    '"تحليل القطاعات والأداء"')
rep('"Net Profit"',         '"صافي الربح"')
rep('"Net Loss"',           '"صافي الخسارة"')
rep('"Top Room"',           '"أكثر غرفة استخداماً"')
rep('"Inventory Value"',    '"قيمة المخزون"')
rep('"Room Type"',          '"نوع الغرفة"')
rep('["Room Type","????????? (?.?)","% of Total"]',
    '["نوع الغرفة","الإيرادات (ج.م)","% من الإجمالي"]')
p = re.sub(r'\["Room Type","[^"]*","[^"]*"\]',
           '["نوع الغرفة","الإيرادات (ج.م)","% من الإجمالي"]', p)
p = re.sub(r'\["Room","[^"]*"\]',
           '["الغرفة","الإيرادات (ج.م)"]', p)
rep('"Net Profit" if p >= 0 else "Net Loss"',
    '"صافي الربح" if p >= 0 else "صافي الخسارة"')

# Sales page
rep('page_container("Sales"',  'page_container("المبيعات"')
rep('["Product","Qty","Price","????????"]',
    '["المنتج","الكمية","السعر","الإجمالي"]')
p = re.sub(r'\["Product","Qty","Price","[^"]*"\]',
           '["المنتج","الكمية","السعر","الإجمالي"]', p)
rep('["Product","Qty","Unit Cost","الإجمالي"]',
    '["المنتج","الكمية","تكلفة الوحدة","الإجمالي"]')

# Accounting GL table
p = re.sub(r'\["قيد#","الحساب","التاريخ","الوصف","الجهة","مدي[^"]*"\]',
           '["قيد#","الحساب","التاريخ","الوصف","الجهة","مدين","دائن","المرجع"]', p)

# MessageBox titles still "???"
p = p.replace('QMessageBox.warning(self.page, "???",',
              'QMessageBox.warning(self.page, "خطأ",')
p = p.replace("QMessageBox.warning(self.page, \"???\",",
              'QMessageBox.warning(self.page, "خطأ",')

# Specific message texts
rep('"No active session."',                  '"لا توجد جلسة نشطة."')
rep('"Select a room from the table first."', '"اختر غرفة من الجدول أولاً."')
rep('"Select a session from the history table."', '"اختر جلسة من السجل."')
rep('"Enter a valid amount."',               '"أدخل مبلغاً صحيحاً."')
rep('"Select an expense."',                  '"اختر مصروفاً."')
rep('"Enter a valid amount."',               '"أدخل مبلغاً صحيحاً."')
rep('"Invalid"',                             '"غير صحيح"')

# Edit Room Price dialog
rep('"Edit Room Price"',                    '"تعديل سعر الغرفة"')
rep('f"Enter new price for {room_name}:"',  'f"أدخل السعر الجديد لـ {room_name}:"')
p = re.sub(r'QInputDialog\.getDouble\(self\.page, "تعديل سعر الغرفة", f"([^"]*)"',
           r'QInputDialog.getDouble(self.page, "تعديل سعر الغرفة", f"أدخل السعر الجديد:"', p)

# "Active" status in sessions table
rep('h[6] or "Active"', 'h[6] or "نشطة"')
rep('or "Active",',     'or "نشطة",')

# Accounting page title still "Accounting" as QLabel text
rep('t = QLabel("Accounting");', 't = QLabel("المحاسبة");')
rep('t = QLabel("Purchase");',   't = QLabel("المشتريات");')
rep('t = QLabel("Sales");',      't = QLabel("المبيعات");')

# General Ledger table - rebuild properly
p = re.sub(r'\["قيد#"[^\]]+\]',
           '["قيد#","الحساب","التاريخ","الوصف","الجهة","مدين","دائن","المرجع"]', p)

# Journal entries table
p = re.sub(r'\["#","التاريخ","الوصف","الجهة","المرجع","إجمالي المدين[^\]]*\]',
           '["#","التاريخ","الوصف","الجهة","المرجع","إجمالي المدين","إجمالي الدائن"]', p)

# Sales invoice page title
rep('page_container("Sales"', 'page_container("فواتير المبيعات"')

# Income statement StatCard
rep('StatCard("??","Net Income"', 'StatCard("📊","صافي الدخل"')
p = re.sub(r'StatCard\("[\?\ud83c-\udfff\u2600-\u26ff]*","Net Income"',
           'StatCard("📊","صافي الدخل"', p)

# Outstanding StatCard
rep('"Outstanding"', '"غير مسدد"')

with open('pages.py', 'w', encoding='utf-8') as f:
    f.write(p)
print('pages.py final pass done')

import subprocess
result = subprocess.run(['python', '-c', 'import pages; print("pages.py OK")'],
                       capture_output=True, text=True, cwd='.')
print(result.stdout.strip())
if result.returncode != 0:
    print('ERROR:', result.stderr[:500])
