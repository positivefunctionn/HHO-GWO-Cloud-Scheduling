# Reproducibility and artifact audit — final convex-power release (2026-10-25)

## Scope

The host-energy implementation was checked against the intended design. The previous code used a linear utilization-to-power relation despite the design describing a configurable convex curve. The implementation now uses the configurable model `P(u)=P_idle+(P_max-P_idle)*u^alpha` for active hosts, where `u` is aggregate host utilization clipped to [0,1]. The default audited exponent is alpha = 2.0; alpha = 1.0 recovers the linear model. Inactive hosts contribute zero power under this synthetic assumption.

Because the power model changes the balanced objective, the earlier linear-power results are preserved under `results/archive_previous_experiments/linear_power_curve_20261025/` and are not used as the final result. Both final experiments below were rerun using the convex model.

## Software checks

- Environment: Python 3.13.5.
- Unit tests: `python -m unittest discover -s tests -v` — **12/12 passed** after the convex model change.
- Smoke test: `python experiments/run_smoke_test.py` — generated **1,320 schedules** across six algorithms; **1,094 output rows** passed the declared handoff schema check. The risk input is a binary `predicted_overload` fallback, not a calibrated probability.
- Benchmark runner smoke check: a small SLA run completed; its protocol recorded the power exponent and selection-policy metadata, and the generic analyzer validated the complete panel.

## Final experiment A — balanced objective profile

- Output directory: `results/final_convex_balanced/`.
- Seed batches: 9601–9610 and 9701–9710; merged only after validating protocol equality and disjoint seed IDs.
- 7 algorithms × 20 paired seeds × 9 scenarios = **1,260 raw runs**.
- 300 objective evaluations per metaheuristic run; 12 VMs across 6 hosts.
- Objective weights: energy proxy = 1/3, SLA rate = 1/3, makespan = 1/3.
- Host power curve exponent: **alpha = 2.0**.

### Reproduced means

| Algorithm | Composite fitness ↓ | Energy proxy ↓ | SLA rate ↓ | Makespan ↓ |
|---|---:|---:|---:|---:|
| **HHO–GWO** | **0.347109 (#1)** | 696.386992 (#4) | 31.1389% (#3) | **0.997238 (#1 by mean)** |
| ABC | 0.354153 (#2) | 680.711529 (#3) | 32.9000% (#5) | 1.174292 (#3) |
| GWO | 0.359136 (#3) | 731.594140 (#6) | **28.9611% (#1)** | 1.257207 (#5) |
| HHO | 0.360257 (#4) | 675.599335 (#2) | 32.2056% (#4) | 1.473139 (#7) |
| GA | 0.363461 (#5) | 736.672245 (#7) | 29.9167% (#2) | 1.245456 (#4) |
| WOA | 0.366947 (#6) | **647.119581 (#1)** | 36.8444% (#6) | 1.467683 (#6) |
| ACO | 0.378231 (#7) | 705.193661 (#5) | 39.4111% (#7) | 1.023967 (#2) |

### Statistical interpretation

Paired two-sided Wilcoxon tests use the 20 seed-level averages across the nine scenarios; Holm correction is applied within each metric's six baseline comparisons.

- Composite fitness: HHO–GWO's mean is best. Differences versus ACO, WOA, GWO, GA and HHO are significant after correction; the difference versus ABC is **not significant** (adjusted p = 0.142906).
- Makespan: HHO–GWO's mean is best (0.997238 vs ACO's 1.023967). The paired difference is significant under this protocol (adjusted p = 0.007296).
- Energy proxy: WOA has the lowest mean.
- SLA rate: GWO has the lowest mean.

**Fairness caveat:** the balanced HHO–GWO uses an 8% epsilon-constraint policy that selects the lowest-makespan candidate among candidates within 8% of its best composite fitness. This policy is not applied to the single-objective baselines. Disclose this asymmetry; a stronger paper should include a policy ablation or implement comparable selection policies for the baselines.

## Final experiment B — SLA-focused objective profile

- Output directory: `results/final_convex_sla/`.
- 7 algorithms × 20 paired seeds (12001–12020) × 9 scenarios = **1,260 raw runs**.
- 100 objective evaluations per metaheuristic run; 12 VMs across 6 hosts.
- Shared objective weights for all methods: SLA = 1, energy = 0, makespan = 0.
- Hybrid budget: 5% HHO, 45% GWO, 50% local refinement; power exponent alpha = 2.0.

### Reproduced means

| Algorithm | SLA violation rate ↓ | Energy proxy | Makespan |
|---|---:|---:|---:|
| **HHO–GWO** | **27.4167%** | 745.786778 | 1.166136 |
| HHO | 31.5111% | 735.736343 | 1.677435 |
| GWO | 31.5778% | 752.743558 | 1.405929 |
| GA | 34.1667% | 756.483840 | 1.355247 |
| ACO | 40.6889% | 709.698226 | 1.019000 |
| WOA | 36.6111% | **640.210079** | 2.059512 |
| ABC | 36.9944% | 689.915709 | 1.226207 |

HHO–GWO's mean SLA rate is 4.1611 percentage points below GWO's, a **13.1773% relative reduction**. It was lower than GWO on 16 of 20 paired seed-level averages. The predeclared one-sided paired Wilcoxon test, with Holm correction across the six baseline comparisons, gives adjusted p = **0.0002413** versus GWO; the reproduced analysis also found adjusted p < 0.05 against each other listed baseline under this SLA-only protocol.

This does not prove balanced-objective superiority: energy and makespan weights are zero in this experiment. WOA has the lowest secondary energy proxy; ACO has the lowest mean makespan.

## Included audit artifacts

Each final result directory contains raw `runs.csv`, `protocol.json`, runner `summary.csv`, `audited_per_seed.csv`, `audited_metric_summary.csv`, and `audited_paired_tests.csv`. The analyzer rejects duplicate keys and incomplete algorithm × seed × scenario panels before testing. The inferential unit is the seed-level average across the same nine scenarios, not each individual task or scenario row.

Charts are in `docs/figures/`:
- `balanced_composite_fitness.png`
- `balanced_makespan.png`
- `balanced_metric_ranks.png`
- `sla_violation_rate.png`

## Limitations and required future work

1. These are synthetic workloads, not CloudSim Plus or production trace validation.
2. Host power values are declared assumptions; energy values are proxy units, not measured watts, joules, cloud cost, or carbon.
3. The smoke test validates output schema, not the accuracy or calibration of an upstream BiLSTM predictor.
4. The balanced epsilon-constraint selection policy creates a comparator asymmetry; add an ablation or comparable baseline policy.
5. A paper should include the exact code, environment, configuration, seed protocol, raw observations, analysis script and limitations. These results cannot guarantee acceptance by a publisher or research board.
