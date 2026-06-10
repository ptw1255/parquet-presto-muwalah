-- Delivery Performance vs. Review Score Correlation
-- Demonstrates: COMPLEX AGGREGATION across multiple tables
-- Britt's use case: "Why did bad reviews spike last month?"

SELECT
    c.customer_state AS state,
    ROUND(AVG(r.review_score), 2) AS avg_review_score,
    ROUND(AVG(
        DATE_DIFF('day',
            o.order_purchase_timestamp,
            o.order_delivered_customer_date)
    ), 1) AS avg_delivery_days,
    ROUND(AVG(
        DATE_DIFF('day',
            o.order_estimated_delivery_date,
            o.order_delivered_customer_date)
    ), 1) AS avg_delay_days,
    COUNT(DISTINCT o.order_id) AS total_orders
FROM muwalah.main.orders o
JOIN muwalah.main.reviews r ON o.order_id = r.order_id
JOIN muwalah.main.customers c ON o.customer_id = c.customer_id
WHERE o.order_status = 'delivered'
  AND o.order_delivered_customer_date IS NOT NULL
GROUP BY c.customer_state
HAVING COUNT(DISTINCT o.order_id) > 100
ORDER BY avg_review_score ASC;
