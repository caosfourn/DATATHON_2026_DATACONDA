"""
Build Training Dataset for Revenue & COGS Forecasting (v2)
============================================================
PK: date | Targets: revenue, cogs
Sources: daily_summary.parquet + features_daily_train.csv + reviews.csv
         + promotions.csv + order_items.csv + orders.csv + products.csv

⚠️  Leakage-safe: tất cả features tính từ dữ liệu thực tế đều dùng lag ≥ 1.
    Chỉ Calendar & Promotion (deterministic) được dùng cùng ngày.
"""

import pandas as pd
import numpy as np
import warnings
import os

warnings.filterwarnings('ignore')

# ─── Paths ──────────────────────────────────────────────────────────────────
DATA_DIR = "dataset_cleaned"
MART_DIR = "joined/marts"
OUTPUT = os.path.join(DATA_DIR, "train_daily_forecasting.csv")

# Lag depths — theo yêu cầu: không quá nhiều, tránh chồng chéo
LAG_DAYS = [3, 7, 15, 30]
ROLLING_WINDOWS = [3, 7, 15, 30]

# ═══════════════════════════════════════════════════════════════════════════
# STEP 1: Load Base Data — daily_summary
# ═══════════════════════════════════════════════════════════════════════════
print("=" * 70)
print("🚀 BUILD TRAINING DATASET — Revenue & COGS Forecasting (v2)")
print("=" * 70)

print("\n📂 [Step 1] Loading daily_summary.parquet (base)...")
ds = pd.read_parquet(f"{MART_DIR}/daily_summary.parquet")
ds['date'] = pd.to_datetime(ds['date'])
ds = ds.sort_values('date').reset_index(drop=True)
print(f"   Shape: {ds.shape}")
print(f"   Date range: {ds['date'].min().date()} → {ds['date'].max().date()}")

# ═══════════════════════════════════════════════════════════════════════════
# STEP 2: Load pre-computed features (calendar, fourier, cat/seg shares, etc.)
# ═══════════════════════════════════════════════════════════════════════════
print("\n📂 [Step 2] Loading features_daily_train.csv...")
feat = pd.read_csv(f"{DATA_DIR}/features_daily_train.csv", parse_dates=['date'])

# Chỉ lấy các cột KHÔNG trùng với daily_summary (trừ 'date' để merge)
overlap_cols = set(ds.columns) - {'date'}
feat_extra_cols = [c for c in feat.columns if c not in overlap_cols]
feat_extra = feat[feat_extra_cols]
print(f"   Extra features from features file: {len(feat_extra.columns) - 1} cols")

# Merge
df = ds.merge(feat_extra, on='date', how='left')
print(f"   After merge with features: {df.shape}")

# ═══════════════════════════════════════════════════════════════════════════
# STEP 3: Add Review features (aggregate by date)
# ═══════════════════════════════════════════════════════════════════════════
print("\n📂 [Step 3] Adding review features...")
reviews = pd.read_csv(f"{DATA_DIR}/reviews.csv", parse_dates=['review_date'])
rev_daily = reviews.groupby('review_date').agg(
    daily_reviews=('review_id', 'count'),
    avg_rating=('rating', 'mean'),
    rating_std=('rating', 'std'),
    low_ratings=('rating', lambda x: (x <= 2).sum()),
    high_ratings=('rating', lambda x: (x >= 4).sum()),
).reset_index().rename(columns={'review_date': 'date'})
rev_daily['date'] = pd.to_datetime(rev_daily['date'])

df = df.merge(rev_daily, on='date', how='left')
df[['daily_reviews', 'low_ratings', 'high_ratings']] = \
    df[['daily_reviews', 'low_ratings', 'high_ratings']].fillna(0)
print(f"   Review features added: daily_reviews, avg_rating, rating_std, low/high_ratings")

# ═══════════════════════════════════════════════════════════════════════════
# STEP 4: Add Promotion features (DETERMINISTIC — biết trước, không leakage)
# ═══════════════════════════════════════════════════════════════════════════
print("\n📂 [Step 4] Adding promotion features (deterministic)...")
promo = pd.read_csv(f"{DATA_DIR}/promotions.csv", parse_dates=['start_date', 'end_date'])

# Với mỗi ngày, đếm số promo đang active và lấy max discount
date_range = pd.date_range(df['date'].min(), df['date'].max(), freq='D')
promo_features = []
for d in date_range:
    active = promo[(promo['start_date'] <= d) & (promo['end_date'] >= d)]
    promo_features.append({
        'date': d,
        'promo_active_count': len(active),
        'promo_active_flag': 1 if len(active) > 0 else 0,
        'promo_max_discount': active['discount_value'].max() if len(active) > 0 else 0,
        'promo_avg_discount': active['discount_value'].mean() if len(active) > 0 else 0,
        # Promotion type flags
        'promo_has_percentage': 1 if (active['promo_type'] == 'percentage').any() else 0,
        'promo_has_fixed': 1 if (active['promo_type'] == 'fixed').any() else 0,
    })
promo_df = pd.DataFrame(promo_features)
df = df.merge(promo_df, on='date', how='left')
print(f"   Promotion features: promo_active_count/flag, max/avg_discount, type flags")

# ═══════════════════════════════════════════════════════════════════════════
# STEP 5: Feature Engineering — LEAKAGE-SAFE
# ═══════════════════════════════════════════════════════════════════════════
print("\n⚙️  [Step 5] Engineering features (leakage-safe)...")
print("   ⚠️  Tất cả lag/rolling features đều dùng shift(1) trở lên!")

# ─── 5.1 Revenue lag & rolling (shifted — chỉ dùng quá khứ) ─────────────
for lag in LAG_DAYS:
    df[f'revenue_lag_{lag}'] = df['revenue'].shift(lag)

# Rolling: .shift(1) trước khi rolling → window kết thúc tại t-1
rev_shifted = df['revenue'].shift(1)
for w in ROLLING_WINDOWS:
    df[f'revenue_ma_{w}'] = rev_shifted.rolling(w, min_periods=1).mean()
    df[f'revenue_std_{w}'] = rev_shifted.rolling(w, min_periods=1).std()

# EWM (shifted)
df['revenue_ewm_7'] = rev_shifted.ewm(span=7).mean()
df['revenue_ewm_30'] = rev_shifted.ewm(span=30).mean()

# ─── 5.2 COGS lag & rolling (shifted) ───────────────────────────────────
for lag in LAG_DAYS:
    df[f'cogs_lag_{lag}'] = df['cogs'].shift(lag)

cogs_shifted = df['cogs'].shift(1)
for w in ROLLING_WINDOWS:
    df[f'cogs_ma_{w}'] = cogs_shifted.rolling(w, min_periods=1).mean()
    df[f'cogs_std_{w}'] = cogs_shifted.rolling(w, min_periods=1).std()

df['cogs_ewm_7'] = cogs_shifted.ewm(span=7).mean()
df['cogs_ewm_30'] = cogs_shifted.ewm(span=30).mean()

# ─── 5.3 Margin/ratio features (LAGGED — tránh leakage) ─────────────────
# Tính ratio cùng ngày → shift toàn bộ để dùng cho forecast
cogs_ratio = df['cogs'] / df['revenue'].replace(0, np.nan)
gross_margin = (df['revenue'] - df['cogs']) / df['revenue'].replace(0, np.nan)

df['cogs_ratio_lag1'] = cogs_ratio.shift(1)
df['cogs_ratio_ma7'] = cogs_ratio.shift(1).rolling(7, min_periods=1).mean()
df['gross_margin_lag1'] = gross_margin.shift(1)
df['gross_margin_ma7'] = gross_margin.shift(1).rolling(7, min_periods=1).mean()
df['gross_margin_ma30'] = gross_margin.shift(1).rolling(30, min_periods=1).mean()

# ─── 5.4 Order features (LAGGED) ────────────────────────────────────────
orders_shifted = df['total_orders'].shift(1)
df['total_orders_lag1'] = orders_shifted
df['unique_customers_lag1'] = df['unique_customers'].shift(1)

# AOV (Average Order Value) — lagged
aov = df['revenue'] / df['total_orders'].replace(0, np.nan)
df['aov_lag1'] = aov.shift(1)
df['aov_ma7'] = aov.shift(1).rolling(7, min_periods=1).mean()
df['aov_ma30'] = aov.shift(1).rolling(30, min_periods=1).mean()

# Items per order — lagged
ipo = df['total_items_sold'] / df['total_orders'].replace(0, np.nan)
df['items_per_order_lag1'] = ipo.shift(1)
df['items_per_order_ma7'] = ipo.shift(1).rolling(7, min_periods=1).mean()

# Order status ratios — lagged
cancel_rate = df['cancelled_orders'] / df['total_orders'].replace(0, np.nan)
delivery_rate = df['delivered_orders'] / df['total_orders'].replace(0, np.nan)
df['cancel_rate_lag1'] = cancel_rate.shift(1)
df['cancel_rate_ma7'] = cancel_rate.shift(1).rolling(7, min_periods=1).mean()
df['delivery_rate_lag1'] = delivery_rate.shift(1)

# ─── 5.5 Return features (LAGGED) ───────────────────────────────────────
return_rate = df['daily_returns'] / df['total_orders'].replace(0, np.nan)
df['return_rate_lag1'] = return_rate.shift(1)
df['return_rate_ma7'] = return_rate.shift(1).rolling(7, min_periods=1).mean()
df['daily_refund_lag1'] = df['daily_refund_amount'].shift(1)

# ─── 5.6 Web traffic features (LAGGED) ──────────────────────────────────
df['total_sessions_lag1'] = df['total_sessions'].shift(1)
df['total_visitors_lag1'] = df['total_visitors'].shift(1)

sessions_shifted = df['total_sessions'].shift(1)
visitors_shifted = df['total_visitors'].shift(1)
for w in [7, 15, 30]:
    df[f'sessions_ma_{w}'] = sessions_shifted.rolling(w, min_periods=1).mean()
    df[f'visitors_ma_{w}'] = visitors_shifted.rolling(w, min_periods=1).mean()

df['avg_bounce_rate_lag1'] = df['avg_bounce_rate'].shift(1)

# Conversion rate — lagged
conversion_rate = df['total_orders'] / df['total_sessions'].replace(0, np.nan)
df['conversion_rate_lag1'] = conversion_rate.shift(1)
df['conversion_rate_ma7'] = conversion_rate.shift(1).rolling(7, min_periods=1).mean()

# ─── 5.7 Shipment features (LAGGED) ─────────────────────────────────────
df['daily_shipments_lag1'] = df['daily_shipments'].shift(1)
df['avg_shipping_fee_lag1'] = df['avg_shipping_fee'].shift(1)
df['total_shipping_fee_lag1'] = df['total_shipping_fee'].shift(1)

# ─── 5.8 Payment features (LAGGED) ──────────────────────────────────────
df['avg_payment_value_lag1'] = df['avg_payment_value'].shift(1)
df['avg_installments_lag1'] = df['avg_installments'].shift(1)

# ─── 5.9 Discount features (LAGGED) ─────────────────────────────────────
df['total_discount_lag1'] = df['total_discount'].shift(1)
df['avg_discount_lag1'] = df['avg_discount_per_line'].shift(1)
df['promo_pct_lag1'] = df['promo_pct'].shift(1)
df['promo_pct_ma7'] = df['promo_pct'].shift(1).rolling(7, min_periods=1).mean()

# ─── 5.10 Review rolling features (LAGGED) ──────────────────────────────
df['avg_rating_lag1'] = df['avg_rating'].shift(1)
df['avg_rating_ma7'] = df['avg_rating'].shift(1).rolling(7, min_periods=1).mean()
df['avg_rating_ma30'] = df['avg_rating'].shift(1).rolling(30, min_periods=1).mean()
df['reviews_ma7'] = df['daily_reviews'].shift(1).rolling(7, min_periods=1).mean()

# ─── 5.11 Inventory rolling features ────────────────────────────────────
# Inventory đã dùng snapshot tháng trước (forward-fill) → an toàn
df['inv_fill_rate_ma3'] = df['inv_avg_fill_rate'].rolling(3, min_periods=1).mean()
df['inv_stockout_trend'] = df['inv_products_stockout'].rolling(3, min_periods=1).mean()

# ─── 5.12 Category/Segment share features (đã có từ features file) ──────
# Các cột cat_share_*, seg_share_* đã được tính trong features_daily_train.csv
# Chúng dùng dữ liệu order_items JOIN orders → cần shift(1) để tránh leakage
cat_seg_cols = [c for c in df.columns if c.startswith('cat_share_') or c.startswith('seg_share_')]
for col in cat_seg_cols:
    df[col] = df[col].shift(1)  # Shift để chỉ dùng quá khứ
print(f"   Category/Segment share cols shifted: {len(cat_seg_cols)} features")

print(f"   ✅ Feature engineering complete.")

# ═══════════════════════════════════════════════════════════════════════════
# STEP 6: Drop LEAKY & REDUNDANT columns
# ═══════════════════════════════════════════════════════════════════════════
print("\n🗑️  [Step 6] Dropping leaky/redundant columns...")

# Danh sách cột cần loại bỏ
drop_cols = [
    # --- Leaky: tính trực tiếp từ targets ---
    'gross_profit',          # = revenue - cogs (leaky tuyệt đối)

    # --- Cột gốc cùng ngày (đã có version lagged thay thế) ---
    'total_orders',          # → dùng total_orders_lag1
    'unique_customers',      # → dùng unique_customers_lag1
    'total_items_sold',      # → dùng items_sold lag từ features file
    'total_item_revenue',    # Gần giống revenue → leaky
    'total_discount',        # → dùng total_discount_lag1
    'avg_discount_per_line', # → dùng avg_discount_lag1
    'unique_products_sold',  # Cùng ngày, phụ thuộc orders cùng ngày
    'promo_lines',           # Cùng ngày
    'total_lines',           # Cùng ngày
    'promo_pct',             # → dùng promo_pct_lag1

    # --- Web traffic cùng ngày ---
    'total_sessions',        # → dùng total_sessions_lag1
    'total_visitors',        # → dùng total_visitors_lag1
    'total_page_views',      # Cùng ngày
    'avg_bounce_rate',       # → dùng avg_bounce_rate_lag1
    'avg_session_duration',  # Cùng ngày

    # --- Returns/Shipments/Payments cùng ngày ---
    'daily_returns',         # → dùng return_rate_lag1
    'daily_return_qty',      # Cùng ngày
    'daily_refund_amount',   # → dùng daily_refund_lag1
    'daily_shipments',       # → dùng daily_shipments_lag1
    'avg_shipping_fee',      # → dùng avg_shipping_fee_lag1
    'total_shipping_fee',    # → dùng total_shipping_fee_lag1
    'avg_payment_value',     # → dùng avg_payment_value_lag1
    'avg_installments',      # → dùng avg_installments_lag1

    # --- Order status cùng ngày ---
    'delivered_orders',      # → dùng delivery_rate_lag1
    'cancelled_orders',      # → dùng cancel_rate_lag1
    'returned_orders',       # Cùng ngày
    'shipped_orders',        # Cùng ngày
    'pending_orders',        # Cùng ngày

    # --- Review cùng ngày ---
    'avg_rating',            # → dùng avg_rating_lag1
    'rating_std',            # Cùng ngày
    'low_ratings',           # Cùng ngày → dùng lag nếu cần
    'high_ratings',          # Cùng ngày → dùng lag nếu cần
    'daily_reviews',         # → dùng reviews_ma7

    # --- Redundant columns from features file ---
    'profit',                # = revenue - cogs, leaky
]

# Chỉ drop cột thực sự tồn tại
actual_drops = [c for c in drop_cols if c in df.columns]
df.drop(columns=actual_drops, inplace=True)
print(f"   Dropped {len(actual_drops)} leaky/redundant columns")

# Cũng loại bỏ các lag chồng chéo từ features file (quá nhiều lag)
# Giữ lại lag 3,7,15,30 theo yêu cầu; loại lag 1,2,14,21,28,60,90,365
excess_lags = []
for prefix in ['revenue_lag_', 'n_orders_lag_', 'items_sold_lag_', 'aov_lag_']:
    for lag_val in [1, 2, 14, 21, 28, 60, 90, 365]:
        col = f'{prefix}{lag_val}'
        if col in df.columns:
            excess_lags.append(col)
# Cũng loại các rolling quá lớn (60, 90)
for prefix in ['revenue_', 'n_orders_', 'items_sold_']:
    for w in [60, 90]:
        for suffix in [f'ma_{w}', f'std_{w}', f'min_{w}', f'max_{w}']:
            col = f'{prefix}{suffix}'
            if col in df.columns:
                excess_lags.append(col)

if excess_lags:
    df.drop(columns=excess_lags, inplace=True, errors='ignore')
    print(f"   Dropped {len(excess_lags)} excess lag/rolling cols (kept lag 3,7,15,30 only)")

# ═══════════════════════════════════════════════════════════════════════════
# STEP 7: Handle NaN from lag/rolling windows
# ═══════════════════════════════════════════════════════════════════════════
print("\n🔧 [Step 7] Handling NaN...")

# Drop đầu 60 ngày (max lag 30 + buffer) để tránh quá nhiều NaN
min_date = df['date'].min() + pd.Timedelta(days=60)
df_clean = df[df['date'] >= min_date].copy()
print(f"   Dropped first 60 days → {len(df) - len(df_clean)} rows removed")

# Forward-fill inventory cols (monthly data)
inv_cols = [c for c in df_clean.columns if c.startswith('inv_')]
df_clean[inv_cols] = df_clean[inv_cols].ffill()

# Fill remaining NaN
n_before = df_clean.isnull().sum().sum()
df_clean = df_clean.ffill().bfill()
n_after = df_clean.isnull().sum().sum()
print(f"   NaN filled: {n_before:,} → {n_after}")

# ═══════════════════════════════════════════════════════════════════════════
# STEP 8: Validate — Leakage Check
# ═══════════════════════════════════════════════════════════════════════════
print("\n🔍 [Step 8] Leakage validation...")

# Kiểm tra correlation giữa features và targets
feature_cols = [c for c in df_clean.columns if c not in ['date', 'revenue', 'cogs']]
high_corr_rev = []
high_corr_cogs = []
for col in feature_cols:
    try:
        corr_rev = df_clean[col].corr(df_clean['revenue'])
        corr_cogs = df_clean[col].corr(df_clean['cogs'])
        if abs(corr_rev) > 0.95:
            high_corr_rev.append((col, corr_rev))
        if abs(corr_cogs) > 0.95:
            high_corr_cogs.append((col, corr_cogs))
    except:
        pass

if high_corr_rev:
    print(f"   ⚠️  Features với |corr(revenue)| > 0.95:")
    for col, corr in sorted(high_corr_rev, key=lambda x: abs(x[1]), reverse=True)[:10]:
        print(f"       {col}: {corr:.4f}")
else:
    print(f"   ✅ Không có feature nào có |corr(revenue)| > 0.95")

if high_corr_cogs:
    print(f"   ⚠️  Features với |corr(cogs)| > 0.95:")
    for col, corr in sorted(high_corr_cogs, key=lambda x: abs(x[1]), reverse=True)[:10]:
        print(f"       {col}: {corr:.4f}")
else:
    print(f"   ✅ Không có feature nào có |corr(cogs)| > 0.95")

# ═══════════════════════════════════════════════════════════════════════════
# STEP 9: Save
# ═══════════════════════════════════════════════════════════════════════════
print(f"\n💾 [Step 9] Saving...")
df_clean.to_csv(OUTPUT, index=False)
print(f"   ✅ Saved: {OUTPUT}")
print(f"   Shape: {df_clean.shape}")
print(f"   Date range: {df_clean['date'].min().date()} → {df_clean['date'].max().date()}")
print(f"   Targets: revenue, cogs")
print(f"   Features: {df_clean.shape[1] - 3} (excl. date + 2 targets)")

# ═══════════════════════════════════════════════════════════════════════════
# STEP 10: Print Feature Summary
# ═══════════════════════════════════════════════════════════════════════════
print(f"\n📋 Feature Summary:")
print("-" * 50)

groups = {
    'Targets': ['revenue', 'cogs'],
    'Calendar/Temporal': [c for c in df_clean.columns if any(k in c for k in
        ['year', 'month', 'quarter', 'day_of', 'week_of', 'is_weekend',
         'is_month', 'is_quarter', 'season', 'is_tet', 'is_1111', 'is_1212'])],
    'Fourier/Cyclical': [c for c in df_clean.columns if any(k in c for k in
        ['sin_', 'cos_', 'yearly_sin', 'yearly_cos', 'weekly_sin', 'weekly_cos',
         'monthly_sin', 'monthly_cos'])],
    'Promotion (deterministic)': [c for c in df_clean.columns if c.startswith('promo_active')
        or c.startswith('promo_max') or c.startswith('promo_avg')
        or c.startswith('promo_has_')],
    'Revenue Lag/Rolling': [c for c in df_clean.columns if c.startswith('revenue_')],
    'COGS Lag/Rolling': [c for c in df_clean.columns if c.startswith('cogs_')],
    'Margin Features': [c for c in df_clean.columns if 'margin' in c or 'cogs_ratio' in c],
    'Order Features (lagged)': [c for c in df_clean.columns if any(k in c for k in
        ['orders_lag', 'customers_lag', 'aov_', 'items_per_order', 'cancel_rate',
         'delivery_rate', 'n_orders_lag', 'n_orders_ma'])],
    'Discount (lagged)': [c for c in df_clean.columns if any(k in c for k in
        ['discount_lag', 'promo_pct_lag', 'promo_pct_ma', 'promo_rate'])],
    'Web Traffic (lagged)': [c for c in df_clean.columns if any(k in c for k in
        ['sessions_', 'visitors_', 'bounce_rate_lag', 'conversion_rate'])],
    'Returns (lagged)': [c for c in df_clean.columns if any(k in c for k in
        ['return_rate', 'refund_lag'])],
    'Shipments (lagged)': [c for c in df_clean.columns if any(k in c for k in
        ['shipments_lag', 'shipping_fee_lag'])],
    'Payments (lagged)': [c for c in df_clean.columns if any(k in c for k in
        ['payment_value_lag', 'installments_lag'])],
    'Inventory': [c for c in df_clean.columns if c.startswith('inv_')],
    'Reviews (lagged)': [c for c in df_clean.columns if any(k in c for k in
        ['rating_', 'reviews_ma', 'avg_rating'])],
    'Category/Segment (lagged)': [c for c in df_clean.columns if
        c.startswith('cat_share_') or c.startswith('seg_share_')],
    'Other Features': [c for c in df_clean.columns if any(k in c for k in
        ['avg_price_sold', 'active_customers', 'new_signups', 'new_customer_ratio',
         'n_active_promos', 'revenue_same_', 'revenue_diff_', 'revenue_pct_change',
         'revenue_expanding', 'revenue_cv'])],
}

for name, cols in groups.items():
    if cols:
        print(f"   {name}: {len(cols)} cols")

print("\n" + "=" * 70)
print("🎉 Training dataset build complete!")
print("=" * 70)
