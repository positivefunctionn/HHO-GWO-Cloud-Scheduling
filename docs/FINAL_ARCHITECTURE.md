# Proposed HHO-GWO scheduler architecture

```text
Task/workload input
        |
        v
Predicted task demand and VM/host configuration
        |
        v
HHO exploration --------------------------+
        |                                  |
        v                                  |
Ranked elite candidate schedules           |
        |                                  |
        v                                  |
GWO refinement seeded from HHO elites       |
        |                                  |
        +----------> Incumbent comparison <-+--- budget-charged BFD seed
                           |
                           v
              Iterated local relocation search
              (remaining objective-evaluation budget)
                           |
                           v
                Best-known schedule returned
                           |
                           v
        Independent realized-metric evaluation
        (energy, SLA violations, makespan, fitness)
```

## Important separation

- Search uses the synthetic predicted-demand values only.
- Actual demand is generated for post-schedule evaluation and is not used to select candidate assignments.
- A single objective-evaluation counter caps the hybrid's search calls.
- The BFD candidate inside HHO-GWO is charged against the same hybrid budget; it is an initialization candidate, not an extra free comparator run.
- Budget fractions are experiment-specific and are recorded in each `protocol.json`: the audited balanced experiment uses 5% HHO / 5% GWO / 90% local refinement (300 evaluations); the audited SLA-focused experiment uses 5% HHO / 45% GWO / 50% local refinement (100 evaluations).
- Balanced-profile HHO–GWO applies an 8% epsilon-constraint selection policy to favor makespan among candidates within tolerance of its best composite fitness. The SLA-focused profile returns the best incumbent for its SLA-only objective. These are distinct objective profiles, not one combined ranking.
- The model counts power once per active host using `P(u)=P_idle+(P_max-P_idle)*u^alpha`, with configurable `alpha >= 1` (the final runs use alpha = 2.0). This is a synthetic convex proxy, not a physical power measurement.
