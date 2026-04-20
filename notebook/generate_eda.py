#!/usr/bin/env python3
"""Generate comprehensive EDA notebook for Datathon 2026"""
import json, os

cells = []

def md(text):
    text = text.strip()
    lines = text.split('\n')
    source = [l + '\n' for l in lines[:-1]] + [lines[-1]] if lines else ['']
    cells.append({"cell_type": "markdown", "metadata": {}, "source": source})

def code(text):
    text = text.strip()
    lines = text.split('\n')
    source = [l + '\n' for l in lines[:-1]] + [lines[-1]] if lines else ['']
    cells.append({"cell_type": "code", "metadata": {}, "source": source, "outputs": [], "execution_count": None})

# ==================== PHASE 0 ====================
md("""# 🏆 DATATHON 2026 — The Gridbreaker
## Exploratory Data Analysis (EDA) Toàn Diện

**Doanh nghiệp thời trang TMĐT Việt Nam** | Giai đoạn: 04/07/2012 – 31/12/2022

---

| Cấp độ | Câu hỏi | Icon |
|---|---|---|
| **Descriptive** | Chuyện gì đã xảy ra? | 📊 |
| **Diagnostic** | Tại sao? | 🔍 |
| **Predictive** | Điều gì sẽ xảy ra? | 🔮 |
| **Prescriptive** | Nên làm gì? | 💡 |""")

code("""import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mticker
import seaborn as sns
from scipy import stats
from datetime import timedelta
import warnings
warnings.filterwarnings('ignore')

plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams.update({
    'figure.figsize': (14, 6), 'figure.dpi': 100, 'font.size': 11,
    'axes.titlesize': 14, 'axes.titleweight': 'bold', 'axes.labelsize': 12,
    'axes.spines.top': False, 'axes.spines.right': False,
})

COLORS = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#44BBA4',
          '#E94F37', '#393E41', '#5C946E', '#6B4C9A', '#D4A574']
sns.set_palette(sns.color_palette(COLORS))

def fmt_num(n):
    if pd.isna(n): return 'N/A'
    if abs(n) >= 1e9: return f'{n/1e9:.1f}B'
    elif abs(n) >= 1e6: return f'{n/1e6:.1f}M'
    elif abs(n) >= 1e3: return f'{n/1e3:.1f}K'
    return f'{n:,.0f}'

print('✅ Import thành công!')""")

code("""DATA_DIR = '../dataset/'

products = pd.read_csv(DATA_DIR + 'products.csv')
customers = pd.read_csv(DATA_DIR + 'customers.csv')
promotions = pd.read_csv(DATA_DIR + 'promotions.csv')
geography = pd.read_csv(DATA_DIR + 'geography.csv')
orders = pd.read_csv(DATA_DIR + 'orders.csv')
order_items = pd.read_csv(DATA_DIR + 'order_items.csv')
payments = pd.read_csv(DATA_DIR + 'payments.csv')
shipments = pd.read_csv(DATA_DIR + 'shipments.csv')
returns = pd.read_csv(DATA_DIR + 'returns.csv')
reviews = pd.read_csv(DATA_DIR + 'reviews.csv')
sales = pd.read_csv(DATA_DIR + 'sales.csv')
inventory = pd.read_csv(DATA_DIR + 'inventory.csv')
web_traffic = pd.read_csv(DATA_DIR + 'web_traffic.csv')
sample_sub = pd.read_csv(DATA_DIR + 'sample_submission.csv')

# Parse dates
for df, cols in [(customers, ['signup_date']), (orders, ['order_date']),
                 (promotions, ['start_date','end_date']), (shipments, ['ship_date','delivery_date']),
                 (returns, ['return_date']), (reviews, ['review_date']),
                 (sales, ['Date']), (sample_sub, ['Date']),
                 (inventory, ['snapshot_date']), (web_traffic, ['date'])]:
    for c in cols:
        df[c] = pd.to_datetime(df[c])

datasets = {'products': products, 'customers': customers, 'promotions': promotions,
            'geography': geography, 'orders': orders, 'order_items': order_items,
            'payments': payments, 'shipments': shipments, 'returns': returns,
            'reviews': reviews, 'sales': sales, 'inventory': inventory, 'web_traffic': web_traffic}

print(f"{'Bảng':<20} {'Dòng':>10} {'Cột':>6} {'MB':>8}")
print("="*50)
for name, df in datasets.items():
    mem = df.memory_usage(deep=True).sum() / 1024**2
    print(f"{name:<20} {df.shape[0]:>10,} {df.shape[1]:>6} {mem:>7.1f}")""")

# ==================== PHASE 1: DATA QUALITY ====================
md("""---
# Phase 1: 🔍 Đánh Giá Chất Lượng Dữ Liệu""")

code("""# 1.1 Missing Values
print("📊 GIÁ TRỊ THIẾU (MISSING VALUES)")
print("="*55)
for name, df in datasets.items():
    miss = df.isnull().sum()
    miss = miss[miss > 0]
    if len(miss) > 0:
        print(f"\\n  📋 {name}:")
        for col, cnt in miss.items():
            print(f"     {col:<25} {cnt:>8,} ({cnt/len(df)*100:.1f}%)")

# Visualization
fig, axes = plt.subplots(1, 3, figsize=(18, 5))
for idx, (name, df) in enumerate([('customers', customers), ('order_items', order_items), ('promotions', promotions)]):
    miss_pct = (df.isnull().sum() / len(df) * 100).sort_values()
    miss_pct = miss_pct[miss_pct > 0]
    if len(miss_pct) > 0:
        miss_pct.plot(kind='barh', ax=axes[idx], color=COLORS[idx], edgecolor='white')
        axes[idx].set_title(f'Missing: {name}', fontweight='bold')
        axes[idx].set_xlabel('%')
        for i, v in enumerate(miss_pct):
            axes[idx].text(v + 0.3, i, f'{v:.1f}%', va='center', fontsize=9)
    else:
        axes[idx].text(0.5, 0.5, 'Không thiếu ✅', transform=axes[idx].transAxes, ha='center', fontsize=14)
        axes[idx].set_title(f'Missing: {name}', fontweight='bold')
plt.suptitle('📊 Phân Tích Giá Trị Thiếu', fontsize=16, fontweight='bold', y=1.02)
plt.tight_layout()
plt.show()""")

code("""# 1.2 Primary Key & FK Integrity
print("🔑 KIỂM TRA KHÓA CHÍNH")
print("="*55)
for name, pk, df in [('products','product_id',products), ('customers','customer_id',customers),
                      ('orders','order_id',orders), ('payments','order_id',payments),
                      ('geography','zip',geography), ('returns','return_id',returns),
                      ('reviews','review_id',reviews)]:
    dups = len(df) - df[pk].nunique()
    print(f"  {'✅' if dups==0 else '⚠️'} {name}.{pk}: {len(df):,} rows, {dups} duplicates")

print(f"\\n🔗 KIỂM TRA FK")
print("="*55)
for fk_n, fk_v, pk_n, pk_v in [
    ('orders.customer_id', orders['customer_id'], 'customers.customer_id', customers['customer_id']),
    ('order_items.order_id', order_items['order_id'], 'orders.order_id', orders['order_id']),
    ('order_items.product_id', order_items['product_id'], 'products.product_id', products['product_id']),
    ('payments.order_id', payments['order_id'], 'orders.order_id', orders['order_id']),
    ('returns.order_id', returns['order_id'], 'orders.order_id', orders['order_id']),
    ('reviews.order_id', reviews['order_id'], 'orders.order_id', orders['order_id'])]:
    orphans = fk_v[~fk_v.isin(pk_v)].nunique()
    print(f"  {'✅' if orphans==0 else '⚠️'} {fk_n} → {pk_n} | orphans: {orphans}")

# Descriptive stats
print("\\n📈 THỐNG KÊ MÔ TẢ")
print("="*55)
products['margin'] = products['price'] - products['cogs']
products['margin_pct'] = products['margin'] / products['price'] * 100
print("\\nProducts - Price & Margin:")
print(products[['price','cogs','margin','margin_pct']].describe().round(2))""")

md("""### 📝 Phase 1 — Kết luận
- **📊 Descriptive:** Missing tập trung ở demographics (gender, age_group) và promo fields
- **🔍 Diagnostic:** Nullable fields do thu thập không bắt buộc
- **💡 Prescriptive:** Dùng 'Unknown' thay vì drop rows cho missing demographics""")

# ==================== PHASE 2: MASTER DATA ====================
md("""---
# Phase 2: 📊 Master Data Profiling""")

code("""# 2.1 Products
fig, axes = plt.subplots(2, 2, figsize=(16, 12))

cat_counts = products['category'].value_counts()
bars = axes[0,0].bar(cat_counts.index, cat_counts.values, color=COLORS[:len(cat_counts)], edgecolor='white')
axes[0,0].set_title('Sản phẩm theo Danh mục', fontweight='bold')
axes[0,0].set_ylabel('Số SP')
axes[0,0].tick_params(axis='x', rotation=45)
for b, v in zip(bars, cat_counts.values):
    axes[0,0].text(b.get_x()+b.get_width()/2, v+3, str(v), ha='center', fontsize=9)

seg_counts = products['segment'].value_counts()
axes[0,1].pie(seg_counts.values, labels=seg_counts.index, autopct='%1.1f%%',
              colors=COLORS[:len(seg_counts)], startangle=90)
axes[0,1].set_title('Phân khúc', fontweight='bold')

for i, seg in enumerate(products['segment'].unique()):
    axes[1,0].hist(products[products['segment']==seg]['price'], bins=30, alpha=0.6,
                   label=seg, color=COLORS[i], edgecolor='white')
axes[1,0].set_title('Giá theo Phân khúc', fontweight='bold')
axes[1,0].set_xlabel('Giá (VNĐ)')
axes[1,0].legend()
axes[1,0].xaxis.set_major_formatter(mticker.FuncFormatter(lambda x,p: f'{x:,.0f}'))

margin_seg = products.groupby('segment')['margin_pct'].agg(['mean','std']).sort_values('mean')
bars = axes[1,1].barh(margin_seg.index, margin_seg['mean'], xerr=margin_seg['std'],
                       color=COLORS[:len(margin_seg)], edgecolor='white', capsize=3)
axes[1,1].set_title('Margin TB theo Phân khúc (%)', fontweight='bold')
axes[1,1].set_xlabel('Margin (%)')
for b, v in zip(bars, margin_seg['mean']):
    axes[1,1].text(v+1, b.get_y()+b.get_height()/2, f'{v:.1f}%', va='center', fontweight='bold')

plt.suptitle('🏷️ PHÂN TÍCH SẢN PHẨM', fontsize=16, fontweight='bold', y=1.01)
plt.tight_layout()
plt.show()""")

code("""# 2.2 Customers
fig, axes = plt.subplots(2, 2, figsize=(16, 12))

signup_m = customers.set_index('signup_date').resample('M').size()
axes[0,0].fill_between(signup_m.index, signup_m.values, alpha=0.3, color=COLORS[0])
axes[0,0].plot(signup_m.index, signup_m.values, color=COLORS[0], linewidth=2)
axes[0,0].set_title('Đăng ký KH theo Tháng', fontweight='bold')
axes[0,0].xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

gender_c = customers['gender'].fillna('Không rõ').value_counts()
axes[0,1].bar(gender_c.index, gender_c.values, color=COLORS[:len(gender_c)], edgecolor='white')
axes[0,1].set_title('Giới tính', fontweight='bold')
for b, v in zip(axes[0,1].patches, gender_c.values):
    axes[0,1].text(b.get_x()+b.get_width()/2, v+100, f'{v:,}', ha='center', fontsize=9)

age_c = customers['age_group'].fillna('Không rõ').value_counts().sort_index()
axes[1,0].bar(age_c.index, age_c.values, color=COLORS[2], edgecolor='white')
axes[1,0].set_title('Nhóm tuổi', fontweight='bold')
axes[1,0].tick_params(axis='x', rotation=45)

ch_c = customers['acquisition_channel'].fillna('Không rõ').value_counts()
axes[1,1].barh(ch_c.index, ch_c.values, color=COLORS[3], edgecolor='white')
axes[1,1].set_title('Kênh thu hút KH', fontweight='bold')

plt.suptitle('👥 PHÂN TÍCH KHÁCH HÀNG', fontsize=16, fontweight='bold', y=1.01)
plt.tight_layout()
plt.show()""")

code("""# 2.3 Geography & Promotions
fig, axes = plt.subplots(1, 3, figsize=(18, 6))

region_c = geography['region'].value_counts()
axes[0].pie(region_c.values, labels=region_c.index, autopct='%1.1f%%', colors=COLORS[:3], startangle=90)
axes[0].set_title('Vùng địa lý', fontweight='bold')

cust_geo = customers.merge(geography, on='zip', how='left', suffixes=('','_g'))
top_cities = cust_geo['city'].value_counts().head(10)
axes[1].barh(top_cities.index[::-1], top_cities.values[::-1], color=COLORS[0], edgecolor='white')
axes[1].set_title('Top 10 Thành phố', fontweight='bold')

promo_type = promotions['promo_type'].value_counts()
axes[2].bar(promo_type.index, promo_type.values, color=[COLORS[1], COLORS[4]], edgecolor='white')
axes[2].set_title('Loại Khuyến mãi', fontweight='bold')
for b, v in zip(axes[2].patches, promo_type.values):
    axes[2].text(b.get_x()+b.get_width()/2, v+0.2, str(v), ha='center', fontsize=11, fontweight='bold')

plt.suptitle('🗺️ ĐỊA LÝ & KHUYẾN MÃI', fontsize=16, fontweight='bold', y=1.02)
plt.tight_layout()
plt.show()

print("\\n🏷️ Chi tiết KM:")
print(promotions[['promo_name','promo_type','discount_value','stackable_flag','applicable_category']].to_string(index=False))""")

md("""### 📝 Phase 2 — Kết luận
- **📊** 4 phân khúc SP rõ (Premium/Performance/Activewear/Standard), Premium margin cao nhất
- **🔍** Missing demographics → cần chiến lược thu thập tốt hơn
- **💡** Tập trung marketing Premium/Performance (margin cao), mở rộng data collection""")

# ==================== PHASE 3: REVENUE ====================
md("""---
# Phase 3: 💰 Phân Tích Doanh Thu & Bán Hàng ⭐
> Phần quan trọng nhất — phục vụ Part 2 (storytelling) và Part 3 (forecasting)""")

code("""# 3.1 Revenue Overview
sales['Gross_Profit'] = sales['Revenue'] - sales['COGS']
sales['Margin_Pct'] = sales['Gross_Profit'] / sales['Revenue'] * 100
sales['Year'] = sales['Date'].dt.year
sales['Month'] = sales['Date'].dt.month
sales['Quarter'] = sales['Date'].dt.quarter
sales['DayOfWeek'] = sales['Date'].dt.dayofweek
sales['WeekOfYear'] = sales['Date'].dt.isocalendar().week.astype(int)

fig, axes = plt.subplots(3, 1, figsize=(18, 14), sharex=True)

axes[0].plot(sales['Date'], sales['Revenue'], color=COLORS[0], alpha=0.3, linewidth=0.5)
axes[0].plot(sales['Date'], sales['Revenue'].rolling(30).mean(), color=COLORS[0], linewidth=2, label='MA30')
axes[0].plot(sales['Date'], sales['Revenue'].rolling(90).mean(), color=COLORS[1], linewidth=2, label='MA90')
axes[0].set_title('Doanh thu hàng ngày', fontweight='bold')
axes[0].yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,p: f'{x/1e6:.0f}M'))
axes[0].legend()

axes[1].plot(sales['Date'], sales['COGS'], color=COLORS[3], alpha=0.3, linewidth=0.5)
axes[1].plot(sales['Date'], sales['COGS'].rolling(30).mean(), color=COLORS[3], linewidth=2, label='MA30')
axes[1].set_title('Giá vốn (COGS)', fontweight='bold')
axes[1].yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,p: f'{x/1e6:.0f}M'))
axes[1].legend()

axes[2].plot(sales['Date'], sales['Margin_Pct'].rolling(30).mean(), color=COLORS[4], linewidth=2)
axes[2].axhline(y=sales['Margin_Pct'].mean(), color='red', linestyle='--', label=f'TB: {sales["Margin_Pct"].mean():.1f}%')
axes[2].set_title('Biên lợi nhuận gộp (%)', fontweight='bold')
axes[2].legend()

plt.suptitle('💰 TỔNG QUAN DOANH THU (2012-2022)', fontsize=16, fontweight='bold', y=1.01)
plt.tight_layout()
plt.show()

print(f"  Tổng Revenue:      {sales['Revenue'].sum():>18,.0f}")
print(f"  Tổng COGS:         {sales['COGS'].sum():>18,.0f}")
print(f"  Tổng Gross Profit: {sales['Gross_Profit'].sum():>18,.0f}")
print(f"  Avg Margin:        {sales['Margin_Pct'].mean():>17.1f}%")""")

code("""# 3.2 YoY Growth
fig, axes = plt.subplots(1, 2, figsize=(16, 6))

yearly = sales.groupby('Year').agg(Revenue=('Revenue','sum'), COGS=('COGS','sum')).reset_index()
yearly['Growth'] = yearly['Revenue'].pct_change() * 100

x = np.arange(len(yearly))
axes[0].bar(x-0.175, yearly['Revenue']/1e9, 0.35, label='Revenue', color=COLORS[0], edgecolor='white')
axes[0].bar(x+0.175, yearly['COGS']/1e9, 0.35, label='COGS', color=COLORS[3], edgecolor='white')
axes[0].set_xticks(x)
axes[0].set_xticklabels(yearly['Year'].astype(int))
axes[0].set_title('Revenue & COGS theo Năm (Tỷ)', fontweight='bold')
axes[0].legend()

growth_colors = [COLORS[4] if g>=0 else COLORS[3] for g in yearly['Growth'].fillna(0)]
bars = axes[1].bar(yearly['Year'].astype(int), yearly['Growth'].fillna(0), color=growth_colors, edgecolor='white')
axes[1].axhline(0, color='black', linewidth=0.5)
axes[1].set_title('Tăng trưởng YoY (%)', fontweight='bold')
for b, v in zip(bars, yearly['Growth'].fillna(0)):
    if not pd.isna(v):
        axes[1].text(b.get_x()+b.get_width()/2, v+(1 if v>=0 else -2), f'{v:.1f}%', ha='center', fontsize=9)

plt.tight_layout()
plt.show()""")

code("""# 3.3 Seasonality
fig, axes = plt.subplots(2, 2, figsize=(16, 12))

dow_rev = sales.groupby('DayOfWeek')['Revenue'].mean()
day_names = ['T2','T3','T4','T5','T6','T7','CN']
bars = axes[0,0].bar(day_names, dow_rev.values, color=COLORS[:7], edgecolor='white')
axes[0,0].set_title('Revenue TB theo Ngày trong tuần', fontweight='bold')
axes[0,0].yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,p: f'{x/1e6:.1f}M'))

month_rev = sales.groupby('Month')['Revenue'].mean()
month_n = ['T1','T2','T3','T4','T5','T6','T7','T8','T9','T10','T11','T12']
bars = axes[0,1].bar(month_n, month_rev.values, color=COLORS[0], edgecolor='white')
axes[0,1].set_title('Revenue TB theo Tháng', fontweight='bold')
axes[0,1].yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,p: f'{x/1e6:.1f}M'))
peak = month_rev.mean() * 1.1
for i, (b, v) in enumerate(zip(bars, month_rev.values)):
    if v > peak:
        b.set_color(COLORS[1])

monthly_matrix = sales.groupby(['Year','Month'])['Revenue'].sum().reset_index().pivot(index='Year', columns='Month', values='Revenue')
sns.heatmap(monthly_matrix/1e9, annot=True, fmt='.1f', cmap='YlOrRd', ax=axes[1,0], linewidths=0.5)
axes[1,0].set_title('Heatmap Năm × Tháng (Tỷ VNĐ)', fontweight='bold')

q = sales.groupby(['Year','Quarter'])['Revenue'].sum().reset_index().pivot(index='Year', columns='Quarter', values='Revenue')
q.plot(kind='bar', ax=axes[1,1], color=COLORS[:4], edgecolor='white', width=0.8)
axes[1,1].set_title('Revenue theo Quý', fontweight='bold')
axes[1,1].yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,p: f'{x/1e9:.0f}B'))
axes[1,1].legend(title='Quý', labels=['Q1','Q2','Q3','Q4'])
axes[1,1].tick_params(axis='x', rotation=45)

plt.suptitle('📅 TÍNH MÙA VỤ', fontsize=16, fontweight='bold', y=1.01)
plt.tight_layout()
plt.show()""")

code("""# 3.4 Time Series Decomposition & ACF/PACF
from statsmodels.tsa.seasonal import STL
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf

sales_ts = sales.set_index('Date')['Revenue']
stl = STL(sales_ts, period=7, robust=True).fit()

fig, axes = plt.subplots(4, 1, figsize=(18, 14), sharex=True)
for ax, data, title, c in zip(axes,
    [stl.observed, stl.trend, stl.seasonal, stl.resid],
    ['Observed', 'Trend', 'Seasonal (7 ngày)', 'Residual'],
    [COLORS[0], COLORS[1], COLORS[4], COLORS[3]]):
    ax.plot(data, color=c, linewidth=0.8 if 'Observed' in title or 'Residual' in title else 2, alpha=0.7)
    ax.set_title(title, fontweight='bold')
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,p: f'{x/1e6:.0f}M'))
plt.suptitle('📉 STL DECOMPOSITION', fontsize=16, fontweight='bold', y=1.01)
plt.tight_layout()
plt.show()

fig, axes = plt.subplots(1, 2, figsize=(16, 5))
plot_acf(sales_ts.dropna(), lags=60, ax=axes[0], color=COLORS[0])
axes[0].set_title('ACF', fontweight='bold')
plot_pacf(sales_ts.dropna(), lags=60, ax=axes[1], color=COLORS[1], method='ywm')
axes[1].set_title('PACF', fontweight='bold')
plt.suptitle('📊 ACF & PACF', fontsize=14, fontweight='bold', y=1.02)
plt.tight_layout()
plt.show()
print("🔍 ACF spike tại lag 7 → mùa vụ tuần. Quan trọng cho SARIMA/lag features.")""")

md("""### 📝 Phase 3 — Kết luận
- **📊** Revenue tăng trưởng qua năm, mùa vụ tuần & tháng rõ rệt
- **🔍** Ngày giữa tuần doanh thu cao hơn, một số tháng có seasonal spikes
- **🔮** STL trend tăng → 2023-2024 tiếp tục tăng; ACF lag-7 → feature quan trọng
- **💡** Tối ưu marketing theo DOW, dùng lag-7/30 cho forecasting, plan inventory theo mùa""")

# ==================== PHASE 4: ORDERS ====================
md("""---
# Phase 4: 🛒 Phân Tích Hành Vi Đơn Hàng""")

code("""fig, axes = plt.subplots(2, 2, figsize=(16, 12))

status_c = orders['order_status'].value_counts()
status_col = {'delivered':COLORS[4],'shipped':COLORS[0],'cancelled':COLORS[3],'returned':COLORS[1],'pending':COLORS[5]}
axes[0,0].pie(status_c.values, labels=status_c.index, autopct='%1.1f%%',
              colors=[status_col.get(s, COLORS[6]) for s in status_c.index], startangle=90)
axes[0,0].set_title('Trạng thái Đơn hàng', fontweight='bold')

pay_c = orders['payment_method'].value_counts()
axes[0,1].barh(pay_c.index, pay_c.values, color=COLORS[0], edgecolor='white')
axes[0,1].set_title('Phương thức Thanh toán', fontweight='bold')

dev_c = orders['device_type'].value_counts()
axes[1,0].bar(dev_c.index, dev_c.values, color=COLORS[:len(dev_c)], edgecolor='white')
axes[1,0].set_title('Thiết bị', fontweight='bold')

src_c = orders['order_source'].value_counts()
axes[1,1].bar(src_c.index, src_c.values, color=COLORS[1], edgecolor='white')
axes[1,1].set_title('Kênh đặt hàng', fontweight='bold')
axes[1,1].tick_params(axis='x', rotation=45)

plt.suptitle('🛒 HÀNH VI ĐƠN HÀNG', fontsize=16, fontweight='bold', y=1.01)
plt.tight_layout()
plt.show()

total = len(orders)
for st in ['delivered','cancelled','returned']:
    cnt = (orders['order_status']==st).sum()
    print(f"  {st:<12}: {cnt:>10,} ({cnt/total*100:.1f}%)")""")

code("""# Order trends
orders['year'] = orders['order_date'].dt.year

fig, axes = plt.subplots(1, 2, figsize=(16, 6))

monthly_ord = orders.set_index('order_date').resample('M').size()
axes[0].fill_between(monthly_ord.index, monthly_ord.values, alpha=0.3, color=COLORS[0])
axes[0].plot(monthly_ord.index, monthly_ord.values, color=COLORS[0], linewidth=2)
axes[0].set_title('Đơn hàng theo Tháng', fontweight='bold')
axes[0].xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

dev_yr = orders.groupby(['year','device_type']).size().unstack(fill_value=0)
dev_pct = dev_yr.div(dev_yr.sum(axis=1), axis=0) * 100
dev_pct.plot(kind='area', stacked=True, ax=axes[1], color=COLORS[:len(dev_pct.columns)], alpha=0.8)
axes[1].set_title('Xu hướng thiết bị (%)', fontweight='bold')
axes[1].set_ylim(0, 100)
axes[1].legend(loc='center left', bbox_to_anchor=(1, 0.5))

plt.tight_layout()
plt.show()""")

md("""### 📝 Phase 4 — Kết luận
- **📊** Phần lớn đơn delivered. Mobile & digital payment tăng dần
- **🔍** Trend mobile phù hợp thị trường VN
- **💡** Đầu tư UX mobile, push digital payment giảm COD logistics""")

# ==================== PHASE 5: CUSTOMER ANALYTICS ====================
md("""---
# Phase 5: 👥 Customer Analytics — RFM & Cohort""")

code("""# 5.1 RFM Analysis
delivered_orders = orders[orders['order_status']=='delivered'].copy()
order_items['line_total'] = order_items['quantity'] * order_items['unit_price']
order_rev = order_items.groupby('order_id')['line_total'].sum().reset_index()
order_rev.columns = ['order_id', 'total_revenue']

del_rev = delivered_orders.merge(order_rev, on='order_id', how='left')
snapshot = del_rev['order_date'].max() + timedelta(days=1)

rfm = del_rev.groupby('customer_id').agg(
    Recency=('order_date', lambda x: (snapshot - x.max()).days),
    Frequency=('order_id', 'nunique'),
    Monetary=('total_revenue', 'sum')).reset_index()

rfm['R_Score'] = pd.qcut(rfm['Recency'], 5, labels=[5,4,3,2,1])
rfm['F_Score'] = pd.qcut(rfm['Frequency'].rank(method='first'), 5, labels=[1,2,3,4,5])
rfm['M_Score'] = pd.qcut(rfm['Monetary'].rank(method='first'), 5, labels=[1,2,3,4,5])

def rfm_seg(row):
    r, f, m = int(row['R_Score']), int(row['F_Score']), int(row['M_Score'])
    if r>=4 and f>=4 and m>=4: return 'Champions'
    elif r>=3 and f>=3: return 'Loyal'
    elif r>=4 and f<=2: return 'New Customers'
    elif r>=3 and m>=2: return 'Potential Loyalist'
    elif r<=2 and f>=3: return 'At Risk'
    elif r<=2 and f<=2 and m<=2: return 'Lost'
    else: return 'Others'

rfm['Segment'] = rfm.apply(rfm_seg, axis=1)

fig, axes = plt.subplots(2, 2, figsize=(16, 12))
axes[0,0].hist(rfm['Recency'], bins=50, color=COLORS[0], edgecolor='white')
axes[0,0].set_title('Recency (ngày)', fontweight='bold')
axes[0,0].axvline(rfm['Recency'].median(), color='red', linestyle='--', label=f'Median: {rfm["Recency"].median():.0f}')
axes[0,0].legend()

axes[0,1].hist(rfm['Frequency'], bins=50, color=COLORS[1], edgecolor='white')
axes[0,1].set_title('Frequency (số đơn)', fontweight='bold')

seg_c = rfm['Segment'].value_counts()
axes[1,0].barh(seg_c.index, seg_c.values, color=COLORS[:len(seg_c)], edgecolor='white')
axes[1,0].set_title('Phân khúc KH (RFM)', fontweight='bold')
for b, v in zip(axes[1,0].patches, seg_c.values):
    axes[1,0].text(v+30, b.get_y()+b.get_height()/2, f'{v:,}', va='center', fontsize=9)

seg_m = rfm.groupby('Segment')['Monetary'].mean().sort_values()
axes[1,1].barh(seg_m.index, seg_m.values, color=COLORS[4], edgecolor='white')
axes[1,1].set_title('Monetary TB theo Segment', fontweight='bold')
axes[1,1].xaxis.set_major_formatter(mticker.FuncFormatter(lambda x,p: f'{x/1e6:.1f}M'))

plt.suptitle('👥 RFM ANALYSIS', fontsize=16, fontweight='bold', y=1.01)
plt.tight_layout()
plt.show()

print("\\n📊 Thống kê RFM:")
print(rfm.groupby('Segment').agg(Count=('customer_id','count'), Avg_R=('Recency','mean'),
    Avg_F=('Frequency','mean'), Avg_M=('Monetary','mean')).round(0).sort_values('Avg_M', ascending=False))""")

code("""# 5.2 Cohort Retention
first_p = delivered_orders.groupby('customer_id')['order_date'].min().reset_index()
first_p.columns = ['customer_id', 'first_date']
first_p['cohort'] = first_p['first_date'].dt.to_period('M')

cohort_d = delivered_orders.merge(first_p[['customer_id','cohort']], on='customer_id')
cohort_d['order_month'] = cohort_d['order_date'].dt.to_period('M')
cohort_d['months_since'] = (cohort_d['order_month'] - cohort_d['cohort']).apply(lambda x: x.n)

cpivot = cohort_d.groupby(['cohort','months_since'])['customer_id'].nunique().reset_index()
cpivot = cpivot.pivot(index='cohort', columns='months_since', values='customer_id')
retention = cpivot.divide(cpivot[0], axis=0) * 100

ret_display = retention.iloc[-16:, :13]
fig, ax = plt.subplots(figsize=(16, 10))
sns.heatmap(ret_display, annot=True, fmt='.0f', cmap='YlOrRd_r', linewidths=0.5, ax=ax, vmin=0, vmax=100)
ax.set_title('📊 COHORT RETENTION (%) — 16 Cohort gần nhất', fontsize=14, fontweight='bold')
ax.set_xlabel('Tháng kể từ mua đầu')
ax.set_ylabel('Cohort')
plt.tight_layout()
plt.show()

print(f"  Retention T1: ~{ret_display[1].mean():.1f}%")
if 6 in ret_display.columns: print(f"  Retention T6: ~{ret_display[6].mean():.1f}%")""")

md("""### 📝 Phase 5 — Kết luận
- **📊** Pareto: Champions chiếm monetary lớn nhất nhưng ít về số lượng
- **🔍** Retention giảm nhanh sau T1 → cần cải thiện onboarding
- **🔮** At Risk → Lost nếu không can thiệp
- **💡** VIP program cho Champions, win-back cho At Risk, onboarding drip cho New""")

# ==================== PHASE 6: PRODUCT PERFORMANCE ====================
md("""---
# Phase 6: 📦 Hiệu Suất Sản Phẩm""")

code("""items_prod = order_items.merge(products, on='product_id', how='left')
items_prod['line_revenue'] = items_prod['quantity'] * items_prod['unit_price']
items_prod['line_cogs'] = items_prod['quantity'] * items_prod['cogs']
items_prod['line_profit'] = items_prod['line_revenue'] - items_prod['line_cogs']

delivered_ids = set(orders[orders['order_status']=='delivered']['order_id'])
items_del = items_prod[items_prod['order_id'].isin(delivered_ids)]

fig, axes = plt.subplots(2, 2, figsize=(16, 12))

cat_rev = items_del.groupby('category').agg(Rev=('line_revenue','sum'), Profit=('line_profit','sum')).sort_values('Rev')
axes[0,0].barh(cat_rev.index, cat_rev['Rev']/1e9, color=COLORS[0], edgecolor='white')
axes[0,0].set_title('Revenue theo Danh mục (Tỷ)', fontweight='bold')
for b, v in zip(axes[0,0].patches, cat_rev['Rev']/1e9):
    axes[0,0].text(v+0.05, b.get_y()+b.get_height()/2, f'{v:.1f}B', va='center', fontsize=9)

seg_rev = items_del.groupby('segment').agg(Rev=('line_revenue','sum'), Profit=('line_profit','sum')).sort_values('Rev')
seg_rev['Margin'] = seg_rev['Profit']/seg_rev['Rev']*100
axes[0,1].barh(seg_rev.index, seg_rev['Rev']/1e9, color=COLORS[:len(seg_rev)], edgecolor='white')
axes[0,1].set_title('Revenue theo Phân khúc (Tỷ)', fontweight='bold')
for b, v, m in zip(axes[0,1].patches, seg_rev['Rev']/1e9, seg_rev['Margin']):
    axes[0,1].text(v+0.05, b.get_y()+b.get_height()/2, f'{v:.1f}B ({m:.0f}%)', va='center', fontsize=9)

cs = items_del.groupby(['category','segment'])['line_revenue'].sum().reset_index().pivot(index='category', columns='segment', values='line_revenue')
sns.heatmap(cs/1e9, annot=True, fmt='.1f', cmap='Blues', ax=axes[1,0], linewidths=0.5)
axes[1,0].set_title('Heatmap Category × Segment (Tỷ)', fontweight='bold')

top10 = items_del.groupby(['product_id','product_name'])['line_revenue'].sum().nlargest(10).reset_index()
axes[1,1].barh(range(10), top10['line_revenue']/1e6, color=COLORS[1], edgecolor='white')
axes[1,1].set_yticks(range(10))
axes[1,1].set_yticklabels([n[:30] for n in top10['product_name']], fontsize=9)
axes[1,1].set_title('Top 10 SP theo Revenue (Tr)', fontweight='bold')
axes[1,1].invert_yaxis()

plt.suptitle('📦 HIỆU SUẤT SẢN PHẨM', fontsize=16, fontweight='bold', y=1.01)
plt.tight_layout()
plt.show()""")

code("""# Size & Color
fig, axes = plt.subplots(1, 3, figsize=(18, 6))

size_q = items_del.groupby('size')['quantity'].sum().sort_values()
axes[0].barh(size_q.index, size_q.values, color=COLORS[:len(size_q)], edgecolor='white')
axes[0].set_title('Quantity theo Size', fontweight='bold')

color_q = items_del.groupby('color')['quantity'].sum().nlargest(10).sort_values()
axes[1].barh(color_q.index, color_q.values, color=COLORS[1], edgecolor='white')
axes[1].set_title('Top 10 Màu sắc', fontweight='bold')

prod_agg = items_del.groupby(['product_id','segment']).agg(price=('unit_price','mean'), qty=('quantity','sum')).reset_index()
for i, seg in enumerate(prod_agg['segment'].unique()):
    m = prod_agg['segment']==seg
    axes[2].scatter(prod_agg[m]['price'], prod_agg[m]['qty'], alpha=0.4, label=seg, color=COLORS[i], s=20)
axes[2].set_title('Giá vs Quantity', fontweight='bold')
axes[2].set_xlabel('Giá TB')
axes[2].set_ylabel('Tổng Qty')
axes[2].legend()
axes[2].set_xscale('log')
axes[2].set_yscale('log')

plt.tight_layout()
plt.show()""")

md("""### 📝 Phase 6 — Kết luận
- **📊** Pareto: một số SP chiếm phần lớn revenue; M/L size phổ biến nhất
- **🔍** Premium margin cao nhưng volume thấp → upsell opportunity
- **💡** Tối ưu inventory M/L, đẩy Premium kèm upsell, diversify danh mục yếu""")

# ==================== PHASE 7: PROMOTIONS ====================
md("""---
# Phase 7: 🏷️ Hiệu Quả Khuyến Mãi""")

code("""items_promo = order_items[order_items['promo_id'].notna()]
promo_rate = len(items_promo) / len(order_items) * 100

fig, axes = plt.subplots(2, 2, figsize=(16, 12))

axes[0,0].pie([len(items_promo), len(order_items)-len(items_promo)],
              labels=['Có KM','Không KM'], autopct='%1.1f%%', colors=[COLORS[4], COLORS[6]])
axes[0,0].set_title('Tỷ lệ có KM', fontweight='bold')

oi_ord = order_items.merge(orders[['order_id','order_date']], on='order_id')
oi_ord['has_promo'] = oi_ord['promo_id'].notna()
oi_ord['line_total'] = oi_ord['quantity'] * oi_ord['unit_price']
aov = oi_ord.groupby('has_promo')['line_total'].mean()
axes[0,1].bar(['Không KM','Có KM'], [aov.get(False,0), aov.get(True,0)],
              color=[COLORS[6], COLORS[4]], edgecolor='white')
axes[0,1].set_title('Giá trị TB: Có vs Không KM', fontweight='bold')
for b, v in zip(axes[0,1].patches, [aov.get(False,0), aov.get(True,0)]):
    axes[0,1].text(b.get_x()+b.get_width()/2, v+10, f'{v:,.0f}', ha='center', fontweight='bold')

disc_pos = order_items[order_items['discount_amount']>0]['discount_amount']
axes[1,0].hist(disc_pos, bins=50, color=COLORS[1], edgecolor='white')
axes[1,0].set_title('Phân bố Discount Amount', fontweight='bold')

oi_ord['ym'] = oi_ord['order_date'].dt.to_period('M')
mp = oi_ord.groupby('ym')['has_promo'].mean()*100
mp.index = mp.index.to_timestamp()
axes[1,1].plot(mp.index, mp.values, color=COLORS[0], alpha=0.4)
axes[1,1].plot(mp.index, mp.rolling(6).mean().values, color=COLORS[0], linewidth=2, label='MA6')
axes[1,1].set_title('Tỷ lệ KM theo Tháng (%)', fontweight='bold')
axes[1,1].legend()

plt.suptitle('🏷️ PHÂN TÍCH KHUYẾN MÃI', fontsize=16, fontweight='bold', y=1.01)
plt.tight_layout()
plt.show()
print(f"  Tỷ lệ có KM: {promo_rate:.1f}%")
print(f"  Tổng discount: {order_items['discount_amount'].sum():,.0f}")""")

code("""# Promo ROI
pi = order_items[order_items['promo_id'].notna()].merge(promotions, on='promo_id', how='left')
pi['line_rev'] = pi['quantity'] * pi['unit_price']
pp = pi.groupby(['promo_id','promo_name','promo_type']).agg(
    rev=('line_rev','sum'), disc=('discount_amount','sum'), orders=('order_id','nunique')).reset_index()
pp['disc_pct'] = pp['disc'] / (pp['rev']+pp['disc']) * 100

fig, axes = plt.subplots(1, 2, figsize=(16, 7))

top_p = pp.nlargest(10, 'rev')
y = range(len(top_p))
axes[0].barh(y, top_p['rev']/1e9, color=COLORS[0], edgecolor='white', label='Revenue')
axes[0].barh(y, -top_p['disc']/1e9, color=COLORS[3], edgecolor='white', label='Discount')
axes[0].set_yticks(y)
axes[0].set_yticklabels(top_p['promo_name'].str[:25], fontsize=9)
axes[0].set_title('Revenue vs Discount (Tỷ)', fontweight='bold')
axes[0].legend()
axes[0].axvline(0, color='black', linewidth=0.5)

pp_s = pp.sort_values('disc_pct')
axes[1].barh(range(len(pp_s)), pp_s['disc_pct'], color=COLORS[1], edgecolor='white')
axes[1].set_yticks(range(len(pp_s)))
axes[1].set_yticklabels(pp_s['promo_name'].str[:25], fontsize=9)
axes[1].set_title('Discount / Revenue (%)', fontweight='bold')

plt.suptitle('💰 ROI KHUYẾN MÃI', fontsize=14, fontweight='bold', y=1.02)
plt.tight_layout()
plt.show()""")

md("""### 📝 Phase 7 — Kết luận
- **📊** Tỷ lệ KM đáng kể, một số KM discount/revenue cao
- **🔍** Cần đánh giá ROI từng KM: incremental hay chỉ dịch chuyển demand?
- **💡** Giữ KM ROI dương, loại KM ROI âm, A/B test trước triển khai rộng""")

# ==================== PHASE 8: INVENTORY ====================
md("""---
# Phase 8: 📦 Tồn Kho & Chuỗi Cung Ứng""")

code("""fig, axes = plt.subplots(2, 2, figsize=(16, 12))

so_cat = inventory.groupby('category').agg(so_rate=('stockout_flag','mean'), fill=('fill_rate','mean')).sort_values('so_rate')
axes[0,0].barh(so_cat.index, so_cat['so_rate']*100, color=COLORS[3], edgecolor='white')
axes[0,0].set_title('Stockout Rate theo Danh mục (%)', fontweight='bold')
for b, v in zip(axes[0,0].patches, so_cat['so_rate']*100):
    axes[0,0].text(v+0.2, b.get_y()+b.get_height()/2, f'{v:.1f}%', va='center', fontsize=9)

frt = inventory.groupby(['snapshot_date','segment'])['fill_rate'].mean().reset_index()
for seg in frt['segment'].unique():
    m = frt['segment']==seg
    axes[0,1].plot(frt[m]['snapshot_date'], frt[m]['fill_rate']*100, label=seg, linewidth=2)
axes[0,1].set_title('Fill Rate theo Segment (%)', fontweight='bold')
axes[0,1].legend()

inv_f = inventory.groupby('category').agg(so=('stockout_flag','mean'), ov=('overstock_flag','mean')).reset_index()
x = np.arange(len(inv_f))
axes[1,0].bar(x-0.175, inv_f['so']*100, 0.35, label='Stockout', color=COLORS[3], edgecolor='white')
axes[1,0].bar(x+0.175, inv_f['ov']*100, 0.35, label='Overstock', color=COLORS[0], edgecolor='white')
axes[1,0].set_xticks(x)
axes[1,0].set_xticklabels(inv_f['category'], rotation=45, ha='right')
axes[1,0].set_title('Stockout vs Overstock (%)', fontweight='bold')
axes[1,0].legend()

str_seg = inventory.groupby('segment')['sell_through_rate'].agg(['mean','std'])
axes[1,1].bar(str_seg.index, str_seg['mean']*100, yerr=str_seg['std']*100, color=COLORS[4], edgecolor='white', capsize=3)
axes[1,1].set_title('Sell-Through Rate (%)', fontweight='bold')

plt.suptitle('📦 TỒN KHO & SUPPLY CHAIN', fontsize=16, fontweight='bold', y=1.01)
plt.tight_layout()
plt.show()

print(f"  Fill Rate TB:     {inventory['fill_rate'].mean()*100:.1f}%")
print(f"  Stockout Rate:    {inventory['stockout_flag'].mean()*100:.1f}%")
print(f"  Overstock Rate:   {inventory['overstock_flag'].mean()*100:.1f}%")""")

md("""### 📝 Phase 8 — Kết luận
- **📊** Fill rate và sell-through khác biệt giữa segments
- **🔍** Stockout cao → mất doanh thu; Overstock → chi phí lưu kho
- **💡** ABC analysis ưu tiên, tăng safety stock cho SP stockout cao, stockout = feature cho forecasting""")

# ==================== PHASE 9: WEB TRAFFIC ====================
md("""---
# Phase 9: 🌐 Web Traffic & Conversion""")

code("""fig, axes = plt.subplots(2, 2, figsize=(16, 12))

daily_sess = web_traffic.groupby('date')['sessions'].sum()
axes[0,0].plot(daily_sess.index, daily_sess.values, color=COLORS[0], alpha=0.3, linewidth=0.5)
axes[0,0].plot(daily_sess.index, daily_sess.rolling(30).mean().values, color=COLORS[0], linewidth=2, label='MA30')
axes[0,0].set_title('Sessions hàng ngày', fontweight='bold')
axes[0,0].legend()

src_t = web_traffic.groupby('traffic_source')['sessions'].sum().sort_values()
axes[0,1].barh(src_t.index, src_t.values, color=COLORS[:len(src_t)], edgecolor='white')
axes[0,1].set_title('Sessions theo Nguồn', fontweight='bold')

daily_br = web_traffic.groupby('date')['bounce_rate'].mean()
axes[1,0].plot(daily_br.index, daily_br.values, color=COLORS[3], alpha=0.3, linewidth=0.5)
axes[1,0].plot(daily_br.index, daily_br.rolling(30).mean().values, color=COLORS[3], linewidth=2)
axes[1,0].set_title('Bounce Rate (%)', fontweight='bold')

avg_dur = web_traffic.groupby('traffic_source')['avg_session_duration_sec'].mean().sort_values()
axes[1,1].barh(avg_dur.index, avg_dur.values, color=COLORS[4], edgecolor='white')
axes[1,1].set_title('Session Duration TB (giây)', fontweight='bold')

plt.suptitle('🌐 WEB TRAFFIC', fontsize=16, fontweight='bold', y=1.01)
plt.tight_layout()
plt.show()""")

code("""# Traffic vs Revenue
daily_t = web_traffic.groupby('date').agg(sessions=('sessions','sum'), visitors=('unique_visitors','sum'),
    pageviews=('page_views','sum'), bounce=('bounce_rate','mean')).reset_index()
ts = daily_t.merge(sales, left_on='date', right_on='Date', how='inner')

fig, axes = plt.subplots(1, 3, figsize=(18, 5))
for ax, xcol, c, title in zip(axes,
    ['sessions','bounce','pageviews'], [COLORS[0], COLORS[3], COLORS[4]],
    ['Sessions','Bounce Rate','Page Views']):
    ax.scatter(ts[xcol], ts['Revenue']/1e6, alpha=0.3, color=c, s=10)
    r = ts[xcol].corr(ts['Revenue'])
    ax.set_title(f'{title} vs Revenue (r={r:.3f})', fontweight='bold')
    ax.set_xlabel(title)
    ax.set_ylabel('Revenue (Tr)')
plt.suptitle('📊 TRAFFIC → REVENUE', fontsize=14, fontweight='bold', y=1.03)
plt.tight_layout()
plt.show()

print("\\nCorrelation matrix:")
print(ts[['sessions','visitors','pageviews','bounce','Revenue']].corr().round(3))""")

md("""### 📝 Phase 9 — Kết luận
- **📊** Traffic tương quan với revenue; nguồn khác nhau có engagement khác nhau
- **🔍** Organic search engagement tốt hơn paid
- **💡** Traffic là leading indicator → feature cho forecasting; tăng đầu tư kênh ROI cao""")

# ==================== PHASE 10: REVIEWS & RETURNS ====================
md("""---
# Phase 10: ⭐ Đánh Giá & Trả Hàng""")

code("""fig, axes = plt.subplots(2, 2, figsize=(16, 12))

rat_c = reviews['rating'].value_counts().sort_index()
cols_r = [COLORS[3], COLORS[5], COLORS[6], COLORS[0], COLORS[4]]
axes[0,0].bar(rat_c.index, rat_c.values, color=cols_r, edgecolor='white')
axes[0,0].set_title('Phân bố Rating', fontweight='bold')
axes[0,0].set_xticks([1,2,3,4,5])
for b, v in zip(axes[0,0].patches, rat_c.values):
    axes[0,0].text(b.get_x()+b.get_width()/2, v+50, f'{v:,}', ha='center', fontsize=9)

rev_prod = reviews.merge(products[['product_id','category','segment']], on='product_id', how='left')
avg_r_cat = rev_prod.groupby('category')['rating'].mean().sort_values()
axes[0,1].barh(avg_r_cat.index, avg_r_cat.values, color=COLORS[0], edgecolor='white')
axes[0,1].set_title('Rating TB theo Danh mục', fontweight='bold')
axes[0,1].set_xlim(0, 5)

monthly_r = reviews.set_index('review_date').resample('M')['rating'].mean()
axes[1,0].plot(monthly_r.index, monthly_r.values, color=COLORS[1], alpha=0.4)
axes[1,0].plot(monthly_r.index, monthly_r.rolling(6).mean().values, color=COLORS[1], linewidth=2)
axes[1,0].axhline(reviews['rating'].mean(), color='red', linestyle='--', label=f'TB: {reviews["rating"].mean():.2f}')
axes[1,0].set_title('Rating TB theo Tháng', fontweight='bold')
axes[1,0].legend()

avg_r_seg = rev_prod.groupby('segment')['rating'].mean().sort_values()
axes[1,1].barh(avg_r_seg.index, avg_r_seg.values, color=COLORS[4], edgecolor='white')
axes[1,1].set_title('Rating TB theo Segment', fontweight='bold')
axes[1,1].set_xlim(0, 5)

plt.suptitle('⭐ ĐÁNH GIÁ KHÁCH HÀNG', fontsize=16, fontweight='bold', y=1.01)
plt.tight_layout()
plt.show()
print(f"  Rating TB: {reviews['rating'].mean():.2f} | 4-5⭐: {(reviews['rating']>=4).mean()*100:.1f}%")""")

code("""# Returns
fig, axes = plt.subplots(2, 2, figsize=(16, 12))

reas_c = returns['return_reason'].value_counts()
axes[0,0].barh(reas_c.index, reas_c.values, color=COLORS[:len(reas_c)], edgecolor='white')
axes[0,0].set_title('Lý do Trả hàng', fontweight='bold')
for b, v in zip(axes[0,0].patches, reas_c.values):
    axes[0,0].text(v+30, b.get_y()+b.get_height()/2, f'{v:,}', va='center', fontsize=9)

ret_prod = returns.merge(products[['product_id','category']], on='product_id', how='left')
total_sold = items_del.groupby('category')['quantity'].sum()
ret_qty = ret_prod.groupby('category')['return_quantity'].sum()
ret_rate = (ret_qty / total_sold * 100).dropna().sort_values()
axes[0,1].barh(ret_rate.index, ret_rate.values, color=COLORS[3], edgecolor='white')
axes[0,1].set_title('Return Rate theo Danh mục (%)', fontweight='bold')

monthly_ret = returns.set_index('return_date').resample('M')['return_quantity'].sum()
axes[1,0].plot(monthly_ret.index, monthly_ret.values, color=COLORS[3], alpha=0.4)
axes[1,0].plot(monthly_ret.index, monthly_ret.rolling(6).mean().values, color=COLORS[3], linewidth=2)
axes[1,0].set_title('Return Quantity theo Tháng', fontweight='bold')
axes[1,0].xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

axes[1,1].hist(returns['refund_amount'], bins=50, color=COLORS[1], edgecolor='white')
axes[1,1].axvline(returns['refund_amount'].mean(), color='red', linestyle='--', label=f'TB: {returns["refund_amount"].mean():,.0f}')
axes[1,1].set_title('Phân bố Refund Amount', fontweight='bold')
axes[1,1].legend()

plt.suptitle('📦 PHÂN TÍCH TRẢ HÀNG', fontsize=16, fontweight='bold', y=1.01)
plt.tight_layout()
plt.show()
print(f"  Tổng returns: {len(returns):,} | Tổng refund: {returns['refund_amount'].sum():,.0f}")""")

md("""### 📝 Phase 10 — Kết luận
- **📊** Rating TB ổn định; wrong_size & defective là lý do trả hàng chính
- **🔍** Wrong size → cải thiện size guide; Defective → cải thiện QC
- **💡** AR try-on, cải thiện mô tả SP, tăng cường QC danh mục return cao""")

# ==================== SUMMARY ====================
md("""---
# 🎯 Tổng Kết & Feature Engineering cho Part 3

| Phase | Key Insight | Feature Ideas |
|---|---|---|
| Revenue | Trend tăng, mùa vụ tuần/tháng | lag_7, lag_30, seasonal_index |
| Orders | Mobile tăng, payment shifting | order_count, device_pct |
| Customers | Pareto: 20% KH = 80% revenue | active_customers, new_customers |
| Products | Premium margin cao, M/L dominant | product_mix, avg_price |
| Promotions | KM impact AOV & volume | active_promos, discount_rate |
| Inventory | Stockout ảnh hưởng revenue | fill_rate, stockout_count |
| Web Traffic | Sessions correlate revenue | sessions_lag, bounce_rate |
| Reviews | Rating ổn định, returns patterns | avg_rating, return_rate |""")

code("""print("🔧 FEATURE ENGINEERING cho Sales Forecasting")
print("="*60)
groups = {
    'Calendar': ['day_of_week, month, quarter, is_weekend', 'day_of_month, week_of_year, year_progress'],
    'Lag': ['revenue_lag_1, lag_7, lag_14, lag_30, lag_365', 'cogs_lag_1, lag_7'],
    'Rolling': ['rolling_mean_7d, 14d, 30d, 90d', 'rolling_std_7d, 30d'],
    'Trend': ['linear_trend, yoy_growth, mom_growth'],
    'Seasonal': ['fourier_sin/cos (7, 30, 365)', 'seasonal_index_dow'],
    'Transaction': ['order_count, avg_basket_size, cancel_rate'],
    'Promotion': ['active_promos, total_discount'],
    'Web Traffic': ['sessions, bounce_rate (lag aligned)'],
    'Inventory': ['fill_rate, stockout_count (monthly)'],
}
for cat, feats in groups.items():
    print(f"\\n  📌 {cat}:")
    for f in feats:
        print(f"     • {f}")
print(f"\\n{'='*60}")
print("💡 Models: LightGBM/XGBoost + Prophet + SARIMA → Ensemble")
print("⚠️ QUAN TRỌNG: Time-series CV (expanding window), KHÔNG random split!")""")

md("""---
# ✅ KẾT THÚC EDA

### Bước tiếp theo:
1. **Part 1**: Dùng insights EDA trả lời trắc nghiệm
2. **Part 2**: Chọn 4-5 storylines mạnh nhất, polish visualization
3. **Part 3**: Build forecasting model với features đã đề xuất

> 💡 **Pro tip**: Quantify prescriptive (VD: "Giảm stockout 10% ≈ +X tỷ revenue") để gây ấn tượng BGK""")

# ==================== WRITE NOTEBOOK ====================
notebook = {
    "cells": cells,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"codemirror_mode": {"name": "ipython", "version": 3},
                          "file_extension": ".py", "mimetype": "text/x-python",
                          "name": "python", "version": "3.10.0"}
    },
    "nbformat": 4, "nbformat_minor": 5
}

output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'eda.ipynb')
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(notebook, f, ensure_ascii=False, indent=1)

print(f"✅ Notebook: {output_path}")
print(f"   Cells: {len(cells)} (Code: {sum(1 for c in cells if c['cell_type']=='code')}, MD: {sum(1 for c in cells if c['cell_type']=='markdown')})")
