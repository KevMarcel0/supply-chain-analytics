"""
One-page visual summary — Supply Chain Analytics
=================================================
Combines the strongest charts into a single shareable image you can attach to
job applications or drop into a portfolio.

Run:
    .venv/bin/python summary.py
Output: summary.png
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import gridspec
import pandas as pd

HERE = Path(__file__).parent
RAW = HERE / "realdata" / "DataCoSupplyChainDataset.csv"

# ── load + prep the real data ───────────────────────────────────────────────
df = pd.read_csv(RAW, encoding="latin-1", low_memory=False)
df = df.rename(columns={
    "Days for shipping (real)": "ActualDays",
    "Days for shipment (scheduled)": "ScheduledDays",
    "Late_delivery_risk": "IsLate",
})

late_rate = df["IsLate"].mean() * 100
mode = df.groupby("Shipping Mode")
by_mode_late = (mode["IsLate"].mean() * 100).sort_values()
sched = mode["ScheduledDays"].mean()
actual = mode["ActualDays"].mean()
by_market = (df.groupby("Market")["IsLate"].mean() * 100).sort_values()
by_dept = df.groupby("Department Name")["Sales"].sum().sort_values().tail(6) / 1e6

# ── build the page ──────────────────────────────────────────────────────────
fig = plt.figure(figsize=(11, 14))
fig.patch.set_facecolor("white")
grid = gridspec.GridSpec(4, 2, height_ratios=[0.9, 3, 3, 1.1],
                         hspace=0.55, wspace=0.3,
                         left=0.09, right=0.95, top=0.97, bottom=0.04)

# Title banner
title_ax = fig.add_subplot(grid[0, :]); title_ax.axis("off")
title_ax.text(0.5, 0.72, "Supply Chain Analytics — Key Findings",
              ha="center", va="center", fontsize=24, fontweight="bold")
title_ax.text(0.5, 0.30,
              "DataCo Global — 180,519 real orders (2015–2018)  ·  SQL + Python  ·  github.com/KevMarcel0",
              ha="center", va="center", fontsize=12, color="#555")

# Chart 1: late rate by shipping mode
ax1 = fig.add_subplot(grid[1, 0])
colors = ["#c62828" if v >= 50 else "#2e7d32" for v in by_mode_late]
ax1.barh(by_mode_late.index, by_mode_late.values, color=colors)
ax1.axvline(50, ls="--", color="gray", lw=1)
ax1.set_title("Late-Delivery Rate by Shipping Mode", fontweight="bold")
ax1.set_xlabel("Late %")
for i, v in enumerate(by_mode_late.values):
    ax1.text(v - 3, i, f"{v:.0f}%", va="center", ha="right", color="white", fontweight="bold")

# Chart 2: scheduled vs actual days (the root cause)
ax2 = fig.add_subplot(grid[1, 1])
x = range(len(sched))
ax2.bar([i - 0.2 for i in x], sched.values, width=0.4, label="Promised", color="#90caf9")
ax2.bar([i + 0.2 for i in x], actual.values, width=0.4, label="Actual", color="#ef6c00")
ax2.set_xticks(list(x)); ax2.set_xticklabels(sched.index, rotation=20, ha="right", fontsize=9)
ax2.set_title("Promised vs Actual Shipping Days", fontweight="bold")
ax2.set_ylabel("Days"); ax2.legend(fontsize=9)

# Chart 3: late rate by market (proves it's not regional)
ax3 = fig.add_subplot(grid[2, 0])
ax3.barh(by_market.index, by_market.values, color="#1565c0")
ax3.set_xlim(0, 70)
ax3.set_title("Late Rate by Market — flat everywhere", fontweight="bold")
ax3.set_xlabel("Late %")
for i, v in enumerate(by_market.values):
    ax3.text(v + 1, i, f"{v:.0f}%", va="center", fontsize=9)

# Chart 4: sales by department
ax4 = fig.add_subplot(grid[2, 1])
ax4.barh(by_dept.index, by_dept.values, color="#6a1b9a")
ax4.set_title("Top Departments by Sales", fontweight="bold")
ax4.set_xlabel("Sales ($ millions)")

# Findings strip
notes_ax = fig.add_subplot(grid[3, :]); notes_ax.axis("off")
findings = (
    f"KEY FINDINGS\n"
    f"•  {late_rate:.0f}% of all orders arrive LATE — a systemic problem, stable across 2015–2018.\n"
    f"•  'First Class' shipping is late 95% of the time, while cheap 'Standard Class' is only 38% late.\n"
    f"•  Lateness is ~55% in EVERY market → it is not a regional/logistics issue.\n"
    f"•  Root cause: premium tiers' ACTUAL days exceed their PROMISED days. The fix is realistic\n"
    f"   delivery windows, not more shipping spend."
)
notes_ax.text(0.0, 0.95, findings, ha="left", va="top", fontsize=12.5,
              family="monospace",
              bbox=dict(boxstyle="round,pad=0.8", facecolor="#f1f5f9", edgecolor="#cbd5e1"))

fig.savefig(HERE / "summary.png", dpi=130, facecolor="white")
print("Saved summary.png")
