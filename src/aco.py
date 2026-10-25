"""Discrete ant-colony optimization baseline under an objective-evaluation cap."""
import random
import numpy as np
from .baseline import best_fit_decreasing
from .fitness import evaluate, get_evaluation_count, EvaluationBudgetExceeded


def ant_colony(tasks, vms, cfg, seed, max_evaluations=300):
    rng = random.Random(seed)
    start_count = get_evaluation_count()
    budget_end = start_count + int(max_evaluations)
    best, best_metric = best_fit_decreasing(tasks, vms, cfg)
    best = list(best)
    n, m = len(tasks), len(vms)
    if n == 0 or m < 2:
        return best, best_metric, [best_metric.fitness], {"evaluations": get_evaluation_count() - start_count}
    pheromone = np.ones((n, m), dtype=float)
    alpha = float(cfg.get("aco", {}).get("alpha", 1.0))
    evaporation = float(cfg.get("aco", {}).get("evaporation", 0.25))
    q = float(cfg.get("aco", {}).get("deposit", 1.0))
    history = [best_metric.fitness]
    iteration = 0
    while get_evaluation_count() < budget_end:
        iteration += 1
        # Each ant builds a fresh assignment from the VMs' initial loads.
        loads = [float(vm.current_cpu_load) for vm in vms]
        util = [loads[j] / max(float(vms[j].cpu_capacity), 1e-12) for j in range(m)]
        assignment = []
        for i, task in enumerate(tasks):
            desirability = []
            for j in range(m):
                # Heuristic favors capacity headroom, with a mild same-host bias to reduce activation.
                headroom = max(0.02, 1.0 - util[j])
                active_host = any(vms[k].host_id == vms[j].host_id and loads[k] > 1e-12 for k in range(m))
                energy_bias = 1.08 if active_host else 1.0
                desirability.append(max(1e-12, float(pheromone[i, j]) ** alpha * headroom * energy_bias))
            total = sum(desirability); pick = rng.random() * total; acc = 0.0; choice = m - 1
            for j, value in enumerate(desirability):
                acc += value
                if acc >= pick:
                    choice = j; break
            assignment.append(choice)
            loads[choice] += max(0.0, float(task.demand))
            util[choice] = loads[choice] / max(float(vms[choice].cpu_capacity), 1e-12)
        try:
            metric = evaluate(tasks, assignment, vms, cfg)
        except EvaluationBudgetExceeded:
            break
        if metric.fitness < best_metric.fitness:
            best, best_metric = list(assignment), metric
        # Evaporate globally and reinforce the best known assignment; all decisions use predicted demand.
        pheromone *= (1.0 - evaporation)
        np.maximum(pheromone, 1e-6, out=pheromone)
        pheromone[np.arange(n), np.asarray(best, dtype=int)] += q / max(1e-6, best_metric.fitness)
        history.append(best_metric.fitness)
    return best, best_metric, history, {"evaluations": get_evaluation_count() - start_count}
