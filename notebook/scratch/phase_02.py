"""Phase 2: Acquisition & Channel Performance"""

def build(md, code):
    md("""---
# PHASE 2: Acquisition va Channel Performance (Dau vao pheu)
**Muc tieu**: Danh gia hieu qua cac kenh Marketing va chat luong khach hang.

> **Cau hoi kinh doanh**: Tien do vao kenh nao la hieu qua nhat? Khach hang den tu dau?""")

    # 2.1 Channel Performance
    code("""# === 2.1 Channel Performance Scorecard ===
# Acquisition channel tu customers
channel_stats = customers.merge(
    orders.groupby('customer_id').agg(
        order_count=('order_id', 'count'),
        total_spent=('total_amount', 'sum')
    ), on='customer_id', how='inner'
)
channel_stats['AOV'] = channel_stats['total_spent'] / channel_stats['order_count']

channel_summary = channel_stats.groupby('acquisition_channel').agg(
    customer_count=('customer_id', 'count'),
    avg_orders=('order_count', 'mean'),
    avg_spent=('total_spent', 'mean'),
    avg_aov=('AOV', 'mean')
).sort_values('avg_spent', ascending=False)

fig, axes = plt.subplots(1, 3, figsize=(18, 6))

# So luong khach
channel_summary['customer_count'].plot(kind='barh', ax=axes[0], color=PALETTE, edgecolor='white')
axes[0].set_title('So luong khach hang theo kenh')
axes[0].set_xlabel('So khach hang')

# Trung binh chi tieu
channel_summary['avg_spent'].plot(kind='barh', ax=axes[1], color=PALETTE, edgecolor='white')
axes[1].set_title('Chi tieu trung binh / khach')
axes[1].set_xlabel('VND')

# AOV
channel_summary['avg_aov'].plot(kind='barh', ax=axes[2], color=PALETTE, edgecolor='white')
axes[2].set_title('AOV trung binh theo kenh')
axes[2].set_xlabel('VND')

plt.suptitle('Channel Performance Scorecard', fontsize=16, fontweight='bold')
plt.tight_layout()
plt.show()

print("\\n=== Channel Performance Table ===")
print(channel_summary.round(0).to_string())\n""")

    # 2.2 Web Traffic & Conversion
    code("""# === 2.2 Web Traffic va Conversion Analysis ===
# Traffic theo source
traffic_by_source = web_traffic.groupby('traffic_source').agg(
    total_sessions=('sessions', 'sum'),
    avg_bounce=('bounce_rate', 'mean'),
    avg_duration=('avg_session_duration_sec', 'mean'),
    total_visitors=('unique_visitors', 'sum')
).sort_values('total_sessions', ascending=False)

fig, axes = plt.subplots(1, 3, figsize=(18, 6))

# Sessions by source
traffic_by_source['total_sessions'].plot(kind='barh', ax=axes[0], color=PALETTE, edgecolor='white')
axes[0].set_title('Tong Sessions theo nguon')
axes[0].set_xlabel('Sessions')

# Bounce rate
colors_bounce = [COLOR_NEG if v > traffic_by_source['avg_bounce'].mean() else COLOR_POS
                 for v in traffic_by_source['avg_bounce']]
traffic_by_source['avg_bounce'].plot(kind='barh', ax=axes[1], color=colors_bounce, edgecolor='white')
axes[1].axvline(traffic_by_source['avg_bounce'].mean(), color='black', linestyle='--', label='TB')
axes[1].set_title('Bounce Rate trung binh theo nguon')
axes[1].set_xlabel('Bounce Rate')
axes[1].legend()

# Avg duration
traffic_by_source['avg_duration'].plot(kind='barh', ax=axes[2], color=PALETTE, edgecolor='white')
axes[2].set_title('Thoi gian phien trung binh (giay)')
axes[2].set_xlabel('Giay')

plt.suptitle('Web Traffic Analysis theo Traffic Source', fontsize=16, fontweight='bold')
plt.tight_layout()
plt.show()

# Traffic trend
monthly_traffic = web_traffic.groupby(web_traffic['date'].dt.to_period('M')).agg(
    sessions=('sessions', 'sum'), bounce=('bounce_rate', 'mean'))
monthly_traffic.index = monthly_traffic.index.to_timestamp()

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 8), sharex=True)
ax1.plot(monthly_traffic.index, monthly_traffic['sessions'], color=COLOR_PRIMARY, linewidth=1.5)
ax1.fill_between(monthly_traffic.index, monthly_traffic['sessions'], alpha=0.2, color=COLOR_PRIMARY)
ax1.set_title('Tong Sessions theo thang')
ax1.set_ylabel('Sessions')

ax2.plot(monthly_traffic.index, monthly_traffic['bounce'], color=COLOR_NEG, linewidth=1.5)
ax2.set_title('Bounce Rate trung binh theo thang')
ax2.set_ylabel('Bounce Rate')

plt.tight_layout()
plt.show()\n""")

    # 2.3 Device Type + Channel Quality Quadrant
    code("""# === 2.3 Device Type Analysis ===
device_stats = orders.groupby('device_type').agg(
    order_count=('order_id', 'count'),
    avg_amount=('total_amount', 'mean')
).sort_values('order_count', ascending=False)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
device_stats['order_count'].plot(kind='bar', ax=ax1, color=PALETTE, edgecolor='white')
ax1.set_title('So don hang theo thiet bi')
ax1.set_ylabel('So don')
ax1.tick_params(axis='x', rotation=0)

device_stats['avg_amount'].plot(kind='bar', ax=ax2, color=PALETTE, edgecolor='white')
ax2.set_title('AOV theo thiet bi')
ax2.set_ylabel('VND')
ax2.tick_params(axis='x', rotation=0)

plt.suptitle('Phan tich theo thiet bi dat hang', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.show()

# === 2.4 Channel Quality Quadrant ===
# Order source analysis
source_stats = orders.groupby('order_source').agg(
    order_count=('order_id', 'count'),
    avg_amount=('total_amount', 'mean'),
    total_rev=('total_amount', 'sum')
).dropna()
source_stats['share'] = source_stats['order_count'] / source_stats['order_count'].sum() * 100

fig, ax = plt.subplots(figsize=(12, 8))
scatter = ax.scatter(source_stats['order_count'], source_stats['avg_amount'],
                     s=source_stats['share'] * 50, alpha=0.7, color=PALETTE[:len(source_stats)],
                     edgecolors='black', linewidth=1)

for name, row in source_stats.iterrows():
    ax.annotate(name, (row['order_count'], row['avg_amount']),
                fontsize=10, ha='center', va='bottom', fontweight='bold')

ax.axhline(source_stats['avg_amount'].mean(), color=COLOR_NEU, linestyle='--', alpha=0.5)
ax.axvline(source_stats['order_count'].mean(), color=COLOR_NEU, linestyle='--', alpha=0.5)
ax.set_xlabel('So don hang (Volume)')
ax.set_ylabel('AOV (Gia tri trung binh)')
ax.set_title('Channel Quality Quadrant: Volume vs AOV theo kenh (size = market share)')

# Quadrant labels
xlim = ax.get_xlim()
ylim = ax.get_ylim()
ax.text(xlim[1]*0.85, ylim[1]*0.95, 'STARS', fontsize=12, ha='center', alpha=0.3, fontweight='bold', color=COLOR_POS)
ax.text(xlim[0]*1.1 + (xlim[1]-xlim[0])*0.15, ylim[1]*0.95, 'NICHE', fontsize=12, ha='center', alpha=0.3, fontweight='bold', color=COLOR_SECONDARY)
ax.text(xlim[1]*0.85, ylim[0]+( ylim[1]-ylim[0])*0.05, 'VOLUME', fontsize=12, ha='center', alpha=0.3, fontweight='bold', color='#f39c12')
ax.text(xlim[0]*1.1 + (xlim[1]-xlim[0])*0.15, ylim[0]+(ylim[1]-ylim[0])*0.05, 'WEAK', fontsize=12, ha='center', alpha=0.3, fontweight='bold', color=COLOR_NEG)

plt.tight_layout()
plt.show()\n""")

    # Phase 2 Insights
    md("""### Insights Phase 2: Acquisition

**Descriptive**: Organic Search mang lai luong khach hang deu dan. Bounce rate va thoi gian
phien truy cap khac biet ro ret giua cac kenh.

**Diagnostic**: Kenh co bounce rate cao cho thay chat luong traffic kem, co the do
landing page khong phu hop hoac target audience sai. Device type anh huong den AOV.

**Predictive**: Neu tiep tuc do tien vao kenh bounce rate cao, ty le chuyen doi se
tiep tuc thap, lang phi ngan sach marketing.

**Prescriptive**: (1) Reallocate budget tu kenh bounce rate cao sang kenh AOV cao.
(2) Toi uu landing page cho mobile (neu AOV mobile thap hon desktop).
(3) Tap trung vao kenh "Stars" (high volume + high AOV).""")
