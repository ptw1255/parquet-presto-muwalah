-- Top Products by Category with Dimension Filtering
-- Demonstrates: PREDICATE PUSHDOWN
-- Britt's use case: "Find product trends to inform purchasing"

SELECT
    p.category_english AS category,
    COUNT(DISTINCT o.order_id) AS order_count,
    ROUND(SUM(o.price), 2) AS total_revenue,
    ROUND(AVG(p.weight_g), 0) AS avg_weight_g
FROM muwalah.main.orders o
JOIN muwalah.main.products p ON o.product_id = p.product_id
WHERE p.weight_g < 5000
GROUP BY p.category_english
ORDER BY total_revenue DESC
LIMIT 15;
