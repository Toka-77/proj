# -*- coding: utf-8 -*-
with open('pages.py', 'r', encoding='utf-8') as f:
    content = f.read()

REPLACEMENTS = [
    ('("All",                 "🔘 All Accounts")', '("All",                 "🔘 جميع الحسابات")'),
    ('("ذمم دائنة",    "📤 Accounts Payable")', '("ذمم دائنة",    "📤 ذمم دائنة")'),
    ('("ذمم مدينة", "📥 Accounts Receivable")', '("ذمم مدينة", "📥 ذمم مدينة")'),
    ('("Sales Revenue",       "💰 Sales Revenue")', '("Sales Revenue",       "💰 إيرادات المبيعات")'),
    ('("Inventory",           "📦 Inventory")', '("Inventory",           "📦 المخزون")'),
]

for old, new in REPLACEMENTS:
    if old in content:
        content = content.replace(old, new)

with open('pages.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Done!')
