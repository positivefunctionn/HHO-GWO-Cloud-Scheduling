# SLA-focused results — convex host-power model

## Summary

The proposed HHO–GWO scheduler achieved the lowest mean realized SLA violation rate among the seven methods in this SLA-focused synthetic benchmark. This experiment is separate from the balanced objective experiment.

## Protocol

- 20 paired seed IDs (12001–12020), 9 synthetic scenarios, 7 algorithms, **1,260 algorithm × seed × scenario runs**.
- 100 objective evaluations per metaheuristic run.
- Shared objective profile for every algorithm: SLA weight = 1; energy and makespan weights = 0.
- Hybrid budget: 5% HHO, 45% GWO, 50% local refinement.
- Host power is calculated with the configurable convex model `P(u) = P_idle + (P_max - P_idle) * u^2` for active hosts. It is a proxy, not measured hardware power. Because energy has zero weight in this experiment, the power curve does not guide the SLA-only search objective, but it changes the secondary energy metric reported below.

## Mean results

| Algorithm | SLA violation rate ↓ | Energy proxy | Makespan | SLA rank |
|---|---:|---:|---:|---:|
| **HHO–GWO** | **27.42%** | 745.79 | 1.16614 | **1** |
| HHO | 31.51% | 735.74 | 1.67743 | 2 |
| GWO | 31.58% | 752.74 | 1.40593 | 3 |
| GA | 34.17% | 756.48 | 1.35525 | 4 |
| WOA | 36.61% | **640.21** | 2.05951 | 5 |
| ABC | 36.99% | 689.92 | 1.22621 | 6 |
| ACO | 40.69% | 709.70 | 1.01900 | 7 |

HHO–GWO's mean SLA violation rate is 4.16 percentage points below GWO's, a 13.18% relative reduction. It was better than GWO on 16 of 20 paired seed-level averages.

## Paired statistical tests

One-sided paired Wilcoxon signed-rank tests evaluated the predeclared direction HHO–GWO < baseline, using seed-level averages across the nine scenarios. Holm correction was applied across the six baseline comparisons. The adjusted p-value versus GWO is **0.000241**. The reproduced analysis also found an adjusted p-value below 0.05 against each of the other five baselines under this SLA-only protocol. See `../results/final_convex_sla/audited_paired_tests.csv`.

## Limitations

- This supports an SLA-focused result on the stated synthetic workload, not balanced-objective superiority.
- WOA has lower mean energy proxy; ACO has lower mean makespan in this profile.
- Workloads and host-power parameters are synthetic assumptions.
- No CloudSim Plus, production trace, measured-energy, or BiLSTM accuracy validation is claimed.

## Reproduction

See `START_HERE.md`. Raw runs, protocol, runner summary, audited seed aggregates, metric summary and paired tests are in `../results/final_convex_sla/`.
