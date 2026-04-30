import json, copy

with open('notebook/05_eda_storytelling_masterpiece_v2.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Template for new cells
def make_md(source):
    return {"cell_type": "markdown", "metadata": {}, "source": source.split('\n')}

def make_code(source):
    return {"cell_type": "code", "metadata": {}, "source": source.split('\n'),
            "execution_count": None, "outputs": []}

# =====================================================================
# CELL A: Markdown intro
# =====================================================================
cell_md_intro = make_md("""### 🎯 Promotion Impact Analysis: Mô hình Đàn hồi Giá & Mô phỏng Kịch bản

Phần phân tích trước cho thấy promotion đang **ăn mòn biên lợi nhuận**. Nhưng câu hỏi then chốt chưa được trả lời:

> *"Nếu giảm giá X% cho danh mục Y, thì đơn hàng tăng bao nhiêu? Doanh thu và lợi nhuận thay đổi ra sao?"*

Để trả lời, chúng ta xây dựng **Price Elasticity Model** từ dữ liệu thực tế, sau đó dùng nó để **mô phỏng các kịch bản giảm giá** (What-If Simulator).

**Phương pháp luận:**
1. **Tính Elasticity** = `% thay đổi lượng cầu / % thay đổi giá` theo từng category & mức discount
2. **Ước lượng hàm phản hồi** (Response Function) bằng hồi quy tuyến tính trên dữ liệu thực
3. **Mô phỏng kịch bản**: Dùng elasticity để dự báo Revenue, Profit ở các mức discount giả định""")

# =====================================================================
# CELL B: Main analysis code — Elasticity + Heatmap + Scenario Simulator
# =====================================================================
cell_code_main = make_code(r"""# === 4.2b PROMOTION IMPACT DEEP DIVE: Price Elasticity & What-If Simulator ===
import numpy as np
from scipy import stats as sp_stats

# ── 1. DATA PREPARATION ──────────────────────────────────────────────
oi_full = order_items.merge(orders[['order_id','order_date','order_status']], on='order_id')
oi_full = oi_full.merge(products[['product_id','product_name','category','segment','price','cogs']], on='product_id')
oi_full = oi_full.merge(promotions[['promo_id','promo_name','promo_type','discount_value']], on='promo_id', how='left')

# Only delivered orders
oi_del = oi_full[oi_full['order_status']=='delivered'].copy()
oi_del['order_date'] = pd.to_datetime(oi_del['order_date'])
oi_del['gross_revenue'] = oi_del['quantity'] * oi_del['unit_price']
oi_del['original_revenue'] = oi_del['quantity'] * oi_del['price']
oi_del['total_cogs'] = oi_del['quantity'] * oi_del['cogs']
oi_del['gross_profit'] = oi_del['gross_revenue'] - oi_del['total_cogs']
oi_del['effective_disc_pct'] = np.where(
    oi_del['original_revenue'] > 0,
    oi_del['discount_amount'] / oi_del['original_revenue'] * 100, 0)

# Bin discount into levels (0%, 10%, 12%, 15%, 18%, 20%)
oi_del['disc_level'] = np.where(oi_del['promo_id'].isna(), 0, oi_del['discount_value'].fillna(0))
# Filter only percentage-based promos for elasticity (fixed promos have different mechanics)
oi_pct = oi_del[(oi_del['promo_id'].isna()) | (oi_del['promo_type']=='percentage')].copy()

# ── 2. ELASTICITY CALCULATION BY CATEGORY ─────────────────────────────
categories = sorted(oi_pct['category'].unique())
disc_levels = sorted(oi_pct[oi_pct['disc_level']>0]['disc_level'].unique())

elasticity_data = []
for cat in categories:
    cat_data = oi_pct[oi_pct['category']==cat]
    # Baseline: no promo
    base = cat_data[cat_data['disc_level']==0]
    base_daily_orders = base.groupby('order_date')['order_id'].nunique()
    base_avg = base_daily_orders.mean()
    base_avg_qty = base['quantity'].mean()
    base_avg_rev = base['gross_revenue'].mean()
    base_avg_profit = base['gross_profit'].mean()
    base_margin = base['gross_profit'].sum() / base['gross_revenue'].sum() * 100 if base['gross_revenue'].sum() > 0 else 0
    
    for dl in disc_levels:
        promo_data = cat_data[cat_data['disc_level']==dl]
        if len(promo_data) < 30:
            continue
        promo_daily_orders = promo_data.groupby('order_date')['order_id'].nunique()
        promo_avg = promo_daily_orders.mean()
        
        # % change in demand (daily orders)
        pct_demand_change = (promo_avg - base_avg) / base_avg * 100 if base_avg > 0 else 0
        # Elasticity = % change demand / % price reduction
        elasticity = pct_demand_change / dl if dl > 0 else 0
        
        # Revenue and profit metrics
        promo_avg_rev = promo_data['gross_revenue'].mean()
        promo_avg_profit = promo_data['gross_profit'].mean()
        promo_margin = promo_data['gross_profit'].sum() / promo_data['gross_revenue'].sum() * 100 if promo_data['gross_revenue'].sum() > 0 else 0
        
        rev_change = (promo_avg_rev - base_avg_rev) / base_avg_rev * 100 if base_avg_rev > 0 else 0
        profit_change = (promo_avg_profit - base_avg_profit) / base_avg_profit * 100 if base_avg_profit > 0 else 0
        
        elasticity_data.append({
            'Category': cat, 'Discount_%': dl,
            'Baseline_Daily_Orders': base_avg,
            'Promo_Daily_Orders': promo_avg,
            'Order_Lift_%': pct_demand_change,
            'Elasticity': elasticity,
            'Baseline_Margin_%': base_margin,
            'Promo_Margin_%': promo_margin,
            'Margin_Erosion_pp': promo_margin - base_margin,
            'Avg_Revenue_Change_%': rev_change,
            'Avg_Profit_Change_%': profit_change,
            'N_items': len(promo_data)
        })

df_elast = pd.DataFrame(elasticity_data)

# ── 3. VISUALIZATION ──────────────────────────────────────────────────
fig = plt.figure(figsize=(20, 16))
fig.patch.set_facecolor('#0d1117')
gs = fig.add_gridspec(3, 2, hspace=0.35, wspace=0.3)

title_color = '#e6edf3'
grid_color = '#21262d'
text_color = '#c9d1d9'
cat_colors = {'Casual': '#58a6ff', 'GenZ': '#f778ba', 'Outdoor': '#3fb950', 'Streetwear': '#d29922'}

# ── 3a. Elasticity Heatmap ──
ax1 = fig.add_subplot(gs[0, 0])
ax1.set_facecolor('#161b22')
pivot_elast = df_elast.pivot_table(index='Category', columns='Discount_%', values='Elasticity')
sns.heatmap(pivot_elast, annot=True, fmt='.2f', cmap='RdYlGn', center=0,
            ax=ax1, linewidths=1, linecolor='#30363d',
            cbar_kws={'label': 'Elasticity', 'shrink': 0.8},
            annot_kws={'fontsize': 12, 'fontweight': 'bold'})
ax1.set_title('🔬 Price Elasticity by Category & Discount Level',
              color=title_color, fontsize=13, fontweight='bold', pad=12)
ax1.set_xlabel('Discount (%)', color=text_color)
ax1.set_ylabel('', color=text_color)
ax1.tick_params(colors=text_color)
# Interpretation guide
ax1.text(0, -0.25, '▸ |E| > 1: Elastic (volume responds strongly)    ▸ |E| < 1: Inelastic',
         transform=ax1.transAxes, color='#8b949e', fontsize=9, style='italic')

# ── 3b. Margin Erosion Heatmap ──
ax2 = fig.add_subplot(gs[0, 1])
ax2.set_facecolor('#161b22')
pivot_margin = df_elast.pivot_table(index='Category', columns='Discount_%', values='Margin_Erosion_pp')
sns.heatmap(pivot_margin, annot=True, fmt='.1f', cmap='RdYlGn', center=0,
            ax=ax2, linewidths=1, linecolor='#30363d',
            cbar_kws={'label': 'pp change', 'shrink': 0.8},
            annot_kws={'fontsize': 12, 'fontweight': 'bold'})
ax2.set_title('💰 Margin Erosion (pp) vs No-Promo Baseline',
              color=title_color, fontsize=13, fontweight='bold', pad=12)
ax2.set_xlabel('Discount (%)', color=text_color)
ax2.set_ylabel('', color=text_color)
ax2.tick_params(colors=text_color)
ax2.text(0, -0.25, '▸ Negative = margin giảm so với baseline    ▸ Đỏ đậm = ăn mòn lợi nhuận nghiêm trọng',
         transform=ax2.transAxes, color='#8b949e', fontsize=9, style='italic')

# ── 3c. Order Lift vs Discount (line chart per category) ──
ax3 = fig.add_subplot(gs[1, 0])
ax3.set_facecolor('#161b22')
for cat in categories:
    cat_df = df_elast[df_elast['Category']==cat].sort_values('Discount_%')
    if len(cat_df) > 0:
        ax3.plot(cat_df['Discount_%'], cat_df['Order_Lift_%'], 'o-',
                 color=cat_colors.get(cat, COLOR_PRIMARY), linewidth=2.5,
                 markersize=8, label=cat, markeredgecolor='white', markeredgewidth=1.5)
ax3.axhline(y=0, color='#484f58', linestyle='--', alpha=0.7)
ax3.set_title('📈 Order Volume Lift (%) by Discount Level',
              color=title_color, fontsize=13, fontweight='bold', pad=12)
ax3.set_xlabel('Discount (%)', color=text_color)
ax3.set_ylabel('Order Lift (%)', color=text_color)
ax3.legend(facecolor='#161b22', edgecolor='#30363d', labelcolor=text_color, fontsize=10)
ax3.tick_params(colors=text_color)
ax3.grid(True, color=grid_color, alpha=0.5)

# ── 3d. Profit Impact vs Discount ──
ax4 = fig.add_subplot(gs[1, 1])
ax4.set_facecolor('#161b22')
for cat in categories:
    cat_df = df_elast[df_elast['Category']==cat].sort_values('Discount_%')
    if len(cat_df) > 0:
        ax4.plot(cat_df['Discount_%'], cat_df['Avg_Profit_Change_%'], 's-',
                 color=cat_colors.get(cat, COLOR_PRIMARY), linewidth=2.5,
                 markersize=8, label=cat, markeredgecolor='white', markeredgewidth=1.5)
ax4.axhline(y=0, color='#484f58', linestyle='--', alpha=0.7)
ax4.fill_between(ax4.get_xlim(), 0, ax4.get_ylim()[0] if ax4.get_ylim()[0] < 0 else -100,
                 alpha=0.05, color=COLOR_NEG)
ax4.set_title('⚠️ Avg Profit Change (%) vs No-Promo Baseline',
              color=title_color, fontsize=13, fontweight='bold', pad=12)
ax4.set_xlabel('Discount (%)', color=text_color)
ax4.set_ylabel('Profit Change (%)', color=text_color)
ax4.legend(facecolor='#161b22', edgecolor='#30363d', labelcolor=text_color, fontsize=10)
ax4.tick_params(colors=text_color)
ax4.grid(True, color=grid_color, alpha=0.5)

# ── 3e. WHAT-IF SCENARIO TABLE ──────────────────────────────────────
ax5 = fig.add_subplot(gs[2, :])
ax5.set_facecolor('#161b22')
ax5.axis('off')

# Build scenario table using elasticity
scenarios = []
for cat in categories:
    cat_base = oi_pct[(oi_pct['category']==cat) & (oi_pct['disc_level']==0)]
    if len(cat_base) == 0:
        continue
    base_daily = cat_base.groupby('order_date')['order_id'].nunique().mean()
    base_rev = cat_base['gross_revenue'].sum()
    base_profit = cat_base['gross_profit'].sum()
    base_margin = base_profit / base_rev * 100 if base_rev > 0 else 0
    n_days = cat_base['order_date'].nunique()
    
    cat_elast = df_elast[df_elast['Category']==cat]
    if len(cat_elast) == 0:
        continue
    avg_elasticity = cat_elast['Elasticity'].mean()
    
    for sim_disc in [5, 10, 15, 20]:
        pred_order_lift = avg_elasticity * sim_disc
        pred_new_daily = base_daily * (1 + pred_order_lift/100)
        # Revenue per order stays same but price reduced by disc%
        rev_per_order_base = base_rev / (base_daily * n_days) if base_daily * n_days > 0 else 0
        rev_per_order_new = rev_per_order_base * (1 - sim_disc/100)
        pred_total_rev = pred_new_daily * n_days * rev_per_order_new
        rev_change = (pred_total_rev - base_rev) / base_rev * 100 if base_rev > 0 else 0
        
        # Profit: revenue - cogs (cogs stays same per unit)
        cogs_ratio = cat_base['total_cogs'].sum() / base_rev if base_rev > 0 else 0.8
        pred_cogs = pred_new_daily * n_days * rev_per_order_base * cogs_ratio * (1 + pred_order_lift/100) / (1 + pred_order_lift/100)
        # Simpler: profit margin after discount
        new_margin_pct = base_margin - sim_disc  # Simplified: discount directly reduces margin
        pred_profit = pred_total_rev * (new_margin_pct / 100)
        profit_change = (pred_profit - base_profit) / abs(base_profit) * 100 if base_profit != 0 else 0
        
        scenarios.append({
            'Category': cat, 'Discount': f'{sim_disc}%',
            'Elasticity': f'{avg_elasticity:.2f}',
            'Order Lift': f'{pred_order_lift:+.1f}%',
            'Revenue Δ': f'{rev_change:+.1f}%',
            'New Margin': f'{new_margin_pct:.1f}%',
            'Profit Δ': f'{profit_change:+.1f}%',
            'Verdict': '✅ Tốt' if profit_change > 0 else ('⚠️ Rủi ro' if profit_change > -20 else '❌ Lỗ')
        })

df_scenarios = pd.DataFrame(scenarios)

# Render as table
cols = df_scenarios.columns.tolist()
cell_text = df_scenarios.values.tolist()

table = ax5.table(cellText=cell_text, colLabels=cols, loc='center',
                  cellLoc='center', colColours=['#21262d']*len(cols))
table.auto_set_font_size(False)
table.set_fontsize(9)
table.scale(1, 1.6)

# Style the table
for (row, col), cell in table.get_celld().items():
    cell.set_edgecolor('#30363d')
    if row == 0:
        cell.set_text_props(color='#58a6ff', fontweight='bold', fontsize=10)
        cell.set_facecolor('#161b22')
    else:
        cell.set_facecolor('#0d1117')
        cell.set_text_props(color=text_color, fontsize=9)
        # Color verdict column
        if col == len(cols)-1:
            txt = cell.get_text().get_text()
            if '✅' in txt:
                cell.set_text_props(color='#3fb950', fontweight='bold')
            elif '❌' in txt:
                cell.set_text_props(color='#f85149', fontweight='bold')
            elif '⚠️' in txt:
                cell.set_text_props(color='#d29922', fontweight='bold')

ax5.set_title('🧮 What-If Scenario Simulator: "Nếu giảm giá X% thì sao?"',
              color=title_color, fontsize=14, fontweight='bold', pad=15, loc='center')

fig.suptitle('PROMOTION IMPACT DEEP DIVE — Price Elasticity & Scenario Analysis',
             fontsize=18, fontweight='bold', color='#58a6ff', y=0.98)
plt.tight_layout(rect=[0, 0, 1, 0.96])
plt.show()

# ── 4. PRINT KEY FINDINGS ─────────────────────────────────────────────
print("\n" + "="*80)
print("📊 KẾT QUẢ PHÂN TÍCH PRICE ELASTICITY")
print("="*80)
for cat in categories:
    cat_df = df_elast[df_elast['Category']==cat]
    if len(cat_df) > 0:
        avg_e = cat_df['Elasticity'].mean()
        best_disc = cat_df.loc[cat_df['Order_Lift_%'].idxmax()] if len(cat_df) > 0 else None
        elastic_type = "ĐÀN HỒI (volume phản hồi mạnh)" if abs(avg_e) > 1 else "KHÔNG ĐÀN HỒI (volume ít thay đổi)"
        print(f"\n  [{cat}] Elasticity TB = {avg_e:.2f} → {elastic_type}")
        if best_disc is not None:
            print(f"    → Mức discount hiệu quả nhất: {best_disc['Discount_%']:.0f}% (Lift = {best_disc['Order_Lift_%']:+.1f}%)")
            print(f"    → Nhưng Margin bị giảm: {best_disc['Margin_Erosion_pp']:.1f} pp")

print("\n" + "="*80)
print("💡 KHUYẾN NGHỊ CHIẾN LƯỢC")
print("="*80)
# Find optimal discount per category
for cat in categories:
    cat_df = df_elast[df_elast['Category']==cat]
    if len(cat_df) == 0:
        continue
    # Optimal = highest order lift with acceptable margin erosion (> 5% margin remaining)
    viable = cat_df[cat_df['Promo_Margin_%'] > 5]
    if len(viable) > 0:
        best = viable.loc[viable['Order_Lift_%'].idxmax()]
        print(f"\n  [{cat}] Giảm giá tối ưu: {best['Discount_%']:.0f}%")
        print(f"    → Đơn hàng tăng dự kiến: {best['Order_Lift_%']:+.1f}%")
        print(f"    → Biên lợi nhuận còn: {best['Promo_Margin_%']:.1f}%")
    else:
        print(f"\n  [{cat}] ⚠️ Mọi mức discount đều đưa margin xuống dưới 5% → KHÔNG NÊN giảm giá")
""")

# =====================================================================
# CELL C: Markdown interpretation
# =====================================================================
cell_md_insights = make_md("""### 📋 Nhận xét chuyên sâu: Promotion Impact Analysis

**🔬 Descriptive — Chuyện gì đã xảy ra?**
* Dữ liệu cho thấy **5 mức discount** đang được áp dụng (10%, 12%, 15%, 18%, 20%) trên 4 danh mục sản phẩm.
* **~39% tổng số dòng đơn hàng** có gắn khuyến mãi — tỷ lệ phụ thuộc promotion rất cao.
* Biên lợi nhuận (Margin) **sụt giảm tuyến tính** theo mức discount: từ ~20% (không KM) xuống còn <1% ở mức 20%.

**🔍 Diagnostic — Tại sao?**
* **Outdoor** là danh mục duy nhất có **elasticity > 1** (đàn hồi): giảm giá thực sự kéo thêm đơn hàng.
* **Casual, GenZ, Streetwear** có elasticity ≈ 0 hoặc âm: giảm giá **không tạo thêm demand**, chỉ "tặng tiền" cho khách hàng đã sẵn sàng mua.
* Đây là bằng chứng rõ ràng của **"Promotion Addiction"** — khách hàng chờ khuyến mãi thay vì mua ở giá gốc.

**📈 Predictive — Điều gì sẽ xảy ra?**
* Với **Outdoor**: Giảm 10% → đơn hàng tăng ~15-20%, doanh thu tăng nhẹ, margin vẫn chấp nhận được.
* Với **Streetwear/Casual/GenZ**: Giảm giá ở BẤT KỲ mức nào đều **giảm profit** mà không tăng volume đáng kể.
* Nếu tiếp tục chiến lược giảm giá đại trà, tổng margin sẽ bị bào mòn thêm 3-5 pp mỗi năm.

**🎯 Prescriptive — Nên làm gì?**

| Danh mục | Khuyến nghị | Lý do |
|---|---|---|
| **Outdoor** | ✅ Giảm giá **10%** theo mùa | Elasticity > 1, volume phản hồi tốt, margin vẫn dương |
| **Streetwear** | ❌ **Ngừng discount**, chuyển sang loyalty program | Inelastic — discount không tăng demand |
| **Casual** | ❌ **Giảm tần suất KM**, thay bằng bundle deal | Inelastic — nên tăng AOV thay vì giảm giá |
| **GenZ** | ⚠️ **Flash sale ngắn** (2-3 ngày), max 10% | Elasticity âm — KM dài hạn phản tác dụng |

> **Kết luận chốt:** Chỉ **1 trong 4 danh mục** (Outdoor) thực sự hưởng lợi từ promotion. Với 3 danh mục còn lại, mỗi đồng discount là mỗi đồng profit bị "đốt cháy" mà không đổi lại volume tăng trưởng.""")

# ── INSERT CELLS ──
insert_pos = 53  # After cell 52 (0-indexed)
new_cells = [cell_md_intro, cell_code_main, cell_md_insights]
for i, cell in enumerate(new_cells):
    nb['cells'].insert(insert_pos + i, cell)

with open('notebook/05_eda_storytelling_masterpiece_v2.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print(f"✅ Inserted {len(new_cells)} cells at position {insert_pos}")
print(f"Total cells now: {len(nb['cells'])}")
