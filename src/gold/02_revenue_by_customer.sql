-- Revenue by customer from eligible completed orders and eligible customers.
SELECT
    c.customer_id,
    c.customer_name,
    c.customer_segment,
    COUNT(DISTINCT o.order_id) AS total_orders,
    CAST(SUM(o.total_amount) AS DECIMAL(18, 2)) AS total_revenue,
    CAST(
        CASE
            WHEN COUNT(DISTINCT o.order_id) = 0 THEN NULL
            ELSE SUM(o.total_amount) / COUNT(DISTINCT o.order_id)
        END AS DECIMAL(18, 2)
    ) AS avg_order_value,
    CAST(SUM(o.total_amount) AS DECIMAL(18, 2)) AS lifetime_value_actual
FROM eligible_orders o
INNER JOIN eligible_customers c
    ON o.customer_id = c.customer_id
GROUP BY
    c.customer_id,
    c.customer_name,
    c.customer_segment
