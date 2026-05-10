# -*- coding: utf-8 -*-
with open('translations.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Just replace actual newlines that are inside strings
# A simple heuristic: if a line doesn't start with 4 spaces or }, it's a broken newline
lines = text.split('\n')
fixed = []
for line in lines:
    if line.startswith('    "') or line.startswith('}'):
        fixed.append(line)
    elif line.startswith('def ') or line.startswith('    ') or line.startswith('import ') or line.startswith('"""') or line.startswith('_lang') or line.startswith('TRANSLATIONS') or line == '':
        fixed.append(line)
    else:
        # it's a continuation of the previous line
        fixed[-1] = fixed[-1] + r'\n' + line

with open('translations.py', 'w', encoding='utf-8') as f:
    f.write('\n'.join(fixed))
print("Fixed translations.py")
