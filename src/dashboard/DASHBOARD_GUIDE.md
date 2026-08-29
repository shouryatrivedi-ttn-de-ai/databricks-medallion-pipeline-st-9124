# Databricks SQL Dashboard Guide

This guide documents the deployed **four-tile** Databricks SQL Dashboard built from Gold-layer tables using the queries in `dashboard_queries.sql`.

## Submission gate (required)

Dashboard work is **not complete** until you have done the following in Databricks:

1. Created and published a SQL dashboard with **all four visualizations** listed below.
2. Created and wired **at least one working dashboard filter** linked to a query parameter (assignment requires filters).
3. Verified that changing a filter **updates at least one visualization tile**.

The repo provides SQL and instructions only; the live dashboard must be built and verified in the Databricks UI.

---

## Deployed dashboard overview

| Tile | Visualization | Chart type | SQL section | Gold table |
|------|---------------|------------|-------------|------------|
| Customer Distribution by Segment | Pie / Donut | QUERY 1 | `customer_segmentation` |
| Total Revenue by Customer Segment | Bar | QUERY 2 | `customer_segmentation` |
| Top 10 Customers by Revenue | Bar | QUERY 3 | `revenue_by_customer` |
| Total Revenue by Product Category | Bar | QUERY 4 | `sales_by_product` |

---

## Prerequisites

Before creating the dashboard, confirm:

1. **Bronze, Silver, and Gold pipelines have run successfully** on Databricks.
2. **Gold tables exist** and contain data:

   | Table | Full name |
   |-------|-----------|
   | Sales by product | `workspace.gold.sales_by_product` |
   | Revenue by customer | `workspace.gold.revenue_by_customer` |
   | Customer segmentation | `workspace.gold.customer_segmentation` |

3. Quick verification in Databricks SQL:

   ```sql
   SELECT COUNT(*) FROM workspace.gold.sales_by_product;
   SELECT COUNT(*) FROM workspace.gold.revenue_by_customer;
   SELECT COUNT(*) FROM workspace.gold.customer_segmentation;
   ```

   Each count should be greater than zero.

4. **A running SQL warehouse or SQL-capable compute** is available in your workspace (Databricks Community Edition or other).

5. **UI note:** Exact menu labels for queries, dashboards, filters, and parameters may vary by Databricks workspace version. Look for equivalent options such as **Queries**, **Dashboards**, **Add filter**, and **Query parameters**.

---

## Gold table reference (actual columns)

Use only these columns - they match the Gold SQL aggregations.

### `workspace.gold.customer_segmentation`

| Column | Use in dashboard |
|--------|------------------|
| `segment_type` | Pie label (QUERY 1); bar category (QUERY 2) |
| `customer_count` | Pie value (QUERY 1) |
| `total_revenue` | Bar value (QUERY 2) |
| `avg_revenue` | n/a |

**Expected `segment_type` values:** `High-Value`, `Repeat`, `One-Time`, `Inactive`

### `workspace.gold.revenue_by_customer`

| Column | Use in dashboard |
|--------|------------------|
| `customer_name` | Bar category (QUERY 3) |
| `customer_segment` | Filter dimension - Premium / Standard / Basic (QUERY 3) |
| `total_revenue` | Bar value (QUERY 3) |
| `customer_id` | n/a |
| `total_orders`, `avg_order_value`, `lifetime_value_actual` | n/a |

### `workspace.gold.sales_by_product`

| Column | Use in dashboard |
|--------|------------------|
| `category` | Bar category (QUERY 4); filter dimension |
| `total_revenue` | Aggregated bar value (QUERY 4) |
| `product_id`, `product_name` | n/a |
| `total_orders`, `avg_order_value` | n/a |

---

## Query and parameter map

Each dashboard tile uses **one saved query** from `dashboard_queries.sql`.

| Saved query name | SQL section | Parameters (default) | Visualization |
|------------------|-------------|----------------------|---------------|
| `Customer Distribution by Segment` | QUERY 1 | none | Pie / donut |
| `Total Revenue by Customer Segment` | QUERY 2 | none | Bar |
| `Top 10 Customers by Revenue` | QUERY 3 | `customer_segment` = `All` | Bar |
| `Total Revenue by Product Category` | QUERY 4 | `product_category` = `All` | Bar |
| `Filter - Customer Segments` | FILTER SUPPORT (segments) | n/a | Filter value source for QUERY 3 |
| `Filter - Product Categories` | FILTER SUPPORT (categories) | n/a | Filter value source for QUERY 4 |

**Parameter safety:** QUERY 3 and QUERY 4 treat `All` or empty string as "no filter" so unset defaults do not return zero rows.

---

## Step 1 - Create saved queries and define parameters

Open **Databricks SQL** -> **Queries** -> **Create query**.

### Customer Distribution by Segment (QUERY 1)

1. Paste QUERY 1 from `dashboard_queries.sql`.
2. No parameters required.
3. Run and confirm rows return for each `segment_type`.
4. Save as `Customer Distribution by Segment`.

### Total Revenue by Customer Segment (QUERY 2)

1. Paste QUERY 2 from `dashboard_queries.sql`.
2. No parameters required.
3. Run and confirm one row per `segment_type` with `total_revenue`.
4. Save as `Total Revenue by Customer Segment`.

### Top 10 Customers by Revenue (QUERY 3)

1. Paste QUERY 3 from `dashboard_queries.sql`.
2. Add a **query parameter**:
   - Name: `customer_segment`
   - Type: text (or string)
   - Default value: `All`
3. Run and confirm up to 10 rows with default `All`.
4. Save as `Top 10 Customers by Revenue`.

### Total Revenue by Product Category (QUERY 4)

1. Paste QUERY 4 from `dashboard_queries.sql`.
2. Add a **query parameter**:
   - Name: `product_category`
   - Type: text (or string)
   - Default value: `All`
3. Run and confirm one row per `category` with default `All`.
4. Save as `Total Revenue by Product Category`.

### Filter support queries (for filter wiring)

1. Save FILTER SUPPORT (segments) as `Filter - Customer Segments`.
2. Save FILTER SUPPORT (categories) as `Filter - Product Categories`.

Both include `All` as the first value for safe defaults.

---

## Step 2 - Configure visualizations

For each saved query, open the **Visualization** tab.

### Tile 1 - Customer Distribution by Segment (Pie / Donut)

**Saved query:** `Customer Distribution by Segment` (QUERY 1)

| Setting | Value |
|---------|-------|
| Visualization type | **Pie** or **Donut** |
| Label / Category | `segment_type` |
| Value | `customer_count` |
| Aggregation | Sum (one row per segment already) |

**Expected columns:** `segment_type`, `customer_count`

---

### Tile 2 - Total Revenue by Customer Segment (Bar)

**Saved query:** `Total Revenue by Customer Segment` (QUERY 2)

| Setting | Value |
|---------|-------|
| Visualization type | **Bar** |
| X-axis / Category | `segment_type` |
| Y-axis / Value | `total_revenue` |
| Aggregation | None (one row per segment already) |

**Expected columns:** `segment_type`, `total_revenue`

---

### Tile 3 - Top 10 Customers by Revenue (Bar)

**Saved query:** `Top 10 Customers by Revenue` (QUERY 3)

| Setting | Value |
|---------|-------|
| Visualization type | **Bar** |
| X-axis / Category | `customer_name` |
| Y-axis / Value | `total_revenue` |
| Aggregation | None (query already limits to 10 rows) |

**Expected columns:** `customer_name`, `total_revenue`

---

### Tile 4 - Total Revenue by Product Category (Bar)

**Saved query:** `Total Revenue by Product Category` (QUERY 4)

| Setting | Value |
|---------|-------|
| Visualization type | **Bar** |
| X-axis / Category | `category` |
| Y-axis / Value | `total_revenue` |
| Aggregation | None (query already aggregates with `SUM`) |

**Expected columns:** `category`, `total_revenue`

---

## Step 3 - Create the dashboard

1. Go to **Databricks SQL** -> **Dashboards** -> **Create dashboard**.
2. Name it (e.g. `E-commerce Medallion Analytics`).
3. Click **Add** -> **Visualization**.
4. Add each tile from its saved query:
   - Customer Distribution by Segment -> Pie/Donut (QUERY 1)
   - Total Revenue by Customer Segment -> Bar (QUERY 2)
   - Top 10 Customers by Revenue -> Bar (QUERY 3)
   - Total Revenue by Product Category -> Bar (QUERY 4)
5. Arrange all four tiles on the canvas.
6. Save or publish the dashboard.

---

## Step 4 - Required filters (assignment: "add filters")

Filters are **required** by `docs/assignment.md`.

Two optional filter dimensions are supported by the Gold schema without modifying Gold tables:

| Filter | Gold column | Filter values query | Parameter on tile query | Tile updated |
|--------|-------------|---------------------|-------------------------|--------------|
| Customer segment | `revenue_by_customer.customer_segment` | `Filter - Customer Segments` | `customer_segment` on QUERY 3 | Top 10 Customers by Revenue |
| Product category | `sales_by_product.category` | `Filter - Product Categories` | `product_category` on QUERY 4 | Total Revenue by Product Category |

QUERY 1 and QUERY 2 do not use filters (they already show all behavioral segments from `customer_segmentation`).

### Wiring filters to query parameters

Exact UI labels vary by workspace version. General flow:

1. On the dashboard, add a **filter** (or **Add filter** / **Dashboard filter**).
2. Choose a filter backed by a query or value list when available.
3. Select the filter support query (e.g. `Filter - Customer Segments`).
4. **Link the filter to the query parameter** on the target saved query:
   - Filter -> `customer_segment` -> QUERY 3 parameter `customer_segment`
   - Filter -> `product_category` -> QUERY 4 parameter `product_category`
5. Set default filter value to **All** so all rows show on first load.
6. Confirm parameter names in SQL match exactly: `{{customer_segment}}` and `{{product_category}}`.

**Important:** Parameters must be defined on the **saved query** that powers the visualization, then connected to the dashboard filter where your workspace supports that linkage.

---

## Step 5 - Verify the dashboard

### Query-level checks

```sql
-- QUERY 1: segment distribution
SELECT segment_type, customer_count
FROM workspace.gold.customer_segmentation
ORDER BY customer_count DESC;

-- QUERY 2: revenue by behavioral segment
SELECT segment_type, total_revenue
FROM workspace.gold.customer_segmentation
ORDER BY total_revenue DESC;

-- QUERY 3: top 10 customers
SELECT customer_name, total_revenue
FROM workspace.gold.revenue_by_customer
ORDER BY total_revenue DESC
LIMIT 10;

-- QUERY 4: revenue by product category
SELECT category, SUM(total_revenue) AS total_revenue
FROM workspace.gold.sales_by_product
GROUP BY category
ORDER BY total_revenue DESC;
```

### Dashboard-level checklist (required)

- [ ] All **four** tiles render without errors.
- [ ] Pie/donut shows `segment_type` slices sized by `customer_count`.
- [ ] Bar chart shows `total_revenue` by `segment_type`.
- [ ] Bar chart shows up to 10 customers by `total_revenue`.
- [ ] Bar chart shows `total_revenue` by product `category`.
- [ ] **At least one dashboard filter is created and linked to a query parameter.**
- [ ] **Changing a filter updates at least one visualization tile** (e.g. customer segment changes the Top 10 list, or category filters the category revenue bars).
- [ ] Default filter value `All` shows data (not zero rows).
- [ ] Values align with direct SQL against Gold tables.

### Cross-check with Gold totals

```sql
SELECT SUM(total_revenue) FROM workspace.gold.sales_by_product;
SELECT SUM(total_revenue) FROM workspace.gold.revenue_by_customer;
SELECT SUM(total_revenue) FROM workspace.gold.customer_segmentation;
```

Customer-attributed revenue totals should be consistent between `revenue_by_customer` and `customer_segmentation` (Gold validation enforces this).

---

## What must be done manually in Databricks UI

The repository provides **SQL queries and this guide** only:

1. Creating saved queries in Databricks SQL.
2. Defining query parameters on QUERY 3 and QUERY 4 (`customer_segment`, `product_category`) with default `All`.
3. Selecting visualization types and field mappings for all four tiles.
4. Creating the dashboard and arranging four tiles.
5. Creating **required** dashboard filters and linking them to query parameters.
6. Publishing the dashboard and verifying filter behavior.

---

## Troubleshooting

| Issue | Likely cause | Action |
|-------|--------------|--------|
| Table not found | Gold not run | Execute `create_gold_tables.py` on Databricks |
| Empty visualization | Gold tables empty | Re-run Bronze -> Silver -> Gold |
| Zero rows after adding filter | Parameter not `All` and no match | Set default to `All`; confirm SQL uses `IN ('All', '')` |
| Pie chart empty | Wrong value column | Use `customer_count`, not `total_revenue` |
| Segment revenue bar empty | Wrong value column | Use `total_revenue`, not `customer_count` |
| Top 10 shows wrong customers | Wrong sort or limit | Confirm `ORDER BY total_revenue DESC LIMIT 10` |
| Category bar shows one row | Filter set to single category | Set filter to `All` or pick a category with multiple products |
| Filter does not apply | Parameter not linked | Define parameter on saved query; link dashboard filter to it |

---

## File reference

| File | Purpose |
|------|---------|
| `src/dashboard/dashboard_queries.sql` | QUERY 1-4 and filter support SQL |
| `src/gold/01_sales_by_product.sql` | Source aggregation for QUERY 4 |
| `src/gold/02_revenue_by_customer.sql` | Source aggregation for QUERY 3 |
| `src/gold/04_customer_segmentation.sql` | Source aggregation for QUERY 1 and QUERY 2 |
| `docs/assignment.md` | Assignment dashboard requirements |
| `README.md` | Project overview and dashboard summary |
