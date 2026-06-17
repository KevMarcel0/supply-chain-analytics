"""
Prepare a Power BI-ready file from the real DataCo dataset
==========================================================
Power BI loads CSVs best when the data is already cleaned: friendly column
names, useful derived columns, and no junk/PII columns. This script does that.

Run (after download_data.py):
    .venv/bin/python powerbi/prep_powerbi_data.py
Output: powerbi/powerbi_dataco.csv   (load THIS into Power BI Desktop)
"""

from pathlib import Path
import pandas as pd

HERE = Path(__file__).parent
RAW = HERE.parent / "realdata" / "DataCoSupplyChainDataset.csv"
OUT = HERE / "powerbi_dataco.csv"

df = pd.read_csv(RAW, encoding="latin-1", low_memory=False)

# Keep only the columns useful for the dashboard (drop fake PII + clutter).
keep = {
    "Order Id": "OrderID",
    "order date (DateOrders)": "OrderDate",
    "Type": "PaymentType",
    "Shipping Mode": "ShippingMode",
    "Delivery Status": "DeliveryStatus",
    "Late_delivery_risk": "IsLate",
    "Days for shipping (real)": "ActualDays",
    "Days for shipment (scheduled)": "ScheduledDays",
    "Category Name": "Category",
    "Department Name": "Department",
    "Market": "Market",
    "Order Region": "Region",
    "Order Country": "Country",
    "Customer Segment": "CustomerSegment",
    "Order Item Quantity": "Quantity",
    "Sales": "Sales",
    "Order Profit Per Order": "Profit",
    "Product Name": "Product",
    "Product Price": "ProductPrice",
}
df = df[list(keep)].rename(columns=keep)

# Parse the date and add columns Power BI likes for time-based visuals.
df["OrderDate"] = pd.to_datetime(df["OrderDate"])
df["OrderYear"] = df["OrderDate"].dt.year
df["OrderMonth"] = df["OrderDate"].dt.month
df["OrderYearMonth"] = df["OrderDate"].dt.strftime("%Y-%m")

# Days delivered past the promised window (negative = early).
df["DaysOverSchedule"] = df["ActualDays"] - df["ScheduledDays"]

df.to_csv(OUT, index=False)
print(f"Wrote {OUT.name}: {len(df):,} rows, {len(df.columns)} columns "
      f"({OUT.stat().st_size/1e6:.1f} MB)")
print("Columns:", ", ".join(df.columns))
