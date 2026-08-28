# Value proposition

## Canvas

| Decision team | Decision lab |
|---|---|
| **Jobs:** profile workload, compare options, answer queries, build business case, plan pilot | **Services:** conversion, Trino queries, benchmarks, local NL-to-SQL, ADRs, proposed evidence ledger |
| **Pains:** broad scans, weak schema, manual joins, demo setup, unverifiable claims, cost uncertainty | **Relievers:** typed columnar data, representative query set, manifests, telemetry, sensitivity ranges |
| **Gains:** faster insight path, defensible decision, transferable learning, bounded risk | **Creators:** guided journey, claim-to-run traceability, pilot gate, failure diagnostics |

## Alternatives

| Alternative | Why it wins | Decision-lab differentiation |
|---|---|---|
| Keep CSV + scripts | Lowest migration cost | Quantify where it stops being sufficient |
| pandas/DuckDB local analytics | Simple and productive | Compare workload fit rather than assume distributed engine |
| Managed warehouse/lakehouse trial | Production-like capabilities | Local lab offers low-cost concept isolation |
| Vendor benchmarks | Easy headline comparison | Reproduce on declared workload and environment |
| Build a one-off POC | Highly tailored | Reusable evidence structure and decision gates |
| Architecture memo only | Fast to circulate | Pair rationale with executable proof |

Parquet + Trino is the repository’s chosen demonstration. A credible product must keep alternatives visible and allow evidence to reject the initial thesis.

## Differentiation hypothesis

The lab’s wedge is the chain from representative business question → transparent storage/query behavior → reproducible run → sensitivity-aware decision. Neither a tutorial nor a benchmark alone completes that chain.

## Proof currently available

- Conversion and partition decisions are executable and documented.
- SQL workload and interactive terminal are inspectable.
- Startup, dataset overview, query timing, result summary, and pruning telemetry are represented in [`muwalah.py`](../../muwalah.py).
- ADR and cost-model documents provide decision rationale.
- **Evidence gap:** generated benchmark outputs referenced by the root README are absent from the clone; performance and cost claims require rerun/verification before reuse.

## Assumptions to test

| Assumption | Experiment | Signal |
|---|---|---|
| Representative queries are sufficient for a first decision | Workload mapping review | Material query shapes covered |
| Guided setup improves evaluation completion | Baseline vs. preflight prototype | Fewer unresolved setup failures |
| Run manifests improve trust | Blind claim review | Higher correct transferability judgment |
| NL-to-SQL adds analyst value | Fixed question study | Correctness and time improve after verification cost |
| Sensitivity ranges improve business cases | Decision-maker test | Fewer point-estimate objections, clearer pilot gate |

## Value boundary

The lab supports evaluation. It does not prove production performance, operating cost, model correctness, security posture, or organizational ROI.
