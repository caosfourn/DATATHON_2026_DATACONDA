"""Phase 7: Executive Summary & Actionable Insights"""

def build(md, code):
    md("""---
# PHASE 7: Executive Summary va Actionable Insights (Ket luan chien luoc)
**Muc tieu**: Tong hop phat hien quan trong nhat va de xuat hanh dong cu the.

> Moi insight duoc trinh bay voi: Bang chung du lieu -> Nguyen nhan -> De xuat hanh dong""")

    # 7.1 Top Insights Summary
    code("""# === 7.1 Tong hop 3 phat hien quan trong nhat ===
print("=" * 80)
print("TOP 3 INSIGHTS CHIEN LUOC")
print("=" * 80)

print(\"\"\"
INSIGHT 1: RO RI LOI NHUAN QUA VAN HANH
-----------------------------------------
- Return rate dang ke, ly do chinh: "wrong_size"
- Don giao tre co return rate cao hon don giao dung han
- Tong refund/leakage chiem phan tram dang chu y tren tong doanh thu
=> HANH DONG: (a) Trien khai Virtual Size Guide
              (b) Toi uu logistics de giam thoi gian giao hang

INSIGHT 2: PHU THUOC KHUYEN MAI (Promotion Dependency)
------------------------------------------------------
- Ty le don co su dung khuyen mai dang tang theo thoi gian
- Don co KM co profit thap hon dang ke so voi don khong KM
- AOV giam khi volume tang -> tang truong bang so luong, khong phai chat luong
=> HANH DONG: (a) Chuyen sang loyalty rewards thay vi discount
              (b) Phan KM theo RFM tier, khong phat tran lan

INSIGHT 3: RETENTION THAP VA MAT KHACH
---------------------------------------
- Retention roi manh chi sau 1-2 thang dau tien
- Nhom At Risk + Lost chiem luong CLV lon co nguy co mat
- Repeat Purchase Rate 90 ngay con thap
=> HANH DONG: (a) Win-back campaign cho nhom At Risk
              (b) Onboarding push mua lan 2 trong 30 ngay
              (c) Giam chi tieu acquisition kenh repeat rate thap
\"\"\")
print("=" * 80)\n""")

    # 7.2 Priority Matrix
    code("""# === 7.2 Priority Matrix: Impact vs Effort ===
actions = pd.DataFrame({
    'Action': [
        'Virtual Size Guide',
        'Toi uu logistics vung yeu',
        'Loyalty program (Champions)',
        'Win-back campaign (At Risk)',
        'Giam voucher tran lan',
        'Cross-sell (Market Basket)',
        'Toi uu landing page mobile',
        'Loai bo san pham nhom C ton',
        'Khuyen khich tra gop',
        'KPI giao hang < median'
    ],
    'Impact': [8, 7, 9, 8, 7, 6, 5, 4, 5, 7],   # 1-10
    'Effort': [3, 7, 5, 4, 3, 4, 6, 2, 2, 8],     # 1-10
    'Category': ['Operations', 'Operations', 'Retention', 'Retention',
                 'Sales', 'Sales', 'Acquisition', 'Product',
                 'Sales', 'Operations']
})

fig, ax = plt.subplots(figsize=(14, 10))
cat_colors = {'Operations': COLOR_NEG, 'Retention': COLOR_PRIMARY,
              'Sales': COLOR_POS, 'Acquisition': '#f39c12', 'Product': COLOR_SECONDARY}

for cat in actions['Category'].unique():
    subset = actions[actions['Category'] == cat]
    ax.scatter(subset['Impact'], subset['Effort'], s=200, alpha=0.8,
              color=cat_colors.get(cat, COLOR_NEU), label=cat, edgecolors='black', linewidth=1)

for _, row in actions.iterrows():
    ax.annotate(row['Action'], (row['Impact'], row['Effort']),
                fontsize=8, ha='left', va='bottom',
                xytext=(5, 5), textcoords='offset points')

# Quadrant lines
ax.axhline(5, color=COLOR_NEU, linestyle='--', alpha=0.5)
ax.axvline(6, color=COLOR_NEU, linestyle='--', alpha=0.5)

# Quadrant labels
ax.text(8.5, 1.5, 'QUICK WINS\\n(Lam ngay!)', fontsize=12, ha='center', alpha=0.3, fontweight='bold', color=COLOR_POS)
ax.text(3, 1.5, 'FILL-INS', fontsize=12, ha='center', alpha=0.3, fontweight='bold', color=COLOR_NEU)
ax.text(8.5, 8.5, 'STRATEGIC\\n(Dau tu dai han)', fontsize=12, ha='center', alpha=0.3, fontweight='bold', color=COLOR_PRIMARY)
ax.text(3, 8.5, 'AVOID', fontsize=12, ha='center', alpha=0.3, fontweight='bold', color=COLOR_NEG)

ax.set_xlabel('Impact (Tac dong) - Cao = Tot', fontsize=12)
ax.set_ylabel('Effort (Cong suc) - Thap = De lam', fontsize=12)
ax.set_title('Priority Matrix: Hanh dong nao nen lam truoc?', fontsize=16, fontweight='bold')
ax.legend(title='Category', loc='upper left')
ax.set_xlim(0, 11)
ax.set_ylim(0, 11)
ax.invert_yaxis()  # Thap = de = o tren
plt.tight_layout()
plt.show()

# Quick wins
quick_wins = actions[(actions['Impact'] >= 6) & (actions['Effort'] <= 5)]
print("\\n=== QUICK WINS (Impact cao, Effort thap) - Lam ngay! ===")
for _, row in quick_wins.iterrows():
    print(f"  [{row['Category']}] {row['Action']} (Impact={row['Impact']}, Effort={row['Effort']})")\n""")

    # 7.3 Revenue Impact Waterfall
    code("""# === 7.3 Revenue Impact Waterfall ===
# Tinh cac "leak" trong chuoi gia tri
gross_revenue = order_items['quantity'].sum() * order_items['unit_price'].mean()  # uoc tinh
total_discount = order_items['discount_amount'].fillna(0).sum()
total_refund_amt = returns['refund_amount'].sum()
total_shipping = shipments['shipping_fee'].sum()
total_cogs = sales['COGS'].sum()
net_revenue = sales['Revenue'].sum()
gross_profit = sales['Gross_Profit'].sum()

# Waterfall data
waterfall_items = [
    ('Doanh thu gop', net_revenue + total_discount + total_refund_amt, COLOR_PRIMARY),
    ('(-) Khuyen mai', -total_discount, COLOR_NEG),
    ('(-) Hoan hang', -total_refund_amt, COLOR_NEG),
    ('= Doanh thu thuan', net_revenue, COLOR_POS),
    ('(-) Gia von (COGS)', -total_cogs, COLOR_NEG),
    ('= Loi nhuan gop', gross_profit, COLOR_POS),
]

fig, ax = plt.subplots(figsize=(14, 7))

labels = [item[0] for item in waterfall_items]
values = [item[1] for item in waterfall_items]
colors = [item[2] for item in waterfall_items]

bars = ax.bar(labels, [abs(v) for v in values], color=colors, edgecolor='white', alpha=0.8)

for bar, val in zip(bars, values):
    sign = '+' if val > 0 else ''
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + abs(val)*0.02,
            f'{sign}{val/1e9:.1f}B', ha='center', va='bottom', fontsize=10, fontweight='bold')

ax.set_title('Revenue Impact Waterfall - Dong tien tu doanh thu den loi nhuan', fontsize=16, fontweight='bold')
ax.set_ylabel('VND')
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x/1e9:.0f}B'))
plt.xticks(rotation=15)
plt.tight_layout()
plt.show()

print(f"\\n=== Tong ket Ro ri ===")
print(f"  Khuyen mai:  {total_discount:>15,.0f} VND ({total_discount/net_revenue*100:.1f}% doanh thu)")
print(f"  Hoan hang:   {total_refund_amt:>15,.0f} VND ({total_refund_amt/net_revenue*100:.1f}% doanh thu)")
print(f"  Gross Margin: {gross_profit/net_revenue*100:.1f}%")\n""")

    # Final conclusion
    md("""---
# TONG KET

Cau chuyen du lieu da chung minh: Doanh nghiep khong thieu so luong ban,
ma dang **ro ri loi nhuan** qua nhieu kenh:

1. **Dut gay ton kho va giao hang tre** lam mat khach va tang return rate
2. **Phu thuoc khuyen mai** an mon margin trong khi AOV co xu huong giam
3. **Retention thap** nghia la chi phi acquisition khong duoc thu hoi du

**Chien luoc uu tien:**
- Thuc hien cac Quick Wins truoc (Virtual Size Guide, giam voucher tran lan, win-back campaign)
- Dau tu dai han vao logistics va loyalty program
- Xay dung mo hinh du bao (Sales Forecasting) phai boc tach cac yeu to mua vu,
  promotion dependency va supply chain disruption de dam bao do chinh xac.

---
*Bao cao duoc tao tu dong bang Python. Moi bieu do la mot bang chung
tra loi cho mot cau hoi kinh doanh cu the.*""")
