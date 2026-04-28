import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

nb = json.load(open('notebook/05_eda_storytelling_masterpiece.ipynb', 'r', encoding='utf-8'))
cells = nb['cells']

for i, c in enumerate(cells):
    ct = c['cell_type']
    src = ''.join(c['source'][:3])[:300]
    print(f"--- Cell {i} ({ct}) ---")
    print(src)
    print()
