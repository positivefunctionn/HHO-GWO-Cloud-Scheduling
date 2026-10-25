# Historical synthetic scheduler benchmark protocol (4-VM baseline)

> This document describes an earlier 4-VM protocol for historical reference. The current final experiments use 12 VMs and 6 hosts; use `FINAL_PROJECT_RESULTS_REPORT.md` and `REPRODUCIBILITY_AUDIT.md` for the authoritative current results.

## Purpose and scope

This benchmark compares BFD, GWO, HHO, HHO-GWO, PSO, and GA on explicitly synthetic concurrent-task instances. **It is not evidence of Bitbrains performance and is not a CloudSim validation.** The Person 1 CSV is a single CPU time series; without concurrent workload identifiers it must not be interpreted as simultaneous tasks.

## Fixed protocol

- Scenarios: 20, 50, and 100 concurrent tasks at offered-load ratios 0.35, 0.65, and 0.95 of total VM CPU capacity.
- Four VMs, each with capacity 100; two hosts, each with capacity 200.
- All VMs/hosts start empty.
- Host 1 power: idle 100, max 220; Host 2 power: idle 80, max 190. These are illustrative simulation parameters, not measured hardware values.
- For each scenario and seed, predicted task demands are positive random weights scaled to the specified offered-load ratio. Realized demand is predicted demand multiplied by a normal random factor with mean 1 and standard deviation 0.08, clipped at zero. Algorithms only receive predicted demand; realized demand is used after assignment for evaluation.
- Primary objective: equal-weight sum of normalized host energy, task SLA violation rate, and makespan. Weights and normalization references are frozen in `protocol.json` before the full run.
- Metaheuristics have a 300 objective-evaluation-call cap per scenario/seed. Repeated assignments count as evaluation calls. BFD is deterministic and reported with its actual call count, normally one.
- Default: 30 paired seeds across all nine scenarios. The seed-level analysis averages each algorithm over the same nine scenarios; seeds, not individual tasks or scenarios, are the paired units for the primary statistical comparison.

## Metric definitions

- Host energy is counted once per host. An inactive host consumes zero power; an active host consumes `idle_power + (max_power - idle_power) * min(max(host_utilization, 0), 1)**alpha`, with configurable `alpha >= 1` (the final runs use `alpha = 2.0`) for one scheduling interval.
- SLA violation is task-based: a task is marked violating if its assigned VM's final utilization exceeds the configured threshold or its individual execution time exceeds the configured execution SLA. This final-load definition is independent of task iteration order.
- Makespan is the maximum sum of task demand divided by assigned VM capacity.
- Predicted metrics are calculated from predicted demand. Realized metrics use `actual_demand` after the assignment is fixed and do not spend the optimizer's evaluation budget.

## Commands

Pilot one scenario with two seeds:

```bash
python experiments/run_synthetic_benchmark.py --seeds 2 --task-counts 20 --load-levels low --output results/pilot_synthetic
```

Full run:

```bash
python experiments/run_synthetic_benchmark.py --seeds 30 --task-counts 20,50,100 --load-levels low,moderate,high --output results/rigorous_v1
```

Outputs: `runs.csv` (per scenario/seed/algorithm), `per_seed.csv` (seed-level paired values averaged across scenarios), `summary.csv` (descriptive summary), and `protocol.json` (protocol and assumptions).

The full run should be performed only after reviewing the synthetic assumptions. Results must be described as synthetic benchmark findings, not as real trace or production-cloud evidence.
