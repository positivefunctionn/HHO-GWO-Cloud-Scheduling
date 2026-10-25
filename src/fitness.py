"""Objective evaluation, evaluation-call accounting, and realized-metric evaluation.

Legacy prediction-trace experiments retain their original objective. The rigorous
synthetic benchmark selects objective_mode='three_term_host_energy_v1'.
"""
import math
from .models import ScheduleMetrics
from .overload import risk_cost

_EVALUATION_COUNT = 0
_EVALUATION_LIMIT = None


class EvaluationBudgetExceeded(RuntimeError):
    """Raised when another objective evaluation would exceed the configured cap."""


def reset_evaluation_count(limit=None):
    global _EVALUATION_COUNT, _EVALUATION_LIMIT
    _EVALUATION_COUNT = 0
    _EVALUATION_LIMIT = None if limit is None else max(0, int(limit))


def get_evaluation_count():
    return _EVALUATION_COUNT


def get_evaluation_limit():
    return _EVALUATION_LIMIT


def decode(position, vm_count):
    return min(vm_count - 1, max(0, int(round(position))))


def repair(position, vm_count):
    return [decode(x, vm_count) for x in position]


def _metrics_for_demand(tasks, assignment, vms, cfg, demand_attribute="demand"):
    if len(tasks) != len(assignment):
        raise ValueError("assignment length differs from task count")
    if not vms:
        raise ValueError("at least one VM is required")
    repaired_assignment = repair(assignment, len(vms))
    demands = []
    loads = [v.current_cpu_load for v in vms]
    completion = [0.0] * len(vms)
    for task, idx in zip(tasks, repaired_assignment):
        demand = getattr(task, demand_attribute, None)
        if demand is None:
            demand = task.demand
        demand = max(0.0, float(demand))
        demands.append(demand)
        vm = vms[idx]
        loads[idx] += demand
        completion[idx] += demand / vm.cpu_capacity

    # SLA is evaluated against the final assigned load, not the order in which
    # tasks happened to be visited. Every task on an overloaded VM is counted.
    utils = [load / v.cpu_capacity for load, v in zip(loads, vms)]
    violations = 0
    risk = 0.0
    for task, idx, demand in zip(tasks, repaired_assignment, demands):
        util = utils[idx]
        execution = demand / vms[idx].cpu_capacity
        bad = util > cfg["allowable_utilization"] or execution > cfg["execution_sla"]
        violations += int(bad)
        risk += risk_cost(task, util, cfg.get("safe_utilization", 0.65), cfg.get("risk_penalty", 2.0))

    if cfg.get("objective_mode") == "three_term_host_energy_v1":
        # Host power is counted once per host, not once per VM. Hosts with no load
        # are off and consume zero power in this explicitly defined synthetic model.
        host_loads = {host["host_id"]: 0.0 for host in cfg["hosts"]}
        for vm, load in zip(vms, loads):
            host_loads[vm.host_id] = host_loads.get(vm.host_id, 0.0) + load
        host_specs = {host["host_id"]: host for host in cfg["hosts"]}
        energy = 0.0
        for host_id, host in host_specs.items():
            load = host_loads.get(host_id, 0.0)
            if load > 1e-12:
                util = min(1.0, max(0.0, load / host["cpu_capacity"]))
                exponent = float(cfg.get("host_power_curve_exponent", 2.0))
                if not math.isfinite(exponent) or exponent < 1.0:
                    raise ValueError("host_power_curve_exponent must be finite and >= 1.0")
                # Convex host power proxy: P(u) = P_idle + (P_max - P_idle) * u**alpha.
                # alpha > 1 is convex; alpha = 1 recovers a linear model.
                power = host["idle_power"] + (host["max_power"] - host["idle_power"]) * (util ** exponent)
                energy += power * cfg["scheduling_interval"]
    else:
        # Preserve the legacy VM-level proxy for the original trace integration.
        energy = sum((v.idle_power + (v.max_power - v.idle_power) * u) * cfg["scheduling_interval"]
                     for v, u in zip(vms, utils))

    makespan = max(completion, default=0.0)
    mean_util = sum(utils) / len(utils) if utils else 0.0
    imbalance = (math.sqrt(sum((u - mean_util) ** 2 for u in utils) / len(utils)) if utils else 0.0)
    sla_rate = violations / len(tasks) if tasks else 0.0
    refs = cfg["normalization_references"]
    weights = cfg["weights"]
    if cfg.get("objective_mode") == "three_term_host_energy_v1":
        score = (weights["energy"] * energy / refs["energy"]
                 + weights["sla"] * sla_rate / refs["sla"]
                 + weights["makespan"] * makespan / refs["makespan"])
    else:
        sla = sla_rate + risk
        score = (weights["energy"] * energy / refs["energy"]
                 + weights["makespan"] * makespan / refs["makespan"]
                 + weights["sla"] * sla / refs["sla"]
                 + weights["imbalance"] * imbalance / refs["imbalance"])
    return ScheduleMetrics(score, energy, makespan, violations, imbalance, mean_util,
                           sum(u > cfg["allowable_utilization"] for u in utils))


def evaluate(tasks, assignment, vms, cfg):
    """Evaluate predicted demand and count every objective-function call."""
    global _EVALUATION_COUNT
    if _EVALUATION_LIMIT is not None and _EVALUATION_COUNT >= _EVALUATION_LIMIT:
        raise EvaluationBudgetExceeded(f"objective-evaluation budget ({_EVALUATION_LIMIT}) exhausted")
    _EVALUATION_COUNT += 1
    return _metrics_for_demand(tasks, assignment, vms, cfg, "demand")


def evaluate_realized(tasks, assignment, vms, cfg):
    """Evaluate a fixed assignment with actual_demand, without affecting search budget."""
    return _metrics_for_demand(tasks, assignment, vms, cfg, "actual_demand")
