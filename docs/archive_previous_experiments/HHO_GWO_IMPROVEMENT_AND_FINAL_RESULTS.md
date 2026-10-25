# HHO-GWO Scheduler: Tuned Algorithm and Independent Results

## Summary

The tuned HHO-GWO scheduler now ranks **1st of 6 algorithms on mean composite fitness** in the independent 12-VM synthetic benchmark. It ranks **2nd on energy** and **2nd on makespan**, while ranking **4th on SLA violation rate**. This is a meaningful improvement in balanced overall performance, but it is not the winner on every metric.

## Algorithm improvements

1. **Global-best retention:** preserve the best schedule found across HHO, GWO, and local refinement rather than returning whichever phase ran last.
2. **Constructive incumbent:** evaluate Best-Fit Decreasing (BFD) as a candidate seed, with its objective call charged to the hybrid's shared 300-evaluation budget.
3. **Iterated local search:** after the metaheuristic phases, spend the remaining budget on guided relocations and bounded multi-task perturbations to escape one-move local optima.
4. **Search budget tuning:** use 20% HHO, 20% GWO, and 60% local refinement in the tested configuration.
5. **Budget parity:** HHO, GWO, HHO-GWO, PSO, and GA each receive a maximum of 300 objective evaluations per run. BFD is deterministic and uses one objective evaluation.

## Independent benchmark protocol

- **Topology:** 12 VMs across 6 hosts (2 VMs per host).
- **Workloads:** 20, 50, and 100 concurrent tasks at low, moderate, and high offered load.
- **Seeds:** 30 paired seeds per scenario, IDs 3001–3030.
- **Total:** 9 scenarios × 30 seeds × 6 algorithms = **1,620 algorithm runs**.
- **Objective:** equal weights for normalized host energy, SLA violation rate, and makespan; the same objective is used for every metaheuristic.
- **Statistics:** per-scenario paired two-sided Wilcoxon tests for HHO-GWO versus each comparator, with Holm adjustment across all 45 scenario-level comparisons.

## Mean results

Lower is better for every metric.

| Algorithm | Composite fitness | Rank | Energy | Rank | SLA violation rate | Rank | Makespan | Rank |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **HHO-GWO** | **0.36981** | **1** | 749.37 | 2 | 0.31315 | 4 | 1.18124 | 2 |
| PSO | 0.37515 | 2 | 837.53 | 4 | **0.24681** | 1 | 1.20701 | 3 |
| HHO | 0.39021 | 3 | **740.22** | 1 | 0.34519 | 5 | 1.55562 | 6 |
| GWO | 0.39072 | 4 | 840.85 | 5 | 0.28778 | 2 | 1.23421 | 5 |
| GA | 0.39653 | 5 | 845.62 | 6 | 0.30152 | 3 | 1.22791 | 4 |
| BFD | 0.43942 | 6 | 788.04 | 3 | 0.51467 | 6 | **0.90442** | 1 |

## What this supports

- HHO-GWO has the **best mean composite fitness**, improving on PSO by about **1.42%** on that metric.
- It has the **second-lowest energy**; HHO uses less energy on average, while HHO-GWO uses about 10.9% less energy than GWO.
- It has the **second-lowest makespan** overall; BFD's makespan is lower, although BFD performs much worse on composite fitness and SLA violation rate.
- SLA is the main remaining weakness: PSO, GWO, and GA have lower mean SLA violation rates than HHO-GWO. We should not describe HHO-GWO as the best on SLA.
- By scenario mean fitness, HHO-GWO ranks first in 4 of 9 scenarios and second in 3 of 9. PSO wins the remaining 5 scenarios; scenario-specific results still vary with workload size and load.
- In paired scenario-level tests after Holm correction, HHO-GWO's mean fitness was significantly better in 5/9 scenarios versus GWO, 3/9 versus PSO, 3/9 versus HHO, 6/9 versus GA, and 5/9 versus BFD. These are scenario-level findings, not a claim that every individual seed improves.

## Limitations and responsible claims

- This is a **synthetic benchmark**, not a real cloud trace or physical energy measurement.
- Actual demand is generated as synthetic noise around predicted demand. The benchmark does **not** validate the BiLSTM forecast model.
- Host capacity, power curves, and SLA definitions are declared simulation assumptions.
- Energy, SLA, and makespan can conflict. The result supports calling HHO-GWO the best **overall on mean composite fitness under this benchmark configuration**, not universally best on every metric or workload.

## Reproduce

From the project root:

```bash
python -m pytest -v
python experiments/run_synthetic_benchmark.py --vm-count 12 --vms-per-host 2 --seeds 30 --seed-start 3001 --objective-profile balanced --hybrid-hho-fraction 0.20 --hybrid-gwo-fraction 0.20 --output results/reproduced_tuned_test
python experiments/analyze_expanded_results.py results/reproduced_tuned_test
```

The remaining 60% of the hybrid evaluation budget is used for local refinement. All metaheuristics share the same maximum of 300 objective evaluations.
