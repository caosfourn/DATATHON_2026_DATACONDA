"""Phase 6: Retention & CLV"""

def build(md, code):
    md("""---
# PHASE 6: Retention va Customer Lifetime Value (Tai san dai han)
**Muc tieu**: Chien luoc giu chan khach hang va toi uu gia tri vong doi.

> **Cau hoi kinh doanh**: Khach hang o lai bao lau? Nhom nao dang mat dan?""")

    # 6.1 Cohort Retention
    code("""# === 6.1 Cohort Retention Analysis ===
cohort_data = orders[['customer_id', 'order_date', 'total_amount']].dropna().copy()
cohort_data = cohort_data.merge(customers[['customer_id', 'true_signup_date']], on='customer_id')

# Cohort month = thang mua dau tien
cohort_data['cohort_month'] = cohort_data.groupby('customer_id')['order_date'].transform('min').dt.to_period('M')
cohort_data['order_period'] = cohort_data['order_date'].dt.to_period('M')
cohort_data['period_number'] = (cohort_data['order_period'] - cohort_data['cohort_month']).apply(lambda x: x.n)

# Retention matrix
cohort_pivot = cohort_data.groupby(['cohort_month', 'period_number'])['customer_id'].nunique().reset_index()
cohort_pivot.columns = ['cohort_month', 'period_number', 'customers']
cohort_sizes = cohort_pivot[cohort_pivot['period_number'] == 0][['cohort_month', 'customers']].rename(columns={'customers': 'cohort_size'})
cohort_pivot = cohort_pivot.merge(cohort_sizes, on='cohort_month')
cohort_pivot['retention'] = cohort_pivot['customers'] / cohort_pivot['cohort_size'] * 100

# Heatmap - lay 12 cohorts gan nhat va 12 periods
cohort_pivot['cohort_month'] = cohort_pivot['cohort_month'].astype(str)
recent_cohorts = sorted(cohort_pivot['cohort_month'].unique())[-18:]
retention_matrix = cohort_pivot[
    (cohort_pivot['cohort_month'].isin(recent_cohorts)) &
    (cohort_pivot['period_number'] <= 12)
].pivot_table(index='cohort_month', columns='period_number', values='retention')

fig, ax = plt.subplots(figsize=(16, 10))
sns.heatmap(retention_matrix, annot=True, fmt='.0f', cmap='YlGnBu', ax=ax,
            linewidths=0.5, vmin=0, vmax=100)
ax.set_title('Cohort Retention Heatmap (% khach quay lai)')
ax.set_xlabel('Thang sau mua dau tien')
ax.set_ylabel('Cohort (thang gia nhap)')
plt.tight_layout()
plt.show()

# Tim "diem gay"
avg_retention = retention_matrix.mean()
print("\\n=== Retention Rate trung binh theo thang ===")
for period in range(min(7, len(avg_retention))):
    if period in avg_retention.index:
        drop = avg_retention[0] - avg_retention[period] if period > 0 else 0
        print(f"  Thang {period}: {avg_retention[period]:.1f}% (giam {drop:.1f}pp tu thang 0)")

# Tim diem gay lon nhat
if len(avg_retention) > 2:
    drops = avg_retention.diff().dropna()
    worst_drop_period = drops.idxmin()
    print(f"\\n[Insight] Diem gay lon nhat: Thang {worst_drop_period} (mat {abs(drops.min()):.1f}pp)")\n""")

    # 6.2 RFM Segmentation
    code("""# === 6.2 RFM Segmentation ===
snapshot_date = orders['order_date'].max() + timedelta(days=1)

rfm = orders_delivered.groupby('customer_id').agg(
    Recency=('order_date', lambda x: (snapshot_date - x.max()).days),
    Frequency=('order_id', 'count'),
    Monetary=('total_amount', 'sum')
).dropna()

# RFM scoring
rfm['R_score'] = pd.qcut(rfm['Recency'], 4, labels=[4, 3, 2, 1])
rfm['F_score'] = pd.qcut(rfm['Frequency'].rank(method='first'), 4, labels=[1, 2, 3, 4])
rfm['M_score'] = pd.qcut(rfm['Monetary'], 4, labels=[1, 2, 3, 4])
rfm['RFM_score'] = rfm['R_score'].astype(int) + rfm['F_score'].astype(int) + rfm['M_score'].astype(int)

# Segment labels
def rfm_segment(row):
    r, f, m = int(row['R_score']), int(row['F_score']), int(row['M_score'])
    if r >= 4 and f >= 4:
        return 'Champions'
    elif r >= 3 and f >= 3:
        return 'Loyal'
    elif r >= 3 and f <= 2:
        return 'Potential'
    elif r == 2 and f >= 2:
        return 'At Risk'
    elif r <= 1 and f >= 2:
        return 'Hibernating'
    elif r <= 1 and f <= 1:
        return 'Lost'
    else:
        return 'Others'

rfm['Segment'] = rfm.apply(rfm_segment, axis=1)

# Segment summary
seg_summary = rfm.groupby('Segment').agg(
    Count=('Recency', 'count'),
    Avg_Recency=('Recency', 'mean'),
    Avg_Frequency=('Frequency', 'mean'),
    Avg_Monetary=('Monetary', 'mean'),
    Total_Revenue=('Monetary', 'sum')
).sort_values('Total_Revenue', ascending=False)
seg_summary['Revenue_Share'] = seg_summary['Total_Revenue'] / seg_summary['Total_Revenue'].sum() * 100

fig, axes = plt.subplots(1, 3, figsize=(18, 6))

# Customer count
seg_summary['Count'].plot(kind='barh', ax=axes[0], color=PALETTE, edgecolor='white')
axes[0].set_title('So khach hang theo Segment')

# Revenue share
seg_summary['Revenue_Share'].plot(kind='barh', ax=axes[1], color=PALETTE, edgecolor='white')
axes[1].set_title('% Doanh thu theo Segment')
axes[1].set_xlabel('%')

# Avg Monetary
seg_summary['Avg_Monetary'].plot(kind='barh', ax=axes[2], color=PALETTE, edgecolor='white')
axes[2].set_title('Chi tieu trung binh theo Segment')
axes[2].set_xlabel('VND')

plt.suptitle('RFM Customer Segmentation', fontsize=16, fontweight='bold')
plt.tight_layout()
plt.show()

print("\\n=== RFM Segment Summary ===")
print(seg_summary.round(0).to_string())

# Add return rate by segment
orders_seg = orders.merge(rfm[['Segment']], left_on='customer_id', right_index=True, how='inner')
ret_seg = returns.merge(orders_seg[['order_id', 'Segment']], on='order_id')
ret_by_seg = ret_seg.groupby('Segment')['return_quantity'].sum()
ord_by_seg = order_items.merge(orders_seg[['order_id', 'Segment']], on='order_id').groupby('Segment')['quantity'].sum()
rr_seg = (ret_by_seg / ord_by_seg * 100).dropna()
print("\\n=== Return Rate theo Segment ===")
print(rr_seg.round(1).to_string())\n""")

    # 6.3 Repeat Purchase Rate + CLV
    code("""# === 6.3 Repeat Purchase Rate (trong 90 ngay) ===
cust_orders = orders_delivered.sort_values('order_date').groupby('customer_id')['order_date'].apply(list)

repeat_90 = 0
total_first = 0
for cid, dates in cust_orders.items():
    if len(dates) >= 1:
        total_first += 1
        if len(dates) >= 2:
            days_to_second = (dates[1] - dates[0]).days
            if days_to_second <= 90:
                repeat_90 += 1

repeat_rate_90 = repeat_90 / total_first * 100 if total_first > 0 else 0
print(f"=== Repeat Purchase Rate ===")
print(f"  Tong khach hang co it nhat 1 don: {total_first:,}")
print(f"  Khach quay lai trong 90 ngay: {repeat_90:,}")
print(f"  Repeat Rate 90 ngay: {repeat_rate_90:.1f}%")

# Repeat rate theo acquisition channel
cust_channel = customers[['customer_id', 'acquisition_channel']].dropna()
cust_ord_channel = orders_delivered.merge(cust_channel, on='customer_id')
repeat_by_channel = {}
for ch in cust_ord_channel['acquisition_channel'].unique():
    ch_data = cust_ord_channel[cust_ord_channel['acquisition_channel'] == ch].sort_values('order_date').groupby('customer_id')['order_date'].apply(list)
    total = 0
    rep = 0
    for dates in ch_data.values:
        total += 1
        if len(dates) >= 2 and (dates[1] - dates[0]).days <= 90:
            rep += 1
    repeat_by_channel[ch] = rep / total * 100 if total > 0 else 0

repeat_ch = pd.Series(repeat_by_channel).sort_values(ascending=False)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

ax1.bar(['Repeat (<=90d)', 'Khong Repeat'], [repeat_rate_90, 100 - repeat_rate_90],
        color=[COLOR_POS, COLOR_NEG], edgecolor='white')
ax1.set_title(f'Repeat Purchase Rate trong 90 ngay: {repeat_rate_90:.1f}%')
ax1.set_ylabel('%')

repeat_ch.plot(kind='barh', ax=ax2, color=PALETTE, edgecolor='white')
ax2.set_title('Repeat Rate 90 ngay theo Kenh')
ax2.set_xlabel('Repeat Rate (%)')

plt.suptitle('Repeat Purchase Analysis', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.show()

# === Simple CLV ===
print("\\n=== Customer Lifetime Value (CLV) theo Segment ===")
clv_data = rfm.copy()
# CLV = AOV x Frequency x estimated lifespan (simplified)
clv_data['AOV'] = clv_data['Monetary'] / clv_data['Frequency']
clv_data['est_annual_freq'] = clv_data['Frequency'] * 365 / (snapshot_date - orders['order_date'].min()).days
clv_data['CLV_1yr'] = clv_data['AOV'] * clv_data['est_annual_freq']

clv_by_seg = clv_data.groupby('Segment').agg(
    Avg_CLV=('CLV_1yr', 'mean'),
    Total_CLV=('CLV_1yr', 'sum'),
    Count=('CLV_1yr', 'count')
).sort_values('Avg_CLV', ascending=False)
clv_by_seg['Revenue_at_Risk'] = clv_by_seg.loc[clv_by_seg.index.isin(['At Risk', 'Hibernating', 'Lost']), 'Total_CLV']

print(clv_by_seg[['Count', 'Avg_CLV', 'Total_CLV']].round(0).to_string())

at_risk_clv = clv_by_seg.loc[clv_by_seg.index.isin(['At Risk', 'Hibernating', 'Lost']), 'Total_CLV'].sum()
print(f"\\n[Insight] CLV tong cong cua nhom At Risk + Hibernating + Lost: {at_risk_clv:,.0f} VND")
print(f"[Insight] Day la so tien co nguy co mat neu khong co chien luoc win-back")\n""")

    # Phase 6 Insights
    md("""### Insights Phase 6: Retention

**Descriptive**: Retention Rate roi manh sau thang dau tien. Repeat Purchase Rate 90 ngay
cho thay ty le khach quay lai tuong doi thap. Champions tao ra phan lon doanh thu.

**Diagnostic**: Khach hang "deal hunter" mua lan 1 khi co KM roi bien mat.
Kenh acquisition co anh huong truc tiep den chat luong retention.

**Predictive**: CLV nhom Champions rat cao, nhom At Risk/Lost neu churn se mat
mot luong doanh thu dang ke. Neu khong can thiep, nhom "At Risk" se chuyen sang "Lost".

**Prescriptive**: (1) Loyalty program cho Champions (exclusive access, early sale).
(2) Win-back campaign cho At Risk (email ca nhan hoa + voucher).
(3) Giam chi tieu acquisition kenh co repeat rate thap.
(4) Onboarding flow cho khach moi: push mua lan 2 trong 30 ngay dau.""")
