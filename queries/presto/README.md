# Presto/Trino Business Queries

Six analytical queries against the Olist e-commerce dataset (Brazilian marketplace, 2016–2018).
Each query is designed to illustrate a specific Parquet + Trino performance feature.

All queries run against catalog `muwalah`, schema `main`.

---

## Query 01 — Monthly Revenue Trend with YoY Comparison
**File:** `01_revenue_trend.sql`

**Business question:** How does monthly revenue compare year-over-year? (Britt's use case: "Prepare the weekly revenue report by region")

**Parquet/Presto feature demonstrated:** **Partition pruning** — `orders` is partitioned by `year` and `month`. The `WHERE year IN (2017, 2018)` predicate lets Trino skip every other partition directory at the file-system level, reading only the relevant row groups.

**Sample output (first 4 rows):**
```
year | month | total_orders | total_revenue | total_freight | avg_order_value
2017 |     1 |          800 |     120312.87 |      16875.62 |          125.98
2017 |     2 |         1780 |     247303.02 |      38977.60 |          126.76
2017 |     3 |         2682 |     374344.30 |      57704.29 |          124.78
2017 |     4 |         2404 |     359927.23 |      52495.01 |          134.10
```

### EXPLAIN excerpt — partition pruning evidence

```
Fragment 2 [SOURCE]
    TableScan[table = muwalah:main:orders]
           Layout: [order_id:varchar, price:double, year:integer, month:integer]
           Estimates: {rows: 51386 (2.74MB), cpu: 2.74M, memory: 0B, network: 0B}
           month := month:int:PARTITION_KEY
               :: [[1], [2], [3], [4], [5], [6], [7], [8], [9], [10], [11], [12]]
           price := price:double:REGULAR
           year := year:int:PARTITION_KEY
               :: [[2017]]
           order_id := order_id:string:REGULAR
```

Key indicators:
- `year` and `month` are both typed `PARTITION_KEY` — Trino resolves them from directory names without reading Parquet row groups.
- `year :: [[2017]]` — only the 2017 partition directory is scanned; all other years are skipped entirely.
- The 4-column layout `[order_id, price, year, month]` confirms **column projection**: Trino reads only the 4 columns needed, ignoring the other 15+ columns in the Parquet files.

---

## Query 02 — Top Products by Category
**File:** `02_top_products.sql`

**Business question:** Which product categories drive the most revenue among lightweight items? (Britt's use case: "Find product trends to inform purchasing")

**Parquet/Presto feature demonstrated:** **Predicate pushdown** — `WHERE p.weight_g < 5000` is pushed into the Parquet scan for `products`, so rows with heavy products are discarded at the storage layer before reaching Trino's compute engine.

**Sample output (top 5):**
```
category              | order_count | total_revenue | avg_weight_g
watches_gifts         |        5611 |   1201896.01 |          556
health_beauty         |        8585 |   1123825.48 |          673
bed_bath_table        |        8447 |    824879.93 |         1309
computers_accessories |        6282 |    809334.91 |          524
sports_leisure        |        7151 |    789454.38 |         1027
```

---

## Query 03 — Customer Cohort Retention
**File:** `03_cohort_retention.sql`

**Business question:** What fraction of customers from each monthly cohort make a repeat purchase? (Britt's use case: "Investigate customer retention patterns")

**Parquet/Trino feature demonstrated:** **Join efficiency + columnar reads** — the CTE `customer_orders` reads only `customer_id`, `order_id`, `order_purchase_timestamp`, and `order_status` from the wide `orders` table. Parquet column projection means Trino skips all other columns on disk.

**Sample output (first 5 rows):**
```
cohort_month              | cohort_size | repeat_customers | repeat_rate_pct
2016-09-01 00:00:00.000   |           1 |                0 |             0.0
2016-10-01 00:00:00.000   |         265 |                0 |             0.0
2017-01-01 00:00:00.000   |         750 |                0 |             0.0
2017-02-01 00:00:00.000   |        1653 |                0 |             0.0
2017-03-01 00:00:00.000   |        2546 |                0 |             0.0
```

Note: The Olist dataset uses one `customer_id` per order (by design), so repeat purchases appear under different `customer_id` values. Repeat rate via `customer_unique_id` would require a join to the customers table — this query intentionally shows the raw schema behavior.

---

## Query 04 — Review Sentiment by Product Category
**File:** `04_review_sentiment.sql`

**Business question:** Which product categories receive the most 1–2 star reviews, and how long are the complaints? (Britt's use case: "Investigate anomalies flagged by leadership")

**Parquet/Trino feature demonstrated:** **Predicate pushdown on a partition key** — `reviews` is partitioned by `review_score`. The filter `WHERE r.review_score <= 2` lets Trino skip the `review_score=3`, `review_score=4`, and `review_score=5` partition directories entirely, reading only ~20% of the reviews data.

**Sample output (top 5):**
```
category              | review_score | review_count | avg_comment_length
bed_bath_table        |            1 |         1614 |               72.0
furniture_decor       |            1 |         1260 |               75.0
computers_accessories |            1 |         1174 |               87.0
health_beauty         |            1 |         1081 |               76.0
sports_leisure        |            1 |         1028 |               80.0
```

---

## Query 05 — Geographic Revenue Heatmap
**File:** `05_geo_revenue.sql`

**Business question:** How does quarterly revenue break down across Brazilian states? (Britt's use case: "Prepare revenue report by region")

**Parquet/Trino feature demonstrated:** **Column projection** — despite `orders` having 20+ columns and `customers` having 7 columns, the query reads only `order_id`, `price`, `order_purchase_timestamp`, `customer_id` from orders and `customer_id`, `customer_state` from customers — 6 columns total out of 27+.

**Sample output (excerpt, SP state):**
```
state | quarter                  | order_count | total_revenue | avg_order_value
SP    | 2017-07-01 00:00:00.000  |        4971 |    601844.85  |          121.07
SP    | 2017-10-01 00:00:00.000  |        7162 |    868897.53  |          121.32
SP    | 2018-01-01 00:00:00.000  |        8792 |   1073432.26  |          122.09
SP    | 2018-04-01 00:00:00.000  |        9039 |   1179247.29  |          130.46
```

---

## Query 06 — Delivery Performance vs. Review Score
**File:** `06_delivery_vs_reviews.sql`

**Business question:** Which states have the worst review scores, and does late delivery explain it? (Britt's use case: "Why did bad reviews spike last month?")

**Parquet/Trino feature demonstrated:** **Complex aggregation across multiple tables** — three-way join (`orders` × `reviews` × `customers`) with `DATE_DIFF` window calculations, `HAVING` filtering, and ordering. Trino's vectorized Parquet reader handles the multi-column scan efficiently.

**Sample output (bottom 5 states by review score):**
```
state | avg_review_score | avg_delivery_days | avg_delay_days | total_orders
MA    |             3.77 |              21.0 |           -9.3 |          712
AL    |             3.82 |              23.9 |           -8.1 |          394
PA    |             3.84 |              23.1 |          -13.6 |          933
BA    |             3.86 |              18.7 |          -10.2 |         3229
RJ    |             3.87 |              14.6 |          -11.2 |        12211
```

Negative `avg_delay_days` means actual delivery was earlier than estimated. States like MA and AL have the lowest review scores despite reasonable delivery times, suggesting other factors (product quality, seller service) drive dissatisfaction in those regions.

---

## Running the queries

```bash
# Run a single query
docker exec -i muwalah-trino trino --catalog muwalah --schema main \
  < queries/presto/01_revenue_trend.sql

# Run all queries
for f in queries/presto/0*.sql; do
  echo "=== $f ==="
  docker exec -i muwalah-trino trino --catalog muwalah --schema main < "$f"
done

# Regenerate the EXPLAIN plan for query 1
docker exec muwalah-trino trino --execute \
  "EXPLAIN SELECT year, month, COUNT(DISTINCT order_id), SUM(price)
   FROM muwalah.main.orders WHERE year = 2017 GROUP BY year, month"
```
