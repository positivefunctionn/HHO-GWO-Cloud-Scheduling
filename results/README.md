# Results directory guide

## Current source-of-truth results

- `final_convex_balanced/`: fresh 1,260-run balanced-profile benchmark using host-power exponent alpha = 2.0. Contains raw `runs.csv`, `protocol.json`, audited seed aggregates, metric summary and paired tests.
- `final_convex_sla/`: fresh 1,260-run SLA-focused benchmark using the same convex power model and SLA-only objective. Contains raw `runs.csv`, `protocol.json`, runner summary, audited seed aggregates, metric summary and paired tests.

Read `../docs/REPRODUCIBILITY_AUDIT.md` and `../docs/FINAL_PROJECT_RESULTS_REPORT.md` for interpretation. The balanced and SLA profiles are separate experiments and must not be combined into a single ranking.

## Historical artifacts

`archive_previous_experiments/` preserves prior linear-power results and other exploratory runs for traceability. They use earlier objective/model versions and are not the final result set. Do not mix their values with the current convex-power outputs.
