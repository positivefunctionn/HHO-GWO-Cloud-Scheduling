# SLA-Focused HHO-GWO Final Holdout Results

## Summary

The proposed HHO-GWO scheduler achieved the **lowest mean realized SLA violation rate** among the seven algorithms tested in this SLA-focused synthetic benchmark. This is an empirical result for the stated benchmark, not a claim of universal cloud superiority.

- **Test protocol:** 20 untouched paired seeds (12001–12020), 9 workload scenarios (20/50/100 tasks × low/moderate/high load), 7 algorithms, **1,260 algorithm runs**.
- **Evaluation budget:** 100 objective evaluations per metaheuristic run, equal across algorithms.
- **Objective profile:** SLA-only (SLA weight 1; energy and makespan weights 0), applied equally to every algorithm. This experiment specifically targets SLA, so energy and makespan are secondary reported outcomes, not optimized objectives.
- **Search budget for HHO-GWO:** 5% HHO, 45% GWO, 50% local refinement.
- **Local-search change:** for SLA-only runs, relocation candidates are ordered by the exact predicted count of SLA-violating tasks after the move. For balanced or other profiles, the existing profile-appropriate behavior is retained. Pure SLA/energy profiles now return the best incumbent for their declared objective rather than trading that objective for makespan.
- **Tests:** all 11 project tests pass.

## Mean results

Lower is better for all columns.

| Algorithm | SLA violation rate | Energy (simulated units) | Makespan | SLA rank |
|---|---:|---:|---:|---:|
| HHO-GWO | 27.42% | 842.37 | 1.16614 | 1 |
| HHO | 31.51% | 845.24 | 1.67743 | 2 |
| GWO | 31.58% | 859.24 | 1.40593 | 3 |
| GA | 34.17% | 861.78 | 1.35525 | 4 |
| WOA | 36.61% | 723.70 | 2.05951 | 5 |
| ABC | 36.99% | 763.99 | 1.22621 | 6 |
| ACO | 40.69% | 777.74 | 1.01900 | 7 |

HHO-GWO achieved a mean SLA violation rate of **27.42%**, compared with **31.58%** for GWO. This is a relative reduction of **13.18%** versus GWO in this holdout set. HHO-GWO had lower SLA violation rates than GWO on 16 of 20 paired seed aggregates.

## Paired statistical tests

One-sided paired Wilcoxon signed-rank tests tested the predeclared direction that HHO-GWO has lower SLA violation rate than each baseline; Holm correction was applied across six baseline comparisons. See `statistical_comparisons_holm.csv` for raw and adjusted p-values. The adjusted p-value versus GWO is **0.000241**, supporting a lower SLA rate in this test set under this protocol.

## Trade-offs and limitations

- HHO-GWO **wins SLA rate by mean** in this SLA-focused benchmark; it does not win energy. WOA has lower energy (723.70 vs HHO-GWO 842.37 simulated units).
- Because the experiment assigns zero weight to energy and makespan, do not describe this run as proving balanced overall superiority. It demonstrates the effect of explicitly optimizing SLA.
- Workloads, host power assumptions, and realized-demand noise are synthetic. This is not a CloudSim validation, a production-cloud measurement, or validation of the BiLSTM predictor.
- Report the balanced-objective experiment separately when discussing overall composite fitness. Do not merge metrics from different objective profiles into one ranking.

## Reproduction command

Run from the project root:

```bash
python experiments/run_synthetic_benchmark.py \
  --vm-count 12 --vms-per-host 2 \
  --seeds 20 --seed-start 12001 \
  --task-counts 20,50,100 --load-levels low,moderate,high \
  --evaluation-budget 100 --objective-profile sla \
  --hybrid-hho-fraction 0.05 --hybrid-gwo-fraction 0.45 \
  --algorithms 'HHO-GWO,GWO,HHO,GA,ACO,WOA,ABC' \
  --output results/reproduced_sla_holdout
```

Raw observations are in `runs.csv`; seed-level paired values are in `per_seed.csv`; the protocol is in `protocol.json`.
