# Start Here — HHO–GWO Cloud Scheduling Research Project

This release contains one HHO–GWO implementation and two **separate objective-profile experiments**. Read this file first; do not combine their metric rankings into one benchmark.

## What is included

- `src/`: HHO, GWO, hybrid scheduler, baselines, fitness and model code.
- `experiments/run_synthetic_benchmark.py`: reproducible synthetic benchmark runner; records the objective profile and convex host-power exponent in `protocol.json`.
- `experiments/analyze_synthetic_results.py`: panel validation, summary tables and paired tests with Holm correction.
- `experiments/merge_benchmark_batches.py`: validates and merges seed-disjoint batches.
- `tests/`: unit tests.
- `results/final_convex_balanced/`: fresh balanced-profile benchmark (1,260 runs).
- `results/final_convex_sla/`: fresh SLA-profile benchmark (1,260 runs).
- `docs/REPRODUCIBILITY_AUDIT.md`: current audit, results and limitations.
- `results/archive_previous_experiments/`: older linear-power results and intermediate experiments, preserved for traceability.

## Current result summary

### Balanced objective profile

20 paired seeds × 9 synthetic scenarios × 7 algorithms = 1,260 runs, with 300 objective evaluations per metaheuristic run. The host energy proxy uses the configurable convex curve `P(u)=P_idle+(P_max-P_idle)*u^2` for active hosts. HHO–GWO ranked first by mean composite fitness (0.34711) and mean makespan (0.99724). Its mean makespan difference versus ACO was significant in the seed-level paired Wilcoxon test after Holm correction (adjusted p = 0.00730). Its composite-fitness difference versus ABC was not significant (adjusted p = 0.1429). WOA had the lowest energy proxy and GWO had the lowest SLA rate. The balanced HHO–GWO policy uses an 8% epsilon constraint to select the shortest makespan among candidates within tolerance of its best composite score; this is a policy asymmetry versus the single-objective baselines and must be disclosed.

### SLA-focused objective profile

20 paired seeds × 9 synthetic scenarios × 7 algorithms = 1,260 runs, with 100 objective evaluations per metaheuristic run. HHO–GWO had a 27.42% mean realized SLA violation rate versus 31.58% for GWO, a 13.18% relative reduction. The one-sided paired Wilcoxon test with Holm correction reports adjusted p = 0.000241 versus GWO. This is a separate SLA-only experiment; it does not establish balanced-objective superiority. WOA had the lowest secondary energy proxy in this profile.

## Run the checks

From the extracted project root (the folder containing `README.md`, `src/`, and `tests/`):

```bash
py -m pip install -r requirements.txt
py -m unittest discover -s tests -v
py experiments/run_smoke_test.py
```

Or double-click `RUN_CHECKS_WINDOWS.bat`. It installs requirements, runs the unit suite, and executes the smoke test. The tested build environment was Python 3.13.5; check dependency installation if using another Python version.

## Reproduce the balanced experiment

```bash
py experiments/run_synthetic_benchmark.py --vm-count 12 --vms-per-host 2 --seeds 10 --seed-start 9601 --task-counts 20,50,100 --load-levels low,moderate,high --evaluation-budget 300 --power-curve-exponent 2.0 --objective-profile balanced --hybrid-hho-fraction 0.05 --hybrid-gwo-fraction 0.05 --algorithms "ACO,WOA,ABC,GWO,GA,HHO,HHO-GWO" --output results/reproduction_balanced_9601
py experiments/run_synthetic_benchmark.py --vm-count 12 --vms-per-host 2 --seeds 10 --seed-start 9701 --task-counts 20,50,100 --load-levels low,moderate,high --evaluation-budget 300 --power-curve-exponent 2.0 --objective-profile balanced --hybrid-hho-fraction 0.05 --hybrid-gwo-fraction 0.05 --algorithms "ACO,WOA,ABC,GWO,GA,HHO,HHO-GWO" --output results/reproduction_balanced_9701
py experiments/merge_benchmark_batches.py results/reproduction_balanced_9601 results/reproduction_balanced_9701 --output results/reproduction_balanced_merged
py experiments/analyze_synthetic_results.py results/reproduction_balanced_merged --reference HHO-GWO --metrics realized_fitness,realized_energy,realized_sla_rate,realized_makespan,load_imbalance --alternative two-sided
```

## Reproduce the SLA-focused experiment

```bash
py experiments/run_synthetic_benchmark.py --vm-count 12 --vms-per-host 2 --seeds 20 --seed-start 12001 --task-counts 20,50,100 --load-levels low,moderate,high --evaluation-budget 100 --power-curve-exponent 2.0 --objective-profile sla --hybrid-hho-fraction 0.05 --hybrid-gwo-fraction 0.45 --algorithms "HHO-GWO,GWO,HHO,GA,ACO,WOA,ABC" --output results/reproduction_sla
py experiments/analyze_synthetic_results.py results/reproduction_sla --reference HHO-GWO --metrics realized_sla_rate --alternative less
```

`RUN_FULL_REPRODUCTION_WINDOWS.bat` runs both profiles and analyses end-to-end. It may take several minutes and uses fresh fixed output folder names; rename or remove those output folders before rerunning it.

## Research limitations

These are synthetic workload experiments, not CloudSim Plus validation, production cloud measurements, or validation of the BiLSTM predictor. Host-power values are assumptions and energy results are proxy units, not measured watts or joules. The balanced HHO–GWO epsilon-constraint policy is not applied to the single-objective baselines, so a policy ablation or comparable baseline policy is needed for a stronger fairness argument. No artifact can guarantee publication acceptance; the goal is transparent methods, reproducible code, auditable data and claims limited to the evidence.
