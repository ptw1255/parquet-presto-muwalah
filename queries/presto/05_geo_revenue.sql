-- Geographic Revenue Heatmap by State and Quarter
-- Demonstrates: COLUMN PROJECTION (reads only 3 of 20+ columns)
-- Britt's use case: "Prepare revenue report by region"

SELECT
    c.customer_state AS state,
    DATE_TRUNC('quarter', o.order_purchase_timestamp) AS quarter,
    COUNT(DISTINCT o.order_id) AS order_count,
    ROUND(SUM(o.price), 2) AS total_revenue,
    ROUND(SUM(o.price) / COUNT(DISTINCT o.order_id), 2) AS avg_order_value
FROM muwalah.main.orders o
JOIN muwalah.main.customers c ON o.customer_id = c.customer_id
GROUP BY c.customer_state, DATE_TRUNC('quarter', o.order_purchase_timestamp)
ORDER BY state, quarter;
