"""Phase 0: Data Quality Dashboard
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from utils.charts import apply_dark_theme, create_metric_card_html, format_number, PLOTLY_COLORS
from utils.data_loader import get_data_summary, get_missing_data_summary, get_duplicates_summary


def render(data):
    st.markdown("## 📋 Phase 0: Data Quality Dashboard")
    st.markdown("**Mục tiêu**: Kiểm tra chất lượng dữ liệu, phát hiện và xử lý anomaly")
    st.markdown("> **Câu hỏi**: Dữ liệu có đủ tin cậy để phân tích không?")
    st.markdown("---")

    anomaly_pct = data.get('anomaly_pct', 0)

    # KPI row
    summary_df = get_data_summary(data)
    total_tables = len(summary_df)
    total_rows = summary_df['Rows'].sum()
    missing_df = get_missing_data_summary(data)
    total_missing_cols = len(missing_df) if missing_df is not None else 0

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(create_metric_card_html("📊 Tổng Tables", str(total_tables)), unsafe_allow_html=True)
    with col2:
        st.markdown(create_metric_card_html("📝 Tổng Records", format_number(total_rows)), unsafe_allow_html=True)
    with col3:
        st.markdown(create_metric_card_html("⚠️ Cột có Missing", str(total_missing_cols)), unsafe_allow_html=True)
    with col4:
        st.markdown(create_metric_card_html("🔧 Anomaly Signup", f"{anomaly_pct:.1f}%"), unsafe_allow_html=True)

    st.markdown("---")

    # === 0.1 Dataset Overview ===
    st.markdown("### 📊 0.1 Dataset Overview")
    fig1 = go.Figure()
    fig1.add_trace(go.Bar(
        x=summary_df['Table'], y=summary_df['Rows'],
        marker_color=PLOTLY_COLORS[:len(summary_df)],
        text=summary_df['Rows'].apply(lambda x: f'{x:,}'),
        textposition='outside',
    ))
    fig1.update_layout(title="Số lượng records theo bảng", xaxis_title="Bảng", yaxis_title="Rows",
                       height=420)
    fig1 = apply_dark_theme(fig1)
    st.plotly_chart(fig1, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Thống kê các bảng:**")
        st.dataframe(summary_df, hide_index=True, use_container_width=True)
    with col2:
        dupes_df = get_duplicates_summary()
        st.markdown("**Kiểm tra trùng lặp:**")
        st.dataframe(dupes_df, hide_index=True, use_container_width=True)

    st.markdown("---")

    # === 0.2 Missing Value Analysis ===
    st.markdown("### 📊 0.2 Phân tích Missing Values")
    if missing_df is not None and len(missing_df) > 0:
        fig2 = px.bar(missing_df.sort_values('Pct', ascending=True),
                      x='Pct', y='Column', color='Table', orientation='h',
                      title="% Missing Value theo cột (chỉ hiển thị cột có missing)",
                      labels={'Pct': 'Missing (%)', 'Column': 'Cột'},
                      color_discrete_sequence=PLOTLY_COLORS, height=max(400, len(missing_df) * 20))
        fig2 = apply_dark_theme(fig2)
        st.plotly_chart(fig2, use_container_width=True)
        st.dataframe(missing_df, hide_index=True, use_container_width=True)
    else:
        st.success("✅ Không có missing values trong tất cả các bảng!")

    st.markdown("---")

    # === 0.3 Anomaly: Signup Date Fix ===
    st.markdown("### 🔧 0.3 Xử lý Anomaly — Signup Date")
    customers = data['customers']
    st.markdown(f"""
> **Phát hiện Anomaly**: **{anomaly_pct:.1f}%** khách hàng có `signup_date` SAU ngày mua hàng đầu tiên.
> Đây là lỗi logic nghiêm trọng.
>
> **Giải pháp**: Tạo cột `true_signup_date = min(signup_date, first_order_date)`.
""")
    if 'true_signup_date' in customers.columns:
        diff_days = (customers['first_order_date'] - customers['true_signup_date']).dt.days.dropna()
        fig3 = px.histogram(diff_days, nbins=50,
                            title="Phân phối chênh lệch (first_order - true_signup) theo ngày",
                            labels={'value': 'Số ngày', 'count': 'Số khách hàng'},
                            color_discrete_sequence=['#3498db'])
        fig3.update_layout(height=350)
        fig3 = apply_dark_theme(fig3)
        st.plotly_chart(fig3, use_container_width=True)

    # === 0.4 Order status distribution ===
    st.markdown("### 📊 0.4 Phân phối trạng thái đơn hàng")
    orders = data['orders']
    status_cnt = orders['order_status'].value_counts().reset_index()
    status_cnt.columns = ['status', 'count']
    fig4 = px.pie(status_cnt, values='count', names='status',
                  title="Phân phối trạng thái đơn hàng",
                  color_discrete_sequence=PLOTLY_COLORS, hole=0.4)
    fig4.update_layout(height=400)
    fig4 = apply_dark_theme(fig4)
    st.plotly_chart(fig4, use_container_width=True)
