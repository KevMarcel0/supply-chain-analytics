# 📊 Power BI Dashboard — Build Guide (DataCo Supply Chain)

A step-by-step guide to build a supply-chain dashboard in **Power BI Desktop**
from the real DataCo data. Takes ~20–30 minutes. The result recreates (and
goes beyond) the charts in this project, in an interactive dashboard.

> **Note:** Power BI Desktop is **Windows-only** and is free. On a Mac, use a
> Windows PC, Parallels/Boot Camp, or a school/library machine. The `.pbix`
> dashboard file can only be created inside Power BI Desktop — this guide gets
> you there fast.

---

## 0. Prepare the data (once)

```bash
python3 download_data.py                     # gets the raw dataset
.venv/bin/python powerbi/prep_powerbi_data.py   # makes powerbi/powerbi_dataco.csv
```

You'll load **`powerbi_dataco.csv`** (180,519 rows, cleaned, 23 columns) into Power BI.

---

## 1. Load the data

1. Open **Power BI Desktop** → **Home → Get Data → Text/CSV**.
2. Pick `powerbi_dataco.csv` → **Load**.
3. Check the data types in the **Data** view (left sidebar):
   - `OrderDate` → **Date**
   - `IsLate`, `Quantity`, `OrderYear`, `OrderMonth` → **Whole number**
   - `Sales`, `Profit`, `ActualDays`, `ScheduledDays`, `DaysOverSchedule`, `ProductPrice` → **Decimal number**
   - everything else → **Text**

---

## 2. Create the measures (DAX)

In the **Report** view: **Home → New measure**, paste each one (one measure at a
time). These are the heart of the dashboard.

```DAX
Total Orders = DISTINCTCOUNT(powerbi_dataco[OrderID])

Late Orders = SUM(powerbi_dataco[IsLate])

Late Rate % =
DIVIDE( [Late Orders], COUNTROWS(powerbi_dataco) )

On-Time Rate % = 1 - [Late Rate %]

Total Sales = SUM(powerbi_dataco[Sales])

Total Profit = SUM(powerbi_dataco[Profit])

Avg Days Over Schedule = AVERAGE(powerbi_dataco[DaysOverSchedule])

Avg Actual Days = AVERAGE(powerbi_dataco[ActualDays])

Avg Scheduled Days = AVERAGE(powerbi_dataco[ScheduledDays])
```

**Format the percentages:** click each `%` measure → **Measure tools →
Format → Percentage**, 1 decimal. Format `Total Sales`/`Total Profit` as
**Currency**.

---

## 3. Build the visuals

Drag these onto the canvas. Suggested layout: KPI cards across the top, then a
2×2 grid below.

### Row 1 — KPI cards (use the **Card** visual)
| Card | Field |
|---|---|
| Late Rate % | `Late Rate %` |
| Total Sales | `Total Sales` |
| Total Profit | `Total Profit` |
| Total Orders | `Total Orders` |

### Row 2 — the core charts
1. **Late Rate by Shipping Mode** — *Clustered bar chart*
   - Y axis: `ShippingMode` · X axis: `Late Rate %`
   - This is the headline: First Class ≈ 95% late.

2. **Promised vs Actual Days** — *Clustered column chart*
   - X axis: `ShippingMode` · Y values: `Avg Scheduled Days` **and** `Avg Actual Days`
   - Shows the root cause: actual exceeds promised on the fast tiers.

3. **Late Rate by Market** — *Clustered bar chart*
   - Y axis: `Market` · X axis: `Late Rate %` → ~55% everywhere (not regional).

4. **Sales by Department** — *Clustered bar chart*
   - Y axis: `Department` · X axis: `Total Sales` → Fan Shop dominates.

### Optional — trend
5. **Late Rate over time** — *Line chart*
   - X axis: `OrderYearMonth` (or `OrderYear`) · Y: `Late Rate %`.

---

## 4. Make it interactive (slicers)

Add **Slicer** visuals for: `Market`, `ShippingMode`, `OrderYear`,
`CustomerSegment`. Clicking any slicer filters every chart at once — this is
what makes it a *dashboard*, not just charts.

---

## 5. Polish (the part that impresses)

- **Conditional color** on the Late Rate bars: Format → Bars → Color →
  *fx* → Rules → red if `Late Rate %` ≥ 0.5, else green.
- **Title** the page: "DataCo Supply Chain — Delivery Performance".
- **Data labels** on: Format → Data labels → On.
- Add a **text box** with the headline insight:
  *"Premium shipping tiers (First/Second Class) miss their promised windows
  ~80–95% of the time. The issue is unrealistic delivery promises, not region."*

---

## 6. Save & showcase

- **File → Save** as `dataco_supply_chain.pbix`.
- **Export a PNG/PDF** (File → Export) to attach to job applications.
- *Optional:* **Publish** to the free [Power BI Service](https://app.powerbi.com)
  to get a shareable web link for your résumé.

---

## What to say about it in an interview

> "I built an interactive Power BI dashboard on 180,000 real supply-chain
> orders. I wrote DAX measures for late-delivery rate, on-time rate, and
> average days over schedule, then built KPI cards, bar charts, and slicers so
> you can filter by market, shipping mode, and year. The dashboard surfaces
> that premium shipping tiers miss their promised delivery windows ~80–95% of
> the time — a promise-setting problem, not a regional one."

That hits the three things Power BI roles want: **DAX**, **data modeling**, and
**turning data into a business story**.
