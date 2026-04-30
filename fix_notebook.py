import json
import re

notebook_path = 'notebook/05_eda_storytelling_masterpiece_v2.ipynb'

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

current_phase = 0
counter = 0

new_cells = []

# Regex patterns
code_header_pattern = re.compile(r'^# === ([\d\.]+) (.*?)( ===|\n)')

for i, cell in enumerate(nb['cells']):
    # If it's a markdown cell indicating a Phase change
    if cell['cell_type'] == 'markdown':
        source = "".join(cell['source'])
        phase_match = re.search(r'# PHASE (\d+):', source)
        if phase_match:
            current_phase = int(phase_match.group(1))
            counter = 0 # reset counter
        new_cells.append(cell)
        continue

    # If it's a code cell, look for the header
    if cell['cell_type'] == 'code':
        source_lines = cell['source']
        if not source_lines:
            new_cells.append(cell)
            continue
            
        first_line = source_lines[0]
        match = code_header_pattern.search(first_line)
        if match and current_phase > 0:
            counter += 1
            # Clean up the old title (remove old numbers)
            raw_title = match.group(2).strip()
            # Sometimes title looks like "Monthly Revenue...", sometimes it's "1.6 WATERFALL..."
            clean_title = re.sub(r'^[\d\.]+\s+', '', raw_title)
            
            new_num = f"{current_phase}.{counter}"
            new_first_line = f"# === {new_num} {clean_title} ===\n"
            source_lines[0] = new_first_line
            cell['source'] = source_lines
            
            # Now, check the PREVIOUS cell in new_cells to see if it's a markdown heading
            # We want to make sure it has a heading. 
            # Look backwards in new_cells for the last markdown cell before any other code cell
            found_heading = False
            for j in range(len(new_cells)-1, -1, -1):
                if new_cells[j]['cell_type'] == 'code':
                    break # Don't go past previous code cell
                if new_cells[j]['cell_type'] == 'markdown':
                    md_source = new_cells[j]['source']
                    if md_source and md_source[0].startswith('### '):
                        # Found a heading! Update it.
                        old_md_title = md_source[0].strip().replace('### ', '')
                        clean_md_title = re.sub(r'^[\d\.]+\s+', '', old_md_title)
                        md_source[0] = f"### {new_num}. {clean_md_title}\n"
                        new_cells[j]['source'] = md_source
                        found_heading = True
                        break
            
            if not found_heading:
                # Insert a new markdown cell right before this code cell
                new_md_cell = {
                    "cell_type": "markdown",
                    "metadata": {},
                    "source": [
                        f"### {new_num}. {clean_title}\n"
                    ]
                }
                new_cells.append(new_md_cell)
            
        new_cells.append(cell)

nb['cells'] = new_cells

with open(notebook_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print("Notebook format updated successfully!")
