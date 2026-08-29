# Databricks SQL Dashboard Guide

This guide walks through building the assignment dashboard from Gold-layer tables using the queries in `dashboard_queries.sql`.

## Submission gate (required)

Dashboard work in the repository is **not complete** until you have done the following in Databricks:

1. Created and published a SQL dashboard with **all 3 required visualizations** (bar, histogram, pie/donut).
2. Created and wired **at least one working dashboard filter** linked to a query parameter (assignment requires filters).
3. Verified that changing the filter **updates at least one visualization tile**.

The repo provides SQL and instructions only; the live dashboard must be built and verified in the Databricks UI.

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

## Gold Table Reference (actual columns)

Use only these columns - they match the Gold SQL aggregations.

### `workspace.gold.sales_by_product`

| Column | Type (conceptual) | Use in dashboard |
|--------|-------------------|------------------|
| `product_id` | INT | Optional identifier |
| `product_name` | STRING | Bar chart category (X-axis) |
| `category` | STRING | Filter dimension |
| `total_orders` | BIGINT | n/a |
| `total_revenue` | DECIMAL | Bar chart value (Y-axis) |
| `avg_order_value` | DECIMAL | n/a |

### `workspace.gold.revenue_by_customer`

| Column | Type (conceptual) | Use in dashboard |
|--------|-------------------|------------------|
| `customer_id` | INT | Row identifier |
| `customer_name` | STRING | n/a |
| `customer_segment` | STRING | Filter dimension (Premium/Standard/Basic) |
| `total_orders` | BIGINT | n/a |
| `total_revenue` | DECIMAL | Histogram numeric field |
| `avg_order_value` | DECIMAL | n/a |
| `lifetime_value_actual` | DECIMAL | n/a |

### `workspace.gold.customer_segmentation`

| Column | Type (conceptual) | Use in dashboard |
|--------|-------------------|------------------|
| `segment_type` | STRING | Pie label (High-Value / Repeat / One-Time / Inactive) |
| `customer_count` | BIGINT | Pie value |
| `avg_revenue` | DECIMAL | n/a |
| `total_revenue` | DECIMAL | n/a |

---

## Query and parameter map

Each dashboard tile uses **one saved query**. Filters use **query parameters** on that same saved query.

| Saved query name | SQL section | Parameters (default) | Visualization |
|------------------|-------------|----------------------|---------------|
| `Top 10 Products by Revenue` | QUERY 1 | `product_category` = `All` | Bar chart tile |
| `Customer Revenue Distribution` | QUERY 2 | `customer_segment` = `All` | Histogram tile |
| `Customer Segmentation` | QUERY 3 | none | Pie / donut tile |
| `Filter - Product Categories` | FILTER SUPPORT (categories) | n/a (filter values only) | Dashboard filter source |
| `Filter - Customer Segments` | FILTER SUPPORT (segments) | n/a (filter values source) | Dashboard filter source |

**Parameter safety:** QUERY 1 and QUERY 2 treat `All` or empty string as "no filter" so unset defaults do not return zero rows.

---

## Step 1 - Create saved queries and define parameters

Open **Databricks SQL** -> **Queries** -> **Create query**.

### Top 10 Products by Revenue (QUERY 1)

1. Paste QUERY 1 from `dashboard_queries.sql`.
2. Add a **query parameter**:
   - Name: `product_category`
   - Type: text (or string)
   - Default value: `All`
3. Run the query and confirm rows return with default `All`.
4. Save as `Top 10 Products by Revenue`.

### Customer Revenue Distribution (QUERY 2)

1. Paste QUERY 2 from `dashboard_queries.sql`.
2. Add a **query parameter**:
   - Name: `customer_segment`
   - Type: text (or string)
   - Default value: `All`
3. Run and confirm rows return with default `All`.
4. Save as `Customer Revenue Distribution`.

If **Histogram** is not available in your workspace Visualization tab, save QUERY 2 FALLBACK instead as `Customer Revenue Distribution (Binned)` and use a Bar chart (see Step 2).

### Customer Segmentation (QUERY 3)

1. Paste QUERY 3 from `dashboard_queries.sql`.
2. No parameters required.
3. Save as `Customer Segmentation`.

### Filter support queries (required for filter wiring)

1. Save FILTER SUPPORT (categories) as `Filter - Product Categories`.
2. Save FILTER SUPPORT (segments) as `Filter - Customer Segments`.

These queries include `All` as the first value for safe defaults.

---

## Step 2 - Configure visualizations

For each tile saved query, open the **Visualization** tab.

### Tile 1 - Top 10 Products by Revenue (Bar Chart)

**Saved query:** `Top 10 Products by Revenue` (QUERY 1)

| Setting | Value |
|---------|-------|
| Visualization type | **Bar** |
| X-axis / Category | `product_name` |
| Y-axis / Value | `total_revenue` |
| Aggregation | None (one row per product) |

**Expected columns:** `product_name`, `total_revenue`

---

### Tile 2 - Customer Revenue Distribution (Histogram)

**Saved query:** `Customer Revenue Distribution` (QUERY 2)

| Setting | Value |
|---------|-------|
| Visualization type | **Histogram** |
| Numeric field / Value | `total_revenue` |
| Bin count | Recommended: 20-30 bins (adjust for readability) |

Each row is one customer; the histogram bins `total_revenue` across customers.

**Do not** use `lifetime_value_actual` or `avg_order_value` for this tile - the assignment asks for customer revenue distribution, and `total_revenue` is the per-customer metric in the Gold table.

**Expected columns:** `customer_id`, `total_revenue`

#### Histogram unavailable fallback (Bar chart on revenue bins)

If Histogram is not listed in your workspace:

1. Save QUERY 2 FALLBACK as `Customer Revenue Distribution (Binned)`.
2. Use visualization type **Bar**.
3. X-axis / Category: `revenue_bin`
4. Y-axis / Value: `customer_count`
5. Use the same `customer_segment` parameter (default `All`) on that saved query.

---

### Tile 3 - Customer Segmentation (Pie or Donut)

**Saved query:** `Customer Segmentation` (QUERY 3)

| Setting | Value |
|---------|-------|
| Visualization type | **Pie** or **Donut** |
| Label / Category | `segment_type` |
| Value | `customer_count` |
| Aggregation | Sum (one row per segment already) |

**Expected columns:** `segment_type`, `customer_count`

**Expected segment labels:** `High-Value`, `Repeat`, `One-Time`, `Inactive` (from `config.SEGMENT_TYPES`).

---

## Step 3 - Create the dashboard

1. Go to **Databricks SQL** -> **Dashboards** -> **Create dashboard**.
2. Name it (e.g. `E-commerce Medallion Analytics`).
3. Click **Add** -> **Visualization**.
4. Add each tile from its saved query:
   - Top 10 Products -> Bar (QUERY 1)
   - Customer Revenue Distribution -> Histogram (QUERY 2) or Bar on QUERY 2 FALLBACK
   - Customer Segmentation -> Pie/Donut (QUERY 3)
5. Arrange tiles on the canvas (three tiles satisfies the assignment).
6. Save or publish the dashboard.

---

## Step 4 - Required filters (assignment: "add filters")

Filters are **required** by `docs/assignment.md`, not optional.

Gold schema supports two filter dimensions without modifying Gold tables:

| Filter | Gold column | Filter values query | Parameter on tile query | Tile updated |
|--------|-------------|---------------------|-------------------------|--------------|
| Product category | `sales_by_product.category` | `Filter - Product Categories` | `product_category` on QUERY 1 | Top 10 Products |
| Customer segment | `revenue_by_customer.customer_segment` | `Filter - Customer Segments` | `customer_segment` on QUERY 2 (or FALLBACK) | Revenue Distribution |

The **Customer Segmentation** pie/donut tile does not use a filter (it already shows all segment types).

### Wiring filters to query parameters

Exact UI labels vary by workspace version. General flow:

1. On the dashboard, add a **filter** (or **Add filter** / **Dashboard filter**).
2. Choose a filter backed by a query or value list when available.
3. Select the filter support query (e.g. `Filter - Product Categories`) or map values from `product_category` / `customer_segment`.
4. **Link the filter to the query parameter** on the target saved query:
   - Filter -> `product_category` -> QUERY 1 saved query parameter `product_category`
   - Filter -> `customer_segment` -> QUERY 2 saved query parameter `customer_segment`
5. Set default filter value to **All** so all rows show on first load.
6. Confirm the parameter name in SQL matches exactly: `{{product_category}}` and `{{customer_segment}}`.

**Important:** Parameters must be defined on the **saved query** that powers the visualization, then connected to the dashboard filter where your workspace supports that linkage.

---

## Step 5 - Verify the dashboard

### Query-level checks

```sql
-- Top 10 (unfiltered): 10 rows or fewer
SELECT product_name, total_revenue
FROM workspace.gold.sales_by_product
ORDER BY total_revenue DESC
LIMIT 10;

-- Histogram input: many customer rows with numeric total_revenue
SELECT COUNT(*), MIN(total_revenue), MAX(total_revenue)
FROM workspace.gold.revenue_by_customer;

-- Segmentation
SELECT segment_type, customer_count
FROM workspace.gold.customer_segmentation
ORDER BY customer_count DESC;
```

### Dashboard-level checklist (required)

- [ ] All three tiles render without errors.
- [ ] Bar chart shows up to 10 products with descending revenue.
- [ ] Histogram (or binned bar fallback) shows distribution of per-customer `total_revenue`.
- [ ] Pie/donut shows `segment_type` slices sized by `customer_count`.
- [ ] **At least one dashboard filter is created and linked to a query parameter.**
- [ ] **Changing a filter updates at least one visualization tile** (e.g. category changes Top 10 list, or segment changes histogram counts).
- [ ] Default filter value `All` shows data (not zero rows).
- [ ] Values align with direct SQL against Gold tables (spot-check one product and one segment).

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
2. Defining query parameters (`product_category`, `customer_segment`) with default `All`.
3. Selecting visualization types and field mappings.
4. Creating the dashboard and arranging tiles.
5. Creating **required** dashboard filters and linking them to query parameters.
6. Publishing the dashboard and verifying filter behavior.

---

## Troubleshooting

| Issue | Likely cause | Action |
|-------|--------------|--------|
| Table not found | Gold not run | Execute `create_gold_tables.py` on Databricks |
| Empty visualization | Gold tables empty | Re-run Bronze -> Silver -> Gold |
| Zero rows after adding filter | Parameter not `All` and no match | Set default to `All`; confirm filter SQL uses `IN ('All', '')` |
| Histogram shows one bar | Wrong field mapped | Use `total_revenue`, not `customer_id` |
| Pie chart empty | Wrong value column | Use `customer_count`, not `total_revenue` |
| Filter does not apply | Parameter not linked | Define parameter on saved query; link dashboard filter to it |
| Histogram missing | Workspace chart types | Use QUERY 2 FALLBACK with Bar chart |

---

## File Reference

| File | Purpose |
|------|---------|
| `src/dashboard/dashboard_queries.sql` | Dashboard, filter, and fallback SQL |
| `src/gold/01_sales_by_product.sql` | Source aggregation for product revenue |
| `src/gold/02_revenue_by_customer.sql` | Source aggregation for customer revenue |
| `src/gold/04_customer_segmentation.sql` | Source aggregation for segmentation |
| `docs/assignment.md` | Assignment dashboard requirements |
