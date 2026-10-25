"""Particle Swarm Optimization with a strict objective-evaluation-call budget."""
import random
from .fitness import evaluate, repair, EvaluationBudgetExceeded


def pso(tasks, vms, cfg, seed, max_evaluations=None):
    random.seed(seed)
    n, iters = cfg["pso"]["population_size"], cfg["pso"]["iterations"]
    d, m = len(tasks), len(vms)
    evaluated = {}
    local_calls = 0
    def score(position):
        nonlocal local_calls
        if max_evaluations is not None and local_calls >= max_evaluations:
            raise EvaluationBudgetExceeded("PSO local evaluation budget exhausted")
        assignment = tuple(repair(position, m))
        metric = evaluate(tasks, assignment, vms, cfg)
        local_calls += 1
        evaluated[assignment] = metric
        return metric.fitness
    if d == 0:
        return [], evaluate(tasks, [], vms, cfg), [0.0] * iters, []
    positions = [[random.uniform(0, m - 1) for _ in range(d)] for _ in range(n)]
    velocities = [[random.uniform(-1, 1) for _ in range(d)] for _ in range(n)]
    pbest = [p[:] for p in positions]
    history = []
    inertia = cfg["pso"].get("inertia", 0.7)
    c1, c2 = cfg["pso"].get("cognitive", 1.4), cfg["pso"].get("social", 1.4)
    try:
        pbest_scores = [score(p) for p in pbest]
        k = min(range(n), key=lambda i: pbest_scores[i])
        gbest, gbest_score = pbest[k][:], pbest_scores[k]
        for _ in range(iters):
            for i in range(n):
                for j in range(d):
                    r1, r2 = random.random(), random.random()
                    velocities[i][j] = (inertia * velocities[i][j] + c1 * r1 * (pbest[i][j] - positions[i][j])
                                        + c2 * r2 * (gbest[j] - positions[i][j]))
                    positions[i][j] = min(m - 1, max(0, positions[i][j] + velocities[i][j]))
                candidate_score = score(positions[i])
                if candidate_score < pbest_scores[i]:
                    pbest[i], pbest_scores[i] = positions[i][:], candidate_score
                    if candidate_score < gbest_score:
                        gbest, gbest_score = positions[i][:], candidate_score
            history.append(gbest_score)
    except EvaluationBudgetExceeded:
        pass
    if not evaluated:
        raise RuntimeError("PSO budget was too small to evaluate any candidate")
    best_assignment = list(min(evaluated, key=lambda a: evaluated[a].fitness))
    return best_assignment, evaluated[tuple(best_assignment)], history, pbest
