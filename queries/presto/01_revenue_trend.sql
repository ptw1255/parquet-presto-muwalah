-- Monthly Revenue Trend with YoY Comparison
-- Demonstrates: PARTITION PRUNING on orders (year/month)
-- Britt's use case: "Prepare the weekly revenue report by region"

SELECT
    year,
    month,
    COUNT(DISTINCT order_id) AS total_orders,
    ROUND(SUM(price), 2) AS total_revenue,
    ROUND(SUM(freight_value), 2) AS total_freight,
    ROUND(AVG(price), 2) AS avg_order_value
FROM muwalah.main.orders
WHERE year IN (2017, 2018)
GROUP BY year, month
ORDER BY year, month;
