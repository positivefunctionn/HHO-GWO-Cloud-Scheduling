"""Genetic Algorithm with a strict objective-evaluation-call budget."""
import random
from .fitness import evaluate, repair, EvaluationBudgetExceeded


def ga(tasks, vms, cfg, seed, max_evaluations=None):
    random.seed(seed)
    n, iters = cfg["ga"]["population_size"], cfg["ga"]["iterations"]
    d, m = len(tasks), len(vms)
    evaluated = {}
    local_calls = 0
    def score(individual):
        nonlocal local_calls
        if max_evaluations is not None and local_calls >= max_evaluations:
            raise EvaluationBudgetExceeded("GA local evaluation budget exhausted")
        assignment = tuple(repair(individual, m))
        metric = evaluate(tasks, assignment, vms, cfg)
        local_calls += 1
        evaluated[assignment] = metric
        return metric.fitness
    if d == 0:
        return [], evaluate(tasks, [], vms, cfg), [0.0] * iters, []
    pop = [[random.uniform(0, m - 1) for _ in range(d)] for _ in range(n)]
    history = []
    elite_count = max(1, min(n, cfg["ga"].get("elite_count", 2)))
    crossover_rate = cfg["ga"].get("crossover_rate", 0.8)
    mutation_rate = cfg["ga"].get("mutation_rate", 0.08)
    try:
        best = min(pop, key=score)[:]
        best_score = score(best)
        for _ in range(iters):
            ranked = sorted(pop, key=score)
            if score(ranked[0]) < best_score:
                best, best_score = ranked[0][:], score(ranked[0])
            nxt = [x[:] for x in ranked[:elite_count]]
            while len(nxt) < n:
                def tournament():
                    contestants = random.sample(ranked, min(3, len(ranked)))
                    return min(contestants, key=score)[:]
                p1, p2 = tournament(), tournament()
                child = p1[:]
                if d > 1 and random.random() < crossover_rate:
                    cut = random.randint(1, d - 1)
                    child = p1[:cut] + p2[cut:]
                for j in range(d):
                    if random.random() < mutation_rate:
                        child[j] = random.uniform(0, m - 1)
                nxt.append([min(m - 1, max(0, x)) for x in child])
            pop = nxt
            gen_best = min(pop, key=score)
            if score(gen_best) < best_score:
                best, best_score = gen_best[:], score(gen_best)
            history.append(best_score)
    except EvaluationBudgetExceeded:
        pass
    if not evaluated:
        raise RuntimeError("GA budget was too small to evaluate any candidate")
    best_assignment = list(min(evaluated, key=lambda a: evaluated[a].fitness))
    return best_assignment, evaluated[tuple(best_assignment)], history, pop
