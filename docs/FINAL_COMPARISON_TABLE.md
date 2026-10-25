# Final comparison — balanced profile with convex host-power proxy

Lower is better. Rankings are means across 20 paired seeds and nine synthetic scenarios per seed. The host power curve uses exponent alpha = 2.0.

| Algorithm | Composite fitness ↓ | Energy proxy ↓ | SLA violations ↓ | Makespan ↓ |
|---|---:|---:|---:|---:|
| **HHO–GWO** | **0.34711 (#1)** | 696.39 (#4) | 31.14% (#3) | **0.99724 (#1 by mean)** |
| ABC | 0.35415 (#2) | 680.71 (#3) | 32.90% (#5) | 1.17429 (#3) |
| GWO | 0.35914 (#3) | 731.59 (#6) | **28.96% (#1)** | 1.25721 (#5) |
| HHO | 0.36026 (#4) | 675.60 (#2) | 32.21% (#4) | 1.47314 (#7) |
| GA | 0.36346 (#5) | 736.67 (#7) | 29.92% (#2) | 1.24546 (#4) |
| WOA | 0.36695 (#6) | **647.12 (#1)** | 36.84% (#6) | 1.46768 (#6) |
| ACO | 0.37823 (#7) | 705.19 (#5) | 39.41% (#7) | 1.02397 (#2) |

## Interpretation

- HHO–GWO ranks first by observed mean composite fitness; the difference versus ABC is not statistically significant after Holm correction (adjusted p = 0.1429).
- HHO–GWO has the lowest observed mean makespan; the paired difference versus ACO is significant under the stated seed-level Wilcoxon test with Holm correction (adjusted p = 0.00730).
- WOA has the lowest energy proxy; GWO has the lowest SLA violation rate.
- HHO–GWO uses an 8% epsilon-constraint selection rule that is not applied to the single-objective baselines. Disclose this asymmetry and include a selection-policy ablation or comparable baseline policy in a stronger follow-up.
- This is synthetic evidence, not CloudSim or real-cloud validation.
