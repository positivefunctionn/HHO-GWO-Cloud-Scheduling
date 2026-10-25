# Expanded 12-VM / 6-host synthetic benchmark results (balanced objective profile)

## Protocol
- 12 VMs across 6 hosts (2 VMs per host), 20/50/100 tasks, low/moderate/high offered load.
- 30 paired seeds per scenario; 6 algorithms; 1,620 algorithm-scenario-seed runs.
- Metaheuristics use the same maximum of 300 objective evaluations; BFD is deterministic and uses one evaluation.
- Objective profile: balanced; shared weights applied equally to every algorithm: {'energy': 0.3333333333333333, 'sla': 0.3333333333333333, 'makespan': 0.3333333333333333}.
- HHO-GWO budget split (fractions): {'hho': 0.2, 'gwo': 0.2, 'local_refinement': 0.6000000000000001}.
- Actual demand remains synthetic noise around predicted demand; these results do not validate BiLSTM forecasts or real-cloud energy savings.
- Host power and capacity values are explicit simulation assumptions, not measurements from physical hosts.

## Per-scenario fitness ranking
| Scenario | Winner by mean fitness | HHO-GWO rank | Mean HHO-GWO fitness |
|---|---|---:|---:|
| n20_high | PSO | 2 / 6 | 0.5500 |
| n20_low | HHO-GWO | 1 / 6 | 0.2013 |
| n20_moderate | HHO-GWO | 1 / 6 | 0.3697 |
| n50_high | PSO | 2 / 6 | 0.5550 |
| n50_low | HHO-GWO | 1 / 6 | 0.1881 |
| n50_moderate | PSO | 3 / 6 | 0.3745 |
| n100_high | PSO | 2 / 6 | 0.5504 |
| n100_low | HHO-GWO | 1 / 6 | 0.1747 |
| n100_moderate | PSO | 5 / 6 | 0.3646 |

## Interpretation
The best method is identified separately for each scenario using mean realized fitness; lower is better for the configured objective profile. See `per_scenario_summary.csv` for all metrics and `hybrid_two_sided_comparisons.csv` for paired two-sided Wilcoxon tests with Holm correction across all 45 scenario-level comparisons.

This is an expanded synthetic experiment, not proof of performance on real cloud traces. Do not claim that HHO-GWO is uniformly best unless the results support that claim across the declared scenarios and metrics.
