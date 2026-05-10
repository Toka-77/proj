# -*- coding: utf-8 -*-
import re

with open('translations.py', 'r', encoding='utf-8') as f:
    t = f.read()

# Fix broken multiline literal added by previous script
# We can find it by looking for the literal text
broken_part = r'''"Are you sure you want to close the current financial year?

This will generate a Closing Journal Entry to zero out all Revenue and Expense accounts into Equity (Current Year Earnings).

Historical data and master data will be preserved.": "هل أنت متأكد من إغلاق السنة المالية الحالية؟

سيتم إنشاء قيد إقفال لتصفير جميع حسابات الإيرادات والمصروفات إلى حقوق الملكية.

سيتم الاحتفاظ بالبيانات التاريخية والأساسية.",'''

fixed_part = r'''"Are you sure you want to close the current financial year?\n\nThis will generate a Closing Journal Entry to zero out all Revenue and Expense accounts into Equity (Current Year Earnings).\n\nHistorical data and master data will be preserved.": "هل أنت متأكد من إغلاق السنة المالية الحالية؟\n\nسيتم إنشاء قيد إقفال لتصفير جميع حسابات الإيرادات والمصروفات إلى حقوق الملكية.\n\nسيتم الاحتفاظ بالبيانات التاريخية والأساسية.",'''

if broken_part in t:
    t = t.replace(broken_part, fixed_part)
else:
    # try regex
    t = re.sub(r'"Are you sure you want to close the current financial year\?.*?preserved\.",', fixed_part, t, flags=re.DOTALL)

with open('translations.py', 'w', encoding='utf-8') as f:
    f.write(t)

print("Fixed translations.py")
