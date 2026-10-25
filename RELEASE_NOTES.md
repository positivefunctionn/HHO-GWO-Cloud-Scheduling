# Release notes — final convex-power research release

Release date: 2026-10-25

## Included changes

- Corrected host-level energy proxy to use configurable `P(u)=P_idle+(P_max-P_idle)*u^alpha` with `alpha >= 1`; final benchmarks use `alpha = 2.0`.
- Added validation rejecting invalid power exponents and tests for convex vs linear behavior.
- Re-ran both objective profiles under the corrected power model: 1,260 balanced runs and 1,260 SLA-focused runs.
- Added protocol metadata for the power formula, exponent, objective profile, hybrid budget split, and selection policy.
- Added generic benchmark panel validation and paired statistical analysis with Holm correction.
- Added seed-disjoint batch merge validation.
- Added Windows scripts for checks and full reproduction.
- Rewrote current reports to distinguish balanced and SLA-focused experiments, disclose the epsilon-constraint policy asymmetry, and label the energy values as synthetic proxy units.
- Preserved older linear-power and intermediate outputs in `results/archive_previous_experiments/` for traceability.

## Verification in the build environment

- Python 3.13.5.
- Unit tests: 12/12 passed.
- Smoke test: 1,320 schedules generated; 1,094 rows passed the declared schema validation.
- Balanced experiment: 1,260 unique algorithm × seed × scenario rows; all expected panel cells present.
- SLA-focused experiment: 1,260 unique algorithm × seed × scenario rows; all expected panel cells present.

## Known limitations

- Synthetic workloads; no CloudSim Plus or production-trace validation.
- Power parameters are assumed; no measured physical energy data.
- Balanced HHO–GWO uses an 8% epsilon-constraint selection policy not applied to single-objective baselines.
- The smoke test does not validate an upstream BiLSTM's predictive accuracy or calibration.
