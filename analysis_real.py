"""
Real Supply Chain Analytics — DataCo Global dataset
===================================================
Analyzes a REAL public supply-chain dataset (180,519 orders, 2015-2018) from
DataCo Global. Calculates delivery, shipping-mode, regional, and profit KPIs,
prints them, and saves charts to charts_real/.

Data source (free): see download_data.py / README.
Run:
    .venv/bin/python analysis_real.py

Written step by step to stay easy to read and explain.
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

HERE = Path(__file__).parent
RAW = HERE / "realdata" / "DataCoSupplyChainDataset.csv"
CHARTS = HERE / "charts_real"
CHARTS.mkdir(exist_ok=True)


# ── Step 1: load the real data ──────────────────────────────────────────────
# The file is latin-1 encoded (it has accented characters), so we say so.
print("Loading real DataCo dataset ...")
df = pd.read_csv(RAW, encoding="latin-1", low_memory=False)
print(f"Loaded {len(df):,} orders, {len(df.columns)} columns.\n")

# Parse the order date so we can look at trends over time.
df["OrderDate"] = pd.to_datetime(df["order date (DateOrders)"])
df["OrderYear"] = df["OrderDate"].dt.year

# Friendlier short names for the columns we use a lot.
df = df.rename(columns={
    "Days for shipping (real)": "ActualDays",
    "Days for shipment (scheduled)": "ScheduledDays",
    "Late_delivery_risk": "IsLate",          # 1 = delivered late, 0 = on time
})


# ── Step 2: overall delivery performance ────────────────────────────────────
print("=" * 60)
print(" OVERALL DELIVERY PERFORMANCE")
print("=" * 60)

late_rate = df["IsLate"].mean() * 100
on_time_rate = 100 - late_rate
avg_actual = df["ActualDays"].mean()
avg_scheduled = df["ScheduledDays"].mean()

print(f"Total orders .............. {len(df):,}")
print(f"On-time rate .............. {on_time_rate:5.1f} %")
print(f"Late rate ................. {late_rate:5.1f} %")
print(f"Avg actual ship days ...... {avg_actual:5.2f}")
print(f"Avg scheduled ship days ... {avg_scheduled:5.2f}")
print(f"Avg days OVER schedule .... {avg_actual - avg_scheduled:5.2f}")

print("\nDelivery Status breakdown:")
status = df["Delivery Status"].value_counts()
for name, count in status.items():
    print(f"  {name:22s} {count:>7,}  ({count / len(df) * 100:4.1f}%)")


# ── Step 3: late rate by shipping mode ──────────────────────────────────────
print("\n" + "=" * 60)
print(" LATE RATE BY SHIPPING MODE")
print("=" * 60)

mode_groups = df.groupby("Shipping Mode")
by_mode = pd.DataFrame()
by_mode["Orders"] = mode_groups["IsLate"].count()
by_mode["LatePct"] = (mode_groups["IsLate"].mean() * 100).round(1)
by_mode["AvgActualDays"] = mode_groups["ActualDays"].mean().round(2)
by_mode = by_mode.sort_values("LatePct", ascending=False)
print(by_mode.to_string())


# ── Step 4: late rate by market / region ────────────────────────────────────
print("\n" + "=" * 60)
print(" LATE RATE BY MARKET")
print("=" * 60)

market_groups = df.groupby("Market")
by_market = pd.DataFrame()
by_market["Orders"] = market_groups["IsLate"].count()
by_market["LatePct"] = (market_groups["IsLate"].mean() * 100).round(1)
by_market = by_market.sort_values("LatePct", ascending=False)
print(by_market.to_string())


# ── Step 5: sales & profit by department ────────────────────────────────────
print("\n" + "=" * 60)
print(" SALES & PROFIT BY DEPARTMENT (top 10 by sales)")
print("=" * 60)

dept_groups = df.groupby("Department Name")
by_dept = pd.DataFrame()
by_dept["Sales"] = dept_groups["Sales"].sum().round(0)
by_dept["Profit"] = dept_groups["Order Profit Per Order"].sum().round(0)
by_dept["LatePct"] = (dept_groups["IsLate"].mean() * 100).round(1)
by_dept = by_dept.sort_values("Sales", ascending=False).head(10)
print(by_dept.to_string())


# ── Step 6: late rate trend by year ─────────────────────────────────────────
print("\n" + "=" * 60)
print(" LATE RATE BY YEAR")
print("=" * 60)
by_year = (df.groupby("OrderYear")["IsLate"].mean() * 100).round(1)
print(by_year.to_string())


# ── Step 7: charts ──────────────────────────────────────────────────────────
# Chart 1: late rate by shipping mode
fig, ax = plt.subplots(figsize=(8, 4.5))
colors = ["#c62828" if v >= 50 else "#2e7d32" for v in by_mode["LatePct"]]
ax.barh(by_mode.index, by_mode["LatePct"], color=colors)
ax.axvline(50, ls="--", color="gray")
ax.set_title("Late-Delivery Rate by Shipping Mode (DataCo, real data)")
ax.set_xlabel("Late %")
fig.tight_layout(); fig.savefig(CHARTS / "01_late_by_mode.png", dpi=120)

# Chart 2: late rate by market
fig, ax = plt.subplots(figsize=(8, 4.5))
ax.barh(by_market.index, by_market["LatePct"], color="#1565c0")
ax.set_title("Late-Delivery Rate by Market")
ax.set_xlabel("Late %")
fig.tight_layout(); fig.savefig(CHARTS / "02_late_by_market.png", dpi=120)

# Chart 3: top departments by sales
fig, ax = plt.subplots(figsize=(8, 4.5))
by_dept["Sales"].sort_values().plot(kind="barh", ax=ax, color="#6a1b9a")
ax.set_title("Total Sales by Department (top 10)")
ax.set_xlabel("Sales ($)")
fig.tight_layout(); fig.savefig(CHARTS / "03_sales_by_department.png", dpi=120)

# Chart 4: scheduled vs actual shipping days by mode
fig, ax = plt.subplots(figsize=(8, 4.5))
sched = mode_groups["ScheduledDays"].mean()
actual = mode_groups["ActualDays"].mean()
x = range(len(sched))
ax.bar([i - 0.2 for i in x], sched, width=0.4, label="Scheduled", color="#90caf9")
ax.bar([i + 0.2 for i in x], actual, width=0.4, label="Actual", color="#ef6c00")
ax.set_xticks(list(x)); ax.set_xticklabels(sched.index, rotation=20, ha="right")
ax.set_title("Scheduled vs Actual Shipping Days by Mode")
ax.set_ylabel("Days"); ax.legend()
fig.tight_layout(); fig.savefig(CHARTS / "04_scheduled_vs_actual.png", dpi=120)

print("\n" + "=" * 60)
print(" CHARTS SAVED to charts_real/")
print("=" * 60)
for p in sorted(CHARTS.glob("*.png")):
    print(f"  {p.name}")
