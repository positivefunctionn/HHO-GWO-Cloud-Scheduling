# Final project viva notes — convex-power release

## One-minute explanation

“Our proposed HHO–GWO scheduler combines Harris Hawks Optimization for exploration, Grey Wolf Optimization seeded from HHO elites, a budget-charged BFD incumbent, and bounded local relocation refinement. It allocates synthetic tasks to VMs and evaluates a balanced objective built from normalized host-energy proxy, SLA violation rate and makespan. We also test a separate SLA-only objective profile. The host-energy proxy counts aggregate utilization once per active host and uses a configurable convex power curve; the final runs use exponent alpha = 2.0.”

## What are the strongest results?

There are two separate experiments, not one all-metric win:

- **Balanced profile:** 20 paired seeds × 9 synthetic scenarios × 7 algorithms = 1,260 runs. HHO–GWO had the lowest observed mean composite fitness (0.34711) and mean makespan (0.99724). The composite-fitness difference versus ABC was not statistically significant after Holm correction (adjusted p = 0.1429). The makespan difference versus ACO was significant under the stated seed-level paired Wilcoxon test with Holm correction (adjusted p = 0.00730).
- **SLA-focused profile:** 20 paired seeds × 9 scenarios × 7 algorithms = 1,260 runs. HHO–GWO had the lowest mean SLA violation rate (27.42%); versus GWO's 31.58%, this is a 13.18% relative reduction. The reported Holm-adjusted one-sided paired Wilcoxon p-value versus GWO is 0.000241.

## Does HHO–GWO win every metric?

No. In the balanced experiment, WOA has the lowest energy proxy and GWO has the lowest SLA violation rate. The balanced HHO–GWO uses an 8% epsilon-constraint policy to choose the lowest makespan among candidates within tolerance of its best composite fitness. This policy is not applied to the single-objective baselines and is a fairness limitation that should be acknowledged and studied with an ablation or comparable baseline selection policy.

## What does the energy number mean?

It is a synthetic host-power proxy, not measured watts, joules, cloud cost or carbon. For active hosts the model uses `P(u)=P_idle+(P_max-P_idle)*u^alpha`, where `u` is aggregate host utilization clipped to [0,1]. The final runs use alpha = 2.0. An inactive host is assumed to consume zero power. These assumptions require calibration before real energy claims.

## What are the limitations?

1. Workloads are synthetic; results do not establish performance on production cloud traces.
2. The project has not been validated in CloudSim Plus.
3. Host power/capacity values are assumptions, not measured hardware data.
4. The smoke test validates the data handoff schema, not the predictive accuracy or calibration of the upstream BiLSTM.
5. The balanced epsilon-constraint policy creates a comparator asymmetry.
6. Statistical significance applies only to the declared benchmark and testing protocol, not to every cloud workload.

## If asked what happens next

Evaluate the schedule assignments in a configured CloudSim Plus simulation or on a realistic independent workload trace, calibrate the host power model, and add an ablation or comparable epsilon-constraint policy for the baselines. See `docs/REPRODUCIBILITY_AUDIT.md` for the exact protocols and output files.
