# Expanded 12-VM / 6-host synthetic benchmark results (balanced objective profile)

## Protocol
- 12 VMs across 6 hosts (2 VMs per host), 20/50/100 tasks, low/moderate/high offered load.
- 30 paired seeds per scenario; 7 algorithms; 1890 algorithm-scenario-seed runs.
- Metaheuristics use the same maximum of 300 objective evaluations; BFD is deterministic and uses one evaluation.
- Objective profile: balanced; shared weights applied equally to every algorithm: {'energy': 0.3333333333333333, 'sla': 0.3333333333333333, 'makespan': 0.3333333333333333}.
- HHO-GWO budget split (fractions): {'hho': 0.1, 'gwo': 0.25, 'local_refinement': 0.65}.
- Actual demand remains synthetic noise around predicted demand; these results do not validate BiLSTM forecasts or real-cloud energy savings.
- Host power and capacity values are explicit simulation assumptions, not measurements from physical hosts.

## Per-scenario fitness ranking
| Scenario | Winner by mean fitness | HHO-GWO rank | Mean HHO-GWO fitness |
|---|---|---:|---:|
| n20_high | HHO-GWO | 1 / 7 | 0.5498 |
| n20_low | HHO-GWO | 1 / 7 | 0.1999 |
| n20_moderate | HHO-GWO | 1 / 7 | 0.3758 |
| n50_high | HHO-GWO | 1 / 7 | 0.5405 |
| n50_low | HHO-GWO | 1 / 7 | 0.1857 |
| n50_moderate | ABC | 2 / 7 | 0.3668 |
| n100_high | HHO-GWO | 1 / 7 | 0.5466 |
| n100_low | HHO-GWO | 1 / 7 | 0.1736 |
| n100_moderate | GWO | 4 / 7 | 0.3622 |

## Interpretation
The best method is identified separately for each scenario using mean realized fitness; lower is better for the configured objective profile. See `per_scenario_summary.csv` for all metrics and `hybrid_two_sided_comparisons.csv` for paired two-sided Wilcoxon tests with Holm correction across all 54 scenario-level comparisons.

This is an expanded synthetic experiment, not proof of performance on real cloud traces. Do not claim that HHO-GWO is uniformly best unless the results support that claim across the declared scenarios and metrics.
