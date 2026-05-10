# -*- coding: utf-8 -*-
"""arabic_fix4.py — Last remaining strings"""

with open('pages.py', 'r', encoding='utf-8') as f:
    p = f.read()

def rep(old, new):
    global p
    p = p.replace(old, new)

import re

# Fix session history table - still has Snacks/Disc
p = re.sub(r'\["#","[^"]*","[^"]*","[^"]*","[^"]*","[^"]*","[^"]*","[^"]*","[^"]*","Snacks","Disc","Total"\]',
           '["#","الغرفة","النوع","العميل","الأشخاص","بداية","نهاية","المدة","رسوم الغرفة","سناكس","خصم","الإجمالي"]', p)
# Direct replacement
rep('"Snacks","Disc","Total")', '"سناكس","خصم","الإجمالي")')
rep('"Snacks","Disc",',         '"سناكس","خصم",')

# Sales invoice page
rep('"Link to Session:"',          '"ربط بجلسة:"')
rep('"Products:"',                 '"المنتجات:"')
rep('"None (no session)"',         '"بدون جلسة"')

# Validation messages
rep('"Invalid Price"',             '"سعر غير صحيح"')
rep('"Warning - Below Cost"',      '"تحذير - السعر أقل من التكلفة"')
rep('"Manager Override"',          '"تفويض المدير"')
rep('"Enter Admin Password to authorize selling below cost:"',
    '"أدخل كلمة مرور المدير للسماح بالبيع أقل من التكلفة:"')

# Purchase invoice table - partial fix
p = re.sub(r'\["#","[^"]*","Date","Total EGP","Status"\]',
           '["#","المورد","التاريخ","الإجمالي ج.م","الحالة"]', p)
p = re.sub(r'"Date","Total EGP","Status"',
           '"التاريخ","الإجمالي ج.م","الحالة"', p)

# Accounting GL filter - Inventory account name
rep('("Inventory",           "?? Inventory")',
    '("المخزون",             "المخزون")')
rep('"?? Inventory"', '"المخزون"')

# Statements tables
p = re.sub(r'\["#","[^"]*","Date","Amount","Status"\]',
           '["#","المورد","التاريخ","المبلغ","الحالة"]', p)
rep('"Date","Amount","Status"', '"التاريخ","المبلغ","الحالة"')

# GL filter docstring - not visible to user, skip
# Fix the "??" broken stat card icons
rep('StatCard("??",', 'StatCard("📊",')
rep('StatCard("?",',  'StatCard("⚠️",')

with open('pages.py', 'w', encoding='utf-8') as f:
    f.write(p)
print('Done')

import subprocess
r = subprocess.run(['python', '-c', 'import pages; print("OK")'],
                   capture_output=True, text=True)
print(r.stdout.strip() or r.stderr[:300])
