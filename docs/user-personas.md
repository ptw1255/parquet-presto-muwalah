# User Personas

Two personas frame every design decision in this project.

## Britt — Business Analyst

**Role:** Commercial team analyst at Muwalah Commerce, São Paulo

**Daily work:** Runs 10-15 queries/day for leadership — revenue trends, category performance, delivery SLA compliance, customer retention.

**Today's pain:**
- Queries on CSV files take minutes, time out on large date ranges
- Can't join across datasets without manual Excel work
- Asks data engineering for help weekly

**What success looks like:**
- Self-service queries that return in seconds
- Slice by geography, time, and category without waiting
- Confidence the numbers are correct

**AI-era need:** Ask questions in plain language ("why did returns spike in Rio last month?") instead of writing SQL from scratch.

**Key jobs-to-be-done:**
| Job | Today | Target |
|---|---|---|
| Weekly revenue report by region | 2 hours | 5 minutes |
| Investigate leadership-flagged anomalies | Files a ticket | Self-service |
| Product trend analysis for purchasing | Gut feel | Data-backed |

**Britt validates:** Business queries, NL→SQL demo, query performance benchmarks.

---

## Diego — Data Platform PM

**Role:** Owns the analytics infrastructure roadmap at Muwalah Commerce

**Daily work:** Evaluates build-vs-buy, format migrations, query engine choices. Balances cost, performance, and team capability.

**Today's pain:**
- CSV-based pipeline breaks when data volume grows
- No schema enforcement — data quality issues surface in dashboards
- Team can't adopt ML tools because data isn't in a consumable format

**What success looks like:**
- Storage format that scales and self-documents (schema)
- Compresses well (lower cloud costs)
- Serves both analytics and AI workloads without a separate ETL

**Decision criteria:** TCO reduction, query performance, schema evolution support, ecosystem compatibility (Presto, Spark, pandas), AI readiness.

**Key jobs-to-be-done:**
| Job | Needs |
|---|---|
| Build the business case for migration | Benchmark data, cost projections |
| Choose the right format and engine | Comparative analysis, ADRs |
| De-risk the migration | Proof-of-concept on real data |

**Diego validates:** ADRs, cost model, format comparison, conversion pipeline.
