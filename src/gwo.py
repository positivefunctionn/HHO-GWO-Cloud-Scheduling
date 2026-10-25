"""Grey Wolf Optimizer with a strict objective-evaluation-call budget."""
import random
from .fitness import evaluate, repair, EvaluationBudgetExceeded


def gwo(tasks, vms, cfg, seed, initial_population=None, max_evaluations=None):
    random.seed(seed)
    n = cfg["gwo"]["population_size"]
    iters = cfg["gwo"]["iterations"]
    d, m = len(tasks), len(vms)
    evaluated = {}
    local_calls = 0

    def fitness(position):
        nonlocal local_calls
        if max_evaluations is not None and local_calls >= max_evaluations:
            raise EvaluationBudgetExceeded("GWO local evaluation budget exhausted")
        assignment = tuple(repair(position, m))
        metric = evaluate(tasks, assignment, vms, cfg)  # count every objective call, including duplicates
        local_calls += 1
        evaluated[assignment] = metric
        return metric.fitness

    pop = [list(x) for x in (initial_population or [])][:n]
    while len(pop) < n:
        pop.append([random.uniform(0, m - 1) for _ in range(d)])
    if d == 0:
        assignment = []
        metric = evaluate(tasks, assignment, vms, cfg)
        return assignment, metric, [0.0] * iters, pop

    history = []
    try:
        best = min(pop, key=fitness)
        best_score = fitness(best)
        for t in range(iters):
            ranked = sorted(pop, key=fitness)
            leaders = (ranked + [ranked[-1]] * 3)[:3]
            alpha, beta, delta = leaders
            a = 2 - 2 * t / max(1, iters - 1)
            new = []
            for wolf in pop:
                pos = []
                for j, x in enumerate(wolf):
                    vals = []
                    for leader in (alpha, beta, delta):
                        A = 2 * a * random.random() - a
                        C = 2 * random.random()
                        vals.append(leader[j] - A * abs(C * leader[j] - x))
                    pos.append(sum(vals) / 3)
                new.append([min(m - 1, max(0, z)) for z in pos])
            pop = new
            iteration_best = min(pop, key=fitness)
            iteration_score = fitness(iteration_best)
            if iteration_score < best_score:
                best, best_score = list(iteration_best), iteration_score
            history.append(best_score)
    except EvaluationBudgetExceeded:
        pass

    if not evaluated:
        raise RuntimeError("GWO budget was too small to evaluate any candidate")
    best_assignment = list(min(evaluated, key=lambda assignment: evaluated[assignment].fitness))
    metric = evaluated[tuple(best_assignment)]
    ranked_positions = [list(a) for a in sorted(evaluated, key=lambda assignment: evaluated[assignment].fitness)]
    return best_assignment, metric, history, ranked_positions or pop
