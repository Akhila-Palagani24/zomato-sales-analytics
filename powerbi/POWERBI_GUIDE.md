# Power BI Dashboard Guide

Power BI Desktop files (.pbix) can't be generated outside Power BI itself, so this
folder gives you the ready-to-import data plus the exact build steps and DAX
measures to recreate the dashboard in ~20 minutes.

## 1. Import the data
- Open Power BI Desktop → Get Data → Excel → select `zomato_sales_data_for_powerbi.xlsx`
- Load the `Orders` table

## 2. (Optional but recommended) Build a star schema
Splitting into fact + dimension tables is a common interview talking point:
- **Dim_City**: unique `city`, `region`
- **Dim_Category**: unique `food_category`
- **Dim_Date**: one row per date, with `month`, `year`, `weekday`, `is_weekend`
- **Fact_Orders**: `order_id`, `order_date`, `city`, `food_category`, `net_revenue`, `order_value`, `quantity`, etc.

In Power Query (Transform Data), use "Reference" to spin off each dimension table
from Orders, then remove duplicates and unneeded columns.

## 3. Create relationships
Model view → drag from `Fact_Orders` foreign keys to the dimension table primary keys
(1-to-many, single direction).

## 4. Key DAX measures
```DAX
Total Revenue = SUM(Fact_Orders[net_revenue])

Total Orders = COUNTROWS(Fact_Orders)

Avg Order Value = AVERAGE(Fact_Orders[order_value])

Revenue LY =
CALCULATE([Total Revenue], SAMEPERIODLASTYEAR(Dim_Date[date]))

YoY Growth % =
DIVIDE([Total Revenue] - [Revenue LY], [Revenue LY])

Weekend Revenue % =
DIVIDE(
    CALCULATE([Total Revenue], Fact_Orders[is_weekend] = TRUE),
    [Total Revenue]
)

Discount Impact =
CALCULATE([Total Revenue], Fact_Orders[discount_pct] > 0)
    / [Total Revenue]
```

## 5. Suggested pages
1. **Overview** — KPI cards (Total Revenue, Total Orders, Avg Order Value, YoY Growth),
   monthly revenue line chart, revenue by region map/bar
2. **City & Region Drilldown** — bar chart of revenue by city, drillthrough to category mix per city
3. **Category Performance** — revenue and order count by food category, avg rating by category
4. **Customer Behavior** — new vs returning customer split, payment mode breakdown, weekday vs weekend orders
5. **Forecast** — line chart combining historical weekly revenue with the 8-week
   forecast from `data/processed/revenue_forecast_next_8_weeks.csv` (import as a
   second table and union/append for a single combined visual)

## 6. Slicers to add
`year`, `region`, `food_category`, `is_weekend` — placed on every page for consistent filtering.

## 7. Interview talking point
Be ready to explain: **measures vs calculated columns** — measures (like the DAX
above) compute at query time and respond to filters/slicers; calculated columns
are computed once at refresh and stored in the table. Use measures for anything
that should change with user selections (which is most KPIs).
