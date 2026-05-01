"""Phase 2: Customer Acquisition Analysis
Notebook cells: 2.1, 2.2 (Channel Quality Quadrant), 2.3 Traffic Trend, 2.4 Device Type
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
    st.markdown("## 🎯 Phase 2: Acquisition & Channel Performance")
    st.markdown("**Mục tiêu**: Đánh giá hiệu quả các kênh thu hút khách hàng")
    st.markdown("---")

    orders = data['orders']
    customers = data['customers']
    web_traffic = data['web_traffic']

    # KPI row
    total_customers = customers['customer_id'].nunique()
    channels = customers['acquisition_channel'].nunique()
    avg_sessions = web_traffic['sessions'].mean()
    avg_bounce = web_traffic['bounce_rate'].mean()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(create_metric_card_html("👥 Tổng Khách Hàng", format_number(total_customers)), unsafe_allow_html=True)
    with col2:
        st.markdown(create_metric_card_html("📡 Số Kênh", str(channels)), unsafe_allow_html=True)
    with col3:
        st.markdown(create_metric_card_html("🌐 Sessions TB/ngày", format_number(int(avg_sessions))), unsafe_allow_html=True)
    with col4:
        st.markdown(create_metric_card_html("📉 Bounce Rate TB", f"{avg_bounce:.1%}"), unsafe_allow_html=True)

    st.markdown("---")

    # ============================================================
    # 2.1 Channel Performance Scorecard
    # ============================================================
    st.markdown("### 📊 2.1 Channel Performance Scorecard")
    st.markdown("Phân tích số lượng khách hàng, đơn hàng trung bình và tổng chi tiêu theo từng kênh tiếp thị.")

    channel_stats = customers.merge(
        orders.groupby('customer_id').agg(
            order_count=('order_id', 'count'),
            total_spent=('total_amount', 'sum')
        ).reset_index(),
        on='customer_id', how='inner'
    )
    channel_summary = channel_stats.groupby('acquisition_channel').agg(
        customer_count=('customer_id', 'count'),
        avg_orders=('order_count', 'mean'),
        avg_spent=('total_spent', 'mean'),
        total_revenue=('total_spent', 'sum')
    ).sort_values('total_revenue', ascending=False).reset_index()
    channel_summary['revenue_share'] = channel_summary['total_revenue'] / channel_summary['total_revenue'].sum() * 100

    col1, col2 = st.columns(2)
    with col1:
        fig1a = px.bar(channel_summary, x='acquisition_channel', y='customer_count',
                       title="Số khách hàng theo kênh",
                       color='acquisition_channel', color_discrete_sequence=PLOTLY_COLORS,
                       labels={'acquisition_channel': 'Kênh', 'customer_count': 'Số KH'})
        fig1a.update_layout(height=380, showlegend=False)
        st.plotly_chart(apply_dark_theme(fig1a), use_container_width=True)
    with col2:
        fig1b = px.bar(channel_summary, x='acquisition_channel', y='avg_spent',
                       title="Chi tiêu trung bình / khách hàng",
                       color='acquisition_channel', color_discrete_sequence=PLOTLY_COLORS,
                       labels={'acquisition_channel': 'Kênh', 'avg_spent': 'Avg Spent (VND)'})
        fig1b.update_layout(height=380, showlegend=False)
        st.plotly_chart(apply_dark_theme(fig1b), use_container_width=True)

    st.markdown("**Channel Summary Table:**")
    st.dataframe(channel_summary.round(0), hide_index=True, use_container_width=True)

    st.markdown("---")

    # ============================================================
    # 2.2 Channel Quality Quadrant (Volume vs AOV)
    # ============================================================
    st.markdown("### 🎯 2.2 Ma trận Chiến lược Kênh (Channel Quality Quadrant)")
    st.markdown("Đánh giá từng nguồn đơn hàng dựa trên cả **khối lượng** lẫn **chất lượng** (AOV).")

    source_stats = orders.groupby('order_source').agg(
        order_count=('order_id', 'count'),
        avg_amount=('total_amount', 'mean'),
        total_rev=('total_amount', 'sum')
    ).reset_index()

    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=source_stats['order_count'],
        y=source_stats['avg_amount'],
        mode='markers+text',
        text=source_stats['order_source'],
        textposition='top center',
        marker=dict(
            size=source_stats['total_rev'] / source_stats['total_rev'].max() * 45 + 12,
            color=PLOTLY_COLORS[:len(source_stats)],
            opacity=0.8,
            line=dict(width=1.5, color='white')
        ),
        hovertemplate='<b>%{text}</b><br>Đơn hàng: %{x:,}<br>AOV: %{y:,.0f}<extra></extra>'
    ))
    mean_count = source_stats['order_count'].mean()
    mean_aov = source_stats['avg_amount'].mean()
    fig2.add_hline(y=mean_aov, line_dash="dash", line_color=COLOR_NEU, opacity=0.5,
                   annotation_text="AOV trung bình")
    fig2.add_vline(x=mean_count, line_dash="dash", line_color=COLOR_NEU, opacity=0.5,
                   annotation_text="Volume trung bình")
    # Quadrant labels
    xmax = source_stats['order_count'].max() * 1.1
    ymax = source_stats['avg_amount'].max() * 1.1
    for txt, x, y, color in [
        ("⭐ STARS", xmax * 0.75, ymax * 0.92, COLOR_POS),
        ("🚀 GROWTH", xmax * 0.15, ymax * 0.92, COLOR_PRIMARY),
        ("💰 CASH COW", xmax * 0.75, mean_aov * 0.65, COLOR_SECONDARY),
        ("⚠️ REVIEW", xmax * 0.15, mean_aov * 0.65, COLOR_NEG),
    ]:
        fig2.add_annotation(x=x, y=y, text=txt, showarrow=False,
                            font=dict(size=11, color=color), opacity=0.4)
    fig2.update_layout(
        title="Channel Quality Quadrant: Volume vs AOV (kích thước = tổng doanh thu)",
        xaxis_title="Số lượng đơn hàng", yaxis_title="AOV (Giá trị đơn TB)",
        height=500
    )
    st.plotly_chart(apply_dark_theme(fig2), use_container_width=True)

    st.markdown("---")

    # ============================================================
    # 2.3 Traffic Trend (Sessions + Bounce Rate)
    # ============================================================
    st.markdown("### 📈 2.3 Xu hướng Lưu lượng và Chất lượng truy cập theo thời gian")

    monthly_traffic = web_traffic.groupby(web_traffic['date'].dt.to_period('M')).agg(
        sessions=('sessions', 'sum'),
        bounce=('bounce_rate', 'mean')
    )
    monthly_traffic.index = monthly_traffic.index.to_timestamp()

    fig3 = make_subplots(rows=2, cols=1,
                         subplot_titles=("Tổng Sessions theo tháng", "Bounce Rate trung bình theo tháng"),
                         vertical_spacing=0.12)
    fig3.add_trace(go.Scatter(x=monthly_traffic.index, y=monthly_traffic['sessions'],
                              mode='lines', name='Sessions', fill='tozeroy',
                              fillcolor='rgba(52,152,219,0.15)',
                              line=dict(color=COLOR_PRIMARY, width=2)), row=1, col=1)
    fig3.add_trace(go.Scatter(x=monthly_traffic.index, y=monthly_traffic['bounce'],
                              mode='lines', name='Bounce Rate',
                              line=dict(color=COLOR_NEG, width=2)), row=2, col=1)
    fig3.add_hline(y=monthly_traffic['bounce'].mean(), line_dash="dash", line_color=COLOR_NEU,
                   row=2, col=1, annotation_text=f"TB: {monthly_traffic['bounce'].mean():.2f}")
    fig3.update_layout(height=520, showlegend=True)
    st.plotly_chart(apply_dark_theme(fig3), use_container_width=True)

    st.markdown("---")

    # ============================================================
    # 2.4 Device Type Analysis
    # ============================================================
    st.markdown("### 📱 2.4 Phân tích Thiết bị đặt hàng")

    device_stats = orders.groupby('device_type').agg(
        order_count=('order_id', 'count'),
        avg_amount=('total_amount', 'mean'),
        total_rev=('total_amount', 'sum')
    ).sort_values('order_count', ascending=False).reset_index()

    col1, col2, col3 = st.columns(3)
    with col1:
        fig4a = px.bar(device_stats, x='device_type', y='order_count',
                       title="Số đơn hàng theo thiết bị",
                       color='device_type', color_discrete_sequence=PLOTLY_COLORS)
        fig4a.update_layout(height=380, showlegend=False)
        st.plotly_chart(apply_dark_theme(fig4a), use_container_width=True)
    with col2:
        fig4b = px.bar(device_stats, x='device_type', y='avg_amount',
                       title="AOV theo thiết bị",
                       color='device_type', color_discrete_sequence=PLOTLY_COLORS)
        fig4b.update_layout(height=380, showlegend=False)
        st.plotly_chart(apply_dark_theme(fig4b), use_container_width=True)
    with col3:
        fig4c = px.pie(device_stats, values='total_rev', names='device_type',
                       title="Tỷ trọng doanh thu theo thiết bị",
                       color_discrete_sequence=PLOTLY_COLORS, hole=0.4)
        fig4c.update_layout(height=380)
        st.plotly_chart(apply_dark_theme(fig4c), use_container_width=True)
