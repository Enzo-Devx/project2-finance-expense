# =============================================================================
# clean_data.py
# Project 02 — Finance Expense Analysis
# Purpose: Clean transactions + budget tables using DuckDB SQL.
#          Output two clean CSVs ready for analysis.
#
# WHY DUCKDB HERE?
# DuckDB lets us write real SQL directly on CSV files —
# no PostgreSQL server needed, no pandas gymnastics.
# It's fast, memory-efficient, and the SQL is identical
# to what you'd write in a real database. Perfect for laptops.
# =============================================================================

import duckdb
import pandas as pd
import numpy as np
import os
from datetime import datetime

# --- PATHS ---
TXN_RAW     = "data/project02_transactions_raw.csv"
BUDGET_RAW  = "data/project02_budget_plan.csv"
TXN_CLEAN   = "outputs/project02_transactions_clean.csv"
BUDGET_CLEAN= "outputs/project02_budget_clean.csv"
REPORT_PATH = "outputs/cleaning_report.txt"

os.makedirs("outputs", exist_ok=True)

print("=" * 60)
print("  CLEAN_DATA.PY — Finance Expense Cleaning Pipeline")
print("=" * 60)

report = []
report.append("=" * 60)
report.append("  CLEANING REPORT — Finance Project 02")
report.append(f"  Run at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
report.append("=" * 60)

# =============================================================================
# CONNECT DUCKDB
# In-memory database — no files, no server, no setup.
# DuckDB reads CSVs directly like they're database tables.
# =============================================================================

con = duckdb.connect()  # in-memory, lightweight
print("\n[DUCKDB] Connected. In-memory database ready.")

# =============================================================================
# STEP 1 — LOAD RAW FILES INTO DUCKDB
# We register the CSVs as virtual tables.
# From this point on we talk to them in pure SQL.
# =============================================================================

con.execute(f"""
    CREATE OR REPLACE VIEW raw_transactions AS
    SELECT * FROM read_csv_auto('{TXN_RAW}', ALL_VARCHAR=TRUE)
""")

con.execute(f"""
    CREATE OR REPLACE VIEW raw_budget AS
    SELECT * FROM read_csv_auto('{BUDGET_RAW}', ALL_VARCHAR=TRUE)
""")

raw_txn_count    = con.execute("SELECT COUNT(*) FROM raw_transactions").fetchone()[0]
raw_budget_count = con.execute("SELECT COUNT(*) FROM raw_budget").fetchone()[0]

print(f"[LOAD]  Transactions raw rows : {raw_txn_count}")
print(f"[LOAD]  Budget raw rows       : {raw_budget_count}")
report.append(f"\nRaw transactions loaded : {raw_txn_count}")
report.append(f"Raw budget loaded       : {raw_budget_count}")


# =============================================================================
# STEP 2 — DROP BLANK ROWS (SQL WAY)
# A blank row has no txn_id and no department.
# In SQL: WHERE txn_id IS NOT NULL AND txn_id != ''
# =============================================================================

blank_count = con.execute("""
    SELECT COUNT(*) FROM raw_transactions
    WHERE TRIM(COALESCE(txn_id, '')) = ''
""").fetchone()[0]

print(f"\n[CLEAN] Blank rows found: {blank_count}")
report.append(f"\n[Step 2] Blank rows dropped: {blank_count}")


# =============================================================================
# STEP 3 — STANDARDIZE DATES (Python — mixed formats need regex logic)
# DuckDB handles this partially but mixed formats need pandas assist.
# We pull the non-blank rows, fix dates in pandas, push back to DuckDB.
# This is a real-world pattern: SQL for structure, Python for messy parsing.
# =============================================================================

# Pull non-blank rows into pandas for date parsing
df_txn = con.execute("""
    SELECT * FROM raw_transactions
    WHERE TRIM(COALESCE(txn_id, '')) != ''
""").df()

def parse_mixed_dates(series):
    formats = ["%Y-%m-%d", "%m/%d/%Y", "%d-%m-%Y", "%Y/%m/%d"]
    parsed = pd.Series([pd.NaT] * len(series), dtype="datetime64[ns]")
    for fmt in formats:
        mask = parsed.isnull() & series.notnull()
        if mask.sum() == 0:
            break
        attempt = pd.to_datetime(series[mask], format=fmt, errors="coerce")
        parsed[mask] = attempt
    return parsed

df_txn["txn_date"] = parse_mixed_dates(df_txn["txn_date"])
df_txn["month"]    = df_txn["txn_date"].dt.month
df_txn["quarter"]  = df_txn["txn_date"].dt.quarter
df_txn["year"]     = df_txn["txn_date"].dt.year

unparseable = df_txn["txn_date"].isnull().sum()
print(f"[CLEAN] Dates standardized. Unparseable: {unparseable}")
report.append(f"[Step 3] Dates standardized. Unparseable: {unparseable}")

# Re-register cleaned df back into DuckDB for SQL use
con.register("txn_dated", df_txn)


# =============================================================================
# STEP 4 — DROP DUPLICATES (SQL WAY)
# Use ROW_NUMBER() window function — classic SQL dedup pattern.
# Keep only the first occurrence of each txn_id.
# This is how you'd do it in PostgreSQL too — same syntax.
# =============================================================================

before_dedup = len(df_txn)

df_txn = con.execute("""
    SELECT * FROM (
        SELECT *,
               ROW_NUMBER() OVER (PARTITION BY txn_id ORDER BY txn_date) AS rn
        FROM txn_dated
        WHERE TRIM(COALESCE(txn_id, '')) != ''
    ) ranked
    WHERE rn = 1
""").df().drop(columns=["rn"])

dup_count = before_dedup - len(df_txn)
print(f"[CLEAN] Duplicates dropped: {dup_count}")
report.append(f"[Step 4] Duplicate rows dropped: {dup_count}")

con.register("txn_deduped", df_txn)


# =============================================================================
# STEP 5 — CLEAN AMOUNT COLUMN
# Cast to float. Flag anomalies (> 400,000) as suspicious.
# Separate refunds (negative amounts) — they're legit but need a flag.
# =============================================================================

df_txn["amount"] = pd.to_numeric(df_txn["amount"], errors="coerce")

# Flag anomalies
ANOMALY_THRESHOLD = 400000
df_txn["is_anomaly"] = df_txn["amount"].abs() > ANOMALY_THRESHOLD
df_txn["is_refund"]  = df_txn["amount"] < 0

anomaly_count = df_txn["is_anomaly"].sum()
refund_count  = df_txn["is_refund"].sum()
null_amounts  = df_txn["amount"].isnull().sum()

# Impute null amounts with median per department
dept_median = df_txn.groupby("department")["amount"].transform("median")
df_txn["amount"] = df_txn["amount"].fillna(dept_median).round(2)

print(f"[CLEAN] Anomalous transactions flagged (>₱400K): {anomaly_count}")
print(f"[CLEAN] Refund transactions flagged: {refund_count}")
print(f"[CLEAN] Null amounts imputed: {null_amounts}")
report.append(f"[Step 5] Anomalies flagged (>₱400K): {anomaly_count}")
report.append(f"         Refunds flagged: {refund_count}")
report.append(f"         Null amounts imputed: {null_amounts}")


# =============================================================================
# STEP 6 — FILL MISSING VENDORS
# Replace empty vendor with 'Unknown Vendor' — don't drop, just flag.
# =============================================================================

df_txn["vendor"] = df_txn["vendor"].replace("", np.nan)
missing_vendors = df_txn["vendor"].isnull().sum()
df_txn["vendor"] = df_txn["vendor"].fillna("Unknown Vendor")

print(f"[CLEAN] Missing vendors filled: {missing_vendors}")
report.append(f"[Step 6] Missing vendors filled: {missing_vendors}")


# =============================================================================
# STEP 7 — NORMALIZE DEPARTMENT NAMES
# This is CRITICAL for the JOIN with budget table.
# If transactions say "Eng" and budget says "Engineering" — join breaks.
# We standardize both tables to the same department names.
# =============================================================================

DEPT_MAP = {
    "marketing"  : "Marketing",
    "engineering": "Engineering",
    "eng"        : "Engineering",
    "operations" : "Operations",
    "ops"        : "Operations",
    "hr"         : "HR",
    "human resources": "HR",
    "sales"      : "Sales",
    "finance"    : "Finance",
}

df_txn["department"] = (
    df_txn["department"]
    .str.strip()
    .str.lower()
    .map(lambda x: DEPT_MAP.get(x, x.title()) if pd.notnull(x) else x)
)

# Same for budget
df_budget = pd.read_csv(BUDGET_RAW)
df_budget["department"] = (
    df_budget["department"]
    .str.strip()
    .str.lower()
    .map(lambda x: DEPT_MAP.get(x, x.title()) if pd.notnull(x) else x)
)
df_budget["budget_amount"] = pd.to_numeric(df_budget["budget_amount"], errors="coerce").round(2)

print(f"[CLEAN] Department names normalized in both tables.")
report.append(f"[Step 7] Department names normalized for clean JOIN.")


# =============================================================================
# STEP 8 — FINAL VALIDATION (SQL on clean data)
# Use DuckDB for a quick sanity check before saving.
# =============================================================================

con.register("txn_clean", df_txn)
con.register("budget_clean", df_budget)

validation = con.execute("""
    SELECT
        COUNT(*)                                    AS total_rows,
        COUNT(DISTINCT department)                  AS unique_depts,
        SUM(CASE WHEN amount IS NULL THEN 1 END)   AS null_amounts,
        SUM(CASE WHEN is_anomaly THEN 1 END)        AS anomalies,
        SUM(CASE WHEN is_refund THEN 1 END)         AS refunds,
        MIN(txn_date)                               AS earliest_date,
        MAX(txn_date)                               AS latest_date
    FROM txn_clean
""").df()

print(f"\n[VALIDATE] Final check:")
print(validation.to_string(index=False))
report.append(f"\n[Step 8] Final Validation:")
report.append(validation.to_string(index=False))


# =============================================================================
# STEP 9 — SAVE CLEAN FILES
# =============================================================================

df_txn.to_csv(TXN_CLEAN, index=False)
df_budget.to_csv(BUDGET_CLEAN, index=False)

final_txn_rows    = len(df_txn)
final_budget_rows = len(df_budget)

summary = (
    f"\nFINAL SUMMARY\n"
    f"  Transactions : {raw_txn_count} raw → {final_txn_rows} clean "
    f"({raw_txn_count - final_txn_rows} removed)\n"
    f"  Budget       : {raw_budget_count} raw → {final_budget_rows} clean\n"
    f"  Anomalies flagged : {anomaly_count}\n"
    f"  Refunds flagged   : {refund_count}"
)

report.append(summary)
report.append(f"\nClean files saved to: outputs/")

with open(REPORT_PATH, "w", encoding="utf-8") as f:
    f.write("\n".join(report))

con.close()

print("\n" + "=" * 60)
print(summary)
print(f"\n  Transactions clean → {TXN_CLEAN}")
print(f"  Budget clean       → {BUDGET_CLEAN}")
print(f"  Cleaning report    → {REPORT_PATH}")
print("=" * 60)