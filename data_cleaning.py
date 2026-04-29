"""
DATATHON 2026 — Data Cleaning Script
=====================================
Vai trò: Data Engineer
Mục đích: Xử lý tất cả lỗi dữ liệu được phát hiện trong Data Quality Audit Report.
         Lưu dữ liệu sạch vào thư mục dataset_cleaned/ — KHÔNG thay đổi dataset/ gốc.

Danh sách lỗi xử lý:
  I.  Financial & Legal Risks
      1. Refund Leakage        → is_unrefunded flag (orders)
      2. Ghost Returns         → missing_return_data flag (orders)
      3. Negative Profit       → is_loss_leader_day flag (sales)
  II. Operational Breakdowns
      1. Fake Deliveries       → ghost_shipment flag (orders)
      2. Supply Chain Failure  → inventory_health_index (inventory)
  III. System Pipeline Errors
      1. Time-Travel Anomaly   → Impute signup_date = MIN(order_date) (customers)
      2. Cart Duplicates       → Groupby aggregate (order_items)
      3. Null Categories       → fillna 'All Categories' (promotions)

Usage:
  cd DATATHON_2026_DATACONDA/
  source .venv/bin/activate
  python data_cleaning.py
"""

import pandas as pd
import numpy as np
import os
import shutil
import time

# ─── Paths ──────────────────────────────────────────────────────────────────
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(PROJECT_DIR, "dataset")
CLEAN_DIR = os.path.join(PROJECT_DIR, "dataset_cleaned")


def timer(label):
    """Context manager đo thời gian."""
    class T:
        def __enter__(self):
            self.t = time.time()
            print(f"\n{'='*60}")
            print(f"⏳ {label}")
            print(f"{'='*60}")
            return self
        def __exit__(self, *a):
            print(f"✅ Done in {time.time()-self.t:.1f}s")
    return T()


def load_csv(name):
    """Đọc file CSV từ thư mục dataset gốc."""
    path = os.path.join(RAW_DIR, name)
    df = pd.read_csv(path)
    print(f"   📂 Loaded {name}: {len(df):,} rows × {len(df.columns)} cols")
    return df


def save_csv(df, name):
    """Lưu DataFrame ra CSV trong thư mục dataset_cleaned."""
    path = os.path.join(CLEAN_DIR, name)
    df.to_csv(path, index=False)
    print(f"   💾 Saved {name}: {len(df):,} rows × {len(df.columns)} cols")


# ═══════════════════════════════════════════════════════════════════════════
# MAIN CLEANING PIPELINE
# ═══════════════════════════════════════════════════════════════════════════
def main():
    start_all = time.time()
    print("🚀 DATATHON 2026 — Data Cleaning Pipeline")
    print("=" * 60)
    print(f"   Input:  {RAW_DIR}")
    print(f"   Output: {CLEAN_DIR}")

    # ── Tạo thư mục output ──────────────────────────────────────────────
    os.makedirs(CLEAN_DIR, exist_ok=True)

    # ── Copy TẤT CẢ file gốc sang thư mục mới trước ────────────────────
    # (để dataset_cleaned tự đủ - self-contained)
    print(f"\n📋 Copying all raw files to {CLEAN_DIR}...")
    for f in os.listdir(RAW_DIR):
        if f.endswith(".csv"):
            src = os.path.join(RAW_DIR, f)
            dst = os.path.join(CLEAN_DIR, f)
            shutil.copy2(src, dst)
    print(f"   Copied {len([f for f in os.listdir(RAW_DIR) if f.endswith('.csv')])} files")

    # ── Load các bảng cần xử lý ─────────────────────────────────────────
    orders = load_csv("orders.csv")
    order_items = load_csv("order_items.csv")
    customers = load_csv("customers.csv")
    sales = load_csv("sales.csv")
    inventory = load_csv("inventory.csv")
    promotions = load_csv("promotions.csv")
    payments = load_csv("payments.csv")
    returns = load_csv("returns.csv")
    shipments = load_csv("shipments.csv")

    # ── Parse dates ──────────────────────────────────────────────────────
    orders["order_date"] = pd.to_datetime(orders["order_date"])
    customers["signup_date"] = pd.to_datetime(customers["signup_date"])
    sales["Date"] = pd.to_datetime(sales["Date"])
    inventory["snapshot_date"] = pd.to_datetime(inventory["snapshot_date"])
    promotions["start_date"] = pd.to_datetime(promotions["start_date"])
    promotions["end_date"] = pd.to_datetime(promotions["end_date"])

    # ═════════════════════════════════════════════════════════════════════
    # I.1  REFUND LEAKAGE — is_unrefunded flag
    # Cancelled orders WITH payments but WITHOUT returns
    # ═════════════════════════════════════════════════════════════════════
    with timer("I.1 Refund Leakage → is_unrefunded flag"):
        cancelled_ids = set(orders.loc[orders["order_status"] == "cancelled", "order_id"])
        paid_ids = set(payments["order_id"])
        returned_ids = set(returns["order_id"])

        # Đơn cancelled + có payment + KHÔNG có return
        unrefunded_ids = cancelled_ids & paid_ids - returned_ids

        orders["is_unrefunded"] = orders["order_id"].isin(unrefunded_ids).astype(int)
        count = orders["is_unrefunded"].sum()
        print(f"   🔴 Flagged {count:,} unrefunded cancelled orders")

    # ═════════════════════════════════════════════════════════════════════
    # I.2  GHOST RETURNS — missing_return_data flag
    # Status = returned but no record in returns table
    # ═════════════════════════════════════════════════════════════════════
    with timer("I.2 Ghost Returns → missing_return_data flag"):
        returned_status_ids = set(
            orders.loc[orders["order_status"] == "returned", "order_id"]
        )
        has_return_ids = set(returns["order_id"])

        ghost_return_ids = returned_status_ids - has_return_ids

        orders["missing_return_data"] = (
            orders["order_id"].isin(ghost_return_ids).astype(int)
        )
        count = orders["missing_return_data"].sum()
        print(f"   🔴 Flagged {count:,} orders with missing return data")

    # ═════════════════════════════════════════════════════════════════════
    # I.3  NEGATIVE PROFIT — is_loss_leader_day flag
    # Days where Revenue - COGS < 0
    # ═════════════════════════════════════════════════════════════════════
    with timer("I.3 Negative Profit → is_loss_leader_day flag"):
        sales["gross_profit"] = sales["Revenue"] - sales["COGS"]
        sales["is_loss_leader_day"] = (sales["gross_profit"] < 0).astype(int)
        count = sales["is_loss_leader_day"].sum()
        print(f"   🔴 Flagged {count:,} loss-leader days (negative profit)")

    # ═════════════════════════════════════════════════════════════════════
    # II.1 FAKE DELIVERIES — ghost_shipment flag
    # shipped/delivered but no shipment record
    # ═════════════════════════════════════════════════════════════════════
    with timer("II.1 Fake Deliveries → ghost_shipment flag"):
        should_have_shipment = set(
            orders.loc[
                orders["order_status"].isin(["shipped", "delivered", "returned"]),
                "order_id",
            ]
        )
        has_shipment_ids = set(shipments["order_id"])

        ghost_shipment_ids = should_have_shipment - has_shipment_ids

        orders["ghost_shipment"] = (
            orders["order_id"].isin(ghost_shipment_ids).astype(int)
        )
        count = orders["ghost_shipment"].sum()
        print(f"   🔴 Flagged {count:,} ghost shipments")

    # ═════════════════════════════════════════════════════════════════════
    # II.2 SUPPLY CHAIN FAILURE — inventory_health_index
    # Composite index from stockout, overstock, fill_rate, days_of_supply
    # Scale: 0 (worst) → 100 (best)
    # ═════════════════════════════════════════════════════════════════════
    with timer("II.2 Supply Chain Failure → inventory_health_index"):
        # Thành phần 1: Penalty cho stockout (-25 nếu stockout)
        score_stockout = (1 - inventory["stockout_flag"]) * 25

        # Thành phần 2: Penalty cho overstock (-25 nếu overstock)
        score_overstock = (1 - inventory["overstock_flag"]) * 25

        # Thành phần 3: fill_rate (0–1) → 0–25 điểm
        score_fill = inventory["fill_rate"].clip(0, 1) * 25

        # Thành phần 4: days_of_supply — lý tưởng 30–90 ngày
        # < 7 ngày = nguy hiểm (0đ), 30–90 = tối ưu (25đ), > 365 = đọng vốn (5đ)
        dos = inventory["days_of_supply"].clip(0, 500)
        score_dos = np.where(
            dos < 7, 0,
            np.where(dos < 30, (dos - 7) / 23 * 25,
            np.where(dos <= 90, 25,
            np.where(dos <= 365, 25 - (dos - 90) / 275 * 20, 5)))
        )

        inventory["inventory_health_index"] = (
            score_stockout + score_overstock + score_fill + score_dos
        ).round(1)

        # Cũng flag các tháng bị cả stockout LẪN overstock đồng thời
        inventory["dual_flag_anomaly"] = (
            (inventory["stockout_flag"] == 1) & (inventory["overstock_flag"] == 1)
        ).astype(int)

        avg_health = inventory["inventory_health_index"].mean()
        dual_count = inventory["dual_flag_anomaly"].sum()
        print(f"   📊 Avg health index: {avg_health:.1f}/100")
        print(f"   🔴 {dual_count:,} records with simultaneous stockout + overstock")

    # ═════════════════════════════════════════════════════════════════════
    # III.1 TIME-TRAVEL ANOMALY — Impute signup_date
    # order_date < signup_date → override signup_date = MIN(order_date)
    # ═════════════════════════════════════════════════════════════════════
    with timer("III.1 Time-Travel Anomaly → Impute signup_date"):
        # Tính ngày đặt hàng đầu tiên của mỗi khách
        first_order = (
            orders.groupby("customer_id")["order_date"]
            .min()
            .reset_index()
            .rename(columns={"order_date": "first_order_date"})
        )

        # Merge vào customers
        customers = customers.merge(first_order, on="customer_id", how="left")

        # Đếm trước khi sửa
        anomaly_mask = customers["first_order_date"] < customers["signup_date"]
        anomaly_count = anomaly_mask.sum()

        # Lưu giá trị gốc để audit trail
        customers["signup_date_original"] = customers["signup_date"]

        # Impute: nếu first_order_date < signup_date → dùng first_order_date
        customers.loc[anomaly_mask, "signup_date"] = customers.loc[
            anomaly_mask, "first_order_date"
        ]

        # Xóa cột tạm
        customers.drop(columns=["first_order_date"], inplace=True)

        print(f"   🔴 Fixed {anomaly_count:,} customers with time-travel signup_date")

    # ═════════════════════════════════════════════════════════════════════
    # III.2 CART DUPLICATES — Groupby aggregate order_items
    # Same (order_id, product_id) split into multiple rows → merge
    # ═════════════════════════════════════════════════════════════════════
    with timer("III.2 Cart Duplicates → Groupby aggregate"):
        rows_before = len(order_items)

        # Tìm các cặp trùng
        dup_mask = order_items.duplicated(
            subset=["order_id", "product_id"], keep=False
        )
        dup_count = dup_mask.sum()

        # Aggregate: sum quantity & discount_amount, giữ first cho các cột khác
        order_items = (
            order_items.groupby(["order_id", "product_id"], as_index=False)
            .agg({
                "quantity": "sum",
                "unit_price": "first",       # Giá đơn vị giống nhau cho cùng SP
                "discount_amount": "sum",     # Tổng giảm giá
                "promo_id": "first",          # Giữ KM chính
                "promo_id_2": "first",        # Giữ KM phụ
            })
        )

        rows_after = len(order_items)
        print(f"   🔴 Merged {dup_count} duplicate rows → {rows_before:,} → {rows_after:,} rows")

    # ═════════════════════════════════════════════════════════════════════
    # III.3 NULL CATEGORIES — fillna promotions.applicable_category
    # ═════════════════════════════════════════════════════════════════════
    with timer("III.3 Null Categories → fillna 'All Categories'"):
        null_count = promotions["applicable_category"].isna().sum()
        promotions["applicable_category"] = promotions["applicable_category"].fillna(
            "All Categories"
        )
        print(f"   🔴 Filled {null_count} null applicable_category → 'All Categories'")

    # ═════════════════════════════════════════════════════════════════════
    # SAVE ALL CLEANED FILES
    # ═════════════════════════════════════════════════════════════════════
    with timer("Saving cleaned datasets"):
        save_csv(orders, "orders.csv")
        save_csv(order_items, "order_items.csv")
        save_csv(customers, "customers.csv")
        save_csv(sales, "sales.csv")
        save_csv(inventory, "inventory.csv")
        save_csv(promotions, "promotions.csv")
        # payments, returns, shipments, reviews, products, geography,
        # web_traffic, sample_submission đã được copy nguyên bản ở bước đầu

    # ═════════════════════════════════════════════════════════════════════
    # SUMMARY
    # ═════════════════════════════════════════════════════════════════════
    elapsed = time.time() - start_all
    print(f"\n{'='*60}")
    print(f"🎉 Data Cleaning Pipeline Complete! ({elapsed:.1f}s)")
    print(f"{'='*60}")
    print(f"   📁 Cleaned data saved to: {CLEAN_DIR}")
    print(f"\n   Modified files:")
    print(f"   ├── orders.csv          (+is_unrefunded, +missing_return_data, +ghost_shipment)")
    print(f"   ├── customers.csv       (signup_date imputed, +signup_date_original)")
    print(f"   ├── order_items.csv     (cart duplicates merged)")
    print(f"   ├── sales.csv           (+gross_profit, +is_loss_leader_day)")
    print(f"   ├── inventory.csv       (+inventory_health_index, +dual_flag_anomaly)")
    print(f"   └── promotions.csv      (applicable_category filled)")
    print(f"\n   Unchanged files (copied as-is):")
    print(f"   ├── products.csv, geography.csv, payments.csv")
    print(f"   ├── shipments.csv, returns.csv, reviews.csv")
    print(f"   └── web_traffic.csv, sample_submission.csv, etc.")
    print(f"\n   ➡️  Next: Run python data_validation.py to verify fixes")


if __name__ == "__main__":
    main()
