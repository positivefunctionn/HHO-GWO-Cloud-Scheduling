# HHO-GWO Eight-Algorithm Independent Benchmark Report

## Executive summary

The tuned HHO-GWO scheduler achieved the lowest mean composite fitness among eight methods in this declared synthetic benchmark. It did **not** win every individual metric: HHO had slightly lower energy, PSO had lower SLA violation rate, and BFD/ACO/SA had lower makespan. These trade-offs must remain visible in any project presentation.

## Methods compared

- Best-Fit Decreasing (BFD)
- Grey Wolf Optimizer (GWO)
- Harris Hawks Optimization (HHO)
- Hybrid HHO-GWO with iterated local refinement
- Particle Swarm Optimization (PSO)
- Genetic Algorithm (GA)
- Simulated Annealing (SA)
- Ant Colony Optimization (ACO)

SA and ACO were implemented as additional reference baselines in `src/sa.py` and `src/aco.py`. Both use predicted demand only, and each candidate evaluation is counted against the shared evaluation cap. Both use a BFD schedule as an initial incumbent; that objective call is included in the 300-call cap.

## Independent test protocol

- 12 VMs distributed across 6 hosts, 2 VMs per host.
- 20, 50, and 100 tasks; low, moderate, and high offered load.
- 30 paired seeds per scenario (seed IDs 6001–6030).
- 9 scenarios × 30 seeds × 8 algorithms = **2,160 algorithm-scenario-seed runs**.
- Balanced objective: one-third each for normalized host energy, SLA violation rate, and makespan; same external evaluation formula for all algorithms.
- Metaheuristics have a maximum of 300 objective evaluations per run; BFD is deterministic and uses one evaluation.
- HHO-GWO budget: 10% HHO, 25% GWO, 65% local refinement.
- Scenario-wise paired two-sided Wilcoxon tests with Holm correction across the 63 HHO-GWO-versus-comparator comparisons.

## Overall mean results

Lower is better for all metrics. SLA values are proportions of tasks with SLA violations.

| Algorithm | Composite fitness (rank) | Energy (rank) | SLA violation rate (rank) | Makespan (rank) |
|---|---:|---:|---:|---:|
| **HHO-GWO** | **0.364561 (1)** | 761.161 (2) | 29.137% (2) | 1.134775 (4) |
| PSO | 0.374414 (2) | 834.944 (7) | **24.533% (1)** | 1.223020 (5) |
| SA | 0.387102 (3) | 774.202 (3) | 35.337% (6) | 1.073009 (3) |
| HHO | 0.389557 (4) | **756.722 (1)** | 33.441% (5) | 1.494457 (8) |
| GWO | 0.392221 (5) | 832.948 (6) | 29.607% (3) | 1.267909 (7) |
| GA | 0.397317 (6) | 846.218 (8) | 30.248% (4) | 1.236618 (6) |
| ACO | 0.406402 (7) | 777.367 (4) | 41.433% (7) | 1.013748 (2) |
| BFD | 0.434166 (8) | 787.017 (5) | 50.022% (8) | **0.900431 (1)** |

HHO-GWO's mean composite fitness is about **2.63% lower than PSO**, the second-ranked method. This is the strongest overall result in this test. It uses about 0.59% more energy than HHO on average, has a higher SLA violation rate than PSO, and is fourth on makespan.

## Statistical comparison

After Holm correction across scenario-level paired tests, HHO-GWO's composite fitness was significantly better in:

- 6 of 9 scenarios versus BFD
- 4 of 9 versus GWO
- 3 of 9 versus HHO
- 3 of 9 versus PSO
- 6 of 9 versus GA
- 4 of 9 versus SA
- 5 of 9 versus ACO

These are scenario-level results. They do not mean HHO-GWO wins every seed or scenario. See `results/final_8_algorithm_independent/hybrid_two_sided_comparisons.csv` for the full adjusted comparisons.

## Changes tested

- Retained the best schedule across HHO, GWO, and local refinement.
- Kept the BFD candidate as an incumbent without exceeding the evaluation cap.
- Added iterated local refinement and bounded multi-task perturbations.
- Tuned the hybrid budget split to 10% HHO, 25% GWO, and 65% local refinement using a separate preliminary seed set; the final independent test used seed IDs 6001–6030.
- Added SA and ACO as additional comparison baselines.

## Reproducibility

From the project root:

```bash
python -m pytest -q
python experiments/run_synthetic_benchmark.py --vm-count 12 --vms-per-host 2 --seeds 30 --seed-start 6001 --objective-profile balanced --hybrid-hho-fraction 0.10 --hybrid-gwo-fraction 0.25 --output results/reproduced_eight_algorithm_test
python experiments/analyze_expanded_results.py results/reproduced_eight_algorithm_test
```

The full final test was split by task count and load level to keep individual runs within execution limits, then combined in `results/final_8_algorithm_independent/`. The final result folder includes the combined raw runs, protocol, overall summary, per-scenario summary, and adjusted statistical comparisons.

## Limitations

- This is a synthetic benchmark, not a real cloud trace, physical energy measurement, or CloudSim validation.
- Actual demand is generated as synthetic noise around predicted demand; the benchmark does not validate BiLSTM predictive performance.
- Host power curves, capacities, and SLA definitions are declared assumptions.
- The benchmark supports the claim that HHO-GWO achieved the best mean composite fitness under this configuration. It does not support a claim that HHO-GWO is universally best or best on every individual metric.
