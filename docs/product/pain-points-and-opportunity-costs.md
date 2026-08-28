# Pain points and opportunity costs

Ratings are prioritization hypotheses. Measure on the target workload before using them in a business case.

| Pain | Expected frequency | Severity | Consequence chain | Proxy |
|---|---:|---:|---|---|
| Full-scan/column waste | Repeated query | 4 | excess I/O → latency/cost → narrower analysis | bytes scanned per answered question |
| Manual cross-file joins | Weekly/daily | 4 | analyst work → errors → engineering request → delay | touch time and handoffs |
| Schema ambiguity | Each ingestion/change | 5 | type drift → late failure → dashboard distrust | schema-related failures |
| Unreproducible benchmark | Each review | 5 | headline claim → challenge → rerun/rework → delayed decision | claims with complete manifests |
| Setup complexity | First run / environment change | 4 | dependency failure → troubleshooting → abandonment | time to first successful query |
| Generated SQL uncertainty | Each NL query | 5 | plausible SQL → wrong answer → decision harm | execution and semantic correctness |
| Cost-model false precision | Each business case | 4 | point assumption → misleading savings → credibility loss | variables with ranges/source dates |
| Production-transfer gap | Pilot transition | 5 | laptop result generalized → under-designed platform | pilot criteria passed |

## Opportunity-cost formulas

Use measured inputs only:

- **Analyst delay:** `questions × (baseline_answer_minutes - candidate_answer_minutes)`
- **Engineering dependency:** `requests_escalated × median_engineering_touch_minutes`
- **Scan efficiency:** `baseline_bytes_scanned - candidate_bytes_scanned` by query class
- **Storage projection:** `logical_data_size × compression_ratio_range × storage_unit_cost`
- **Compute projection:** `queries × scanned_bytes × engine_unit_cost`, with concurrency and cache assumptions
- **Decision evidence cost:** `reruns + review_rework + environment_debug_minutes`
- **NL-to-SQL net value:** `manual_SQL_minutes - (generation + verification + correction minutes)`
- **Migration payback:** `(one_time_migration + training + dual_run + risk_reserve) / monthly_validated_savings`

Every formula requires source date, owner, low/base/high values, and sensitivity. A laptop result is not a production coefficient without validation.

## Risks of inaction

1. Flat-file pain compounds as workload complexity grows.
2. Analysts continue trading question scope for turnaround time.
3. Uncommitted generated results weaken auditability of existing claims.
4. Model-assisted query enthusiasm can outpace correctness controls.
5. Architecture decisions remain polarized between anecdote and vendor claims.

## Prioritization

| Opportunity | Confidence | Rationale |
|---|---|---|
| Reproducibility manifest/artifact check | High | Current evidence gap is directly observable |
| First-run preflight and failure guidance | High | Many external dependencies are documented |
| Query semantic evaluation | High | Generated SQL is a core trust risk |
| Workload profiler | Medium | Strong decision value; target inputs unknown |
| Cost sensitivity tool | Medium | Existing cost model provides a base |
| Production pilot automation | Low | Premature before representative evidence |
