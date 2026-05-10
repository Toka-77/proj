# -*- coding: utf-8 -*-
with open('translations.py', 'r', encoding='utf-8') as f:
    t = f.read()

missing = {
    "Toggle Dark / Light mode": "تبديل الوضع الفاتح/الداكن",
    "Switch language / تغيير اللغة": "تغيير اللغة",
    "Co-Working Space AIS — Accounting Information System": "نظام المعلومات المحاسبية — AIS Hub",
    "🔴 Admin": "🔴 مدير",
    "🎫 Employee": "🎫 موظف",
    "🚪 Logout": "🚪 تسجيل خروج",
    "AIS Hub — Login": "نظام AIS Hub — تسجيل الدخول",
}

insert_idx = t.find('}')
out = []
for k, v in missing.items():
    if f'"{k}"' not in t and f"'{k}'" not in t:
        out.append(f'    "{k}": "{v}",')

t = t[:insert_idx] + '\n'.join(out) + '\n' + t[insert_idx:]
with open('translations.py', 'w', encoding='utf-8') as f:
    f.write(t)
print("Updated translations.py with main.py strings")
