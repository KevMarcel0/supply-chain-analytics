-- ============================================================================
-- Supply Chain Analytics — load star schema into SQLite
-- Run from the supply-chain/ folder:
--     sqlite3 supplychain.db < load_sqlite.sql
-- ============================================================================

.mode csv
.headers on

DROP TABLE IF EXISTS dim_date;
DROP TABLE IF EXISTS dim_supplier;
DROP TABLE IF EXISTS dim_product;
DROP TABLE IF EXISTS dim_warehouse;
DROP TABLE IF EXISTS fact_purchase_orders;
DROP TABLE IF EXISTS fact_shipments;
DROP TABLE IF EXISTS fact_inventory_snapshot;

-- ── dimensions ──────────────────────────────────────────────────────────────
CREATE TABLE dim_date (
    DateKey INTEGER PRIMARY KEY, Date TEXT, Year INTEGER, Quarter INTEGER,
    Month INTEGER, MonthName TEXT, WeekOfYear INTEGER, DayName TEXT,
    IsWeekend INTEGER, IsPeakSeason INTEGER
);
CREATE TABLE dim_supplier (
    SupplierID INTEGER PRIMARY KEY, SupplierName TEXT, Country TEXT,
    ReliabilityScore REAL, PromisedLeadDays INTEGER, DefectRate REAL
);
CREATE TABLE dim_product (
    ProductID INTEGER PRIMARY KEY, ProductName TEXT, Family TEXT,
    UnitCost REAL, UnitPrice REAL, GrossMarginPct REAL, PrimarySupplierID INTEGER
);
CREATE TABLE dim_warehouse (
    WarehouseID INTEGER PRIMARY KEY, WarehouseName TEXT, Location TEXT, Region TEXT
);

-- ── facts ───────────────────────────────────────────────────────────────────
CREATE TABLE fact_purchase_orders (
    POID INTEGER PRIMARY KEY, SupplierID INTEGER, ProductID INTEGER,
    WarehouseID INTEGER, OrderDate TEXT, PromisedDate TEXT, ActualReceiptDate TEXT,
    QtyOrdered INTEGER, QtyReceived INTEGER, QtyRejected INTEGER,
    UnitCost REAL, FreightCost REAL, OnTimeFlag INTEGER, DaysLate INTEGER
);
CREATE TABLE fact_shipments (
    ShipmentID INTEGER PRIMARY KEY, ProductID INTEGER, WarehouseID INTEGER,
    Carrier TEXT, ShipDate TEXT, RequestedDate TEXT, DeliveredDate TEXT,
    Qty INTEGER, Revenue REAL, FreightCost REAL, OnTimeFlag INTEGER, TransitDays INTEGER
);
CREATE TABLE fact_inventory_snapshot (
    DateKey INTEGER, WarehouseID INTEGER, ProductID INTEGER,
    OnHandQty INTEGER, ReorderPoint INTEGER, InTransitQty INTEGER,
    UnitsSoldMonth INTEGER, BelowReorderFlag INTEGER, StockoutFlag INTEGER,
    InventoryValue REAL
);

-- ── import CSVs (skip the header row each file) ──────────────────────────────
.import --skip 1 data/dim_date.csv dim_date
.import --skip 1 data/dim_supplier.csv dim_supplier
.import --skip 1 data/dim_product.csv dim_product
.import --skip 1 data/dim_warehouse.csv dim_warehouse
.import --skip 1 data/fact_purchase_orders.csv fact_purchase_orders
.import --skip 1 data/fact_shipments.csv fact_shipments
.import --skip 1 data/fact_inventory_snapshot.csv fact_inventory_snapshot

CREATE INDEX idx_po_supplier ON fact_purchase_orders(SupplierID);
CREATE INDEX idx_po_product  ON fact_purchase_orders(ProductID);
CREATE INDEX idx_ship_product ON fact_shipments(ProductID);
CREATE INDEX idx_inv_product ON fact_inventory_snapshot(ProductID);

SELECT 'dim_date'        AS tbl, COUNT(*) AS rows FROM dim_date
UNION ALL SELECT 'dim_supplier', COUNT(*) FROM dim_supplier
UNION ALL SELECT 'dim_product',  COUNT(*) FROM dim_product
UNION ALL SELECT 'dim_warehouse',COUNT(*) FROM dim_warehouse
UNION ALL SELECT 'fact_purchase_orders', COUNT(*) FROM fact_purchase_orders
UNION ALL SELECT 'fact_shipments',       COUNT(*) FROM fact_shipments
UNION ALL SELECT 'fact_inventory_snapshot', COUNT(*) FROM fact_inventory_snapshot;
