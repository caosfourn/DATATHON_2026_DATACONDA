import nbformat as nbf

nb = nbf.v4.new_notebook()

# Markdown: Title
nb.cells.append(nbf.v4.new_markdown_cell("""\
# 📊 07 - Modelling (Daily Revenue & COGS Forecasting)

**Mục tiêu**: Huấn luyện mô hình XGBoost dự báo Doanh thu (Revenue) và Giá vốn hàng bán (COGS) theo ngày cho 18 tháng (01/01/2023 - 01/07/2024).

**Phương pháp**: Để đảm bảo độ ổn định cho dự báo dài hạn (18 tháng) mà không bị nhiễu do thiếu hụt các đặc trưng nội sinh (lags/rolling), mô hình sẽ chỉ sử dụng các **Deterministic Features** (Calendar, Fourier, Promotion).
"""))

# Code: Imports & Setup
nb.cells.append(nbf.v4.new_code_cell("""\
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, r2_score
import warnings

warnings.filterwarnings('ignore')
plt.rcParams['figure.figsize'] = (14, 6)
sns.set_style('whitegrid')
"""))

# Markdown: Data Loading
nb.cells.append(nbf.v4.new_markdown_cell("""\
## 1. Load Data & Lọc Deterministic Features
"""))

# Code: Data Loading
nb.cells.append(nbf.v4.new_code_cell("""\
df = pd.read_csv('../dataset_cleaned/train_daily_forecasting.csv', parse_dates=['date'])
df = df.sort_values('date').reset_index(drop=True)

# Lọc các cột deterministic
calendar_cols = [c for c in df.columns if any(k in c for k in
        ['year', 'month', 'quarter', 'day_of', 'week_of', 'is_weekend',
         'is_month', 'is_quarter', 'is_tet', 'is_1111', 'is_1212'])]
fourier_cols = [c for c in df.columns if any(k in c for k in
        ['sin_', 'cos_', 'yearly_sin', 'yearly_cos', 'weekly_sin', 'weekly_cos',
         'monthly_sin', 'monthly_cos'])]
promo_cols = [c for c in df.columns if c.startswith('promo_active')
        or c.startswith('promo_max') or c.startswith('promo_avg')
        or c.startswith('promo_has_')]

feature_cols = calendar_cols + fourier_cols + promo_cols
print(f"Tổng số deterministic features: {len(feature_cols)}")
"""))

# Markdown: Split
nb.cells.append(nbf.v4.new_markdown_cell("""\
## 2. Train / Validation Split
Sử dụng năm 2022 làm tập Validation để đánh giá mô hình cục bộ.
"""))

# Code: Split
nb.cells.append(nbf.v4.new_code_cell("""\
train = df[df['date'].dt.year < 2022].copy()
val = df[df['date'].dt.year == 2022].copy()

X_train = train[feature_cols]
y_train_rev = train['revenue']
y_train_cogs = train['cogs']

X_val = val[feature_cols]
y_val_rev = val['revenue']
y_val_cogs = val['cogs']

print(f"Train set: {train['date'].min().date()} to {train['date'].max().date()} ({len(train)} days)")
print(f"Val set:   {val['date'].min().date()} to {val['date'].max().date()} ({len(val)} days)")
"""))

# Markdown: Training
nb.cells.append(nbf.v4.new_markdown_cell("""\
## 3. Huấn luyện mô hình (XGBoost)
"""))

# Code: Training
nb.cells.append(nbf.v4.new_code_cell("""\
# Train Revenue Model
model_rev = XGBRegressor(n_estimators=300, learning_rate=0.05, max_depth=6, random_state=42)
model_rev.fit(X_train, y_train_rev)

# Train COGS Model
model_cogs = XGBRegressor(n_estimators=300, learning_rate=0.05, max_depth=6, random_state=42)
model_cogs.fit(X_train, y_train_cogs)
"""))

# Markdown: Evaluation
nb.cells.append(nbf.v4.new_markdown_cell("""\
## 4. Đánh giá mô hình trên tập Validation (2022)
"""))

# Code: Evaluation
nb.cells.append(nbf.v4.new_code_cell("""\
preds_rev = model_rev.predict(X_val)
preds_cogs = model_cogs.predict(X_val)

def evaluate(y_true, y_pred, name):
    mae = mean_absolute_error(y_true, y_pred)
    me = np.mean(y_pred - y_true)
    r2 = r2_score(y_true, y_pred)
    print(f"--- {name} ---")
    print(f"MAE: {mae:,.0f}")
    print(f"ME : {me:,.0f} (Dương: Dự báo cao hơn thực tế, Âm: Dự báo thấp hơn thực tế)")
    print(f"R² : {r2:.4f}\\n")

evaluate(y_val_rev, preds_rev, "Revenue")
evaluate(y_val_cogs, preds_cogs, "COGS")

# Plot
fig, axes = plt.subplots(2, 1, figsize=(15, 10))

axes[0].plot(val['date'], y_val_rev, label='Actual Revenue', alpha=0.7)
axes[0].plot(val['date'], preds_rev, label='Predicted Revenue', alpha=0.7)
axes[0].set_title('Revenue: Actual vs Predicted (2022)')
axes[0].legend()

axes[1].plot(val['date'], y_val_cogs, label='Actual COGS', color='orange', alpha=0.7)
axes[1].plot(val['date'], preds_cogs, label='Predicted COGS', color='green', alpha=0.7)
axes[1].set_title('COGS: Actual vs Predicted (2022)')
axes[1].legend()

plt.tight_layout()
plt.show()
"""))

# Markdown: Feature Importances
nb.cells.append(nbf.v4.new_markdown_cell("""\
## 5. Khả năng Giải thích (Explainability) & Yếu tố dẫn động Doanh thu
"""))

# Code: Feature Importances
nb.cells.append(nbf.v4.new_code_cell("""\
def plot_importance(model, features, title, ax):
    importance = model.feature_importances_
    idx = np.argsort(importance)[-15:]  # Top 15
    ax.barh(np.array(features)[idx], importance[idx], color='steelblue')
    ax.set_title(title)

fig, axes = plt.subplots(1, 2, figsize=(16, 6))
plot_importance(model_rev, feature_cols, 'Top 15 Yếu tố dẫn động Revenue', axes[0])
plot_importance(model_cogs, feature_cols, 'Top 15 Yếu tố dẫn động COGS', axes[1])
plt.tight_layout()
plt.show()
"""))

# Markdown: Business Explanation
nb.cells.append(nbf.v4.new_markdown_cell("""\
### Giải thích Mô hình bằng Ngôn ngữ Kinh doanh
Dựa trên Feature Importances ở trên, các yếu tố chính dẫn động Doanh thu (Revenue) và Giá vốn (COGS) bao gồm:

1. **Yếu tố Khuyến mãi (Promotions)**: Các biến `promo_active_count` và `promo_active_flag` thường đóng vai trò quan trọng nhất. Khách hàng thời trang nhạy cảm với giá và có xu hướng chờ đợi các đợt Sale lớn (như Mid-Year, Year-End, 11/11). Sự hiện diện của các chương trình khuyến mãi kích thích lượng đơn hàng tăng vọt.
2. **Tính Mùa vụ hàng năm (Yearly Seasonality)**: `yearly_cos` và `yearly_sin` nắm bắt chu kỳ tăng giảm doanh số theo các thời điểm trong năm. Doanh số thường tăng mạnh vào cuối năm và các đợt chuyển mùa (nhu cầu thay đổi tủ đồ).
3. **Thứ trong tuần (Day of Week & Weekly Fourier)**: Yếu tố ngày trong tuần (đặc biệt là cuối tuần `is_weekend`) có ảnh hưởng mạnh đến hành vi mua sắm trực tuyến. Thông thường, lượng truy cập và chốt đơn cao hơn vào cuối tuần.
4. **Thời điểm trong tháng (Day of Month)**: Nhu cầu mua sắm thường tăng vào những ngày đầu tháng hoặc cuối tháng (kỳ trả lương).
"""))

# Markdown: Submission
nb.cells.append(nbf.v4.new_markdown_cell("""\
## 6. Dự báo cho Tập Test & Xuất file Submission
Tập Test kéo dài từ 01/01/2023 đến 01/07/2024.
Vì mô hình chỉ dùng các Deterministic Features, chúng ta sẽ sinh lại chính xác các biến này cho khoảng thời gian trên.
"""))

# Code: Submission Feature Gen
nb.cells.append(nbf.v4.new_code_cell("""\
sub = pd.read_csv('../dataset/sample_submission.csv')
sub['Date'] = pd.to_datetime(sub['Date'])

# Hàm tái tạo Deterministic Features
def create_future_features(dates):
    df_fut = pd.DataFrame({'date': dates})
    
    # Calendar
    df_fut['year'] = df_fut['date'].dt.year
    df_fut['month'] = df_fut['date'].dt.month
    df_fut['quarter'] = df_fut['date'].dt.quarter
    df_fut['day_of_week'] = df_fut['date'].dt.dayofweek
    df_fut['day_of_year'] = df_fut['date'].dt.dayofyear
    df_fut['week_of_year'] = df_fut['date'].dt.isocalendar().week.astype(int)
    df_fut['is_weekend'] = df_fut['day_of_week'].isin([5, 6]).astype(int)
    df_fut['day_of_month'] = df_fut['date'].dt.day
    df_fut['is_month_start'] = df_fut['date'].dt.is_month_start.astype(int)
    df_fut['is_month_end'] = df_fut['date'].dt.is_month_end.astype(int)
    df_fut['is_quarter_start'] = df_fut['date'].dt.is_quarter_start.astype(int)
    df_fut['is_quarter_end'] = df_fut['date'].dt.is_quarter_end.astype(int)
    df_fut['week_of_month'] = (df_fut['day_of_month'] - 1) // 7 + 1
    
    df_fut['is_tet_season'] = df_fut['month'].isin([1, 2]).astype(int)
    df_fut['is_1111'] = ((df_fut['month'] == 11) & (df_fut['day_of_month'] == 11)).astype(int)
    df_fut['is_1212'] = ((df_fut['month'] == 12) & (df_fut['day_of_month'] == 12)).astype(int)
    
    # Fourier
    df_fut['yearly_sin_1'] = np.sin(2 * np.pi * df_fut['day_of_year'] / 365.25)
    df_fut['yearly_cos_1'] = np.cos(2 * np.pi * df_fut['day_of_year'] / 365.25)
    df_fut['yearly_sin_2'] = np.sin(4 * np.pi * df_fut['day_of_year'] / 365.25)
    df_fut['yearly_cos_2'] = np.cos(4 * np.pi * df_fut['day_of_year'] / 365.25)
    df_fut['yearly_sin_3'] = np.sin(6 * np.pi * df_fut['day_of_year'] / 365.25)
    df_fut['yearly_cos_3'] = np.cos(6 * np.pi * df_fut['day_of_year'] / 365.25)
    
    df_fut['weekly_sin_1'] = np.sin(2 * np.pi * df_fut['day_of_week'] / 7)
    df_fut['weekly_cos_1'] = np.cos(2 * np.pi * df_fut['day_of_week'] / 7)
    df_fut['weekly_sin_2'] = np.sin(4 * np.pi * df_fut['day_of_week'] / 7)
    df_fut['weekly_cos_2'] = np.cos(4 * np.pi * df_fut['day_of_week'] / 7)
    
    df_fut['monthly_sin_1'] = np.sin(2 * np.pi * df_fut['day_of_month'] / 31)
    df_fut['monthly_cos_1'] = np.cos(2 * np.pi * df_fut['day_of_month'] / 31)
    df_fut['monthly_sin_2'] = np.sin(4 * np.pi * df_fut['day_of_month'] / 31)
    df_fut['monthly_cos_2'] = np.cos(4 * np.pi * df_fut['day_of_month'] / 31)
    
    # Promotion (Mock based on recurring periods: Spring, Mid-Year, Fall, Year-End)
    # Cố định khoảng thời gian: 18/3-17/4, 23/6-22/7, 30/8-1/10, 18/11-2/1
    def get_promo_flags(dt):
        md = dt.month * 100 + dt.day
        if (318 <= md <= 417) or (623 <= md <= 722) or (830 <= md <= 1001) or (md >= 1118 or md <= 102):
            return 1, 1, 0.3, 0.15, 1, 0 # giả định các thông số
        return 0, 0, 0.0, 0.0, 0, 0
        
    promo_sims = df_fut['date'].apply(get_promo_flags)
    df_fut['promo_active_count'] = [x[0] for x in promo_sims]
    df_fut['promo_active_flag'] = [x[1] for x in promo_sims]
    df_fut['promo_max_discount'] = [x[2] for x in promo_sims]
    df_fut['promo_avg_discount'] = [x[3] for x in promo_sims]
    df_fut['promo_has_percentage'] = [x[4] for x in promo_sims]
    df_fut['promo_has_fixed'] = [x[5] for x in promo_sims]
    
    return df_fut

# Tạo features
X_test = create_future_features(sub['Date'])[feature_cols]

# Do mô hình XGBoost ở trên huấn luyện đến 2021, ta nên huấn luyện lại trên TOÀN BỘ dữ liệu (2012-2022)
# để có dự báo tốt nhất cho 2023.
print("Retraining on full data (2012-2022)...")
model_rev_full = XGBRegressor(n_estimators=300, learning_rate=0.05, max_depth=6, random_state=42)
model_rev_full.fit(df[feature_cols], df['revenue'])

model_cogs_full = XGBRegressor(n_estimators=300, learning_rate=0.05, max_depth=6, random_state=42)
model_cogs_full.fit(df[feature_cols], df['cogs'])

# Dự báo
sub['Revenue'] = model_rev_full.predict(X_test)
sub['COGS'] = model_cogs_full.predict(X_test)

# Đảm bảo không có giá trị âm
sub['Revenue'] = sub['Revenue'].clip(lower=0)
sub['COGS'] = sub['COGS'].clip(lower=0)

# Lưu kết quả
sub_out = sub[['Date', 'Revenue', 'COGS']].copy()
# Format Date về chuỗi YYYY-MM-DD để khớp hoàn toàn với sample
sub_out['Date'] = sub_out['Date'].dt.strftime('%Y-%m-%d')
sub_out.to_csv('../dataset/submission.csv', index=False)
sub_out.to_csv('../submission.csv', index=False)

print("Đã lưu submission vào dataset/submission.csv")
print(sub_out.head())
"""))

nbf.write(nb, 'notebook/07_modelling.ipynb')
