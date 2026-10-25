# Final HHO-GWO project — independent benchmark report

## Headline

The proposed HHO-GWO method had the lowest mean composite fitness in this 7-algorithm synthetic benchmark. It did **not** win every individual metric. This report is the source of truth for the included final experiment; earlier exploratory reports in the archive are historical and should not be mixed with these results.

## Protocol

- Algorithms: ACO, WOA, ABC, GWO, GA, HHO, HHO-GWO.
- 30 independent paired seed IDs (8001–8030), 9 workload scenarios, 1890 algorithm-scenario-seed runs.
- 12 VMs on 6 hosts (2 VMs per host); 20, 50 and 100 tasks; low, moderate and high offered load.
- All stochastic/metaheuristic methods have the same maximum 300 objective evaluations per run.
- HHO-GWO budget: 10% HHO, 25% GWO, 65% iterated local refinement; its BFD constructive candidate, when evaluated, is charged to the shared budget.
- Balanced objective: equal one-third weights for normalized energy, SLA violation rate and makespan.
- Task actual demand is generated synthetically as predicted demand times Gaussian noise; host power values are declared assumptions.
- Realized metrics are used only for reporting, not to guide search. This is not a CloudSim or real-cloud validation and does not validate the BiLSTM model.

## Overall results

Lower is better for all four metrics. Values are means across all 270 workload-scenario/seed combinations per algorithm.

| Algorithm | Composite fitness | Energy | SLA violation rate | Makespan |
|---|---:|---:|---:|---:|
| HHO-GWO | 0.36676 (#1) | 760.23 (#4) | 29.93% (#2) | 1.12952 (#2) |
| ABC | 0.38606 (#2) | 758.23 (#3) | 35.63% (#5) | 1.15699 (#3) |
| HHO | 0.38784 (#3) | 743.21 (#2) | 34.16% (#4) | 1.49353 (#7) |
| GWO | 0.39252 (#4) | 836.53 (#6) | 29.44% (#1) | 1.26059 (#5) |
| WOA | 0.39512 (#5) | 723.77 (#1) | 38.91% (#6) | 1.41233 (#6) |
| GA | 0.39842 (#6) | 848.91 (#7) | 30.47% (#3) | 1.22293 (#4) |
| ACO | 0.40864 (#7) | 775.02 (#5) | 42.33% (#7) | 1.01208 (#1) |

## Interpretation

- **Composite fitness:** HHO-GWO ranks 1st of 7, about 5.00% lower than the second-best algorithm (ABC) by mean.
- **Energy:** HHO-GWO ranks 4; WOA has the lowest mean energy.
- **SLA violations:** HHO-GWO ranks 2; GWO has the lowest mean SLA violation rate.
- **Makespan:** HHO-GWO ranks 2; ACO has the lowest mean makespan.
- The paired two-sided Wilcoxon tests compare HHO-GWO with each baseline using seed-level averages across all nine scenarios. Holm correction covers all 24 metric/comparator tests. See `FINAL_PAIRED_STATISTICAL_TESTS.csv`.
- Per-scenario fitness ranks and scenario-level tests are in `per_scenario_summary.csv` and `hybrid_two_sided_comparisons.csv`.

## Presentation-ready conclusion

In this synthetic benchmark, the proposed HHO-GWO scheduler achieved the best average balanced composite fitness among ACO, WOA, ABC, GWO, GA, standalone HHO and HHO-GWO. It did not achieve the lowest average energy, SLA violation rate or makespan individually. Claims should remain limited to this workload model until the method is evaluated with realistic cloud traces or CloudSim.

## Reproduce

```bash
python -m pip install -r requirements.txt
python -m pytest -q
python experiments/run_synthetic_benchmark.py --vm-count 12 --vms-per-host 2 --seeds 30 --seed-start 8001 --evaluation-budget 300 --algorithms 'ACO,WOA,ABC,GWO,GA,HHO,HHO-GWO' --output results/reproduced_final_test
python experiments/analyze_expanded_results.py results/reproduced_final_test
python experiments/analyze_final_project.py results/reproduced_final_test
```
