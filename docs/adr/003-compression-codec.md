# ADR-003: Compression Codec Selection

## Status
Accepted

## Context
Parquet supports multiple compression codecs. The choice affects read speed, write speed, compression ratio, and CPU cost. The right codec depends on the access pattern.

## Options Considered

| Codec | Compression Ratio | Read Speed | Write Speed | CPU Cost |
|---|---|---|---|---|
| None | 1x | Fastest | Fastest | None |
| Snappy | ~2-4x | Very fast | Very fast | Low |
| Zstd | ~3-6x | Fast | Moderate | Medium |
| Gzip | ~3-5x | Slow | Slow | High |

## Decision

| Table | Codec | Rationale |
|---|---|---|
| orders | Snappy | High-frequency reads, fast decompression critical |
| reviews | Snappy | Frequently queried for sentiment analysis |
| customers | Zstd | Queried less often, better compression ratio saves storage |
| products | Snappy | Small table, default fast codec |
| sellers | Snappy | Small table, default fast codec |

## Consequences
- Snappy tables: ~2-3x compression, sub-millisecond decompression overhead
- Zstd tables: ~4-5x compression, slightly higher CPU on read
- At 50TB production scale, the storage difference between Snappy and Zstd on customers alone would save ~$500/year (see cost-model.md)
