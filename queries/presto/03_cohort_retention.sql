-- Customer Cohort Retention (Repeat Purchase Rate)
-- Demonstrates: JOIN EFFICIENCY + COLUMNAR READS
-- Britt's use case: "Investigate customer retention patterns"

WITH customer_orders AS (
    SELECT
        customer_id,
        COUNT(DISTINCT order_id) AS order_count,
        MIN(order_purchase_timestamp) AS first_order,
        MAX(order_purchase_timestamp) AS last_order
    FROM muwalah.main.orders
    WHERE order_status = 'delivered'
    GROUP BY customer_id
),
cohorts AS (
    SELECT
        DATE_TRUNC('month', first_order) AS cohort_month,
        COUNT(*) AS cohort_size,
        SUM(CASE WHEN order_count > 1 THEN 1 ELSE 0 END) AS repeat_customers
    FROM customer_orders
    GROUP BY DATE_TRUNC('month', first_order)
)
SELECT
    cohort_month,
    cohort_size,
    repeat_customers,
    ROUND(100.0 * repeat_customers / cohort_size, 1) AS repeat_rate_pct
FROM cohorts
ORDER BY cohort_month;
