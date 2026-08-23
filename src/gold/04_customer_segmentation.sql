-- Customer segmentation from eligible customers and their eligible completed orders.
WITH customer_order_metrics AS (
    SELECT
        customer_id,
        COUNT(DISTINCT order_id) AS total_orders,
        CAST(SUM(total_amount) AS DECIMAL(18, 2)) AS total_revenue
    FROM eligible_orders
    GROUP BY customer_id
),
segmentation_base AS (
    SELECT
        c.customer_id,
        COALESCE(m.total_orders, 0) AS total_orders,
        COALESCE(m.total_revenue, CAST(0 AS DECIMAL(18, 2))) AS total_revenue
    FROM eligible_customers c
    LEFT JOIN customer_order_metrics m
        ON c.customer_id = m.customer_id
),
labeled AS (
    SELECT
        customer_id,
        total_orders,
        total_revenue,
        CASE
            WHEN total_revenue >= {{SEGMENTATION_HIGH_VALUE_THRESHOLD}} THEN 'High-Value'
            WHEN total_orders >= 2 THEN 'Repeat'
            WHEN total_orders = 1 THEN 'One-Time'
            ELSE 'Inactive'
        END AS segment_type
    FROM segmentation_base
)
SELECT
    segment_type,
    COUNT(*) AS customer_count,
    CAST(AVG(total_revenue) AS DECIMAL(18, 2)) AS avg_revenue,
    CAST(SUM(total_revenue) AS DECIMAL(18, 2)) AS total_revenue
FROM labeled
GROUP BY segment_type
