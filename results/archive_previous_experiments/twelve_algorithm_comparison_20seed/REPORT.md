# Twelve-Algorithm Cloud Scheduling Comparison

## Protocol

- Synthetic benchmark only; not a real-cloud trace, production performance claim, or validation of the BiLSTM predictor.
- 12 VMs across 6 hosts; 20, 50, and 100 tasks; low, moderate, and high offered load.
- 20 paired seeds (6001–6020), 9 workload scenarios, and 12 algorithms: 2,160 algorithm/scenario/seed runs.
- The original eight algorithms were filtered to the same 20 seeds; DE, WOA, ABC, and NSGA-II were run on those exact seeds and scenarios.
- All metaheuristics used a maximum of 300 objective evaluations per run; each used exactly 300 in this experiment. BFD is deterministic and used one objective evaluation.
- Shared balanced objective: equal weights for normalized energy, SLA violation rate, and makespan. Lower is better for all four metrics.
- Statistical tests compare HHO-GWO against each competitor on paired scenario/seed rows using two-sided Wilcoxon tests; Holm correction is applied across the 11 competitor comparisons separately for each metric.

## Mean results (180 scenario/seed pairs per algorithm)

| Algorithm | Composite fitness | Energy | SLA violations | Makespan |
|---|---:|---:|---:|---:|
| BFD | 0.43592 | 786.64 | 50.58% | 0.90099 |
| GWO | 0.39210 | 832.93 | 29.73% | 1.25237 |
| HHO | 0.39148 | 748.17 | 34.55% | 1.51879 |
| HHO-GWO | 0.36619 | 762.17 | 29.58% | 1.13041 |
| PSO | 0.37575 | 835.22 | 24.84% | 1.23013 |
| GA | 0.39718 | 845.49 | 30.23% | 1.24110 |
| SA | 0.38774 | 773.60 | 35.57% | 1.07419 |
| ACO | 0.40894 | 776.85 | 42.22% | 1.01576 |
| DE | 0.39656 | 757.82 | 38.40% | 1.19869 |
| WOA | 0.39590 | 718.15 | 39.56% | 1.42165 |
| ABC | 0.38984 | 754.88 | 37.06% | 1.15803 |
| NSGA-II | 0.39508 | 750.33 | 38.54% | 1.20764 |

## HHO-GWO ranking

- **Composite fitness: 1/12.** Best mean: HHO-GWO (0.36619).
- **Energy consumption: 6/12.** Best mean: WOA (718.15).
- **SLA violation rate: 2/12.** Best mean: PSO (24.84%).
- **Makespan: 4/12.** Best mean: BFD (0.90099).

## Main finding

HHO-GWO ranked **first in mean composite fitness** (0.36619), approximately **2.55% lower than PSO** (0.37575). On the paired tests, HHO-GWO had a lower composite-fitness score than each of the other 11 algorithms, with Holm-adjusted p < 0.05 for every comparison.

HHO-GWO ranked **second for SLA violation rate** (29.58%); PSO was best at 24.84%. HHO-GWO ranked sixth for energy and fourth for makespan. Thus the evidence supports a strong overall-score result for this benchmark, not a win on every individual metric.

## Statistical detail

- The full paired comparison table is `paired_comparisons.csv`, including per-metric means, paired differences, win/loss pair counts, raw p-values, Holm-adjusted p-values, and significance flags.
- Composite fitness: HHO-GWO outperformed all 11 alternatives with Holm-adjusted p < 0.05.
- Energy: differences versus HHO, DE, WOA, ABC, and NSGA-II were not statistically significant after Holm correction; WOA had the lowest observed mean energy.
- SLA: PSO had significantly fewer violations than HHO-GWO; differences versus GWO and GA were not significant after correction.
- Makespan: BFD, SA, and ACO had lower observed means than HHO-GWO; HHO-GWO was faster than several metaheuristics, but not all baselines.

## Limitations and interpretation

- The task generator, host power values, and capacity model are synthetic assumptions.
- NSGA-II searches the energy/SLA/makespan objectives as a multiobjective optimizer; to report one schedule in this head-to-head table, the selected candidate is the best observed under the shared balanced score.
- Results depend on the workload generator, objective definition, parameter settings, and evaluation budget. The test does not establish that HHO-GWO is universally superior or will win on CloudSim or real workloads.
- Use these findings as a defensible benchmark result and future-work direction, not as a claim of universal optimality.
