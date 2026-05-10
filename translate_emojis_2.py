# -*- coding: utf-8 -*-
with open('extracted_ui.txt', 'r', encoding='utf-8') as f:
    lines = f.read().splitlines()

# Extract the emojis from pages.py
with open('pages.py', 'r', encoding='utf-8') as f:
    pages_code = f.read()

import re
import ast
import translations

new_translations = {
    "Enter customer name.": "أدخل اسم العميل.",
    "Type product name.": "اكتب اسم المنتج.",
    "Points: -": "النقاط: -",
    "Spent: -": "المنفق: -",
}

tree = ast.parse(pages_code)
ui_funcs = {'QLabel':0, 'QPushButton':0, 'page_container':0, 'addRow':0, 'make_table':0}
class EVisitor(ast.NodeVisitor):
    def visit_Call(self, node):
        func_name = None
        if isinstance(node.func, ast.Name): func_name = node.func.id
        elif isinstance(node.func, ast.Attribute): func_name = node.func.attr
        if func_name in ui_funcs or 'page_container' in func_name:
            for arg in node.args:
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    s = arg.value
                    if len(s)>3 and not s.isascii():
                        eng_part = re.sub(r'[^\x00-\x7F]+', '', s).strip()
                        if eng_part in translations.TRANSLATIONS:
                            new_translations[s] = s.replace(eng_part, translations.TRANSLATIONS[eng_part])
                        elif eng_part.replace('  ', ' ') in translations.TRANSLATIONS:
                            new_translations[s] = s.replace(eng_part, translations.TRANSLATIONS[eng_part.replace('  ', ' ')])
                        elif eng_part == "Bronze": new_translations[s] = s.replace("Bronze", "برونزي")
                        elif eng_part == "PDF": new_translations[s] = s.replace("PDF", "تصدير PDF")
                        elif "Start New Financial Year" in eng_part: new_translations[s] = "⚠️ بدء سنة مالية جديدة"
                        elif "Edit Price" in eng_part: new_translations[s] = s.replace(eng_part, "تعديل السعر والتكلفة")
                        elif "Customer Lookup" in eng_part: new_translations[s] = s.replace(eng_part, "بحث عن عميل")
        self.generic_visit(node)

EVisitor().visit(tree)

with open('translations.py', 'r', encoding='utf-8') as f:
    t = f.read()
    
insert_idx = t.find('}')
out = []
for k, v in new_translations.items():
    if f'"{k}"' not in t and f"'{k}'" not in t:
        out.append(f'    "{k}": "{v}",')

t = t[:insert_idx] + '\n'.join(out) + '\n' + t[insert_idx:]
with open('translations.py', 'w', encoding='utf-8') as f:
    f.write(t)
