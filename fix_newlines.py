# -*- coding: utf-8 -*-
with open('translations.py', 'r', encoding='utf-8') as f:
    t = f.read()

# Replace literal newlines in the Clears string
t = t.replace('"Clears the notification dedup cache\nso alerts can show again."', '"Clears the notification dedup cache\\nso alerts can show again."')
# Replace literal newlines in Session Closed string
t = t.replace('"Session #{res[\'session_id\']} Closed\n\n"', '"Session #{res[\'session_id\']} Closed\\n\\n"')
t = t.replace('"Duration:     {res[\'duration_hours\']:.2f} hrs\n"', '"Duration:     {res[\'duration_hours\']:.2f} hrs\\n"')

with open('translations.py', 'w', encoding='utf-8') as f:
    f.write(t)

print("Fixed newlines in translations.py")
