# Product brief

## WHY: modernization decisions fail before technology does

Teams outgrow flat-file analytics through a chain of costs: broad scans, duplicated transformations, unclear schema, slow investigations, and engineering dependency. Yet a generic “columnar is faster” demo is insufficient. Decision makers need workload-specific evidence, reproducible methods, explicit assumptions, and a migration path that does not confuse laptop results with production economics.

**Evidence:** the repository provides conversion, analytical queries, benchmarks, architecture decisions, a cost model, and an interactive local query flow. **Inference:** its strongest value is decision enablement rather than the runtime itself.

## Product thesis

For an analyst and platform decision maker evaluating a CSV-to-columnar transition, the Muwalah decision lab should turn a representative workload into reproducible technical and economic evidence, then expose which assumptions must be validated before migration.

## Promise

“Move from format opinion to a bounded, inspectable modernization decision.”

## Outcomes

1. Reproduce the current workload and identify its dominant bottleneck.
2. Compare formats using declared data, environment, query, and method.
3. Explore SQL and natural-language query paths with transparent telemetry.
4. Translate results into a decision record, sensitivity range, and next experiment.
5. Prevent demo claims from being mistaken for production guarantees.

## Scope

**Current evidence-backed scope**

- Convert a public e-commerce dataset into Parquet with typed, partitioned datasets.
- Run local Trino tables and sample analytical SQL.
- Generate and execute local model-assisted SQL, then summarize results.
- Benchmark selected read patterns and document architecture/cost reasoning.
- Provide a local walkthrough and startup checks.

**Candidate product scope**

- Preflight and synthetic/demo-data option.
- Reproducibility manifest: commit, environment, dataset fingerprint, query, and run.
- Workload profile and benchmark comparison UI.
- Evidence ledger linking claims to runs.
- Sensitivity-based cost model and migration decision brief.
- Query-generation evaluation set and failure taxonomy.

## Non-goals

- Production data platform, managed service, BI tool, or migration automation.
- Universal proof that one format/engine is optimal.
- Running against confidential or customer datasets by default.
- Claiming production cost/performance from laptop benchmarks.
- Executing generated SQL against write-capable systems.
- Replacing capacity planning, security, governance, or architecture review.

## Principles

1. **Decision first:** every demo step answers a decision question.
2. **Reproducible or labeled anecdotal:** claims link to run conditions.
3. **Representative beats impressive:** optimize for workload fidelity.
4. **Ranges over point certainty:** cost and scale assumptions remain editable.
5. **Safe local boundary:** read-only, public/synthetic data, explicit external dependencies.
6. **Show failure:** invalid SQL, cold model, missing data, and engine startup are product states.
7. **Separate layers:** storage, engine, model, and UX value are evaluated independently.

## Risks

| Risk | Consequence | Response |
|---|---|---|
| Demo benchmark overgeneralization | Unsound migration decision | Reproducibility manifest and external-validation gate |
| Missing generated evidence | Claims cannot be audited | Run ledger and artifact presence checks |
| Model-generated invalid/unsafe SQL | Lost trust or unintended execution | Read-only parser/policy, evaluation suite, confirmation |
| Complex local prerequisites | Demo abandonment | Preflight, progressive setup, fixtures |
| Dataset mismatch | Irrelevant conclusions | Workload profile and representativeness scorecard |
| “latest” container drift | Non-reproducible behavior | Pin versions as a future engineering decision |
| Cost model false precision | Misleading business case | sensitivity ranges and source dates |

## Dependencies

Docker, Python packages, local model runtime, model availability, Trino image, public dataset access, sufficient local resources, and platform-specific shell behavior. Current setup is documented in [`docs/getting-started.md`](../getting-started.md); product claims must state which dependencies were active.

## Open decisions

Which workload archetypes to support, which benchmark methodology is credible, how to package a legal redistribution-safe fixture, which SQL safety policy precedes broader use, and what evidence is sufficient to advance from lab to production pilot.
