# -*- coding: utf-8 -*-
import re
with open('pages.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
count = 0
found_strings = set()
for i, line in enumerate(lines, 1):
    stripped = line.strip()
    if not stripped or stripped.startswith('#'): continue
    matches = re.findall(r'(?<!tr\()\"([A-Za-z][A-Za-z0-9 &,_\-!?.()/:#%@\'*+]{2,})\"', stripped)
    for m in matches:
        skip_words = ['utf', 'EGP', 'objectName', 'yyyy', 'HH:mm', 'Arial', 'Segoe', 
                      'PyQt', 'SQLite', 'fpdf', 'AIS Hub', 'Multi-Activity',
                      'CLOSE-YR', 'COGS', 'BK-', 'PI-', 'SI-', 'PAY', 'EXP',
                      'dark', 'light', 'danger', 'primary', 'secondary',
                      'admin', 'employee', 'root', 'sec_title', 'subtitle', 'title',
                      'icon_btn', 'toast_', 'AIS', 'v3.0', 'Helvetica', 'B', 'C', 'L', 'R', 'F']
        if any(sw in m for sw in skip_words): continue
        if len(m) >= 3:
            found_strings.add(m)
            count += 1

print(f'Total unwrapped instances: {count}')
for s in sorted(list(found_strings)):
    print(f'"{s}"')
