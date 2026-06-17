"""
Supply Chain Analytics — synthetic data generator
==================================================

NOTE FOR READERS / INTERVIEWS
-----------------------------
This file just *creates the fake sample data* so the project has something to
analyze. It is a behind-the-scenes utility — the real analysis work is in
`analysis.sql` (SQL) and `analysis.py` (Python). You do not need to understand
every line here; in an interview, the one-sentence summary is:

    "I generated a realistic, seeded sample dataset so the analysis is
     reproducible, with a few operational problems built in on purpose
     (unreliable suppliers, a Q4 slowdown, an under-stocked product line)."

Creates a small star-schema dataset (dimensions + facts) for a fictional
consumer-goods company, "Northbound Supply Co.", operating 4 regional
distribution centers.

Design goals
------------
* Pure Python standard library only (csv, random, datetime) — runs anywhere,
  no pip install needed.
* SEEDED so the data is identical on every run (reproducible portfolio).
* Realistic, *discoverable* patterns are baked in on purpose so the analysis
  has a story to tell:
    - Suppliers differ in reliability  -> on-time-delivery (OTD) varies a lot.
    - Q4 (Nov/Dec) demand spike        -> more late inbound POs + stockouts.
    - One product family is chronically under-stocked -> stockout hot-spot.
    - Faster carriers cost more         -> cost-vs-service trade-off.

Run:
    python3 generate_data.py
Output: ./data/*.csv
"""

import csv
import random
from datetime import date, timedelta
from pathlib import Path

SEED = 42
random.seed(SEED)

OUT = Path(__file__).parent / "data"
OUT.mkdir(exist_ok=True)

START = date(2024, 1, 1)
END = date(2025, 12, 31)


def write_csv(name, header, rows):
    path = OUT / name
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print(f"  wrote {name:32s} ({len(rows):>5} rows)")


# ── dim_date ───────────────────────────────────────────────────────────────
def build_dim_date():
    rows = []
    d = START
    while d <= END:
        rows.append([
            int(d.strftime("%Y%m%d")),          # DateKey
            d.isoformat(),                        # Date
            d.year,                               # Year
            (d.month - 1) // 3 + 1,               # Quarter
            d.month,                              # Month
            d.strftime("%B"),                     # MonthName
            d.isocalendar()[1],                   # WeekOfYear
            d.strftime("%A"),                     # DayName
            1 if d.weekday() >= 5 else 0,         # IsWeekend
            1 if d.month in (11, 12) else 0,      # IsPeakSeason
        ])
        d += timedelta(days=1)
    write_csv("dim_date.csv",
              ["DateKey", "Date", "Year", "Quarter", "Month", "MonthName",
               "WeekOfYear", "DayName", "IsWeekend", "IsPeakSeason"],
              rows)


# ── dim_supplier ────────────────────────────────────────────────────────────
# reliability  = baseline probability a PO arrives on/before promised date
# avg_lead     = promised lead time in days
# defect_rate  = fraction of received units rejected for quality
SUPPLIERS = [
    # id, name,                country,    reliability, avg_lead, defect_rate
    [1, "Atlas Components",     "USA",        0.96,       7,        0.010],
    [2, "Brightline Mfg",       "USA",        0.94,      10,        0.015],
    [3, "Cathay Parts Ltd",     "China",      0.78,      32,        0.030],
    [4, "Delta Industrial",     "Mexico",     0.88,      14,        0.020],
    [5, "Eastgate Trading",     "Vietnam",    0.71,      35,        0.045],
    [6, "Forge & Co",           "USA",        0.92,       9,        0.012],
    [7, "Global Linkage",       "India",      0.74,      28,        0.038],
    [8, "Harbor Supply",        "Canada",     0.90,      12,        0.018],
]


def build_dim_supplier():
    rows = [[s[0], s[1], s[2], round(s[3], 2), s[4], s[5]] for s in SUPPLIERS]
    write_csv("dim_supplier.csv",
              ["SupplierID", "SupplierName", "Country",
               "ReliabilityScore", "PromisedLeadDays", "DefectRate"],
              rows)


# ── dim_product ─────────────────────────────────────────────────────────────
# Family "Fasteners" is intentionally the high-velocity / stockout-prone line.
PRODUCTS = [
    # id, name,               family,        unit_cost, unit_price, primary_supplier
    [101, "Hex Bolt M6",      "Fasteners",      0.40,    1.20,   1],
    [102, "Hex Bolt M8",      "Fasteners",      0.55,    1.60,   1],
    [103, "Wood Screw 2in",   "Fasteners",      0.20,    0.75,   6],
    [104, "Lock Washer",      "Fasteners",      0.10,    0.45,   6],
    [105, "Steel Bracket L",  "Brackets",       2.10,    6.50,   2],
    [106, "Steel Bracket XL", "Brackets",       3.40,    9.90,   2],
    [107, "Corner Brace",     "Brackets",       1.20,    3.80,   4],
    [108, "Hinge 3in",        "Hardware",       1.80,    5.40,   3],
    [109, "Drawer Slide",     "Hardware",       4.50,   12.00,   3],
    [110, "Cabinet Handle",   "Hardware",       2.75,    8.25,   8],
    [111, "Caster Wheel 2in", "Wheels",         3.10,    9.50,   5],
    [112, "Caster Wheel 4in", "Wheels",         5.60,   15.75,   5],
    [113, "Rubber Gasket",    "Seals",          0.85,    2.95,   7],
    [114, "O-Ring Kit",       "Seals",          1.40,    4.60,   7],
    [115, "Adhesive Tube",    "Consumables",    2.30,    6.99,   4],
]


def build_dim_product():
    rows = [[p[0], p[1], p[2], p[3], p[4],
             round((p[4] - p[3]) / p[4], 3), p[5]] for p in PRODUCTS]
    write_csv("dim_product.csv",
              ["ProductID", "ProductName", "Family",
               "UnitCost", "UnitPrice", "GrossMarginPct", "PrimarySupplierID"],
              rows)


# ── dim_warehouse ───────────────────────────────────────────────────────────
WAREHOUSES = [
    [1, "DC-East",    "Edison, NJ",      "Northeast"],
    [2, "DC-South",   "Dallas, TX",      "South"],
    [3, "DC-West",    "Ontario, CA",     "West"],
    [4, "DC-Central", "Joliet, IL",      "Midwest"],
]


def build_dim_warehouse():
    write_csv("dim_warehouse.csv",
              ["WarehouseID", "WarehouseName", "Location", "Region"],
              WAREHOUSES)


# ── fact_purchase_orders (INBOUND) ──────────────────────────────────────────
def build_fact_purchase_orders():
    sup = {s[0]: s for s in SUPPLIERS}
    rows = []
    po_id = 5000
    d = START
    while d <= END:
        # ~1 PO/day on average, more during peak season
        peak = d.month in (10, 11, 12)
        daily = 1 + (1 if peak else 0)
        for _ in range(daily):
            if random.random() > 0.65:        # not every "slot" creates a PO
                continue
            product = random.choice(PRODUCTS)
            supplier_id = product[5]
            s = sup[supplier_id]
            reliability, lead, defect = s[3], s[4], s[5]

            qty = random.choice([500, 750, 1000, 1500, 2000, 2500])
            unit_cost = round(product[3] * random.uniform(0.97, 1.06), 3)
            promised = d + timedelta(days=lead)

            # Lateness: peak season erodes reliability; unreliable suppliers slip more
            eff_reliability = reliability - (0.10 if peak else 0.0)
            if random.random() <= eff_reliability:
                slip = random.randint(-3, 0)          # on time or early
            else:
                slip = random.randint(1, max(4, lead // 3))  # genuinely late
            actual = promised + timedelta(days=slip)

            qty_received = qty
            # occasional short shipment
            if random.random() < 0.07:
                qty_received = int(qty * random.uniform(0.80, 0.97))
            # Quality is a per-PO event: most POs are clean; a defect batch shows
            # up roughly defect_rate-often, and only then carries rejected units.
            if random.random() < defect * 6:
                qty_rejected = int(qty_received * defect * random.uniform(0.5, 2.0))
            else:
                qty_rejected = 0

            freight = round(qty * unit_cost * random.uniform(0.04, 0.09), 2)
            po_id += 1
            rows.append([
                po_id, supplier_id, product[0], 1 + (po_id % 4),  # round-robin WH
                d.isoformat(), promised.isoformat(), actual.isoformat(),
                qty, qty_received, qty_rejected, unit_cost, freight,
                1 if actual <= promised else 0,        # OnTimeFlag
                (actual - promised).days,              # DaysLate (neg = early)
            ])
        d += timedelta(days=1)
    write_csv("fact_purchase_orders.csv",
              ["POID", "SupplierID", "ProductID", "WarehouseID",
               "OrderDate", "PromisedDate", "ActualReceiptDate",
               "QtyOrdered", "QtyReceived", "QtyRejected",
               "UnitCost", "FreightCost", "OnTimeFlag", "DaysLate"],
              rows)
    return rows


# ── fact_shipments (OUTBOUND to customers) ──────────────────────────────────
CARRIERS = [
    # name,        speed_days, on_time_base, cost_mult
    ["GroundCo",      4,          0.90,        1.00],
    ["RegionalX",     3,          0.93,        1.25],
    ["AirFast",       1,          0.97,        2.10],
]


def build_fact_shipments():
    rows = []
    ship_id = 80000
    d = START
    while d <= END:
        peak = d.month in (11, 12)
        daily = random.randint(3, 6) + (3 if peak else 0)
        for _ in range(daily):
            product = random.choice(PRODUCTS)
            wh = random.randint(1, 4)
            carrier = random.choices(CARRIERS, weights=[5, 3, 1])[0]
            qty = random.choice([10, 20, 25, 40, 50, 75, 100])

            requested = d + timedelta(days=carrier[1] + random.randint(0, 2))
            on_time_prob = carrier[2] - (0.08 if peak else 0.0)
            if random.random() <= on_time_prob:
                delivered = d + timedelta(days=carrier[1] + random.randint(-1, 1))
            else:
                delivered = requested + timedelta(days=random.randint(1, 5))
            delivered = max(delivered, d + timedelta(days=1))

            revenue = round(qty * product[4], 2)
            freight = round(qty * product[3] * 0.10 * carrier[3]
                            * random.uniform(0.8, 1.3), 2)
            ship_id += 1
            rows.append([
                ship_id, product[0], wh, carrier[0],
                d.isoformat(), requested.isoformat(), delivered.isoformat(),
                qty, revenue, freight,
                1 if delivered <= requested else 0,    # OnTimeFlag
                (delivered - d).days,                  # TransitDays
            ])
        d += timedelta(days=1)
    write_csv("fact_shipments.csv",
              ["ShipmentID", "ProductID", "WarehouseID", "Carrier",
               "ShipDate", "RequestedDate", "DeliveredDate",
               "Qty", "Revenue", "FreightCost", "OnTimeFlag", "TransitDays"],
              rows)


# ── fact_inventory_snapshot (month-end on-hand per WH x Product) ─────────────
def build_fact_inventory():
    rows = []
    # month-end dates across the window
    months = []
    y, m = START.year, START.month
    while (y, m) <= (END.year, END.month):
        # last day of month
        first_next = date(y + (m // 12), (m % 12) + 1, 1)
        months.append(first_next - timedelta(days=1))
        y, m = (y + (m // 12), (m % 12) + 1)

    for snap in months:
        peak = snap.month in (11, 12)
        for p in PRODUCTS:
            for wh in range(1, 5):
                # Fasteners family is high-velocity & under-stocked
                if p[2] == "Fasteners":
                    reorder = 800
                    base = random.randint(200, 1400)
                else:
                    reorder = 300
                    base = random.randint(350, 2000)
                # peak season draws stock down
                on_hand = int(base * (0.55 if peak else 1.0))
                on_hand = max(0, on_hand)
                in_transit = random.choice([0, 0, 500, 1000])
                # monthly units sold (drives turnover) ~ correlated to velocity
                vel = 900 if p[2] == "Fasteners" else 350
                units_sold = int(vel * random.uniform(0.6, 1.4)
                                 * (1.6 if peak else 1.0))
                rows.append([
                    int(snap.strftime("%Y%m%d")), wh, p[0],
                    on_hand, reorder, in_transit, units_sold,
                    1 if on_hand < reorder else 0,        # BelowReorderFlag
                    1 if on_hand == 0 else 0,             # StockoutFlag
                    round(on_hand * p[3], 2),             # InventoryValue (at cost)
                ])
    write_csv("fact_inventory_snapshot.csv",
              ["DateKey", "WarehouseID", "ProductID",
               "OnHandQty", "ReorderPoint", "InTransitQty", "UnitsSoldMonth",
               "BelowReorderFlag", "StockoutFlag", "InventoryValue"],
              rows)


if __name__ == "__main__":
    print(f"Generating supply-chain data (seed={SEED}) -> {OUT}")
    build_dim_date()
    build_dim_supplier()
    build_dim_product()
    build_dim_warehouse()
    build_fact_purchase_orders()
    build_fact_shipments()
    build_fact_inventory()
    print("Done. Star schema: 4 dimensions + 3 fact tables.")
