# -*- coding: utf-8 -*-
"""scan_english.py - finds remaining English UI strings in pages.py"""
import re

with open('pages.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

found = []
for i, line in enumerate(lines, 1):
    stripped = line.strip()
    if not stripped or stripped.startswith('#'): continue
    # Find quoted English strings with 3+ chars
    matches = re.findall(r'"([A-Za-z][A-Za-z0-9 &,_\-!?.()/:#%@\'*+]{2,})"', stripped)
    for m in matches:
        # Skip code-related things
        skip_words = ['utf', 'EGP', 'objectName', 'yyyy', 'HH:mm', 'Arial', 'Segoe', 
                      'PyQt', 'SQLite', 'fpdf', 'AIS Hub', 'Multi-Activity',
                      'CLOSE-YR', 'COGS', 'BK-', 'PI-', 'SI-', 'PAY', 'EXP',
                      'dark', 'light', 'danger', 'primary', 'secondary',
                      'admin', 'employee', 'Bronze', 'Silver', 'Gold', 'Platinum',
                      'Study', 'Gaming', 'Cinema', 'Asset', 'Liability', 'Equity', 
                      'Revenue', 'Expense', 'Cash', 'Available', 'Occupied',
                      'Confirmed', 'Cancelled', 'Completed', 'Paid', 'Unpaid',
                      'Arial', 'root', 'card', 'sec_title', 'subtitle', 'title',
                      'icon_btn', 'toast_', 'AIS', 'v3.0']
        if any(sw in m for sw in skip_words): continue
        if len(m) >= 4:
            found.append((i, m, stripped[:80]))

with open('english_remaining.txt', 'w', encoding='utf-8') as out:
    for lno, txt, ctx in found:
        out.write(f"L{lno}: [{txt}]\n  {ctx}\n\n")

print(f"Found {len(found)} English strings. See english_remaining.txt")
