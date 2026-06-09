# Muwalah Commerce: Parquet + Presto Analytics Modernization — Design Spec

**Date:** 2026-06-09
**Author:** Parker Wall
**Purpose:** Portfolio project for IBM Senior PM role demonstrating Presto/Parquet competency for business analytics in the AI era.

---

## 1. Project Narrative

Muwalah Commerce is a fictional mid-size e-commerce retailer. Leadership wants to modernize analytics from legacy CSV/JSON flat files to support AI-driven insights. This repo is the PM's business case and working proof-of-concept.

The README reads as a product decision document — not a tech tutorial. Interviewers who never run the code get the full story. Those who do get live proof.

**Target audience:** IBM interviewers evaluating PM competency in Presto, Parquet, and AI-era analytics.

**Delivery format:** Polished GitHub repo + live demo walkthrough.

**Timeline:** This week (June 9-13, 2026).

---

## 2. Constraints

- MacBook Pro M4 Pro, 12 cores, 24GB RAM
- 10GB storage budget
- Everything runs locally (Docker + Python)
- Estimated footprint: ~50MB Parquet data + ~1.5GB Trino Docker image = ~1.6GB
- Data source: Olist Brazilian E-Commerce dataset from Kaggle (~100MB CSV)

---

## 3. Repo Structure

```
parquet-presto-muwalah/
├── README.md                    # Product decision document
├── docs/
│   ├── adr/                     # Architecture Decision Records
│   │   ├── 001-why-parquet.md
│   │   ├── 002-partition-strategy.md
│   │   ├── 003-compression-codec.md
│   │   └── 004-ai-integration.md
│   └── cost-model.md            # TCO comparison: legacy vs modern
├── data/
│   ├── raw/                     # Original Olist CSVs (gitignored)
│   ├── parquet/                 # Converted Parquet files (gitignored)
│   ├── convert.py               # CSV → Parquet conversion pipeline
│   └── schemas/                 # Parquet schema definitions
├── benchmarks/
│   ├── format_comparison.py     # CSV vs JSON vs Parquet
│   └── results/                 # Benchmark outputs, charts
├── queries/
│   ├── presto/                  # Business analytics SQL
│   └── ai/                      # NL→SQL and embedding scripts
├── docker-compose.yml           # Trino + Hive catalog config
└── demo/
    └── walkthrough.md           # 10-minute live demo script
```

---

## 4. Data Model

### 4.1 Data Source

**Olist Brazilian E-Commerce Dataset** (Kaggle): ~100K real orders from Brazilian marketplace, 2016-2018. Nine related CSV files covering orders, items, products, customers, sellers, reviews, payments, and geolocation.

### 4.2 Tables (Olist → Parquet mapping)

| Parquet Table | Source CSVs | Rows | Purpose |
|---|---|---|---|
| `orders` | olist_orders + olist_order_items + olist_order_payments | ~100K orders, ~113K items | Partitioned by `year/month` — demonstrates partition pruning |
| `products` | olist_products + category_name_translation | ~33K | Nested structs (dimensions, category hierarchy) — shows nested type support |
| `customers` | olist_customers + olist_geolocation | ~100K | Geo columns — demonstrates column projection and geographic queries |
| `reviews` | olist_order_reviews | ~100K | Review text + scores — predicate pushdown on score, text for AI embeddings |
| `sellers` | olist_sellers + olist_geolocation | ~3K | Small dimension table — join target |

### 4.3 Partition Strategy (ADR-002)

- **orders:** partitioned by `year/month` — queries almost always filter by date range
- **reviews:** partitioned by `review_score` — enables fast filtering by rating tier
- **products, customers, sellers:** unpartitioned — small enough to scan fully

### 4.4 Compression (ADR-003)

- **Snappy** for orders and reviews — larger tables, frequent reads, fast decompression
- **Zstd** for customers — better compression ratio, queried less frequently

### 4.5 Data Pipeline (`data/convert.py`)

Python script using `pyarrow` that:
1. Reads Olist CSVs from `data/raw/`
2. Joins related tables (e.g., orders + items + payments into a denormalized orders table)
3. Creates nested structs where appropriate (product dimensions, category hierarchy)
4. Applies partition strategy and compression codec per table
5. Writes Parquet files to `data/parquet/`

This conversion pipeline IS part of the demo — it shows PM understanding of the ETL decisions involved in a format migration.

---

## 5. Presto (Trino) Setup

Single `docker-compose.yml` running Trino with a Hive connector pointing at local Parquet files. One command to start, one to stop.

Trino is the community continuation of Presto — same SQL dialect, same concepts. The ADR will acknowledge the PrestoDB vs Trino lineage.

---

## 6. Business Queries

Six queries, each exercising a different Parquet/Presto capability:

| # | Query | Feature Demonstrated |
|---|---|---|
| 1 | Monthly revenue trend with YoY comparison | Partition pruning on orders |
| 2 | Top products by category with dimension filtering | Nested types + predicate pushdown |
| 3 | Customer cohort retention (repeat purchase rate) | Join efficiency, columnar reads |
| 4 | Review sentiment distribution by product category | Predicate pushdown on review_score |
| 5 | Geographic revenue heatmap by state/quarter | Column projection (3 of 20 cols) |
| 6 | Delivery performance vs. review score correlation | Complex aggregation across tables |

Each query has a companion markdown file with:
- The business question it answers
- Which Parquet/Presto feature it exercises
- `EXPLAIN` output showing pruning/pushdown
- Performance comparison vs. CSV

---

## 7. AI-Era Integration

### 7.1 Natural Language → SQL (NL→SQL)

Python script that:
1. Takes a plain English question
2. Sends Parquet schema + table metadata to Claude API
3. Returns valid Presto SQL
4. Runs the query against Trino, returns results

Example: "Which product categories in São Paulo had the highest revenue in Q4 2017?" → SQL → results.

**PM angle (ADR-004):** Schema-rich formats like Parquet give LLMs enough context (column names, types, nested structures) to generate accurate SQL. CSV headers can't do this.

### 7.2 Review Embedding & Product Similarity

- Presto extracts product feature vectors (category, price band, avg review score, order frequency) + review text
- Generate embeddings from review text for sentiment clustering
- Python cosine similarity search: "Find products similar to X" based on combined structured + text features

**PM angle:** Parquet bridges analytics and ML — same data, same format, no ETL copy step. Review text stored efficiently in Parquet alongside structured data.

### 7.3 Explicit Non-Goals

- No fine-tuning or model training
- No real-time serving layer
- No vector database — simple Python similarity to prove the point

---

## 8. Benchmarks & Cost Model

### 8.1 Format Comparison (`benchmarks/format_comparison.py`)

Runs each of the 6 business queries against CSV, JSON, and Parquet. Captures:
- Query execution time (wall clock)
- Data scanned (bytes read)
- Storage footprint (file size per format)

Auto-generates charts via matplotlib, saved to `benchmarks/results/`, embedded in README.

### 8.2 Cost Model (`docs/cost-model.md`)

Translates benchmarks to dollar projections for a 50TB production dataset:
- Storage costs (S3-style pricing)
- Query costs (bytes-scanned pricing, a la AWS Athena / IBM Analytics Engine)
- Projected annual savings: Parquet vs CSV

Simple table, not a financial model. The artifact that differentiates a PM from an engineer.

---

## 9. Demo Flow

10-minute guided walkthrough (`demo/walkthrough.md`):

1. `docker compose up` — Trino starts in ~30 seconds
2. Show raw Parquet files, point out partition structure on disk
3. Run a business query, show results, show `EXPLAIN` plan
4. Run the same query against CSV — show performance gap
5. Ask a natural language question → generated SQL → results
6. Show cost model — "at production scale, this saves $X/year"
7. `docker compose down` — clean shutdown

---

## 10. README Structure

The README is a product brief, not a setup guide:

```
# Muwalah Commerce: Analytics Modernization

## The Problem
Legacy flat-file analytics can't scale for AI-era workloads.

## The Recommendation
Columnar storage (Parquet) + distributed SQL (Presto) —
with a migration path to AI-native analytics.

## Evidence
### Storage & Performance [links to benchmarks]
### Cost Impact [links to cost model]
### AI Readiness [links to NL→SQL demo, embeddings]

## Architecture Decisions
[Links to each ADR]

## How to Run This
[Setup in 3 commands]

## Key Takeaways
[PM narrative — what I'd recommend to leadership and why]
```

---

## 11. Tech Stack Summary

| Component | Tool | Size |
|---|---|---|
| Query engine | Trino (Docker) | ~1.5GB |
| Data source | Olist (Kaggle) | ~100MB CSV, ~50MB Parquet |
| Data pipeline | Python + pyarrow | minimal |
| Benchmarks | Python + matplotlib | minimal |
| AI: NL→SQL | Python + Claude API | minimal |
| AI: Embeddings | Python + numpy | minimal |
| Orchestration | docker-compose | — |

**Total estimated footprint:** ~1.6GB of 10GB budget.
