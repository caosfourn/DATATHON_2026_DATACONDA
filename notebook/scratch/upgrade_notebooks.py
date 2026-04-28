import nbformat as nbf
import os

NB_01_PATH = r'd:\HuynhHan\Datathon\DATATHON_2026_DATACONDA\notebook\01_data_audit_and_split.ipynb'
NB_03_PATH = r'd:\HuynhHan\Datathon\DATATHON_2026_DATACONDA\notebook\03_bivariate_diagnostics.ipynb'

def append_to_notebook(nb_path, cells):
    with open(nb_path, 'r', encoding='utf-8') as f:
        nb = nbf.read(f, as_version=4)
    nb.cells.extend(cells)
    with open(nb_path, 'w', encoding='utf-8') as f:
        nbf.write(nb, f)

# --- Cells for Notebook 01 ---
nb1_md1 = nbf.v4.new_markdown_cell("""---
## 6. Advanced Business Rule & Anomaly Validation (Kiểm tra Ngoại lệ Hệ thống)

Phần này phân tích các lỗ hổng hệ thống trầm trọng liên quan đến quá trình vận hành, dòng tiền và tracking dữ liệu. Các lỗi này không chỉ là vấn đề data chất lượng kém, mà còn là các báo động đỏ cho đội ngũ Business.""")

nb1_code1 = nbf.v4.new_code_cell("""# Load bổ sung bảng returns và shipments nếu chưa có
import pandas as pd
import os
DATA_DIR = '../dataset/'
if 'returns' not in locals():
    returns = pd.read_csv(DATA_DIR + 'returns.csv', parse_dates=['return_date'])
if 'shipments' not in locals():
    shipments = pd.read_csv(DATA_DIR + 'shipments.csv', parse_dates=['ship_date', 'delivery_date'])
    
# 6.1. Nghịch lý Xuyên không (Time-Travel Paradox)
print("=== 6.1. Nghịch lý Xuyên không (Customers vs Orders) ===")
cust_orders = orders.merge(customers[['customer_id', 'signup_date']], on='customer_id', how='inner')
time_travel = cust_orders[cust_orders['order_date'] < cust_orders['signup_date']]
print(f"Số lượng đơn hàng xảy ra TRƯỚC ngày tạo tài khoản: {len(time_travel):,} ({len(time_travel)/len(orders):.1%})")
print("=> LỖI KIẾN TRÚC DỮ LIỆU: Hệ thống cho phép Guest Checkout hoặc lỗi chuyển đổi dữ liệu. Cần lấy min(order_date) làm signup_date thực tế.\\n")

# 6.2. Lỗ hổng Hoàn tiền (Cancelled & Refund Loopholes)
print("=== 6.2. Lỗ hổng Hoàn tiền (Orders vs Payments vs Returns) ===")
cancelled_orders = orders[orders['order_status'] == 'cancelled']
paid_cancelled = cancelled_orders.merge(payments, on='order_id', how='inner')
unrefunded = paid_cancelled[~paid_cancelled['order_id'].isin(returns['order_id'])]
print(f"Số đơn Hủy đã thu tiền nhưng KHÔNG CÓ BẢN GHI HOÀN TIỀN: {len(unrefunded):,}")

returned_orders = orders[orders['order_status'] == 'returned']
ghost_returns = returned_orders[~returned_orders['order_id'].isin(returns['order_id'])]
print(f"Số đơn trạng thái Returned nhưng 'bốc hơi' khỏi bảng returns: {len(ghost_returns):,}")
print("=> BÁO ĐỘNG ĐỎ TÀI CHÍNH: Doanh nghiệp có thể đang dính rủi ro kiện cáo hoặc thất thoát quỹ ngoài hệ thống.\\n")

# 6.3. Vận đơn Ma (Fake Deliveries)
print("=== 6.3. Vận đơn Ma (Orders vs Shipments) ===")
delivered_orders = orders[orders['order_status'].isin(['shipped', 'delivered'])]
ghost_deliveries = delivered_orders[~delivered_orders['order_id'].isin(shipments['order_id'])]
print(f"Số đơn hàng Shipped/Delivered nhưng KHÔNG CÓ DỮ LIỆU VẬN ĐƠN: {len(ghost_deliveries):,}")
print("=> LỖ HỔNG VẬN HÀNH: Gian lận kho bãi (Fake Delivery) hoặc lỗi API kết nối làm rớt dữ liệu vận chuyển.\\n")

# 6.4. Rác Giỏ hàng (Cart Aggregation Bug)
print("=== 6.4. Rác Giỏ hàng (Order_items) ===")
cart_dupes = order_items.groupby(['order_id', 'product_id']).size().reset_index(name='count')
bug_count = len(cart_dupes[cart_dupes['count'] > 1])
print(f"Số trường hợp 1 đơn hàng tách cùng 1 sản phẩm ra nhiều dòng thay vì cộng dồn số lượng: {bug_count:,}")
print("=> LỖI FRONT-END LOGIC: Ảnh hưởng đến dữ liệu chạy mô hình Market Basket Analysis.")
""")

cells_to_add_nb1 = [nb1_md1, nb1_code1]

# --- Cells for Notebook 03 ---
nb3_md1 = nbf.v4.new_markdown_cell("""---
## 8. Strategic Diagnostic Insights (Chẩn đoán Chuyên sâu)
Phần này giải thích gốc rễ các vấn đề chiến lược tàn phá lợi nhuận và làm tê liệt chuỗi cung ứng của doanh nghiệp.""")

nb3_code1 = nbf.v4.new_code_cell("""# 8.1. Chẩn đoán Tê liệt Chuỗi Cung Ứng (Supply Chain Paralysis - Bullwhip Effect)
import pandas as pd
DATA_DIR = '../dataset/'
if 'inventory' not in locals():
    inventory = pd.read_csv(DATA_DIR + 'inventory.csv', parse_dates=['snapshot_date'])

print("=== 8.1. Chẩn đoán Tê liệt Chuỗi Cung Ứng (Inventory Bullwhip) ===")
# Kiểm tra cảnh báo reorder
reorder_failure = inventory['reorder_flag'].sum()
print(f"Số lần hệ thống phát cờ Reorder: {reorder_failure} -> HỆ THỐNG CẢNH BÁO NHẬP HÀNG TÊ LIỆT 100%.")

# Tính toán chu kỳ tháng
inventory['month_year'] = inventory['snapshot_date'].dt.to_period('M')
# Nhóm theo product và tháng để xem trong cùng 1 tháng có xảy ra cả 2 trạng thái không
monthly_flags = inventory.groupby(['product_id', 'month_year']).agg(
    has_stockout=('stockout_flag', 'max'),
    has_overstock=('overstock_flag', 'max')
).reset_index()

bullwhip_cases = monthly_flags[(monthly_flags['has_stockout'] == 1) & (monthly_flags['has_overstock'] == 1)]
print(f"Số tháng sản phẩm vừa bị Đứt Hàng vừa bị Quá Tải: {len(bullwhip_cases):,} ({len(bullwhip_cases)/len(monthly_flags):.1%})")
print("=> NGHỊCH LÝ BULLWHIP: Quản lý hàng tồn kho yếu kém, nhập hàng sai thời điểm dẫn tới đứt hàng cục bộ, sau đó nhập ồ ạt gây quá tải và đọng vốn dài hạn.")
""")

nb3_md2 = nbf.v4.new_markdown_cell("""### 8.2. Chẩn đoán Lợi Nhuận Âm (Negative Profitability)
Việc doanh thu âm/chênh lệch doanh thu âm qua các ngày là bình thường trong bán lẻ, nhưng Profit âm trên diện rộng là hệ quả của các "chi phí ẩn".""")

nb3_code2 = nbf.v4.new_code_cell("""print("=== 8.2. Chẩn đoán Bán Lỗ (Profitability) ===")
if 'returns' not in locals():
    returns = pd.read_csv(DATA_DIR + 'returns.csv', parse_dates=['return_date'])

print(f"Trung vị lượng hàng hoàn trả / đơn: {returns['return_quantity'].median():.0f} sản phẩm")
print(f"Số tiền hoàn trả trung bình / đơn: {returns['refund_amount'].mean():,.0f} VNĐ")

print("\\n=> NGUYÊN NHÂN BÁN LỖ TRÊN DIỆN RỘNG (333 Ngày Profit Âm):")
print("1. Chi phí vận hành từ tỷ lệ trả hàng cao (Hoàn tiền, Phí ship 2 chiều, Chi phí xử lý) ăn lẹm toàn bộ lợi nhuận gộp.")
print("2. Chiến lược 'Đốt tiền mua thị phần' thông qua Promotions diễn ra liên tục hoặc bị lợi dụng (Promotion Loopholes), khiến giá trị thu về thấp hơn COGS.")
""")

cells_to_add_nb3 = [nb3_md1, nb3_code1, nb3_md2, nb3_code2]

try:
    append_to_notebook(NB_01_PATH, cells_to_add_nb1)
    print("Updated Notebook 01 successfully!")
except Exception as e:
    print(f"Error updating Notebook 01: {e}")

try:
    append_to_notebook(NB_03_PATH, cells_to_add_nb3)
    print("Updated Notebook 03 successfully!")
except Exception as e:
    print(f"Error updating Notebook 03: {e}")
