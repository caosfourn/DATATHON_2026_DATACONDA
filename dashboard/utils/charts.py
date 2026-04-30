"""
Chart creation utilities for the EDA Dashboard.
Uses Plotly for interactive charts.
"""
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

from utils.constants import PLOTLY_COLORS, COLOR_POS, COLOR_NEG, COLOR_NEU, COLOR_PRIMARY, COLOR_SECONDARY


def apply_dark_theme(fig):
    """Apply a consistent light theme to all charts."""
    fig.update_layout(
        template='plotly_white',
        paper_bgcolor='#ffffff',
        plot_bgcolor='#fafbfc',
        font=dict(family='Inter, sans-serif', size=12, color='#2d3748'),
        margin=dict(l=40, r=40, t=60, b=40),
        title_font=dict(color='#1a202c', size=16),
    )
    fig.update_xaxes(gridcolor='#e2e8f0', zerolinecolor='#cbd5e0')
    fig.update_yaxes(gridcolor='#e2e8f0', zerolinecolor='#cbd5e0')
    return fig


def create_metric_card_html(label, value, delta=None, delta_color="normal"):
    """Create an HTML metric card with custom styling."""
    delta_html = ""
    if delta is not None:
        color = COLOR_POS if delta_color == "normal" and delta >= 0 else COLOR_NEG
        arrow = "▲" if delta >= 0 else "▼"
        delta_html = f'<p style="color:{color}; font-size:14px; margin:0;">{arrow} {delta}</p>'

    return f"""
    <div style="
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 1px 6px rgba(0,0,0,0.04);
        transition: box-shadow 0.2s;
    ">
        <p style="color:#718096; font-size:12px; margin:0 0 8px 0; text-transform:uppercase; letter-spacing:1px; font-weight:600;">{label}</p>
        <p style="color:#1a202c; font-size:26px; font-weight:700; margin:0 0 4px 0;">{value}</p>
        {delta_html}
    </div>
    """


def create_heatmap(pivot_df, title="Heatmap"):
    """Create a heatmap from a pivot table."""
    fig = go.Figure(data=go.Heatmap(
        z=pivot_df.values,
        x=pivot_df.columns.tolist(),
        y=pivot_df.index.tolist(),
        colorscale='YlOrRd',
        text=pivot_df.values.round(1),
        texttemplate='%{text}%',
        textfont=dict(size=10),
        hoverongaps=False,
    ))
    fig.update_layout(title=title, height=400)
    return apply_dark_theme(fig)


def create_line_chart(df, x, y, title="", labels=None, color=None):
    """Create a line chart."""
    fig = px.line(df, x=x, y=y, title=title, labels=labels, color=color,
                  color_discrete_sequence=PLOTLY_COLORS)
    fig.update_layout(height=400)
    return apply_dark_theme(fig)


def create_bar_chart(df, x, y, title="", orientation='v', color=None, labels=None):
    """Create a bar chart."""
    fig = px.bar(df, x=x, y=y, title=title, orientation=orientation,
                 color=color, labels=labels,
                 color_discrete_sequence=PLOTLY_COLORS)
    fig.update_layout(height=400)
    return apply_dark_theme(fig)


def create_scatter_chart(df, x, y, size=None, color=None, text=None, title=""):
    """Create a scatter chart with quadrant lines."""
    fig = px.scatter(df, x=x, y=y, size=size, color=color, text=text,
                     title=title, color_discrete_sequence=PLOTLY_COLORS)
    fig.update_traces(textposition='top center')
    fig.update_layout(height=500)
    return apply_dark_theme(fig)


def create_dual_axis_chart(df, x, y1, y2, name1="", name2="", title=""):
    """Create a chart with two Y axes."""
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Scatter(x=df[x], y=df[y1], name=name1, line=dict(color=COLOR_PRIMARY)),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(x=df[x], y=df[y2], name=name2, line=dict(color=COLOR_NEG)),
        secondary_y=True,
    )
    fig.update_layout(title=title, height=400)
    fig.update_yaxes(title_text=name1, secondary_y=False)
    fig.update_yaxes(title_text=name2, secondary_y=True)
    return apply_dark_theme(fig)


def create_pie_chart(df, values, names, title=""):
    """Create a pie/donut chart."""
    fig = px.pie(df, values=values, names=names, title=title, hole=0.4,
                 color_discrete_sequence=PLOTLY_COLORS)
    fig.update_layout(height=400)
    return apply_dark_theme(fig)


def create_cohort_heatmap(cohort_data, title="Cohort Analysis"):
    """Create a cohort retention heatmap."""
    fig = go.Figure(data=go.Heatmap(
        z=cohort_data.values,
        x=[f"Month {i}" for i in range(cohort_data.shape[1])],
        y=cohort_data.index.astype(str).tolist(),
        colorscale='Blues',
        text=cohort_data.values.round(1),
        texttemplate='%{text}%',
        textfont=dict(size=9),
    ))
    fig.update_layout(title=title, height=500)
    return apply_dark_theme(fig)


def format_number(n, decimals=0):
    """Format a number with commas."""
    if pd.isna(n):
        return "N/A"
    if decimals == 0:
        return f"{int(n):,}"
    return f"{n:,.{decimals}f}"


def format_currency(n):
    """Format as Vietnamese currency."""
    if pd.isna(n):
        return "N/A"
    return f"{n:,.0f} VND"


def format_pct(n, decimals=1):
    """Format as percentage."""
    if pd.isna(n):
        return "N/A"
    return f"{n:.{decimals}f}%"
