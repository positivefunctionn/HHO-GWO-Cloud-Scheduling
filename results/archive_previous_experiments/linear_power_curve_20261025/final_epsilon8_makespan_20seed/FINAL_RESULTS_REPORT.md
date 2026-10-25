# HHO-GWO tuned project: independent makespan validation

## Executive result

On a **fresh 20-seed holdout experiment**, the tuned HHO-GWO scheduler achieved the lowest mean composite fitness and the lowest mean makespan among seven algorithms: ACO, WOA, ABC, GWO, GA, standalone HHO, and proposed HHO-GWO.

The mean makespan was **0.99540** for HHO-GWO and **1.01455** for ACO. This is first place by mean, but the paired Wilcoxon test is **not statistically significant** after Holm correction (adjusted p = 0.1140). Report it as a mean-rank win, not a proven statistical win.

The final holdout seeds (9601–9610 and 9701–9710) were not used to choose the 8% epsilon threshold. Earlier seeds were used during development and tuning.

## Benchmark protocol

- 7 algorithms: ACO, WOA, ABC, GWO, GA, HHO, and proposed HHO-GWO.
- 12 VMs on 6 hosts, 2 VMs per host.
- 9 workload scenarios: 20, 50, and 100 tasks × low, moderate, and high offered loads.
- 20 untouched paired seed IDs: 9601–9610 and 9701–9710.
- 1,260 total algorithm-scenario-seed runs (180 per algorithm).
- 300 objective evaluations per metaheuristic run.
- Synthetic workload with the same declared VM/host capacities and scoring references for all methods.
- Power parameters are simulation assumptions, not measured real-world energy.

## Algorithm change

The hybrid budget is 5% HHO, 5% GWO, and 90% local refinement. Local search orders candidate moves by projected makespan. The final selection uses a declared **8% epsilon constraint**: among candidates within 8% of the best predicted composite fitness found, select the candidate with the lowest predicted makespan.

This is a deliberate multi-objective trade-off. The selection policy differs from the single-objective search policy of some baselines, so the comparison must state this clearly. A stronger follow-up would add the same epsilon-constraint/Pareto selection option to the baselines.

## Results

| Algorithm | Composite fitness ↓ | Energy ↓ | SLA violations ↓ | Makespan ↓ |
|---|---:|---:|---:|---:|
| **HHO-GWO** | 0.37135 (#1) | 769.41 (#4) | 31.82% (#3) | 0.99540 (#1) |
| ABC | 0.37981 (#2) | 758.95 (#3) | 33.74% (#5) | 1.15199 (#3) |
| HHO | 0.38946 (#3) | 753.47 (#2) | 33.73% (#4) | 1.49242 (#7) |
| WOA | 0.39094 (#4) | 724.66 (#1) | 37.57% (#6) | 1.41336 (#6) |
| GWO | 0.39110 (#5) | 839.23 (#6) | 28.88% (#1) | 1.25039 (#4) |
| GA | 0.39690 (#6) | 844.35 (#7) | 30.08% (#2) | 1.25795 (#5) |
| ACO | 0.39977 (#7) | 775.75 (#5) | 39.58% (#7) | 1.01455 (#2) |

## Statistical interpretation

Paired two-sided Wilcoxon signed-rank tests were performed on the 20 seed-level aggregates, with Holm correction within each metric family. See `FINAL_PAIRED_STATISTICAL_TESTS.csv`.

- **Composite fitness:** HHO-GWO has the best mean. The paired advantage is significant after Holm correction against ACO, GA, GWO, HHO and WOA. Against ABC, the adjusted p-value is 0.0637, so the difference is not significant at 0.05.
- **Makespan:** HHO-GWO has the best mean. It was better than ACO on 13 of 20 paired seed aggregates and worse on 7; the difference is not statistically significant (Holm-adjusted p = 0.1140).
- **SLA:** GWO and GA have lower mean violation rates than HHO-GWO.
- **Energy:** WOA, HHO and ABC have lower mean energy than HHO-GWO.

## Reproducibility

Install requirements and run tests from the project root:

```bash
python -m pip install -r requirements.txt
python -m pytest -q
```

Reproduce the two independent holdout batches:

```bash
python experiments/run_synthetic_benchmark.py \\
  --seeds 10 --seed-start 9601 --task-counts 20,50,100 \\
  --load-levels low,moderate,high --vm-count 12 --vms-per-host 2 \\
  --objective-profile balanced --evaluation-budget 300 \\
  --algorithms ACO,WOA,ABC,GWO,GA,HHO,HHO-GWO \\
  --hybrid-hho-fraction 0.05 --hybrid-gwo-fraction 0.05 \\
  --output results/holdout_batch_9601

python experiments/run_synthetic_benchmark.py \\
  --seeds 10 --seed-start 9701 --task-counts 20,50,100 \\
  --load-levels low,moderate,high --vm-count 12 --vms-per-host 2 \\
  --objective-profile balanced --evaluation-budget 300 \\
  --algorithms ACO,WOA,ABC,GWO,GA,HHO,HHO-GWO \\
  --hybrid-hho-fraction 0.05 --hybrid-gwo-fraction 0.05 \\
  --output results/holdout_batch_9701
```

## Limitations and next step

This is a synthetic benchmark, not a CloudSim or real-cloud validation. The result supports saying HHO-GWO had the best observed mean composite fitness and makespan in this holdout experiment. It does **not** support saying it wins energy and SLA individually, nor that the makespan advantage over ACO is statistically proven. The next step is validation with realistic traces/CloudSim and a fair multi-objective comparison policy for the baselines.
