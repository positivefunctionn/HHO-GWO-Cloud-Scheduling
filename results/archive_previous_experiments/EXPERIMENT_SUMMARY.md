# Person 2 scheduler integration — exploratory run summary

> **IMPORTANT: historical, pre-budget results.** The CSVs summarized below were generated before the strict 300 objective-call budget was added. Do not cite this table as the equal-budget comparison. Rerun `python experiments/run_experiments.py` to regenerate the result CSVs under the new budget policy. The input predictions remain unchanged.

**Input:** `data/person2_scheduler_input.csv` (1,094 rows; SHA-256 verified against the supplied file).
**Run:** 6 algorithms × 10 seeds × 110 horizons = 6,600 horizon-level schedules.
**Validation:** 8 unit tests passed; full experiment completed.

## Mean results across seeds and horizons

Lower is better for fitness, energy, makespan, SLA violations, load imbalance, runtime and evaluation count. Utilization is reported as a proxy and should not be interpreted as a realistic utilization estimate under the current synthetic-task abstraction.

| Algorithm | Fitness mean ± SD | Energy mean | Makespan mean | SLA violations / horizon mean | Runtime / horizon mean (s) | Objective evaluations / horizon mean |
|---|---:|---:|---:|---:|---:|---:|
| BFD | 3.776730 ± 0.000000 | 850.896 | 1.6758 | 5.855 | 0.000026 | 1.00 |
| GWO | 3.761057 ± 0.002008 | 850.471 | 1.6500 | 5.815 | 0.007257 | 243.94 |
| HHO | 3.762774 ± 0.001705 | 850.456 | 1.6563 | 5.825 | 0.005970 | 156.59 |
| HHO-GWO | 3.759046 ± 0.000777 | 850.468 | 1.6501 | 5.821 | 0.013172 | 388.89 |
| PSO | 3.765942 ± 0.009634 | 850.526 | 1.6573 | 5.817 | 0.003839 | 174.32 |
| GA | 3.758470 ± 0.000700 | 850.471 | 1.6501 | 5.806 | 0.008863 | 165.93 |

## Interpretation and limitations

- GA has the lowest mean objective score in this run (3.758470), with HHO–GWO close behind (3.759046). The gap is very small and this run does not establish statistical significance or prove that GA is generally superior.
- These historical results have different objective-evaluation counts. They are superseded for comparison purposes by the new strict budget policy; rerun the experiment before interpreting algorithm rankings.
- The supplied CSV has no task IDs, VM IDs, or task-capacity metadata. The current implementation treats each time-series observation as a synthetic task in a batch of 10; cumulative utilization and SLA metrics are therefore proxies and can be unrealistic.
- The handoff has a binary predicted-overload label but no calibrated overload probability. The integration uses the binary flag as a documented 0/1 risk-score proxy; this is not a probability estimate.
- `timestamp_ms` values look like Unix seconds; confirm the unit with Person 1.
- The original prediction CSV is not edited. Negative predictions are preserved in the source; only derived demand is floored at zero and logged.
- Person 1 reported that persistence outperforms BiLSTM on the current test set. This scheduling run does not change that finding or claim BiLSTM is the best predictor.
- Treat these outputs as an integration/prototype result, not validated CloudSim performance. Confirm task semantics and evaluate in Person 3’s CloudSim Plus environment before making final performance claims.
