"""Phase 6: Retention & Customer Lifetime Value
Notebook cells: 6.1 Cohort Retention, 6.2 RFM Segmentation, 6.3 Repeat Purchase Rate
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from utils.charts import (
    apply_dark_theme, create_metric_card_html, format_number, format_currency, format_pct,
    PLOTLY_COLORS, COLOR_PRIMARY, COLOR_POS, COLOR_NEG, COLOR_SECONDARY, COLOR_NEU
)


def render(data):
    st.markdown("## 🔁 Phase 6: Retention & Customer Lifetime Value")
    st.markdown("**Mục tiêu**: Đánh giá khả năng giữ chân khách hàng và định giá trị vòng đời (CLV)")
    st.markdown("---")

    orders = data['orders']
    customers = data['customers']

    # KPIs
    total_customers = customers['customer_id'].nunique()
    
    # Calculate repeat buyers
    order_counts = orders.groupby('customer_id')['order_id'].nunique()
    repeat_buyers = (order_counts > 1).sum()
    repeat_rate = repeat_buyers / total_customers * 100 if total_customers > 0 else 0
    
    # Calculate average CLV (total spent / total customers)
    total_revenue = orders['total_amount'].sum()
    avg_clv = total_revenue / total_customers if total_customers > 0 else 0

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(create_metric_card_html("👥 Tổng Khách Hàng", format_number(total_customers)), unsafe_allow_html=True)
    with col2:
        color = COLOR_NEG if repeat_rate < 20 else COLOR_POS
        st.markdown(create_metric_card_html("🔁 Tỷ Lệ Mua Lại", f"<span style='color:{color}'>{repeat_rate:.1f}%</span>"), unsafe_allow_html=True)
    with col3:
        st.markdown(create_metric_card_html("💎 Avg CLV", format_currency(avg_clv)), unsafe_allow_html=True)

    st.markdown("---")

    # ============================================================
    # 6.1 Cohort Retention Analysis
    # ============================================================
    st.markdown("### 🗓️ 6.1 Phân tích Tỷ lệ giữ chân (Cohort Retention Analysis)")

    # Prepare data for cohort
    df_cohort = orders[['customer_id', 'order_date', 'total_amount']].dropna().copy()
    df_cohort['order_month'] = df_cohort['order_date'].dt.to_period('M').dt.to_timestamp()
    
    # Get first order month for each customer
    first_orders = df_cohort.groupby('customer_id')['order_month'].min().reset_index()
    first_orders.columns = ['customer_id', 'cohort_month']
    
    df_cohort = df_cohort.merge(first_orders, on='customer_id')
    
    # Calculate month difference
    df_cohort['cohort_index'] = (df_cohort['order_month'].dt.year - df_cohort['cohort_month'].dt.year) * 12 + \
                                (df_cohort['order_month'].dt.month - df_cohort['cohort_month'].dt.month)

    cohort_data = df_cohort.groupby(['cohort_month', 'cohort_index'])['customer_id'].nunique().reset_index()
    cohort_pivot = cohort_data.pivot(index='cohort_month', columns='cohort_index', values='customer_id')
    
    # Select last 12 cohorts for cleaner visualization
    if len(cohort_pivot) > 12:
        cohort_pivot = cohort_pivot.tail(12)
        
    cohort_size = cohort_pivot.iloc[:, 0]
    retention = cohort_pivot.divide(cohort_size, axis=0) * 100

    # Format y-axis labels
    y_labels = [dt.strftime('%Y-%m') for dt in retention.index]

    fig1 = go.Figure(data=go.Heatmap(
        z=retention.values,
        x=retention.columns.tolist(),
        y=y_labels,
        colorscale='Blues',
        text=[[f"{v:.1f}%" if not np.isnan(v) else "" for v in row] for row in retention.values],
        texttemplate='%{text}', textfont=dict(size=10),
        hovertemplate="Cohort: %{y}<br>Tháng thứ: %{x}<br>Retention: %{z:.1f}%<extra></extra>",
        zmin=0, zmax=20  # Cap the color scale to see variations in low retention
    ))
    fig1.update_layout(
        title="Cohort Retention Heatmap (%) - 12 tháng gần nhất",
        xaxis_title="Số tháng kể từ lần mua đầu tiên (Cohort Index)",
        yaxis_title="Tháng gia nhập (Cohort Month)",
        height=500
    )
    st.plotly_chart(apply_dark_theme(fig1), use_container_width=True)

    st.markdown("""
> **Insight - "Chiếc phễu thủng"**: Tỷ lệ giữ chân sụt giảm cực kỳ nghiêm trọng ngay sau tháng đầu tiên (chỉ còn dưới 3-5%). Doanh nghiệp đang tiêu tốn nhiều chi phí Acquisition nhưng không giữ được khách hàng ở lại.
    """)

    st.markdown("---")

    # ============================================================
    # 6.2 RFM Segmentation
    # ============================================================
    st.markdown("### 🎯 6.2 Phân khúc Khách hàng RFM (Recency, Frequency, Monetary)")

    # Tính RFM
    max_date = orders['order_date'].max()
    rfm = orders.groupby('customer_id').agg(
        Recency=('order_date', lambda x: (max_date - x.max()).days),
        Frequency=('order_id', 'nunique'),
        Monetary=('total_amount', 'sum')
    ).reset_index()

    # Xếp hạng bằng qcut (nếu đủ đa dạng)
    try:
        rfm['R_Score'] = pd.qcut(rfm['Recency'], 4, labels=[4, 3, 2, 1])
    except:
        rfm['R_Score'] = 1  # Fallback
        
    # Frequency thường tập trung ở 1 rất nhiều nên dùng cut thủ công thay vì qcut để tránh lỗi duplicate edges
    def f_score(x):
        if x == 1: return 1
        elif x == 2: return 2
        elif x <= 4: return 3
        else: return 4
    rfm['F_Score'] = rfm['Frequency'].apply(f_score)
    
    try:
        rfm['M_Score'] = pd.qcut(rfm['Monetary'], 4, labels=[1, 2, 3, 4])
    except:
        rfm['M_Score'] = 1

    rfm['RFM_Segment'] = rfm['R_Score'].astype(str) + rfm['F_Score'].astype(str) + rfm['M_Score'].astype(str)

    # Gán nhãn segment
    def segment_customer(row):
        r, f, m = int(row['R_Score']), int(row['F_Score']), int(row['M_Score'])
        if r >= 3 and f >= 3 and m >= 3: return 'Champions'
        elif r >= 3 and f >= 2: return 'Loyal Customers'
        elif r >= 3 and f == 1: return 'Recent/New'
        elif r <= 2 and f >= 3: return 'At Risk'
        elif r <= 2 and f <= 2: return 'Hibernating / Lost'
        else: return 'Others'

    rfm['Segment_Label'] = rfm.apply(segment_customer, axis=1)

    segment_stats = rfm.groupby('Segment_Label').agg(
        customer_count=('customer_id', 'count'),
        avg_recency=('Recency', 'mean'),
        avg_freq=('Frequency', 'mean'),
        total_value=('Monetary', 'sum')
    ).reset_index()
    segment_stats['customer_share'] = segment_stats['customer_count'] / segment_stats['customer_count'].sum() * 100
    segment_stats['revenue_share'] = segment_stats['total_value'] / segment_stats['total_value'].sum() * 100

    col1, col2 = st.columns(2)
    with col1:
        fig2a = px.pie(segment_stats, values='customer_count', names='Segment_Label',
                       title="Cơ cấu Khách hàng theo RFM Segment",
                       color_discrete_sequence=PLOTLY_COLORS, hole=0.35)
        fig2a.update_layout(height=400)
        st.plotly_chart(apply_dark_theme(fig2a), use_container_width=True)
    with col2:
        fig2b = px.bar(segment_stats.sort_values('total_value', ascending=False),
                       x='Segment_Label', y='revenue_share',
                       title="Tỷ trọng Doanh thu theo RFM Segment (%)",
                       color='Segment_Label', color_discrete_sequence=PLOTLY_COLORS,
                       labels={'Segment_Label': 'Phân khúc', 'revenue_share': '% Doanh thu'})
        fig2b.update_layout(height=400, showlegend=False)
        st.plotly_chart(apply_dark_theme(fig2b), use_container_width=True)

    st.markdown("**Bảng Phân tích RFM chi tiết:**")
    st.dataframe(segment_stats.round(1).sort_values('customer_count', ascending=False), hide_index=True, use_container_width=True)

    st.markdown("---")

    # ============================================================
    # 6.3 Tỷ lệ mua lại trong 90 ngày (Repeat Purchase Rate)
    # ============================================================
    st.markdown("### ⏳ 6.3 Tỷ lệ mua lại trong 90 ngày")

    # Sort orders by customer and date
    df_sorted = orders.sort_values(['customer_id', 'order_date'])
    # Get the time difference between consecutive orders
    df_sorted['next_order_date'] = df_sorted.groupby('customer_id')['order_date'].shift(-1)
    df_sorted['days_to_next_order'] = (df_sorted['next_order_date'] - df_sorted['order_date']).dt.days

    # Khách hàng có mua lại
    repeat_orders = df_sorted.dropna(subset=['days_to_next_order'])
    
    col1, col2 = st.columns([1, 2])
    with col1:
        repeat_90d = len(repeat_orders[repeat_orders['days_to_next_order'] <= 90])
        total_possible = len(df_sorted) - len(orders['customer_id'].unique()) # Max possible repeat transitions
        
        # Calculate a simplified repeat rate within 90 days of ANY order
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown(create_metric_card_html(
            "🔁 Repeat in 90 Days", 
            f"{(repeat_90d / len(repeat_orders) * 100) if len(repeat_orders) > 0 else 0:.1f}%"
        ), unsafe_allow_html=True)
        st.markdown("<p style='color:#7f8c8d; font-size:12px; text-align:center;'>Trong số những người có mua lần 2, tỷ lệ quay lại trong vòng 90 ngày</p>", unsafe_allow_html=True)
        
    with col2:
        # Distribution of days to next order
        fig3 = px.histogram(repeat_orders[repeat_orders['days_to_next_order'] <= 365], 
                            x='days_to_next_order', nbins=50,
                            title="Phân phối khoảng cách thời gian giữa 2 lần mua (Days)",
                            labels={'days_to_next_order': 'Số ngày đến lần mua tiếp theo', 'count': 'Số lượng giao dịch'},
                            color_discrete_sequence=[COLOR_PRIMARY])
        fig3.add_vline(x=90, line_dash="dash", line_color=COLOR_NEG, annotation_text="90 Days")
        fig3.update_layout(height=350)
        st.plotly_chart(apply_dark_theme(fig3), use_container_width=True)
