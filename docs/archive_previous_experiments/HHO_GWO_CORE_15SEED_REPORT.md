# Core HHO-GWO comparison (PSO excluded)

## Result

In this separate 15-seed synthetic benchmark, HHO-GWO ranked first on the balanced composite fitness and energy among the eight core algorithms. It did not rank first on SLA violations or makespan. This is promising evidence within the declared simulation only, not proof of universal superiority.

## Protocol

- Methods: FCFS, Round Robin, BFD, standalone GWO, standalone HHO, proposed HHO-GWO, GA, ACO. PSO excluded as requested.
- 9 workload scenarios: 20, 50, 100 tasks × low/moderate/high load.
- 15 paired seeds (7001–7015), 1,080 runs total.
- Metaheuristics capped at 100 objective evaluations per run; deterministic baselines use one direct evaluation.
- Same balanced objective weights (one-third each for normalized energy, SLA violation rate, and makespan).
- Workloads and realized demand are synthetic; this is not CloudSim or real trace validation.
- Statistical comparisons: two-sided paired Wilcoxon tests on per-seed means across scenarios, Holm correction within each metric over seven competitors.

## Results (lower is better)

| Algorithm | Composite fitness (rank) | Energy (rank) | SLA violation rate (rank) | Makespan (rank) |
|---|---:|---:|---:|---:|
| HHO-GWO | 0.39275 (#1) | 759.25958 (#1) | 37.45% (#6) | 1.16625 (#5) |
| GWO | 0.39894 (#2) | 847.40863 (#5) | 30.27% (#1) | 1.27200 (#7) |
| HHO | 0.40250 (#3) | 807.88037 (#4) | 34.16% (#5) | 1.34757 (#8) |
| FCFS | 0.40379 (#4) | 885.20414 (#8) | 33.10% (#2) | 0.79307 (#1) |
| Round Robin | 0.40677 (#5) | 878.77130 (#7) | 33.64% (#3) | 0.88678 (#2) |
| ACO | 0.40968 (#6) | 774.01078 (#2) | 42.68% (#7) | 1.01760 (#4) |
| GA | 0.41225 (#7) | 851.31155 (#6) | 33.95% (#4) | 1.26844 (#6) |
| BFD | 0.43780 (#8) | 783.73179 (#3) | 51.41% (#8) | 0.90080 (#3) |

## Interpretation

- HHO-GWO is first on composite fitness in this 15-seed core comparison.
- HHO-GWO is also first on energy in this seed set.
- GWO is first on SLA violation rate; HHO-GWO ranks sixth.
- FCFS is first on makespan; HHO-GWO ranks fifth.
- The earlier broad 13-method comparison used different seed IDs and 10 seeds. Do not merge its averages with this 15-seed core test; results may shift across seed sets.
- Read the statistics CSV for adjusted paired tests; with 15 seed-level pairs and synthetic tasks, findings still need more seeds and external validation.

## Reproduce

```bash
python -m pytest -q
python experiments/run_synthetic_benchmark.py --vm-count 12 --vms-per-host 2 --seeds 15 --seed-start 7001 --evaluation-budget 100 --objective-profile balanced --algorithms 'FCFS,Round Robin,BFD,GWO,HHO,HHO-GWO,GA,ACO' --output results/guide_core_no_pso_15seed_budget100
```
