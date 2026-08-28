# Analytics modernization decision-lab portfolio

## WHY this portfolio exists

Storage-format and query-engine choices are not valuable because they are technically interesting. They matter when decision makers can connect workload pain to reproducible evidence, understand migration tradeoffs, and choose a bounded next step. This repository is best treated as a local decision lab—not as evidence of a production migration.

| Artifact | Decision supported |
|---|---|
| [Product brief](product-brief.md) | Thesis, scope, non-goals, principles, and risk |
| [Users and JTBD](users-and-jtbd.md) | Analyst, platform-decision, operator, and reviewer needs |
| [Value proposition](value-proposition.md) | Alternatives, differentiation, evidence, assumptions |
| [Pain points and opportunity costs](pain-points-and-opportunity-costs.md) | Prioritization and formulas without invented actuals |
| [Wireframes](wireframes.md) | Guided decision and query journeys across states |
| [Roadmap and success metrics](roadmap-and-success-metrics.md) | Phases, hypotheses, telemetry, experiments, dependencies |

## Evidence discipline

- **Evidence:** runnable conversion, benchmark, Trino, query, and local NL-to-SQL paths exist in [`data/convert.py`](../../data/convert.py), [`benchmarks/format_comparison.py`](../../benchmarks/format_comparison.py), [`docker-compose.yml`](../../docker-compose.yml), [`queries/presto/`](../../queries/presto/), and [`muwalah.py`](../../muwalah.py).
- **Evidence:** architecture and cost arguments are documented in [`docs/adr/`](../adr/) and [`docs/cost-model.md`](../cost-model.md).
- **Evidence gap:** generated benchmark artifacts are not committed under `benchmarks/results/`; documentation claims are therefore not repeated here as independently verified actuals.
- **Inference:** the coherent product is an evaluation workflow connecting business workload, technical proof, and migration decision.
- **Hypothesis:** guided reproducibility and uncertainty labels improve decision quality.

No production scale, cost saving, user adoption, model accuracy, or migration outcome is fabricated.
