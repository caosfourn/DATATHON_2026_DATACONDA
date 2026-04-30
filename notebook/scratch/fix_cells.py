import json

with open('notebook/05_eda_storytelling_masterpiece_v2.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Fix cells 53, 54, 55 — add newlines to source lines
for idx in [53, 54, 55]:
    src = nb['cells'][idx]['source']
    new_src = []
    for i, line in enumerate(src):
        if i < len(src) - 1:
            if not line.endswith('\n'):
                new_src.append(line + '\n')
            else:
                new_src.append(line)
        else:
            new_src.append(line)  # Last line no newline
    nb['cells'][idx]['source'] = new_src

with open('notebook/05_eda_storytelling_masterpiece_v2.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print("Fixed newlines in cells 53-55")
