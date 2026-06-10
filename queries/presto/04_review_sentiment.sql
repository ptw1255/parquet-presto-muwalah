-- Review Sentiment Distribution by Product Category
-- Demonstrates: PREDICATE PUSHDOWN on review_score partition
-- Britt's use case: "Investigate anomalies flagged by leadership"

SELECT
    p.category_english AS category,
    r.review_score,
    COUNT(*) AS review_count,
    ROUND(AVG(LENGTH(r.review_comment_message)), 0) AS avg_comment_length
FROM muwalah.main.reviews r
JOIN muwalah.main.orders o ON r.order_id = o.order_id
JOIN muwalah.main.products p ON o.product_id = p.product_id
WHERE r.review_score <= 2
GROUP BY p.category_english, r.review_score
ORDER BY review_count DESC
LIMIT 20;
