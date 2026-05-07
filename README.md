# DATATHON 2026 — The Gridbreaker 
### Breaking Business Boundaries
> VinTelligence — VinUniversity Data Science & AI Club

---

##  Tổng Quan

Bộ dữ liệu mô phỏng hoạt động của một **doanh nghiệp thời trang thương mại điện tử tại Việt Nam**, giai đoạn **04/07/2012 – 31/12/2022** (train) và **01/01/2023 – 01/07/2024** (test).

Cuộc thi gồm **3 phần**:
- **Phần 1 (20đ):** 10 câu hỏi trắc nghiệm — tính toán trực tiếp từ dữ liệu
- **Phần 2 (60đ):** Trực quan hoá & Phân tích EDA — data storytelling 4 cấp độ
- **Phần 3 (20đ):** Mô hình dự báo doanh thu (Sales Forecasting)

---

##  Cấu Trúc Thư Mục

```text
DATATHON_2026_DATACONDA/
│
├── dataset/                    #    Dữ liệu thô (15 file CSV từ BTC)
│   ├── products.csv            #    Master — Danh mục sản phẩm
│   ├── customers.csv           #    Master — Thông tin khách hàng
│   ├── promotions.csv          #    Master — Chiến dịch khuyến mãi
│   ├── geography.csv           #    Master — Địa lý vùng miền
│   ├── orders.csv              #    Transaction — Đơn hàng
│   ├── order_items.csv         #    Transaction — Chi tiết đơn hàng
│   ├── payments.csv            #    Transaction — Thanh toán
│   ├── shipments.csv           #    Transaction — Vận chuyển
│   ├── returns.csv             #    Transaction — Trả hàng
│   ├── reviews.csv             #    Transaction — Đánh giá
│   ├── sales.csv               #    Analytical — Doanh thu train
│   ├── sample_submission.csv   #    Analytical — Mẫu file nộp
│   ├── inventory.csv           #    Operational — Tồn kho (monthly)
│   └── web_traffic.csv         #    Operational — Web traffic (daily)
│
├── dataset_cleaned/            #    Dữ liệu sau khi làm sạch từ cleaning pipeline
│                               #    Đã xử lý missing values, outliers, và bugs
│
├── dashboard/                  #    Streamlit dashboard (EDA Storytelling)
│   ├── app.py                  #    Application entry point
│   ├── requirements.txt        #    UI dependencies riêng biệt
│   ├── utils/                  #    Dashboard utilities
│   └── views/                  #    UI views cho các phases
│
├── joined/                     #    Data Engineering — Pipeline & Data Marts
│   ├── __init__.py             #    Package init (cho import từ notebook)
│   ├── data_pipeline.py        #    Script build 4 Data Marts
│   └── marts/                  #    Output: 4 file Parquet đã JOIN
│       ├── README.md           #    Tài liệu chi tiết từng Data Mart
│       ├── transaction_master.parquet
│       ├── returns_enriched.parquet
│       ├── reviews_enriched.parquet
│       └── daily_summary.parquet
│
├── notebook/                   #   Notebooks phân tích
│   ├── 01_data_audit_and_split.ipynb
│   ├── 02_univariate_eda.ipynb
│   ├── 03_bivariate_diagnostics.ipynb
│   ├── 04_feature_engineering.ipynb
│   ├── 05_eda_storytelling.ipynb
│   ├── 06_modelling.ipynb
│   └── mcq.ipynb
│
├── data_cleaning.py            #    Script làm sạch dữ liệu tự động (ETL)
├── data_validation.py          #    Script validate dữ liệu tự động (DuckDB)
├── fix_notebook.py             #    Script update & fix lỗi tự động cho notebook
├── requirements.txt            
└── README.md                   
```

---

##  Hướng Dẫn Setup

### 1. Tạo môi trường Python
```bash
python3 -m venv .venv

# Windows:
# .venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Tiền xử lý dữ liệu (Data Engineer)
Thực hiện làm sạch dữ liệu và kiểm tra tính toàn vẹn:
```bash
python data_cleaning.py
python data_validation.py
```

### 3. Build Data Marts
```bash
cd joined/
python data_pipeline.py          
python data_pipeline.py --mart 1 
cd ..
```

### 4. Khởi chạy Dashboard (Storytelling)
```bash
cd dashboard/
streamlit run app.py
```

### 5. Sử dụng trong Notebook (BA / Data Scientist)
```python
import sys; sys.path.insert(0, '..')
from joined.data_pipeline import (
    load_transaction_master,    
    load_returns_enriched,      
    load_reviews_enriched,      
    load_daily_summary,         
)

df = load_transaction_master()
```

---

## Phân Công Nhóm

| Vai trò | Trọng tâm |
|---|---|
| **Data Engineer** | Pipeline, Data Marts, Data Cleaning/Validation, Trắc nghiệm (Phần 1) |
| **Business Analyst** | Storytelling EDA (Phần 2), Báo cáo LaTeX, Streamlit App |
| **Data Scientist 1** | Forecast model (Phần 3), Kaggle submission |
| **Data Scientist 2** | Code EDA biểu đồ (Phần 2), Feature Engineering |

---

## Dependencies

Xem chi tiết tại [requirements.txt](requirements.txt).