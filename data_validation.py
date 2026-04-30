"""
DATATHON 2026 — Data Validation Script
========================================
Vai trò: Data Engineer
Mục đích: Kiểm tra toàn bộ các lỗi dữ liệu sau khi chạy data_cleaning.py.
         Dùng DuckDB để truy vấn trực tiếp trên dataset_cleaned/.

Kỳ vọng: TẤT CẢ checks đều PASS (0 lỗi còn sót lại).

Usage:
  cd DATATHON_2026_DATACONDA/
  source .venv/bin/activate
  python data_validation.py
"""

import duckdb
import os
import sys

# ─── Paths ──────────────────────────────────────────────────────────────────
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
CLEAN_DIR = os.path.join(PROJECT_DIR, "dataset_cleaned")


def csv(name: str) -> str:
    """Trả về đường dẫn file CSV trong dataset_cleaned/."""
    return os.path.join(CLEAN_DIR, name).replace("\\", "/")


def run_check(con, check_id: str, description: str, query: str, expect_zero: bool = True):
    """
    Chạy một validation check.
    - expect_zero=True: kỳ vọng query trả về 0 (= không còn lỗi)
    - expect_zero=False: kỳ vọng query trả về > 0 (= flag đã được tạo)
    """
    try:
        result = con.execute(query).fetchone()
        value = result[0] if result else None

        if expect_zero:
            status = "✅ PASS" if value == 0 else f"❌ FAIL ({value:,} issues remaining)"
        else:
            status = f"✅ PASS ({value:,} flagged)" if value and value > 0 else "❌ FAIL (no flags found)"

        print(f"   {check_id} | {status} | {description}")
        return value == 0 if expect_zero else (value is not None and value > 0)
    except Exception as e:
        print(f"   {check_id} | ⚠️  ERROR | {description}")
        print(f"         → {e}")
        return False


def main():
    if not os.path.exists(CLEAN_DIR):
        print(f"❌ Thư mục {CLEAN_DIR} không tồn tại. Hãy chạy data_cleaning.py trước!")
        sys.exit(1)

    con = duckdb.connect(database=":memory:")
    results = []

    print("=" * 80)
    print("🔍 DATATHON 2026 — Data Validation Report")
    print(f"   Dataset: {CLEAN_DIR}")
    print("=" * 80)

    # ═════════════════════════════════════════════════════════════════════
    # I. FINANCIAL & LEGAL RISKS
    # ═════════════════════════════════════════════════════════════════════
    print(f"\n{'─'*80}")
    print("I. FINANCIAL & LEGAL RISKS")
    print(f"{'─'*80}")

    # I.1 Refund Leakage — Check flag exists
    results.append(run_check(
        con, "I.1a",
        "is_unrefunded column exists in orders",
        f"""
        SELECT COUNT(*)
        FROM read_csv_auto('{csv("orders.csv")}')
        WHERE is_unrefunded = 1
        """,
        expect_zero=False
    ))

    # I.1 Refund Leakage — Verify logic: all cancelled+paid+no-return are flagged
    results.append(run_check(
        con, "I.1b",
        "No unflagged cancelled orders with payments but without returns",
        f"""
        SELECT COUNT(*)
        FROM read_csv_auto('{csv("orders.csv")}') o
        WHERE o.order_status = 'cancelled'
          AND o.order_id IN (SELECT order_id FROM read_csv_auto('{csv("payments.csv")}'))
          AND o.order_id NOT IN (SELECT order_id FROM read_csv_auto('{csv("returns.csv")}'))
          AND o.is_unrefunded = 0
        """
    ))

    # I.2 Ghost Returns — Check flag exists
    results.append(run_check(
        con, "I.2a",
        "missing_return_data column exists in orders",
        f"""
        SELECT COUNT(*)
        FROM read_csv_auto('{csv("orders.csv")}')
        WHERE missing_return_data = 1
        """,
        expect_zero=False
    ))

    # I.2 Ghost Returns — Verify: all returned-status orders without return records are flagged
    results.append(run_check(
        con, "I.2b",
        "No unflagged returned-status orders missing from returns table",
        f"""
        SELECT COUNT(*)
        FROM read_csv_auto('{csv("orders.csv")}') o
        WHERE o.order_status = 'returned'
          AND o.order_id NOT IN (SELECT order_id FROM read_csv_auto('{csv("returns.csv")}'))
          AND o.missing_return_data = 0
        """
    ))

    # I.3 Negative Profit — Check flag exists
    results.append(run_check(
        con, "I.3a",
        "is_loss_leader_day column exists in sales",
        f"""
        SELECT COUNT(*)
        FROM read_csv_auto('{csv("sales.csv")}')
        WHERE is_loss_leader_day = 1
        """,
        expect_zero=False
    ))

    # I.3 Negative Profit — Verify: all negative-profit days are flagged
    results.append(run_check(
        con, "I.3b",
        "No unflagged negative-profit days",
        f"""
        SELECT COUNT(*)
        FROM read_csv_auto('{csv("sales.csv")}')
        WHERE (Revenue - COGS) < 0
          AND is_loss_leader_day = 0
        """
    ))

    # ═════════════════════════════════════════════════════════════════════
    # II. OPERATIONAL BREAKDOWNS
    # ═════════════════════════════════════════════════════════════════════
    print(f"\n{'─'*80}")
    print("II. OPERATIONAL BREAKDOWNS")
    print(f"{'─'*80}")

    # II.1 Ghost Shipments — Check flag exists
    results.append(run_check(
        con, "II.1a",
        "ghost_shipment column exists in orders",
        f"""
        SELECT COUNT(*)
        FROM read_csv_auto('{csv("orders.csv")}')
        WHERE ghost_shipment = 1
        """,
        expect_zero=False
    ))

    # II.1 Ghost Shipments — Verify logic
    results.append(run_check(
        con, "II.1b",
        "No unflagged shipped/delivered orders missing from shipments",
        f"""
        SELECT COUNT(*)
        FROM read_csv_auto('{csv("orders.csv")}') o
        WHERE o.order_status IN ('shipped', 'delivered', 'returned')
          AND o.order_id NOT IN (SELECT order_id FROM read_csv_auto('{csv("shipments.csv")}'))
          AND o.ghost_shipment = 0
        """
    ))

    # II.2 Inventory Health Index — Check column exists
    results.append(run_check(
        con, "II.2a",
        "inventory_health_index column exists in inventory",
        f"""
        SELECT COUNT(*)
        FROM read_csv_auto('{csv("inventory.csv")}')
        WHERE inventory_health_index IS NOT NULL
        """,
        expect_zero=False
    ))

    # II.2 Inventory Health Index — Check range 0–100
    results.append(run_check(
        con, "II.2b",
        "inventory_health_index is within [0, 100]",
        f"""
        SELECT COUNT(*)
        FROM read_csv_auto('{csv("inventory.csv")}')
        WHERE inventory_health_index < 0 OR inventory_health_index > 100
        """
    ))

    # II.2 dual_flag_anomaly — Check exists
    results.append(run_check(
        con, "II.2c",
        "dual_flag_anomaly column exists (stockout + overstock simultaneously)",
        f"""
        SELECT COUNT(*)
        FROM read_csv_auto('{csv("inventory.csv")}')
        WHERE dual_flag_anomaly = 1
        """,
        expect_zero=False
    ))

    # ═════════════════════════════════════════════════════════════════════
    # III. SYSTEM PIPELINE ERRORS
    # ═════════════════════════════════════════════════════════════════════
    print(f"\n{'─'*80}")
    print("III. SYSTEM PIPELINE ERRORS")
    print(f"{'─'*80}")

    # III.1 Time-Travel — No more order_date < signup_date
    results.append(run_check(
        con, "III.1a",
        "No orders placed before customer signup_date",
        f"""
        SELECT COUNT(*)
        FROM read_csv_auto('{csv("orders.csv")}') o
        JOIN read_csv_auto('{csv("customers.csv")}') c
          ON o.customer_id = c.customer_id
        WHERE CAST(o.order_date AS DATE) < CAST(c.signup_date AS DATE)
        """
    ))

    # III.1 Time-Travel — Original signup_date preserved
    results.append(run_check(
        con, "III.1b",
        "signup_date_original column preserved for audit trail",
        f"""
        SELECT COUNT(*)
        FROM read_csv_auto('{csv("customers.csv")}')
        WHERE signup_date_original IS NOT NULL
        """,
        expect_zero=False
    ))

    # III.2 Cart Duplicates — No duplicate (order_id, product_id) pairs
    results.append(run_check(
        con, "III.2",
        "No duplicate (order_id, product_id) pairs in order_items",
        f"""
        SELECT COUNT(*) FROM (
            SELECT order_id, product_id, COUNT(*) as cnt
            FROM read_csv_auto('{csv("order_items.csv")}')
            GROUP BY order_id, product_id
            HAVING cnt > 1
        )
        """
    ))

    # III.3 Null Categories — No nulls in applicable_category
    results.append(run_check(
        con, "III.3",
        "No NULL applicable_category in promotions",
        f"""
        SELECT COUNT(*)
        FROM read_csv_auto('{csv("promotions.csv")}')
        WHERE applicable_category IS NULL
        """
    ))

    # ═════════════════════════════════════════════════════════════════════
    # BONUS: DATA INTEGRITY CROSS-CHECKS
    # ═════════════════════════════════════════════════════════════════════
    print(f"\n{'─'*80}")
    print("IV. BONUS — DATA INTEGRITY CROSS-CHECKS")
    print(f"{'─'*80}")

    # Row count check — order_items should have fewer rows after dedup
    results.append(run_check(
        con, "IV.1",
        "order_items cleaned has fewer rows than raw (dedup applied)",
        f"""
        SELECT CASE
            WHEN (SELECT COUNT(*) FROM read_csv_auto('{csv("order_items.csv")}'))
               < (SELECT COUNT(*) FROM read_csv_auto('{os.path.join(RAW_DIR, "order_items.csv").replace(chr(92), "/")}'))
            THEN 0 ELSE 1
        END
        """
    ))

    # Verify gross_profit column in sales
    results.append(run_check(
        con, "IV.2",
        "gross_profit = Revenue - COGS (consistency check)",
        f"""
        SELECT COUNT(*)
        FROM read_csv_auto('{csv("sales.csv")}')
        WHERE ABS(gross_profit - (Revenue - COGS)) > 0.01
        """
    ))

    # FK integrity: all order_ids in order_items exist in orders
    results.append(run_check(
        con, "IV.3",
        "All order_ids in order_items exist in orders (FK integrity)",
        f"""
        SELECT COUNT(*)
        FROM read_csv_auto('{csv("order_items.csv")}') oi
        WHERE oi.order_id NOT IN (
            SELECT order_id FROM read_csv_auto('{csv("orders.csv")}')
        )
        """
    ))

    # ═════════════════════════════════════════════════════════════════════
    # SUMMARY
    # ═════════════════════════════════════════════════════════════════════
    con.close()

    passed = sum(results)
    total = len(results)
    print(f"\n{'='*80}")
    print(f"📊 VALIDATION SUMMARY: {passed}/{total} checks passed")
    if passed == total:
        print("🎉 ALL CHECKS PASSED — Dataset is clean and ready!")
    else:
        print(f"⚠️  {total - passed} check(s) failed — review issues above")
    print(f"{'='*80}")

    sys.exit(0 if passed == total else 1)


RAW_DIR = os.path.join(PROJECT_DIR, "dataset")

if __name__ == "__main__":
    main()
