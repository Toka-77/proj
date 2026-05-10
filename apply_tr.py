# -*- coding: utf-8 -*-
import re

with open('translations.py', 'r', encoding='utf-8') as f:
    exec(f.read(), globals())

with open('pages.py', 'r', encoding='utf-8') as f:
    content = f.read()

if 'from translations import tr' not in content:
    content = content.replace('from datetime import datetime', 
                              'from datetime import datetime\nfrom translations import tr, is_arabic')

keys = sorted(list(TRANSLATIONS.keys()), key=len, reverse=True)

for key in keys:
    # We want to replace "key" with tr("key")
    # But only if it's not already tr("key")
    # And not in objectName="key"
    
    # regex to find "key" not preceded by tr( and not preceded by objectName=
    # using negative lookbehind
    
    # To be safer, just split and replace manually, avoiding objectName
    # Actually, objectName doesn't use the display strings like "Dashboard", it uses "title", "root", etc.
    # So we can just replace '"{key}"' with 'tr("{key}")'
    # And to avoid double wrapping: replace 'tr(tr("{key}"))' with 'tr("{key}")' later.
    
    # We also have to handle 'key' (single quotes) if any, but most are double quotes.
    
    # First, wrap
    content = content.replace(f'"{key}"', f'tr("{key}")')
    content = content.replace(f"'{key}'", f'tr("{key}")')

# Fix double wraps
for key in keys:
    content = content.replace(f'tr(tr("{key}"))', f'tr("{key}")')
    content = content.replace(f"tr(tr('{key}'))", f'tr("{key}")')
    
# Wait, some concatenations like `"🏠  " + tr("All Rooms")` might already exist?
# No, `pages.py` was restored to pure English.

with open('pages.py', 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Wrapped {len(keys)} unique strings in tr()!")
