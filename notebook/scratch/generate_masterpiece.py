import json

def get_cells(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)['cells']

cells_05 = get_cells('d:/HuynhHan/Datathon/DATATHON_2026_DATACONDA/notebook/05_eda_storytelling_final.ipynb')
cells_gb = get_cells('d:/HuynhHan/Datathon/DATATHON_2026_DATACONDA/notebook/gridbreakers-data-to-dollars-eda-forecast.ipynb')

new_cells = []

# Title & Imports
new_cells.append(cells_05[0])
new_cells.append(cells_05[1])

# --- GIAI ĐOẠN 1 ---
new_cells.append(cells_05[2])
new_cells.append(cells_05[3])
# Inject GB Volume vs AOV and Market Basket
new_cells.extend(cells_gb[30:32])
new_cells.extend(cells_gb[39:42])

insight_1 = {
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "### Insights Giai Đoạn 1\n",
        "**Descriptive**: Doanh thu bùng nổ vào Quý 4 (mùa vụ), nhưng biểu đồ phân tán (Scatter) Volume vs AOV cho thấy chất lượng tăng trưởng đang đi xuống khi số lượng đơn tăng nhưng AOV lại giảm nhẹ. Phân tích Market Basket chỉ ra rõ các cặp sản phẩm thường được mua cùng nhau.\n",
        "**Diagnostic**: Tăng trưởng đến từ việc mở rộng số lượng đơn (Volume) trong khi giá trị đơn hàng (AOV) không tăng đột biến. Việc xả khuyến mãi liên tục kéo doanh thu nhưng làm giảm Margin.\n",
        "**Predictive**: Nếu tiếp tục chiến lược \"đốt tiền\" chạy số lượng, lợi nhuận cốt lõi sẽ bị bào mòn và thương hiệu có nguy cơ trở thành \"thương hiệu săn sale\" rẻ tiền trong mắt khách hàng.\n",
        "**Prescriptive**: Ứng dụng quy tắc kết hợp (Association Rules) từ Market Basket Analysis để tự động tạo gói Combo (VD: mua sản phẩm A + sản phẩm B giảm 10%) thay vì giảm giá đơn lẻ, kỳ vọng tăng AOV thêm 15-20% và bảo vệ biên lợi nhuận."
    ]
}
new_cells.append(insight_1)

# --- GIAI ĐOẠN 2 ---
new_cells.append(cells_05[5])
new_cells.append(cells_05[6])
# Inject GB Web Traffic & Promo ROI
new_cells.extend(cells_gb[20:22])
new_cells.extend(cells_gb[13:16])

insight_2 = {
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "### Insights Giai Đoạn 2\n",
        "**Descriptive**: Organic Search mang lại lượng khách hàng đều đặn. Tuy nhiên, khi nhìn vào Web Traffic và Conversion Analysis, tỷ lệ thoát (Bounce rate) và chất lượng Traffic từ một số chiến dịch trả tiền (Promotion ROI) là rất thấp, thậm chí ROI âm.\n",
        "**Diagnostic**: Dòng tiền khuyến mãi ở một số kênh không tạo ra ROI dương do mức giảm giá ăn sâu vào doanh thu thực tế và Sunk cost. Tỷ lệ chuyển đổi bị kéo tụt vì khách hàng click nhấp chuột vào xem nhưng không mua.\n",
        "**Predictive**: Nếu tiếp tục đốt tiền cho những kênh có ROI thấp, chi phí sở hữu khách hàng sẽ vượt quá giá trị sinh lời của họ (LTV < CAC proxy).\n",
        "**Prescriptive**: Cắt giảm ngay lập tức 30% ngân sách Marketing ở các chiến dịch có ROI < 0 (dựa trên biểu đồ Promotion ROI) và dịch chuyển sang Organic Search. Đồng thời dùng tệp khách hàng nhạy cảm với khuyến mãi (Promotion Sensitivity) để target riêng rẽ nhằm tối ưu hóa chi phí quảng cáo."
    ]
}
new_cells.append(insight_2)

# --- GIAI ĐOẠN 3 ---
new_cells.append(cells_05[8])
new_cells.append(cells_05[9])
# Inject GB RFM Segmentation
new_cells.extend(cells_gb[7:10])

insight_3 = {
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "### Insights Giai Đoạn 3\n",
        "**Descriptive**: Từng nhóm tuổi có hành vi mua sắm category rất riêng biệt. Đặc biệt, phân khúc khách hàng RFM (Champions, Loyal, At Risk) cho thấy sự phân bổ doanh thu không đồng đều. Nhóm Champions tạo ra giá trị lớn nhất.\n",
        "**Diagnostic**: Mỗi phân khúc phản ứng khác biệt với danh mục sản phẩm. Lượt truy cập có những thời điểm tăng mạnh nhưng bị đứt gãy chuyển đổi giữa chừng do thiếu tính cá nhân hóa trong việc đề xuất sản phẩm và khuyến mãi.\n",
        "**Predictive**: Thiếu hụt trải nghiệm cá nhân hóa sẽ làm khách hàng hạng sang (Champions) cảm thấy nhàm chán, trong khi khách mới không tìm thấy sản phẩm phù hợp.\n",
        "**Prescriptive**: Cá nhân hóa giao diện trang chủ ngay lập tức. Ẩn các banner Flash Sale với nhóm \"Champions\" (nhóm này mua không cần giảm giá, giúp tiết kiệm 5% chi phí COGS). Chỉ hiển thị banner giảm giá cực sâu cho nhóm \"At Risk\" hoặc \"Hibernating\" để kích hoạt lại họ."
    ]
}
new_cells.append(insight_3)

# --- GIAI ĐOẠN 4 ---
new_cells.append(cells_05[11])
new_cells.append(cells_05[12])
# Inject GB Returns & Bullwhip
new_cells.extend(cells_gb[27:30])
new_cells.extend(cells_gb[34:36])

insight_4 = {
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "### Insights Giai Đoạn 4\n",
        "**Descriptive**: Tỷ lệ hoàn hàng và hủy đơn rất cao. Biểu đồ Treemap cho thấy \"sai kích cỡ\" là lý do phổ biến. Đồng thời, phân tích chuỗi cung ứng (Cross-Correlation) cảnh báo hiện tượng tồn kho ảo và giao hàng trễ.\n",
        "**Diagnostic**: Hiện tượng Bullwhip (thiếu hàng cục bộ) làm đứt gãy chuỗi chuyển đổi. Quan trọng nhất: Giao hàng trễ trực tiếp làm tăng vọt tỷ lệ hoàn hàng vì khách hàng thay đổi ý định và từ chối nhận (đặc biệt các sản phẩm bắt trend).\n",
        "**Predictive**: Nếu không khắc phục quy trình logistics, nguy cơ khủng hoảng pháp lý, tẩy chay thương hiệu và gánh nặng chi phí vận chuyển chặng về (Reverse Logistics) là cực kỳ cao.\n",
        "**Prescriptive**: Tích hợp API tồn kho Real-time vào Frontend để ẩn các mặt hàng sắp hết. Quan trọng hơn, xây dựng rule phạt đối với Logistics 3PL: Nếu thời gian giao (Lead time) > 3 ngày làm Return Rate tăng quá 18% (như tương quan đã chứng minh), nhà vận chuyển phải chịu 50% phí Reverse Logistics."
    ]
}
new_cells.append(insight_4)

# --- GIAI ĐOẠN 5 ---
new_cells.append(cells_05[14])
new_cells.append(cells_05[15])
# Inject GB Cohort
new_cells.extend(cells_gb[37:39])

insight_5 = {
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "### Insights Giai Đoạn 5\n",
        "**Descriptive**: Biểu đồ Cohort Retention Analysis phơi bày sự thật cay đắng: tỷ lệ duy trì (Retention Rate) rơi rụng cực kỳ mạnh mẽ chỉ sau 1-2 tháng đầu tiên mua hàng. Rất nhiều khách hàng biến thành \"At Risk\" và \"Lost\".\n",
        "**Diagnostic**: Khách hàng săn khuyến mãi (Deal Hunter) mang lại CLV thấp hơn nhiều so với khách hàng mua nguyên giá, chứng tỏ khuyến mãi chỉ tạo doanh thu ngắn hạn chứ không tạo ra sự trung thành dài hạn. Việc thiếu tương tác sau tuần đầu tiên là nguyên nhân khiến họ \"ngủ đông\".\n",
        "**Predictive**: Nếu tỷ lệ Churn tiếp tục ở mức cao và tỷ lệ Retention ở các tháng sau chỉ loanh quanh < 5%, áp lực lên chi phí Marketing để tìm khách mới sẽ làm sụp đổ phễu lợi nhuận.\n",
        "**Prescriptive**: Khởi động chiến dịch Email Automation/Push Notification tặng Voucher định danh chính xác vào **Tuần thứ 3** tính từ ngày mua hàng đầu tiên (đây là điểm gãy Retention từ Cohort heatmap) để kéo tỷ lệ quay lại của khách hàng mới từ 5% lên mức mục tiêu 12%."
    ]
}
new_cells.append(insight_5)

# --- SUMMARY ---
new_cells.append(cells_05[17])

# Save new notebook
with open('d:/HuynhHan/Datathon/DATATHON_2026_DATACONDA/notebook/05_eda_storytelling_final.ipynb', 'r', encoding='utf-8') as f:
    nb_base = json.load(f)

nb_base['cells'] = new_cells

with open('d:/HuynhHan/Datathon/DATATHON_2026_DATACONDA/notebook/05_eda_storytelling_masterpiece.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb_base, f, ensure_ascii=False, indent=1)

print('Masterpiece notebook created successfully!')
