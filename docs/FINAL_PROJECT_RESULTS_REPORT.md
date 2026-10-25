# HHO–GWO Final Research Report — Convex Host-Power Model

## Executive summary

This release evaluates one HHO–GWO scheduler under two separate objective profiles. The host-aware energy proxy now uses a configurable convex power curve with exponent alpha = 2.0. Because that change affects the balanced objective, older linear-power results are archived and are not mixed with this release's final numbers.

- **Balanced profile:** HHO–GWO achieved the lowest observed mean composite fitness and mean makespan among seven methods. Its composite-fitness advantage over ABC was not statistically significant; its makespan difference versus ACO was significant under the stated paired test and Holm correction.
- **SLA-focused profile:** HHO–GWO achieved the lowest mean SLA violation rate; the paired improvement versus GWO was significant after Holm correction.
- HHO–GWO did not win every metric. WOA had the lowest energy proxy and GWO had the lowest SLA rate in the balanced experiment.
- All results are from synthetic workloads and declared host-power assumptions, not CloudSim Plus or measured production-cloud performance.

## Experiment A — balanced objective profile

**Protocol:** 7 algorithms (ACO, WOA, ABC, GWO, GA, HHO, HHO–GWO); 20 paired seed IDs (9601–9610 and 9701–9710); 9 scenarios (20/50/100 tasks × low/moderate/high load); 1,260 runs; 300 objective evaluations per metaheuristic run; 12 VMs on 6 hosts; host-power exponent alpha = 2.0. The objective weights normalized energy proxy, SLA rate, and makespan equally.

| Algorithm | Composite fitness ↓ | Energy proxy ↓ | SLA violation rate ↓ | Makespan ↓ |
|---|---:|---:|---:|---:|
| **HHO–GWO** | **0.34711 (#1)** | 696.39 (#4) | 31.14% (#3) | **0.99724 (#1 by mean)** |
| ABC | 0.35415 (#2) | 680.71 (#3) | 32.90% (#5) | 1.17429 (#3) |
| GWO | 0.35914 (#3) | 731.59 (#6) | **28.96% (#1)** | 1.25721 (#5) |
| HHO | 0.36026 (#4) | 675.60 (#2) | 32.21% (#4) | 1.47314 (#7) |
| GA | 0.36346 (#5) | 736.67 (#7) | 29.92% (#2) | 1.24546 (#4) |
| WOA | 0.36695 (#6) | **647.12 (#1)** | 36.84% (#6) | 1.46768 (#6) |
| ACO | 0.37823 (#7) | 705.19 (#5) | 39.41% (#7) | 1.02397 (#2) |

Paired two-sided Wilcoxon tests use 20 seed-level averages across scenarios, with Holm correction within each metric's six baseline comparisons. The composite-fitness difference versus ABC is not significant (adjusted p = 0.1429). The makespan difference versus ACO is significant under this protocol (adjusted p = 0.00730). HHO–GWO uses an 8% epsilon-constraint policy to choose the lowest makespan among candidates within tolerance of its best composite score; this is a comparator asymmetry that should be addressed through ablation or comparable baseline selection in follow-up work.

## Experiment B — SLA-focused objective profile

**Protocol:** 7 algorithms; 20 paired seed IDs (12001–12020); 9 synthetic scenarios; 1,260 runs; 100 objective evaluations per metaheuristic run; SLA weight 1 and energy/makespan weights 0 for all algorithms.

| Algorithm | Mean SLA violation rate ↓ | Rank |
|---|---:|---:|
| **HHO–GWO** | **27.42%** | **1** |
| HHO | 31.51% | 2 |
| GWO | 31.58% | 3 |
| GA | 34.17% | 4 |
| WOA | 36.61% | 5 |
| ABC | 36.99% | 6 |
| ACO | 40.69% | 7 |

HHO–GWO's mean SLA rate was 4.16 percentage points below GWO's, a 13.18% relative reduction. A predeclared one-sided paired Wilcoxon test over seed-level averages, with Holm correction across six baselines, gave adjusted p = 0.000241 versus GWO and adjusted p < 0.05 versus each of the six listed baselines. This is evidence for the SLA-focused synthetic protocol, not a universal claim.

## Interpretation and scope

The strongest defensible statement is that HHO–GWO showed promising, objective-specific results in these synthetic experiments: best observed mean composite fitness and makespan in the balanced profile, and lowest mean SLA violation rate in the separate SLA-focused profile. The balanced composite-fitness difference versus ABC is not significant, the balanced epsilon-constraint policy is not applied to baselines, WOA wins energy, and GWO wins SLA in the balanced profile.

The project has not been validated in CloudSim Plus or on production cloud traces. Host power values are assumptions, not measured energy. The smoke test does not validate BiLSTM predictive accuracy. See [`REPRODUCIBILITY_AUDIT.md`](REPRODUCIBILITY_AUDIT.md) and `START_HERE.md` for full protocols, raw data locations, commands and limitations.
