# -*- coding: utf-8 -*-
import re
with open('pages.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
count = 0
found_strings = set()
for i, line in enumerate(lines, 1):
    stripped = line.strip()
    if not stripped or stripped.startswith('#'): continue
    matches = re.findall(r'\"([^\"]*[A-Za-z]{3,}[^\"]*)\"', stripped)
    for m in matches:
        if 'tr(' in line: continue # rough check
        skip_words = ['utf', 'EGP', 'objectName', 'yyyy', 'HH:mm', 'Arial', 'Segoe', 
                      'PyQt', 'SQLite', 'fpdf', 'AIS Hub', 'Multi-Activity', 'Co-Working', 'System',
                      'CLOSE-YR', 'COGS', 'BK-', 'PI-', 'SI-', 'PAY', 'EXP',
                      'dark', 'light', 'danger', 'primary', 'secondary',
                      'admin', 'employee', 'root', 'sec_title', 'subtitle', 'title',
                      'icon_btn', 'toast_', 'AIS', 'v3.0', 'Helvetica']
        if any(sw in m for sw in skip_words): continue
        if not re.search(r'[A-Za-z]{3,}', m): continue
        found_strings.add(m)
        count += 1

print(f'Total English strings on lines without tr(): {count}')
for s in sorted(list(found_strings)):
    print(f'"{s}"')
