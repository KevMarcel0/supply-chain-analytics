-- ============================================================================
-- Supply Chain Analytics — KPI query pack
-- Run:  sqlite3 supplychain.db < analysis.sql
-- Each block answers one business question. Read the comment, run, interpret.
--
-- ONE PATTERN TO KNOW (used in almost every query below):
--   Columns like OnTimeFlag are 1 (yes) or 0 (no).
--   SUM of those flags = how many "yes". Divide by COUNT(*) = the percentage.
--   So:  100.0 * SUM(OnTimeFlag) / COUNT(*)  ==  "what % were on time".
--   Once that clicks, every query here reads the same way.
-- ============================================================================
.mode column
.headers on
.width 22 10 10 10 12

-- ────────────────────────────────────────────────────────────────────────────
-- Q1. SUPPLIER SCORECARD — who do we actually trust?
--     On-time delivery %, avg days late, fill rate, quality reject rate.
--     This is the headline table of any procurement review.
-- ────────────────────────────────────────────────────────────────────────────
SELECT
    s.SupplierName,
    s.Country,
    COUNT(*)                                            AS POs,
    ROUND(100.0 * SUM(po.OnTimeFlag) / COUNT(*), 1)     AS OnTimePct,
    ROUND(AVG(CASE WHEN po.DaysLate > 0 THEN po.DaysLate END), 1) AS AvgDaysLate_whenLate,
    ROUND(100.0 * SUM(po.QtyReceived) / SUM(po.QtyOrdered), 1)    AS FillRatePct,
    ROUND(100.0 * SUM(po.QtyRejected) / SUM(po.QtyReceived), 2)   AS RejectPct
FROM fact_purchase_orders po
JOIN dim_supplier s ON s.SupplierID = po.SupplierID
GROUP BY s.SupplierID
ORDER BY OnTimePct ASC;     -- worst performers first

.print ''
.print '== Q2: On-time delivery by quarter (does peak season hurt us?) =='
-- ────────────────────────────────────────────────────────────────────────────
-- Q2. SEASONALITY — inbound OTD by quarter. Expect Q4 to dip.
-- ────────────────────────────────────────────────────────────────────────────
SELECT
    d.Year, d.Quarter,
    COUNT(*)                                         AS POs,
    ROUND(100.0 * SUM(po.OnTimeFlag) / COUNT(*), 1)  AS OnTimePct
FROM fact_purchase_orders po
JOIN dim_date d ON d.Date = po.OrderDate
GROUP BY d.Year, d.Quarter
ORDER BY d.Year, d.Quarter;

.print ''
.print '== Q3: Perfect-order rate (on-time AND complete AND defect-free) =='
-- ────────────────────────────────────────────────────────────────────────────
-- Q3. PERFECT ORDER % — the gold-standard composite metric. A PO is "perfect"
--     only if it was on time, fully received, and had zero rejects.
-- ────────────────────────────────────────────────────────────────────────────
SELECT
    ROUND(100.0 * SUM(
        CASE WHEN po.OnTimeFlag = 1
              AND po.QtyReceived >= po.QtyOrdered
              AND po.QtyRejected = 0
             THEN 1 ELSE 0 END) / COUNT(*), 1)  AS PerfectOrderPct,
    COUNT(*)                                     AS TotalPOs
FROM fact_purchase_orders po;

.print ''
.print '== Q4: Inventory health — turnover & stockout risk by product family =='
.width 14 10 12 14 12
-- ────────────────────────────────────────────────────────────────────────────
-- Q4. INVENTORY TURNOVER & STOCKOUT RISK by family.
--     Turnover ~ annual units sold / avg on-hand. High turnover + low stock
--     = the family most likely to stock out. Expect "Fasteners" to flag.
-- ────────────────────────────────────────────────────────────────────────────
SELECT
    p.Family,
    ROUND(AVG(inv.OnHandQty), 0)                              AS AvgOnHand,
    SUM(inv.UnitsSoldMonth)                                   AS UnitsSold,
    ROUND(1.0 * SUM(inv.UnitsSoldMonth) / AVG(inv.OnHandQty), 1) AS TurnoverRatio,
    ROUND(100.0 * SUM(inv.BelowReorderFlag) / COUNT(*), 1)   AS PctBelowReorder
FROM fact_inventory_snapshot inv
JOIN dim_product p ON p.ProductID = inv.ProductID
GROUP BY p.Family
ORDER BY TurnoverRatio DESC;

.print ''
.print '== Q5: Carrier cost-vs-service trade-off (outbound) =='
.width 12 10 12 14 12
-- ────────────────────────────────────────────────────────────────────────────
-- Q5. CARRIER TRADE-OFF — faster carriers deliver on time more often but cost
--     more freight per unit. Quantify the trade so we can pick deliberately.
-- ────────────────────────────────────────────────────────────────────────────
SELECT
    sh.Carrier,
    COUNT(*)                                           AS Shipments,
    ROUND(100.0 * SUM(sh.OnTimeFlag) / COUNT(*), 1)    AS OnTimePct,
    ROUND(AVG(sh.TransitDays), 1)                      AS AvgTransitDays,
    ROUND(SUM(sh.FreightCost) / SUM(sh.Qty), 3)        AS FreightPerUnit
FROM fact_shipments sh
GROUP BY sh.Carrier
ORDER BY FreightPerUnit;

.print ''
.print '== Q6: Top 5 stockout-risk SKUs (most months below reorder point) =='
.width 18 10 12 12
-- ────────────────────────────────────────────────────────────────────────────
-- Q6. SKU WATCHLIST — which specific items spend the most time below their
--     reorder point? These are where expediting / safety-stock should go.
-- ────────────────────────────────────────────────────────────────────────────
SELECT
    p.ProductName,
    p.Family,
    COUNT(*)                                          AS Snapshots,
    ROUND(100.0 * SUM(inv.BelowReorderFlag) / COUNT(*), 1) AS PctBelowReorder
FROM fact_inventory_snapshot inv
JOIN dim_product p ON p.ProductID = inv.ProductID
GROUP BY inv.ProductID
ORDER BY PctBelowReorder DESC
LIMIT 5;

.print ''
.print '== Q7: Landed cost leakage — freight as % of goods cost, by supplier =='
.width 22 14 14 12
-- ────────────────────────────────────────────────────────────────────────────
-- Q7. LANDED COST — freight as a share of the goods value. High ratios are
--     candidates for consolidation / renegotiation.
-- ────────────────────────────────────────────────────────────────────────────
SELECT
    s.SupplierName,
    ROUND(SUM(po.QtyOrdered * po.UnitCost), 0)         AS GoodsCost,
    ROUND(SUM(po.FreightCost), 0)                      AS FreightCost,
    ROUND(100.0 * SUM(po.FreightCost)
              / SUM(po.QtyOrdered * po.UnitCost), 1)   AS FreightPctOfGoods
FROM fact_purchase_orders po
JOIN dim_supplier s ON s.SupplierID = po.SupplierID
GROUP BY s.SupplierID
ORDER BY FreightPctOfGoods DESC;
