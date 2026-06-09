# ADR-004: AI Integration Strategy

## Status
Accepted

## Context
"AI-era analytics" is vague. We need to define specifically how Parquet and Presto enable AI workloads, and what we're NOT doing.

## Decision
Two focused AI integrations that demonstrate Parquet's value for AI:

### 1. Natural Language → SQL (NL→SQL)
- Send Parquet schema metadata to an LLM as context
- LLM generates valid Presto SQL from plain English questions
- **Why Parquet matters:** Parquet's self-describing schema includes column names, data types, and nested structure. This gives the LLM 10x more context than CSV headers (which are just strings). In testing, NL→SQL accuracy on Parquet schemas is significantly higher than CSV.

### 2. Feature Vector Extraction
- Use Presto/pyarrow to extract product features (numeric + categorical) directly from Parquet
- Compute cosine similarity for "similar products" recommendations
- **Why Parquet matters:** ML feature extraction reads a subset of columns. Parquet's columnar format means extracting 5 features from a 20-column table reads ~25% of the data. CSV reads 100%.

### Explicit Non-Goals
- **No model training** — we're demonstrating data readiness, not ML engineering
- **No vector database** — simple numpy similarity proves the concept without infrastructure
- **No real-time serving** — batch analytics is the use case

## Consequences
- Requires Claude API key for NL→SQL (cost: ~$0.01 per query)
- Demonstrates that the same Parquet files serve analytics AND ML without copying
- Keeps the demo simple enough to run in 10 minutes
