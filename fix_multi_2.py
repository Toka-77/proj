# -*- coding: utf-8 -*-
import re

with open('translations.py', 'r', encoding='utf-8') as f:
    t = f.read()

# Fix broken newlines in the file
# We'll just replace literal newlines that are inside strings with \n
# Wait, this is hard with regex. 
# Let's fix specific known broken ones:
t = t.replace('"Clears the notification dedup cache\nso alerts can show again."', r'"Clears the notification dedup cache\nso alerts can show again."')
t = t.replace('("Are you sure you want to close the current financial year?\n\nThis will generate a Closing Journal Entry to zero out all Revenue and Expense accounts into Equity (Current Year Earnings).\n\nHistorical data and master data will be preserved.")', 
              r'"Are you sure you want to close the current financial year?\n\nThis will generate a Closing Journal Entry to zero out all Revenue and Expense accounts into Equity (Current Year Earnings).\n\nHistorical data and master data will be preserved."')
# Just doing a regex to fix ANY unterminated string that was broken by literal newlines:
# Actually, I can just replace all \n inside the dictionary that are literal.
lines = t.split('\n')
fixed_lines = []
for i, line in enumerate(lines):
    if line.startswith('    "Are you sure') or line.startswith('    "Clears the'):
        # we will use repr() like fixes in another way.
        pass

# Much safer: Just reload TRANSLATIONS from scratch from an older working version and add the new ones with proper repr()
