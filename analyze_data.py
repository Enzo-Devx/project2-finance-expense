# =============================================================================
# analyze_data.py
# Project 02 — Finance Expense Analysis
# Purpose: Answer Marcus's 4 business questions using DuckDB SQL.
#          JOIN transactions vs budget. Find overspenders, trends, anomalies.
# =============================================================================

import pandas as pd
import duckdb
import os
from datetime import datetime

# --- PATHS ---
TXN_PATH    = "outputs/project02_transactions_clean.csv"
BUDGET_PATH = "data/project02_budget_plan.csv"
REPORT_PATH = "outputs/analysis_report.txt"

os.makedirs("outputs", exist_ok=True)

print("=" * 60)
print("  ANALYZE_DATA.PY — Finance Expense Analysis")
print("=" * 60)
print("\n  Powered by DuckDB SQL.\n")

report = []
report.append("=" * 60)
report.append("  ANALYSIS REPORT — Finance Expense Analysis")
report.append(f"  Run at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
report.append("=" * 60)

# =============================================================================
# LOAD & PREP
# =============================================================================

txn = pd.read_csv(TXN_PATH)
bud = pd.read_csv(BUDGET_PATH)

txn["txn_date"]   = pd.to_datetime(txn["txn_date"], errors="coerce")
txn["txn_month"]  = txn["txn_date"].dt.month
txn["amount"]     = pd.to_numeric(txn["amount"], errors="coerce")
txn["is_refund"]  = txn["is_refund"].astype(str).str.strip().str.lower()  == "true"
txn["is_anomaly"] = txn["is_anomaly"].astype(str).str.strip().str.lower() == "true"

con = duckdb.connect()
con.register("transactions", txn)
con.register("budget", bud)

print(f"[LOAD] Transactions: {len(txn)} rows | Budget: {len(bud)} rows")
print("[DUCKDB] Tables registered.\n")


# =============================================================================
# QUESTION 1 — WHICH DEPARTMENTS ARE OVER BUDGET?
# ─────────────────────────────────────────────────────────────────────────────
# FIX: Pre-aggregate budget BEFORE joining.
# Why? If you join raw transactions to raw budget, each budget row gets
# repeated once per transaction → budget sum gets inflated → variance = ~0.
# Solution: SUM budget per dept first, THEN join to actual spend.
# This is called avoiding "JOIN fan-out" — a classic SQL gotcha.
# =============================================================================

print("[Q1] Which departments are over budget?")

q1 = con.execute("""
    WITH actual AS (
        SELECT
            department,
            ROUND(SUM(amount), 2) AS actual_spend
        FROM transactions
        WHERE is_refund  = false
          AND is_anomaly = false
        GROUP BY department
    ),
    planned AS (
        SELECT
            department,
            ROUND(SUM(budget_amount), 2) AS total_budget
        FROM budget
        GROUP BY department
    )
    SELECT
        a.department,
        a.actual_spend,
        p.total_budget,
        ROUND(a.actual_spend - p.total_budget, 2)              AS variance,
        ROUND(
            (a.actual_spend - p.total_budget)
            / p.total_budget * 100, 1
        )                                                        AS variance_pct,
        CASE
            WHEN a.actual_spend > p.total_budget THEN 'OVER BUDGET'
            ELSE 'Under Budget'
        END                                                      AS budget_status
    FROM actual a
    LEFT JOIN planned p ON a.department = p.department
    ORDER BY variance DESC
""").df()

report.append("\n" + "=" * 60)
report.append("QUESTION 1 — Department Budget vs Actual Spend")
report.append("=" * 60 + "\n")
for _, row in q1.iterrows():
    flag = "⚠ OVER BUDGET" if row["budget_status"] == "OVER BUDGET" else "✓ Under Budget"
    report.append(
        f"  {row['department']:<15} "
        f"Actual: ₱{row['actual_spend']:>12,.0f}  "
        f"Budget: ₱{row['total_budget']:>12,.0f}  "
        f"Variance: {row['variance_pct']:>+.1f}%  {flag}"
    )

over_budget = q1[q1["budget_status"] == "OVER BUDGET"]
report.append(f"\n  Departments over budget: {len(over_budget)} of {len(q1)}")
q1.to_csv("outputs/q1_budget_vs_actual.csv", index=False)
print(f"  → {len(over_budget)} of {len(q1)} departments over budget")


# =============================================================================
# QUESTION 2 — WHERE IS THE MONEY GOING?
# =============================================================================

print("\n[Q2] Where is the money actually going?")

q2_category = con.execute("""
    SELECT
        department,
        category,
        COUNT(*)               AS txn_count,
        ROUND(SUM(amount), 2)  AS total_spend,
        ROUND(AVG(amount), 2)  AS avg_per_txn
    FROM transactions
    WHERE is_refund  = false
      AND is_anomaly = false
    GROUP BY department, category
    ORDER BY total_spend DESC
    LIMIT 15
""").df()

q2_vendors = con.execute("""
    SELECT
        vendor,
        department,
        COUNT(*)               AS txn_count,
        ROUND(SUM(amount), 2)  AS total_spend
    FROM transactions
    WHERE is_refund  = false
      AND is_anomaly = false
      AND vendor    != 'Unknown Vendor'
    GROUP BY vendor, department
    ORDER BY total_spend DESC
    LIMIT 10
""").df()

report.append("\n" + "=" * 60)
report.append("QUESTION 2 — Top Spending Categories")
report.append("=" * 60 + "\n")
for _, row in q2_category.iterrows():
    report.append(
        f"  {row['department']:<15} | {row['category']:<25} "
        f"₱{row['total_spend']:>12,.0f}  ({row['txn_count']} txns)"
    )

report.append("\n  Top 10 Vendors by Spend:\n")
for _, row in q2_vendors.iterrows():
    report.append(
        f"  {row['vendor']:<25} [{row['department']:<12}] "
        f"₱{row['total_spend']:>12,.0f}"
    )

q2_category.to_csv("outputs/q2_spend_by_category.csv", index=False)
q2_vendors.to_csv("outputs/q2_top_vendors.csv",        index=False)
print(f"  → Category and vendor breakdowns saved")


# =============================================================================
# QUESTION 3 — SUSPICIOUS TRANSACTIONS?
# =============================================================================

print("\n[Q3] Pulling anomalous transactions...")

q3 = con.execute("""
    SELECT
        txn_id,
        txn_date,
        department,
        category,
        vendor,
        ROUND(amount, 2) AS amount,
        status
    FROM transactions
    WHERE is_anomaly = true
    ORDER BY amount DESC
""").df()

q3_refunds = con.execute("""
    SELECT
        department,
        COUNT(*)               AS refund_count,
        ROUND(SUM(amount), 2)  AS total_refunded
    FROM transactions
    WHERE is_refund = true
    GROUP BY department
    ORDER BY total_refunded ASC
""").df()

report.append("\n" + "=" * 60)
report.append("QUESTION 3 — Suspicious / Anomalous Transactions")
report.append("=" * 60)
report.append(f"\n  Total flagged: {len(q3)} transactions\n")
for _, row in q3.iterrows():
    report.append(
        f"  {row['txn_id']}  |  {str(row['txn_date'])[:10]}  |  "
        f"{row['department']:<12}  |  {row['category']:<20}  |  "
        f"₱{row['amount']:>12,.0f}  |  {row['vendor']}"
    )

report.append("\n  Refunds by Department:\n")
for _, row in q3_refunds.iterrows():
    report.append(
        f"    {row['department']:<15} "
        f"{row['refund_count']} refunds  "
        f"₱{abs(row['total_refunded']):,.0f}"
    )

q3.to_csv("outputs/q3_anomalies.csv",   index=False)
q3_refunds.to_csv("outputs/q3_refunds.csv", index=False)
print(f"  → {len(q3)} anomalies flagged")


# =============================================================================
# QUESTION 4 — MONTHLY SPENDING TREND
# Same fix applied: pre-aggregate both sides before joining.
# =============================================================================

print("\n[Q4] Building monthly spend trends...")

q4 = con.execute("""
    WITH monthly_actual AS (
        SELECT
            txn_month       AS month,
            department,
            ROUND(SUM(amount), 2) AS actual_spend
        FROM transactions
        WHERE is_refund  = false
          AND is_anomaly = false
        GROUP BY txn_month, department
    ),
    monthly_budget AS (
        SELECT
            month,
            department,
            ROUND(SUM(budget_amount), 2) AS budget_amount
        FROM budget
        GROUP BY month, department
    )
    SELECT
        a.month,
        a.department,
        a.actual_spend,
        b.budget_amount,
        ROUND(a.actual_spend - b.budget_amount, 2) AS variance
    FROM monthly_actual a
    LEFT JOIN monthly_budget b
        ON  a.department = b.department
        AND a.month      = b.month
    ORDER BY a.month, a.department
""").df()

q4_totals = con.execute("""
    SELECT
        txn_month              AS month,
        COUNT(*)               AS txn_count,
        ROUND(SUM(amount), 2)  AS total_spend
    FROM transactions
    WHERE is_refund  = false
      AND is_anomaly = false
    GROUP BY txn_month
    ORDER BY txn_month
""").df()

month_names = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",
               6:"Jun",7:"Jul",8:"Aug",9:"Sep"}

report.append("\n" + "=" * 60)
report.append("QUESTION 4 — Monthly Spending Trend")
report.append("=" * 60 + "\n")
for _, row in q4_totals.iterrows():
    m = month_names.get(int(row["month"]), str(int(row["month"])))
    report.append(
        f"    {m}:  ₱{row['total_spend']:>12,.0f}  "
        f"({int(row['txn_count'])} transactions)"
    )

q4.to_csv("outputs/q4_monthly_trends.csv",       index=False)
q4_totals.to_csv("outputs/q4_monthly_totals.csv", index=False)
print(f"  → Monthly trends saved")


# =============================================================================
# OVERALL SUMMARY
# =============================================================================

total_actual = txn[~txn["is_refund"] & ~txn["is_anomaly"]]["amount"].sum()
total_budget = bud["budget_amount"].sum()
variance     = total_actual - total_budget
variance_pct = (variance / total_budget) * 100

summary = (
    f"\nOVERALL SUMMARY"
    f"\n  Total Actual Spend : ₱{total_actual:>12,.0f}"
    f"\n  Total Budget       : ₱{total_budget:>12,.0f}"
    f"\n  Overall Variance   : ₱{variance:>+12,.0f}  ({variance_pct:+.1f}%)"
    f"\n  Anomalous Txns     : {len(q3)} flagged for investigation"
    f"\n  Departments Over   : {len(over_budget)} of {len(q1)}"
)

report.append("\n" + "=" * 60)
report.append(summary)

with open(REPORT_PATH, "w", encoding="utf-8") as f:
    f.write("\n".join(report))

print("\n" + "=" * 60)
print(summary)
print(f"\n  Report → {REPORT_PATH}")
print("=" * 60)

con.close()