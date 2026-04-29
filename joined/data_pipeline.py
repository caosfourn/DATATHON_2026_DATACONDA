"""
DATATHON 2026 — Data Pipeline
=============================
Vai trò: Data Engineer
Mục đích: Xây dựng 4 Data Marts từ 15 file CSV thô, xuất ra Parquet.

Data Marts:
  1. transaction_master  — Grain: order-item level (8 bảng JOIN)
  2. returns_enriched    — Grain: return level (5 bảng JOIN)
  3. reviews_enriched    — Grain: review level (4 bảng JOIN)
  4. daily_summary       — Grain: daily level (aggregate + JOIN)

Usage:
  cd joined/
  python data_pipeline.py                # Build từ dataset/ gốc
  python data_pipeline.py --cleaned      # Build từ dataset_cleaned/
  python data_pipeline.py --mart 1       # Build riêng Data Mart 1
"""

import duckdb
import os
import time
import argparse

# ─── Paths ──────────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(SCRIPT_DIR, "..", "dataset")
OUT_DIR = os.path.join(SCRIPT_DIR, "marts")

def _csv(name: str) -> str:
    """Trả về đường dẫn đầy đủ tới file CSV trong thư mục dataset."""
    return os.path.join(RAW_DIR, name).replace("\\", "/")

def _out(name: str) -> str:
    """Trả về đường dẫn đầy đủ tới file Parquet output trong thư mục marts."""
    return os.path.join(OUT_DIR, name).replace("\\", "/")

# ─── Helpers ────────────────────────────────────────────────────────────────
def _timer(label: str):
    """Context manager đo thời gian chạy."""
    class Timer:
        def __enter__(self):
            self.start = time.time()
            print(f"⏳ Building {label}...", flush=True)
            return self
        def __exit__(self, *args):
            elapsed = time.time() - self.start
            print(f"✅ {label} done in {elapsed:.1f}s", flush=True)
    return Timer()


# ═══════════════════════════════════════════════════════════════════════════
# DATA MART 1: transaction_master
# Grain: 1 row = 1 product in 1 order (order-item level)
# JOIN: order_items + orders + customers + geography + payments
#        + shipments + products + promotions (x2)
# ═══════════════════════════════════════════════════════════════════════════
def build_transaction_master(con: duckdb.DuckDBPyConnection) -> None:
    with _timer("transaction_master"):
        con.execute(f"""
            COPY (
                SELECT
                    -- ── Order Items (base) ──────────────────────────────
                    oi.order_id,
                    oi.product_id,
                    oi.quantity,
                    oi.unit_price,
                    oi.discount_amount,
                    oi.promo_id,
                    oi.promo_id_2,

                    -- ── Orders ───────────────────────────────────────────
                    o.order_date,
                    o.customer_id,
                    o.zip,
                    o.order_status,
                    o.payment_method   AS order_payment_method,
                    o.device_type,
                    o.order_source,

                    -- ── Customers ────────────────────────────────────────
                    c.signup_date      AS customer_signup_date,
                    c.gender,
                    c.age_group,
                    c.acquisition_channel,

                    -- ── Geography ────────────────────────────────────────
                    g.city,
                    g.region,
                    g.district,

                    -- ── Products ─────────────────────────────────────────
                    p.product_name,
                    p.category,
                    p.segment,
                    p.size,
                    p.color,
                    p.price            AS list_price,
                    p.cogs,

                    -- ── Payments ─────────────────────────────────────────
                    pay.payment_value,
                    pay.installments,

                    -- ── Shipments ────────────────────────────────────────
                    sh.ship_date,
                    sh.delivery_date,
                    sh.shipping_fee,

                    -- ── Promotion 1 ─────────────────────────────────────
                    pr1.promo_name     AS promo1_name,
                    pr1.promo_type     AS promo1_type,
                    pr1.discount_value AS promo1_discount_value,

                    -- ── Promotion 2 ─────────────────────────────────────
                    pr2.promo_name     AS promo2_name,
                    pr2.promo_type     AS promo2_type,
                    pr2.discount_value AS promo2_discount_value,

                    -- ── Derived Columns ─────────────────────────────────
                    (oi.quantity * oi.unit_price)                          AS line_revenue,
                    (oi.quantity * p.cogs)                                 AS line_cogs,
                    (oi.quantity * oi.unit_price) - (oi.quantity * p.cogs) AS gross_profit,
                    CASE
                        WHEN (oi.quantity * oi.unit_price) > 0
                        THEN ((oi.quantity * oi.unit_price) - (oi.quantity * p.cogs))
                             / (oi.quantity * oi.unit_price)
                        ELSE 0
                    END                                                    AS gross_margin,
                    date_diff('day', o.order_date, sh.ship_date)           AS processing_days,
                    date_diff('day', sh.ship_date,  sh.delivery_date)      AS delivery_days,
                    YEAR(o.order_date)                                      AS order_year,
                    MONTH(o.order_date)                                     AS order_month,
                    QUARTER(o.order_date)                                   AS order_quarter,
                    DAYOFWEEK(o.order_date)                                 AS order_dow

                FROM read_csv_auto('{_csv("order_items.csv")}')   AS oi

                LEFT JOIN read_csv_auto('{_csv("orders.csv")}')   AS o
                       ON oi.order_id   = o.order_id

                LEFT JOIN read_csv_auto('{_csv("customers.csv")}') AS c
                       ON o.customer_id = c.customer_id

                LEFT JOIN read_csv_auto('{_csv("geography.csv")}') AS g
                       ON o.zip         = g.zip

                LEFT JOIN read_csv_auto('{_csv("products.csv")}')  AS p
                       ON oi.product_id = p.product_id

                LEFT JOIN read_csv_auto('{_csv("payments.csv")}')  AS pay
                       ON o.order_id    = pay.order_id

                LEFT JOIN read_csv_auto('{_csv("shipments.csv")}') AS sh
                       ON o.order_id    = sh.order_id

                LEFT JOIN read_csv_auto('{_csv("promotions.csv")}') AS pr1
                       ON oi.promo_id   = pr1.promo_id

                LEFT JOIN read_csv_auto('{_csv("promotions.csv")}') AS pr2
                       ON oi.promo_id_2 = pr2.promo_id

            ) TO '{_out("transaction_master.parquet")}' (FORMAT PARQUET, COMPRESSION ZSTD);
        """)

        # Print summary
        info = con.execute(f"""
            SELECT
                COUNT(*)                     AS total_rows,
                COUNT(DISTINCT order_id)      AS unique_orders,
                COUNT(DISTINCT product_id)    AS unique_products,
                COUNT(DISTINCT customer_id)   AS unique_customers,
                MIN(order_date)               AS min_date,
                MAX(order_date)               AS max_date
            FROM read_parquet('{_out("transaction_master.parquet")}')
        """).fetchone()
        print(f"   📊 {info[0]:,} rows | {info[1]:,} orders | {info[2]:,} products | "
              f"{info[3]:,} customers | {info[4]} → {info[5]}")


# ═══════════════════════════════════════════════════════════════════════════
# DATA MART 2: returns_enriched
# Grain: 1 row = 1 return record
# ═══════════════════════════════════════════════════════════════════════════
def build_returns_enriched(con: duckdb.DuckDBPyConnection) -> None:
    with _timer("returns_enriched"):
        con.execute(f"""
            COPY (
                SELECT
                    r.return_id,
                    r.order_id,
                    r.product_id,
                    r.return_date,
                    r.return_reason,
                    r.return_quantity,
                    r.refund_amount,

                    -- ── Orders context ───────────────────────────────────
                    o.order_date,
                    o.customer_id,
                    o.order_status,
                    o.device_type,
                    o.order_source,

                    -- ── Customer context ─────────────────────────────────
                    c.gender,
                    c.age_group,

                    -- ── Geography ────────────────────────────────────────
                    g.region,
                    g.city,

                    -- ── Product context ──────────────────────────────────
                    p.product_name,
                    p.category,
                    p.segment,
                    p.size,
                    p.color,
                    p.price            AS list_price,
                    p.cogs,

                    -- ── Derived ──────────────────────────────────────────
                    date_diff('day', o.order_date, r.return_date) AS days_to_return

                FROM read_csv_auto('{_csv("returns.csv")}')     AS r

                LEFT JOIN read_csv_auto('{_csv("orders.csv")}')    AS o
                       ON r.order_id    = o.order_id

                LEFT JOIN read_csv_auto('{_csv("customers.csv")}') AS c
                       ON o.customer_id = c.customer_id

                LEFT JOIN read_csv_auto('{_csv("geography.csv")}') AS g
                       ON o.zip         = g.zip

                LEFT JOIN read_csv_auto('{_csv("products.csv")}')  AS p
                       ON r.product_id  = p.product_id

            ) TO '{_out("returns_enriched.parquet")}' (FORMAT PARQUET, COMPRESSION ZSTD);
        """)

        info = con.execute(f"""
            SELECT COUNT(*) AS total, COUNT(DISTINCT order_id) AS orders
            FROM read_parquet('{_out("returns_enriched.parquet")}')
        """).fetchone()
        print(f"   📊 {info[0]:,} return records | {info[1]:,} unique orders")


# ═══════════════════════════════════════════════════════════════════════════
# DATA MART 3: reviews_enriched
# Grain: 1 row = 1 review record
# ═══════════════════════════════════════════════════════════════════════════
def build_reviews_enriched(con: duckdb.DuckDBPyConnection) -> None:
    with _timer("reviews_enriched"):
        con.execute(f"""
            COPY (
                SELECT
                    rev.review_id,
                    rev.order_id,
                    rev.product_id,
                    rev.customer_id,
                    rev.review_date,
                    rev.rating,
                    rev.review_title,

                    -- ── Orders context ───────────────────────────────────
                    o.order_date,
                    o.device_type,
                    o.order_source,

                    -- ── Customer context ─────────────────────────────────
                    c.gender,
                    c.age_group,

                    -- ── Geography ────────────────────────────────────────
                    g.region,
                    g.city,

                    -- ── Product context ──────────────────────────────────
                    p.product_name,
                    p.category,
                    p.segment,
                    p.size,
                    p.color,

                    -- ── Derived ──────────────────────────────────────────
                    date_diff('day', o.order_date, rev.review_date) AS days_to_review

                FROM read_csv_auto('{_csv("reviews.csv")}')     AS rev

                LEFT JOIN read_csv_auto('{_csv("orders.csv")}')    AS o
                       ON rev.order_id    = o.order_id

                LEFT JOIN read_csv_auto('{_csv("customers.csv")}') AS c
                       ON rev.customer_id = c.customer_id

                LEFT JOIN read_csv_auto('{_csv("geography.csv")}') AS g
                       ON o.zip           = g.zip

                LEFT JOIN read_csv_auto('{_csv("products.csv")}')  AS p
                       ON rev.product_id  = p.product_id

            ) TO '{_out("reviews_enriched.parquet")}' (FORMAT PARQUET, COMPRESSION ZSTD);
        """)

        info = con.execute(f"""
            SELECT COUNT(*) AS total, ROUND(AVG(rating), 2) AS avg_rating
            FROM read_parquet('{_out("reviews_enriched.parquet")}')
        """).fetchone()
        print(f"   📊 {info[0]:,} reviews | avg rating: {info[1]}")


# ═══════════════════════════════════════════════════════════════════════════
# DATA MART 4: daily_summary
# Grain: 1 row = 1 day
# Aggregate từ: sales + orders + order_items + web_traffic + returns
# Thêm: calendar features, inventory (monthly → forward-fill)
# ═══════════════════════════════════════════════════════════════════════════
def build_daily_summary(con: duckdb.DuckDBPyConnection) -> None:
    with _timer("daily_summary"):
        con.execute(f"""
            COPY (
                WITH
                -- ── Base: sales (đã có sẵn daily Revenue, COGS) ────────
                sales AS (
                    SELECT
                        CAST("Date" AS DATE) AS date,
                        "Revenue"            AS revenue,
                        "COGS"               AS cogs,
                        "Revenue" - "COGS"   AS gross_profit
                    FROM read_csv_auto('{_csv("sales.csv")}')
                ),

                -- ── Aggregate orders theo ngày ─────────────────────────
                orders_agg AS (
                    SELECT
                        CAST(order_date AS DATE) AS date,
                        COUNT(*)                                                          AS total_orders,
                        COUNT(DISTINCT customer_id)                                       AS unique_customers,
                        SUM(CASE WHEN order_status = 'delivered'  THEN 1 ELSE 0 END)      AS delivered_orders,
                        SUM(CASE WHEN order_status = 'cancelled'  THEN 1 ELSE 0 END)      AS cancelled_orders,
                        SUM(CASE WHEN order_status = 'returned'   THEN 1 ELSE 0 END)      AS returned_orders,
                        SUM(CASE WHEN order_status = 'shipped'    THEN 1 ELSE 0 END)      AS shipped_orders,
                        SUM(CASE WHEN order_status = 'pending'    THEN 1 ELSE 0 END)      AS pending_orders
                    FROM read_csv_auto('{_csv("orders.csv")}')
                    GROUP BY CAST(order_date AS DATE)
                ),

                -- ── Aggregate order_items theo ngày ────────────────────
                items_agg AS (
                    SELECT
                        CAST(o.order_date AS DATE)                              AS date,
                        SUM(oi.quantity)                                         AS total_items_sold,
                        SUM(oi.quantity * oi.unit_price)                         AS total_item_revenue,
                        SUM(oi.discount_amount)                                  AS total_discount,
                        AVG(oi.discount_amount)                                  AS avg_discount_per_line,
                        COUNT(DISTINCT oi.product_id)                            AS unique_products_sold,
                        SUM(CASE WHEN oi.promo_id IS NOT NULL THEN 1 ELSE 0 END) AS promo_lines,
                        COUNT(*)                                                 AS total_lines,
                        SUM(CASE WHEN oi.promo_id IS NOT NULL THEN 1 ELSE 0 END) * 100.0
                            / COUNT(*)                                           AS promo_pct
                    FROM read_csv_auto('{_csv("order_items.csv")}') AS oi
                    JOIN read_csv_auto('{_csv("orders.csv")}')      AS o
                      ON oi.order_id = o.order_id
                    GROUP BY CAST(o.order_date AS DATE)
                ),

                -- ── Aggregate web_traffic theo ngày ────────────────────
                web_agg AS (
                    SELECT
                        CAST(date AS DATE)                AS date,
                        SUM(sessions)                     AS total_sessions,
                        SUM(unique_visitors)              AS total_visitors,
                        SUM(page_views)                   AS total_page_views,
                        AVG(bounce_rate)                  AS avg_bounce_rate,
                        AVG(avg_session_duration_sec)      AS avg_session_duration
                    FROM read_csv_auto('{_csv("web_traffic.csv")}')
                    GROUP BY CAST(date AS DATE)
                ),

                -- ── Aggregate returns theo ngày ────────────────────────
                returns_agg AS (
                    SELECT
                        CAST(return_date AS DATE)   AS date,
                        COUNT(*)                    AS daily_returns,
                        SUM(return_quantity)         AS daily_return_qty,
                        SUM(refund_amount)           AS daily_refund_amount
                    FROM read_csv_auto('{_csv("returns.csv")}')
                    GROUP BY CAST(return_date AS DATE)
                ),

                -- ── Aggregate shipments theo ngày ──────────────────────
                ship_agg AS (
                    SELECT
                        CAST(ship_date AS DATE)       AS date,
                        COUNT(*)                      AS daily_shipments,
                        AVG(shipping_fee)             AS avg_shipping_fee,
                        SUM(shipping_fee)             AS total_shipping_fee
                    FROM read_csv_auto('{_csv("shipments.csv")}')
                    GROUP BY CAST(ship_date AS DATE)
                ),

                -- ── Inventory monthly → map to last day of month ──────
                inv_agg AS (
                    SELECT
                        CAST(snapshot_date AS DATE)    AS snapshot_date,
                        SUM(stock_on_hand)             AS total_stock,
                        SUM(units_received)            AS total_received,
                        SUM(units_sold)                AS total_inv_sold,
                        AVG(fill_rate)                 AS avg_fill_rate,
                        AVG(stockout_days)             AS avg_stockout_days,
                        SUM(stockout_flag)             AS products_stockout,
                        SUM(overstock_flag)            AS products_overstock,
                        AVG(sell_through_rate)         AS avg_sell_through
                    FROM read_csv_auto('{_csv("inventory.csv")}')
                    GROUP BY CAST(snapshot_date AS DATE)
                ),

                -- ── Payments aggregate theo ngày ──────────────────────
                pay_agg AS (
                    SELECT
                        CAST(o.order_date AS DATE) AS date,
                        AVG(p.payment_value)       AS avg_payment_value,
                        AVG(p.installments)        AS avg_installments
                    FROM read_csv_auto('{_csv("payments.csv")}')  AS p
                    JOIN read_csv_auto('{_csv("orders.csv")}')    AS o
                      ON p.order_id = o.order_id
                    GROUP BY CAST(o.order_date AS DATE)
                )

                -- ════════════════════════════════════════════════════════
                -- FINAL JOIN: tất cả aggregate tables vào sales base
                -- ════════════════════════════════════════════════════════
                SELECT
                    s.date,
                    s.revenue,
                    s.cogs,
                    s.gross_profit,

                    -- ── Calendar features ───────────────────────────────
                    YEAR(s.date)                        AS year,
                    MONTH(s.date)                       AS month,
                    QUARTER(s.date)                     AS quarter,
                    DAYOFWEEK(s.date)                   AS day_of_week,
                    DAYOFYEAR(s.date)                   AS day_of_year,
                    WEEKOFYEAR(s.date)                  AS week_of_year,
                    CASE WHEN DAYOFWEEK(s.date) IN (0, 6) THEN 1 ELSE 0 END AS is_weekend,

                    -- ── Orders agg ──────────────────────────────────────
                    oa.total_orders,
                    oa.unique_customers,
                    oa.delivered_orders,
                    oa.cancelled_orders,
                    oa.returned_orders,
                    oa.shipped_orders,
                    oa.pending_orders,

                    -- ── Items agg ───────────────────────────────────────
                    ia.total_items_sold,
                    ia.total_item_revenue,
                    ia.total_discount,
                    ia.avg_discount_per_line,
                    ia.unique_products_sold,
                    ia.promo_lines,
                    ia.total_lines,
                    ia.promo_pct,

                    -- ── Web traffic agg ─────────────────────────────────
                    wa.total_sessions,
                    wa.total_visitors,
                    wa.total_page_views,
                    wa.avg_bounce_rate,
                    wa.avg_session_duration,

                    -- ── Returns agg ─────────────────────────────────────
                    COALESCE(ra.daily_returns, 0)        AS daily_returns,
                    COALESCE(ra.daily_return_qty, 0)     AS daily_return_qty,
                    COALESCE(ra.daily_refund_amount, 0)  AS daily_refund_amount,

                    -- ── Shipments agg ───────────────────────────────────
                    COALESCE(sha.daily_shipments, 0)     AS daily_shipments,
                    sha.avg_shipping_fee,
                    COALESCE(sha.total_shipping_fee, 0)  AS total_shipping_fee,

                    -- ── Payments agg ────────────────────────────────────
                    pa.avg_payment_value,
                    pa.avg_installments,

                    -- ── Inventory (monthly, forward-fill via month match)
                    inv.total_stock                       AS inv_total_stock,
                    inv.total_received                    AS inv_total_received,
                    inv.avg_fill_rate                     AS inv_avg_fill_rate,
                    inv.avg_stockout_days                 AS inv_avg_stockout_days,
                    inv.products_stockout                 AS inv_products_stockout,
                    inv.products_overstock                AS inv_products_overstock,
                    inv.avg_sell_through                  AS inv_avg_sell_through

                FROM sales AS s

                LEFT JOIN orders_agg   AS oa  ON s.date = oa.date
                LEFT JOIN items_agg    AS ia  ON s.date = ia.date
                LEFT JOIN web_agg      AS wa  ON s.date = wa.date
                LEFT JOIN returns_agg  AS ra  ON s.date = ra.date
                LEFT JOIN ship_agg     AS sha ON s.date = sha.date
                LEFT JOIN pay_agg      AS pa  ON s.date = pa.date

                -- Inventory: join on last day of the previous month
                -- (forward-fill: dùng snapshot tháng trước cho tháng hiện tại)
                LEFT JOIN inv_agg AS inv
                       ON inv.snapshot_date = LAST_DAY(s.date - INTERVAL 1 MONTH)

                ORDER BY s.date

            ) TO '{_out("daily_summary.parquet")}' (FORMAT PARQUET, COMPRESSION ZSTD);
        """)

        info = con.execute(f"""
            SELECT
                COUNT(*)    AS total_days,
                MIN(date)   AS min_date,
                MAX(date)   AS max_date,
                ROUND(SUM(revenue), 0) AS total_revenue
            FROM read_parquet('{_out("daily_summary.parquet")}')
        """).fetchone()
        print(f"   📊 {info[0]:,} days | {info[1]} → {info[2]} | "
              f"Total Revenue: {info[3]:,.0f}")


# ═══════════════════════════════════════════════════════════════════════════
# PUBLIC API — Hàm tiện ích cho team gọi từ notebook
# ═══════════════════════════════════════════════════════════════════════════
def load_transaction_master():
    """Load transaction_master.parquet → pandas DataFrame."""
    import pandas as pd
    return pd.read_parquet(_out("transaction_master.parquet"))

def load_returns_enriched():
    """Load returns_enriched.parquet → pandas DataFrame."""
    import pandas as pd
    return pd.read_parquet(_out("returns_enriched.parquet"))

def load_reviews_enriched():
    """Load reviews_enriched.parquet → pandas DataFrame."""
    import pandas as pd
    return pd.read_parquet(_out("reviews_enriched.parquet"))

def load_daily_summary():
    """Load daily_summary.parquet → pandas DataFrame."""
    import pandas as pd
    return pd.read_parquet(_out("daily_summary.parquet"))


# ═══════════════════════════════════════════════════════════════════════════
# CLI Entry Point
# ═══════════════════════════════════════════════════════════════════════════
def main():
    global RAW_DIR
    parser = argparse.ArgumentParser(description="DATATHON 2026 — Data Pipeline")
    parser.add_argument("--mart", type=int, default=0,
                        help="Build specific mart (1-4). 0 = build all.")
    parser.add_argument("--cleaned", action="store_true",
                        help="Read from dataset_cleaned/ instead of dataset/")
    args = parser.parse_args()

    if args.cleaned:
        RAW_DIR = os.path.join(SCRIPT_DIR, "..", "dataset_cleaned")
        print("📂 Source: dataset_cleaned/ (quality-fixed data)")

    # Create output directory
    os.makedirs(OUT_DIR, exist_ok=True)

    con = duckdb.connect(database=":memory:")
    print("=" * 60)
    print("🚀 DATATHON 2026 — Data Pipeline")
    print("=" * 60)

    builders = {
        1: ("Data Mart 1: transaction_master",  build_transaction_master),
        2: ("Data Mart 2: returns_enriched",    build_returns_enriched),
        3: ("Data Mart 3: reviews_enriched",    build_reviews_enriched),
        4: ("Data Mart 4: daily_summary",       build_daily_summary),
    }

    if args.mart == 0:
        for idx, (label, fn) in builders.items():
            fn(con)
            print()
    elif args.mart in builders:
        label, fn = builders[args.mart]
        fn(con)
    else:
        print(f"❌ Invalid mart number: {args.mart}. Use 1-4 or 0 for all.")
        return

    con.close()

    # Print file sizes
    print("=" * 60)
    print("📁 Output files in joined/marts/")
    print("-" * 60)
    for f in sorted(os.listdir(OUT_DIR)):
        if f.endswith(".parquet"):
            size_mb = os.path.getsize(os.path.join(OUT_DIR, f)) / (1024 * 1024)
            print(f"   {f:<35} {size_mb:>8.1f} MB")
    print("=" * 60)
    print("🎉 Pipeline complete! Team có thể load data bằng:")
    print("   from joined.data_pipeline import load_transaction_master")
    print("   df = load_transaction_master()")


if __name__ == "__main__":
    main()
