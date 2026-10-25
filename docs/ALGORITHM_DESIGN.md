# Algorithm design and integration

The scheduler comparison includes BFD, GWO, HHO, sequential HHO→GWO, PSO and GA. All methods operate on the same normalized internal task representation and use the shared fitness function. GWO, HHO, PSO and GA use real-valued candidate vectors that are rounded/repaired to discrete VM indices; HHO→GWO seeds the GWO population with HHO-ranked candidates.

The objective is the configured weighted normalized sum of energy, makespan, SLA penalty, and load imbalance. Risk cost uses the available overload-risk field. The current Person 1 handoff contains a binary overload flag but no calibrated probability; the integration therefore uses that flag as a documented 0/1 risk-score proxy, not as a probability. Ask Person 1 for a calibrated overload probability if the probability-based penalty is required.

The source predictions are not rewritten. Negative predicted CPU values are logged and only the derived nonnegative demand is floored at zero. Values above 100 are retained. Actual CPU is evaluation-only and is not used in the optimizer's fitness function.

Because the handoff contains time-series observations rather than independent tasks and VM metadata, task-to-VM allocations and performance metrics are synthetic proxies. They are not CloudSim results and should not be described as such. The hybrid also performs more internal objective evaluations than some standalone methods under equal iteration settings; use the reported evaluation counts when interpreting results.
