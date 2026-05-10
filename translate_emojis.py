# -*- coding: utf-8 -*-
import translations

with open('extracted_ui.txt', 'r', encoding='utf-8') as f:
    lines = f.read().splitlines()

new_translations = {
    "0 EGP": "0 ج.م",
    "1,000 pts to Silver": "1,000 نقطة للفضية",
    "100 pts = 1.00 EGP discount": "100 نقطة = 1.00 ج.م خصم",
    "Amount (EGP)": "المبلغ (ج.م)",
    "Are you sure you want to close the current financial year?\n\nThis will generate a Closing Journal Entry to zero out all Revenue and Expense accounts into Equity (Current Year Earnings).\n\nHistorical data and master data will be preserved.": "هل أنت متأكد من إغلاق السنة المالية الحالية؟\n\nسيتم إنشاء قيد إقفال لتصفير جميع حسابات الإيرادات والمصروفات إلى حقوق الملكية.\n\nسيتم الاحتفاظ بالبيانات التاريخية والأساسية.",
    "Balance (EGP)": "الرصيد (ج.م)",
    "Capacity:": "السعة:",
    "Category:": "الفئة:",
    "Cinema": "سينما",
    "Clears the notification dedup cache\nso alerts can show again.": "يمسح ذاكرة التنبيهات المكررة\nلتظهر التنبيهات مرة أخرى.",
    "Click a row first.": "انقر على صف أولاً.",
    "Daily Revenue Target:": "هدف الإيرادات اليومية:",
    "Enter customer name.": "أدخل اسم العميل.",
    "Invalid admin password! Transaction blocked.": "كلمة مرور المدير غير صحيحة! تم حظر المعاملة.",
    "Points: -": "النقاط: -",
    "Price must be > 0.": "السعر يجب أن يكون > 0.",
    "Required": "مطلوب",
    "Revenue (EGP)": "الإيرادات (ج.م)",
    "Room $": "رسوم الغرفة",
    "Room name is required.": "اسم الغرفة مطلوب.",
    "Spent: 0.00 EGP": "المنفق: 0.00 ج.م",
    "Spent: -": "المنفق: -",
    "Total Credit: 0.00": "إجمالي الدائن: 0.00",
    "Total Inventory Value: 0.00 EGP": "إجمالي قيمة المخزون: 0.00 ج.م",
    "Total Liabilities": "إجمالي الالتزامات",
    "Total Revenue": "إجمالي الإيرادات",
    "Total Value: 0.00 EGP": "إجمالي القيمة: 0.00 ج.م",
    "Total: 0 EGP": "الإجمالي: 0 ج.م",
    "Total: 0.00 EGP": "الإجمالي: 0.00 ج.م",
    "Type product name.": "اكتب اسم المنتج.",
    "Unit Cost:": "تكلفة الوحدة:",
    "e.g. Study Room C": "مثال: غرفة دراسة ج",
}

# Now for the emoji ones
# First extract real emojis directly from pages.py to avoid ? marks
with open('pages.py', 'r', encoding='utf-8') as f:
    pages_code = f.read()

import re
import ast

tree = ast.parse(pages_code)
ui_funcs = {'QLabel':0, 'QPushButton':0, 'page_container':0, 'addRow':0, 'make_table':0}
class EVisitor(ast.NodeVisitor):
    def visit_Call(self, node):
        func_name = None
        if isinstance(node.func, ast.Name): func_name = node.func.id
        elif isinstance(node.func, ast.Attribute): func_name = node.func.attr
        if func_name in ui_funcs or 'page_container' in func_name:
            # check all args
            for arg in node.args:
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    s = arg.value
                    # if it has emoji and english letters
                    if len(s)>3 and not s.isascii():
                        # auto translate
                        eng_part = re.sub(r'[^\x00-\x7F]+', '', s).strip()
                        if eng_part in translations.TRANSLATIONS:
                            ar_part = translations.TRANSLATIONS[eng_part]
                            # replace eng part with ar part inside the string
                            ar_full = s.replace(eng_part, ar_part)
                            new_translations[s] = ar_full
                        elif eng_part.replace('  ', ' ') in translations.TRANSLATIONS:
                            ar_full = s.replace(eng_part, translations.TRANSLATIONS[eng_part.replace('  ', ' ')])
                            new_translations[s] = ar_full
        self.generic_visit(node)

EVisitor().visit(tree)

# Custom overrides
new_translations["⚙️  Settings"] = "⚙️  الإعدادات"
new_translations["🚨  Danger Zone"] = "🚨  منطقة الخطر"
new_translations["🔔  Notification Thresholds"] = "🔔  حدود التنبيهات"
new_translations["🗑️ Delete"] = "🗑️ حذف"
new_translations["✅ Mark Paid"] = "✅ تأشير مدفوع"
new_translations["💾  Save Invoice"] = "💾  حفظ الفاتورة"

with open('translations.py', 'r', encoding='utf-8') as f:
    t = f.read()
    
insert_idx = t.find('}')
lines = []
for k, v in new_translations.items():
    if f'"{k}"' not in t and f"'{k}'" not in t:
        lines.append(f'    "{k}": "{v}",')

t = t[:insert_idx] + '\n'.join(lines) + '\n' + t[insert_idx:]
with open('translations.py', 'w', encoding='utf-8') as f:
    f.write(t)

print("Added", len(lines), "new translations.")
