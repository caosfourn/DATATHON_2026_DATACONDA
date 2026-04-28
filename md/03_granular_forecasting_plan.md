# KẾ HOẠCH DỰ BÁO NHU CẦU CHI TIẾT & TỐI ƯU HÓA HẬU CẦN (GRANULAR FORECASTING & LOGISTICS OPTIMIZATION)
*Định hướng phát triển mô hình Machine Learning cho bài toán Chuỗi cung ứng (Supply Chain) toàn quốc*

---

Dựa trên các phân tích Đơn biến (Univariate EDA) tổng quan ở cấp độ Công ty (Aggregate Level), để giải quyết trọn vẹn yêu cầu của bài toán Datathon: **"Dự báo chính xác ở mức chi tiết nhằm tối ưu phân bổ tồn kho và chuỗi logistics toàn quốc"**, chúng ta cần thực hiện kế hoạch chuyển đổi từ "Nhìn nhận Vĩ mô" sang "Action Vi mô".

Dưới đây là các Giai đoạn triển khai đề xuất cho vòng Modeling tiếp theo:

## PHẦN I: CÁC INSIGHT CHI TIẾT (GRANULAR INSIGHTS) CẦN ĐÀO SÂU TRONG BIVARIATE EDA

Thay vì chỉ nhìn vào Tổng Doanh Thu (Total Revenue), chúng ta cần bóc tách dữ liệu theo Không gian (Geography) và Hàng hóa (SKU/Category) để ra quyết định:

### 💡 Insight 6: Hiện tượng Lệch pha Mùa vụ theo Địa lý (Geographical Seasonality)
* **Giả thuyết:** Thời trang là ngành nhạy cảm với thời tiết. Spike doanh thu Quý 4 trên toàn sàn có thể chủ yếu đến từ nhu cầu áo lạnh/đồ đông ở khu vực Miền Bắc và Bắc Trung Bộ, trong khi khu vực Miền Nam vẫn tiếp tục tiêu thụ đồ hè.
* **Đề xuất Hành động (Logistics & Inventory):** Thay vì áp dụng công thức điều phối tồn kho chung cho toàn quốc, phân bổ Tồn kho (Inventory Allocation) phải được quy hoạch mảng áo lạnh nằm rải rác ở các Dark Store / Nhà kho Miền Bắc từ tháng 9. Điều này giúp rút ngắn lead-time giao hàng chặng cuối (Last-mile) và giảm chi phí vận chuyển liên vùng.

### 💡 Insight 7: Chuyển động Vòng đời Sản phẩm (Category Velocity & Intermittent Demand)
* **Giả thuyết:** Quần áo bao gồm những Category bán cực đều (ví dụ: Tất, Đồ lót cơ bản - Fast-moving), và những Category "bạo phát bạo tàn" (ví dụ: Đồ Trend, váy dự tiệc mùa lễ hội - Slow-moving).
* **Đề xuất Hành động (Warehouse & Promo):** Cấu trúc không gian kho bãi (Slotting/Space Allocation) phải linh hoạt. Các cụm mã lỗi mốt (dead-stock) cần được team Marketing đánh Flash Sale xả hàng ngay lập tức để giải phóng không gian nâng đỡ kệ chứa (Rack space) nhập các mã có tỷ suất Lợi nhuận gộp (Margin) cao.

### 💡 Insight 8: Tỷ lệ Hoàn hàng định hình chi phí Logistics ngược (Reverse Logistics)
* **Giả thuyết:** Doanh thu có thể tạo đỉnh cục bộ ở một nhóm khách hàng/khu vực cụ thể, nhưng nếu cụm địa lý đó có tỷ lệ "boom hàng" (Return rate) lớn, kho trung tâm sẽ "vỡ trận" do hàng hóa dội về phải chờ quy trình kiểm định (QC), giặt ủi và tái nhập kho.
* **Đề xuất Hành động:** Thêm tỷ lệ hoàn trả (Return Rate) làm một biến số để tính toán hao hụt khi dự báo và chốt công suất tải của đối tác giao hàng (3PL). 

---

## PHẦN II: KIẾN TRÚC MÔ HÌNH DỰ BÁO PHÂN CẤP (HIERARCHICAL FORECASTING ARCHITECTURE)

Để biến các Insights trên thành một mô hình Học máy (Machine Learning) thực chiến cho bài toán Tồn kho cấp SKU/Region, lộ trình sau đây được đề xuất:

### Bước 1: Chuyển đổi định dạng dữ liệu & Mức độ Hạt (Data Granularity Setup)
* Dừng hướng tiếp cận dự báo một chuỗi thời gian đơn biến (Univariate). Kiến trúc mới sẽ là **Dự báo chuỗi thời gian phân cấp (Hierarchical Time Series Forecasting)**.
* Định dạng dữ liệu huấn luyện (Training Set) không gộp tổng, mà bẻ gãy theo cấu trúc: `Date` x `Province/Region` x `Product Category`. Khi đó, ta có hàng chục ngàn chuỗi thời gian chạy song song.

### Bước 2: Xây dựng Hệ Đặc trưng (Feature Engineering)
* **Time Features:** Đưa các phát hiện từ EDA vào mô hình dưới dạng Dummy Variables: `is_week_3`, `is_week_4` (Chu kỳ tháng), `is_tuesday_wednesday` (Thung lũng), `is_mega_sale_Q4` (Mùa vụ).
* **External/Exogenous Features:** Bổ sung dữ liệu Thời tiết (Dự báo Nhiệt độ theo Region) và dữ liệu cờ Khuyến mãi (Promo Flag) áp dụng cho từng SKU.

### Bước 3: Lựa Chọn Mô Hình (Modeling Strategy)
* **Bỏ qua ARIMA/SARIMA truyền thống:** Các mô hình kinh điển chỉ xử lý tốt cho chuỗi vĩ mô. Tuy nhiên, khi hạ cấp độ xuống SKU/Tỉnh thành, dữ liệu sẽ cực kỳ nhiễu và chứa nhiều ngày đứt quãng không có đơn hàng (Giá trị bằng 0 - Intermittent demand).
* **Model Khuyến nghị:** Sử dụng các Global Machine Learning Model mạnh mẽ có khả năng xử lý phi tuyến tính, tích hợp tốt External Features như **XGBoost**, **LightGBM**, hoặc **CatBoost**. Tiên tiến hơn có thể dùng mạng học sâu (Deep Learning) thiết kế riêng cho chuỗi thời gian nhiều tập hợp như **Temporal Fusion Transformer (TFT)** hay **N-BEATS**. 
* **Multi-horizon:** Mở rộng cửa sổ output dự báo cùng lúc cho các khung thời gian 7/14/30 ngày tiếp theo.

### Bước 4: Tổng hợp Tồn kho (Reconciliation Strategy)
* **Mục tiêu:** Tính Cân Bằng (Coherence). Tổng số lượng dự báo hàng xuất đi ở kho Miền Bắc cộng với Miền Nam phải khớp chính xác với dự báo tổng nhu cầu xuất kho toàn quốc.
* **Triển khai:** Áp dụng phương pháp cân bằng **Bottom-Up** (dự báo từ cấp SKU cộng lên) hoặc **Middle-Out** (dự báo khu vực rồi chia tỷ lệ xuống cấp dưới). Output cuối cùng sẽ tự động tích hợp vào hệ thống máy chủ ERP, tạo lệnh chủ động thuê thêm đối tác Logisitcs hoặc báo động đỏ cảnh báo thiếu hàng lên team Thu mua.
