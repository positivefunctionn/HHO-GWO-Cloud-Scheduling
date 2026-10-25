"""Simulated annealing baseline with a strict objective-evaluation budget."""
import math
import random
from .baseline import best_fit_decreasing
from .fitness import evaluate, get_evaluation_count, EvaluationBudgetExceeded


def simulated_annealing(tasks, vms, cfg, seed, max_evaluations=300):
    rng = random.Random(seed)
    start_count = get_evaluation_count()
    budget_end = start_count + int(max_evaluations)
    current, current_metric = best_fit_decreasing(tasks, vms, cfg)
    best, best_metric = list(current), current_metric
    history = [best_metric.fitness]
    if len(tasks) == 0 or len(vms) < 2:
        return best, best_metric, history, {"evaluations": get_evaluation_count() - start_count}
    # Geometric cooling; candidate generation biases toward tasks on highly loaded VMs.
    temp0 = max(0.01, float(cfg.get("sa", {}).get("initial_temperature", 0.08)))
    temp_min = max(1e-5, float(cfg.get("sa", {}).get("minimum_temperature", 0.0005)))
    iteration = 0
    while get_evaluation_count() < budget_end:
        iteration += 1
        loads = [float(vm.current_cpu_load) for vm in vms]
        for task, vm_idx in zip(tasks, current):
            loads[vm_idx] += max(0.0, float(task.demand))
        util = [loads[i] / max(float(vms[i].cpu_capacity), 1e-12) for i in range(len(vms))]
        weights = [max(0.0, float(t.demand)) * (1.0 + util[current[i]]) for i, t in enumerate(tasks)]
        total = sum(weights)
        if total > 0:
            pick = rng.random() * total
            accum = 0.0; task_idx = len(tasks) - 1
            for i, weight in enumerate(weights):
                accum += weight
                if accum >= pick:
                    task_idx = i; break
        else:
            task_idx = rng.randrange(len(tasks))
        candidate = list(current)
        source = candidate[task_idx]
        destinations = [j for j in range(len(vms)) if j != source]
        # Mostly favor same-host moves (potential VM-level balance without waking a host).
        destinations.sort(key=lambda j: (vms[j].host_id != vms[source].host_id, util[j], rng.random()))
        shortlist = destinations[:max(1, min(4, len(destinations)))]
        candidate[task_idx] = rng.choice(shortlist)
        try:
            metric = evaluate(tasks, candidate, vms, cfg)
        except EvaluationBudgetExceeded:
            break
        temp = max(temp_min, temp0 * (0.985 ** iteration))
        delta = metric.fitness - current_metric.fitness
        if delta <= 0 or rng.random() < math.exp(-min(700.0, delta / temp)):
            current, current_metric = candidate, metric
        if metric.fitness < best_metric.fitness:
            best, best_metric = list(candidate), metric
        history.append(best_metric.fitness)
    return best, best_metric, history, {"evaluations": get_evaluation_count() - start_count}
