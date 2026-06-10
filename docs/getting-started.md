# Getting Started Guide

A step-by-step walkthrough of every command in this project -- what it does, why it matters, and how the pieces connect. Start from zero and end with a working analytics stack on your laptop.

---

## Quick Start

Two commands to go from zero to interactive NL-to-SQL:

```bash
python3 data/convert.py   # convert CSV -> Parquet (run separately so you can swap datasets)
./demo.sh                 # everything else: installs deps, pulls AI model, starts Trino, launches prompt
```

`demo.sh` handles Python dependencies, the Granite model download, Docker/Trino startup, and data loading automatically. On subsequent runs it skips what's already done and goes straight to the prompt.

You can also pass a question directly for a single query:

```bash
./demo.sh "Top 5 categories by revenue in Q4 2017?"
```

**Tip:** Run `./demo.sh` a minute before a demo to warm up the Granite model. The first query after a cold start takes ~60 seconds; subsequent queries take 2-3 seconds.

### Demo Queries

These 5 questions are tuned for the interactive terminal. They tell a story from revenue overview to deep investigation, and each demonstrates a different Parquet/Trino feature:

| # | Question to type | What it demonstrates |
|---|---|---|
| 1 | `What were the top 5 product categories by total revenue?` | Join across orders + products, revenue drivers |
| 2 | `Compare total revenue between 2017 and 2018` | Partition pruning on year, YoY growth |
| 3 | `What percentage of orders were paid with credit card vs boleto?` | Single-table aggregation, fast response |
| 4 | `Which 5 states have the worst average review scores, and what is their average delivery time?` | 3-table join (orders + customers + reviews), date math |
| 5 | `What are the top 5 product categories with the most 1-star reviews?` | Partition pruning on review_score, complaint investigation |

**The narrative:** Start with "where's the money?" (Q1-2), then "how do customers pay?" (Q3), then "where are customers unhappy?" (Q4-5).

The rest of this guide explains what each piece does under the hood.

---

## Prerequisites

Before starting, make sure you have these installed:

| Tool | Why you need it | Install |
|---|---|---|
| **Docker Desktop** | Runs Trino (the SQL engine) in a container so you don't install Java, configure catalogs, or manage a JVM yourself | [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/) |
| **Python 3.10+** | Runs the conversion pipeline, data loaders, benchmarks, and AI scripts | `brew install python` or [python.org](https://www.python.org/) |
| **Ollama** | Runs IBM Granite 4.0 locally for NL-to-SQL (Step 4 only) | [ollama.com](https://ollama.com/) |
| **Olist dataset** | The raw CSV data -- 9 files from a real Brazilian e-commerce marketplace | [Kaggle download](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) |

**Dataset setup:** Download the Olist dataset from Kaggle and place all 9 CSV files into `data/raw/`:

```
data/raw/
  olist_customers_dataset.csv
  olist_geolocation_dataset.csv
  olist_order_items_dataset.csv
  olist_order_payments_dataset.csv
  olist_order_reviews_dataset.csv
  olist_orders_dataset.csv
  olist_products_dataset.csv
  olist_sellers_dataset.csv
  product_category_name_translation.csv
```

---

## Step 1: CSV to Parquet Conversion

### Install Python dependencies

```bash
pip install -r requirements.txt
```

> **Note:** `./demo.sh` runs this automatically if deps are missing. You only need to run it manually if you're doing the conversion step without `demo.sh`.

This installs:
- **pyarrow** -- the Apache Arrow library that reads/writes Parquet files
- **pandas** -- DataFrame library used for joins, aggregations, and type coercion during conversion
- **matplotlib** -- generates benchmark charts
- **numpy** -- used by the product similarity engine
- **anthropic** -- Claude API client (used in an earlier iteration of NL-to-SQL; current version uses Ollama instead)
- **trino** -- Python client for loading data into Trino's managed tables
- **rich** -- styled terminal output for the interactive UI (`muwalah.py`)

### Run the conversion

```bash
python3 data/convert.py
```

**What this does:** Reads 9 raw CSV files and writes 5 Parquet datasets. It's not a simple format swap -- the script makes several intentional decisions:

**Denormalization:** Orders, order items, and payments are three separate CSVs. The script joins them into one `orders` dataset so downstream queries don't need three-way joins. Products are joined with category name translations. Customers and sellers are joined with geolocation averages.

**Partitioning:** Two datasets are partitioned -- meaning the data is split into subdirectories by column values:
- `orders/` is partitioned by `year/month` (e.g., `orders/year=2017/month=10/`). This matches how analysts query: "show me Q4 2017 revenue." Trino reads only the directories that match, skipping everything else.
- `reviews/` is partitioned by `review_score` (1-5). Queries like "show me all 1-star reviews" only read 20% of the data.
- `products/`, `customers/`, `sellers/` are small tables (< 100K rows), so they're stored as single files with no partitioning.

**Compression:**
- **Snappy** for orders, reviews, products, sellers -- fast decompression, good for frequently-read tables
- **Zstd** for customers -- better compression ratio, less frequently queried

**Nested structs:** Products use Parquet's nested type support. Physical dimensions (`weight_g`, `length_cm`, `height_cm`, `width_cm`) are stored as a `dimensions` struct, and categories (`portuguese`, `english`) as a `category` struct. This keeps related fields grouped in the schema.

**Expected output:**
```
Converting orders...
  → 112,650 rows → data/parquet/orders
Converting products...
  → 32,951 rows → data/parquet/products
Converting customers...
  → 99,441 rows → data/parquet/customers
Converting reviews...
  → 99,224 rows → data/parquet/reviews
Converting sellers...
  → 3,095 rows → data/parquet/sellers

==================================================
CSV total:     120.3 MB
Parquet total: 32.0 MB
Compression:   73% smaller
==================================================
```

**Why this matters:** The same data, 73% smaller, with self-describing schemas, typed columns, and a directory structure that eliminates unnecessary I/O. This is the foundation for everything that follows.

---

## Step 2: Docker / Trino Setup

### Start Trino

```bash
docker compose up -d
```

**What this does:** Starts a single Trino container (`muwalah-trino`) in the background. Let's break down what `docker-compose.yml` configures:

- **Image:** `trinodb/trino:latest` -- the official Trino Docker image, includes the Hive connector needed for Parquet
- **Port 8080:** Trino's HTTP interface. The `trino` CLI client connects here, and the Python `trino` library uses it too
- **Volume mounts:**
  - `./etc/trino` -> `/etc/trino` -- Trino server config (JVM settings, node ID, coordinator settings)
  - `./etc/catalog` -> `/etc/trino/catalog` -- catalog config that tells Trino where to find data
  - `./data/parquet` -> `/data/parquet` -- the Parquet files you created in Step 1, mounted read-only into the container
  - `trino-metastore` -> `/data/metastore` -- a Docker volume for Trino's file-based metastore (table definitions persist across container restarts)
- **Health check:** Trino runs `SELECT 1` every 10 seconds until the server is ready (up to 2 minutes)

The catalog config (`etc/catalog/muwalah.properties`) tells Trino to use the **Hive connector** with a local file-based metastore. This means Trino can create and manage tables that reference the Parquet files on disk -- no Hive server or S3 needed.

### Load data into Trino

```bash
python3 scripts/load_data.py
```

**What this does:** Creates 5 managed tables in Trino and inserts all data from the Parquet files. The script:

1. Waits for Trino to be ready (polls `SELECT 1` for up to 60 seconds)
2. Creates the `muwalah.main` schema
3. For each table (`sellers`, `products`, `customers`, `reviews`, `orders`):
   - Drops the table if it exists (clean slate)
   - Creates the table with `WITH (format = 'PARQUET')` -- Trino stores the data as Parquet internally
   - For partitioned tables (`orders`, `reviews`), adds `partitioned_by = ARRAY[...]`
   - Reads the Parquet files via pyarrow and inserts rows in batches of 500
4. Verifies row counts match

**Why managed tables?** The alternative is external tables (defined in `scripts/init_tables.sql`) that point directly at the Parquet files on disk. Managed tables copy the data into Trino's own storage, which means:
- Trino controls the file layout and metadata
- Partition metadata is automatically tracked
- No risk of the source files being moved or deleted

The `load_orders.py` script is a standalone loader for just the orders table (the largest), useful if you need to reload it independently:

```bash
python3 scripts/load_orders.py
```

### Verify it's working

```bash
docker exec muwalah-trino trino --execute "SELECT COUNT(*) FROM muwalah.main.orders"
```

You should see a row count around `112,650`.

### Stopping and restarting

```bash
# Stop Trino (data persists in the trino-metastore volume)
docker compose down

# Restart (tables are still there -- no need to reload)
docker compose up -d

# Full reset (deletes the metastore volume -- you'll need to reload data)
docker compose down -v
```

---

## Step 3: Running Presto Queries

The project includes 6 analytical queries, each designed to demonstrate a specific Parquet + Trino performance feature.

### Run a single query

```bash
docker exec -i muwalah-trino trino --catalog muwalah --schema main \
  < queries/presto/01_revenue_trend.sql
```

The `-i` flag pipes stdin into the container, so the SQL file contents are sent to the `trino` CLI.

### Run all 6 queries

```bash
for f in queries/presto/0*.sql; do
  echo "=== $f ==="
  docker exec -i muwalah-trino trino --catalog muwalah --schema main < "$f"
done
```

### What each query demonstrates

| # | File | Business Question | Parquet Feature |
|---|---|---|---|
| 01 | `01_revenue_trend.sql` | Monthly revenue, year-over-year | **Partition pruning** -- `WHERE year IN (2017, 2018)` skips all other year directories |
| 02 | `02_top_products.sql` | Top categories by revenue (lightweight items) | **Predicate pushdown** -- `WHERE weight_g < 5000` filters at the storage layer |
| 03 | `03_cohort_retention.sql` | Customer cohort repeat purchase rate | **Column projection** -- reads 4 columns from a 20-column table |
| 04 | `04_review_sentiment.sql` | Low-star review analysis by category | **Partition pruning** -- `WHERE review_score <= 2` reads only 2 of 5 partitions |
| 05 | `05_geo_revenue.sql` | Revenue by state and quarter | **Column projection** -- 6 columns from 27+ across two tables |
| 06 | `06_delivery_vs_reviews.sql` | Delivery speed vs. review score by state | **Complex joins** -- 3-table join with window functions |

### Run ad-hoc SQL

You can run any Trino SQL directly:

```bash
docker exec muwalah-trino trino --execute "
  SELECT customer_state, COUNT(*) AS order_count
  FROM muwalah.main.orders o
  JOIN muwalah.main.customers c ON o.customer_id = c.customer_id
  GROUP BY customer_state
  ORDER BY order_count DESC
  LIMIT 5
"
```

### View query execution plans

To see how Trino reads Parquet (and verify partition pruning / column projection):

```bash
docker exec muwalah-trino trino --execute "
  EXPLAIN SELECT year, month, SUM(price)
  FROM muwalah.main.orders
  WHERE year = 2017
  GROUP BY year, month
"
```

Look for `PARTITION_KEY` in the output -- that confirms Trino is using partition metadata from the directory structure instead of scanning every file.

For detailed explanation of what each query returns and the EXPLAIN plan evidence, see [`queries/presto/README.md`](../queries/presto/README.md).

---

## Step 4: AI Features

Two AI-powered features demonstrate why Parquet's self-describing schema matters for the AI era.

### Natural Language to SQL

**Prerequisite:** Install and start Ollama, then pull the Granite model:

```bash
ollama pull sam860/granite-4.0:7b
```

This downloads IBM Granite 4.0 (7B parameters) -- runs locally, no API keys needed.

**Run it:**

```bash
python3 queries/ai/nl2sql.py "Top 5 categories by revenue in Sao Paulo, Q4 2017?"
```

**What happens:**
1. The script sends the full Parquet schema (table names, column names, column types, partition columns, SQL dialect notes) to Granite via Ollama's local API
2. Granite generates valid Trino SQL based on the schema context
3. The script runs that SQL against Trino via `docker exec`
4. Results are displayed

The interactive terminal (`./demo.sh`) adds more on top of this:

- **Natural language answer** -- sends the question and raw results back to Granite, which returns a plain-English summary with the actual numbers
- **Dataset overview** -- on startup, shows a table of all 5 tables with row counts (348K+ total) and which columns are partitioned
- **Query telemetry** -- after each query, shows timing for each step (SQL generation, query execution, summarization), rows returned, and partition pruning evidence from EXPLAIN

So you see the full pipeline: generated SQL, raw data table, plain English answer, and performance telemetry.

**Why this matters:** The schema context is the key. The model knows that `price` is a `DOUBLE`, that `year` is an `INTEGER` partition column, and that table names are fully qualified as `muwalah.main.tablename`. CSV headers are untyped strings -- they can't provide this context, which means LLMs generate unreliable SQL from them.

You can also run it interactively (no argument = prompt mode):

```bash
python3 queries/ai/nl2sql.py
# → Ask a question about the data: _
```

**Easier option:** `./demo.sh` wraps all of this into a single interactive session with styled output -- see [Quick Start](#quick-start).

### Product Similarity

```bash
python3 queries/ai/similarity.py
```

**What happens:**
1. Reads product features directly from Parquet files (not from Trino -- demonstrating that ML pipelines can consume the same Parquet files as analytics)
2. Enriches products with order statistics (avg price, order count) and review scores
3. Builds 11-dimensional feature vectors (weight, dimensions, price, reviews, etc.)
4. Normalizes features to [0,1] and computes cosine similarity
5. Displays the most popular products and lets you pick one to find similar items

**Run with a specific product:**

```bash
python3 queries/ai/similarity.py <product_id>
```

**Why this matters:** Same Parquet files serve both SQL analytics and ML feature extraction. No separate ETL step, no data copy, no format conversion. This is the "Parquet as AI on-ramp" argument from the README.

---

## Step 5: Benchmarks

```bash
python3 benchmarks/format_comparison.py
```

**What this does:** Compares CSV, JSON, and Parquet across three dimensions:
1. **Full table read** -- read the entire orders dataset
2. **Column projection** -- read only 2 of 19 columns
3. **Filtered read** -- read only October 2017 orders (partition pruning vs. full scan + filter)

The script also measures storage footprint, generates PNG charts, and saves raw results to `benchmarks/results/benchmark_results.json`.

**View the charts:**

```bash
open benchmarks/results/format_comparison.png
open benchmarks/results/storage_comparison.png
```

---

## Quick Reference

```bash
# === QUICK START (recommended) ===
python3 data/convert.py                            # CSV -> Parquet (one-time, or when data changes)
./demo.sh                                          # auto-installs deps, pulls model, launches prompt
./demo.sh "your question"                          # single query mode

# === MANUAL START ===
pip install -r requirements.txt                    # install Python deps
ollama pull sam860/granite-4.0:7b                  # pull the model
docker compose up -d                               # start Trino
python3 scripts/load_data.py                       # load all tables
python3 muwalah.py                                 # launch interactive prompt

# === QUERY ===
docker exec -i muwalah-trino trino \
  --catalog muwalah --schema main \
  < queries/presto/01_revenue_trend.sql            # run a query file

docker exec muwalah-trino trino \
  --execute "SELECT COUNT(*) FROM muwalah.main.orders"  # ad-hoc SQL

# === AI (standalone) ===
python3 queries/ai/nl2sql.py "your question here"  # NL -> SQL
python3 queries/ai/similarity.py                   # product similarity

# === BENCHMARKS ===
python3 benchmarks/format_comparison.py            # run benchmarks

# === STOP ===
docker compose down                                # stop (data persists)
docker compose down -v                             # stop + delete data
```
