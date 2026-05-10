# -*- coding: utf-8 -*-
with open('translations.py', 'r', encoding='utf-8') as f:
    t = f.read()

missing = {
    'Account Name:': 'اسم الحساب:',
    'Account Statements': 'كشوف الحسابات',
    'Account Type:': 'نوع الحساب:',
    'Accounts Payable': 'ذمم دائنة',
    'All': 'الكل',
    'Auto-filled on row select': 'يُملأ عند الاختيار',
    'Description:': 'الوصف:',
    'Drinks': 'مشروبات',
    'Elapsed': 'المدة المنقضية',
    'Gaming': 'ألعاب',
    'Hot': 'مشروبات ساخنة',
    'Name:': 'الاسم:',
    'No active session.': 'لا توجد جلسة نشطة.',
    'No available room.': 'لا توجد غرفة متاحة.',
    'Optional description': 'وصف (اختياري)',
    'Other': 'أخرى',
    'Price': 'السعر',
    'Price/hr:': 'السعر/ساعة:',
    'Product name (editable)': 'اسم المنتج (قابل للتعديل)',
    'Product updated.': 'تم تحديث المنتج.',
    'Profit': 'ربح',
    'SKU:': 'الكود:',
    'Sale Price:': 'سعر البيع:',
    'Select Product': 'اختيار منتج',
    'Select a product row, then update its selling price and cost.': 'اختر منتجاً لتعديل سعره وتكلفته.',
    'Select an invoice.': 'اختر فاتورة.',
    'Snacks & Inventory': 'المخزون والسناكس',
    'Started': 'البداية',
    'Study': 'دراسة',
    'To:': 'إلى:',
    'Total Assets': 'إجمالي الأصول',
    'Total Debit: 0.00': 'إجمالي المدين: 0.00',
    'Total Equity': 'إجمالي حقوق الملكية',
    'Total Expenses': 'إجمالي المصروفات',
    'Total: 0.00': 'الإجمالي: 0.00',
    'Type:': 'النوع:',
    'Unpaid Invoice Alert:': 'تنبيه الفواتير غير المدفوعة:',
    'Accounting & Finance': 'المحاسبة والتمويل',
    'Reservations & Bookings': 'الحجوزات والمواعيد',
    'Real-time Overview': 'نظرة عامة فورية',
    'Total Rooms': 'إجمالي الغرف',
    'Rooms & Sessions': 'الغرف والجلسات',
}

insert_idx = t.find('}')
lines = []
for k, v in missing.items():
    if f'"{k}"' not in t and f"'{k}'" not in t:
        lines.append(f'    "{k}": "{v}",')

t = t[:insert_idx] + '\n'.join(lines) + '\n' + t[insert_idx:]

with open('translations.py', 'w', encoding='utf-8') as f:
    f.write(t)
print('Missing translations appended.')
