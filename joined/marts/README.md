# 📦 Data Marts — DATATHON 2026

> **Tạo bởi:** Data Engineer  
> **Công cụ:** DuckDB + Parquet (ZSTD compression)  
> **Source:** 15 file CSV trong `dataset/`  
> **Rebuild:** `cd joined/ && python data_pipeline.py`

---

## Tổng Quan

Thư mục này chứa **4 file Parquet** đã được JOIN và tính toán sẵn từ 15 bảng CSV thô.  
Team **KHÔNG cần** đọc trực tiếp từ `dataset/` nữa — hãy dùng các file ở đây.

| # | File | Grain (1 dòng = ?) | Rows | Size | Dùng cho |
|---|---|---|---|---|---|
| 1 | `transaction_master.parquet` | 1 sản phẩm trong 1 đơn hàng | ~714K | 36.8 MB | EDA chính (Phần 2) |
| 2 | `returns_enriched.parquet` | 1 lần trả hàng | ~40K | 1.0 MB | Phân tích hậu mãi |
| 3 | `reviews_enriched.parquet` | 1 đánh giá | ~114K | 1.8 MB | Phân tích hậu mãi |
| 4 | `daily_summary.parquet` | 1 ngày | ~3.8K | 0.3 MB | Forecast (Phần 3) + Time-series EDA |

---

## Cách Sử Dụng Trong Notebook

```python
# Cách 1: Dùng hàm tiện ích (Khuyến nghị)
import sys; sys.path.insert(0, '..')
from joined.data_pipeline import (
    load_transaction_master,
    load_returns_enriched,
    load_reviews_enriched,
    load_daily_summary,
)

df_txn    = load_transaction_master()
df_ret    = load_returns_enriched()
df_rev    = load_reviews_enriched()
df_daily  = load_daily_summary()

# Cách 2: Đọc trực tiếp bằng pandas
import pandas as pd
df = pd.read_parquet('../joined/marts/transaction_master.parquet')
```

---

## Chi Tiết Từng Data Mart

---

### 1️⃣ `transaction_master.parquet`

**Mục đích:** Bảng xương sống cho phần lớn EDA — chứa toàn bộ thông tin giao dịch ở mức chi tiết nhất.

**Các bảng đã JOIN (8 bảng):**
```
order_items (base)
├── LEFT JOIN orders         → order_date, status, device, source
│   ├── LEFT JOIN customers  → age_group, gender, signup_date, channel
│   ├── LEFT JOIN geography  → region, city, district
│   ├── LEFT JOIN payments   → payment_value, installments
│   └── LEFT JOIN shipments  → ship_date, delivery_date, shipping_fee
├── LEFT JOIN products       → category, segment, size, color, price, cogs
├── LEFT JOIN promotions p1  → thông tin KM chính
└── LEFT JOIN promotions p2  → thông tin KM thứ hai
```

**Các cột có sẵn:**

| Nhóm | Cột | Mô tả |
|---|---|---|
| Đơn hàng | `order_id` | Mã đơn hàng (FK → orders) |
| Đơn hàng | `order_date` | Ngày đặt hàng |
| Đơn hàng | `order_status` | Trạng thái: pending / shipped / delivered / cancelled / returned |
| Đơn hàng | `device_type` | Thiết bị đặt hàng (mobile / desktop / tablet) |
| Đơn hàng | `order_source` | Kênh marketing dẫn đến đơn hàng |
| Sản phẩm | `product_id` | Mã sản phẩm (FK → products) |
| Sản phẩm | `product_name` | Tên sản phẩm |
| Sản phẩm | `category` | Danh mục sản phẩm |
| Sản phẩm | `segment` | Phân khúc: Premium / Performance / Activewear / Standard |
| Sản phẩm | `size` | Kích cỡ: S / M / L / XL |
| Sản phẩm | `color` | Màu sắc sản phẩm |
| Giá cả | `quantity` | Số lượng sản phẩm trong dòng |
| Giá cả | `unit_price` | Đơn giá sau khuyến mãi |
| Giá cả | `list_price` | Giá niêm yết gốc (từ products.price) |
| Giá cả | `cogs` | Giá vốn hàng bán (từ products.cogs) |
| Giá cả | `discount_amount` | Tổng tiền giảm giá cho dòng này |
| Khách hàng | `customer_id` | Mã khách hàng |
| Khách hàng | `customer_signup_date` | Ngày đăng ký tài khoản |
| Khách hàng | `gender` | Giới tính (nullable) |
| Khách hàng | `age_group` | Nhóm tuổi (nullable) |
| Khách hàng | `acquisition_channel` | Kênh tiếp thị đăng ký (nullable) |
| Địa lý | `zip` | Mã bưu chính giao hàng |
| Địa lý | `city` | Thành phố |
| Địa lý | `region` | Vùng: West / Central / East |
| Địa lý | `district` | Quận/huyện |
| Thanh toán | `order_payment_method` | Phương thức thanh toán |
| Thanh toán | `payment_value` | Tổng giá trị thanh toán của đơn |
| Thanh toán | `installments` | Số kỳ trả góp |
| Vận chuyển | `ship_date` | Ngày gửi hàng (NULL nếu chưa ship) |
| Vận chuyển | `delivery_date` | Ngày giao hàng (NULL nếu chưa giao) |
| Vận chuyển | `shipping_fee` | Phí vận chuyển (0 = miễn phí) |
| KM chính | `promo_id` | Mã khuyến mãi chính (nullable) |
| KM chính | `promo1_name` | Tên chiến dịch KM chính |
| KM chính | `promo1_type` | Loại KM: percentage / fixed |
| KM chính | `promo1_discount_value` | Giá trị giảm (% hoặc VND) |
| KM phụ | `promo_id_2` | Mã khuyến mãi thứ hai (nullable) |
| KM phụ | `promo2_name` | Tên chiến dịch KM thứ hai |
| KM phụ | `promo2_type` | Loại KM thứ hai |
| KM phụ | `promo2_discount_value` | Giá trị giảm KM thứ hai |
| **Derived** | `line_revenue` | `quantity × unit_price` — Doanh thu dòng (sau KM) |
| **Derived** | `line_cogs` | `quantity × cogs` — Giá vốn dòng |
| **Derived** | `gross_profit` | `line_revenue - line_cogs` — Lợi nhuận gộp dòng |
| **Derived** | `gross_margin` | `gross_profit / line_revenue` — Tỷ suất lợi nhuận gộp |
| **Derived** | `processing_days` | `ship_date - order_date` — Số ngày xử lý đơn |
| **Derived** | `delivery_days` | `delivery_date - ship_date` — Số ngày giao hàng |
| **Derived** | `order_year` | Năm đặt hàng |
| **Derived** | `order_month` | Tháng đặt hàng |
| **Derived** | `order_quarter` | Quý đặt hàng |
| **Derived** | `order_dow` | Ngày trong tuần (0=Sun, 1=Mon, ..., 6=Sat) |

---

### 2️⃣ `returns_enriched.parquet`

**Mục đích:** Phân tích trả hàng — tại sao khách trả, sản phẩm/vùng nào bị trả nhiều nhất.

**Các bảng đã JOIN (5 bảng):**
```
returns (base)
├── LEFT JOIN orders     → order_date, customer_id, order_status, device_type, order_source
│   ├── LEFT JOIN customers → gender, age_group
│   └── LEFT JOIN geography → region, city
└── LEFT JOIN products   → product_name, category, segment, size, color, list_price, cogs
```

**Các cột có sẵn:**

| Nhóm | Cột | Mô tả |
|---|---|---|
| Trả hàng | `return_id` | Mã trả hàng (PK) |
| Trả hàng | `order_id` | Mã đơn hàng liên quan |
| Trả hàng | `product_id` | Mã sản phẩm bị trả |
| Trả hàng | `return_date` | Ngày khách gửi trả hàng |
| Trả hàng | `return_reason` | Lý do trả: defective / wrong_size / changed_mind / not_as_described / ... |
| Trả hàng | `return_quantity` | Số lượng sản phẩm trả lại |
| Trả hàng | `refund_amount` | Số tiền hoàn lại cho khách (VND) |
| Đơn hàng | `order_date` | Ngày đặt hàng gốc |
| Đơn hàng | `customer_id` | Mã khách hàng |
| Đơn hàng | `order_status` | Trạng thái đơn hàng |
| Đơn hàng | `device_type` | Thiết bị đặt hàng |
| Đơn hàng | `order_source` | Kênh marketing |
| Khách hàng | `gender` | Giới tính (nullable) |
| Khách hàng | `age_group` | Nhóm tuổi (nullable) |
| Địa lý | `region` | Vùng: West / Central / East |
| Địa lý | `city` | Thành phố |
| Sản phẩm | `product_name` | Tên sản phẩm bị trả |
| Sản phẩm | `category` | Danh mục sản phẩm |
| Sản phẩm | `segment` | Phân khúc: Premium / Performance / Activewear / Standard |
| Sản phẩm | `size` | Kích cỡ: S / M / L / XL |
| Sản phẩm | `color` | Màu sắc sản phẩm |
| Sản phẩm | `list_price` | Giá niêm yết gốc |
| Sản phẩm | `cogs` | Giá vốn hàng bán |
| **Derived** | `days_to_return` | `return_date - order_date` — Số ngày từ lúc mua đến lúc trả |

---

### 3️⃣ `reviews_enriched.parquet`

**Mục đích:** Phân tích đánh giá — rating theo sản phẩm, vùng miền, nhóm khách hàng.

**Các bảng đã JOIN (5 bảng):**
```
reviews (base)
├── LEFT JOIN orders     → order_date, device_type, order_source
├── LEFT JOIN customers  → gender, age_group
├── LEFT JOIN geography  → region, city
└── LEFT JOIN products   → product_name, category, segment, size, color
```

**Các cột có sẵn:**

| Nhóm | Cột | Mô tả |
|---|---|---|
| Đánh giá | `review_id` | Mã đánh giá (PK) |
| Đánh giá | `order_id` | Mã đơn hàng liên quan |
| Đánh giá | `product_id` | Mã sản phẩm được đánh giá |
| Đánh giá | `customer_id` | Mã khách hàng đánh giá |
| Đánh giá | `review_date` | Ngày gửi đánh giá |
| Đánh giá | `rating` | Điểm đánh giá: 1–5 |
| Đánh giá | `review_title` | Tiêu đề đánh giá (text) |
| Đơn hàng | `order_date` | Ngày đặt hàng gốc |
| Đơn hàng | `device_type` | Thiết bị đặt hàng |
| Đơn hàng | `order_source` | Kênh marketing |
| Khách hàng | `gender` | Giới tính (nullable) |
| Khách hàng | `age_group` | Nhóm tuổi (nullable) |
| Địa lý | `region` | Vùng: West / Central / East |
| Địa lý | `city` | Thành phố |
| Sản phẩm | `product_name` | Tên sản phẩm |
| Sản phẩm | `category` | Danh mục sản phẩm |
| Sản phẩm | `segment` | Phân khúc: Premium / Performance / Activewear / Standard |
| Sản phẩm | `size` | Kích cỡ: S / M / L / XL |
| Sản phẩm | `color` | Màu sắc sản phẩm |
| **Derived** | `days_to_review` | `review_date - order_date` — Số ngày từ lúc mua đến lúc review |

---

### 4️⃣ `daily_summary.parquet`

**Mục đích:** Input chính cho mô hình Forecast (Phần 3) + Phân tích time-series EDA.

**Logic tổng hợp:**
```
sales.csv (base — đã có Revenue, COGS theo ngày)
├── LEFT JOIN orders       (GROUP BY order_date)    → đếm đơn, đếm khách, đếm trạng thái
├── LEFT JOIN order_items  (GROUP BY order_date)    → tổng SL bán, tổng giảm giá, tỷ lệ KM
├── LEFT JOIN web_traffic  (GROUP BY date)          → sessions, visitors, bounce rate
├── LEFT JOIN returns      (GROUP BY return_date)   → số lần trả, số tiền hoàn
├── LEFT JOIN shipments    (GROUP BY ship_date)     → số lần ship, phí ship
├── LEFT JOIN payments     (GROUP BY order_date)    → giá trị thanh toán TB, trả góp TB
└── LEFT JOIN inventory    (forward-fill monthly)   → tồn kho, fill rate, stockout
```

**Các cột có sẵn:**

| Nhóm | Cột | Mô tả |
|---|---|---|
| Target | `date` | Ngày (PK) |
| Target | `revenue` | Tổng doanh thu thuần trong ngày |
| Target | `cogs` | Tổng giá vốn hàng bán trong ngày |
| Target | `gross_profit` | `revenue - cogs` — Lợi nhuận gộp trong ngày |
| Calendar | `year` | Năm |
| Calendar | `month` | Tháng (1–12) |
| Calendar | `quarter` | Quý (1–4) |
| Calendar | `day_of_week` | Ngày trong tuần (0=Sun ... 6=Sat) |
| Calendar | `day_of_year` | Ngày trong năm (1–366) |
| Calendar | `week_of_year` | Tuần trong năm (1–53) |
| Calendar | `is_weekend` | 1 = Thứ 7 hoặc CN, 0 = ngày thường |
| Orders | `total_orders` | Tổng số đơn hàng trong ngày |
| Orders | `unique_customers` | Số khách hàng duy nhất đặt hàng |
| Orders | `delivered_orders` | Số đơn có trạng thái delivered |
| Orders | `cancelled_orders` | Số đơn có trạng thái cancelled |
| Orders | `returned_orders` | Số đơn có trạng thái returned |
| Orders | `shipped_orders` | Số đơn có trạng thái shipped |
| Orders | `pending_orders` | Số đơn có trạng thái pending |
| Items | `total_items_sold` | Tổng số lượng sản phẩm bán ra |
| Items | `total_item_revenue` | Tổng doanh thu tính từ order_items (quantity × unit_price) |
| Items | `total_discount` | Tổng tiền giảm giá trong ngày |
| Items | `avg_discount_per_line` | Giảm giá trung bình mỗi dòng order_item |
| Items | `unique_products_sold` | Số sản phẩm khác nhau được bán |
| Items | `promo_lines` | Số dòng order_items có áp dụng KM |
| Items | `total_lines` | Tổng số dòng order_items |
| Items | `promo_pct` | Tỷ lệ % dòng có KM (promo_lines / total_lines × 100) |
| Web Traffic | `total_sessions` | Tổng phiên truy cập website |
| Web Traffic | `total_visitors` | Số khách truy cập duy nhất |
| Web Traffic | `total_page_views` | Tổng lượt xem trang |
| Web Traffic | `avg_bounce_rate` | Tỷ lệ thoát trung bình (%) |
| Web Traffic | `avg_session_duration` | Thời gian TB mỗi phiên (giây) |
| Returns | `daily_returns` | Số lần trả hàng trong ngày (0 nếu không có) |
| Returns | `daily_return_qty` | Tổng SL sản phẩm trả lại |
| Returns | `daily_refund_amount` | Tổng tiền hoàn lại (VND) |
| Shipments | `daily_shipments` | Số đơn được gửi đi trong ngày |
| Shipments | `avg_shipping_fee` | Phí ship trung bình (VND) |
| Shipments | `total_shipping_fee` | Tổng phí ship trong ngày |
| Payments | `avg_payment_value` | Giá trị thanh toán trung bình mỗi đơn |
| Payments | `avg_installments` | Số kỳ trả góp trung bình |
| Inventory | `inv_total_stock` | Tổng tồn kho (forward-fill từ tháng trước) |
| Inventory | `inv_total_received` | Tổng hàng nhập kho tháng trước |
| Inventory | `inv_avg_fill_rate` | Tỷ lệ đáp ứng đơn hàng TB |
| Inventory | `inv_avg_stockout_days` | Số ngày hết hàng TB (tháng trước) |
| Inventory | `inv_products_stockout` | Số SP bị hết hàng (tháng trước) |
| Inventory | `inv_products_overstock` | Số SP tồn kho quá mức (tháng trước) |
| Inventory | `inv_avg_sell_through` | Tỷ lệ bán hàng qua TB (tháng trước) |

> ⚠️ **Lưu ý Inventory:** Dữ liệu inventory là snapshot cuối tháng. Trong bảng daily, giá trị inventory của tháng trước được map cho tất cả các ngày của tháng hiện tại (forward-fill). Ví dụ: các ngày trong tháng 3/2020 sử dụng snapshot inventory của 28/02/2020.

---

## FAQ

**Q: Tại sao 4 file chứ không phải 3?**  
A: Ban đầu đề xuất 3 Data Marts, nhưng Data Mart 2 (Post-Sale) được tách thành `returns_enriched` + `reviews_enriched` vì chúng có grain khác nhau (1 đơn có thể trả nhiều sản phẩm nhưng review ở cấp sản phẩm riêng biệt). Tách ra giúp phân tích gọn hơn, tránh duplicate rows khi JOIN.

**Q: Cần rebuild khi nào?**  
A: Chỉ rebuild nếu dữ liệu source (`dataset/`) thay đổi. Chạy: `cd joined/ && python data_pipeline.py`

**Q: Sao không dùng CSV?**  
A: Parquet nén tốt hơn (~70%), đọc nhanh hơn 5-10x, và giữ nguyên data types (không bị mất kiểu date, int khi đọc lại). Đây là chuẩn industry cho analytical workloads.

**Q: Build riêng 1 Data Mart được không?**  
A: Được. Ví dụ `python data_pipeline.py --mart 1` chỉ build transaction_master.
