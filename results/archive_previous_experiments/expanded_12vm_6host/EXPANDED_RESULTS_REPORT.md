# Expanded 12-VM / 6-host synthetic benchmark results

## Protocol
- 12 VMs across 6 hosts (2 VMs per host), 20/50/100 tasks, low/moderate/high offered load.
- 30 paired seeds per scenario; 6 algorithms; 1,620 algorithm-scenario-seed runs.
- Metaheuristics use the same maximum of 300 objective evaluations; BFD is deterministic and uses one evaluation.
- Primary score is the equal-weight normalized sum of host energy, SLA violation rate, and makespan.
- Actual demand remains synthetic noise around predicted demand; these results do not validate BiLSTM forecasts or real-cloud energy savings.
- Host power and capacity values are explicit simulation assumptions, not measurements from physical hosts.

## Per-scenario fitness ranking
| Scenario | Winner by mean fitness | HHO-GWO rank | Mean HHO-GWO fitness |
|---|---|---:|---:|
| n20_high | PSO | 3 / 6 | 0.5692 |
| n20_low | PSO | 5 / 6 | 0.2189 |
| n20_moderate | BFD | 4 / 6 | 0.4306 |
| n50_high | PSO | 3 / 6 | 0.5685 |
| n50_low | HHO | 2 / 6 | 0.2055 |
| n50_moderate | PSO | 4 / 6 | 0.3850 |
| n100_high | PSO | 2 / 6 | 0.5615 |
| n100_low | HHO | 2 / 6 | 0.2049 |
| n100_moderate | PSO | 2 / 6 | 0.3545 |

## Interpretation
The best method is identified separately for each scenario using mean realized fitness; lower is better. See `per_scenario_summary.csv` for all metrics and `hybrid_two_sided_comparisons.csv` for paired two-sided Wilcoxon tests with Holm correction across all 45 scenario-level comparisons.

This is an expanded synthetic experiment, not proof of performance on real cloud traces. Do not claim that HHO-GWO is uniformly best unless the results support that claim across the declared scenarios and metrics.
