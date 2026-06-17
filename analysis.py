"""
Supply Chain Analytics — Python analysis + charts (simple version)
==================================================================
Reads the data, calculates the key supply-chain numbers, prints them,
and saves 4 charts to the charts/ folder.

Run:
    .venv/bin/python analysis.py

Written to be easy to read: each KPI is calculated step by step,
with no clever one-liners. If you can read a spreadsheet, you can read this.
"""

import sqlite3
from pathlib import Path

import matplotlib
matplotlib.use("Agg")          # save charts to files instead of opening a window
import matplotlib.pyplot as plt
import pandas as pd

HERE = Path(__file__).parent
CHARTS = HERE / "charts"
CHARTS.mkdir(exist_ok=True)


# ── Step 1: load the tables ─────────────────────────────────────────────────
def load_tables():
    """Read every table out of the SQLite database into a pandas DataFrame."""
    connection = sqlite3.connect(HERE / "supplychain.db")
    table_names = [
        "dim_supplier", "dim_product", "dim_date",
        "fact_purchase_orders", "fact_shipments", "fact_inventory_snapshot",
    ]
    tables = {}
    for name in table_names:
        tables[name] = pd.read_sql(f"SELECT * FROM {name}", connection)
    connection.close()
    return tables


tables = load_tables()
purchase_orders = tables["fact_purchase_orders"]
shipments = tables["fact_shipments"]
inventory = tables["fact_inventory_snapshot"]
suppliers = tables["dim_supplier"]
products = tables["dim_product"]
dates = tables["dim_date"]


# ── Step 2: Supplier scorecard ──────────────────────────────────────────────
# Add the supplier name onto each purchase order, then group by supplier.
print("\n" + "=" * 60)
print(" SUPPLIER SCORECARD")
print("=" * 60)

po_with_supplier = purchase_orders.merge(suppliers, on="SupplierID")
groups = po_with_supplier.groupby("SupplierName")

scorecard = pd.DataFrame()
scorecard["POs"] = groups["POID"].count()
# OnTimeFlag is 1 when on time, 0 when late. The average = the on-time share.
scorecard["OnTimePct"] = (groups["OnTimeFlag"].mean() * 100).round(1)
# Fill rate = total units received divided by total units ordered.
scorecard["FillRatePct"] = (groups["QtyReceived"].sum()
                            / groups["QtyOrdered"].sum() * 100).round(1)
# Reject rate = total units rejected divided by total units received.
scorecard["RejectPct"] = (groups["QtyRejected"].sum()
                          / groups["QtyReceived"].sum() * 100).round(2)

scorecard = scorecard.sort_values("OnTimePct", ascending=False)
print(scorecard.to_string())


# ── Step 3: Overall health numbers ──────────────────────────────────────────
print("\n" + "=" * 60)
print(" OVERALL HEALTH")
print("=" * 60)

# A purchase order is "perfect" when ALL three are true:
#   on time, received everything ordered, and zero rejects.
is_on_time = purchase_orders["OnTimeFlag"] == 1
is_complete = purchase_orders["QtyReceived"] >= purchase_orders["QtyOrdered"]
is_clean = purchase_orders["QtyRejected"] == 0
is_perfect = is_on_time & is_complete & is_clean

perfect_rate = is_perfect.mean() * 100
inbound_on_time = purchase_orders["OnTimeFlag"].mean() * 100
outbound_on_time = shipments["OnTimeFlag"].mean() * 100

print(f"Perfect-Order Rate ........ {perfect_rate:5.1f} %")
print(f"Inbound On-Time ........... {inbound_on_time:5.1f} %")
print(f"Outbound On-Time .......... {outbound_on_time:5.1f} %")


# ── Step 4: Inventory turnover by product family ────────────────────────────
print("\n" + "=" * 60)
print(" INVENTORY TURNOVER BY FAMILY")
print("=" * 60)

inv_with_family = inventory.merge(products, on="ProductID")
family_groups = inv_with_family.groupby("Family")

family = pd.DataFrame()
family["AvgOnHand"] = family_groups["OnHandQty"].mean().round(0)
family["UnitsSold"] = family_groups["UnitsSoldMonth"].sum()
# Turnover = how many times we sold through the shelf stock. Higher = faster mover.
family["Turnover"] = (family["UnitsSold"] / family["AvgOnHand"]).round(1)
# How often this family sat below its reorder point (a stockout-risk signal).
family["PctBelowReorder"] = (family_groups["BelowReorderFlag"].mean() * 100).round(1)

family = family.sort_values("Turnover", ascending=False)
print(family.to_string())


# ── Step 5: Carrier cost vs service ─────────────────────────────────────────
carrier_groups = shipments.groupby("Carrier")
carrier = pd.DataFrame()
carrier["OnTimePct"] = (carrier_groups["OnTimeFlag"].mean() * 100).round(1)
carrier["FreightPerUnit"] = (carrier_groups["FreightCost"].sum()
                             / carrier_groups["Qty"].sum()).round(3)


# ── Step 6: make the charts ─────────────────────────────────────────────────
# Chart 1: supplier on-time bar (green if >= 85% target, else red)
bar_colors = []
for value in scorecard["OnTimePct"]:
    if value >= 85:
        bar_colors.append("#2e7d32")   # green = good
    else:
        bar_colors.append("#c62828")   # red = below target

figure, axis = plt.subplots(figsize=(8, 4.5))
axis.barh(scorecard.index, scorecard["OnTimePct"], color=bar_colors)
axis.axvline(85, linestyle="--", color="gray")
axis.set_title("Supplier On-Time Delivery %  (red = below 85% target)")
axis.set_xlabel("On-Time %")
figure.tight_layout()
figure.savefig(CHARTS / "01_supplier_ontime.png", dpi=120)

# Chart 2: on-time by quarter (shows the Q4 dip)
po_with_dates = purchase_orders.merge(dates, left_on="OrderDate", right_on="Date")
by_quarter = po_with_dates.groupby(["Year", "Quarter"])["OnTimeFlag"].mean() * 100
by_quarter = by_quarter.round(1)

figure, axis = plt.subplots(figsize=(8, 4))
by_quarter.plot(kind="line", marker="o", ax=axis, color="#1565c0")
axis.set_title("Inbound On-Time % by Quarter  (Q4 peak-season dip)")
axis.set_ylabel("On-Time %")
axis.set_xlabel("Year, Quarter")
figure.tight_layout()
figure.savefig(CHARTS / "02_ontime_by_quarter.png", dpi=120)

# Chart 3: inventory turnover by family
figure, axis = plt.subplots(figsize=(8, 4))
family["Turnover"].plot(kind="bar", ax=axis, color="#6a1b9a")
axis.set_title("Inventory Turnover by Family  (Fasteners = stockout risk)")
axis.set_ylabel("Turnover ratio")
plt.xticks(rotation=30, ha="right")
figure.tight_layout()
figure.savefig(CHARTS / "03_turnover_by_family.png", dpi=120)

# Chart 4: carrier cost vs service (scatter)
figure, axis = plt.subplots(figsize=(7, 5))
axis.scatter(carrier["FreightPerUnit"], carrier["OnTimePct"], s=140, color="#ef6c00")
for carrier_name in carrier.index:
    x = carrier.loc[carrier_name, "FreightPerUnit"]
    y = carrier.loc[carrier_name, "OnTimePct"]
    axis.annotate(carrier_name, (x, y), xytext=(6, 6), textcoords="offset points")
axis.set_title("Carrier: Cost vs Service")
axis.set_xlabel("Freight $ / unit")
axis.set_ylabel("On-Time %")
figure.tight_layout()
figure.savefig(CHARTS / "04_carrier_tradeoff.png", dpi=120)

print("\n" + "=" * 60)
print(" CHARTS SAVED to charts/")
print("=" * 60)
for chart_file in sorted(CHARTS.glob("*.png")):
    print(f"  {chart_file.name}")
