# Beginner guide

Person 1 predicts CPU and overload risk; Person 2 uses those predictions to choose VM placements. `predicted_cpu` supplies workload magnitude, while `p_overload` describes workload risk and τ=0.18 is Person 1's fixed decision threshold. A horizon is a short batch; its rows are modeled as synthetic tasks solely for this experiment.

BFD is deterministic tight-fit packing. HHO searches schedules with hawk behaviors; GWO refines schedules around its three leaders. HHO comes first in the hybrid to discover diverse promising schedules, then GWO receives HHO's elites to refine them. Continuous optimizer values need repair because VM IDs are discrete. A common normalized objective balances proxy energy, completion-time makespan, SLA/risk, and utilization balance. If no safe VM exists, the least-bad placement is retained and a violation is recorded. Person 3 later replaces proxies with CloudSim evaluation.
