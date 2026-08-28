# Users and jobs-to-be-done

## Primary users

### Platform decision maker

- **Context:** must justify or reject a modernization investment under uncertain future scale.
- **Trigger:** rising query latency/cost, AI-readiness initiative, reliability issue, or architecture review.
- **Functional job:** compare alternatives and define a low-risk migration step.
- **Emotional job:** feel evidence-backed rather than sold a technology narrative.
- **Social job:** communicate tradeoffs credibly to finance, engineering, and analytics.
- **Repository evidence:** PM persona and decision criteria exist in [`docs/user-personas.md`](../user-personas.md).

### Business analyst / evaluation partner

- **Context:** repeats revenue, category, geography, delivery, and review analysis.
- **Trigger:** a question exceeds the flat-file workflow or requires joins.
- **Functional job:** answer a business question quickly and verify the result.
- **Emotional job:** trust that speed did not trade away correctness.
- **Evidence:** six business queries and interactive prompt exist under [`queries/presto/`](../../queries/presto/) and [`muwalah.py`](../../muwalah.py).

## Secondary users

- **Data engineer / demo operator:** needs deterministic setup, observability, teardown, and troubleshooting.
- **Architecture reviewer:** needs assumptions, alternatives, risks, and repeatable evidence.
- **AI evaluation owner:** needs generated-SQL validity, semantic correctness, latency, and failure data.

## Negative users

- Production operators expecting support, security hardening, HA, governance, or SLAs.
- Teams needing evidence for unrepresented workloads without rerunning on representative data.
- Anyone proposing to send confidential data to an unreviewed model.
- Users expecting unrestricted generated SQL execution.

## JTBD statements

1. **When** flat-file analytics becomes painful, **I want to** characterize the workload before choosing technology, **so I can** test the actual bottleneck.
2. **When** a benchmark shows improvement, **I want to** inspect environment and method, **so I can** judge whether the evidence transfers.
3. **When** leadership asks for a business case, **I want to** vary scale and cost assumptions, **so I can** present a range rather than false precision.
4. **When** an analyst asks a natural-language question, **I want to** see generated SQL, results, and timing, **so I can** verify rather than blindly trust.
5. **When** setup fails, **I want to** know which dependency failed and preserve progress, **so I can** recover without restarting blindly.
6. **When** the lab is promising, **I want to** define a production pilot gate, **so I can** learn without prematurely committing.

## Stories

| Story | Acceptance intent |
|---|---|
| As a decision maker, I want a workload profile | Data size, query shapes, concurrency, freshness, and constraints are explicit |
| As a reviewer, I want reproducible claims | Each claim links to run manifest and raw output |
| As an analyst, I want explainable query results | SQL, table, source dataset, timing, and warnings remain visible |
| As an operator, I want preflight | Missing Docker/model/data/resources produce specific recovery steps |
| As a security reviewer, I want a hard boundary | Read-only execution and public/synthetic data are enforced |

## Journey

| Stage | Question | Desired progress | Current evidence / gap |
|---|---|---|---|
| Frame | “What hurts and why now?” | Baseline workload and pain | Personas/docs; no captured baseline workflow |
| Prepare | “Can I reproduce this?” | Preflight and dataset provenance | Detailed guide; manual prerequisites |
| Convert | “What changed in storage?” | Schema, partition, compression artifact | Conversion code exists |
| Query | “Does it answer representative questions?” | Correct result and explain plan | Query set and telemetry exist |
| Compare | “How much/why?” | Controlled benchmark with raw results | Benchmark code; generated results absent |
| Decide | “Should we pilot?” | Decision record, sensitivity, risks | ADRs/cost doc; no unified evidence ledger |
| Pilot | “Does it transfer?” | Representative non-production validation | Not current scope |

## Forces of progress

| Push | Pull | Habit | Anxiety |
|---|---|---|---|
| Slow scans; schema issues; engineering queues | Faster queries; typed schema; shared analytics/AI format | CSV familiarity; spreadsheets; existing scripts | Migration cost; benchmark bias; operational complexity; lock-in |

## Research

- Observe one analyst workflow from question to validated answer.
- Interview decision makers using a recent architecture choice and evidence expectations.
- Run benchmark-review sessions where participants challenge method and transferability.
- Test first-run setup on clean supported environments.
- Evaluate natural-language queries with a fixed synthetic question set and human-reviewed expected semantics.
