# HHO–GWO Hybrid Cloud Scheduler

**Research artifact with balanced and SLA-focused objective profiles.** Start with [`START_HERE.md`](START_HERE.md) and read [`docs/REPRODUCIBILITY_AUDIT.md`](docs/REPRODUCIBILITY_AUDIT.md) before using any result in a report.

## Proposed method

A hybrid Harris Hawks Optimization–Grey Wolf Optimization scheduler for synthetic task-to-VM assignment. HHO explores candidate assignments, GWO refines an HHO-seeded population, a deterministic BFD candidate may serve as a budget-charged incumbent, and bounded local relocation search refines the schedule. A shared objective-evaluation counter caps metaheuristic search calls.

The benchmark supports multiple declared objective profiles:

- **Balanced:** equal weights for normalized host-energy proxy, SLA violation rate and makespan. The host-energy model is configurable and convex for exponent alpha > 1: `P(u)=P_idle+(P_max-P_idle)*u^alpha` for active hosts. The audited experiment uses alpha = 2.0.
- **SLA-focused:** SLA violation rate receives weight 1; energy and makespan receive weight 0.

The balanced HHO–GWO implementation additionally uses an 8% epsilon-constraint selection policy: among candidate schedules within 8% of its best composite score, choose the shortest makespan, then fitness. This is part of the proposed policy and is a comparator asymmetry that must be disclosed.

## Current audited evidence

- **Balanced profile:** 7 algorithms × 20 seeds × 9 synthetic scenarios = 1,260 runs; 300 objective evaluations per metaheuristic run. HHO–GWO ranked first by mean composite fitness (0.34711) and mean makespan (0.99724). The makespan difference versus ACO was significant after Holm correction within the makespan comparison family (adjusted p = 0.00730). The composite-fitness difference versus ABC was not significant (adjusted p = 0.1429). WOA had the lowest energy proxy; GWO had the lowest SLA rate.
- **SLA profile:** 7 algorithms × 20 seeds × 9 synthetic scenarios = 1,260 runs; 100 objective evaluations per metaheuristic run. HHO–GWO's mean SLA violation rate was 27.42% versus GWO's 31.58%, a 13.18% relative reduction; the one-sided paired Wilcoxon comparison adjusted by Holm gave p = 0.000241 versus GWO.

These are separate experiments with different objective profiles and must not be merged into a single ranking. All workload scenarios and host power values are synthetic assumptions. This project has not been validated in CloudSim Plus or on production cloud traces; the energy metric is not measured physical energy.

## Project layout

```text
src/                 Models, objective, HHO/GWO/hybrid and baseline implementations
experiments/         Benchmark runner, merge tool, analysis script and smoke test
config/              Default configuration
data/                Input handoff data
results/             Final convex-model runs, statistics and historical archive
tests/               Unit tests
docs/                Algorithm design, methodology, audit, results and charts
```

## Windows setup and checks

From the project root:

```bash
py -m pip install -r requirements.txt
py -m unittest discover -s tests -v
py experiments/run_smoke_test.py
```

Or double-click `RUN_CHECKS_WINDOWS.bat`. In the build environment (Python 3.13.5), all **12 unit tests passed**. The smoke test generated 1,320 schedules across six algorithms; 1,094 output rows passed the declared schema validation. The smoke test's risk input is a binary `predicted_overload` fallback, not a calibrated probability.

## Reproducibility and reporting

The final convex-model outputs are under `results/final_convex_balanced/` and `results/final_convex_sla/`. They include raw run-level observations, `protocol.json`, metric summaries, seed-level aggregates and paired statistical tests. Older linear-power results and development runs are preserved under `results/archive_previous_experiments/` and are explicitly historical.

Use `experiments/merge_benchmark_batches.py` for seed-disjoint balanced batches and `experiments/analyze_synthetic_results.py` for panel validation and paired analysis. The analysis script rejects duplicate/missing algorithm × seed × scenario cells and applies Holm correction within each metric's baseline-comparison family.

## Scope of claims

The evidence supports promising performance under the declared synthetic workloads. It does not prove universal superiority, real-world energy savings, CloudSim performance, or validation of an upstream learned overload predictor. A strong follow-up should evaluate realistic cloud traces or CloudSim Plus and compare the epsilon-constraint selection policy fairly against baselines. No artifact can guarantee acceptance by a research board or publisher.
