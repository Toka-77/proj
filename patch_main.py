# -*- coding: utf-8 -*-
with open('main.py', 'r', encoding='utf-8') as f:
    m = f.read()

import re

# 1. Imports
if 'from translations import tr, set_lang, current_lang, is_arabic' not in m:
    m = m.replace('from core import SettingsManager, NotificationManager, UserManager',
                  'from core import SettingsManager, NotificationManager, UserManager\nfrom translations import tr, set_lang, current_lang, is_arabic\nfrom PyQt5.QtGui import QFont')

# 2. Login Window
m = m.replace('self.setWindowTitle("AIS Hub — Login")', 'self.setWindowTitle(tr("AIS Hub — Login"))')

# 3. AISApp __init__
init_str = '''
        self._theme = SettingsManager.get('theme', 'dark') or 'dark'
        self._toast_y_offset = 0

        self._build_ui()
        self._apply_theme()
        self._apply_role_restrictions()
'''
init_str_new = '''
        self._theme = SettingsManager.get('theme', 'dark') or 'dark'
        self._toast_y_offset = 0

        saved_lang = SettingsManager.get('language', 'ar') or 'ar'
        set_lang(saved_lang)

        self._build_ui()
        self._apply_theme()
        self._apply_lang_direction()
        self._apply_role_restrictions()
'''
m = m.replace(init_str, init_str_new)

# 4. Nav Keys inside _build_ui
build_ui_str = '''
        self.nav_btns = []
        for icon, label in self.NAV_KEYS:
            btn = NavButton(icon, label)
'''
build_ui_str_new = '''
        self.nav_btns = []
        for icon, label in self.NAV_KEYS:
            btn = NavButton(icon, tr(label))
'''
m = m.replace(build_ui_str, build_ui_str_new)

# 5. Language Switcher Button
theme_str = '''
        self.theme_btn.setToolTip("Toggle Dark / Light mode")
        sb.addWidget(self.theme_btn)
'''
theme_str_new = '''
        self.theme_btn.setToolTip(tr("Toggle Dark / Light mode"))
        
        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)
        btn_row.addWidget(self.theme_btn)
        
        self.lang_btn = QPushButton("🌐 EN" if is_arabic() else "🌐 AR")
        self.lang_btn.setObjectName("icon_btn")
        self.lang_btn.setFixedHeight(34)
        self.lang_btn.setCursor(Qt.PointingHandCursor)
        self.lang_btn.clicked.connect(self.toggle_lang)
        self.lang_btn.setToolTip(tr("Switch language / تغيير اللغة"))
        btn_row.addWidget(self.lang_btn)
        
        sb.addLayout(btn_row)
'''
m = m.replace(theme_str, theme_str_new)

# 6. Apply lang direction and toggle method
methods_str = '''
    def _apply_theme(self):
        QApplication.instance().setStyleSheet(get_qss(self._theme))
'''
methods_str_new = '''
    def _apply_theme(self):
        QApplication.instance().setStyleSheet(get_qss(self._theme))

    def toggle_lang(self):
        new_lang = 'ar' if current_lang() == 'en' else 'en'
        set_lang(new_lang)
        SettingsManager.set('language', new_lang)
        self.lang_btn.setText("🌐 EN" if new_lang == 'ar' else "🌐 AR")
        
        for i, (icon, label) in enumerate(self.NAV_KEYS):
            self.nav_btns[i].setText(f"{icon}  {tr(label)}")
            
        self._apply_lang_direction()
        self.refresh_all()

    def _apply_lang_direction(self):
        app = QApplication.instance()
        if is_arabic():
            app.setLayoutDirection(Qt.RightToLeft)
            app.setFont(QFont("Arial", 10))
        else:
            app.setLayoutDirection(Qt.LeftToRight)
            app.setFont(QFont("Segoe UI", 10))
'''
m = m.replace(methods_str, methods_str_new)

# wrap hardcoded things in tr
m = m.replace('"Co-Working Space AIS — Accounting Information System"', 'tr("Co-Working Space AIS — Accounting Information System")')
m = m.replace('("🔴 Admin" if role == \'admin\' else "🎫 Employee")', '(tr("🔴 Admin") if role == \'admin\' else tr("🎫 Employee"))')
m = m.replace('"🚪 Logout"', 'tr("🚪 Logout")')

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(m)

print("Patched main.py")
