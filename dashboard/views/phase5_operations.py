"""Phase 5: Operations & Fulfillment Analysis
Notebook cells: 5.1 Return Rate, 5.2 Delivery Time vs Rating, 5.3 Geography, 5.4 Delivery Performance
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
    st.markdown("## 🚚 Phase 5: Operations & Fulfillment")
    st.markdown("**Mục tiêu**: Đánh giá hiệu suất vận hành, giao hàng và tỷ lệ hoàn trả (rò rỉ lợi nhuận)")
    st.markdown("---")

    orders = data['orders']
    order_items = data['order_items']
    returns = data['returns']
    ship_data = data['ship_data']  # This has delivery_time
    reviews = data['reviews']

    # KPIs
    total_orders = len(orders)
    total_returned_orders = orders[orders['order_status'] == 'returned']['order_id'].nunique()
    return_rate = total_returned_orders / total_orders * 100 if total_orders > 0 else 0
    avg_delivery_time = ship_data['delivery_time'].mean()
    avg_rating = reviews['rating'].mean()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(create_metric_card_html("📦 Tổng Số Đơn Hàng", format_number(total_orders)), unsafe_allow_html=True)
    with col2:
        # Highlight high return rate if needed
        color = COLOR_NEG if return_rate > 5 else COLOR_POS
        st.markdown(create_metric_card_html("🔄 Tỷ Lệ Hoàn Trả (Order)", f"<span style='color:{color}'>{return_rate:.1f}%</span>"), unsafe_allow_html=True)
    with col3:
        st.markdown(create_metric_card_html("⏱️ TG Giao Hàng TB", f"{avg_delivery_time:.1f} ngày"), unsafe_allow_html=True)
    with col4:
        st.markdown(create_metric_card_html("⭐ Đánh Giá TB", f"{avg_rating:.1f} / 5.0"), unsafe_allow_html=True)

    st.markdown("---")

    # ============================================================
    # 5.1 Return Rate Analysis
    # ============================================================
    st.markdown("### 🔄 5.1 Phân tích Rủi ro Hoàn hàng (Return Analysis)")

    # Return by category
    returns_full = returns.merge(order_items[['order_id', 'product_id', 'item_revenue']], on=['order_id', 'product_id'], how='left')
    returns_full = returns_full.merge(data['products'][['product_id', 'category', 'segment']], on='product_id', how='left')
    
    cat_returns = returns_full.groupby('category').agg(
        return_count=('return_id', 'count'),
        return_value=('item_revenue', 'sum')
    ).sort_values('return_count', ascending=False).reset_index()

    col1, col2 = st.columns(2)
    with col1:
        fig1a = px.bar(cat_returns, x='category', y='return_count',
                       title="Số lượng sản phẩm hoàn trả theo danh mục",
                       color='category', color_discrete_sequence=PLOTLY_COLORS,
                       labels={'category': 'Danh mục', 'return_count': 'Số lượng'})
        fig1a.update_layout(height=380, showlegend=False)
        st.plotly_chart(apply_dark_theme(fig1a), use_container_width=True)
    with col2:
        reason_cnt = returns['return_reason'].value_counts().reset_index()
        reason_cnt.columns = ['reason', 'count']
        fig1b = px.pie(reason_cnt, values='count', names='reason',
                       title="Lý do hoàn trả phổ biến",
                       color_discrete_sequence=PLOTLY_COLORS, hole=0.4)
        fig1b.update_layout(height=380)
        st.plotly_chart(apply_dark_theme(fig1b), use_container_width=True)

    # Return value lost
    total_value_lost = returns_full['item_revenue'].sum()
    st.markdown(f"> **Insight**: Tổng giá trị doanh thu bị mất do hoàn trả ước tính: **{format_currency(total_value_lost)}**.")

    st.markdown("---")

    # ============================================================
    # 5.2 Tương quan Giao hàng & Trải nghiệm
    # ============================================================
    st.markdown("### ⭐ 5.2 Ảnh hưởng của Thời gian Giao hàng đến Trải nghiệm Khách hàng")

    delivery_reviews = ship_data[['order_id', 'delivery_time']].merge(
        reviews[['order_id', 'rating']], on='order_id', how='inner'
    )
    # Remove outliers for plot clarity (e.g. negative or > 30 days)
    delivery_reviews = delivery_reviews[(delivery_reviews['delivery_time'] >= 0) & (delivery_reviews['delivery_time'] <= 30)]
    
    rating_by_days = delivery_reviews.groupby('delivery_time')['rating'].agg(['mean', 'count']).reset_index()
    rating_by_days = rating_by_days[rating_by_days['count'] >= 5]  # Filter noise

    fig2 = px.scatter(rating_by_days, x='delivery_time', y='mean', size='count',
                      title="Thời gian giao hàng (ngày) vs Điểm đánh giá trung bình",
                      labels={'delivery_time': 'Thời gian giao hàng (Ngày)', 'mean': 'Rating Trung Bình'},
                      color='mean', color_continuous_scale='RdYlGn')
    fig2.add_hline(y=avg_rating, line_dash="dash", line_color=COLOR_NEU, annotation_text="Rating TB chung")
    fig2.update_layout(height=450)
    st.plotly_chart(apply_dark_theme(fig2), use_container_width=True)

    st.markdown("---")

    # ============================================================
    # 5.3 Geographic Analysis
    # ============================================================
    st.markdown("### 🗺️ 5.3 Phân bố Địa lý & Hiệu suất Vùng miền")

    geo_orders = orders.dropna(subset=['region'])
    region_stats = geo_orders.groupby('region').agg(
        order_count=('order_id', 'count'),
        total_rev=('total_amount', 'sum')
    ).reset_index()
    
    # Calculate avg delivery time by region
    geo_ships = geo_orders[['order_id', 'region']].merge(ship_data[['order_id', 'delivery_time']], on='order_id', how='inner')
    region_delivery = geo_ships.groupby('region')['delivery_time'].mean().reset_index()
    region_stats = region_stats.merge(region_delivery, on='region', how='left')

    col1, col2 = st.columns(2)
    with col1:
        fig3a = px.pie(region_stats, values='order_count', names='region',
                       title="Cơ cấu đơn hàng theo Vùng (Region)",
                       color_discrete_sequence=PLOTLY_COLORS, hole=0.3)
        fig3a.update_layout(height=380)
        st.plotly_chart(apply_dark_theme(fig3a), use_container_width=True)
    with col2:
        fig3b = px.bar(region_stats, x='region', y='delivery_time',
                       title="Thời gian giao hàng trung bình theo Vùng",
                       color='region', color_discrete_sequence=PLOTLY_COLORS,
                       labels={'region': 'Vùng', 'delivery_time': 'Ngày giao hàng TB'})
        fig3b.add_hline(y=avg_delivery_time, line_dash="dash", line_color=COLOR_NEG, annotation_text="TB Toàn quốc")
        fig3b.update_layout(height=380, showlegend=False)
        st.plotly_chart(apply_dark_theme(fig3b), use_container_width=True)

    st.markdown("---")

    # ============================================================
    # 5.4 Nghịch lý Phí vận chuyển (Shipping Paradox)
    # ============================================================
    st.markdown("### 💸 5.4 Phân tích Hiệu suất Giao hàng và Nghịch lý Phí vận chuyển")

    shipping_stats = geo_ships.merge(ship_data[['order_id', 'shipping_fee']], on='order_id', how='inner')
    
    # Phân nhóm thời gian giao hàng
    shipping_stats['delivery_speed'] = pd.cut(
        shipping_stats['delivery_time'],
        bins=[-1, 2, 5, 10, 100],
        labels=['Fast (0-2d)', 'Normal (3-5d)', 'Slow (6-10d)', 'Very Slow (>10d)']
    )
    
    speed_summary = shipping_stats.groupby('delivery_speed').agg(
        order_count=('order_id', 'count'),
        avg_fee=('shipping_fee', 'mean')
    ).reset_index()

    fig4 = make_subplots(specs=[[{"secondary_y": True}]])
    fig4.add_trace(go.Bar(x=speed_summary['delivery_speed'], y=speed_summary['order_count'],
                          name='Số lượng đơn', marker_color=COLOR_PRIMARY, opacity=0.7),
                   secondary_y=False)
    fig4.add_trace(go.Scatter(x=speed_summary['delivery_speed'], y=speed_summary['avg_fee'],
                              mode='lines+markers+text', name='Phí ship TB',
                              text=speed_summary['avg_fee'].apply(lambda x: f"${x:.2f}"),
                              textposition="top center",
                              line=dict(color=COLOR_NEG, width=3), marker=dict(size=10)),
                   secondary_y=True)

    fig4.update_layout(title="Mối quan hệ giữa Tốc độ giao hàng và Phí vận chuyển trung bình",
                       height=450)
    fig4.update_yaxes(title_text="Số lượng đơn", secondary_y=False)
    fig4.update_yaxes(title_text="Phí ship trung bình ($)", secondary_y=True)
    st.plotly_chart(apply_dark_theme(fig4), use_container_width=True)

    st.markdown("""
> **Insight - Nghịch lý Phí Vận Chuyển**: 
> Khách hàng chờ lâu hơn lại phải trả phí ship trung bình cao hơn. Điều này chỉ ra vấn đề nghiêm trọng trong logic định tuyến hoặc thỏa thuận với đối tác giao hàng (đặc biệt ở các tuyến vùng sâu vùng xa). Cần rà soát ngay lập tức!
    """)
