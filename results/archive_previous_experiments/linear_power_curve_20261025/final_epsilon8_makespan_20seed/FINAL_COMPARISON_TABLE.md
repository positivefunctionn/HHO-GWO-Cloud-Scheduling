# Final comparison table — HHO-GWO tuned for makespan

Lower is better for all numeric metrics. Ranks are based on the mean over 20 untouched paired seed aggregates, with 9 workload scenarios per seed.

| Algorithm | Composite fitness ↓ | Energy ↓ | SLA violations ↓ | Makespan ↓ |
|---|---:|---:|---:|---:|
| **HHO-GWO** | 0.37135 (#1) | 769.41 (#4) | 31.82% (#3) | 0.99540 (#1) |
| ABC | 0.37981 (#2) | 758.95 (#3) | 33.74% (#5) | 1.15199 (#3) |
| HHO | 0.38946 (#3) | 753.47 (#2) | 33.73% (#4) | 1.49242 (#7) |
| WOA | 0.39094 (#4) | 724.66 (#1) | 37.57% (#6) | 1.41336 (#6) |
| GWO | 0.39110 (#5) | 839.23 (#6) | 28.88% (#1) | 1.25039 (#4) |
| GA | 0.39690 (#6) | 844.35 (#7) | 30.08% (#2) | 1.25795 (#5) |
| ACO | 0.39977 (#7) | 775.75 (#5) | 39.58% (#7) | 1.01455 (#2) |

## Honest takeaway

- HHO-GWO ranks first by mean composite fitness and mean makespan in the holdout experiment.
- The makespan mean is 0.99540 for HHO-GWO versus 1.01455 for ACO, but the paired difference is not statistically significant after Holm correction (adjusted p = 0.1140).
- HHO-GWO does not rank first in energy or SLA violation rate.
- The makespan-focused epsilon-constraint policy is explicitly documented; do not present it as a universal win or real-cloud validation.
