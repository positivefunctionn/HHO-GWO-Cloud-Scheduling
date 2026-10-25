# HHO-GWO comparison against guide-requested algorithms (PSO excluded)

## Executive result

In this synthetic benchmark, the proposed HHO-GWO scheduler achieved the lowest mean balanced composite fitness among 13 methods. This is a result for the tested simulation setup, not proof of universal superiority or production-cloud performance. The benchmark intentionally excludes PSO, as requested.

## Experimental protocol

- 13 methods: FCFS, Round Robin, BFD, standalone GWO, standalone HHO, proposed HHO-GWO, GA, SA, ACO, DE, WOA, ABC, and NSGA-II.
- 9 synthetic workload scenarios: 20, 50, and 100 tasks, each at low, moderate, and high offered load.
- 10 paired random seeds per scenario (seed IDs 6001–6010); same generated tasks and evaluation rules across methods.
- 1,170 algorithm runs total (13 methods × 9 scenarios × 10 seeds).
- Metaheuristics: 100 objective evaluations per run; deterministic baselines FCFS, Round Robin and BFD use one direct objective evaluation.
- Equal balanced objective weights: one-third energy, one-third SLA violation rate, one-third makespan after the benchmark’s declared normalization.
- Realized metrics are evaluated using noisy synthetic actual demand; this is not validation of the project’s BiLSTM predictor or CloudSim.
- Statistical tests use paired per-seed means across nine scenarios; two-sided Wilcoxon signed-rank tests with Holm correction within each metric across 12 hybrid-vs-competitor comparisons.

## Overall results

Lower is better for all four metrics. Energy values are in the synthetic model’s units; SLA is a proportion of tasks. Rankings are within this run.

| Algorithm | Composite fitness (rank) | Energy (rank) | SLA rate (rank) | Makespan (rank) |
|---|---:|---:|---:|---:|
| HHO-GWO | 0.38429 (#1) | 760.88881 (#5) | 34.60% (#6) | 1.18290 (#8) |
| ABC | 0.39955 (#2) | 760.51073 (#4) | 39.63% (#7) | 1.14059 (#6) |
| DE | 0.40121 (#3) | 760.02053 (#3) | 39.68% (#8) | 1.19051 (#9) |
| HHO | 0.40143 (#4) | 799.92419 (#9) | 33.79% (#4) | 1.42488 (#13) |
| WOA | 0.40145 (#5) | 736.81676 (#1) | 40.14% (#10) | 1.36106 (#12) |
| NSGA-II | 0.40169 (#6) | 759.08936 (#2) | 40.06% (#9) | 1.17568 (#7) |
| GWO | 0.40291 (#7) | 840.08690 (#10) | 31.83% (#1) | 1.30127 (#10) |
| FCFS | 0.40554 (#8) | 886.66035 (#13) | 33.51% (#3) | 0.79101 (#1) |
| Round Robin | 0.40560 (#9) | 880.23883 (#12) | 33.29% (#2) | 0.87301 (#2) |
| SA | 0.40902 (#10) | 778.99271 (#7) | 42.07% (#11) | 1.01423 (#4) |
| ACO | 0.41251 (#11) | 777.94404 (#6) | 43.13% (#12) | 1.02184 (#5) |
| GA | 0.41311 (#12) | 848.80755 (#11) | 33.98% (#5) | 1.31407 (#11) |
| BFD | 0.43830 (#13) | 787.47190 (#8) | 51.19% (#13) | 0.90374 (#3) |

## Interpretation

- **Composite fitness:** HHO-GWO ranks first in this test and has a lower mean score than each competing method.
- **Energy:** WOA ranks first; HHO-GWO ranks fifth.
- **SLA violation rate:** GWO ranks first; HHO-GWO ranks sixth.
- **Makespan:** FCFS ranks first; HHO-GWO ranks eighth.
- This means the proposed scheduler wins the chosen balanced aggregate objective, but does not win every individual metric.

## Statistical comparison

The attached statistics CSV contains paired two-sided Wilcoxon tests for HHO-GWO versus each of the other 12 methods for each metric, with Holm correction within each metric family. With only 10 seed-level pairs, treat these as preliminary evidence; repeat with more independent seeds before making a strong research claim.

## Important limitations

- Workloads and actual demand are synthetic; host power values and SLA thresholds are modeling assumptions.
- FCFS and Round Robin are defined here as deterministic list-scheduling baselines; this is an explicit implementation definition, not a claim that every published FCFS/RR scheduler behaves identically.
- NSGA-II is represented by this project’s implementation and scalar evaluation interface; it is not a full Pareto-front comparison. A rigorous multi-objective NSGA-II comparison should report Pareto fronts/hypervolume and a documented selection rule.
- This benchmark does not establish that HHO-GWO will win on real cloud traces, a production scheduler, or every task distribution.

## Reproducibility

From the project root:

```bash
python -m pytest -q
python experiments/run_synthetic_benchmark.py --vm-count 12 --vms-per-host 2 --seeds 10 --seed-start 6001 --evaluation-budget 100 --objective-profile balanced --algorithms 'FCFS,Round Robin,BFD,GWO,HHO,HHO-GWO,GA,SA,ACO,DE,WOA,ABC,NSGA-II' --output results/guide_requested_no_pso_10seed_budget100
```

The 10-seed experiment is an initial, reproducible comparison chosen to fit the available runtime. For final academic claims, increase the seed count and validate with CloudSim or a realistic cloud trace.
