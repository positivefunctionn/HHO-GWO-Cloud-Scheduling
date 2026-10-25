# Expanded 12-VM / 6-host synthetic benchmark recipe

This is a recipe for running an expanded synthetic experiment. It is not the source of the currently audited final results. For the current report and verified output directories, read `FINAL_PROJECT_RESULTS_REPORT.md` and `REPRODUCIBILITY_AUDIT.md`.

- 12 VMs across 6 hosts, 2 VMs per host.
- Task counts: 20, 50, 100.
- Offered-load levels: low, moderate, high.
- The runner records the objective profile, seed IDs, power assumptions, evaluation budget, hybrid budget split, and selection-policy description in `protocol.json`.
- Synthetic workloads and host power assumptions only; not CloudSim or production validation.

Example balanced run:

```bash
py experiments/run_synthetic_benchmark.py --seeds 20 --seed-start 18001 --task-counts 20,50,100 --load-levels low,moderate,high --vm-count 12 --vms-per-host 2 --evaluation-budget 300 --objective-profile balanced --algorithms "ACO,WOA,ABC,GWO,GA,HHO,HHO-GWO" --output results/reproduction_expanded_balanced
py experiments/analyze_synthetic_results.py results/reproduction_expanded --reference HHO-GWO --metrics realized_fitness,realized_energy,realized_sla_rate,realized_makespan,load_imbalance --alternative two-sided
```

Use a fresh output directory for every new experiment and record the protocol before interpreting results.
