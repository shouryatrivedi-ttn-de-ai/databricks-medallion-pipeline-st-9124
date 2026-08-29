-- Sales by product from eligible completed orders and eligible products.
SELECT
    p.product_id,
    p.product_name,
    p.category,
    COUNT(DISTINCT o.order_id) AS total_orders,
    CAST(SUM(o.total_amount) AS DECIMAL(18, 2)) AS total_revenue,
    CAST(
        CASE
            WHEN COUNT(DISTINCT o.order_id) = 0 THEN NULL
            ELSE SUM(o.total_amount) / COUNT(DISTINCT o.order_id)
        END AS DECIMAL(18, 2)
    ) AS avg_order_value
FROM eligible_orders o
INNER JOIN eligible_products p
    ON o.product_id = p.product_id
GROUP BY
    p.product_id,
    p.product_name,
    p.category
