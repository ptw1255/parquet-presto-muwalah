# ADR-002: Partition Strategy

## Status
Accepted

## Context
Parquet supports Hive-style partitioning, where data is split into directories by column value. Correct partitioning dramatically reduces data scanned; incorrect partitioning creates too many small files or skewed partitions.

## Decision

| Table | Partition Column(s) | Rationale |
|---|---|---|
| orders | year, month | >95% of business queries filter by date range |
| reviews | review_score | Sentiment analysis queries filter by rating tier (1-2 = negative, 4-5 = positive) |
| products | (none) | ~33K rows — full scan is <1 second |
| customers | (none) | ~100K rows — full scan is fast, no dominant filter pattern |
| sellers | (none) | ~3K rows — trivially small |

### Why year/month for orders (not year/quarter or date)?
- **year/month** creates ~24 partitions (2016-2018) — manageable file count
- **year/quarter** creates only ~8 partitions — too coarse for monthly reports
- **date** creates ~700+ partitions — too many small files for 100K orders

### Why review_score for reviews (not date)?
- Review analysis almost always filters by score tier ("show me 1-star reviews")
- 5 partitions (scores 1-5) — clean, balanced split
- Date-based partitioning would create too many small partitions

## Consequences
- Orders queries with date filters skip ~90% of data on average
- Review queries for negative sentiment read only 2 of 5 partitions
- Adding new data requires writing to the correct partition directory
