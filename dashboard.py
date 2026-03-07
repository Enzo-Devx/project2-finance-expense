# =============================================================================
# dashboard.py
# Project 02 — Finance Expense Analysis
# Purpose: Interactive Streamlit dashboard for Marcus and the CEO.
#          Run with: streamlit run dashboard.py
# =============================================================================

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import os

# =============================================================================
# PAGE CONFIG — must be first Streamlit command
# =============================================================================

st.set_page_config(
    page_title="FinTrack — Expense Dashboard",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================================================================
# CUSTOM CSS — clean professional look
# =============================================================================

st.markdown("""
<style>
    /* Main background */
    .stApp { background-color: #F8FAFC; }

    /* KPI card style */
    .kpi-card {
        background: white;
        border-radius: 12px;
        padding: 20px 24px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.08);
        border-left: 5px solid #2563EB;
    }
    .kpi-card.danger  { border-left-color: #DC2626; }
    .kpi-card.warning { border-left-color: #D97706; }
    .kpi-card.success { border-left-color: #16A34A; }

    .kpi-label {
        font-size: 13px;
        color: #64748B;
        font-weight: 500;
        margin-bottom: 4px;
    }
    .kpi-value {
        font-size: 26px;
        font-weight: 700;
        color: #1E293B;
    }
    .kpi-sub {
        font-size: 12px;
        color: #94A3B8;
        margin-top: 2px;
    }

    /* Section headers */
    .section-header {
        font-size: 16px;
        font-weight: 700;
        color: #1E293B;
        margin: 24px 0 12px 0;
        padding-bottom: 6px;
        border-bottom: 2px solid #E2E8F0;
    }

    /* Anomaly alert */
    .anomaly-alert {
        background: #FEF2F2;
        border: 1px solid #FECACA;
        border-radius: 8px;
        padding: 12px 16px;
        color: #DC2626;
        font-weight: 600;
        margin-bottom: 16px;
    }

    /* Hide streamlit default elements */
    #MainMenu {visibility: hidden;}
    footer    {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# =============================================================================
# LOAD DATA
# Cache it so filters don't reload from disk every time.
# =============================================================================

@st.cache_data
def load_data():
    txn = pd.read_csv("outputs/project02_transactions_clean.csv")
    bud = pd.read_csv("data/project02_budget_plan.csv")
    q1  = pd.read_csv("outputs/q1_budget_vs_actual.csv")
    q2  = pd.read_csv("outputs/q2_spend_by_category.csv")
    q3  = pd.read_csv("outputs/q3_anomalies.csv")
    q4  = pd.read_csv("outputs/q4_monthly_trends.csv")
    q4t = pd.read_csv("outputs/q4_monthly_totals.csv")

    # Normalize
    txn["txn_date"]   = pd.to_datetime(txn["txn_date"], errors="coerce")
    txn["txn_month"]  = txn["txn_date"].dt.month
    txn["amount"]     = pd.to_numeric(txn["amount"], errors="coerce")
    txn["is_refund"]  = txn["is_refund"].astype(str).str.lower()  == "true"
    txn["is_anomaly"] = txn["is_anomaly"].astype(str).str.lower() == "true"

    return txn, bud, q1, q2, q3, q4, q4t

txn, bud, q1, q2, q3, q4, q4t = load_data()

MONTH_NAMES = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",
               6:"Jun",7:"Jul",8:"Aug",9:"Sep"}

DEPT_COLORS = {
    "Engineering": "#2563EB",
    "Marketing"  : "#7C3AED",
    "Sales"      : "#D97706",
    "Finance"    : "#DC2626",
    "Operations" : "#16A34A",
    "HR"         : "#0891B2",
}

COLORS = {
    "over"   : "#DC2626",
    "under"  : "#16A34A",
    "actual" : "#2563EB",
    "budget" : "#CBD5E1",
    "bg"     : "#F8FAFC",
    "grid"   : "#E2E8F0",
    "warning": "#D97706",
}


# =============================================================================
# SIDEBAR — FILTERS
# =============================================================================

st.sidebar.image("https://img.icons8.com/fluency/48/budget.png", width=48)
st.sidebar.title("FinTrack Dashboard")
st.sidebar.markdown("**Q1–Q3 2024 Expense Review**")
st.sidebar.markdown("---")

# Department filter
all_depts = sorted(txn["department"].dropna().unique().tolist())
selected_depts = st.sidebar.multiselect(
    "🏢 Department",
    options=all_depts,
    default=all_depts,
)

# Month filter
all_months = sorted(txn["txn_month"].dropna().unique().tolist())
month_labels = {m: MONTH_NAMES.get(int(m), str(m)) for m in all_months}
selected_months = st.sidebar.multiselect(
    "📅 Month",
    options=all_months,
    default=all_months,
    format_func=lambda x: month_labels[x],
)

# Status filter
all_statuses = sorted(txn["status"].dropna().unique().tolist())
selected_statuses = st.sidebar.multiselect(
    "📋 Status",
    options=all_statuses,
    default=[s for s in all_statuses if s != "Flagged"],
)

st.sidebar.markdown("---")
st.sidebar.markdown(
    "📊 **Project 02** — Finance Expense Analysis  \n"
    "🛠 Stack: Python · DuckDB · Plotly · Streamlit  \n"
    "👤 Analyst: Junior DA"
)

# =============================================================================
# APPLY FILTERS TO TRANSACTION DATA
# =============================================================================

filtered = txn[
    txn["department"].isin(selected_depts) &
    txn["txn_month"].isin(selected_months) &
    txn["status"].isin(selected_statuses) &
    (~txn["is_refund"]) &
    (~txn["is_anomaly"])
]

total_actual  = filtered["amount"].sum()
total_budget  = bud[bud["department"].isin(selected_depts)]["budget_amount"].sum()
variance      = total_actual - total_budget
variance_pct  = (variance / total_budget * 100) if total_budget > 0 else 0
anomaly_count = txn["is_anomaly"].sum()
refund_total  = txn[txn["is_refund"]]["amount"].sum()


# =============================================================================
# HEADER
# =============================================================================

st.markdown("## 💰 FinTrack — Expense Analysis Dashboard")
st.markdown("**Q1–Q3 2024 · Finance Team Review · Prepared for Marcus & CEO**")
st.markdown("---")


# =============================================================================
# KPI CARDS — ROW 1
# =============================================================================

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">💸 Total Actual Spend</div>
        <div class="kpi-value">₱{total_actual/1_000_000:.2f}M</div>
        <div class="kpi-sub">Filtered selection</div>
    </div>""", unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="kpi-card warning">
        <div class="kpi-label">📋 Total Budget</div>
        <div class="kpi-value">₱{total_budget/1_000_000:.2f}M</div>
        <div class="kpi-sub">Approved budget</div>
    </div>""", unsafe_allow_html=True)

with c3:
    card_class = "danger" if variance > 0 else "success"
    arrow = "▲" if variance > 0 else "▼"
    st.markdown(f"""
    <div class="kpi-card {card_class}">
        <div class="kpi-label">📊 Budget Variance</div>
        <div class="kpi-value">{arrow} {variance_pct:+.1f}%</div>
        <div class="kpi-sub">₱{variance:+,.0f} vs budget</div>
    </div>""", unsafe_allow_html=True)

with c4:
    st.markdown(f"""
    <div class="kpi-card danger">
        <div class="kpi-label">🚨 Flagged Transactions</div>
        <div class="kpi-value">{int(anomaly_count)}</div>
        <div class="kpi-sub">Requires investigation</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# =============================================================================
# ANOMALY ALERT BANNER
# =============================================================================

if anomaly_count > 0:
    st.markdown(f"""
    <div class="anomaly-alert">
        🚨 {int(anomaly_count)} anomalous transactions detected with unusually
        high amounts. Scroll down to the Anomaly Report for details.
    </div>""", unsafe_allow_html=True)


# =============================================================================
# ROW 2 — BUDGET VS ACTUAL + VARIANCE %
# =============================================================================

st.markdown('<div class="section-header">📊 Budget vs Actual Spend</div>',
            unsafe_allow_html=True)

col_left, col_right = st.columns([3, 2])

with col_left:
    # Recompute q1 based on filter
    act_grp = filtered.groupby("department")["amount"].sum().reset_index()
    act_grp.columns = ["department", "actual_spend"]
    bud_grp = bud[bud["department"].isin(selected_depts)].groupby(
        "department")["budget_amount"].sum().reset_index()
    bud_grp.columns = ["department", "total_budget"]
    q1_live = pd.merge(act_grp, bud_grp, on="department")
    q1_live["variance_pct"] = (
        (q1_live["actual_spend"] - q1_live["total_budget"])
        / q1_live["total_budget"] * 100
    ).round(1)
    q1_live["status"] = q1_live.apply(
        lambda r: "OVER BUDGET" if r["actual_spend"] > r["total_budget"]
        else "Under Budget", axis=1
    )
    q1_live = q1_live.sort_values("actual_spend", ascending=False)

    bar_colors = [
        COLORS["over"] if s == "OVER BUDGET" else COLORS["under"]
        for s in q1_live["status"]
    ]

    fig_bva = go.Figure()
    fig_bva.add_trace(go.Bar(
        name="Budget",
        x=q1_live["department"],
        y=q1_live["total_budget"],
        marker_color=COLORS["budget"],
        hovertemplate="<b>%{x}</b><br>Budget: ₱%{y:,.0f}<extra></extra>",
    ))
    fig_bva.add_trace(go.Bar(
        name="Actual",
        x=q1_live["department"],
        y=q1_live["actual_spend"],
        marker_color=bar_colors,
        hovertemplate="<b>%{x}</b><br>Actual: ₱%{y:,.0f}<extra></extra>",
    ))
    fig_bva.update_layout(
        barmode="group",
        paper_bgcolor="white", plot_bgcolor="white",
        height=350, margin=dict(l=40,r=20,t=20,b=40),
        legend=dict(orientation="h", y=1.05),
        yaxis=dict(tickprefix="₱", tickformat=",.0f",
                   gridcolor=COLORS["grid"]),
        xaxis=dict(showgrid=False),
        font=dict(size=11),
    )
    st.plotly_chart(fig_bva, use_container_width=True)

with col_right:
    q1_var = q1_live.sort_values("variance_pct", ascending=True)
    var_colors = [
        COLORS["over"] if v > 0 else COLORS["under"]
        for v in q1_var["variance_pct"]
    ]
    fig_var = go.Figure(go.Bar(
        x=q1_var["variance_pct"],
        y=q1_var["department"],
        orientation="h",
        marker_color=var_colors,
        text=[f"{v:+.1f}%" for v in q1_var["variance_pct"]],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Variance: %{x:+.1f}%<extra></extra>",
    ))
    fig_var.add_vline(x=0, line_color="#475569", line_width=1.5)
    fig_var.update_layout(
        paper_bgcolor="white", plot_bgcolor="white",
        height=350, margin=dict(l=10,r=60,t=20,b=40),
        xaxis=dict(ticksuffix="%", showgrid=False),
        yaxis=dict(gridcolor=COLORS["grid"]),
        font=dict(size=11),
    )
    st.plotly_chart(fig_var, use_container_width=True)


# =============================================================================
# ROW 3 — MONTHLY TREND + TREEMAP
# =============================================================================

st.markdown('<div class="section-header">📈 Spend Trends & Breakdown</div>',
            unsafe_allow_html=True)

col_trend, col_tree = st.columns([3, 2])

with col_trend:
    fig_trend = go.Figure()
    for dept in selected_depts:
        dept_data = filtered[filtered["department"] == dept].copy()
        monthly   = dept_data.groupby("txn_month")["amount"].sum().reset_index()
        monthly   = monthly.sort_values("txn_month")
        if monthly.empty:
            continue
        fig_trend.add_trace(go.Scatter(
            x=[MONTH_NAMES.get(int(m), str(m)) for m in monthly["txn_month"]],
            y=monthly["amount"],
            name=dept,
            mode="lines+markers",
            line=dict(color=DEPT_COLORS.get(dept, "#888"), width=2),
            marker=dict(size=6),
            hovertemplate=f"<b>{dept}</b><br>%{{x}}: ₱%{{y:,.0f}}<extra></extra>",
        ))
    fig_trend.update_layout(
        paper_bgcolor="white", plot_bgcolor="white",
        height=350, margin=dict(l=40,r=20,t=20,b=40),
        legend=dict(orientation="h", y=1.08, font=dict(size=10)),
        yaxis=dict(tickprefix="₱", tickformat=",.0f",
                   gridcolor=COLORS["grid"]),
        xaxis=dict(showgrid=False),
        font=dict(size=11),
    )
    st.plotly_chart(fig_trend, use_container_width=True)

with col_tree:
    cat_grp = (
        filtered.groupby(["department","category"])["amount"]
        .sum().reset_index()
    )
    cat_grp.columns = ["department","category","total_spend"]
    cat_grp = cat_grp[cat_grp["total_spend"] > 0]

    if not cat_grp.empty:
        fig_tree = px.treemap(
            cat_grp,
            path=["department","category"],
            values="total_spend",
            color="department",
            color_discrete_map=DEPT_COLORS,
        )
        fig_tree.update_traces(
            hovertemplate=(
                "<b>%{label}</b><br>"
                "Spend: ₱%{value:,.0f}<extra></extra>"
            ),
            texttemplate="%{label}",
        )
        fig_tree.update_layout(
            paper_bgcolor="white",
            height=350,
            margin=dict(l=0,r=0,t=20,b=0),
        )
        st.plotly_chart(fig_tree, use_container_width=True)


# =============================================================================
# ROW 4 — ANOMALY REPORT TABLE
# =============================================================================

st.markdown('<div class="section-header">🚨 Anomaly Report — Flagged Transactions</div>',
            unsafe_allow_html=True)

if not q3.empty:
    q3_display = q3.copy()
    q3_display["amount"] = q3_display["amount"].apply(lambda x: f"₱{x:,.0f}")
    q3_display["txn_date"] = pd.to_datetime(
        q3_display["txn_date"], errors="coerce"
    ).dt.strftime("%Y-%m-%d")
    q3_display = q3_display.rename(columns={
        "txn_id"    : "Transaction ID",
        "txn_date"  : "Date",
        "department": "Department",
        "category"  : "Category",
        "vendor"    : "Vendor",
        "amount"    : "Amount",
        "status"    : "Status",
    })
    st.dataframe(
        q3_display,
        use_container_width=True,
        hide_index=True,
    )
    st.caption(
        "⚠️ These transactions were flagged using IQR statistical method "
        "(amount > Q3 + 3×IQR). Recommend manual review and approval verification."
    )
else:
    st.success("✅ No anomalous transactions detected.")


# =============================================================================
# ROW 5 — TOP VENDORS TABLE
# =============================================================================

st.markdown('<div class="section-header">🏪 Top Vendors by Spend</div>',
            unsafe_allow_html=True)

vendor_grp = (
    filtered[filtered["vendor"] != "Unknown Vendor"]
    .groupby(["vendor","department"])["amount"]
    .agg(["sum","count"])
    .reset_index()
    .sort_values("sum", ascending=False)
    .head(10)
    .reset_index(drop=True)
)
vendor_grp.columns = ["Vendor","Department","Total Spend","# Transactions"]
vendor_grp["Total Spend"] = vendor_grp["Total Spend"].apply(lambda x: f"₱{x:,.0f}")

st.dataframe(vendor_grp, use_container_width=True, hide_index=True)


# =============================================================================
# FOOTER
# =============================================================================

st.markdown("---")
st.markdown(
    "<div style='text-align:center; color:#94A3B8; font-size:12px;'>"
    "FinTrack Expense Dashboard · Project 02 · "
    "Built with Python, DuckDB, Plotly & Streamlit"
    "</div>",
    unsafe_allow_html=True,
)