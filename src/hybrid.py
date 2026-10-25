"""Budgeted HHO -> GWO hybrid with global-best retention and local refinement.

The optimizer sees predicted task demand only. Realized demand is used only by
``evaluate_realized`` in the experiment runner. The hybrid preserves the best
solution found by HHO, GWO, or a deterministic BFD seed, then spends the remaining
budget on iterated local refinement. All objective calls share one budget counter.
"""
import random

from .fitness import (
    EvaluationBudgetExceeded,
    evaluate,
    get_evaluation_count,
)
from .hho import hho
from .gwo import gwo
from .baseline import best_fit_decreasing


def _local_relocation_search(tasks, vms, cfg, start_assignment, start_metric,
                             absolute_budget_end, seed):
    """Iterated local search with guided relocations and bounded perturbations.

    Unlike a single deterministic scan, this explores several basins under the
    same objective-evaluation cap. Every accepted best solution is evaluated by
    the shared objective; no realized-demand information leaks into search.
    """
    rng = random.Random(seed)
    global_best = list(start_assignment)
    global_metric = start_metric
    # Keep candidate schedules for the balanced-profile epsilon-constraint
    # selection. Pure SLA/energy profiles return their best incumbent for the
    # active objective instead of trading that objective for makespan.
    pareto_candidates = [(list(start_assignment), start_metric)]
    local_start = get_evaluation_count()
    task_count, vm_count = len(tasks), len(vms)
    weights = cfg.get("weights", {})
    sla_objective = (
        float(weights.get("sla", 0.0)) > 0.999
        and float(weights.get("energy", 0.0)) < 1e-9
        and float(weights.get("makespan", 0.0)) < 1e-9
    )
    if task_count == 0 or vm_count < 2:
        return global_best, global_metric, 0

    def load_state(assignment):
        loads = [float(vm.current_cpu_load) for vm in vms]
        for task, vm_idx in zip(tasks, assignment):
            loads[vm_idx] += max(0.0, float(task.demand))
        utils = [loads[i] / max(float(vms[i].cpu_capacity), 1e-12)
                 for i in range(vm_count)]
        active_hosts = {vms[i].host_id for i, load in enumerate(loads) if load > 1e-12}
        return loads, utils, active_hosts

    # Try a modest number of strategically biased candidate moves per descent
    # pass. This leaves room for multiple restarts even on 100-task scenarios.
    while get_evaluation_count() < absolute_budget_end:
        current = list(global_best)
        current_metric = global_metric
        _, utils, active_hosts = load_state(current)

        # Iterated perturbation: escape the current one-move local optimum by
        # relocating a small bundle of tasks before descending again.
        if get_evaluation_count() + 1 <= absolute_budget_end and task_count >= 2:
            perturbed = current.copy()
            k_max = min(6, task_count)
            k = rng.randint(2, k_max)
            chosen = rng.sample(range(task_count), k)
            for task_idx in chosen:
                source = perturbed[task_idx]
                choices = [j for j in range(vm_count) if j != source]
                # Prefer an already-active host, then the least loaded VM.
                choices.sort(key=lambda j: (
                    0 if vms[j].host_id in active_hosts else 1,
                    utils[j], rng.random()))
                shortlist = choices[:max(1, min(3, len(choices)))]
                perturbed[task_idx] = rng.choice(shortlist)
            try:
                perturbed_metric = evaluate(tasks, perturbed, vms, cfg)
                pareto_candidates.append((list(perturbed), perturbed_metric))
                # Continue from this basin even if it is temporarily worse; the
                # global incumbent is retained separately and can never regress.
                current, current_metric = perturbed, perturbed_metric
                if perturbed_metric.fitness < global_metric.fitness - 1e-12:
                    global_best, global_metric = list(perturbed), perturbed_metric
            except EvaluationBudgetExceeded:
                break

        improved_this_round = False
        # Two small neighborhood passes are often more useful than spending the
        # entire budget on the first few moves of a large deterministic scan.
        for _pass in range(2):
            if get_evaluation_count() >= absolute_budget_end:
                break
            loads, utils, active_hosts = load_state(current)
            task_order = sorted(
                range(task_count),
                key=lambda i: (utils[current[i]], max(0.0, float(tasks[i].demand))),
                reverse=True,
            )
            # Sample across the whole assignment while retaining bias toward
            # overloaded sources and energy-friendly same-host destinations.
            candidate_moves = []
            # Makespan-aware neighborhood ordering: estimate the completion-time
            # impact of moving each task, while retaining energy-friendly moves
            # to the same host and already-active hosts. This is only a proposal
            # ordering heuristic; every accepted move is still evaluated by the
            # shared, unchanged composite objective.
            completion = [0.0] * vm_count
            for ti, assigned_vm in enumerate(current):
                completion[assigned_vm] += max(0.0, float(tasks[ti].demand)) / max(float(vms[assigned_vm].cpu_capacity), 1e-12)
            for task_idx in task_order:
                source = current[task_idx]
                demand = max(0.0, float(tasks[task_idx].demand))
                destinations = []
                for target in range(vm_count):
                    if target == source:
                        continue
                    projected = completion.copy()
                    projected[source] -= demand / max(float(vms[source].cpu_capacity), 1e-12)
                    projected[target] += demand / max(float(vms[target].cpu_capacity), 1e-12)
                    projected_makespan = max(projected, default=0.0)
                    # For SLA-focused runs, rank destinations by the exact
                    # predicted number of violating tasks after this relocation.
                    # Other profiles retain makespan-first ordering.
                    if sla_objective:
                        projected_loads = loads.copy()
                        projected_loads[source] -= demand
                        projected_loads[target] += demand
                        projected_utils = [projected_loads[i] / max(float(vms[i].cpu_capacity), 1e-12)
                                            for i in range(vm_count)]
                        projected_sla = 0
                        for ti, assigned_vm in enumerate(current):
                            final_vm = target if ti == task_idx else assigned_vm
                            task_demand = max(0.0, float(tasks[ti].demand))
                            if (projected_utils[final_vm] > float(cfg["allowable_utilization"])
                                    or task_demand / max(float(vms[final_vm].cpu_capacity), 1e-12)
                                    > float(cfg["execution_sla"])):
                                projected_sla += 1
                        primary_score = projected_sla
                    else:
                        primary_score = projected_makespan
                    tie = (0 if vms[target].host_id == vms[source].host_id else 1,
                           0 if vms[target].host_id in active_hosts else 1,
                           utils[target], target)
                    destinations.append((primary_score, projected_makespan, tie, target))
                destinations.sort(key=lambda item: (item[0], item[1], item[2]))
                # Preserve neighborhood diversity while prioritizing the active
                # objective (SLA count for SLA-focused runs; makespan otherwise).
                selected = []
                for _, _, _, target in destinations:
                    if target not in selected:
                        selected.append(target)
                    if len(selected) >= min(3, len(destinations)):
                        break
                for primary_score, projected_makespan, _, target in destinations:
                    if target in selected:
                        candidate_moves.append((primary_score, projected_makespan, task_idx, target))
            # Screen the neighborhood toward the active objective, while keeping
            # a bounded number of objective evaluations under the shared budget.
            candidate_moves.sort(key=lambda item: (item[0], item[1], item[2], item[3]))
            limit = min(len(candidate_moves), max(12, min(36, task_count // 2 + 12)))
            candidate_moves = [(task_idx, target) for _, _, task_idx, target in candidate_moves[:limit]]
            round_best_assignment = None
            round_best_metric = current_metric
            for task_idx, target in candidate_moves:
                if get_evaluation_count() >= absolute_budget_end:
                    break
                candidate = current.copy()
                candidate[task_idx] = target
                try:
                    metric = evaluate(tasks, candidate, vms, cfg)
                    pareto_candidates.append((list(candidate), metric))
                except EvaluationBudgetExceeded:
                    break
                if metric.fitness < round_best_metric.fitness - 1e-12:
                    round_best_assignment, round_best_metric = candidate, metric
            if round_best_assignment is None:
                break
            current, current_metric = round_best_assignment, round_best_metric
            improved_this_round = True
            if current_metric.fitness < global_metric.fitness - 1e-12:
                global_best, global_metric = list(current), current_metric

        # If no improvement was found, the next loop perturbs the best-known
        # incumbent again, instead of stopping after one unlucky neighborhood.
        if not improved_this_round and get_evaluation_count() >= absolute_budget_end:
            break

    # Selection must respect the declared objective profile. For single-objective
    # energy or SLA runs, return the best incumbent for that exact objective;
    # do not trade away up to 8% of the target metric for makespan. For the
    # balanced profile, retain the documented epsilon-constraint compromise.
    weights = cfg.get("weights", {})
    energy_weight = float(weights.get("energy", 0.0))
    sla_weight = float(weights.get("sla", 0.0))
    makespan_weight = float(weights.get("makespan", 0.0))
    pure_energy = energy_weight > 0.999 and sla_weight < 1e-9 and makespan_weight < 1e-9
    pure_sla = sla_weight > 0.999 and energy_weight < 1e-9 and makespan_weight < 1e-9
    if pure_energy or pure_sla:
        return global_best, global_metric, get_evaluation_count() - local_start

    # Balanced-profile epsilon constraint: among candidates no more than 8%
    # worse than the best fitness, select the lowest makespan, then fitness.
    threshold = global_metric.fitness * 1.08
    eligible = [(assignment, metric) for assignment, metric in pareto_candidates
                if metric.fitness <= threshold + 1e-12]
    if eligible:
        selected_assignment, selected_metric = min(
            eligible,
            key=lambda item: (item[1].makespan, item[1].fitness),
        )
        return selected_assignment, selected_metric, get_evaluation_count() - local_start
    return global_best, global_metric, get_evaluation_count() - local_start


def hho_gwo(tasks, vms, cfg, seed, max_evaluations=None):
    """Run HHO exploration, GWO refinement, then budgeted local improvement.

    When a total budget is supplied, the HHO and GWO stage fractions are read from
    cfg["hybrid_budget"]. Different declared experiment profiles may use different
    fractions; the protocol file must record the selected values. Unused stage budget is not wasted:
    the GWO/local stages can use any still-available evaluations up to the shared
    total cap. The best schedule across all stages is returned, never just the
    last stage's result.
    """
    start_count = get_evaluation_count()
    if max_evaluations is None:
        # Keep a bounded, reproducible default when called outside the benchmark.
        hho_cap = max(1, cfg["hho"]["population_size"] * (cfg["hho"]["iterations"] + 1) * 4)
        gwo_cap = max(1, cfg["gwo"]["population_size"] * (cfg["gwo"]["iterations"] + 1) * 4)
        total_budget = hho_cap + gwo_cap + max(1, len(tasks) * max(0, len(vms) - 1))
    else:
        total_budget = max(1, int(max_evaluations))
        fractions = cfg.get("hybrid_budget", {})
        hho_fraction = float(fractions.get("hho_fraction", 0.10))
        gwo_fraction = float(fractions.get("gwo_fraction", 0.25))
        if hho_fraction <= 0 or gwo_fraction <= 0 or hho_fraction + gwo_fraction >= 1.0:
            raise ValueError("hybrid budget fractions must be positive and sum to less than 1")
        hho_cap = max(1, int(total_budget * hho_fraction))
        gwo_cap = max(1, int(total_budget * gwo_fraction))

    absolute_budget_end = start_count + total_budget
    hho_cap = min(hho_cap, total_budget)
    hho_result = hho(tasks, vms, cfg, seed, max_evaluations=hho_cap)
    hho_assignment, hho_metric, hho_history, ranked = hho_result
    hho_used = get_evaluation_count() - start_count

    # Build a diverse seeded population from HHO's ranked candidates.
    elite_count = min(cfg["hho"].get("elite_size", 4), len(ranked))
    elite = [list(x) for x in ranked[:elite_count]]
    rng = random.Random(seed + 100000)
    vm_count = len(vms)
    seeds = [x.copy() for x in elite]
    while seeds and len(seeds) < cfg["gwo"]["population_size"]:
        parent = elite[len(seeds) % len(elite)]
        perturbed = [min(vm_count - 1, max(0, x + rng.uniform(-0.5, 0.5))) for x in parent]
        seeds.append(perturbed)

    best_assignment = list(hho_assignment)
    best_metric = hho_metric
    best_source = "HHO"
    # Include a deterministic constructive incumbent. This is not a separate
    # comparator advantage: its objective call is charged to the same hybrid cap.
    if get_evaluation_count() < absolute_budget_end:
        try:
            bfd_assignment, bfd_metric = best_fit_decreasing(tasks, vms, cfg)
            if bfd_metric.fitness < best_metric.fitness:
                best_assignment = list(bfd_assignment)
                best_metric = bfd_metric
                best_source = "BFD-seed"
        except EvaluationBudgetExceeded:
            pass
    gwo_used = 0
    gwo_history = []
    if seeds and get_evaluation_count() < absolute_budget_end:
        remaining_total = absolute_budget_end - get_evaluation_count()
        stage_cap = min(gwo_cap, max(1, remaining_total))
        try:
            gwo_result = gwo(tasks, vms, cfg, seed + 1, seeds, max_evaluations=stage_cap)
            gwo_assignment, gwo_metric, gwo_history = gwo_result[:3]
            if gwo_metric.fitness < best_metric.fitness:
                best_assignment = list(gwo_assignment)
                best_metric = gwo_metric
                best_source = "GWO"
        except EvaluationBudgetExceeded:
            pass
        gwo_used = get_evaluation_count() - start_count - hho_used

    before_local = get_evaluation_count()
    if get_evaluation_count() < absolute_budget_end:
        try:
            local_assignment, local_metric, _ = _local_relocation_search(
                tasks, vms, cfg, best_assignment, best_metric,
                absolute_budget_end, seed + 200000,
            )
            current_quality = best_metric.makespan
            local_quality = local_metric.makespan
            within_composite_tolerance = local_metric.fitness <= best_metric.fitness * 1.08
            if (local_metric.fitness < best_metric.fitness - 1e-12
                    or (within_composite_tolerance and local_quality < current_quality - 1e-12)):
                best_assignment = local_assignment
                best_metric = local_metric
                best_source = "local_refinement_epsilon_constraint"
        except EvaluationBudgetExceeded:
            pass
    local_used = get_evaluation_count() - before_local

    details = {
        "hho_elite_count": len(elite),
        "gwo_seeded_population": len(seeds),
        "hho_evaluations": hho_used,
        "gwo_evaluations": gwo_used,
        "local_search_evaluations": local_used,
        "best_source": best_source,
        "total_evaluations": get_evaluation_count() - start_count,
        "total_budget": total_budget,
    }
    return best_assignment, best_metric, hho_history + gwo_history, details
