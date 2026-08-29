-- =============================================================================
-- Databricks Medallion Pipeline - Dashboard SQL Queries
-- =============================================================================
-- Prerequisites: Gold tables must exist in workspace.gold (run create_gold_tables.py).
-- Run each query separately in Databricks SQL. Use query names suggested in
-- DASHBOARD_GUIDE.md when saving queries for the dashboard.
--
-- Deployed dashboard tiles (four visualizations):
--   QUERY 1 - Customer Distribution by Segment       (pie / donut)
--   QUERY 2 - Total Revenue by Customer Segment    (bar)
--   QUERY 3 - Top 10 Customers by Revenue          (bar)
--   QUERY 4 - Total Revenue by Product Category    (bar)
--
-- Optional parameters (define on saved queries in Databricks SQL):
--   customer_segment  (text, default: All) - QUERY 3
--   product_category  (text, default: All) - QUERY 4
-- =============================================================================


-- -----------------------------------------------------------------------------
-- QUERY 1: Customer Distribution by Segment (Pie / Donut Chart)
-- Source: workspace.gold.customer_segmentation
-- Columns: segment_type, customer_count
-- -----------------------------------------------------------------------------
SELECT
    segment_type,
    customer_count
FROM workspace.gold.customer_segmentation
ORDER BY customer_count DESC;


-- -----------------------------------------------------------------------------
-- QUERY 2: Total Revenue by Customer Segment (Bar Chart)
-- Source: workspace.gold.customer_segmentation
-- Columns: segment_type, total_revenue
-- -----------------------------------------------------------------------------
SELECT
    segment_type,
    total_revenue
FROM workspace.gold.customer_segmentation
ORDER BY total_revenue DESC;


-- -----------------------------------------------------------------------------
-- QUERY 3: Top 10 Customers by Revenue (Bar Chart)
-- Source: workspace.gold.revenue_by_customer
-- Parameter: customer_segment (text, default All)
-- Columns: customer_name, total_revenue
-- -----------------------------------------------------------------------------
SELECT
    customer_name,
    total_revenue
FROM workspace.gold.revenue_by_customer
WHERE (
    '{{customer_segment}}' IN ('All', '')
    OR customer_segment = '{{customer_segment}}'
)
ORDER BY total_revenue DESC
LIMIT 10;


-- -----------------------------------------------------------------------------
-- QUERY 4: Total Revenue by Product Category (Bar Chart)
-- Source: workspace.gold.sales_by_product
-- Parameter: product_category (text, default All)
-- Columns: category, total_revenue
-- -----------------------------------------------------------------------------
SELECT
    category,
    SUM(total_revenue) AS total_revenue
FROM workspace.gold.sales_by_product
WHERE (
    '{{product_category}}' IN ('All', '')
    OR category = '{{product_category}}'
)
GROUP BY category
ORDER BY total_revenue DESC;


-- -----------------------------------------------------------------------------
-- FILTER SUPPORT: Customer segments (dashboard filter for QUERY 3)
-- Source: workspace.gold.revenue_by_customer.customer_segment
-- Premium / Standard / Basic from the customer master.
-- Bind to parameter customer_segment on the Top 10 Customers saved query.
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


-- -----------------------------------------------------------------------------
-- FILTER SUPPORT: Product categories (dashboard filter for QUERY 4)
-- Source: workspace.gold.sales_by_product.category
-- Bind to parameter product_category on the Revenue by Category saved query.
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
