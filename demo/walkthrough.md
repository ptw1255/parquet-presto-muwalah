# Live Demo Walkthrough (10 minutes)

## Prerequisites
- Docker Desktop running
- Olist CSVs in `data/raw/`
- `ANTHROPIC_API_KEY` environment variable set (for NL→SQL)

## Setup (do before the interview)
```bash
# Convert CSV → Parquet
python3 data/convert.py

# Start Trino
docker compose up -d

# Load data into Trino
python3 scripts/load_data.py
python3 scripts/load_orders.py
```

---

## Demo Script

### 1. The Data (1 min)
> "Let me show you the raw data and what we did with it."

```bash
# Show original CSV sizes
ls -lh data/raw/*.csv | awk '{print $5, $9}'

# Show Parquet structure — note the partitions
find data/parquet/orders -type d | head -10

# Size comparison
echo "CSV total:" && du -sh data/raw/
echo "Parquet total:" && du -sh data/parquet/
```

**Talking point:** "73% smaller just from the format change. No data lost."

### 2. A Business Query (2 min)
> "Britt, our business analyst, wants the monthly revenue trend."

```bash
docker exec -i muwalah-trino trino --catalog muwalah --schema main < queries/presto/01_revenue_trend.sql
```

**Then show the EXPLAIN plan:**
```bash
docker exec muwalah-trino trino --execute "EXPLAIN SELECT year, month, SUM(price) FROM muwalah.main.orders WHERE year = 2017 GROUP BY year, month"
```

**Talking point:** "See 'PARTITION_KEY' in the plan — Presto only reads the 2017 partitions. At 50TB, that means scanning 4TB instead of 50TB."

### 3. Product Analytics (1 min)
> "Top products by category, filtering by weight."

```bash
docker exec -i muwalah-trino trino --catalog muwalah --schema main < queries/presto/02_top_products.sql
```

**Talking point:** "The weight filter uses predicate pushdown — Presto skips Parquet row groups where all weights exceed 5000g."

### 4. CSV vs Parquet Performance (2 min)
> "Here's why this matters — same data, three formats."

```bash
python3 benchmarks/format_comparison.py
open benchmarks/results/format_comparison.png
```

**Talking point:** Walk through the three charts. "Column projection is where Parquet really shines — it reads 2 columns out of 19 without touching the others. And partition pruning is 26x faster."

### 5. AI: Natural Language → SQL (2 min)
> "This is the AI-era angle. Britt doesn't need to write SQL."

```bash
python3 queries/ai/nl2sql.py "Which product categories in Sao Paulo had the highest revenue in Q4 2017?"
```

**Talking point:** "The LLM gets the full Parquet schema — column names, types, partition columns. That's why it generates accurate SQL. CSV headers are just strings — they can't tell the model that 'price' is a DOUBLE or that 'year' is a partition key."

### 6. Cost Impact (1 min)
> "For Diego, the platform PM, here's the business case."

Open `docs/cost-model.md` and walk through the TCO table.

**Talking point:** "At 50TB, we're looking at 83% cost reduction — $7.5M annually. The compression, column projection, and partition pruning multiply each other."

### 7. Clean Up (30 sec)
```bash
docker compose down
```

---

## If Asked...

**"Why Trino instead of PrestoDB?"**
> Same SQL, same concepts. Trino is the community fork with faster release cycles. IBM Analytics Engine uses Presto — the skills transfer directly.

**"How would you handle schema evolution?"**
> Parquet supports schema evolution — you can add columns without rewriting data. Presto reads the union of all schemas. That's an ADR we'd write for the migration plan.

**"What about real-time data?"**
> This demo is batch analytics. For real-time, I'd recommend Apache Iceberg on top of Parquet — it adds ACID transactions and streaming support while keeping Parquet as the storage format.
