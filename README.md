# 💰 Finance Expense Analysis

> **Role:** Junior Data Analyst  
> **Scenario:** FinTech startup FinTrack is massively overspending. CEO wants answers.  
> **Stack:** Python · pandas · DuckDB · Plotly · Streamlit

---

## 🧠 Business Problem

The finance team flagged that company-wide spending was significantly over budget. The manager needed to understand:

- Which departments are over budget and by how much?
- Where is the money actually going?
- Are there any suspicious transactions?
- What does the monthly spending trend look like?

---

## 📊 Key Findings

| Metric | Value |
|---|---|
| Total Actual Spend | ₱37,331,789 |
| Total Budget | ₱15,596,330 |
| Overall Variance | **+₱21,735,459 (+139.4%) 🚨** |
| Departments Over Budget | **6 of 6** |
| Flagged Transactions | **5 anomalies** |

### Department Breakdown
| Department | Actual | Budget | Variance |
|---|---|---|---|
| Engineering | ₱12.15M | ₱3.91M | **+210.7% 🚨** |
| Marketing | ₱7.99M | ₱3.12M | **+156.0% 🚨** |
| Finance | ₱2.70M | ₱1.24M | **+116.7% 🚨** |
| Sales | ₱6.78M | ₱3.57M | **+90.1% 🚨** |
| Operations | ₱3.25M | ₱2.02M | **+60.8% 🚨** |
| HR | ₱4.46M | ₱2.79M | **+60.2% 🚨** |

---

## 🛠 Tech Stack

| Tool | Purpose |
|---|---|
| Python / pandas | Data cleaning & transformation |
| DuckDB | SQL JOINs on CSV files |
| Plotly | Interactive HTML charts |
| Streamlit | Interactive dashboard |
| Git | Version control |

---

## 📁 Project Structure

```
project2_finance/
├── data/
│   ├── project02_transactions_raw.csv    ← raw transactions
│   └── project02_budget_plan.csv         ← budget reference table
├── outputs/
│   ├── project02_transactions_clean.csv  ← cleaned data
│   ├── q1_budget_vs_actual.csv           ← department analysis
│   ├── q2_spend_by_category.csv          ← category breakdown
│   ├── q3_anomalies.csv                  ← flagged transactions
│   ├── q4_monthly_trends.csv             ← monthly trends
│   ├── analysis_report.txt               ← full text report
│   └── charts/                           ← HTML + PNG charts
├── clean_data.py                         ← ETL pipeline
├── analyze_data.py                       ← DuckDB SQL analysis
├── visualize_results.py                  ← Plotly charts
├── dashboard.py                          ← Streamlit dashboard
└── .gitignore
```

---

## ▶️ How to Run

```bash
# 1. Clone the repo
git clone https://github.com/Enzo-Devx/project2-finance-expense.git
cd project2-finance-expense

# 2. Create and activate virtual environment
python -m venv venv
venv\Scripts\Activate.ps1      # Windows
source venv/bin/activate       # Mac/Linux

# 3. Install dependencies
pip install pandas numpy duckdb plotly streamlit kaleido

# 4. Run the pipeline in order
python clean_data.py
python analyze_data.py
python visualize_results.py

# 5. Launch the dashboard
streamlit run dashboard.py
```

---

## 🔑 Key SQL Concept — JOIN Fan-Out Fix

A critical bug encountered and fixed during this project:

```sql
-- ❌ WRONG — budget inflates when joined to raw transactions
SELECT department, SUM(t.amount), SUM(b.budget_amount)
FROM transactions t
LEFT JOIN budget b ON t.department = b.department
GROUP BY department

-- ✅ CORRECT — pre-aggregate both sides with CTEs first
WITH actual  AS (SELECT department, SUM(amount) ...),
     planned AS (SELECT department, SUM(budget_amount) ...)
SELECT a.department, a.actual_spend, p.total_budget
FROM actual a LEFT JOIN planned p ON a.department = p.department
```

---

## 📈 Dashboard Features

- 4 KPI cards — Total Spend, Budget, Variance %, Flagged Transactions
- Sidebar filters — by department, month, status
- Budget vs Actual grouped bar chart (live filtered)
- Variance % horizontal bar chart
- Monthly spend trend lines per department
- Category treemap
- Anomaly report table with flagged transactions

---

## 💡 Business Recommendation

1. **Immediate** — Investigate 5 flagged transactions (₱500K–₱900K each)
2. **Short term** — Engineering needs a hard budget review (+210% over)
3. **Short term** — Implement monthly budget checkpoints per department
4. **Medium term** — Revise 2025 budgets with realistic baselines

---

*Built as part of a data analyst portfolio. Simulated business scenario with realistic synthetic data.*
