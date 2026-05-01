"""
E-Commerce Fashion Vietnam - EDA Storytelling Dashboard
Main application entry point.

Run with: streamlit run app.py
"""
import streamlit as st
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.constants import PAGE_TITLE, PAGE_ICON, LAYOUT, PHASE_NAMES
from utils.data_loader import load_and_transform_data

# Page config
st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout=LAYOUT,
    initial_sidebar_state="expanded",
)

# Custom CSS for premium look
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* Main background - clean light */
    .stApp {
        background: #f8f9fc;
        font-family: 'Inter', sans-serif;
    }

    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e3a5f 0%, #2c5282 100%);
        border-right: none;
        box-shadow: 2px 0 12px rgba(0,0,0,0.08);
    }
    section[data-testid="stSidebar"] * {
        color: #e2e8f0 !important;
    }
    section[data-testid="stSidebar"] .stRadio label:hover {
        background: rgba(255,255,255,0.1);
        border-radius: 6px;
    }

    /* Header styling */
    h1, h2, h3 {
        color: #1a202c !important;
        font-family: 'Inter', sans-serif !important;
    }
    h2 {
        border-bottom: 2px solid #3182ce;
        padding-bottom: 8px;
    }

    /* Body text */
    p, span, li, div {
        color: #2d3748;
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background: #fff;
        border-radius: 10px;
        padding: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border: none;
        border-radius: 8px;
        padding: 8px 16px;
        color: #718096;
    }
    .stTabs [aria-selected="true"] {
        background: #3182ce !important;
        color: #ffffff !important;
        border-radius: 8px;
    }

    /* Metric cards */
    [data-testid="stMetricValue"] {
        font-size: 24px;
        font-weight: 700;
        color: #1a202c;
    }

    /* Dataframe styling */
    .stDataFrame {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 1px 6px rgba(0,0,0,0.06);
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Custom divider */
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, #cbd5e0, transparent);
        margin: 24px 0;
    }

    /* Plotly chart containers */
    .js-plotly-plot {
        border-radius: 12px;
        box-shadow: 0 1px 8px rgba(0,0,0,0.05);
    }

    /* Blockquote styling for insights */
    blockquote {
        background: #ebf8ff !important;
        border-left: 4px solid #3182ce !important;
        border-radius: 0 8px 8px 0;
        padding: 12px 16px !important;
        color: #2d3748 !important;
    }
</style>
""", unsafe_allow_html=True)


def main():
    # Sidebar
    with st.sidebar:
        st.markdown("""
        <div style="text-align:center; padding: 16px 0;">
            <h2 style="margin:0; font-size:20px;">📊 EDA Dashboard</h2>
            <p style="color:#95a5a6; font-size:12px; margin:4px 0 0 0;">
                E-Commerce Fashion Vietnam
            </p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("---")

        selected_phase = st.radio(
            "📑 Chọn Phase phân tích",
            PHASE_NAMES,
            index=0,
        )

        st.markdown("---")
        st.markdown("""
        <div style="text-align:center; color:#7f8c8d; font-size:11px;">
            <p>Dữ liệu: 13 datasets</p>
            <p>8 giai đoạn phân tích</p>
            <p>EDA Storytelling Masterpiece v2</p>
        </div>
        """, unsafe_allow_html=True)

    # Main content
    st.markdown(f"""
    <h1 style="text-align:center; font-size:28px; margin-bottom:4px;">
        Báo Cáo Phân Tích Dữ Liệu Kinh Doanh
    </h1>
    <p style="text-align:center; color:#95a5a6; font-size:14px; margin-bottom:24px;">
        EDA Storytelling Masterpiece — E-Commerce Fashion Vietnam
    </p>
    """, unsafe_allow_html=True)

    # Load data with spinner
    with st.spinner("⏳ Đang tải dữ liệu..."):
        data = load_and_transform_data()

    # Route to the selected phase
    phase_index = PHASE_NAMES.index(selected_phase)

    if phase_index == 0:
        from views.phase0_data_quality import render
        render(data)
    elif phase_index == 1:
        from views.phase1_business_pulse import render
        render(data)
    elif phase_index == 2:
        from views.phase2_acquisition import render
        render(data)
    elif phase_index == 3:
        from views.phase3_product import render
        render(data)
    elif phase_index == 4:
        from views.phase4_sales import render
        render(data)
    elif phase_index == 5:
        from views.phase5_operations import render
        render(data)
    elif phase_index == 6:
        from views.phase6_retention import render
        render(data)
    elif phase_index == 7:
        from views.phase7_summary import render
        render(data)


if __name__ == "__main__":
    main()
