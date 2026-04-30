"""Phase 7: Executive Summary & Strategic Insights
3 phần từ notebook:
  7.1 Executive KPI Dashboard + Health Scorecard
  7.2 RICE Priority Framework (bar + scatter)
  7.3 Revenue Impact Waterfall
  + Strategic Insights
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


def normalize_1_10(series):
    s_min, s_max = series.min(), series.max()
    if s_max == s_min:
        return pd.Series([5] * len(series), index=series.index)
    return 1 + 9 * (series - s_min) / (s_max - s_min)


def render(data):
    st.markdown("## 📊 Phase 7: Executive Summary & Strategic Insights")
    st.markdown("**Mục tiêu**: Tổng kết và đưa ra hành động chiến lược")
    st.markdown("---")

    orders = data['orders']
    order_items = data['order_items']
    returns = data['returns']
    ship_data = data['ship_data']
    sales = data['sales']
    customers = data['customers']
    products = data['products']
    web_traffic = data['web_traffic']

    # ============================================================
    # 7.1 Executive KPI Dashboard
    # ============================================================
    st.markdown("### 🎯 Executive KPI Dashboard")

    total_revenue = orders['total_amount'].sum()
    total_orders = len(orders)
    total_customers = orders['customer_id'].nunique()
    aov = orders['total_amount'].mean()
    gross_margin = sales['Gross_Margin'].mean() * 100
    return_rate = len(returns) / len(orders) * 100
    avg_delivery = ship_data['delivery_time'].mean()
    median_delivery = ship_data['delivery_time'].median()

    cust_orders = orders.groupby('customer_id')['order_id'].nunique()
    repeat_rate = (cust_orders > 1).mean() * 100

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(create_metric_card_html("💰 Tổng Doanh Thu", format_currency(total_revenue)), unsafe_allow_html=True)
    with col2:
        st.markdown(create_metric_card_html("📦 Tổng Đơn Hàng", format_number(total_orders)), unsafe_allow_html=True)
    with col3:
        st.markdown(create_metric_card_html("👥 Tổng Khách Hàng", format_number(total_customers)), unsafe_allow_html=True)
    with col4:
        st.markdown(create_metric_card_html("🛒 AOV", format_currency(aov)), unsafe_allow_html=True)

    st.markdown("")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(create_metric_card_html("📊 Gross Margin", format_pct(gross_margin)), unsafe_allow_html=True)
    with col2:
        # Retention low is bad
        color_rt = COLOR_NEG if repeat_rate < 20 else COLOR_POS
        st.markdown(create_metric_card_html("🔁 Repeat Rate", f"<span style='color:{color_rt}'>{repeat_rate:.1f}%</span>"), unsafe_allow_html=True)
    with col3:
        st.markdown(create_metric_card_html("🔄 Return Rate", format_pct(return_rate)), unsafe_allow_html=True)
    with col4:
        st.markdown(create_metric_card_html("🚚 Delivery Time", f"{avg_delivery:.1f} ngày"), unsafe_allow_html=True)

    st.markdown("---")

    # === Business Health Scorecard (Radar) ===
    st.markdown("### 🏥 Business Health Scorecard")

    revenue_score = min(100, (total_revenue / 1e10) * 100) if total_revenue > 0 else 0
    margin_score = gross_margin
    retention_score = min(100, repeat_rate * 3) # scale it up since retail retention is low
    ops_score = max(0, 100 - return_rate * 5)
    delivery_score = max(0, 100 - (avg_delivery - 3) * 10)

    categories = ['Doanh thu', 'Biên lợi nhuận', 'Giữ chân KH', 'Vận hành', 'Giao hàng']
    scores = [revenue_score, margin_score, retention_score, ops_score, delivery_score]

    fig_radar = go.Figure(data=go.Scatterpolar(
        r=scores + [scores[0]],
        theta=categories + [categories[0]],
        fill='toself',
        fillcolor='rgba(52,152,219,0.2)',
        line=dict(color=COLOR_PRIMARY, width=2),
    ))
    fig_radar.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        title="Business Health Radar", height=500,
    )
    fig_radar = apply_dark_theme(fig_radar)
    st.plotly_chart(fig_radar, use_container_width=True)

    st.markdown("---")

    # ============================================================
    # 7.2 RICE Priority Framework
    # ============================================================
    st.markdown("### 📋 RICE Priority Ranking (Data-Driven)")

    # Build RICE data
    # 1. Virtual Size Guide
    size_returns = returns[returns['return_reason'].str.contains('size', case=False, na=False)]
    reach_1 = len(size_returns) / len(returns) if len(returns) > 0 else 0
    impact_1 = size_returns['refund_amount'].sum() if len(size_returns) > 0 else 0

    # 2. Tối ưu logistics
    late_ship = ship_data[ship_data['delivery_time'] > median_delivery]
    reach_2 = len(late_ship) / len(ship_data) if len(ship_data) > 0 else 0
    impact_2 = total_revenue * 0.05

    # 3. Loyalty program
    orders_delivered = orders[orders['order_status'] == 'delivered']
    rfm_cust = orders_delivered.groupby('customer_id').agg(total=('total_amount', 'sum'))
    champions = rfm_cust[rfm_cust['total'] > rfm_cust['total'].quantile(0.8)]
    reach_3 = len(champions) / len(rfm_cust) if len(rfm_cust) > 0 else 0
    impact_3 = champions['total'].sum() * 0.15

    # 4. Win-back campaign
    at_risk = rfm_cust[(rfm_cust['total'] > rfm_cust['total'].quantile(0.2)) & (rfm_cust['total'] <= rfm_cust['total'].quantile(0.5))]
    reach_4 = len(at_risk) / len(rfm_cust) if len(rfm_cust) > 0 else 0
    impact_4 = at_risk['total'].sum() * 0.10

    # 5. Giảm voucher tràn lan
    promo_orders = order_items[order_items['promo_id'].notna()]
    reach_5 = len(promo_orders) / len(order_items) if len(order_items) > 0 else 0
    impact_5 = order_items['discount_amount'].fillna(0).sum() * 0.30

    # 6. Cross-sell
    reach_6 = 0.5
    impact_6 = total_revenue * 0.03

    # 7. Landing page optimization
    avg_bounce = web_traffic['bounce_rate'].mean()
    reach_7 = avg_bounce
    impact_7 = total_revenue * avg_bounce * 0.10

    # 8. Loại bỏ SP nhóm C
    prod_sales = order_items.groupby('product_id')['quantity'].sum()
    bottom20 = prod_sales.quantile(0.20)
    low_products = prod_sales[prod_sales <= bottom20]
    reach_8 = len(low_products) / len(products) if len(products) > 0 else 0
    impact_8 = products[products['product_id'].isin(low_products.index)]['cogs'].sum()

    # 9. Khuyến khích trả góp
    q3_amount = orders['total_amount'].quantile(0.75)
    high_value = orders[orders['total_amount'] >= q3_amount]
    reach_9 = len(high_value) / total_orders if total_orders > 0 else 0
    impact_9 = high_value['total_amount'].sum() * 0.10

    # 10. KPI giao hàng
    late_orders = ship_data[ship_data['delivery_time'] > median_delivery].merge(orders[['order_id', 'total_amount']], on='order_id')
    reach_10 = len(late_orders) / total_orders if total_orders > 0 else 0
    impact_10 = late_orders['total_amount'].sum()

    actions = pd.DataFrame({
        'Action': ['Virtual Size Guide', 'Tối ưu logistics vùng yếu', 'Loyalty program (Champions)',
                   'Win-back campaign (At Risk)', 'Giảm voucher tràn lan', 'Cross-sell (Market Basket)',
                   'Tối ưu landing page', 'Loại bỏ SP nhóm C tồn kho', 'Khuyến khích trả góp',
                   'KPI giao hàng < median'],
        'Category': ['Operations', 'Operations', 'Retention', 'Retention', 'Sales', 'Sales',
                     'Acquisition', 'Product', 'Sales', 'Operations'],
        'Reach_raw': [reach_1, reach_2, reach_3, reach_4, reach_5, reach_6, reach_7, reach_8, reach_9, reach_10],
        'Impact_raw': [impact_1, impact_2, impact_3, impact_4, impact_5, impact_6, impact_7, impact_8, impact_9, impact_10],
        'Confidence': [0.9, 0.9, 1.0, 0.8, 1.0, 0.7, 0.5, 0.8, 0.5, 0.9],
        'Effort_raw': [3, 7, 5, 3, 2, 4, 6, 2, 2, 8]
    })

    actions['Reach'] = normalize_1_10(actions['Reach_raw']).round(1)
    actions['Impact'] = normalize_1_10(actions['Impact_raw']).round(1)
    actions['Effort'] = actions['Effort_raw']
    actions['RICE'] = ((actions['Reach'] * actions['Impact'] * actions['Confidence']) / actions['Effort']).round(2)
    actions = actions.sort_values('RICE', ascending=False).reset_index(drop=True)

    cat_colors = {'Operations': COLOR_NEG, 'Retention': COLOR_PRIMARY,
                  'Sales': COLOR_POS, 'Acquisition': '#f39c12', 'Product': COLOR_SECONDARY}

    col1, col2 = st.columns(2)
    with col1:
        fig_rice = go.Figure()
        fig_rice.add_trace(go.Bar(
            y=actions['Action'], x=actions['RICE'],
            orientation='h',
            marker_color=[cat_colors.get(c, COLOR_NEU) for c in actions['Category']],
            text=[f"{v:.1f}" for v in actions['RICE']],
            textposition='outside'
        ))
        fig_rice.update_layout(title="RICE Priority Ranking", height=500,
                               xaxis_title="RICE Score = (Reach × Impact × Confidence) / Effort",
                               yaxis=dict(autorange="reversed"))
        fig_rice = apply_dark_theme(fig_rice)
        st.plotly_chart(fig_rice, use_container_width=True)

    with col2:
        fig_matrix = go.Figure()
        for cat in actions['Category'].unique():
            subset = actions[actions['Category'] == cat]
            fig_matrix.add_trace(go.Scatter(
                x=subset['Impact'], y=subset['Effort'],
                mode='markers+text', text=subset['Action'],
                textposition='top right', textfont=dict(size=8),
                marker=dict(size=subset['RICE'] * 3 + 10, color=cat_colors.get(cat, COLOR_NEU),
                            opacity=0.8, line=dict(width=1, color='black')),
                name=cat
            ))
        fig_matrix.add_hline(y=5, line_dash="dash", line_color=COLOR_NEU, opacity=0.5)
        fig_matrix.add_vline(x=5.5, line_dash="dash", line_color=COLOR_NEU, opacity=0.5)
        fig_matrix.update_layout(title="Priority Matrix: Impact vs Effort",
                                 xaxis_title="Impact (1-10)", yaxis_title="Effort (person-months)",
                                 height=500, xaxis=dict(range=[0, 11]),
                                 yaxis=dict(range=[0, 11], autorange="reversed"))
        fig_matrix = apply_dark_theme(fig_matrix)
        st.plotly_chart(fig_matrix, use_container_width=True)

    st.markdown("---")

    # ============================================================
    # TỔNG HỢP 3 PHÁT HIỆN CHIẾN LƯỢC QUAN TRỌNG NHẤT
    # ============================================================
    st.markdown("### 📋 TỔNG HỢP 3 PHÁT HIỆN CHIẾN LƯỢC QUAN TRỌNG NHẤT")

    st.markdown("""
    <div style="
        background: #fff5f5;
        border-left: 4px solid #e53e3e;
        border-radius: 0 8px 8px 0;
        padding: 20px; margin: 12px 0;
    ">
        <h4 style="color:#c53030; margin:0 0 8px 0;">🔴 PHÁT HIỆN 1: RÒ RỈ LỢI NHUẬN TRONG VẬN HÀNH</h4>
        <ul style="color:#2d3748; margin:0;">
            <li><strong>Lỗ hổng:</strong> Một phần lớn tỷ lệ hoàn hàng đến từ sai sót về kích cỡ (size) hoặc màu sắc, gây lãng phí chi phí logistics và làm xói mòn lợi nhuận trực tiếp.</li>
            <li><strong>Nghịch lý vận chuyển:</strong> Tốc độ giao hàng chậm trễ ở một số tuyến lại đi kèm với chi phí cao hơn mức trung bình, tác động xấu đến đánh giá (rating) của khách hàng.</li>
            <li><strong>Action:</strong> Khẩn trương triển khai tính năng hướng dẫn chọn size (Virtual Size Guide), đồng thời đánh giá và thay thế đối tác logistics tại các vùng có thời gian giao hàng > 5 ngày.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="
        background: #fffaf0;
        border-left: 4px solid #dd6b20;
        border-radius: 0 8px 8px 0;
        padding: 20px; margin: 12px 0;
    ">
        <h4 style="color:#c05621; margin:0 0 8px 0;">🟠 PHÁT HIỆN 2: SỰ PHỤ THUỘC VÀO KHUYẾN MÃI</h4>
        <ul style="color:#2d3748; margin:0;">
            <li><strong>Lỗ hổng:</strong> Lượng đơn hàng phụ thuộc quá nhiều vào các đợt giảm giá. Nhiều nhóm sản phẩm có độ co giãn giá (Price Elasticity) thấp, nghĩa là việc giảm giá không mang lại đủ lượng đơn hàng để bù đắp sự sụt giảm margin.</li>
            <li><strong>Nghịch lý:</strong> Đơn hàng tăng vọt vào ngày Double Days (11/11, 12/12) nhưng AOV không tăng mạnh, cho thấy khách hàng chỉ tập trung 'săn sale'.</li>
            <li><strong>Action:</strong> Tái cấu trúc chính sách khuyến mãi dựa trên Elasticity. Dừng giảm giá với các Category có Elasticity < 1.0. Tăng cường cross-sell/up-sell qua mô hình "Mua X tặng Y" thay vì giảm giá trực tiếp.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="
        background: #ebf8ff;
        border-left: 4px solid #3182ce;
        border-radius: 0 8px 8px 0;
        padding: 20px; margin: 12px 0;
    ">
        <h4 style="color:#2b6cb0; margin:0 0 8px 0;">🔵 PHÁT HIỆN 3: TỶ LỆ GIỮ CHÂN THẤP VÀ NGUY CƠ MẤT KHÁCH</h4>
        <ul style="color:#2d3748; margin:0;">
            <li><strong>Lỗ hổng:</strong> Retention Rate sụt giảm nghiêm trọng ngay trong 2-3 tháng đầu. "Chiếc phễu thủng" này khiến CLV trung bình ở mức thấp.</li>
            <li><strong>Cơ hội:</strong> Phân khúc RFM cho thấy nhóm "Loyal" và "Champions" dù số lượng ít nhưng đóng góp lượng lớn doanh thu. Nhóm "At Risk" đang cần sự can thiệp lập tức.</li>
            <li><strong>Action:</strong> Triển khai chiến dịch Win-back tự động sau 30-45 ngày cho nhóm At Risk. Thiết lập chương trình VIP Loyalty Program cho nhóm Champions để bảo vệ nguồn doanh thu cốt lõi.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
