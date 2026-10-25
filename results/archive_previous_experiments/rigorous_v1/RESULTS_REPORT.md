# Synthetic scheduler benchmark v1 — results

## Scope

This is a **synthetic scheduling benchmark**, not a Bitbrains performance result and not a CloudSim validation. It was designed because the supplied Person 1 CSV is one CPU time series without workload identifiers for concurrent tasks. The generator creates synthetic concurrent task sets at declared offered-load ratios. The `actual_demand` field is a synthetic noisy realization of predicted demand, not measured Bitbrains actual demand.

## Protocol completed

- 9 scenarios: 20, 50, and 100 tasks crossed with low (0.35), moderate (0.65), and high (0.95) offered load.
- 30 paired seeds per scenario.
- Six algorithms: BFD, GWO, HHO, HHO-GWO, PSO, and GA.
- 1,620 algorithm runs total.
- 300 objective-evaluation calls per metaheuristic run; BFD uses one objective evaluation.
- Objective: equal-weight normalized host energy + task SLA violation rate + makespan.
- Hosts start empty. Host power is counted once per active host, with declared illustrative power parameters in `protocol.json`.
- `runs.csv` records per-scenario results; `per_seed.csv` averages each algorithm across the same nine scenarios per seed; the inferential unit for the paired tests is the seed-level average (n=30), not each task or scenario.

## Descriptive results

Lower realized fitness is better under the predeclared objective.

| Algorithm | Mean realized fitness | SD | Mean energy | Mean SLA violation rate | Mean makespan |
|---|---:|---:|---:|---:|---:|
| BFD | 0.433379 | 0.016692 | 304.436 | 0.4715 | 0.8613 |
| GWO | **0.344203** | 0.005557 | 322.200 | **0.1561** | 0.9064 |
| HHO | 0.348980 | 0.011904 | 277.640 | 0.2429 | 1.2692 |
| HHO-GWO | 0.349146 | 0.009745 | 288.470 | 0.2238 | 1.2007 |
| PSO | 0.346686 | 0.008254 | 323.659 | 0.1654 | **0.8524** |
| GA | 0.355774 | 0.008525 | 324.390 | 0.1880 | 0.8813 |

## Paired one-sided Wilcoxon tests

The test direction is HHO-GWO having lower realized fitness than the named baseline. P-values are corrected across the five comparisons with Holm's method.

| Comparison | Mean improvement of HHO-GWO | Holm-adjusted p | Significant at 0.05? |
|---|---:|---:|---|
| vs BFD | +19.44% | 4.66e-09 | Yes |
| vs GWO | -1.44% | 1.000 | No |
| vs HHO | -0.05% | 1.000 | No |
| vs PSO | -0.71% | 1.000 | No |
| vs GA | +1.86% | 0.00291 | Yes |

## Interpretation

The results **do not support the claim that HHO-GWO outperforms all five baselines**. HHO-GWO performs better than BFD and GA on the primary objective in this synthetic benchmark, but GWO and PSO have lower mean objective values, and HHO is effectively tied with the hybrid. The hybrid uses less energy on average than GWO and PSO, but has a higher SLA violation rate and longer makespan. These trade-offs are exactly why individual metrics must be reported alongside the combined objective.

## Limitations and next work

- Workloads, task demand, actual-demand variation, host power parameters, and capacities are synthetic assumptions.
- Results should not be presented as evidence of Bitbrains or production-cloud performance.
- The three objective weights and normalization references are fixed in the protocol; conclusions depend on these choices and should be justified in the report.
- The prediction ablation (persistence versus BiLSTM) remains a separate experiment using valid aligned trace data. No claim that BiLSTM improves scheduling is supported here.
- If claiming real cloud energy savings, validate the host model in CloudSim Plus or another explicitly described simulator with defensible power parameters.
