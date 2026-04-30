"""
Color palette and constants for the EDA Dashboard.
Matching the notebook's design system.
"""

# Color palette matching the notebook
COLOR_POS = '#2ecc71'    # Green - positive
COLOR_NEG = '#e74c3c'    # Red - risk
COLOR_NEU = '#95a5a6'    # Gray - neutral
COLOR_PRIMARY = '#3498db'
COLOR_SECONDARY = '#9b59b6'

PALETTE = [
    COLOR_PRIMARY, COLOR_NEG, COLOR_POS, COLOR_SECONDARY,
    '#f39c12', '#1abc9c', '#e67e22', '#34495e'
]

# Plotly-compatible color sequence
PLOTLY_COLORS = [
    '#3498db', '#e74c3c', '#2ecc71', '#9b59b6',
    '#f39c12', '#1abc9c', '#e67e22', '#34495e',
    '#e84393', '#00cec9', '#fdcb6e', '#6c5ce7'
]

# Data directory (relative to dashboard/)
DATA_DIR = '../dataset/'

# Dashboard config
PAGE_TITLE = "E-Commerce Fashion Vietnam - EDA Dashboard"
PAGE_ICON = "📊"
LAYOUT = "wide"

# Phase names for navigation
PHASE_NAMES = [
    "📋 Phase 0: Data Quality",
    "📈 Phase 1: Business Pulse",
    "🎯 Phase 2: Acquisition",
    "👗 Phase 3: Product Portfolio",
    "💰 Phase 4: Sales Performance",
    "🚚 Phase 5: Operations",
    "🔄 Phase 6: Retention & CLV",
    "📊 Phase 7: Executive Summary",
]
