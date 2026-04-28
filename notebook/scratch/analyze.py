import json
import sys

def analyze_nb(path):
    with open(path, 'r', encoding='utf-8') as f:
        nb = json.load(f)
    print(f'Analyzing {path}: {len(nb["cells"])} cells')
    for i, cell in enumerate(nb['cells']):
        if cell['cell_type'] == 'markdown':
            source = ''.join(cell.get('source', []))
            if any(h in source for h in ['#', 'GIAI ÐO?N', 'Descriptive', 'Diagnostic', 'Predictive', 'Prescriptive']):
                print(f'Cell {i} (MD): {source[:100].replace(chr(10), " ")}')
        elif cell['cell_type'] == 'code':
            source = ''.join(cell.get('source', []))
            src_lower = source.lower()
            if 'import' in source or 'plt' in source or 'sns' in source or 'rfm' in src_lower or 'cohort' in src_lower or 'basket' in src_lower:
                print(f'Cell {i} (CODE snippet): {source[:60].replace(chr(10), " ")}')

analyze_nb('d:/HuynhHan/Datathon/DATATHON_2026_DATACONDA/notebook/05_eda_storytelling_final.ipynb')
