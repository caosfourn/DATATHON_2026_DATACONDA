"""Phase 4: Sales Behavior Analysis
4 biểu đồ từ notebook:
  4.1 AOV Distribution Analysis
  4.2 Promotion Sensitivity Analysis
  4.3 Promotion Impact Deep Dive (Price Elasticity & What-If Simulator)
  4.4 Payment Method & Installment Analysis
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
    st.markdown("## 💰 Phase 4: Sales Behavior Analysis")
    st.markdown("**Mục tiêu**: Phân tích hành vi mua hàng và hiệu quả khuyến mãi")
    st.markdown("---")

    orders = data['orders']
    order_items = data['order_items']
    payments = data['payments']
    products = data['products']
    promotions = data['promotions']

    # ============================================================
    # 4.1 AOV Distribution Analysis
    # ============================================================
    st.markdown("### 📊 4.1 AOV Distribution Analysis")

    order_values = orders.dropna(subset=['total_amount'])

    col1, col2 = st.columns(2)
    with col1:
        fig1a = px.histogram(order_values, x='total_amount', nbins=50,
                             title="Phân phối giá trị đơn hàng",
                             labels={'total_amount': 'Giá trị đơn (VND)'},
                             color_discrete_sequence=[COLOR_PRIMARY])
        q1 = order_values['total_amount'].quantile(0.25)
        median = order_values['total_amount'].median()
        q3 = order_values['total_amount'].quantile(0.75)
        fig1a.add_vline(x=median, line_dash="dash", line_color=COLOR_NEG,
                        annotation_text=f"Median: {median:,.0f}")
        fig1a.update_layout(height=400)
        fig1a = apply_dark_theme(fig1a)
        st.plotly_chart(fig1a, use_container_width=True)

    with col2:
        fig1b = px.box(order_values, y='total_amount',
                       title="Box Plot giá trị đơn hàng",
                       labels={'total_amount': 'Giá trị đơn (VND)'},
                       color_discrete_sequence=[COLOR_PRIMARY])
        fig1b.update_layout(height=400)
        fig1b = apply_dark_theme(fig1b)
        st.plotly_chart(fig1b, use_container_width=True)

    # Stats
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(create_metric_card_html("Mean AOV", format_currency(order_values['total_amount'].mean())), unsafe_allow_html=True)
    with col2:
        st.markdown(create_metric_card_html("Median AOV", format_currency(median)), unsafe_allow_html=True)
    with col3:
        st.markdown(create_metric_card_html("Q1", format_currency(q1)), unsafe_allow_html=True)
    with col4:
        st.markdown(create_metric_card_html("Q3", format_currency(q3)), unsafe_allow_html=True)

    st.markdown("---")

    # ============================================================
    # 4.2 Promotion Sensitivity Analysis
    # ============================================================
    st.markdown("### 🏷️ 4.2 Promotion Sensitivity Analysis")

    oi_promo = order_items.copy()
    oi_promo['has_promo'] = oi_promo['promo_id'].notna()

    promo_comparison = oi_promo.groupby('has_promo').agg(
        order_count=('order_id', 'nunique'),
        avg_revenue=('item_revenue', 'mean'),
        avg_quantity=('quantity', 'mean'),
        avg_discount=('discount_amount', 'mean')
    )
    promo_comparison.index = ['Không KM', 'Có KM']

    fig2 = make_subplots(rows=1, cols=3,
                         subplot_titles=("Số đơn hàng", "Doanh thu TB / item", "Chiết khấu TB"))
    fig2.add_trace(go.Bar(x=promo_comparison.index, y=promo_comparison['order_count'],
                          marker_color=[COLOR_PRIMARY, COLOR_POS]), row=1, col=1)
    fig2.add_trace(go.Bar(x=promo_comparison.index, y=promo_comparison['avg_revenue'],
                          marker_color=[COLOR_PRIMARY, COLOR_POS]), row=1, col=2)
    fig2.add_trace(go.Bar(x=promo_comparison.index, y=promo_comparison['avg_discount'].fillna(0),
                          marker_color=[COLOR_PRIMARY, COLOR_NEG]), row=1, col=3)
    fig2.update_layout(height=400, showlegend=False,
                       title_text="So sánh đơn có/không có khuyến mãi")
    fig2 = apply_dark_theme(fig2)
    st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")

    # ============================================================
    # 4.3 PROMOTION IMPACT DEEP DIVE: Price Elasticity
    # ============================================================
    st.markdown("### 📉 4.3 PROMOTION IMPACT DEEP DIVE: Price Elasticity & What-If Simulator")

    # Data Prep
    oi_full = order_items.merge(orders[['order_id','order_date','order_status']], on='order_id')
    oi_full = oi_full.merge(products[['product_id','product_name','category','segment','price','cogs']], on='product_id')
    oi_full = oi_full.merge(promotions[['promo_id','promo_name','promo_type','discount_value']], on='promo_id', how='left')

    oi_del = oi_full[oi_full['order_status']=='delivered'].copy()
    oi_del['order_date'] = pd.to_datetime(oi_del['order_date'])
    oi_del['gross_revenue'] = oi_del['quantity'] * oi_del['unit_price']
    oi_del['original_revenue'] = oi_del['quantity'] * oi_del['price']
    oi_del['total_cogs'] = oi_del['quantity'] * oi_del['cogs']
    oi_del['gross_profit'] = oi_del['gross_revenue'] - oi_del['total_cogs']

    oi_del['disc_level'] = np.where(oi_del['promo_id'].isna(), 0, oi_del['discount_value'].fillna(0))
    oi_pct = oi_del[(oi_del['promo_id'].isna()) | (oi_del['promo_type']=='percentage')].copy()

    categories = sorted(oi_pct['category'].unique())
    # Safely get unique discount levels > 0
    positive_discounts = oi_pct[oi_pct['disc_level']>0]['disc_level'].unique()
    disc_levels = sorted(positive_discounts) if len(positive_discounts) > 0 else []

    if len(disc_levels) > 0:
        elasticity_data = []
        for cat in categories:
            cat_data = oi_pct[oi_pct['category']==cat]
            base = cat_data[cat_data['disc_level']==0]
            if len(base) == 0: continue
            
            base_daily_orders = base.groupby('order_date')['order_id'].nunique()
            base_avg = base_daily_orders.mean()
            base_avg_rev = base['gross_revenue'].mean()
            base_avg_profit = base['gross_profit'].mean()
            base_margin = base['gross_profit'].sum() / base['gross_revenue'].sum() * 100 if base['gross_revenue'].sum() > 0 else 0
            
            for dl in disc_levels:
                promo_data = cat_data[cat_data['disc_level']==dl]
                if len(promo_data) < 30: continue
                promo_daily_orders = promo_data.groupby('order_date')['order_id'].nunique()
                promo_avg = promo_daily_orders.mean()
                
                pct_demand_change = (promo_avg - base_avg) / base_avg * 100 if base_avg > 0 else 0
                elasticity = pct_demand_change / dl if dl > 0 else 0
                
                promo_avg_rev = promo_data['gross_revenue'].mean()
                promo_avg_profit = promo_data['gross_profit'].mean()
                promo_margin = promo_data['gross_profit'].sum() / promo_data['gross_revenue'].sum() * 100 if promo_data['gross_revenue'].sum() > 0 else 0
                
                profit_change = (promo_avg_profit - base_avg_profit) / base_avg_profit * 100 if base_avg_profit > 0 else 0
                
                elasticity_data.append({
                    'Category': cat, 'Discount_%': dl,
                    'Elasticity': elasticity,
                    'Order_Lift_%': pct_demand_change,
                    'Margin_Erosion_pp': promo_margin - base_margin,
                    'Avg_Profit_Change_%': profit_change,
                    'Promo_Margin_%': promo_margin
                })

        if elasticity_data:
            df_elast = pd.DataFrame(elasticity_data)

            # Draw 4 subplots
            col1, col2 = st.columns(2)
            
            with col1:
                # 1. Elasticity Heatmap
                pivot_elast = df_elast.pivot_table(index='Category', columns='Discount_%', values='Elasticity')
                fig_el = go.Figure(data=go.Heatmap(
                    z=pivot_elast.values, x=pivot_elast.columns, y=pivot_elast.index,
                    colorscale='RdYlGn', zmid=0, text=pivot_elast.values.round(2), texttemplate="%{text}"
                ))
                fig_el.update_layout(title="Price Elasticity by Category & Discount Level", height=350)
                st.plotly_chart(apply_dark_theme(fig_el), use_container_width=True)
                
                # 3. Order Lift vs Discount
                fig_lift = px.line(df_elast, x='Discount_%', y='Order_Lift_%', color='Category', markers=True,
                                   title="Order Volume Lift (%) by Discount Level",
                                   color_discrete_sequence=PLOTLY_COLORS)
                fig_lift.add_hline(y=0, line_dash="dash", line_color=COLOR_NEU)
                fig_lift.update_layout(height=350)
                st.plotly_chart(apply_dark_theme(fig_lift), use_container_width=True)
                
            with col2:
                # 2. Margin Erosion Heatmap
                pivot_margin = df_elast.pivot_table(index='Category', columns='Discount_%', values='Margin_Erosion_pp')
                fig_mg = go.Figure(data=go.Heatmap(
                    z=pivot_margin.values, x=pivot_margin.columns, y=pivot_margin.index,
                    colorscale='RdYlGn', zmid=0, text=pivot_margin.values.round(1), texttemplate="%{text}"
                ))
                fig_mg.update_layout(title="Margin Erosion (pp) vs No-Promo Baseline", height=350)
                st.plotly_chart(apply_dark_theme(fig_mg), use_container_width=True)
                
                # 4. Profit Impact vs Discount
                fig_prof = px.line(df_elast, x='Discount_%', y='Avg_Profit_Change_%', color='Category', markers=True,
                                   title="Avg Profit Change (%) vs No-Promo Baseline",
                                   color_discrete_sequence=PLOTLY_COLORS)
                fig_prof.add_hline(y=0, line_dash="dash", line_color=COLOR_NEU)
                fig_prof.update_layout(height=350)
                st.plotly_chart(apply_dark_theme(fig_prof), use_container_width=True)

            # What-If Simulator Table
            st.markdown("#### 🔮 What-If Scenario Simulator")
            scenarios = []
            for cat in categories:
                cat_base = oi_pct[(oi_pct['category']==cat) & (oi_pct['disc_level']==0)]
                if len(cat_base) == 0: continue
                base_margin = cat_base['gross_profit'].sum() / cat_base['gross_revenue'].sum() * 100
                avg_elasticity = df_elast[df_elast['Category']==cat]['Elasticity'].mean()
                
                for sim_disc in [5, 10, 15, 20]:
                    pred_order_lift = avg_elasticity * sim_disc
                    rev_change = (1 + pred_order_lift/100) * (1 - sim_disc/100) - 1
                    new_margin_pct = base_margin - sim_disc
                    profit_change = (pred_order_lift/100 + 1) * (new_margin_pct/base_margin) - 1
                    
                    scenarios.append({
                        'Category': cat, 'Discount (%)': sim_disc,
                        'Elasticity': round(avg_elasticity, 2),
                        'Order Lift (%)': round(pred_order_lift, 1),
                        'Revenue Δ (%)': round(rev_change*100, 1),
                        'New Margin (%)': round(new_margin_pct, 1),
                        'Profit Δ (%)': round(profit_change*100, 1),
                        'Verdict': 'Tốt' if profit_change > 0 else ('Rủi ro' if profit_change > -0.2 else 'Lỗ')
                    })
            if scenarios:
                st.dataframe(pd.DataFrame(scenarios), hide_index=True)

    st.markdown("---")

    # ============================================================
    # 4.4 Payment Method & Installment Analysis
    # ============================================================
    st.markdown("### 💳 4.4 Payment Method & Installment Analysis")

    pay_stats = payments.groupby('payment_method').agg(
        count=('order_id', 'count'),
        avg_value=('payment_value', 'mean'),
        avg_installments=('installments', 'mean')
    ).sort_values('count', ascending=False)

    fig3 = make_subplots(rows=1, cols=3,
                         subplot_titles=("Số lượng giao dịch", "Giá trị TB / giao dịch", "Số kỳ trả góp TB"))
    fig3.add_trace(go.Bar(x=pay_stats.index, y=pay_stats['count'],
                          marker_color=PLOTLY_COLORS[:len(pay_stats)]), row=1, col=1)
    fig3.add_trace(go.Bar(x=pay_stats.index, y=pay_stats['avg_value'],
                          marker_color=PLOTLY_COLORS[:len(pay_stats)]), row=1, col=2)
    fig3.add_trace(go.Bar(x=pay_stats.index, y=pay_stats['avg_installments'],
                          marker_color=PLOTLY_COLORS[:len(pay_stats)]), row=1, col=3)
    fig3.update_layout(height=400, showlegend=False,
                       title_text="Payment Method & Installment Analysis")
    fig3 = apply_dark_theme(fig3)
    st.plotly_chart(fig3, use_container_width=True)

    st.markdown("**Payment Method Summary:**")
    st.dataframe(pay_stats.round(1), use_container_width=True)
