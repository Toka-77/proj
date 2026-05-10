# -*- coding: utf-8 -*-
with open('pages.py', 'r', encoding='utf-8') as f:
    p = f.read()

p = p.replace('"Enter customer name."', 'tr("Enter a customer name.")')
p = p.replace('"??"', '"📊"')
p = p.replace('"?"', '"⚠️"')
p = p.replace('"??  Loyalty Program"', 'tr("Loyalty")')
p = p.replace('"??  Settings"', 'tr("Settings")')

with open('pages.py', 'w', encoding='utf-8') as f:
    f.write(p)
print('Cleaned up.')
