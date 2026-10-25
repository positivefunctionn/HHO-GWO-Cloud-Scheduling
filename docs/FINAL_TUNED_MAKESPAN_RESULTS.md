# Balanced-profile results — convex host-power model

This report supersedes the earlier linear-power experiment archived under `results/archive_previous_experiments/linear_power_curve_20261025/`.

## Protocol

- 7 algorithms: ACO, WOA, ABC, GWO, GA, HHO, and proposed HHO–GWO.
- 20 paired seed IDs: 9601–9610 and 9701–9710.
- 9 synthetic workload scenarios: 20/50/100 tasks × low/moderate/high offered load.
- 1,260 algorithm × seed × scenario observations; 300 objective evaluations per metaheuristic run.
- 12 VMs across 6 hosts (2 VMs per host).
- Host power proxy: `P(u) = P_idle + (P_max - P_idle) * u^2` for active hosts; inactive hosts contribute zero. `u` is aggregate host utilization clipped to [0,1]. This is a convex synthetic proxy, not measured physical energy.
- Balanced fitness uses equal weights for normalized energy proxy, SLA violation rate, and makespan.
- HHO–GWO uses an 8% epsilon-constraint selection rule: among its candidate schedules within 8% of its best observed composite fitness, choose the lowest makespan, then fitness. This policy is specific to HHO–GWO in this comparison and is a fairness limitation that must be disclosed.

## Results (lower is better)

| Algorithm | Composite fitness | Energy proxy | SLA violations | Makespan |
|---|---:|---:|---:|---:|
| **HHO–GWO** | **0.34711 (#1)** | 696.39 (#4) | 31.14% (#3) | **0.99724 (#1 by mean)** |
| ABC | 0.35415 (#2) | 680.71 (#3) | 32.90% (#5) | 1.17429 (#3) |
| GWO | 0.35914 (#3) | 731.59 (#6) | **28.96% (#1)** | 1.25721 (#5) |
| HHO | 0.36026 (#4) | 675.60 (#2) | 32.21% (#4) | 1.47314 (#7) |
| GA | 0.36346 (#5) | 736.67 (#7) | 29.92% (#2) | 1.24546 (#4) |
| WOA | 0.36695 (#6) | **647.12 (#1)** | 36.84% (#6) | 1.46768 (#6) |
| ACO | 0.37823 (#7) | 705.19 (#5) | 39.41% (#7) | 1.02397 (#2) |

## Statistical interpretation

Paired two-sided Wilcoxon signed-rank tests use the 20 seed-level averages across the nine scenarios; Holm correction is applied within each metric's six baseline comparisons. HHO–GWO's mean composite-fitness advantage is significant against ACO, WOA, GWO, GA and HHO, but **not against ABC** (adjusted p = 0.1429). Its mean makespan is 0.99724 versus 1.02397 for ACO; this paired difference is statistically significant under the stated test and correction (adjusted p = 0.00730). The epsilon-constraint selection asymmetry remains an important caveat: include an ablation or apply a comparable selection policy to baselines before making a strong superiority claim.

HHO–GWO is not the energy leader (WOA is) or the SLA leader (GWO is) in the balanced profile.

## Source files

- Raw run data: `../results/final_convex_balanced/runs.csv`
- Protocol: `../results/final_convex_balanced/protocol.json`
- Audited metric summary: `../results/final_convex_balanced/audited_metric_summary.csv`
- Paired tests: `../results/final_convex_balanced/audited_paired_tests.csv`
- Charts: `figures/balanced_composite_fitness.png`, `figures/balanced_makespan.png`, `figures/balanced_metric_ranks.png`

This is a synthetic benchmark. It does not establish performance on CloudSim Plus, real traces, or production infrastructure.
