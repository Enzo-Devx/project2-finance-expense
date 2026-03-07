# =============================================================================
# visualize_results.py
# Project 02 — Finance Expense Analysis
# Purpose: Generate interactive Plotly charts from analysis outputs.
#          Charts saved as HTML files — open in any browser, fully interactive.
#          Also exports PNG versions for emails/slides.
# =============================================================================

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import os

# --- PATHS ---
CHARTS_DIR = "outputs/charts"
os.makedirs(CHARTS_DIR, exist_ok=True)

# --- LOAD DATA ---
q1 = pd.read_csv("outputs/q1_budget_vs_actual.csv")
q2 = pd.read_csv("outputs/q2_spend_by_category.csv")
q2v= pd.read_csv("outputs/q2_top_vendors.csv")
q3 = pd.read_csv("outputs/q3_anomalies.csv")
q4 = pd.read_csv("outputs/q4_monthly_trends.csv")
q4t= pd.read_csv("outputs/q4_monthly_totals.csv")

print("=" * 60)
print("  VISUALIZE_RESULTS.PY — Interactive Plotly Charts")
print("=" * 60)

# =============================================================================
# GLOBAL STYLE
# =============================================================================

COLORS = {
    "over"    : "#DC2626",   # red — over budget
    "under"   : "#16A34A",   # green — under budget
    "actual"  : "#2563EB",   # blue — actual spend
    "budget"  : "#94A3B8",   # gray — budget
    "warning" : "#D97706",   # amber
    "bg"      : "#F8FAFC",
    "grid"    : "#E2E8F0",
}

DEPT_COLORS = {
    "Engineering": "#2563EB",
    "Marketing"  : "#7C3AED",
    "Sales"      : "#D97706",
    "Finance"    : "#DC2626",
    "Operations" : "#16A34A",
    "HR"         : "#0891B2",
}

MONTH_NAMES = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",
               6:"Jun",7:"Jul",8:"Aug",9:"Sep"}

def base_layout(title, height=500):
    return dict(
        title=dict(text=title, font=dict(size=16, color="#1E293B"), x=0.02),
        paper_bgcolor=COLORS["bg"],
        plot_bgcolor=COLORS["bg"],
        font=dict(family="sans-serif", size=12, color="#475569"),
        height=height,
        margin=dict(l=60, r=40, t=70, b=60),
        xaxis=dict(showgrid=False, linecolor=COLORS["grid"]),
        yaxis=dict(gridcolor=COLORS["grid"], linecolor=COLORS["grid"]),
    )


# =============================================================================
# CHART 1 — BUDGET VS ACTUAL BY DEPARTMENT (Grouped Bar)
# The headline chart. Red = over budget. Shows the damage at a glance.
# =============================================================================

print("\n[CHART 1] Budget vs Actual by Department...")

q1_sorted = q1.sort_values("variance", ascending=False)
bar_colors = [
    COLORS["over"] if s == "OVER BUDGET" else COLORS["under"]
    for s in q1_sorted["budget_status"]
]

fig1 = go.Figure()

fig1.add_trace(go.Bar(
    name="Budget",
    x=q1_sorted["department"],
    y=q1_sorted["total_budget"],
    marker_color=COLORS["budget"],
    text=[f"₱{v:,.0f}" for v in q1_sorted["total_budget"]],
    textposition="outside",
    textfont=dict(size=10),
))

fig1.add_trace(go.Bar(
    name="Actual Spend",
    x=q1_sorted["department"],
    y=q1_sorted["actual_spend"],
    marker_color=bar_colors,
    text=[f"₱{v:,.0f}" for v in q1_sorted["actual_spend"]],
    textposition="outside",
    textfont=dict(size=10),
))

fig1.update_layout(
    **base_layout("Budget vs Actual Spend by Department — All Departments Over Budget 🚨", height=520),
    barmode="group",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)
fig1.update_yaxes(tickprefix="₱", tickformat=",.0f")

fig1.write_html(f"{CHARTS_DIR}/chart1_budget_vs_actual.html")
fig1.write_image(f"{CHARTS_DIR}/chart1_budget_vs_actual.png", width=1000, height=520, scale=2)
print("   ✓ chart1_budget_vs_actual")


# =============================================================================
# CHART 2 — VARIANCE % BY DEPARTMENT (Horizontal Bar)
# Shows who is MOST over budget proportionally, not just in raw numbers.
# =============================================================================

print("\n[CHART 2] Variance % by Department...")

q1_var = q1.sort_values("variance_pct", ascending=True)
var_colors = [
    COLORS["over"] if v > 0 else COLORS["under"]
    for v in q1_var["variance_pct"]
]

fig2 = go.Figure(go.Bar(
    x=q1_var["variance_pct"],
    y=q1_var["department"],
    orientation="h",
    marker_color=var_colors,
    text=[f"{v:+.1f}%" for v in q1_var["variance_pct"]],
    textposition="outside",
    hovertemplate="<b>%{y}</b><br>Variance: %{x:+.1f}%<extra></extra>",
))

fig2.add_vline(x=0, line_color="#475569", line_width=1.5)
fig2.update_layout(
    **base_layout("Budget Variance % by Department — Engineering +210% Over 🚨", height=420),
)
fig2.update_xaxes(ticksuffix="%", title="Variance vs Budget (%)")

fig2.write_html(f"{CHARTS_DIR}/chart2_variance_pct.html")
fig2.write_image(f"{CHARTS_DIR}/chart2_variance_pct.png", width=900, height=420, scale=2)
print("   ✓ chart2_variance_pct")


# =============================================================================
# CHART 3 — TOP SPENDING CATEGORIES (Treemap)
# Treemaps are great for showing proportional spend across dept + category.
# One glance tells you where the money is going.
# =============================================================================

print("\n[CHART 3] Spend by Category (Treemap)...")

fig3 = px.treemap(
    q2,
    path=["department", "category"],
    values="total_spend",
    color="department",
    color_discrete_map=DEPT_COLORS,
    custom_data=["txn_count", "avg_per_txn"],
)

fig3.update_traces(
    hovertemplate=(
        "<b>%{label}</b><br>"
        "Total Spend: ₱%{value:,.0f}<br>"
        "Transactions: %{customdata[0]}<br>"
        "Avg per Txn: ₱%{customdata[1]:,.0f}<extra></extra>"
    ),
    textinfo="label+value",
    texttemplate="%{label}<br>₱%{value:,.0f}",
)

fig3.update_layout(
    title=dict(
        text="Spend Breakdown by Department & Category",
        font=dict(size=16, color="#1E293B"), x=0.02
    ),
    paper_bgcolor=COLORS["bg"],
    height=520,
    margin=dict(l=20, r=20, t=60, b=20),
)

fig3.write_html(f"{CHARTS_DIR}/chart3_spend_treemap.html")
fig3.write_image(f"{CHARTS_DIR}/chart3_spend_treemap.png", width=1000, height=520, scale=2)
print("   ✓ chart3_spend_treemap")


# =============================================================================
# CHART 4 — MONTHLY SPEND TREND BY DEPARTMENT (Line Chart)
# Shows which departments spiked which months.
# =============================================================================

print("\n[CHART 4] Monthly Spend Trend by Department...")

fig4 = go.Figure()

for dept, color in DEPT_COLORS.items():
    dept_data = q4[q4["department"] == dept].sort_values("month")
    if dept_data.empty:
        continue
    fig4.add_trace(go.Scatter(
        x=[MONTH_NAMES.get(int(m), str(m)) for m in dept_data["month"]],
        y=dept_data["actual_spend"],
        name=dept,
        mode="lines+markers",
        line=dict(color=color, width=2),
        marker=dict(size=6),
        hovertemplate=f"<b>{dept}</b><br>Month: %{{x}}<br>Spend: ₱%{{y:,.0f}}<extra></extra>",
    ))

fig4.update_layout(
    **base_layout("Monthly Spend by Department — Jan to Sep 2024", height=500),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)
fig4.update_yaxes(tickprefix="₱", tickformat=",.0f", title="Actual Spend (₱)")
fig4.update_xaxes(title="Month")

fig4.write_html(f"{CHARTS_DIR}/chart4_monthly_trends.html")
fig4.write_image(f"{CHARTS_DIR}/chart4_monthly_trends.png", width=1000, height=500, scale=2)
print("   ✓ chart4_monthly_trends")


# =============================================================================
# CHART 5 — ANOMALOUS TRANSACTIONS (Table + Bar)
# Present the 5 flagged transactions clearly for Marcus.
# A table visual is the right choice here — exact numbers matter.
# =============================================================================

print("\n[CHART 5] Anomalous Transactions...")

q3["txn_date"] = pd.to_datetime(q3["txn_date"]).dt.strftime("%Y-%m-%d")
q3_display = q3.copy()
q3_display["amount_fmt"] = q3_display["amount"].apply(lambda x: f"₱{x:,.0f}")

fig5 = go.Figure()

# Bar showing anomaly amounts
fig5.add_trace(go.Bar(
    x=q3_display["txn_id"],
    y=q3_display["amount"],
    marker_color=COLORS["over"],
    text=q3_display["amount_fmt"],
    textposition="outside",
    hovertemplate=(
        "<b>%{x}</b><br>"
        "Amount: ₱%{y:,.0f}<br>"
        "<extra></extra>"
    ),
    customdata=q3_display[["department","category","vendor"]].values,
))

# Add average normal transaction line for context
avg_normal = pd.read_csv("outputs/project02_transactions_clean.csv")
avg_normal["amount"] = pd.to_numeric(avg_normal["amount"], errors="coerce")
avg_normal["is_anomaly"] = avg_normal["is_anomaly"].astype(str).str.lower() == "true"
avg_normal_val = avg_normal[~avg_normal["is_anomaly"]]["amount"].mean()

fig5.add_hline(
    y=avg_normal_val,
    line_color=COLORS["warning"],
    line_dash="dash",
    line_width=2,
    annotation_text=f"Avg normal txn: ₱{avg_normal_val:,.0f}",
    annotation_position="top right",
    annotation_font=dict(color=COLORS["warning"]),
)

fig5.update_layout(
    **base_layout("Flagged Anomalous Transactions — Requires Investigation 🚨", height=480),
    showlegend=False,
)
fig5.update_yaxes(tickprefix="₱", tickformat=",.0f", title="Transaction Amount (₱)")
fig5.update_xaxes(title="Transaction ID")

fig5.write_html(f"{CHARTS_DIR}/chart5_anomalies.html")
fig5.write_image(f"{CHARTS_DIR}/chart5_anomalies.png", width=900, height=480, scale=2)
print("   ✓ chart5_anomalies")


# =============================================================================
# DONE
# =============================================================================

all_files = sorted(os.listdir(CHARTS_DIR))
print("\n" + "=" * 60)
print("  ALL CHARTS GENERATED")
print(f"  Location: {CHARTS_DIR}/")
print(f"\n  HTML (interactive) — open in browser for Zoom calls:")
for f in all_files:
    if f.endswith(".html"):
        print(f"    → {f}")
print(f"\n  PNG (static) — use in emails/slides:")
for f in all_files:
    if f.endswith(".png"):
        print(f"    → {f}")
print("=" * 60)