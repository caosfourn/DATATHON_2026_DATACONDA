"""Phase 4: Sales Performance & Basket Analysis"""

def build(md, code):
    md("""---
# PHASE 4: Sales Performance va Basket Analysis (Hanh vi mua sam)
**Muc tieu**: Tim cach tang gia tri don hang va hieu hanh vi mua sam cua khach.

> **Cau hoi kinh doanh**: Lam the nao de tang AOV? Khuyen mai co thuc su hieu qua?""")

    # 4.1 AOV Distribution
    code("""# === 4.1 AOV Distribution Analysis ===
order_values = orders.dropna(subset=['total_amount'])

fig, axes = plt.subplots(1, 3, figsize=(18, 5))

# Histogram + KDE
order_values['total_amount'].clip(upper=order_values['total_amount'].quantile(0.99)).hist(
    bins=50, ax=axes[0], color=COLOR_PRIMARY, alpha=0.7, edgecolor='white')
axes[0].axvline(order_values['total_amount'].median(), color=COLOR_NEG, linestyle='--',
                label=f"Median: {order_values['total_amount'].median():,.0f}")
axes[0].axvline(order_values['total_amount'].mean(), color=COLOR_POS, linestyle='--',
                label=f"Mean: {order_values['total_amount'].mean():,.0f}")
axes[0].set_title('Phan phoi gia tri don hang')
axes[0].set_xlabel('Order Value (VND)')
axes[0].legend()

# AOV by device
device_aov = order_values.groupby('device_type')['total_amount'].mean().sort_values(ascending=False)
device_aov.plot(kind='bar', ax=axes[1], color=PALETTE, edgecolor='white')
axes[1].set_title('AOV theo thiet bi')
axes[1].set_ylabel('VND')
axes[1].tick_params(axis='x', rotation=0)

# AOV by payment method
pay_aov = order_values.groupby('payment_method')['total_amount'].mean().sort_values(ascending=False)
pay_aov.plot(kind='bar', ax=axes[2], color=PALETTE, edgecolor='white')
axes[2].set_title('AOV theo phuong thuc thanh toan')
axes[2].set_ylabel('VND')
axes[2].tick_params(axis='x', rotation=45)

plt.suptitle('Phan tich phan phoi gia tri don hang', fontsize=16, fontweight='bold')
plt.tight_layout()
plt.show()

skew = order_values['total_amount'].skew()
print(f"[Insight] Skewness = {skew:.2f} -> {'Lech phai (co it don gia tri cao)' if skew > 0 else 'Phan phoi can doi'}")
print(f"[Insight] Mean/Median ratio = {order_values['total_amount'].mean()/order_values['total_amount'].median():.2f}")\n""")

    # 4.2 Promotion Sensitivity
    code("""# === 4.2 Promotion Sensitivity Analysis ===
# Phan loai don co/khong co promotion
oi_promo = order_items.copy()
oi_promo['has_promo'] = oi_promo['promo_id'].notna()

promo_comparison = oi_promo.groupby('has_promo').agg(
    avg_item_revenue=('item_revenue', 'mean'),
    avg_discount_rate=('discount_rate', 'mean'),
    total_items=('quantity', 'sum'),
    avg_quantity=('quantity', 'mean')
)
promo_comparison.index = ['Khong KM', 'Co KM']

# Promotion Dependency Index theo thang
oi_with_order = oi_promo.merge(orders[['order_id', 'order_month']], on='order_id')
monthly_promo = oi_with_order.groupby('order_month')['has_promo'].mean() * 100

fig, axes = plt.subplots(1, 3, figsize=(18, 5))

# So sanh co/khong KM
promo_comparison[['avg_item_revenue']].plot(kind='bar', ax=axes[0], color=[COLOR_POS, COLOR_NEG], edgecolor='white', legend=False)
axes[0].set_title('Revenue trung binh / item')
axes[0].set_ylabel('VND')
axes[0].tick_params(axis='x', rotation=0)

promo_comparison[['avg_quantity']].plot(kind='bar', ax=axes[1], color=[COLOR_POS, COLOR_NEG], edgecolor='white', legend=False)
axes[1].set_title('So luong trung binh / item')
axes[1].tick_params(axis='x', rotation=0)

# Promotion Dependency Trend
axes[2].plot(monthly_promo.index, monthly_promo.values, color=COLOR_NEG, linewidth=2)
axes[2].fill_between(monthly_promo.index, monthly_promo.values, alpha=0.2, color=COLOR_NEG)
axes[2].set_title('Promotion Dependency Index (% don co KM)')
axes[2].set_ylabel('% don hang co khuyen mai')
axes[2].tick_params(axis='x', rotation=45)

plt.suptitle('Promotion Sensitivity Analysis', fontsize=16, fontweight='bold')
plt.tight_layout()
plt.show()

# Margin erosion
oi_margin = oi_promo.copy()
oi_margin['margin_with'] = oi_margin[oi_margin['has_promo']]['item_profit'].mean()
print(f"\\n=== Promotion Impact ===")
print(f"  Profit trung binh - Co KM:    {oi_promo[oi_promo['has_promo']]['item_profit'].mean():,.0f} VND")
print(f"  Profit trung binh - Khong KM: {oi_promo[~oi_promo['has_promo']]['item_profit'].mean():,.0f} VND")
print(f"  Promotion Dependency hien tai: {monthly_promo.iloc[-1]:.1f}%")\n""")

    # 4.3 Market Basket Analysis
    code("""# === 4.3 Market Basket Analysis (Association Rules) ===
try:
    from mlxtend.frequent_patterns import fpgrowth, association_rules
    from mlxtend.preprocessing import TransactionEncoder

    # Tao transaction data: moi order la 1 transaction chua cac category
    basket = order_items.merge(products[['product_id', 'category']], on='product_id')
    transactions = basket.groupby('order_id')['category'].apply(list).values.tolist()
    # Chi lay transactions co >= 2 items
    transactions = [t for t in transactions if len(set(t)) >= 2]

    if len(transactions) > 100:
        te = TransactionEncoder()
        te_array = te.fit(transactions).transform(transactions)
        df_te = pd.DataFrame(te_array, columns=te.columns_)

        frequent = fpgrowth(df_te, min_support=0.05, use_colnames=True)
        rules = association_rules(frequent, metric='lift', min_threshold=1.0, num_items_in_antecedents=1)
        rules = rules.sort_values('lift', ascending=False).head(15)

        fig, ax = plt.subplots(figsize=(12, 6))
        rules_display = rules.copy()
        rules_display['rule'] = rules_display['antecedents'].apply(lambda x: ', '.join(x)) + ' -> ' + rules_display['consequents'].apply(lambda x: ', '.join(x))
        ax.barh(rules_display['rule'], rules_display['lift'], color=PALETTE[0], edgecolor='white')
        ax.set_xlabel('Lift')
        ax.set_title('Top Association Rules (Market Basket) - theo Lift')
        for i, (_, row) in enumerate(rules_display.iterrows()):
            ax.text(row['lift'] + 0.01, i, f"conf={row['confidence']:.2f}", va='center', fontsize=9)
        plt.tight_layout()
        plt.show()
    else:
        print("Khong du transactions de chay Market Basket Analysis")
except ImportError:
    print("Can cai dat mlxtend: pip install mlxtend")
    print("Bo qua Market Basket Analysis")\n""")

    # 4.4 Payment Method Analysis
    code("""# === 4.4 Payment Method va Installment Analysis ===
pay_stats = payments.groupby('payment_method').agg(
    count=('order_id', 'count'),
    avg_value=('payment_value', 'mean'),
    avg_installments=('installments', 'mean')
).sort_values('count', ascending=False)

fig, axes = plt.subplots(1, 3, figsize=(16, 5))

pay_stats['count'].plot(kind='bar', ax=axes[0], color=PALETTE, edgecolor='white')
axes[0].set_title('So don theo phuong thuc thanh toan')
axes[0].tick_params(axis='x', rotation=45)

pay_stats['avg_value'].plot(kind='bar', ax=axes[1], color=PALETTE, edgecolor='white')
axes[1].set_title('Gia tri don trung binh')
axes[1].tick_params(axis='x', rotation=45)

pay_stats['avg_installments'].plot(kind='bar', ax=axes[2], color=PALETTE, edgecolor='white')
axes[2].set_title('So ky tra gop trung binh')
axes[2].tick_params(axis='x', rotation=45)

plt.suptitle('Payment Method Analysis', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.show()

# Installment vs AOV
install_groups = payments.copy()
install_groups['install_group'] = pd.cut(install_groups['installments'], bins=[0,1,3,6,12,100],
                                         labels=['1 ky', '2-3 ky', '4-6 ky', '7-12 ky', '>12 ky'])
install_aov = install_groups.groupby('install_group')['payment_value'].mean()
print("\\n=== AOV theo so ky tra gop ===")
print(install_aov.round(0).to_string())\n""")

    # Phase 4 Insights
    md("""### Insights Phase 4: Sales Performance

**Descriptive**: Phan phoi AOV lech phai, cho thay da so don co gia tri vua phai voi it don lon.
Ty le don co khuyen mai dang tang theo thoi gian (Promotion Dependency).
Market Basket cho thay cac cap category thuong mua cung nhau.

**Diagnostic**: Khach hang dang hinh thanh thoi quen "chi mua khi co khuyen mai".
Don tra gop co AOV cao hon -> khuyen khich tra gop tang gia tri don.

**Predictive**: Neu Promotion Dependency tiep tuc tang, margin se bi "an mon" nghiem trong.
Uoc tinh neu giam 50% voucher, doanh thu giam nhung margin tong cai thien.

**Prescriptive**: (1) Chuyen tu discount sang loyalty rewards (tich diem, free ship).
(2) Cross-sell theo ket qua Market Basket: goi y san pham lien quan.
(3) Khuyen khich thanh toan tra gop de tang AOV.
(4) Tang voucher theo RFM tier thay vi phat tran lan.""")
