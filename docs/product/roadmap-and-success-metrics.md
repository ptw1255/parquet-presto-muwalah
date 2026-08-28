# Roadmap and success metrics

## Evidence-gated roadmap

### Phase 0 — Make current evidence auditable

- Define supported environment matrix and pin reproducibility metadata.
- Add artifact-presence checks; distinguish documented claims from available run output.
- Establish fixed correctness fixtures for conversion, SQL, and generated SQL.
- Exit: a reviewer can reproduce a baseline run or see exactly why not.

### Phase 1 — Reliable first decision loop

- Preflight, synthetic fixture path, progressive setup, specific recovery guidance.
- Run manifests containing code revision, dependency versions, dataset fingerprint, query, warm/cold state, and raw outputs.
- Read-only generated-SQL policy and visible confirmation.
- Exit: first-time evaluators reach a successful representative query with no unresolved safety failures.

### Phase 2 — Workload-specific evidence

- Workload profile, repeated benchmark protocol, correctness checks, confidence/limitation labels.
- Query-class comparisons and accessible raw-result views.
- Exit: benchmark reviewers agree which findings transfer and which do not.

### Phase 3 — Decision economics

- Low/base/high cost assumptions, source dates, one-time migration cost, sensitivity analysis.
- Claim-to-run evidence ledger and exportable decision brief.
- Exit: decision makers can identify variables that change the recommendation.

### Phase 4 — Bounded pilot

- Pilot design for representative non-production data, concurrency, freshness, governance, and operations.
- Compare alternative engines/formats where workload evidence warrants.
- Exit: explicit proceed/change/stop decision; no automatic production rollout.

## Hypotheses

| ID | Hypothesis | Falsification |
|---|---|---|
| H1 | Preflight reduces setup abandonment | Time/failure rate does not improve |
| H2 | Manifests improve evidence trust | Reviewers still misjudge transferability |
| H3 | Workload profiling changes benchmark priorities | Generic and tailored runs lead to same decisions |
| H4 | Visible SQL/telemetry enables safe analyst verification | Correctness errors remain undetected |
| H5 | Sensitivity ranges improve pilot decisions | Users still anchor on a point estimate |

## Metric hierarchy

**North-star candidate:** decision-grade workload claims—correct, reproducible, linked to a representative run, and accepted with limitations by a reviewer. Count alone is insufficient; quality gates apply.

| Type | Metric | Definition |
|---|---|---|
| Leading | Time to first valid query | preflight start → correctness-checked result |
| Leading | Setup recovery rate | dependency failures resolved / failures |
| Leading | Manifest coverage | completed runs with required metadata / runs |
| Leading | Correct benchmark completion | run pairs passing result-equivalence checks |
| Lagging | Decision-grade claim rate | reviewer-accepted claims / claims proposed |
| Lagging | Pilot decision completion | evaluations ending in explicit proceed/change/stop |
| Lagging | Analyst net task time | question → verified answer including correction |
| Guardrail | Semantic query error | generated queries producing wrong interpretation / evaluated queries |
| Guardrail | Unsafe execution blocked | prohibited statements blocked / attempted |
| Guardrail | Non-reproducible claim | claims without rerunnable evidence / claims |
| Guardrail | Setup resource failure | runs failing from resource exhaustion |
| Guardrail | Accessibility task failure | critical evaluation tasks not completed |

Do not set targets before baseline and evaluation protocol approval.

## Instrumentation

Never log raw confidential datasets or unrestricted query results. Default to local run records.

| Event | Properties |
|---|---|
| `preflight_completed` | dependency statuses, environment class, duration bucket |
| `dataset_profiled` | public/synthetic/custom flag, size/schema buckets, fingerprint |
| `conversion_completed` | format, duration, row-count check, error class |
| `benchmark_run_completed` | workload ID, warm/cold, correctness, duration/bytes buckets, manifest ID |
| `query_generated` | question fixture ID, validation result, model/version |
| `query_executed` | read-only policy result, execution outcome, latency/row buckets |
| `claim_linked` | claim type, manifest ID, limitation count |
| `decision_recorded` | proceed/change/stop, evidence-gap categories |

## Experiments

1. Manual guide vs. preflight wizard on a clean supported environment.
2. Benchmark table alone vs. table + manifest + limitation labels; assess reviewer transfer judgments.
3. Generic benchmark suite vs. workload-profiled suite; compare decision confidence and disagreements.
4. Generated result summary with hidden vs. visible SQL/EXPLAIN; measure semantic error detection.
5. Point cost estimate vs. sensitivity range; measure which assumptions reviewers challenge.
6. Cold/warm and repeated-run protocol; quantify variance before publishing a claim.

## Dependencies and gates

- Public/synthetic fixture licensing and deterministic generation.
- Pinned runtime/container/model dependencies.
- Conversion/query correctness oracles.
- SQL parser/policy and read-only execution boundary.
- Environment/resource observability.
- Security and privacy review before custom datasets.
- Architecture, finance, analytics, and accessibility review before pilot recommendation.
