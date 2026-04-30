"""Phase 3: Product Portfolio & Fashion Assortment Analysis
Notebook cells: 3.1 ABC Pareto, 3.2 Size/Color Gap, 3.3 Category Mix & Margin
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils.charts import (
    apply_dark_theme, create_metric_card_html, format_number, format_currency, format_pct,
    PLOTLY_COLORS, COLOR_PRIMARY, COLOR_POS, COLOR_NEG, COLOR_SECONDARY, COLOR_NEU
)


def render(data):
    st.markdown("## 👗 Phase 3: Product Portfolio & Fashion Assortment")
    st.markdown("**Mục tiêu**: Tối ưu hóa danh mục sản phẩm, xác định sản phẩm chiến lược")
    st.markdown("---")

    order_items = data['order_items']
    products = data['products']
    inventory = data['inventory']
    returns = data['returns']

    # KPIs
    total_products = products['product_id'].nunique()
    total_categories = products['category'].nunique()
    total_sku_revenue = order_items['item_revenue'].sum()
    avg_margin_pct = ((order_items.merge(products[['product_id', 'cogs']], on='product_id')['unit_price'] -
                       order_items.merge(products[['product_id', 'cogs']], on='product_id')['cogs']) /
                      order_items.merge(products[['product_id', 'cogs']], on='product_id')['unit_price']).mean() * 100

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(create_metric_card_html("📦 Tổng Products", format_number(total_products)), unsafe_allow_html=True)
    with col2:
        st.markdown(create_metric_card_html("🗂️ Số Categories", str(total_categories)), unsafe_allow_html=True)
    with col3:
        st.markdown(create_metric_card_html("💰 Tổng SKU Revenue", format_currency(total_sku_revenue)), unsafe_allow_html=True)
    with col4:
        st.markdown(create_metric_card_html("📊 Avg Margin", f"{avg_margin_pct:.1f}%"), unsafe_allow_html=True)

    st.markdown("---")

    # ============================================================
    # 3.1 ABC Pareto Analysis
    # ============================================================
    st.markdown("### 📊 3.1 ABC Pareto Analysis — Phân loại sản phẩm theo đóng góp doanh thu")
    st.markdown("Không phải mọi sản phẩm đều quan trọng như nhau. Quy luật 80/20 giúp xác định trọng tâm.")

    product_revenue = (order_items.groupby('product_id')['item_revenue']
                       .sum().sort_values(ascending=False).reset_index())
    product_revenue.columns = ['product_id', 'total_revenue']
    product_revenue = product_revenue.merge(
        products[['product_id', 'product_name', 'category', 'segment']], on='product_id', how='left')
    product_revenue['cumulative_pct'] = (product_revenue['total_revenue'].cumsum()
                                         / product_revenue['total_revenue'].sum() * 100)
    product_revenue['rank'] = range(1, len(product_revenue) + 1)
    product_revenue['rank_pct'] = product_revenue['rank'] / len(product_revenue) * 100
    product_revenue['ABC_class'] = 'C'
    product_revenue.loc[product_revenue['cumulative_pct'] <= 80, 'ABC_class'] = 'A'
    product_revenue.loc[(product_revenue['cumulative_pct'] > 80) &
                        (product_revenue['cumulative_pct'] <= 95), 'ABC_class'] = 'B'

    colors_abc = {'A': COLOR_POS, 'B': '#f39c12', 'C': COLOR_NEG}

    fig1 = make_subplots(specs=[[{"secondary_y": True}]])
    for cls in ['A', 'B', 'C']:
        subset = product_revenue[product_revenue['ABC_class'] == cls]
        fig1.add_trace(go.Bar(x=subset['rank_pct'], y=subset['total_revenue'],
                              name=f'Class {cls}', marker_color=colors_abc[cls], opacity=0.65,
                              width=0.4),
                       secondary_y=False)
    fig1.add_trace(go.Scatter(x=product_revenue['rank_pct'], y=product_revenue['cumulative_pct'],
                              mode='lines', name='Cumulative %',
                              line=dict(color='#1a202c', width=2.5)),
                   secondary_y=True)
    fig1.add_hline(y=80, line_dash="dash", line_color=COLOR_POS, opacity=0.6,
                   secondary_y=True, annotation_text="80% Revenue (Class A)")
    fig1.add_hline(y=95, line_dash="dash", line_color='#f39c12', opacity=0.6,
                   secondary_y=True, annotation_text="95% Revenue (Class B)")
    fig1.update_layout(title="ABC Pareto Analysis: Phân loại sản phẩm theo đóng góp doanh thu",
                       xaxis_title="% Sản phẩm (xếp theo doanh thu giảm dần)",
                       height=520, barmode='stack')
    fig1.update_yaxes(title_text="Doanh thu (VND)", secondary_y=False)
    fig1.update_yaxes(title_text="Cumulative Revenue (%)", secondary_y=True)
    st.plotly_chart(apply_dark_theme(fig1), use_container_width=True)

    abc_summary = product_revenue.groupby('ABC_class').agg(
        product_count=('product_id', 'count'),
        total_rev=('total_revenue', 'sum')
    ).reset_index()
    abc_summary['% Products'] = (abc_summary['product_count'] / abc_summary['product_count'].sum() * 100).round(1)
    abc_summary['% Revenue'] = (abc_summary['total_rev'] / abc_summary['total_rev'].sum() * 100).round(1)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**ABC Classification Summary:**")
        st.dataframe(abc_summary, hide_index=True, use_container_width=True)
    with col2:
        fig1b = px.bar(abc_summary, x='ABC_class', y='% Revenue', color='ABC_class',
                       title="% Revenue theo Class",
                       color_discrete_map=colors_abc)
        fig1b.update_layout(height=250, showlegend=False)
        st.plotly_chart(apply_dark_theme(fig1b), use_container_width=True)

    st.markdown("---")

    # ============================================================
    # 3.2 Size & Color Gap Analysis
    # ============================================================
    st.markdown("### 🎨 3.2 Size & Color Gap Analysis — Lỗ hổng vận hành thời trang")
    st.markdown("Phân tích Sell-Through Rate và tần suất Stockout theo thuộc tính Size và Color.")

    # inventory already has product_name, category, segment but NOT size/color → need merge with products
    inv_with_attrs = inventory.merge(
        products[['product_id', 'size', 'color']], on='product_id', how='left'
    )

    col1, col2 = st.columns(2)
    with col1:
        size_color_str = inv_with_attrs.groupby(['size', 'color'])['sell_through_rate'].mean().unstack(fill_value=0)
        fig2a = go.Figure(data=go.Heatmap(
            z=size_color_str.values,
            x=size_color_str.columns.tolist(),
            y=size_color_str.index.tolist(),
            colorscale='RdYlGn',
            text=[[f"{v:.2f}" for v in row] for row in size_color_str.values],
            texttemplate='%{text}', textfont=dict(size=9),
            hovertemplate="Size: %{y}<br>Color: %{x}<br>Sell-through: %{z:.2f}<extra></extra>",
            zmin=0, zmax=1,
        ))
        fig2a.update_layout(title="Sell-Through Rate: Size vs Color<br>(Cao = bán tốt, Thấp = tồn kho)",
                            height=420)
        st.plotly_chart(apply_dark_theme(fig2a), use_container_width=True)
    with col2:
        size_color_stockout = inv_with_attrs.groupby(['size', 'color'])['stockout_flag'].mean().unstack(fill_value=0)
        fig2b = go.Figure(data=go.Heatmap(
            z=size_color_stockout.values,
            x=size_color_stockout.columns.tolist(),
            y=size_color_stockout.index.tolist(),
            colorscale='YlOrRd',
            text=[[f"{v:.2f}" for v in row] for row in size_color_stockout.values],
            texttemplate='%{text}', textfont=dict(size=9),
            hovertemplate="Size: %{y}<br>Color: %{x}<br>Stockout rate: %{z:.2f}<extra></extra>",
        ))
        fig2b.update_layout(title="Tỷ lệ Stockout: Size vs Color<br>(Cao = thường xuyên hết hàng)",
                            height=420)
        st.plotly_chart(apply_dark_theme(fig2b), use_container_width=True)

    # Wrong-size returns
    wrong_size = returns[returns['return_reason'].str.contains('size', case=False, na=False)]
    if len(wrong_size) > 0:
        ws_merged = wrong_size.merge(products[['product_id', 'size', 'category']], on='product_id', how='left')
        ws_by_size = ws_merged.groupby('size')['return_quantity'].sum().sort_values(ascending=False).reset_index()
        fig2c = px.bar(ws_by_size, x='size', y='return_quantity',
                       title="Số lượng hoàn hàng do 'wrong size' theo Size",
                       color='return_quantity', color_continuous_scale='Reds')
        fig2c.update_layout(height=330)
        st.plotly_chart(apply_dark_theme(fig2c), use_container_width=True)

    st.markdown("---")

    # ============================================================
    # 3.3 Category Mix & Margin Analysis
    # ============================================================
    st.markdown("### 📈 3.3 Category Mix & Margin Analysis")
    st.markdown("Phân tích cơ cấu doanh thu và biên lợi nhuận theo danh mục sản phẩm.")

    cat_analysis = order_items.merge(
        products[['product_id', 'category', 'segment', 'cogs']], on='product_id', how='left')
    cat_analysis['margin'] = ((cat_analysis['unit_price'] - cat_analysis['cogs'])
                              / cat_analysis['unit_price'].replace(0, np.nan) * 100)
    cat_summary = cat_analysis.groupby('category').agg(
        total_revenue=('item_revenue', 'sum'),
        total_quantity=('quantity', 'sum'),
        avg_margin=('margin', 'mean'),
        product_count=('product_id', 'nunique')
    ).sort_values('total_revenue', ascending=False).reset_index()
    cat_summary['revenue_share'] = cat_summary['total_revenue'] / cat_summary['total_revenue'].sum() * 100

    col1, col2 = st.columns(2)
    with col1:
        fig3a = px.pie(cat_summary, values='revenue_share', names='category',
                       title="Cơ cấu doanh thu theo Category",
                       color_discrete_sequence=PLOTLY_COLORS, hole=0.35)
        fig3a.update_layout(height=420)
        st.plotly_chart(apply_dark_theme(fig3a), use_container_width=True)
    with col2:
        fig3b = px.scatter(cat_summary, x='revenue_share', y='avg_margin',
                           size='total_quantity', text='category',
                           title="Revenue Share vs Margin<br>(kích thước = số lượng bán)",
                           labels={'revenue_share': 'Revenue Share (%)', 'avg_margin': 'Gross Margin (%)'},
                           color='category', color_discrete_sequence=PLOTLY_COLORS)
        fig3b.update_traces(textposition='top center')
        fig3b.add_hline(y=cat_summary['avg_margin'].mean(), line_dash="dash", line_color=COLOR_NEU, opacity=0.5)
        fig3b.add_vline(x=cat_summary['revenue_share'].mean(), line_dash="dash", line_color=COLOR_NEU, opacity=0.5)
        fig3b.update_layout(height=420, showlegend=False)
        st.plotly_chart(apply_dark_theme(fig3b), use_container_width=True)

    st.markdown("**Category Performance Table:**")
    st.dataframe(cat_summary.round(1), hide_index=True, use_container_width=True)
