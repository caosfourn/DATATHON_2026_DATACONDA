"""Phase 5: Operations & Fulfillment"""

def build(md, code):
    md("""---
# PHASE 5: Operations va Fulfillment (Ro ri loi nhuan)
**Muc tieu**: Tim loi trong khau van hanh anh huong den trai nghiem khach hang va loi nhuan.

> **Cau hoi kinh doanh**: Doanh nghiep dang mat tien o dau trong chuoi van hanh?""")

    # 5.1 Return Rate Analysis
    code("""# === 5.1 Return Rate Analysis ===
# Ty le hoan hang theo category
returns_full = returns.merge(products[['product_id', 'category', 'segment', 'size']], on='product_id')
returns_full = returns_full.merge(orders[['order_id', 'order_date', 'order_month']], on='order_id')

# Return rate theo category
cat_orders = order_items.merge(products[['product_id', 'category']], on='product_id')
cat_total = cat_orders.groupby('category')['quantity'].sum()
cat_returns = returns_full.groupby('category')['return_quantity'].sum()
return_rate_cat = (cat_returns / cat_total * 100).sort_values(ascending=False).dropna()

fig, axes = plt.subplots(1, 3, figsize=(18, 6))

# Return rate by category
colors_rr = [COLOR_NEG if v > return_rate_cat.mean() else COLOR_POS for v in return_rate_cat]
return_rate_cat.plot(kind='barh', ax=axes[0], color=colors_rr, edgecolor='white')
axes[0].axvline(return_rate_cat.mean(), color='black', linestyle='--', label=f'TB: {return_rate_cat.mean():.1f}%')
axes[0].set_title('Ty le hoan hang theo Category')
axes[0].set_xlabel('Return Rate (%)')
axes[0].legend()

# Return reason distribution
reason_dist = returns['return_reason'].value_counts()
reason_dist.plot(kind='barh', ax=axes[1], color=PALETTE, edgecolor='white')
axes[1].set_title('Phan bo ly do hoan hang')
axes[1].set_xlabel('So luot tra')

# Return rate trend
monthly_returns = returns_full.groupby('order_month')['return_quantity'].sum()
monthly_orders_qty = order_items.merge(orders[['order_id', 'order_month']], on='order_id').groupby('order_month')['quantity'].sum()
monthly_rr = (monthly_returns / monthly_orders_qty * 100).dropna()
axes[2].plot(monthly_rr.index, monthly_rr.values, color=COLOR_NEG, linewidth=2)
axes[2].fill_between(monthly_rr.index, monthly_rr.values, alpha=0.2, color=COLOR_NEG)
axes[2].set_title('Return Rate trend theo thang')
axes[2].set_ylabel('Return Rate (%)')
axes[2].tick_params(axis='x', rotation=45)

plt.suptitle('Return Rate Analysis - Phan tich ro ri do hoan hang', fontsize=16, fontweight='bold')
plt.tight_layout()
plt.show()

# Financial impact
total_refund = returns['refund_amount'].sum()
total_revenue = order_items['item_revenue'].sum()
leakage_rate = total_refund / total_revenue * 100
print(f"\\n=== Financial Impact cua Returns ===")
print(f"  Tong refund: {total_refund:,.0f} VND")
print(f"  Leakage rate: {leakage_rate:.2f}% tren tong doanh thu")\n""")

    # 5.2 Shipping Impact on Rating
    code("""# === 5.2 Tuong quan Thoi gian giao hang va Rating ===
# Merge: shipments -> orders -> reviews
ship_review = shipments.merge(orders[['order_id', 'order_date']], on='order_id')
ship_review['total_delivery_days'] = (ship_review['delivery_date'] - ship_review['order_date']).dt.days
ship_review = ship_review.merge(reviews[['order_id', 'rating']], on='order_id', how='inner')
ship_review = ship_review.dropna(subset=['total_delivery_days', 'rating'])

if len(ship_review) > 0:
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    # Boxplot: delivery time by rating
    ship_review.boxplot(column='total_delivery_days', by='rating', ax=axes[0])
    axes[0].set_title('Thoi gian giao hang theo Rating')
    axes[0].set_xlabel('Rating (1-5 sao)')
    axes[0].set_ylabel('Ngay giao hang')
    plt.sca(axes[0])
    plt.title('Thoi gian giao hang theo Rating')

    # Avg rating by delivery time bucket
    ship_review['delivery_bucket'] = pd.cut(ship_review['total_delivery_days'],
                                             bins=[0, 3, 5, 7, 10, 999],
                                             labels=['1-3', '4-5', '6-7', '8-10', '>10'])
    bucket_rating = ship_review.groupby('delivery_bucket')['rating'].mean()
    colors_bucket = [COLOR_POS if v >= 4 else (COLOR_NEG if v < 3 else '#f39c12') for v in bucket_rating]
    bucket_rating.plot(kind='bar', ax=axes[1], color=colors_bucket, edgecolor='white')
    axes[1].set_title('Rating trung binh theo nhom ngay giao')
    axes[1].set_xlabel('So ngay giao hang')
    axes[1].set_ylabel('Rating trung binh')
    axes[1].tick_params(axis='x', rotation=0)
    axes[1].axhline(ship_review['rating'].mean(), color='black', linestyle='--', alpha=0.5)

    # Scatter
    avg_by_days = ship_review.groupby('total_delivery_days')['rating'].mean()
    avg_by_days = avg_by_days[avg_by_days.index <= 20]  # clip outliers
    axes[2].scatter(avg_by_days.index, avg_by_days.values, color=COLOR_PRIMARY, alpha=0.7, s=50)
    z = np.polyfit(avg_by_days.index, avg_by_days.values, 1)
    p = np.poly1d(z)
    x_line = np.linspace(avg_by_days.index.min(), avg_by_days.index.max(), 100)
    axes[2].plot(x_line, p(x_line), '--', color=COLOR_NEG, linewidth=2)
    axes[2].set_title(f'Tuong quan: Ngay giao vs Rating (slope={z[0]:.3f})')
    axes[2].set_xlabel('Ngay giao hang')
    axes[2].set_ylabel('Rating trung binh')

    plt.suptitle('Shipping Impact on Customer Satisfaction', fontsize=16, fontweight='bold')
    fig.subplots_adjust(top=0.85)
    plt.tight_layout()
    plt.show()

    print(f"\\n[Insight] Moi ngay giao cham them, rating giam trung binh {abs(z[0]):.3f} sao")
    print(f"[Insight] Don giao <= 3 ngay: rating TB = {bucket_rating.iloc[0]:.2f}")
    late_rating = bucket_rating.iloc[-1] if len(bucket_rating) > 4 else bucket_rating.iloc[-1]
    print(f"[Insight] Don giao > 10 ngay: rating TB = {late_rating:.2f}")
else:
    print("Khong du du lieu de phan tich Shipping vs Rating")\n""")

    # 5.3 Geographic Analysis
    code("""# === 5.3 Geographic Analysis ===
# Merge orders voi geography (da merge o Phase 0)
geo_orders = orders.dropna(subset=['region']).copy()

# KPI theo Region
region_kpi = geo_orders.groupby('region').agg(
    order_count=('order_id', 'count'),
    total_revenue=('total_amount', 'sum'),
    avg_amount=('total_amount', 'mean')
)

# Shipping cost theo region
ship_geo = shipments.merge(orders[['order_id', 'region']], on='order_id')
ship_geo = ship_geo.dropna(subset=['region'])
ship_region = ship_geo.groupby('region').agg(
    avg_shipping=('shipping_fee', 'mean'),
    avg_delivery=('delivery_time', 'mean')
)

# Return rate theo region
ret_geo = returns.merge(orders[['order_id', 'region']], on='order_id').dropna(subset=['region'])
ret_region = ret_geo.groupby('region')['return_quantity'].sum()
order_qty_region = order_items.merge(orders[['order_id', 'region']], on='order_id').dropna(subset=['region']).groupby('region')['quantity'].sum()
rr_region = (ret_region / order_qty_region * 100).dropna()

# Combine
region_dashboard = region_kpi.join(ship_region).join(rr_region.rename('return_rate'))

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

region_dashboard['total_revenue'].plot(kind='bar', ax=axes[0, 0], color=PALETTE, edgecolor='white')
axes[0, 0].set_title('Tong doanh thu theo Vung')
axes[0, 0].yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x/1e9:.1f}B'))
axes[0, 0].tick_params(axis='x', rotation=0)

region_dashboard['avg_shipping'].plot(kind='bar', ax=axes[0, 1], color=PALETTE, edgecolor='white')
axes[0, 1].set_title('Phi van chuyen trung binh theo Vung')
axes[0, 1].tick_params(axis='x', rotation=0)

region_dashboard['avg_delivery'].plot(kind='bar', ax=axes[1, 0], color=PALETTE, edgecolor='white')
axes[1, 0].set_title('Thoi gian giao TB (ngay) theo Vung')
axes[1, 0].tick_params(axis='x', rotation=0)

if 'return_rate' in region_dashboard.columns:
    colors_rr = [COLOR_NEG if v > rr_region.mean() else COLOR_POS for v in region_dashboard['return_rate'].fillna(0)]
    region_dashboard['return_rate'].fillna(0).plot(kind='bar', ax=axes[1, 1], color=colors_rr, edgecolor='white')
    axes[1, 1].set_title('Return Rate (%) theo Vung')
    axes[1, 1].tick_params(axis='x', rotation=0)

plt.suptitle('Geographic Performance Dashboard', fontsize=16, fontweight='bold')
plt.tight_layout()
plt.show()

print("\\n=== Region Performance Table ===")
print(region_dashboard.round(2).to_string())\n""")

    # 5.4 Delivery Performance
    code("""# === 5.4 Delivery Performance Dashboard ===
ship_full = shipments.merge(orders[['order_id', 'order_date', 'region']], on='order_id')
ship_full['total_delivery'] = (ship_full['delivery_date'] - ship_full['order_date']).dt.days
ship_full['processing'] = (ship_full['ship_date'] - ship_full['order_date']).dt.days
ship_full['transit'] = (ship_full['delivery_date'] - ship_full['ship_date']).dt.days
ship_full = ship_full.dropna(subset=['total_delivery'])

fig, axes = plt.subplots(1, 3, figsize=(18, 5))

# Distribution
ship_full['total_delivery'].clip(upper=30).hist(bins=30, ax=axes[0], color=COLOR_PRIMARY, alpha=0.7, edgecolor='white')
median_del = ship_full['total_delivery'].median()
axes[0].axvline(median_del, color=COLOR_NEG, linestyle='--', label=f'Median: {median_del:.0f} ngay')
axes[0].set_title('Phan phoi thoi gian giao hang (ngay)')
axes[0].set_xlabel('Ngay')
axes[0].legend()

# Late delivery rate by region
late_threshold = ship_full['total_delivery'].quantile(0.75)
ship_full['is_late'] = ship_full['total_delivery'] > late_threshold
if 'region' in ship_full.columns:
    late_by_region = ship_full.dropna(subset=['region']).groupby('region')['is_late'].mean() * 100
    colors_late = [COLOR_NEG if v > late_by_region.mean() else COLOR_POS for v in late_by_region]
    late_by_region.plot(kind='bar', ax=axes[1], color=colors_late, edgecolor='white')
    axes[1].set_title(f'% Don giao tre (> {late_threshold:.0f} ngay) theo Vung')
    axes[1].set_ylabel('%')
    axes[1].tick_params(axis='x', rotation=0)

# Shipping fee vs delivery time
axes[2].scatter(ship_full['shipping_fee'], ship_full['total_delivery'].clip(upper=25),
                alpha=0.1, s=10, color=COLOR_PRIMARY)
axes[2].set_xlabel('Phi van chuyen (VND)')
axes[2].set_ylabel('Thoi gian giao (ngay)')
axes[2].set_title('Phi van chuyen vs Thoi gian giao')

plt.suptitle('Delivery Performance Dashboard', fontsize=16, fontweight='bold')
plt.tight_layout()
plt.show()

# Late delivery -> return rate
ship_returns = ship_full.merge(returns[['order_id']].drop_duplicates(), on='order_id', how='left', indicator=True)
ship_returns['has_return'] = ship_returns['_merge'] == 'both'
late_return_rate = ship_returns[ship_returns['is_late']]['has_return'].mean() * 100
ontime_return_rate = ship_returns[~ship_returns['is_late']]['has_return'].mean() * 100
print(f"\\n[Insight] Return rate - Don giao tre: {late_return_rate:.1f}%")
print(f"[Insight] Return rate - Don giao dung han: {ontime_return_rate:.1f}%")
print(f"[Insight] Don giao tre co return rate cao hon {late_return_rate/ontime_return_rate:.1f}x")\n""")

    # Phase 5 Insights
    md("""### Insights Phase 5: Operations

**Descriptive**: Return rate toan he thong la dang ke. "Wrong_size" la ly do pho bien nhat.
Thoi gian giao hang anh huong truc tiep den rating va return rate.
Cac vung (region) co hieu suat van hanh khac biet ro ret.

**Diagnostic**: Giao hang tre lam tang return rate gap doi. Vung co phi van chuyen
cao nhat chua chac la vung giao nhanh nhat -> van de toi uu logistics.
Rating giam tuyen tinh theo so ngay giao hang.

**Predictive**: Neu khong cai thien thoi gian giao hang, uoc tinh mat them doanh thu
do returns va rating thap dan den mat khach.

**Prescriptive**: (1) Cap nhat Virtual Size Guide de giam return "wrong_size".
(2) Toi uu kho hang o vung co delivery time cao nhat.
(3) Dat KPI giao hang < median hien tai.
(4) Mien phi van chuyen cho don gia tri cao de giam ty le huy.""")
