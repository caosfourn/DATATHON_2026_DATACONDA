"""Phase 1: Business Pulse & Time Series Overview
Biểu đồ từ notebook:
  1.1 Monthly Revenue, COGS & Gross Profit Trend + Gross Margin
  1.2 Waterfall Chart: Dòng chảy lợi nhuận
  1.3 Time Series Decomposition
  1.4 MoM & YoY Growth
  1.5 Spike Analysis
  1.6 Volume vs AOV
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils.charts import (
    apply_dark_theme, create_metric_card_html, format_number, format_currency,
    format_pct, PLOTLY_COLORS, COLOR_PRIMARY, COLOR_POS, COLOR_NEG, COLOR_SECONDARY, COLOR_NEU
)


def render(data):
    st.markdown("## 📈 Phase 1: Business Pulse & Time Series Overview")
    st.markdown("**Mục tiêu**: Xác định tình trạng doanh nghiệp, đưa ra cái nhìn toàn cảnh về doanh thu")
    st.markdown("> **Câu hỏi kinh doanh**: Doanh thu đang có xu hướng như thế nào, có tăng trưởng bền vững không?")
    st.markdown("---")

    orders = data['orders']
    sales = data['sales']
    order_items = data['order_items']
    products = data['products']
    shipments = data['ship_data']

    # === KPI Metrics ===
    total_revenue = orders['total_amount'].sum()
    total_orders = len(orders)
    avg_order_value = orders['total_amount'].mean()
    gross_margin_avg = sales['Gross_Margin'].mean() * 100

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(create_metric_card_html("💰 Tổng Doanh Thu", format_currency(total_revenue)), unsafe_allow_html=True)
    with col2:
        st.markdown(create_metric_card_html("📦 Tổng Đơn Hàng", format_number(total_orders)), unsafe_allow_html=True)
    with col3:
        st.markdown(create_metric_card_html("🛒 AOV Trung Bình", format_currency(avg_order_value)), unsafe_allow_html=True)
    with col4:
        st.markdown(create_metric_card_html("📊 Gross Margin TB", format_pct(gross_margin_avg)), unsafe_allow_html=True)

    st.markdown("---")

    # ============================================================
    # 1.1 Monthly Revenue, COGS & Gross Profit Trend + Gross Margin
    # ============================================================
    st.markdown("### 📈 1.1 Doanh thu, Giá vốn và Lợi nhuận gộp theo tháng")

    monthly_sales = sales.groupby('YearMonth').agg(
        Revenue=('Revenue', 'sum'), COGS=('COGS', 'sum'), Gross_Profit=('Gross_Profit', 'sum')
    ).reset_index()
    monthly_sales['month_dt'] = monthly_sales['YearMonth'].dt.to_timestamp()
    monthly_sales['Gross_Margin'] = monthly_sales['Gross_Profit'] / monthly_sales['Revenue'] * 100

    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=("Doanh thu, Giá vốn và Lợi nhuận gộp theo tháng", "Gross Margin Rate theo tháng"),
        vertical_spacing=0.15,
        row_heights=[0.6, 0.4],
    )
    fig.add_trace(go.Scatter(x=monthly_sales['month_dt'], y=monthly_sales['Revenue'],
                             mode='lines', name='Revenue', line=dict(color=COLOR_PRIMARY, width=2)), row=1, col=1)
    fig.add_trace(go.Scatter(x=monthly_sales['month_dt'], y=monthly_sales['COGS'],
                             mode='lines', name='COGS', line=dict(color=COLOR_NEG, width=2)), row=1, col=1)
    fig.add_trace(go.Scatter(x=monthly_sales['month_dt'], y=monthly_sales['Gross_Profit'],
                             mode='lines', name='Gross Profit', fill='tozeroy',
                             fillcolor='rgba(46,204,113,0.15)',
                             line=dict(color=COLOR_POS, width=2)), row=1, col=1)

    gm_mean = monthly_sales['Gross_Margin'].mean()
    colors_gm = [COLOR_POS if v >= gm_mean else COLOR_NEG for v in monthly_sales['Gross_Margin']]
    fig.add_trace(go.Bar(x=monthly_sales['month_dt'], y=monthly_sales['Gross_Margin'],
                         name='Gross Margin %', marker_color=colors_gm, opacity=0.7), row=2, col=1)
    fig.add_hline(y=gm_mean, line_dash="dash", line_color="black", row=2, col=1,
                  annotation_text=f"TB: {gm_mean:.1f}%")

    fig.update_layout(height=650, showlegend=True)
    fig = apply_dark_theme(fig)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown(f"> **Insight**: Gross Margin trung bình: **{gm_mean:.1f}%**.")

    st.markdown("---")

    # ============================================================
    # 1.2 Waterfall Chart: Dòng chảy lợi nhuận
    # ============================================================
    st.markdown("### 💧 1.2 Waterfall Chart: Dòng chảy lợi nhuận (Tiền đã biến đi đâu?)")

    oi_with_cogs = order_items.merge(products[['product_id', 'cogs', 'price']], on='product_id', how='left')
    total_gross_revenue = (oi_with_cogs['quantity'] * oi_with_cogs['unit_price']).sum()
    total_cogs = (oi_with_cogs['quantity'] * oi_with_cogs['cogs']).sum()
    total_promo = oi_with_cogs['discount_amount'].fillna(0).sum()
    total_shipping = shipments['shipping_fee'].fillna(0).sum()

    total_net_profit = total_gross_revenue - total_cogs - total_promo - total_shipping

    fig_wf = go.Figure(go.Waterfall(
        orientation="v",
        measure=["relative", "relative", "relative", "relative", "total"],
        x=['Doanh thu tổng<br>(Gross Revenue)', 'Giá vốn<br>(COGS)', 'Khuyến mãi<br>(Promo)', 'Phí vận chuyển<br>(Shipping)', 'Lợi nhuận cuối<br>(Net Profit)'],
        textposition="outside",
        text=[f"{total_gross_revenue/1e9:.1f}B", f"-{total_cogs/1e9:.1f}B", f"-{total_promo/1e9:.1f}B", f"-{total_shipping/1e9:.1f}B", f"{total_net_profit/1e9:.1f}B"],
        y=[total_gross_revenue, -total_cogs, -total_promo, -total_shipping, total_net_profit],
        connector={"line": {"color": COLOR_NEU}},
        increasing={"marker": {"color": COLOR_PRIMARY}},
        decreasing={"marker": {"color": COLOR_NEG}},
        totals={"marker": {"color": COLOR_POS}},
    ))
    fig_wf.update_layout(title="Revenue Impact Waterfall - Dòng tiền từ doanh thu đến lợi nhuận",
                         yaxis_title="VND", height=500)
    fig_wf = apply_dark_theme(fig_wf)
    st.plotly_chart(fig_wf, use_container_width=True)

    st.markdown("---")

    # ============================================================
    # 1.3 Time Series Decomposition
    # ============================================================
    st.markdown("### 📊 1.3 Time Series Decomposition (Phân rã chuỗi thời gian)")

    try:
        from statsmodels.tsa.seasonal import seasonal_decompose
        monthly_rev = sales.groupby('YearMonth')['Revenue'].sum()
        monthly_rev.index = monthly_rev.index.to_timestamp()

        if len(monthly_rev) >= 24:
            result = seasonal_decompose(monthly_rev, model='multiplicative', period=12)

            fig2 = make_subplots(
                rows=4, cols=1,
                subplot_titles=('Observed (Dữ liệu gốc)', 'Trend (Xu hướng dài hạn)',
                                'Seasonal (Tính mùa vụ)', 'Residual (Nhiễu/Bất thường)'),
                vertical_spacing=0.08,
            )
            components = [
                (result.observed, COLOR_PRIMARY, 'Observed'),
                (result.trend, COLOR_POS, 'Trend'),
                (result.seasonal, COLOR_SECONDARY, 'Seasonal'),
                (result.resid, COLOR_NEG, 'Residual'),
            ]
            for i, (comp_data, color, name) in enumerate(components, 1):
                fig2.add_trace(go.Scatter(x=comp_data.index, y=comp_data.values,
                                         mode='lines', name=name, line=dict(color=color, width=1.5)),
                               row=i, col=1)

            fig2.update_layout(height=700, title_text="Time Series Decomposition - Doanh thu hàng tháng (Multiplicative)")
            fig2 = apply_dark_theme(fig2)
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.warning("Không đủ dữ liệu để thực hiện seasonal decomposition (cần >= 24 tháng)")
    except ImportError:
        st.warning("Cần cài đặt statsmodels để hiển thị biểu đồ này: `pip install statsmodels`")

    st.markdown("---")

    # ============================================================
    # 1.4 MoM & YoY Growth
    # ============================================================
    st.markdown("### 📈 1.4 Phân tích chỉ số tăng trưởng (Growth Rate)")

    monthly_sales['MoM_Growth'] = monthly_sales['Revenue'].pct_change() * 100
    monthly_sales['Year'] = monthly_sales['month_dt'].dt.year
    monthly_sales['Month'] = monthly_sales['month_dt'].dt.month

    monthly_sales['YoY_Growth'] = None
    for idx, row in monthly_sales.iterrows():
        prev = monthly_sales[(monthly_sales['Year'] == row['Year'] - 1) & (monthly_sales['Month'] == row['Month'])]
        if len(prev) > 0:
            prev_rev = prev['Revenue'].values[0]
            if prev_rev > 0:
                monthly_sales.at[idx, 'YoY_Growth'] = (row['Revenue'] - prev_rev) / prev_rev * 100
    monthly_sales['YoY_Growth'] = pd.to_numeric(monthly_sales['YoY_Growth'])

    fig3 = make_subplots(rows=2, cols=1,
                         subplot_titles=("Tăng trưởng Month-over-Month (MoM %)", "Tăng trưởng Year-over-Year (YoY %)"),
                         vertical_spacing=0.12)

    mom_vals = monthly_sales['MoM_Growth'].fillna(0)
    colors_mom = [COLOR_POS if v >= 0 else COLOR_NEG for v in mom_vals]
    fig3.add_trace(go.Bar(x=monthly_sales['month_dt'], y=mom_vals, name='MoM %',
                          marker_color=colors_mom, opacity=0.7), row=1, col=1)
    fig3.add_hline(y=0, line_color="black", line_width=0.8, row=1, col=1)

    yoy_data = monthly_sales.dropna(subset=['YoY_Growth'])
    if len(yoy_data) > 0:
        colors_yoy = [COLOR_POS if v >= 0 else COLOR_NEG for v in yoy_data['YoY_Growth']]
        fig3.add_trace(go.Bar(x=yoy_data['month_dt'], y=yoy_data['YoY_Growth'], name='YoY %',
                              marker_color=colors_yoy, opacity=0.7), row=2, col=1)
        fig3.add_hline(y=0, line_color="black", line_width=0.8, row=2, col=1)

    fig3.update_layout(height=550, showlegend=True)
    fig3 = apply_dark_theme(fig3)
    st.plotly_chart(fig3, use_container_width=True)

    st.markdown("---")

    # ============================================================
    # 1.5 Spike Analysis
    # ============================================================
    st.markdown("### 🔥 1.5 Phân tích các ngày doanh thu đột biến (Spike Analysis)")

    from datetime import timedelta
    daily_rev = sales.set_index('Date')['Revenue']

    special_dates = {}
    for year in range(daily_rev.index.year.min(), daily_rev.index.year.max() + 1):
        for m, d in [(11, 11), (12, 12)]:
            dt = pd.Timestamp(year, m, d)
            if dt in daily_rev.index:
                special_dates[dt] = f'{m}/{d}'

    threshold = daily_rev.quantile(0.99)
    spike_days = daily_rev[daily_rev >= threshold]

    fig4 = go.Figure()
    fig4.add_trace(go.Scatter(x=daily_rev.index, y=daily_rev.values,
                              mode='lines', name='Daily Revenue',
                              line=dict(color=COLOR_NEU, width=0.5), opacity=0.4))
    ma30 = daily_rev.rolling(30).mean()
    fig4.add_trace(go.Scatter(x=ma30.index, y=ma30.values,
                              mode='lines', name='MA 30 ngày',
                              line=dict(color=COLOR_PRIMARY, width=2)))
    fig4.add_trace(go.Scatter(x=spike_days.index, y=spike_days.values,
                              mode='markers', name=f'Top 1% spikes (>= {threshold:,.0f})',
                              marker=dict(color=COLOR_NEG, size=8)))

    for dt, label in special_dates.items():
        if dt in daily_rev.index:
            rev = daily_rev[dt]
            surrounding = daily_rev[dt - timedelta(days=7):dt + timedelta(days=7)].mean()
            multiplier = rev / surrounding if surrounding > 0 else 0
            if multiplier > 1.5:
                fig4.add_annotation(x=dt, y=rev, text=f'{label}<br>{multiplier:.1f}x',
                                    showarrow=True, arrowhead=2, font=dict(color=COLOR_NEG, size=10))

    fig4.update_layout(title="Daily Revenue với Spike Analysis (Double Days 11/11, 12/12)",
                       yaxis_title="Revenue (VND)", height=450)
    fig4 = apply_dark_theme(fig4)
    st.plotly_chart(fig4, use_container_width=True)

    st.markdown("---")

    # ============================================================
    # 1.6 Volume vs AOV
    # ============================================================
    st.markdown("### 🎯 1.6 Phân tích Chất lượng Tăng trưởng: Volume vs AOV")

    monthly_kpi = orders.groupby('order_month').agg(
        order_count=('order_id', 'count'),
        total_revenue=('total_amount', 'sum')
    ).dropna()
    monthly_kpi['AOV'] = monthly_kpi['total_revenue'] / monthly_kpi['order_count']
    monthly_kpi['year'] = monthly_kpi.index.year

    fig5 = px.scatter(monthly_kpi, x='order_count', y='AOV',
                      color='year', color_continuous_scale='Viridis',
                      title="Chất lượng tăng trưởng: Volume vs AOV theo tháng",
                      labels={'order_count': 'Số lượng đơn hàng / tháng', 'AOV': 'AOV (Giá trị đơn TB)'},
                      size_max=12)

    z = np.polyfit(monthly_kpi['order_count'], monthly_kpi['AOV'], 1)
    p = np.poly1d(z)
    x_line = np.linspace(monthly_kpi['order_count'].min(), monthly_kpi['order_count'].max(), 100)
    fig5.add_trace(go.Scatter(x=x_line, y=p(x_line), mode='lines',
                              name=f'Trend (slope={z[0]:.2f})',
                              line=dict(color=COLOR_NEG, width=2, dash='dash')))

    fig5.update_layout(height=500)
    fig5 = apply_dark_theme(fig5)
    st.plotly_chart(fig5, use_container_width=True)
