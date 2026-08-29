-- =============================================================================
-- Databricks Medallion Pipeline - Dashboard SQL Queries
-- =============================================================================
-- Prerequisites: Gold tables must exist in workspace.gold (run create_gold_tables.py).
-- Run each query separately in Databricks SQL. Use query names suggested in
-- DASHBOARD_GUIDE.md when saving queries for the dashboard.
--
-- Parameters (define on each saved query in Databricks SQL):
--   product_category  (text, default: All) - Top 10 Products tile
--   customer_segment  (text, default: All) - Customer Revenue Distribution tile
-- =============================================================================


-- -----------------------------------------------------------------------------
-- QUERY 1: Top 10 Products by Revenue (Bar Chart)
-- Source: workspace.gold.sales_by_product
-- Parameter: product_category (text, default All)
-- Columns: product_name, total_revenue
-- -----------------------------------------------------------------------------
SELECT
    product_name,
    total_revenue
FROM workspace.gold.sales_by_product
WHERE (
    '{{product_category}}' IN ('All', '')
    OR category = '{{product_category}}'
)
ORDER BY total_revenue DESC
LIMIT 10;


-- -----------------------------------------------------------------------------
-- QUERY 2: Customer Revenue Distribution (Histogram)
-- Source: workspace.gold.revenue_by_customer
-- Parameter: customer_segment (text, default All)
-- One row per customer; histogram visualization bins total_revenue automatically.
-- Metric: total_revenue (per-customer revenue from Gold aggregation).
-- -----------------------------------------------------------------------------
SELECT
    customer_id,
    total_revenue
FROM workspace.gold.revenue_by_customer
WHERE total_revenue IS NOT NULL
  AND (
      '{{customer_segment}}' IN ('All', '')
      OR customer_segment = '{{customer_segment}}'
  )
ORDER BY total_revenue;


-- -----------------------------------------------------------------------------
-- QUERY 2 FALLBACK: Customer Revenue Distribution (Bar chart fallback)
-- Use only if Histogram is unavailable in your Databricks SQL workspace.
-- Same customer_segment parameter as QUERY 2.
-- Columns: revenue_bin, customer_count
-- -----------------------------------------------------------------------------
SELECT
    revenue_bin,
    customer_count
FROM (
    SELECT
        CASE
            WHEN total_revenue < 100 THEN '0-99'
            WHEN total_revenue < 500 THEN '100-499'
            WHEN total_revenue < 1000 THEN '500-999'
            WHEN total_revenue < 5000 THEN '1000-4999'
            ELSE '5000+'
        END AS revenue_bin,
        CASE
            WHEN total_revenue < 100 THEN 1
            WHEN total_revenue < 500 THEN 2
            WHEN total_revenue < 1000 THEN 3
            WHEN total_revenue < 5000 THEN 4
            ELSE 5
        END AS bin_order,
        COUNT(*) AS customer_count
    FROM workspace.gold.revenue_by_customer
    WHERE total_revenue IS NOT NULL
      AND (
          '{{customer_segment}}' IN ('All', '')
          OR customer_segment = '{{customer_segment}}'
      )
    GROUP BY 1, 2
)
ORDER BY bin_order;


-- -----------------------------------------------------------------------------
-- QUERY 3: Customer Segmentation (Pie / Donut Chart)
-- Source: workspace.gold.customer_segmentation
-- No parameters (tile is not filtered).
-- Columns: segment_type, customer_count
-- -----------------------------------------------------------------------------
SELECT
    segment_type,
    customer_count
FROM workspace.gold.customer_segmentation
ORDER BY customer_count DESC;


-- -----------------------------------------------------------------------------
-- FILTER SUPPORT: Product categories (dashboard filter for QUERY 1)
-- Includes All so unset filters do not return zero rows.
-- Bind to parameter product_category on the Top 10 Products saved query.
-- -----------------------------------------------------------------------------
SELECT product_category
FROM (
    SELECT 'All' AS product_category, 0 AS sort_order
    UNION ALL
    SELECT DISTINCT category AS product_category, 1 AS sort_order
    FROM workspace.gold.sales_by_product
    WHERE category IS NOT NULL
)
ORDER BY sort_order, product_category;


-- -----------------------------------------------------------------------------
-- FILTER SUPPORT: Customer segments (dashboard filter for QUERY 2)
-- Includes All so unset filters do not return zero rows.
-- Bind to parameter customer_segment on the Revenue Distribution saved query.
-- -----------------------------------------------------------------------------
SELECT customer_segment
FROM (
    SELECT 'All' AS customer_segment, 0 AS sort_order
    UNION ALL
    SELECT DISTINCT customer_segment, 1 AS sort_order
    FROM workspace.gold.revenue_by_customer
    WHERE customer_segment IS NOT NULL
)
ORDER BY sort_order, customer_segment;
