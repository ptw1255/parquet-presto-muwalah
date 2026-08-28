# Muwalah Commerce: Analytics Modernization

**A product manager's case for Apache Parquet + Presto in the AI era.**

This project demonstrates how a mid-size e-commerce company should modernize its analytics stack — moving from legacy CSV flat files to columnar storage with a distributed SQL engine. Built with real data ([Olist Brazilian E-Commerce](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)), running entirely on a laptop.

---

## The Problem

Muwalah Commerce's analytics team runs on CSV files. As data grows and AI-driven insights become table stakes, this breaks down:

- **Slow queries** — every query reads every column, every row
- **High storage costs** — no compression, data duplicated across teams
- **No AI readiness** — CSV headers are untyped strings; LLMs can't generate reliable SQL from them
- **No schema enforcement** — type errors surface in dashboards, not at ingestion

## The Recommendation

**Apache Parquet** (columnar storage) + **Presto/Trino** (distributed SQL):

| Capability | CSV (Today) | Parquet + Presto (Proposed) |
|---|---|---|
| Column projection | Reads all columns | Reads only queried columns |
| Partition pruning | Full table scan | Skips irrelevant partitions |
| Compression | None | 73% smaller (Snappy/Zstd) |
| Schema | Untyped headers | Self-describing, typed |
| AI readiness | Poor | LLMs generate accurate SQL from schema |
| Cost at 50TB | $9M/year | $1.5M/year |

---

## Evidence

### Storage & Performance

Real benchmarks on the Olist dataset (100K+ orders, 5 tables):

![Format Comparison](benchmarks/results/format_comparison.png)
![Storage Comparison](benchmarks/results/storage_comparison.png)

**Key findings:**
- Parquet partition pruning is **26x faster** than CSV for filtered reads
- Column projection is **3.5x faster** than CSV
- Storage: **120 MB → 32 MB** (73% reduction)

Full benchmark data: [`benchmarks/results/benchmark_results.json`](benchmarks/results/benchmark_results.json)

### Cost Impact

At production scale (50TB), Parquet reduces total cost of ownership by **83%** — from $9M to $1.5M annually. The savings compound: compression x column projection x partition pruning.

Full analysis: [`docs/cost-model.md`](docs/cost-model.md)

### AI Readiness

**Natural Language → SQL:** Ask a question in English, get Presto SQL back. Works because Parquet schemas give LLMs column names, types, and partition structure.

```
$ python3 queries/ai/nl2sql.py "Top 5 categories by revenue in Sao Paulo, Q4 2017?"
→ Generates valid Presto SQL → Returns results
```

**Product Similarity:** Feature vectors extracted directly from Parquet feed a similarity engine — no separate ML pipeline or ETL step.

Details: [`docs/adr/004-ai-integration.md`](docs/adr/004-ai-integration.md)

---

## Architecture Decisions

| ADR | Decision | Rationale |
|---|---|---|
| [001 — Why Parquet](docs/adr/001-why-parquet.md) | Parquet over CSV, JSON, ORC | Broadest ecosystem + AI readiness |
| [002 — Partition Strategy](docs/adr/002-partition-strategy.md) | Orders by year/month, reviews by score | Matches >95% of query patterns |
| [003 — Compression](docs/adr/003-compression-codec.md) | Snappy (hot), Zstd (cold) | Balance speed vs. ratio by access pattern |
| [004 — AI Integration](docs/adr/004-ai-integration.md) | NL→SQL + feature extraction | Proves Parquet as bridge between analytics and ML |

---

## User Personas

This project is designed around two users: [full personas doc](docs/user-personas.md)

- **Britt (Business Analyst)** — Runs daily queries, needs speed and self-service. Validates: queries, NL→SQL, benchmarks.
- **Diego (Data Platform PM)** — Builds the business case for migration. Validates: ADRs, cost model, conversion pipeline.

## Product portfolio

The [product portfolio index](docs/product/README.md) extends the technical demonstration into an evidence-led product strategy. It includes a [product brief](docs/product/product-brief.md), [users and jobs-to-be-done](docs/product/users-and-jtbd.md), [value proposition](docs/product/value-proposition.md), [pain and opportunity-cost analysis](docs/product/pain-points-and-opportunity-costs.md), [wireframes](docs/product/wireframes.md), and [roadmap and success metrics](docs/product/roadmap-and-success-metrics.md).

These artifacts distinguish implemented repository behavior, documented claims, inference, and hypotheses. Generated benchmark outputs are not treated as committed evidence when absent from the repository.

---

## How to Run This

For a detailed walkthrough of every step, see the [Getting Started Guide](docs/getting-started.md).

**Prerequisites:** Docker Desktop, Python 3.10+, [Olist dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) downloaded to `data/raw/`

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Convert CSV → Parquet (shows compression + partitioning)
python3 data/convert.py

# 3. Start Trino + load data
docker compose up -d
python3 scripts/load_data.py
python3 scripts/load_orders.py

# 4. Run a business query
docker exec -i muwalah-trino trino --catalog muwalah --schema main < queries/presto/01_revenue_trend.sql

# 5. Run benchmarks
python3 benchmarks/format_comparison.py

# 6. Try NL→SQL (requires ANTHROPIC_API_KEY)
python3 queries/ai/nl2sql.py "What were the top categories by revenue in 2017?"

# 7. Shut down
docker compose down
```

Full demo script: [`demo/walkthrough.md`](demo/walkthrough.md)

---

## Key Takeaways

If I were advising Muwalah Commerce's leadership:

1. **Migrate to Parquet immediately.** The conversion is a one-time cost; the savings are permanent and compound with data growth.

2. **Start with Presto/Trino for analytics.** It speaks standard SQL (low learning curve), reads Parquet natively, and scales from laptop to cluster.

3. **Parquet is your AI on-ramp.** The same files that serve dashboards can feed ML pipelines and LLM-based query tools — no separate data copy needed.

4. **Partition and compress intentionally.** The wrong partition strategy wastes the format's advantages. Invest a week in schema design; it pays for itself in the first month.

---

## Tech Stack

| Component | Tool |
|---|---|
| Storage format | Apache Parquet |
| Query engine | Trino (Presto-compatible) |
| Data pipeline | Python + pyarrow |
| AI: NL→SQL | Claude API + Parquet schema |
| AI: Similarity | numpy cosine similarity |
| Benchmarks | pandas + matplotlib |
| Infrastructure | Docker Compose |

---

*Built by Parker Wall as a product management portfolio project.*
