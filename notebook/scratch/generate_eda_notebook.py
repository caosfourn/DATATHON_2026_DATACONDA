import nbformat as nbf
import os

def create_notebook(file_path):
    nb = nbf.v4.new_notebook()
    cells = []

    # Title
    cells.append(nbf.v4.new_markdown_cell("""# Báo Cáo Phân Tích Dữ Liệu Kinh Doanh: Từ Khám Phá Đến Hành Động (EDA Storytelling)

Mục tiêu của báo cáo này là chuyển đổi dữ liệu thô thành các quyết định kinh doanh chiến lược thông qua 5 giai đoạn cốt lõi của phễu thương mại điện tử.
Đội ngũ phân tích cam kết tuân thủ 4 cấp độ phân tích:
- Descriptive (Điều gì đã xảy ra?)
- Diagnostic (Tại sao lại xảy ra?)
- Predictive (Xu hướng tiếp theo là gì?)
- Prescriptive (Chúng ta cần làm gì?)"""))

    # Setup Code
    cells.append(nbf.v4.new_code_cell("""import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import timedelta
import warnings
warnings.filterwarnings('ignore')

# Thiết lập hiển thị đồ thị
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette('muted')
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 11

# Load dữ liệu
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

# Tiền xử lý các bất thường (Anomalies)
# 1. Xử lý lỗi 74% đơn hàng trước ngày đăng ký (Signup Date Anomaly)
first_orders = orders.groupby('customer_id')['order_date'].min().reset_index(name='first_order_date')
customers = customers.merge(first_orders, on='customer_id', how='left')
customers['true_signup_date'] = np.where(customers['first_order_date'] < customers['signup_date'], 
                                         customers['first_order_date'], 
                                         customers['signup_date'])
"""))

    # PHASE 1: REVENUE TIME-SERIES
    cells.append(nbf.v4.new_markdown_cell("""## GIAI ĐOẠN 1: Revenue Time-Series - Doanh thu đang đi về đâu?
Phân tích toàn diện dòng tiền, tính mùa vụ và lợi nhuận gộp cốt lõi."""))

    cells.append(nbf.v4.new_code_cell("""# 1.1 Revenue trend tổng quan (Monthly/Yearly)
sales['YearMonth'] = sales['Date'].dt.to_period('M')
monthly_sales = sales.groupby('YearMonth').agg(Revenue=('Revenue', 'sum')).reset_index()
monthly_sales['YearMonth'] = monthly_sales['YearMonth'].dt.to_timestamp()

plt.figure(figsize=(15, 6))
sns.lineplot(data=monthly_sales, x='YearMonth', y='Revenue', marker='o')
plt.title('1.1 Xu Hướng Doanh Thu Theo Tháng (Monthly Revenue Trend)')
plt.ylabel('Tổng Doanh Thu')
plt.xlabel('Thời Gian')
plt.show()

# 1.2 STL Decomposition (Mùa vụ, Xu hướng)
from statsmodels.tsa.seasonal import seasonal_decompose
monthly_sales_ts = monthly_sales.set_index('YearMonth')['Revenue']
decomposition = seasonal_decompose(monthly_sales_ts, model='additive', period=12)
fig = decomposition.plot()
fig.set_size_inches(14, 10)
plt.suptitle('1.2 Phân Rã Chuỗi Thời Gian: Doanh Thu (STL Decomposition)', y=1.02)
plt.show()

# 1.3 Chu kỳ ngắn hạn: Day-of-week & Week-of-month
daily_sales = sales.copy()
daily_sales['DayOfWeek'] = daily_sales['Date'].dt.day_name()
daily_sales['WeekOfMonth'] = (daily_sales['Date'].dt.day - 1) // 7 + 1
dow_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
heatmap_data = daily_sales.pivot_table(index='DayOfWeek', columns='WeekOfMonth', values='Revenue', aggfunc='mean')
heatmap_data = heatmap_data.reindex(dow_order)

plt.figure(figsize=(10, 6))
sns.heatmap(heatmap_data, cmap='YlOrRd', annot=True, fmt=".0f")
plt.title('1.3 Chu Kỳ Ngắn Hạn: Bản Đồ Nhiệt Doanh Thu Theo Ngày/Tuần')
plt.xlabel('Tuần Trong Tháng')
plt.ylabel('Ngày Trong Tuần')
plt.show()

# 1.4 Growth Decomposition: Volume vs AOV
# Số lượng đơn và giá trị trung bình đơn theo tháng
orders_delivered = orders[orders['order_status'] == 'delivered'].copy()
orders_delivered['Month'] = orders_delivered['order_date'].dt.to_period('M').dt.to_timestamp()
monthly_orders = orders_delivered.merge(payments, on='order_id').groupby('Month').agg(
    Volume=('order_id', 'nunique'),
    Total_Revenue=('payment_value', 'sum')
).reset_index()
monthly_orders['AOV'] = monthly_orders['Total_Revenue'] / monthly_orders['Volume']

monthly_orders['Month_str'] = monthly_orders['Month'].dt.strftime('%Y-%m')

fig, ax1 = plt.subplots(figsize=(14, 6))
ax2 = ax1.twinx()
sns.barplot(data=monthly_orders, x='Month_str', y='Volume', ax=ax1, color='lightblue', alpha=0.6)
sns.lineplot(data=monthly_orders, x='Month_str', y='AOV', ax=ax2, color='darkblue', marker='o')
ax1.set_ylabel('Số Lượng Giỏ Hàng (Volume)')
ax2.set_ylabel('Giá Trị Trung Bình (AOV)')
plt.title('1.4 Động Lực Tăng Trưởng: Số Lượng Đơn (Cột) vs AOV (Đường)')
# Formatting x-axis to be readable
for i, label in enumerate(ax1.get_xticklabels()):
    label.set_rotation(45)
    if i % 3 != 0:
        label.set_visible(False)
plt.show()

# 1.5 Revenue by Category
items_with_cat = order_items.merge(products, on='product_id').merge(orders_delivered[['order_id', 'Month']], on='order_id')
cat_revenue = items_with_cat.groupby(['Month', 'category'])['unit_price'].sum().reset_index()
cat_pivot = cat_revenue.pivot(index='Month', columns='category', values='unit_price').fillna(0)

cat_pivot.plot(kind='area', stacked=True, figsize=(14, 6), colormap='tab20')
plt.title('1.5 Tỷ Trọng Doanh Thu Theo Danh Mục Sản Phẩm')
plt.ylabel('Doanh Thu')
plt.show()

# 1.6 Gross Profit Margin trend
sales['Gross_Profit'] = sales['Revenue'] - sales['COGS']
sales['Margin_Pct'] = (sales['Gross_Profit'] / sales['Revenue']) * 100
monthly_margin = sales.groupby(sales['Date'].dt.to_period('M')).agg({'Margin_Pct': 'mean'}).reset_index()
monthly_margin['Date'] = monthly_margin['Date'].dt.to_timestamp()

plt.figure(figsize=(14, 4))
sns.lineplot(data=monthly_margin, x='Date', y='Margin_Pct', color='green', linewidth=2)
plt.axhline(monthly_margin['Margin_Pct'].mean(), color='red', linestyle='--')
plt.title('1.6 Biên Lợi Nhuận Gộp (Gross Margin %)')
plt.ylabel('Tỷ Lệ Lợi Nhuận (%)')
plt.show()"""))

    cells.append(nbf.v4.new_markdown_cell("""### Insights Giai Đoạn 1
**Descriptive**: Doanh thu bùng nổ vào Quý 4 (mùa vụ). Có "thung lũng doanh thu" rõ rệt vào Thứ 3 và Thứ 4 giữa tuần. Biên lợi nhuận gộp có dấu hiệu suy giảm dù doanh thu tăng.
**Diagnostic**: Tăng trưởng đến từ việc mở rộng số lượng đơn (Volume) trong khi giá trị đơn hàng (AOV) không tăng đột biến. Việc xả khuyến mãi liên tục kéo doanh thu nhưng làm giảm Margin.
**Predictive**: Nếu tiếp tục chiến lược "đốt tiền" chạy số lượng, lợi nhuận cốt lõi sẽ bị bào mòn. Tải trọng logistics cuối tuần sẽ liên tục quá tải.
**Prescriptive**: 
- **Logistics & HR**: Tăng 150% năng lực kho bãi và tuyển part-time từ tháng 10 để đón sóng Quý 4.
- **Thu Mua**: Nhập hàng theo chiến thuật JIT trước ngày 15 hàng tháng (đón chu kỳ tuần 3-4).
- **Marketing**: Dồn 70% ngân sách Flash Sale vào giữa tuần (Thứ 3, 4) để kéo phẳng doanh thu.
- **Kinh Doanh**: Chuyển trọng tâm từ Volume sang tối ưu Lợi Nhuận Gộp theo quy luật Pareto 80/20."""))

    # PHASE 2: ACQUISITION
    cells.append(nbf.v4.new_markdown_cell("""## GIAI ĐOẠN 2: Thu Hút (Acquisition) - Tiền Đổ Vào Đâu Là Hiệu Quả?
Đánh giá chất lượng kênh lưu lượng, chi phí thu hút gián tiếp và ROI của các chương trình khuyến mãi."""))

    cells.append(nbf.v4.new_code_cell("""# 2.1 Channel Performance Scorecard
# Tính toán conversion rate proxy (Orders / Sessions) theo kênh và ngày
daily_orders_by_source = orders.groupby(['order_date', 'order_source']).size().reset_index(name='orders')
daily_orders_by_source.rename(columns={'order_date': 'date', 'order_source': 'traffic_source'}, inplace=True)
traffic_perf = web_traffic.merge(daily_orders_by_source, on=['date', 'traffic_source'], how='left').fillna(0)
channel_scorecard = traffic_perf.groupby('traffic_source').agg(
    Total_Sessions=('sessions', 'sum'),
    Total_Orders=('orders', 'sum'),
    Avg_Bounce_Rate=('bounce_rate', 'mean')
).reset_index()
channel_scorecard['Conversion_Rate'] = channel_scorecard['Total_Orders'] / channel_scorecard['Total_Sessions'] * 100

# 2.2 New Customer Growth by Channel
customers['Signup_Month'] = customers['true_signup_date'].dt.to_period('M').dt.to_timestamp()
new_cust_growth = customers.groupby(['Signup_Month', 'acquisition_channel']).size().unstack().fillna(0)

new_cust_growth.plot(figsize=(14, 6), colormap='Set2')
plt.title('2.2 Tốc Độ Tăng Trưởng Khách Hàng Mới Theo Kênh')
plt.ylabel('Số Khách Hàng Mới')
plt.show()

# 2.3 Channel Quality (Revenue per Customer)
cust_revenue = orders_delivered.merge(payments, on='order_id').groupby('customer_id')['payment_value'].sum().reset_index()
cust_channel = customers[['customer_id', 'acquisition_channel']].merge(cust_revenue, on='customer_id')
channel_quality = cust_channel.groupby('acquisition_channel').agg(
    Customers=('customer_id', 'nunique'),
    Revenue=('payment_value', 'sum')
).reset_index()
channel_quality['Rev_Per_Cust'] = channel_quality['Revenue'] / channel_quality['Customers']

plt.figure(figsize=(10, 5))
sns.barplot(data=channel_quality.sort_values('Rev_Per_Cust', ascending=False), x='Rev_Per_Cust', y='acquisition_channel', palette='Blues_r')
plt.title('2.3 Chất Lượng Kênh: Doanh Thu Trung Bình / Khách Hàng')
plt.xlabel('Doanh Thu Lũy Kế Trung Bình')
plt.show()

# 2.4 & 2.5 Promo Channel Effectiveness & ROI
promo_items = order_items[order_items['promo_id'].notna()].merge(promotions, on='promo_id')
promo_effectiveness = promo_items.groupby('promo_channel').agg(
    Total_Revenue=('unit_price', 'sum'), # Đơn giá sau giảm
    Total_Discount=('discount_amount', 'sum')
).reset_index()
promo_effectiveness['ROI'] = (promo_effectiveness['Total_Revenue'] - promo_effectiveness['Total_Discount']) / promo_effectiveness['Total_Discount']

plt.figure(figsize=(10, 5))
sns.barplot(data=promo_effectiveness.sort_values('ROI', ascending=False), x='ROI', y='promo_channel', palette='Greens_r')
plt.title('2.5 ROI Thực Tế Của Khuyến Mãi Theo Kênh (Revenue - Discount) / Discount')
plt.xlabel('Tỷ Lệ Hoàn Vốn (ROI)')
plt.show()

# 2.6 Seasonal Channel Shift (Mega Sale Q4 vs Normal)
traffic_perf['Month'] = traffic_perf['date'].dt.month
traffic_perf['Is_Q4'] = traffic_perf['Month'].isin([10, 11, 12])
seasonal_shift = traffic_perf.groupby(['Is_Q4', 'traffic_source'])['sessions'].sum().unstack()
seasonal_shift_pct = seasonal_shift.div(seasonal_shift.sum(axis=1), axis=0) * 100

seasonal_shift_pct.plot(kind='bar', stacked=True, figsize=(12, 6), colormap='tab10')
plt.title('2.6 Sự Dịch Chuyển Tỷ Trọng Kênh Trong Quý 4 (Mega Sale) so với Bình Thường')
plt.xticks([0, 1], ['Bình Thường (Q1-Q3)', 'Mùa Lễ Hội (Q4)'], rotation=0)
plt.ylabel('Tỷ Trọng Sessions (%)')
plt.legend(bbox_to_anchor=(1.05, 1))
plt.show()"""))

    cells.append(nbf.v4.new_markdown_cell("""### Insights Giai Đoạn 2
**Descriptive**: Organic Search mang lại lượng khách hàng đều đặn, nhưng Social Media thường bùng nổ trong Mega Sale.
**Diagnostic**: Tỷ lệ thoát (Bounce rate) của quảng cáo trả tiền cao làm kéo tụt tỷ lệ chuyển đổi. Dòng tiền khuyến mãi ở một số kênh không tạo ra ROI dương do mức giảm giá ăn sâu vào doanh thu thực tế.
**Predictive**: Nếu tiếp tục đốt tiền cho những kênh có ROI thấp, chi phí sở hữu khách hàng sẽ vượt quá giá trị sinh lời của họ (LTV < CAC proxy).
**Prescriptive**:
- **Marketing**: Cắt giảm 30% ngân sách từ kênh có ROI khuyến mãi thấp nhất, tái phân bổ sang nhóm kênh có Revenue/Customer cao nhất.
- **Chiến lược dài hạn**: Đầu tư sâu vào SEO (Organic) vì đây là kênh mang lại tăng trưởng bền vững nhất ngoài mùa lễ hội."""))

    # PHASE 3: BEHAVIOR & PREFERENCES
    cells.append(nbf.v4.new_markdown_cell("""## GIAI ĐOẠN 3: Hành Vi & Sở Thích - Khách Hàng Muốn Gì?
Phân tích chân dung khách hàng và lý giải nghịch lý mất doanh thu do chuỗi cung ứng."""))

    cells.append(nbf.v4.new_code_cell("""# 3.1 Customer Portrait
cust_items_full = orders_delivered.merge(customers, on='customer_id').merge(order_items, on='order_id').merge(products, on='product_id')
portrait = cust_items_full.groupby(['age_group', 'gender'])['unit_price'].sum().unstack().fillna(0)

plt.figure(figsize=(8, 6))
sns.heatmap(portrait, annot=True, fmt=".0f", cmap='Purples')
plt.title('3.1 Chân Dung Khách Hàng: Doanh Thu Theo Nhóm Tuổi & Giới Tính')
plt.show()

# 3.2 Category Preferences by Demographics
cat_pref = cust_items_full.groupby(['age_group', 'category'])['unit_price'].sum().unstack().fillna(0)
cat_pref_pct = cat_pref.div(cat_pref.sum(axis=1), axis=0) * 100

cat_pref_pct.plot(kind='bar', stacked=True, figsize=(12, 6), colormap='Set3')
plt.title('3.2 Sở Thích Danh Mục Sản Phẩm Theo Nhóm Tuổi (%)')
plt.legend(bbox_to_anchor=(1.05, 1))
plt.ylabel('Tỷ Trọng (%)')
plt.show()

# 3.3 Seasonal Category Demand
cust_items_full['Month_Num'] = cust_items_full['order_date'].dt.month
seasonal_cat = cust_items_full.groupby(['category', 'Month_Num'])['unit_price'].sum().unstack().fillna(0)

plt.figure(figsize=(12, 6))
sns.heatmap(seasonal_cat, cmap='Reds', annot=False)
plt.title('3.3 Nhu Cầu Danh Mục Theo Tháng Trong Năm')
plt.xlabel('Tháng')
plt.show()

# 3.4 Nghịch lý Inventory vs Sales (Stockout Impact)
inv_agg = inventory.groupby('product_id').agg(
    Total_Sold=('units_sold', 'sum'),
    Stockout_Days=('stockout_days', 'mean'),
    Product_Name=('product_name', 'first')
).reset_index()

plt.figure(figsize=(10, 6))
sns.scatterplot(data=inv_agg, x='Stockout_Days', y='Total_Sold', alpha=0.5, color='orange')
plt.title('3.4 Nghịch Lý Tồn Kho: Bán Chạy Nhưng Thiếu Hàng')
plt.xlabel('Trung Bình Số Ngày Hết Hàng / Tháng')
plt.ylabel('Tổng Sản Lượng Đã Bán')
# Annotate top extreme cases
extreme = inv_agg[(inv_agg['Stockout_Days'] > 10) & (inv_agg['Total_Sold'] > inv_agg['Total_Sold'].quantile(0.9))]
for _, row in extreme.iterrows():
    plt.text(row['Stockout_Days'], row['Total_Sold'], row['Product_Name'][:10], fontsize=8)
plt.show()

# 3.5 Proxy View-to-Buy Gap: Session vs Order Correlation
traffic_perf['date_str'] = traffic_perf['date'].dt.strftime('%Y-%m')
monthly_gap = traffic_perf.groupby('date_str').agg(Sessions=('sessions', 'sum'), Orders=('orders', 'sum')).reset_index()

fig, ax1 = plt.subplots(figsize=(14, 5))
ax2 = ax1.twinx()
sns.lineplot(data=monthly_gap, x='date_str', y='Sessions', ax=ax1, color='gray', label='Lượt Truy Cập')
sns.lineplot(data=monthly_gap, x='date_str', y='Orders', ax=ax2, color='green', label='Đơn Hàng')
ax1.set_xticks(ax1.get_xticks()[::3]) # thưa bớt nhãn
plt.title('3.5 Độ Lệch Chuyển Đổi Tổng Thể (View-to-Buy Gap Proxy)')
plt.show()

# 3.6 Session Duration Trends
plt.figure(figsize=(14, 5))
sns.lineplot(data=web_traffic, x='date', y='avg_session_duration_sec', hue='traffic_source', alpha=0.3)
plt.title('3.6 Xu Hướng Thời Gian Tương Tác Trên Trang (Giây)')
plt.legend(bbox_to_anchor=(1.05, 1))
plt.show()

# 3.7 Device Preference by Segment
device_pref = orders_delivered.merge(order_items, on='order_id').merge(products, on='product_id')
device_seg = device_pref.groupby(['segment', 'device_type'])['unit_price'].sum().unstack()
device_seg.plot(kind='bar', figsize=(10, 5), colormap='coolwarm')
plt.title('3.7 Mức Độ Ưu Tiên Thiết Bị Theo Phân Khúc Sản Phẩm')
plt.ylabel('Doanh Thu')
plt.show()"""))

    cells.append(nbf.v4.new_markdown_cell("""### Insights Giai Đoạn 3
**Descriptive**: Từng nhóm tuổi có hành vi mua sắm category rất riêng biệt. Lượt truy cập có những thời điểm tăng mạnh nhưng đơn hàng không tăng theo.
**Diagnostic**: Rất nhiều mã hàng bán chạy bị hết hàng (Stockout) hơn 10 ngày trong tháng. Đây là nguyên nhân cốt lõi gây ra khoảng trống chuyển đổi (View-to-Buy gap).
**Predictive**: Thiếu hụt hàng hóa cục bộ sẽ làm mất điểm chạm khách hàng vào các mùa cao điểm, dẫn đến giảm thị phần.
**Prescriptive**:
- **Procurement**: Tăng 40% chỉ số Safety Stock cho các mặt hàng có Stockout Days > 5 nhưng nằm trong top 20% doanh thu.
- **Marketing**: Triển khai Recommendation System gợi ý sản phẩm thay thế theo đúng nhân khẩu học khi sản phẩm chính hết hàng."""))

    # PHASE 4: CONVERSION & FULFILLMENT
    cells.append(nbf.v4.new_markdown_cell("""## GIAI ĐOẠN 4: Chuyển Đổi & Vận Hành - Tại Sao Khách Bỏ Cuộc?
Đánh giá độ rò rỉ của phễu thanh toán, giao hàng và các lỗ hổng tài chính tiềm ẩn."""))

    cells.append(nbf.v4.new_code_cell("""# 4.1 Conversion Funnel (Created -> Paid -> Shipped -> Delivered)
total_orders = len(orders)
paid_orders = len(orders.merge(payments, on='order_id'))
shipped_orders = len(orders[orders['order_status'].isin(['shipped', 'delivered', 'returned'])])
delivered_only = len(orders[orders['order_status'] == 'delivered'])

funnel_df = pd.DataFrame({
    'Step': ['1. Created', '2. Paid', '3. Shipped', '4. Delivered'],
    'Count': [total_orders, paid_orders, shipped_orders, delivered_only]
})
funnel_df['Retention_%'] = (funnel_df['Count'] / total_orders) * 100

plt.figure(figsize=(10, 5))
sns.barplot(data=funnel_df, x='Retention_%', y='Step', palette='magma')
for i, v in enumerate(funnel_df['Retention_%']):
    plt.text(v + 1, i, f"{v:.1f}% ({funnel_df['Count'].iloc[i]})", va='center')
plt.title('4.1 Phễu Chuyển Đổi Đơn Hàng Tích Lũy')
plt.xlim(0, 115)
plt.show()

# 4.2 Device Conversion Gap
device_conv = orders.groupby('device_type').apply(lambda x: (x['order_status'] == 'delivered').mean() * 100).reset_index(name='Delivery_Rate')
plt.figure(figsize=(8, 4))
sns.barplot(data=device_conv, x='device_type', y='Delivery_Rate', palette='pastel')
plt.title('4.2 Tỷ Lệ Giao Hàng Thành Công Theo Thiết Bị')
plt.show()

# 4.3 Cart Abandonment Rate (Proxy via Cancelled)
orders['Month'] = orders['order_date'].dt.to_period('M').dt.to_timestamp()
abandon_rate = orders.groupby('Month').apply(
    lambda x: sum(x['order_status'] == 'cancelled') / len(x) * 100
).reset_index(name='Abandon_Rate')

plt.figure(figsize=(12, 4))
sns.lineplot(data=abandon_rate, x='Month', y='Abandon_Rate', color='red', marker='s')
plt.title('4.3 Tỷ Lệ Hủy Đơn (Cart Abandonment Proxy) Qua Các Tháng')
plt.show()

# 4.4 Payment Bottleneck (Lỗi Kế Toán 59,462 đơn)
cancelled_with_payment = orders[orders['order_status'] == 'cancelled'].merge(payments, on='order_id', how='inner')
refunded_cancelled = cancelled_with_payment.merge(returns, on='order_id', how='inner')
print(f"4.4 LỖI NGHIÊM TRỌNG: Số đơn Hủy đã thanh toán: {len(cancelled_with_payment)}, Số đơn đã hoàn tiền hệ thống: {len(refunded_cancelled)}")

# 4.5 Delivery Lead Time Analysis
valid_shipments = shipments.dropna(subset=['delivery_date', 'ship_date']).copy()
valid_shipments['Lead_Time'] = (valid_shipments['delivery_date'] - valid_shipments['ship_date']).dt.days
valid_shipments = valid_shipments[valid_shipments['Lead_Time'] >= 0]

plt.figure(figsize=(10, 5))
sns.histplot(valid_shipments['Lead_Time'], bins=20, kde=True, color='purple')
plt.title('4.5 Phân Bố Thời Gian Giao Hàng (Lead Time)')
plt.xlabel('Số Ngày')
plt.show()

# 4.6 Late Delivery -> Return correlation
# Gắn cờ trễ hạn: Lấy mốc > 5 ngày
valid_shipments['Is_Late'] = valid_shipments['Lead_Time'] > 5
ship_status = valid_shipments.merge(orders[['order_id', 'order_status']], on='order_id')
return_by_late = ship_status.groupby('Is_Late').apply(lambda x: (x['order_status'] == 'returned').mean() * 100).reset_index(name='Return_Rate')

plt.figure(figsize=(6, 4))
sns.barplot(data=return_by_late, x='Is_Late', y='Return_Rate', palette='Reds')
plt.title('4.6 Tỷ Lệ Hoàn Hàng Khi Giao Trễ (>5 Ngày)')
plt.xticks([0, 1], ['Đúng Hạn', 'Trễ Hạn'])
plt.ylabel('Tỷ Lệ Trả Hàng (%)')
plt.show()

# 4.7 Late Delivery -> Rating correlation
ship_review = valid_shipments.merge(reviews, on='order_id')
rating_by_late = ship_review.groupby('Is_Late')['rating'].mean().reset_index()
print("4.7 Đánh Giá Trung Bình: Đúng Hạn =", round(rating_by_late.iloc[0]['rating'], 2), 
      "| Trễ Hạn =", round(rating_by_late.iloc[1]['rating'], 2))

# 4.8 Return Reason Breakdown
plt.figure(figsize=(10, 4))
sns.countplot(data=returns, y='return_reason', order=returns['return_reason'].value_counts().index, palette='viridis')
plt.title('4.8 Phân Phối Lý Do Khách Trả Hàng')
plt.show()

# 4.9 Return Rate by Category
returned_items = returns.merge(products, on='product_id')
ret_cat = returned_items['category'].value_counts()
plt.figure(figsize=(10, 4))
ret_cat.plot(kind='bar', color='salmon')
plt.title('4.9 Số Lượng Trả Hàng Theo Danh Mục')
plt.show()

# 4.10 AOV Trend
aov_trend = monthly_orders[['Month', 'AOV']] # Đã tính ở GĐ1
plt.figure(figsize=(12, 4))
sns.lineplot(data=aov_trend, x='Month', y='AOV', color='navy')
plt.title('4.10 Xu Hướng Giá Trị Đơn Trung Bình (AOV)')
plt.show()"""))

    cells.append(nbf.v4.new_markdown_cell("""### Insights Giai Đoạn 4
**Descriptive**: Hàng chục ngàn đơn bị hủy sau khi thu tiền nhưng không có lịch sử hoàn tiền. Giao hàng trễ hạn trực tiếp làm tăng vọt tỷ lệ hoàn hàng. "Sai kích cỡ" là lý do phổ biến nhất.
**Diagnostic**: Dòng tiền hoàn trả bị xử lý ngoài Data Warehouse hoặc công ty đang có nguy cơ chiếm dụng vốn trái phép. Việc giao hàng trễ làm khách hàng thay đổi ý định và từ chối nhận (đặc biệt các sản phẩm bắt trend).
**Predictive**: Nếu không khắc phục quy trình hoàn tiền, nguy cơ khủng hoảng pháp lý và tẩy chay thương hiệu là cực kỳ cao.
**Prescriptive**:
- **Kế Toán & IT**: Mở kiểm toán chéo (cross-audit) lập tức 59,462 đơn hàng "bốc hơi" tiền hoàn. Tích hợp API hoàn tiền tự động.
- **Operations**: Thắt chặt SLA giao nhận với 3PL. Đưa bảng quy đổi kích cỡ chi tiết hơn lên trang chủ đề giảm tỷ lệ hoàn trả do "Wrong Size"."""))

    # PHASE 5: RETENTION & LOYALTY
    cells.append(nbf.v4.new_markdown_cell("""## GIAI ĐOẠN 5: Giữ Chân & Trung Thành - Khai Thác Giá Trị Dài Hạn
Phân khúc khách hàng đa chiều và định hướng tối ưu hóa Customer Lifetime Value (CLV)."""))

    cells.append(nbf.v4.new_code_cell("""# Thiết lập Base cho RFM và CLV
snapshot_date = orders['order_date'].max() + timedelta(days=1)
cust_history = orders_delivered.groupby('customer_id').agg(
    Recency=('order_date', lambda x: (snapshot_date - x.max()).days),
    Frequency=('order_id', 'nunique'),
    First_Order=('order_date', 'min'),
    Last_Order=('order_date', 'max')
).reset_index()

cust_spend = orders_delivered.merge(payments, on='order_id').groupby('customer_id')['payment_value'].sum().reset_index()
cust_history = cust_history.merge(cust_spend, on='customer_id')
cust_history.rename(columns={'payment_value': 'Monetary'}, inplace=True)

# 5.1 RFM Segmentation
cust_history['R_Score'] = pd.qcut(cust_history['Recency'], 4, labels=[4, 3, 2, 1])
cust_history['F_Score'] = pd.qcut(cust_history['Frequency'].rank(method='first'), 4, labels=[1, 2, 3, 4])
cust_history['M_Score'] = pd.qcut(cust_history['Monetary'], 4, labels=[1, 2, 3, 4])

def assign_segment(row):
    r, f = int(row['R_Score']), int(row['F_Score'])
    if r >= 3 and f >= 3: return 'Champions'
    elif r >= 3 and f < 3: return 'Promising'
    elif r < 3 and f >= 3: return 'At Risk'
    else: return 'Lost/Hibernating'

cust_history['Segment'] = cust_history.apply(assign_segment, axis=1)

segment_dist = cust_history['Segment'].value_counts()
plt.figure(figsize=(8, 8))
plt.pie(segment_dist, labels=segment_dist.index, autopct='%1.1f%%', colors=sns.color_palette('pastel'))
plt.title('5.1 Phân Khúc Khách Hàng (RFM)')
plt.show()

# 5.2 RFM x Revenue Contribution
rev_by_seg = cust_history.groupby('Segment')['Monetary'].sum()
plt.figure(figsize=(10, 4))
rev_by_seg.plot(kind='barh', color='teal')
plt.title('5.2 Đóng Góp Doanh Thu Theo Phân Khúc')
plt.xlabel('Tổng Doanh Thu Lũy Kế')
plt.show()

# 5.3 CLV Distribution
cust_history['Lifespan_Days'] = (cust_history['Last_Order'] - cust_history['First_Order']).dt.days
cust_history['Historical_CLV'] = cust_history['Monetary']

plt.figure(figsize=(10, 5))
sns.histplot(cust_history[cust_history['Historical_CLV'] < cust_history['Historical_CLV'].quantile(0.95)]['Historical_CLV'], bins=50, color='darkgreen')
plt.title('5.3 Phân Bố Giá Trị Vòng Đời Khách Hàng (CLV)')
plt.xlabel('CLV')
plt.show()

# 5.4 CLV by Channel
clv_channel = cust_history.merge(customers[['customer_id', 'acquisition_channel']], on='customer_id')
plt.figure(figsize=(12, 6))
sns.boxplot(data=clv_channel[clv_channel['Historical_CLV'] < 20000], x='acquisition_channel', y='Historical_CLV', palette='Set2')
plt.title('5.4 Giá Trị Vòng Đời (CLV) Theo Kênh Thu Hút')
plt.show()

# 5.5 Repeat Rate Cohort (Giả lập đơn giản)
total_cust = len(cust_history)
repeat_cust = len(cust_history[cust_history['Frequency'] > 1])
print(f"5.5 Tỷ Lệ Quay Lại (Repeat Rate) Tổng Thể: {repeat_cust/total_cust*100:.1f}%")

# 5.6 Inter-order Gap Median
multi_buyers = cust_history[cust_history['Frequency'] > 1]['customer_id']
order_dates = orders_delivered[orders_delivered['customer_id'].isin(multi_buyers)].sort_values(['customer_id', 'order_date'])
order_dates['Prev_Date'] = order_dates.groupby('customer_id')['order_date'].shift(1)
order_dates['Gap_Days'] = (order_dates['order_date'] - order_dates['Prev_Date']).dt.days

median_gap = order_dates['Gap_Days'].median()
plt.figure(figsize=(10, 4))
sns.kdeplot(order_dates['Gap_Days'].dropna(), fill=True, color='indigo')
plt.axvline(median_gap, color='red', linestyle='--')
plt.text(median_gap+5, 0.005, f'Median: {int(median_gap)} ngày', color='red', fontweight='bold')
plt.title('5.6 Khoảng Cách Mua Lại (Inter-order Gap)')
plt.xlim(0, 180)
plt.show()

# 5.7 Deal Hunter Ratio
promo_orders = order_items.groupby('order_id').apply(lambda x: x['promo_id'].notna().any()).reset_index(name='Has_Promo')
cust_promo = orders_delivered.merge(promo_orders, on='order_id').groupby('customer_id').agg(
    Total_Orders=('order_id', 'count'),
    Promo_Orders=('Has_Promo', 'sum')
).reset_index()
cust_promo['Promo_Ratio'] = cust_promo['Promo_Orders'] / cust_promo['Total_Orders']
cust_promo['Is_Deal_Hunter'] = cust_promo['Promo_Ratio'] > 0.8

deal_hunter_dist = cust_promo['Is_Deal_Hunter'].value_counts(normalize=True) * 100
print(f"5.7 Tỷ Lệ Deal Hunter (Chỉ mua khi có khuyến mãi > 80%): {deal_hunter_dist.get(True, 0):.1f}%")

# 5.8 Deal Hunter CLV vs Full-price CLV
cust_hunter_clv = cust_history.merge(cust_promo[['customer_id', 'Is_Deal_Hunter']], on='customer_id')
plt.figure(figsize=(8, 4))
sns.barplot(data=cust_hunter_clv, x='Is_Deal_Hunter', y='Historical_CLV', palette='magma')
plt.title('5.8 So Sánh CLV: Khách Nguyên Giá vs Deal Hunter')
plt.xticks([0, 1], ['Mua Nguyên Giá', 'Deal Hunter'])
plt.show()

# 5.9 Rating Distribution Trend
reviews['YearMonth'] = reviews['review_date'].dt.to_period('M').dt.to_timestamp()
monthly_rating = reviews.groupby('YearMonth')['rating'].mean().reset_index()
plt.figure(figsize=(12, 4))
sns.lineplot(data=monthly_rating, x='YearMonth', y='rating', color='orange')
plt.title('5.9 Xu Hướng Điểm Đánh Giá Trung Bình')
plt.show()

# 5.10 Churn Rate
churn_threshold_days = 180
cust_history['Is_Churned'] = cust_history['Recency'] > churn_threshold_days
churn_rate = cust_history['Is_Churned'].mean() * 100
print(f"5.10 Tỷ Lệ Rời Bỏ (Ngủ đông > {churn_threshold_days} ngày): {churn_rate:.1f}%")"""))

    cells.append(nbf.v4.new_markdown_cell("""### Insights Giai Đoạn 5
**Descriptive**: Có tỷ lệ "At Risk" và "Lost" rất lớn. Khoảng cách mua hàng trung vị rất rõ ràng (điểm rơi nhu cầu). 
**Diagnostic**: Khách hàng săn khuyến mãi (Deal Hunter) mang lại CLV thấp hơn nhiều so với khách hàng mua nguyên giá, chứng tỏ khuyến mãi chỉ tạo doanh thu ngắn hạn chứ không tạo ra sự trung thành dài hạn.
**Predictive**: Nếu tỷ lệ Churn (ngủ đông) tiếp tục ở mức cao, áp lực lên chi phí Marketing để tìm khách mới sẽ làm sụp đổ phễu lợi nhuận.
**Prescriptive**:
- **Marketing**: Cắt giảm rải rác mã giảm giá đại trà. Thiết lập hệ thống Email/Push Notification gửi voucher tự động trước đúng 3 ngày so với Trung vị Khoảng cách mua lại (Inter-order gap).
- **Chăm Sóc Khách Hàng**: Xây dựng Loyalty Program đặc quyền cho nhóm Champions. Khởi động chiến dịch Win-back cho nhóm "At Risk" trước khi họ thành "Lost"."""))

    # Conclusion
    cells.append(nbf.v4.new_markdown_cell("""# TỔNG KẾT
Câu chuyện dữ liệu đã chứng minh: Doanh nghiệp không thiếu số lượng bán, mà đang rò rỉ lợi nhuận qua đứt gãy tồn kho, chi phí vận hành giao trễ/hoàn hàng, và chiến lược marketing sai lệch kênh. Việc xây dựng Mô hình Dự báo Máy học (Sales Forecasting) tiếp theo bắt buộc phải bóc tách sâu tới mức SKU và Tỉnh thành để tự động hóa hoàn toàn các hành động can thiệp (Prescriptive Actions) đã được vạch ra ở trên."""))

    nb['cells'] = cells
    
    with open(file_path, 'w', encoding='utf-8') as f:
        nbf.write(nb, f)

if __name__ == "__main__":
    file_path = "d:/HuynhHan/Datathon/DATATHON_2026_DATACONDA/notebook/05_eda_storytelling_final.ipynb"
    create_notebook(file_path)
    print("Created detailed notebook at:", file_path)
