# ADR-001: Why Apache Parquet

## Status
Accepted

## Context
Muwalah Commerce stores analytics data in CSV files. As data volume grows and AI workloads emerge, we need a storage format that supports:
- Fast analytical queries (column-oriented reads)
- Schema enforcement (self-describing, typed)
- Efficient storage (compression, encoding)
- Ecosystem compatibility (Presto, Spark, pandas, ML tools)
- AI readiness (rich metadata for LLM-based query generation)

## Options Considered

### CSV (status quo)
- Universal compatibility
- No schema enforcement — type errors surface in dashboards
- No column projection — reads entire row for every query
- No compression — storage costs grow linearly
- AI: column headers only, no types — LLMs generate incorrect SQL

### JSON
- Semi-structured, supports nesting
- Row-oriented — same read amplification as CSV
- Larger on disk than CSV (key repetition)
- AI: better than CSV (types inferrable), worse than Parquet

### Apache Parquet
- Columnar — reads only the columns a query needs
- Self-describing schema with types, nesting, and metadata
- Built-in compression (Snappy, Zstd, etc.)
- Native support in Presto/Trino, Spark, pandas, pyarrow
- AI: full schema with types gives LLMs high-accuracy SQL generation

### Apache ORC
- Similar benefits to Parquet
- Stronger in Hive ecosystem, weaker in broader ecosystem
- Less adoption in Python/ML tooling

## Decision
**Apache Parquet.** Broadest ecosystem support across both analytics engines (Presto, Spark) and ML/AI tools (pandas, pyarrow, scikit-learn). The self-describing schema is critical for the NL→SQL use case.

## Consequences
- Migration required: CSV → Parquet conversion pipeline
- Team needs to learn partition strategy and compression tuning
- Schema changes require intentional evolution (not just adding a CSV column)
- Significant reduction in storage and query costs at scale
