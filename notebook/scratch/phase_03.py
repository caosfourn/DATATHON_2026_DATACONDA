"""Phase 3: Product Portfolio & Fashion Assortment"""

def build(md, code):
    md("""---
# PHASE 3: Product Portfolio va Fashion Assortment (Linh hon san pham)
**Muc tieu**: Toi uu hoa danh muc hang hoa, phat hien co hoi va rui ro theo dac thu nganh thoi trang.

> **Cau hoi kinh doanh**: San pham nao tao gia tri? Size/Color nao dang mat doanh thu do het hang?""")

    # 3.1 ABC Pareto Analysis
    code("""# === 3.1 ABC Analysis (Pareto) - Phan loai san pham ===
product_revenue = order_items.groupby('product_id')['item_revenue'].sum().sort_values(ascending=False).reset_index()
product_revenue.columns = ['product_id', 'total_revenue']
product_revenue = product_revenue.merge(products[['product_id', 'product_name', 'category', 'segment']], on='product_id')
product_revenue['cumulative_pct'] = product_revenue['total_revenue'].cumsum() / product_revenue['total_revenue'].sum() * 100
product_revenue['rank'] = range(1, len(product_revenue) + 1)
product_revenue['rank_pct'] = product_revenue['rank'] / len(product_revenue) * 100

# Phan loai ABC
product_revenue['ABC_class'] = 'C'
product_revenue.loc[product_revenue['cumulative_pct'] <= 80, 'ABC_class'] = 'A'
product_revenue.loc[(product_revenue['cumulative_pct'] > 80) & (product_revenue['cumulative_pct'] <= 95), 'ABC_class'] = 'B'

fig, ax1 = plt.subplots(figsize=(14, 7))

# Bar chart revenue
colors_abc = {'A': COLOR_POS, 'B': '#f39c12', 'C': COLOR_NEG}
bar_colors = [colors_abc[c] for c in product_revenue['ABC_class']]
ax1.bar(product_revenue['rank_pct'], product_revenue['total_revenue'], width=0.3, color=bar_colors, alpha=0.6)
ax1.set_xlabel('% San pham (xep theo doanh thu giam dan)')
ax1.set_ylabel('Doanh thu (VND)', color=COLOR_PRIMARY)
ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x/1e6:.0f}M'))

# Cumulative line
ax2 = ax1.twinx()
ax2.plot(product_revenue['rank_pct'], product_revenue['cumulative_pct'], color=COLOR_NEG, linewidth=2.5)
ax2.axhline(80, color=COLOR_NEG, linestyle='--', alpha=0.5, label='80% Revenue')
ax2.axhline(95, color='#f39c12', linestyle='--', alpha=0.5, label='95% Revenue')
ax2.set_ylabel('Cumulative Revenue (%)', color=COLOR_NEG)
ax2.legend(loc='center right')

ax1.set_title('ABC Pareto Analysis: Phan loai san pham theo dong gop doanh thu')
plt.tight_layout()
plt.show()

# Summary
abc_summary = product_revenue.groupby('ABC_class').agg(
    product_count=('product_id', 'count'),
    total_rev=('total_revenue', 'sum')
)
abc_summary['pct_products'] = abc_summary['product_count'] / abc_summary['product_count'].sum() * 100
abc_summary['pct_revenue'] = abc_summary['total_rev'] / abc_summary['total_rev'].sum() * 100
print("\\n=== ABC Classification Summary ===")
print(abc_summary[['product_count', 'pct_products', 'pct_revenue']].round(1).to_string())

# ABC x Category cross-tab
abc_cat = product_revenue.groupby(['category', 'ABC_class']).size().unstack(fill_value=0)
print("\\n=== So san pham A/B/C theo Category ===")
print(abc_cat.to_string())\n""")

    # 3.2 Size & Color Gap
    code("""# === 3.2 Size va Color Gap Analysis ===
# Dung inventory.csv de phan tich sell-through rate theo size/color
inv_product = inventory.merge(products[['product_id', 'size', 'color', 'category']], on='product_id')

# Heatmap: Size vs Color - Sell Through Rate trung binh
size_color_str = inv_product.groupby(['size', 'color'])['sell_through_rate'].mean().unstack()

fig, axes = plt.subplots(1, 2, figsize=(18, 6))

# Sell-through rate
sns.heatmap(size_color_str, annot=True, fmt='.2f', cmap='RdYlGn', ax=axes[0],
            linewidths=0.5, vmin=0, vmax=1)
axes[0].set_title('Sell-Through Rate trung binh: Size vs Color\\n(Cao = ban tot, Thap = ton kho)')

# Stockout frequency
size_color_stockout = inv_product.groupby(['size', 'color'])['stockout_flag'].mean().unstack()
sns.heatmap(size_color_stockout, annot=True, fmt='.2f', cmap='YlOrRd', ax=axes[1],
            linewidths=0.5)
axes[1].set_title('Ty le Stockout: Size vs Color\\n(Cao = thuong xuyen het hang)')

plt.suptitle('Size va Color Gap Analysis - Dac thu nganh thoi trang', fontsize=16, fontweight='bold')
plt.tight_layout()
plt.show()

# Cross-reference voi returns - wrong_size
wrong_size_returns = returns[returns['return_reason'].str.contains('size', case=False, na=False)]
if len(wrong_size_returns) > 0:
    ws_products = wrong_size_returns.merge(products[['product_id', 'size', 'category']], on='product_id')
    ws_by_size = ws_products.groupby('size')['return_quantity'].sum().sort_values(ascending=False)
    print("\\n=== Returns do 'wrong_size' theo Size ===")
    print(ws_by_size.to_string())
else:
    print("Khong tim thay returns lien quan den 'size'")\n""")

    # 3.3 Category Mix
    code("""# === 3.3 Category Mix va Margin Analysis ===
cat_analysis = order_items.merge(products[['product_id', 'category', 'segment', 'cogs']], on='product_id')
cat_analysis['margin'] = (cat_analysis['unit_price'] - cat_analysis['cogs']) / cat_analysis['unit_price'] * 100

cat_summary = cat_analysis.groupby('category').agg(
    total_revenue=('item_revenue', 'sum'),
    total_quantity=('quantity', 'sum'),
    avg_margin=('margin', 'mean'),
    product_count=('product_id', 'nunique')
).sort_values('total_revenue', ascending=False)
cat_summary['revenue_share'] = cat_summary['total_revenue'] / cat_summary['total_revenue'].sum() * 100

fig, axes = plt.subplots(1, 2, figsize=(16, 7))

# Revenue share pie
axes[0].pie(cat_summary['revenue_share'], labels=cat_summary.index,
            autopct='%1.1f%%', colors=PALETTE[:len(cat_summary)], startangle=90)
axes[0].set_title('Co cau doanh thu theo Category')

# Scatter: Revenue vs Margin
scatter = axes[1].scatter(cat_summary['revenue_share'], cat_summary['avg_margin'],
                          s=cat_summary['total_quantity']/cat_summary['total_quantity'].max()*500,
                          c=PALETTE[:len(cat_summary)], alpha=0.7, edgecolors='black')
for name, row in cat_summary.iterrows():
    axes[1].annotate(name, (row['revenue_share'], row['avg_margin']),
                     fontsize=9, ha='center', va='bottom', fontweight='bold')
axes[1].axhline(cat_summary['avg_margin'].mean(), color=COLOR_NEU, linestyle='--', alpha=0.5)
axes[1].axvline(cat_summary['revenue_share'].mean(), color=COLOR_NEU, linestyle='--', alpha=0.5)
axes[1].set_xlabel('Revenue Share (%)')
axes[1].set_ylabel('Gross Margin (%)')
axes[1].set_title('Revenue Share vs Margin theo Category\\n(size = so luong ban)')

plt.suptitle('Category Mix va Margin Analysis', fontsize=16, fontweight='bold')
plt.tight_layout()
plt.show()

print("\\n=== Category Performance Table ===")
print(cat_summary.round(1).to_string())\n""")

    # Phase 3 Insights
    md("""### Insights Phase 3: Product Portfolio

**Descriptive**: Phan tich Pareto cho thay mot so luong nho san pham tao ra phan lon doanh thu.
Heatmap Size/Color boc lo cac "gap" trong danh muc: mot so size ban chay nhung hay het hang,
mot so color ton kho nhieu.

**Diagnostic**: Size pho bien (M, L) co sell-through rate cao nhung stockout thuong xuyen
-> van de du bao va nhap hang. Returns do "wrong_size" tap trung o mot so category cu the.

**Predictive**: Neu khong dieu chinh, stockout o size ban chay se tiep tuc lam mat
doanh thu uoc tinh theo ty le fill_rate hien tai. San pham nhom C co nguy co tro thanh
hang ton kho chet.

**Prescriptive**: (1) Tang ty le dat hang size M/L them 20-30%.
(2) Giam san xuat size/color co sell-through rate thap.
(3) Trien khai Virtual Size Guide de giam return rate do "wrong_size".
(4) Loai bo san pham nhom C co overstock_flag keo dai > 3 thang.""")
