# Cost Model: CSV vs Parquet at Production Scale

Diego's question: "What does this save us at 50TB?"

## Assumptions
- Production dataset: 50 TB (CSV equivalent)
- Cloud storage: $0.023/GB/month (S3 Standard)
- Query pricing: $5.00/TB scanned (Athena / IBM Analytics Engine model)
- Queries per month: 10,000 (Britt's team + automated reports)
- Average query scans 30% of data on CSV, 5% on Parquet (column projection + partition pruning)

## Storage Costs

| Format | Size | Monthly Cost | Annual Cost |
|---|---|---|---|
| CSV | 50 TB | $1,150 | $13,800 |
| Parquet (Snappy) | ~15 TB (70% compression) | $345 | $4,140 |

**Annual storage savings: $9,660 (70%)**

## Query Costs

| Format | Data Scanned/Query | Monthly Scan | Monthly Cost | Annual Cost |
|---|---|---|---|---|
| CSV | 15 TB (30% of 50TB) | 150,000 TB | $750,000 | $9,000,000 |
| Parquet | 2.5 TB (5% of 50TB) | 25,000 TB | $125,000 | $1,500,000 |

**Annual query savings: $7,500,000 (83%)**

*Note: These are theoretical projections based on benchmark ratios. Actual savings depend on query patterns, caching, and reserved capacity pricing.*

## Total Cost of Ownership

| Cost Category | CSV (Annual) | Parquet (Annual) | Savings |
|---|---|---|---|
| Storage | $13,800 | $4,140 | $9,660 |
| Query compute | $9,000,000 | $1,500,000 | $7,500,000 |
| **Total** | **$9,013,800** | **$1,504,140** | **$7,509,660 (83%)** |

## Migration Cost (One-Time)
- Engineering effort: ~2 weeks (conversion pipeline, testing, validation)
- Infrastructure: Trino/Presto cluster setup, ~1 week
- **Payback period: < 1 month**

## Key Insight
The savings compound: smaller files (compression) x fewer columns read (projection) x fewer partitions scanned (pruning) = dramatically lower TCO. Each optimization multiplies the others.

---

*Based on benchmark results from this project. See `benchmarks/results/` for raw data.*
