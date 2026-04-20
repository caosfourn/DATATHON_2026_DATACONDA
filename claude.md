# DATATHON 2026 — The Gridbreaker
## Tổng quan bài toán

Bộ dữ liệu mô phỏng hoạt động của một **doanh nghiệp thời trang thương mại điện tử tại Việt Nam**, giai đoạn **04/07/2012 – 31/12/2022** (train) và **01/01/2023 – 01/07/2024** (test).

Cuộc thi gồm **3 phần**:
- **Phần 1 (20đ):** Câu hỏi trắc nghiệm — tính toán trực tiếp từ dữ liệu
- **Phần 2 (60đ):** Trực quan hoá & Phân tích EDA — data storytelling 4 cấp độ
- **Phần 3 (20đ):** Mô hình dự báo doanh thu (Sales Forecasting)

---

## Cấu trúc dữ liệu

### Lớp Master (dữ liệu tham chiếu)

**`products.csv`**
| Cột | Kiểu | Mô tả |
|---|---|---|
| product_id | int | PK |
| product_name | str | Tên sản phẩm |
| category | str | Danh mục |
| segment | str | Phân khúc (Premium / Performance / Activewear / Standard) |
| size | str | Kích cỡ (S/M/L/XL) |
| color | str | Màu sắc |
| price | float | Giá bán lẻ |
| cogs | float | Giá vốn (`cogs < price` luôn đúng) |

**`customers.csv`**
| Cột | Kiểu | Mô tả |
|---|---|---|
| customer_id | int | PK |
| zip | int | FK → geography.zip |
| city | str | Thành phố |
| signup_date | date | Ngày đăng ký |
| gender | str | nullable |
| age_group | str | Nhóm tuổi (nullable) |
| acquisition_channel | str | Kênh tiếp thị (nullable) |

**`promotions.csv`**
| Cột | Kiểu | Mô tả |
|---|---|---|
| promo_id | str | PK |
| promo_name | str | Tên chiến dịch |
| promo_type | str | `percentage` hoặc `fixed` |
| discount_value | float | Giá trị giảm |
| start_date / end_date | date | Thời gian hiệu lực |
| applicable_category | str | Danh mục áp dụng (null = tất cả) |
| promo_channel | str | Kênh phân phối (nullable) |
| stackable_flag | int | Cho phép gộp nhiều khuyến mãi |
| min_order_value | float | Giá trị đơn tối thiểu (nullable) |

> **Công thức giảm giá:**
> - `percentage`: `discount_amount = quantity × unit_price × (discount_value / 100)`
> - `fixed`: `discount_amount = quantity × discount_value`

**`geography.csv`**
| Cột | Kiểu | Mô tả |
|---|---|---|
| zip | int | PK |
| city | str | Thành phố |
| region | str | Vùng địa lý (West / Central / East) |
| district | str | Quận/huyện |

---

### Lớp Transaction

**`orders.csv`**
| Cột | Kiểu | Mô tả |
|---|---|---|
| order_id | int | PK |
| order_date | date | Ngày đặt hàng |
| customer_id | int | FK → customers |
| zip | int | FK → geography |
| order_status | str | `pending / shipped / delivered / cancelled / returned` |
| payment_method | str | Phương thức thanh toán |
| device_type | str | Thiết bị đặt hàng |
| order_source | str | Kênh marketing |

**`order_items.csv`**
| Cột | Kiểu | Mô tả |
|---|---|---|
| order_id | int | FK → orders |
| product_id | int | FK → products |
| quantity | int | Số lượng |
| unit_price | float | Đơn giá sau khuyến mãi |
| discount_amount | float | Tổng tiền giảm cho dòng này |
| promo_id | str | FK → promotions (nullable) |
| promo_id_2 | str | Khuyến mãi thứ hai (nullable) |

**`payments.csv`** — Quan hệ 1:1 với orders
| Cột | Kiểu | Mô tả |
|---|---|---|
| order_id | int | FK → orders |
| payment_method | str | Phương thức thanh toán |
| payment_value | float | Tổng giá trị thanh toán |
| installments | int | Số kỳ trả góp |

**`shipments.csv`** — Chỉ tồn tại cho đơn `shipped / delivered / returned`
| Cột | Kiểu | Mô tả |
|---|---|---|
| order_id | int | FK → orders |
| ship_date | date | Ngày gửi hàng |
| delivery_date | date | Ngày giao hàng |
| shipping_fee | float | Phí vận chuyển (0 nếu miễn phí) |

**`returns.csv`**
| Cột | Kiểu | Mô tả |
|---|---|---|
| return_id | str | PK |
| order_id | int | FK → orders |
| product_id | int | FK → products |
| return_date | date | Ngày trả hàng |
| return_reason | str | Lý do (defective / wrong_size / changed_mind / not_as_described / ...) |
| return_quantity | int | Số lượng trả |
| refund_amount | float | Số tiền hoàn lại |

**`reviews.csv`** — Chỉ ~20% đơn `delivered` có đánh giá
| Cột | Kiểu | Mô tả |
|---|---|---|
| review_id | str | PK |
| order_id | int | FK → orders |
| product_id | int | FK → products |
| customer_id | int | FK → customers |
| review_date | date | Ngày đánh giá |
| rating | int | Điểm 1–5 |
| review_title | str | Tiêu đề đánh giá |

---

### Lớp Analytical

**`sales.csv`** (train) / **`sales_test.csv`** (test — không công bố, dùng để chấm trên Kaggle)
| Cột | Kiểu | Mô tả |
|---|---|---|
| Date | date | Ngày đặt hàng |
| Revenue | float | Tổng doanh thu thuần |
| COGS | float | Tổng giá vốn hàng bán |

| Split | File | Khoảng thời gian |
|---|---|---|
| Train | sales.csv | 04/07/2012 – 31/12/2022 |
| Test | sales_test.csv | 01/01/2023 – 01/07/2024 |

---

### Lớp Operational

**`inventory.csv`** — Snapshot cuối tháng, 1 dòng/sản phẩm/tháng
| Cột | Kiểu | Mô tả |
|---|---|---|
| snapshot_date | date | Ngày chụp (cuối tháng) |
| product_id | int | FK → products |
| stock_on_hand | int | Tồn kho cuối tháng |
| units_received | int | Nhập kho trong tháng |
| units_sold | int | Bán ra trong tháng |
| stockout_days | int | Số ngày hết hàng |
| days_of_supply | float | Số ngày tồn kho đáp ứng được |
| fill_rate | float | Tỷ lệ đơn được đáp ứng đủ |
| stockout_flag | int | Flag hết hàng |
| overstock_flag | int | Flag tồn kho vượt mức |
| reorder_flag | int | Flag cần tái đặt hàng |
| sell_through_rate | float | Tỷ lệ hàng đã bán / tổng hàng sẵn có |
| product_name, category, segment | str | Denormalized từ products |
| year, month | int | Trích từ snapshot_date |

**`web_traffic.csv`** — Daily
| Cột | Kiểu | Mô tả |
|---|---|---|
| date | date | Ngày ghi nhận |
| sessions | int | Tổng phiên truy cập |
| unique_visitors | int | Khách truy cập duy nhất |
| page_views | int | Tổng lượt xem trang |
| bounce_rate | float | Tỷ lệ thoát (chỉ xem 1 trang) |
| avg_session_duration_sec | float | Thời gian trung bình mỗi phiên (giây) |
| traffic_source | str | Kênh nguồn (organic_search / paid_search / email_campaign / social_media / ...) |

---

## Quan hệ giữa các bảng

| Quan hệ | Cardinality |
|---|---|
| orders ↔ payments | 1 : 1 |
| orders ↔ shipments | 1 : 0..1 (chỉ shipped/delivered/returned) |
| orders ↔ returns | 1 : 0..N (chỉ returned) |
| orders ↔ reviews | 1 : 0..N (chỉ delivered, ~20%) |
| order_items ↔ promotions | N : 0..1 |
| products ↔ inventory | 1 : N (1 dòng/sản phẩm/tháng) |

---

## Phần 3 — Sales Forecasting

### Bài toán
Dự báo cột `Revenue` theo ngày cho giai đoạn **01/01/2023 – 01/07/2024**.

### Chỉ số đánh giá
- **MAE** (Mean Absolute Error) — thấp hơn tốt hơn
- **RMSE** (Root Mean Squared Error) — thấp hơn tốt hơn, phạt nặng outlier
- **R²** (Coefficient of Determination) — cao hơn tốt hơn, lý tưởng gần 1

### Định dạng file nộp (`submission.csv`)
```
Date,Revenue,COGS
2023-01-01,26607.2,2585.15
2023-01-02,1007.89,163.0
...
```
Giữ đúng thứ tự dòng như `sample_submission.csv`, không sắp xếp lại.

### Ràng buộc quan trọng
1. **Không dùng dữ liệu ngoài** — mọi feature phải từ các file được cung cấp.
2. **Không dùng Revenue/COGS từ tập test làm feature** (data leakage → bị loại).
3. **Reproducibility** — đặt random seed, đính kèm toàn bộ mã nguồn.
4. **Explainability** — báo cáo phải có giải thích feature importance / SHAP values bằng ngôn ngữ kinh doanh.
5. Cross-validation phải theo **chiều thời gian** (time-series split, không dùng random split).

---

## Phần 2 — EDA & Visualisation (60đ)

Phân tích tự do, đánh giá theo 4 cấp độ tăng dần:

| Cấp độ | Câu hỏi | Mô tả |
|---|---|---|
| Descriptive | What happened? | Thống kê tổng hợp, biểu đồ có nhãn rõ |
| Diagnostic | Why did it happen? | Giả thuyết nhân quả, phân tích bất thường |
| Predictive | What is likely? | Ngoại suy xu hướng, tính mùa vụ |
| Prescriptive | What should we do? | Đề xuất hành động, đánh đổi định lượng |

Đội đạt **Prescriptive nhất quán** trên nhiều phân tích sẽ đạt điểm cao nhất.
