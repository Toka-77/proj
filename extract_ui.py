# -*- coding: utf-8 -*-
import ast

with open('pages.py', 'r', encoding='utf-8') as f:
    source = f.read()

tree = ast.parse(source)

ui_strings = set()

class UIStringVisitor(ast.NodeVisitor):
    def visit_Call(self, node):
        func_name = None
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr

        ui_funcs = {
            'QLabel': [0],
            'QPushButton': [0],
            'QMessageBox.warning': [1, 2],
            'QMessageBox.information': [1, 2],
            'QMessageBox.question': [1, 2],
            'warning': [1, 2],
            'information': [1, 2],
            'question': [1, 2],
            'StatCard': [1, 2],
            'page_container': [0, 1],
            'addRow': [0],
            'addItems': [0],
            'make_table': [0],
            'setPlaceholderText': [0],
            'setText': [0]
        }

        if func_name in ui_funcs:
            for idx in ui_funcs[func_name]:
                if idx < len(node.args):
                    arg = node.args[idx]
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                        ui_strings.add(arg.value)
                    elif isinstance(arg, ast.List):
                        for el in arg.elts:
                            if isinstance(el, ast.Constant) and isinstance(el.value, str):
                                ui_strings.add(el.value)

        self.generic_visit(node)

UIStringVisitor().visit(tree)

import translations
for k in translations.TRANSLATIONS:
    if k in ui_strings:
        ui_strings.remove(k)

skip_words = ['root', 'title', 'subtitle', 'sec_title', 'icon_btn', 'danger', 'primary', 'secondary', 'AIS Hub', 'AIS v3.0', 'yyyy-MM-dd', 'HH:mm']

filtered = []
for s in ui_strings:
    if len(s) < 3: continue
    if any(sw in s for sw in skip_words): continue
    filtered.append(s)

with open('extracted_ui.txt', 'w', encoding='utf-8') as f:
    for s in sorted(filtered):
        f.write(s + '\n')
