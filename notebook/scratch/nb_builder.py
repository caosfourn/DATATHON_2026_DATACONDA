"""
Notebook builder - tạo file .ipynb từ các cell definitions.
Chạy: python notebook/scratch/nb_builder.py
"""
import json, os, sys, importlib

cells = []

def md(text):
    """Add markdown cell"""
    lines = text.strip().split('\n')
    source = [l + '\n' for l in lines[:-1]] + [lines[-1]]
    cells.append({"cell_type": "markdown", "metadata": {}, "source": source})

def code(text):
    """Add code cell"""
    lines = text.strip().split('\n')
    source = [l + '\n' for l in lines[:-1]] + [lines[-1]]
    cells.append({"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": source})

# Import all phase modules
sys.path.insert(0, os.path.dirname(__file__))
for phase_file in sorted([f for f in os.listdir(os.path.dirname(__file__)) if f.startswith('phase_') and f.endswith('.py')]):
    mod_name = phase_file[:-3]
    print(f"Loading {mod_name}...")
    mod = importlib.import_module(mod_name)
    mod.build(md, code)

# Assemble notebook
notebook = {
    "nbformat": 4,
    "nbformat_minor": 5,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.10.0"}
    },
    "cells": cells
}

out_path = os.path.join(os.path.dirname(__file__), '..', '05_eda_storytelling_masterpiece_v2.ipynb')
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(notebook, f, ensure_ascii=False, indent=1)

print(f"\nNotebook saved to: {os.path.abspath(out_path)}")
print(f"Total cells: {len(cells)}")
