"""Harris Hawks Optimizer with a strict objective-evaluation-call budget."""
import random
import math
from .fitness import evaluate, repair, EvaluationBudgetExceeded


def hho(tasks, vms, cfg, seed, max_evaluations=None):
    random.seed(seed)
    n = cfg["hho"]["population_size"]
    iters = cfg["hho"]["iterations"]
    d, m = len(tasks), len(vms)
    evaluated = {}
    local_calls = 0

    def fitness(position):
        nonlocal local_calls
        if max_evaluations is not None and local_calls >= max_evaluations:
            raise EvaluationBudgetExceeded("HHO local evaluation budget exhausted")
        assignment = tuple(repair(position, m))
        metric = evaluate(tasks, assignment, vms, cfg)  # count every objective call, including duplicates
        local_calls += 1
        evaluated[assignment] = metric
        return metric.fitness

    pop = [[random.uniform(0, m - 1) for _ in range(d)] for _ in range(n)]
    if d == 0:
        return [], evaluate(tasks, [], vms, cfg), [0.0] * iters, pop
    history = []
    try:
        best = min(pop, key=fitness)
        best_score = fitness(best)
        for t in range(iters):
            prey = min(pop, key=fitness)
            mean = [sum(x[j] for x in pop) / n for j in range(d)]
            nxt = []
            for x in pop:
                E = 2 * (1 - t / max(1, iters)) * (2 * random.random() - 1)
                q, r = random.random(), random.random()
                if abs(E) >= 1:
                    peer = random.choice(pop)
                    y = ([peer[j] - random.random() * abs(peer[j] - 2 * random.random() * x[j])
                          for j in range(d)] if q < .5 else
                         [(prey[j] - mean[j]) - random.random() * ((m - 1) * random.random())
                          for j in range(d)])
                else:
                    J = 2 * (1 - random.random())
                    base = [prey[j] - E * abs(J * prey[j] - x[j]) if r >= .5
                            else prey[j] - E * abs(prey[j] - x[j]) for j in range(d)]
                    dive = [base[j] + 0.01 * math.tan(math.pi * (random.random() - .5)) for j in range(d)]
                    y = dive if fitness(dive) < fitness(base) else base
                nxt.append([min(m - 1, max(0, z)) for z in y])
            pop = nxt
            iteration_best = min(pop, key=fitness)
            iteration_score = fitness(iteration_best)
            if iteration_score < best_score:
                best, best_score = list(iteration_best), iteration_score
            history.append(best_score)
    except EvaluationBudgetExceeded:
        pass

    if not evaluated:
        raise RuntimeError("HHO budget was too small to evaluate any candidate")
    best_assignment = list(min(evaluated, key=lambda assignment: evaluated[assignment].fitness))
    metric = evaluated[tuple(best_assignment)]
    ranked_positions = [list(a) for a in sorted(evaluated, key=lambda assignment: evaluated[assignment].fitness)]
    return best_assignment, metric, history, ranked_positions
