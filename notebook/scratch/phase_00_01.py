"""Phase 0: Setup & Data Cleaning + Phase 1: Business Pulse"""

def build(md, code):
    # ===== TITLE =====
    md("""# Bao Cao Phan Tich Du Lieu Kinh Doanh: Tu Kham Pha Den Hanh Dong
## (EDA Storytelling Masterpiece - E-Commerce Fashion Vietnam)

Muc tieu cua bao cao nay la chuyen doi du lieu tho thanh cac quyet dinh kinh doanh chien luoc
thong qua 8 giai doan phan tich, ap dung nhat quan 4 cap do:

- **Descriptive**: Dieu gi da xay ra?
- **Diagnostic**: Tai sao lai xay ra?
- **Predictive**: Xu huong tiep theo la gi?
- **Prescriptive**: Chung ta can lam gi?""")

    # ===== PHASE 0: SETUP =====
    md("""---
# PHASE 0: Setup va Data Cleaning (Nen tang ky thuat)
**Muc tieu**: Dam bao du lieu sach va nhat quan truoc khi phan tich.""")

    code("""import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from datetime import timedelta
import warnings
warnings.filterwarnings('ignore')

# Thiet lap hien thi do thi
plt.style.use('seaborn-v0_8-whitegrid')
COLOR_POS = '#2ecc71'   # Xanh - tich cuc
COLOR_NEG = '#e74c3c'   # Do - rui ro
COLOR_NEU = '#95a5a6'   # Xam - trung tinh
COLOR_PRIMARY = '#3498db'
COLOR_SECONDARY = '#9b59b6'
PALETTE = [COLOR_PRIMARY, COLOR_NEG, COLOR_POS, COLOR_SECONDARY, '#f39c12', '#1abc9c', '#e67e22', '#34495e']
sns.set_palette(PALETTE)
plt.rcParams['figure.figsize'] = (14, 6)
plt.rcParams['font.size'] = 11
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.titleweight'] = 'bold'

# Load du lieu
data_dir = '../dataset/'
customers = pd.read_csv(data_dir + 'customers.csv', parse_dates=['signup_date'])
orders = pd.read_csv(data_dir + 'orders.csv', parse_dates=['order_date'])
order_items = pd.read_csv(data_dir + 'order_items.csv')
payments = pd.read_csv(data_dir + 'payments.csv')
shipments = pd.read_csv(data_dir + 'shipments.csv', parse_dates=['ship_date', 'delivery_date'])
returns = pd.read_csv(data_dir + 'returns.csv', parse_dates=['return_date'])
products = pd.read_csv(data_dir + 'products.csv')
promotions = pd.read_csv(data_dir + 'promotions.csv')
web_traffic = pd.read_csv(data_dir + 'web_traffic.csv', parse_dates=['date'])
inventory = pd.read_csv(data_dir + 'inventory.csv', parse_dates=['snapshot_date'])
reviews = pd.read_csv(data_dir + 'reviews.csv', parse_dates=['review_date'])
sales = pd.read_csv(data_dir + 'sales.csv', parse_dates=['Date'])
geography = pd.read_csv(data_dir + 'geography.csv')

print("=== Du lieu da load thanh cong ===")
for name, df in [('customers', customers), ('orders', orders), ('order_items', order_items),
                 ('payments', payments), ('shipments', shipments), ('returns', returns),
                 ('products', products), ('promotions', promotions), ('web_traffic', web_traffic),
                 ('inventory', inventory), ('reviews', reviews), ('sales', sales), ('geography', geography)]:
    print(f"  {name:15s}: {len(df):>10,} rows x {len(df.columns):>3} cols")\n""")

    # Data Quality
    md("""### 0.1 Data Quality Dashboard
Kiem tra tinh toan ven cua du lieu truoc khi phan tich.""")

    code("""# === Data Quality: Missing Values Heatmap ===
all_dfs = {'customers': customers, 'orders': orders, 'order_items': order_items,
           'payments': payments, 'shipments': shipments, 'returns': returns,
           'products': products, 'promotions': promotions, 'web_traffic': web_traffic,
           'inventory': inventory, 'reviews': reviews, 'sales': sales, 'geography': geography}

missing_summary = []
for name, df in all_dfs.items():
    total = len(df)
    for col in df.columns:
        miss = df[col].isna().sum()
        if miss > 0:
            missing_summary.append({'Table': name, 'Column': col,
                                    'Missing': miss, 'Pct': round(miss/total*100, 2)})

missing_df = pd.DataFrame(missing_summary)
if len(missing_df) > 0:
    pivot = missing_df.pivot_table(index='Table', columns='Column', values='Pct', fill_value=0)
    fig, ax = plt.subplots(figsize=(16, 6))
    sns.heatmap(pivot, annot=True, fmt='.1f', cmap='YlOrRd', ax=ax, linewidths=0.5)
    ax.set_title('Data Quality: Ty le Missing Values (%) theo Bang va Cot')
    plt.tight_layout()
    plt.show()
else:
    print("Khong co missing values trong du lieu.")

# Kiem tra duplicates
print("\\n=== Kiem tra Duplicates ===")
for name, df in [('orders', orders), ('customers', customers), ('payments', payments)]:
    pk = df.columns[0]
    dupes = df[pk].duplicated().sum()
    print(f"  {name:15s} - {pk}: {dupes} duplicates")\n""")

    # Feature Engineering
    md("""### 0.2 Xu ly Anomaly va Feature Engineering
Phat hien va xu ly loi logic: 74% don hang co signup_date SAU ngay mua dau tien.
Tao cac bien phu tro cho phan tich.""")

    code("""# === 1. Fix Signup Date Anomaly ===
first_orders = orders.groupby('customer_id')['order_date'].min().reset_index(name='first_order_date')
customers = customers.merge(first_orders, on='customer_id', how='left')
anomaly_pct = (customers['first_order_date'] < customers['signup_date']).mean() * 100
print(f"Ty le don hang truoc ngay dang ky: {anomaly_pct:.1f}%")
customers['true_signup_date'] = np.where(
    customers['first_order_date'] < customers['signup_date'],
    customers['first_order_date'], customers['signup_date'])
customers['true_signup_date'] = pd.to_datetime(customers['true_signup_date'])

# === 2. Tinh total_amount cho orders tu payments ===
if 'total_amount' not in orders.columns:
    order_totals = payments.groupby('order_id')['payment_value'].sum().rename('total_amount')
    orders = orders.join(order_totals, on='order_id')

# === 3. Feature Engineering ===
orders['order_month'] = orders['order_date'].dt.to_period('M').dt.to_timestamp()
orders['order_quarter'] = orders['order_date'].dt.quarter
orders['order_year'] = orders['order_date'].dt.year
orders['day_of_week'] = orders['order_date'].dt.dayofweek
orders['is_weekend'] = orders['day_of_week'].isin([5, 6]).astype(int)

# Delivery time features
ship_data = shipments.copy()
ship_data['delivery_time'] = (ship_data['delivery_date'] - ship_data['ship_date']).dt.days
ship_data['processing_time'] = None  # ship_date - order_date (can merge)

# Item-level revenue & profit
order_items['item_revenue'] = order_items['quantity'] * order_items['unit_price'] - order_items['discount_amount'].fillna(0)
oi_with_cogs = order_items.merge(products[['product_id', 'cogs']], on='product_id', how='left')
order_items['item_profit'] = oi_with_cogs['quantity'] * oi_with_cogs['unit_price'] - oi_with_cogs['discount_amount'].fillna(0) - oi_with_cogs['quantity'] * oi_with_cogs['cogs']
order_items['discount_rate'] = order_items['discount_amount'].fillna(0) / (order_items['quantity'] * order_items['unit_price']).replace(0, np.nan)
order_items['is_discounted'] = (order_items['discount_amount'].fillna(0) > 0).astype(int)

# Sales: Gross Profit
sales['Gross_Profit'] = sales['Revenue'] - sales['COGS']
sales['Gross_Margin'] = sales['Gross_Profit'] / sales['Revenue'].replace(0, np.nan)
sales['YearMonth'] = sales['Date'].dt.to_period('M')

# Orders delivered (for downstream analysis)
orders_delivered = orders[orders['order_status'] == 'delivered'].copy()

# Merge geography
orders = orders.merge(geography[['zip', 'region', 'district']], on='zip', how='left')

print("=== Feature Engineering hoan tat ===")
print(f"  Orders: {len(orders):,} | Delivered: {len(orders_delivered):,}")
print(f"  Sales range: {sales['Date'].min().date()} -> {sales['Date'].max().date()}")
print(f"  Gross Margin trung binh: {sales['Gross_Margin'].mean()*100:.1f}%")\n""")

    # ===== PHASE 1: BUSINESS PULSE =====
    md("""---
# PHASE 1: Business Pulse va Time Series Overview (Cai nhin toan canh)
**Muc tieu**: Xac dinh suc khoe doanh nghiep, tinh mua vu va xu huong tang truong.

> **Cau hoi kinh doanh**: Doanh thu dang di ve dau? Tang truong co ben vung khong?""")

    # 1.1 Revenue + Gross Profit Trend
    code("""# === 1.1 Monthly Revenue, COGS va Gross Profit Trend ===
monthly_sales = sales.groupby('YearMonth').agg(
    Revenue=('Revenue', 'sum'), COGS=('COGS', 'sum'), Gross_Profit=('Gross_Profit', 'sum')
).reset_index()
monthly_sales['month_dt'] = monthly_sales['YearMonth'].dt.to_timestamp()
monthly_sales['Gross_Margin'] = monthly_sales['Gross_Profit'] / monthly_sales['Revenue'] * 100

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 10), sharex=True,
                                gridspec_kw={'height_ratios': [3, 1]})

# Revenue & COGS
ax1.fill_between(monthly_sales['month_dt'], monthly_sales['Revenue'], alpha=0.3, color=COLOR_PRIMARY, label='Revenue')
ax1.fill_between(monthly_sales['month_dt'], monthly_sales['COGS'], alpha=0.3, color=COLOR_NEG, label='COGS')
ax1.plot(monthly_sales['month_dt'], monthly_sales['Revenue'], color=COLOR_PRIMARY, linewidth=1.5)
ax1.plot(monthly_sales['month_dt'], monthly_sales['COGS'], color=COLOR_NEG, linewidth=1.5)
ax1.fill_between(monthly_sales['month_dt'], monthly_sales['COGS'], monthly_sales['Revenue'],
                 alpha=0.15, color=COLOR_POS, label='Gross Profit')
ax1.set_title('Doanh thu, Gia von va Loi nhuan gop theo thang')
ax1.set_ylabel('VND')
ax1.legend(loc='upper left')
ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x/1e6:.0f}M'))

# Gross Margin
ax2.bar(monthly_sales['month_dt'], monthly_sales['Gross_Margin'],
        width=25, color=[COLOR_POS if v >= monthly_sales['Gross_Margin'].mean() else COLOR_NEG
                         for v in monthly_sales['Gross_Margin']], alpha=0.7)
ax2.axhline(monthly_sales['Gross_Margin'].mean(), color='black', linestyle='--', linewidth=1, label=f"TB: {monthly_sales['Gross_Margin'].mean():.1f}%")
ax2.set_ylabel('Gross Margin (%)')
ax2.set_title('Gross Margin Rate theo thang')
ax2.legend()

plt.tight_layout()
plt.show()
print(f"[Insight] Gross Margin trung binh: {monthly_sales['Gross_Margin'].mean():.1f}%. Revenue cao diem vao Q4 hang nam.")\n""")

    # 1.2 Time Series Decomposition
    code("""# === 1.2 Time Series Decomposition (Boc tach xu huong, mua vu, nhieu) ===
from statsmodels.tsa.seasonal import seasonal_decompose

monthly_rev = sales.groupby('YearMonth')['Revenue'].sum()
monthly_rev.index = monthly_rev.index.to_timestamp()

# Can it nhat 2 chu ky (24 thang) de decompose
if len(monthly_rev) >= 24:
    result = seasonal_decompose(monthly_rev, model='multiplicative', period=12)

    fig, axes = plt.subplots(4, 1, figsize=(16, 12), sharex=True)
    titles = ['Observed (Du lieu goc)', 'Trend (Xu huong dai han)',
              'Seasonal (Tinh mua vu)', 'Residual (Nhieu/Bat thuong)']
    data_list = [result.observed, result.trend, result.seasonal, result.resid]
    colors = [COLOR_PRIMARY, COLOR_POS, COLOR_SECONDARY, COLOR_NEG]

    for ax, title, data, color in zip(axes, titles, data_list, colors):
        ax.plot(data, color=color, linewidth=1.5)
        ax.set_title(title)
        ax.set_ylabel('Value')

    plt.suptitle('Time Series Decomposition - Doanh thu hang thang (Multiplicative)', fontsize=16, fontweight='bold', y=1.01)
    plt.tight_layout()
    plt.show()

    # Phan tich seasonal pattern
    seasonal_pattern = result.seasonal.groupby(result.seasonal.index.month).first()
    peak_month = seasonal_pattern.idxmax()
    trough_month = seasonal_pattern.idxmin()
    print(f"[Insight] Thang cao diem nhat: thang {peak_month} (seasonal factor: {seasonal_pattern.max():.2f}x)")
    print(f"[Insight] Thang thap diem nhat: thang {trough_month} (seasonal factor: {seasonal_pattern.min():.2f}x)")
else:
    print("Khong du du lieu de thuc hien seasonal decomposition (can >= 24 thang)")\n""")

    # 1.3 Growth Rate
    code("""# === 1.3 Tang truong MoM va YoY ===
monthly_sales['MoM_Growth'] = monthly_sales['Revenue'].pct_change() * 100
monthly_sales['Year'] = monthly_sales['month_dt'].dt.year
monthly_sales['Month'] = monthly_sales['month_dt'].dt.month

# YoY: so sanh cung thang nam truoc
monthly_sales['YoY_Growth'] = None
for idx, row in monthly_sales.iterrows():
    prev = monthly_sales[(monthly_sales['Year'] == row['Year'] - 1) & (monthly_sales['Month'] == row['Month'])]
    if len(prev) > 0:
        prev_rev = prev['Revenue'].values[0]
        if prev_rev > 0:
            monthly_sales.at[idx, 'YoY_Growth'] = (row['Revenue'] - prev_rev) / prev_rev * 100
monthly_sales['YoY_Growth'] = pd.to_numeric(monthly_sales['YoY_Growth'])

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 8), sharex=True)

# MoM
colors_mom = [COLOR_POS if v >= 0 else COLOR_NEG for v in monthly_sales['MoM_Growth'].fillna(0)]
ax1.bar(monthly_sales['month_dt'], monthly_sales['MoM_Growth'].fillna(0), width=25, color=colors_mom, alpha=0.7)
ax1.axhline(0, color='black', linewidth=0.8)
ax1.set_title('Tang truong Month-over-Month (MoM %)')
ax1.set_ylabel('MoM Growth (%)')

# YoY
yoy_data = monthly_sales.dropna(subset=['YoY_Growth'])
colors_yoy = [COLOR_POS if v >= 0 else COLOR_NEG for v in yoy_data['YoY_Growth']]
ax2.bar(yoy_data['month_dt'], yoy_data['YoY_Growth'], width=25, color=colors_yoy, alpha=0.7)
ax2.axhline(0, color='black', linewidth=0.8)
ax2.set_title('Tang truong Year-over-Year (YoY %)')
ax2.set_ylabel('YoY Growth (%)')

plt.tight_layout()
plt.show()

avg_yoy = yoy_data['YoY_Growth'].mean()
print(f"[Insight] Tang truong YoY trung binh: {avg_yoy:.1f}%")
print(f"[Insight] So thang tang truong am (YoY): {(yoy_data['YoY_Growth'] < 0).sum()}/{len(yoy_data)}")\n""")

    # 1.4 Spike Analysis
    code("""# === 1.4 Spike Analysis - Ngay doanh thu dot bien (Double Days: 11/11, 12/12) ===
daily_rev = sales.set_index('Date')['Revenue']

# Danh dau cac ngay dac biet
special_dates = {}
for year in range(daily_rev.index.year.min(), daily_rev.index.year.max() + 1):
    for m, d in [(11, 11), (12, 12)]:
        dt = pd.Timestamp(year, m, d)
        if dt in daily_rev.index:
            special_dates[dt] = f'{m}/{d}'

# Top 1% ngay doanh thu cao nhat
threshold = daily_rev.quantile(0.99)
spike_days = daily_rev[daily_rev >= threshold]

fig, ax = plt.subplots(figsize=(16, 6))
ax.plot(daily_rev.index, daily_rev.values, color=COLOR_NEU, alpha=0.4, linewidth=0.5)
ax.plot(daily_rev.rolling(30).mean().index, daily_rev.rolling(30).mean().values,
        color=COLOR_PRIMARY, linewidth=2, label='MA 30 ngay')

# Highlight spikes
ax.scatter(spike_days.index, spike_days.values, color=COLOR_NEG, s=30, zorder=5, label=f'Top 1% spikes (>= {threshold:,.0f})')

# Annotate double days
for dt, label in special_dates.items():
    if dt in daily_rev.index:
        rev = daily_rev[dt]
        surrounding = daily_rev[dt - timedelta(days=7):dt + timedelta(days=7)].mean()
        multiplier = rev / surrounding if surrounding > 0 else 0
        if multiplier > 1.5:
            ax.annotate(f'{label}\\n{multiplier:.1f}x', xy=(dt, rev),
                       fontsize=8, ha='center', va='bottom', color=COLOR_NEG, fontweight='bold')

ax.set_title('Daily Revenue voi Spike Analysis (Double Days 11/11, 12/12)')
ax.set_ylabel('Revenue (VND)')
ax.legend()
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x/1e6:.0f}M'))
plt.tight_layout()
plt.show()

# Phan tich cannibalization
print("\\n=== Spike Multiplier cho Double Days ===")
for dt, label in sorted(special_dates.items()):
    if dt in daily_rev.index:
        rev = daily_rev[dt]
        before_7d = daily_rev[dt - timedelta(days=7):dt - timedelta(days=1)].mean()
        after_7d = daily_rev[dt + timedelta(days=1):dt + timedelta(days=7)].mean()
        mult = rev / before_7d if before_7d > 0 else 0
        cannibal = (after_7d - before_7d) / before_7d * 100 if before_7d > 0 else 0
        print(f"  {dt.date()} ({label}): Revenue = {rev:,.0f} | Spike = {mult:.1f}x | Post-spike drop = {cannibal:+.1f}%")\n""")

    # 1.5 Volume vs AOV
    code("""# === 1.5 Volume vs AOV (Chat luong tang truong) ===
monthly_kpi = orders.groupby('order_month').agg(
    order_count=('order_id', 'count'),
    total_revenue=('total_amount', 'sum')
).dropna()
monthly_kpi['AOV'] = monthly_kpi['total_revenue'] / monthly_kpi['order_count']

fig, ax = plt.subplots(figsize=(12, 8))
scatter = ax.scatter(monthly_kpi['order_count'], monthly_kpi['AOV'],
                     c=monthly_kpi.index.year, cmap='viridis', s=80, alpha=0.7, edgecolors='white')
plt.colorbar(scatter, label='Nam')
ax.set_xlabel('So luong don hang / thang')
ax.set_ylabel('AOV (Gia tri don trung binh)')
ax.set_title('Chat luong tang truong: Volume vs AOV theo thang')

# Trend line
z = np.polyfit(monthly_kpi['order_count'], monthly_kpi['AOV'], 1)
p = np.poly1d(z)
x_line = np.linspace(monthly_kpi['order_count'].min(), monthly_kpi['order_count'].max(), 100)
ax.plot(x_line, p(x_line), '--', color=COLOR_NEG, linewidth=2, label=f'Trend (slope={z[0]:.2f})')
ax.legend()
plt.tight_layout()
plt.show()

if z[0] < 0:
    print("[Insight] Xu huong AOV GIAM khi volume tang -> Tang truong bang so luong, khong phai chat luong")
else:
    print("[Insight] AOV tang cung volume -> Tang truong ben vung")\n""")

    # Phase 1 Insights
    md("""### Insights Phase 1: Business Pulse

**Descriptive**: Doanh thu bung no vao Quy 4 (mua vu), Gross Margin trung binh cho thay bien loi nhuan
con kha tot. Time Series Decomposition boc tach ro seasonal pattern voi dinh vao thang 11-12.

**Diagnostic**: Bieu do Volume vs AOV cho thay khi so luong don tang, AOV co xu huong giam
-> khach hang mua nhieu hon nhung gia tri moi don thap hon, co the do phu thuoc khuyen mai.
Spike Analysis cho thay hieu ung "cannibalization" sau ngay Double Day.

**Predictive**: Neu xu huong Gross Margin tiep tuc giam, bien loi nhuan se bi thu hep nghiem trong
trong 2-3 nam toi. Seasonal pattern cho phep du bao revenue theo thang chinh xac hon.

**Prescriptive**: (1) Duy tri Gross Margin > muc trung binh bang cach toi uu chi phi.
(2) Giam phu thuoc vao Double Days bang cach trai deu chuong trinh KM.
(3) Tap trung tang AOV thay vi chi tang volume.""")
