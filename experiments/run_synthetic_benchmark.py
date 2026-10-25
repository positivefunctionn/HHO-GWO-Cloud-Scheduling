"""Controlled synthetic scheduling benchmark; not a Bitbrains performance claim.

Default protocol: 3 task counts x 3 offered-load levels x 30 paired seeds,
with multiple algorithms and a shared 300 objective-evaluation cap for each metaheuristic.
"""
import argparse
import csv
import json
import random
import statistics
import sys
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import yaml
from src.baseline import best_fit_decreasing
from src.fitness import reset_evaluation_count, get_evaluation_count, evaluate, evaluate_realized
from src.gwo import gwo
from src.hho import hho
from src.hybrid import hho_gwo
from src.models import Task, VM
from src.ga import ga
from src.sa import simulated_annealing
from src.aco import ant_colony
from src.de import differential_evolution
from src.woa import whale_optimization
from src.abc import artificial_bee_colony
from src.nsga2 import nsga2

LOAD_LEVELS = {"low": 0.35, "moderate": 0.65, "high": 0.95}
ALGORITHMS = ("FCFS", "Round Robin", "BFD", "GWO", "HHO", "HHO-GWO", "GA", "SA", "ACO", "DE", "WOA", "ABC", "NSGA-II")


def write_csv(path, rows):
    if not rows:
        raise ValueError(f"no rows to write: {path}")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def make_synthetic_tasks(task_count, load_name, seed, total_capacity, vm_capacity):
    """Create concurrent synthetic tasks with fixed offered load and noisy actual demand."""
    rng = random.Random(9_000_000 + seed * 1009 + task_count * 17 + list(LOAD_LEVELS).index(load_name))
    target_total = LOAD_LEVELS[load_name] * total_capacity
    weights = [rng.uniform(0.5, 1.5) for _ in range(task_count)]
    predicted = [target_total * w / sum(weights) for w in weights]
    tasks = []
    for i, pred in enumerate(predicted):
        # Actual demand varies around predicted demand; actual values are evaluation-only.
        actual = max(0.0, pred * rng.gauss(1.0, 0.08))
        overload_flag = int(pred >= 0.80 * vm_capacity)
        tasks.append(Task(
            task_id=i, horizon_id=0, predicted_cpu=pred,
            p_overload=float(overload_flag), predicted_overload=overload_flag,
            demand=pred, actual_cpu=actual, timestamp=float(i), actual_demand=actual,
        ))
    return tasks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=30, help="number of paired random seeds (default: 30)")
    parser.add_argument("--task-counts", default="20,50,100", help="comma-separated concurrent task counts")
    parser.add_argument("--load-levels", default="low,moderate,high", help="comma-separated load levels")
    parser.add_argument("--output", default="results/rigorous_v1", help="output directory relative to project root")
    parser.add_argument("--vm-count", type=int, default=4, help="number of VMs (default preserves the original 4-VM benchmark)")
    parser.add_argument("--vms-per-host", type=int, default=2, help="VMs per host (default 2)")
    parser.add_argument("--objective-profile", choices=("balanced", "energy", "sla", "makespan"), default="balanced", help="shared objective weights applied equally to all algorithms")
    parser.add_argument("--seed-start", type=int, default=1001, help="first seed ID (default 1001)")
    parser.add_argument("--evaluation-budget", type=int, default=300, help="objective evaluations per metaheuristic run (default 300)")
    parser.add_argument("--power-curve-exponent", type=float, default=2.0, help="host power curve exponent alpha in P=P_idle+(P_max-P_idle)*utilization**alpha; alpha >= 1 (default 2.0, convex)")
    parser.add_argument("--algorithms", default=",".join(ALGORITHMS), help="comma-separated subset of algorithms to run")
    parser.add_argument("--hybrid-hho-fraction", type=float, default=0.10, help="fraction of hybrid budget reserved for HHO")
    parser.add_argument("--hybrid-gwo-fraction", type=float, default=0.25, help="fraction of hybrid budget reserved for GWO; remainder goes to local refinement")
    args = parser.parse_args()
    if args.seeds < 1:
        parser.error("--seeds must be >= 1")
    if args.evaluation_budget < 10:
        parser.error("--evaluation-budget must be >= 10")
    if args.hybrid_hho_fraction <= 0 or args.hybrid_gwo_fraction <= 0 or args.hybrid_hho_fraction + args.hybrid_gwo_fraction >= 1:
        parser.error("hybrid HHO/GWO fractions must be positive and sum to less than 1; remainder is local search")
    if args.power_curve_exponent < 1.0:
        parser.error("--power-curve-exponent must be >= 1.0; values > 1 are convex")
    if args.vm_count < 2 or args.vms_per_host < 1 or args.vm_count % args.vms_per_host != 0:
        parser.error("vm-count must be >= 2 and divisible by vms-per-host")
    selected_algorithms = [x.strip() for x in args.algorithms.split(",") if x.strip()]
    unknown_algorithms = sorted(set(selected_algorithms) - set(ALGORITHMS))
    if not selected_algorithms or unknown_algorithms:
        parser.error(f"unknown or empty algorithm selection: {unknown_algorithms}")
    task_counts = [int(x) for x in args.task_counts.split(",")]
    load_levels = [x.strip() for x in args.load_levels.split(",")]
    if any(n < 1 for n in task_counts) or any(level not in LOAD_LEVELS for level in load_levels):
        parser.error("task counts must be positive; load levels must be low,moderate,high")

    cfg = yaml.safe_load((ROOT / "config/config.yaml").read_text(encoding="utf-8"))
    cfg["objective_mode"] = "three_term_host_energy_v1"
    profile_weights = {
        "balanced": {"energy": 1 / 3, "sla": 1 / 3, "makespan": 1 / 3},
        "energy": {"energy": 1.0, "sla": 0.0, "makespan": 0.0},
        "sla": {"energy": 0.0, "sla": 1.0, "makespan": 0.0},
        "makespan": {"energy": 0.0, "sla": 0.0, "makespan": 1.0},
    }
    cfg["weights"] = profile_weights[args.objective_profile]
    cfg["allowable_utilization"] = 0.80
    cfg["execution_sla"] = 1.50
    cfg["scheduling_interval"] = 1.0
    cfg["host_power_curve_exponent"] = args.power_curve_exponent
    # Synthetic VMs start empty. Host power is counted once per active host.
    # Preserve the exact original 4-VM/2-host configuration for reproducibility;
    # larger configurations use the same capacity per VM and explicit host assumptions.
    host_count = args.vm_count // args.vms_per_host
    if args.vm_count == 4 and args.vms_per_host == 2:
        hosts = [
            {"host_id": "host_1", "cpu_capacity": 200.0, "idle_power": 100.0, "max_power": 220.0},
            {"host_id": "host_2", "cpu_capacity": 200.0, "idle_power": 80.0, "max_power": 190.0},
        ]
    else:
        idle_values = [80.0, 90.0, 70.0, 85.0, 75.0, 88.0, 82.0, 92.0]
        max_values = [180.0, 200.0, 165.0, 190.0, 175.0, 195.0, 185.0, 205.0]
        hosts = []
        for i in range(host_count):
            hosts.append({
                "host_id": f"host_{i + 1}",
                "cpu_capacity": float(args.vms_per_host * 100.0),
                "idle_power": idle_values[i % len(idle_values)],
                "max_power": max_values[i % len(max_values)],
            })
    vm_specs = []
    for i in range(args.vm_count):
        host_id = f"host_{i // args.vms_per_host + 1}"
        vm_specs.append({
            "vm_id": f"vm_{i + 1}", "host_id": host_id,
            "cpu_capacity": 100.0, "current_cpu_load": 0.0,
            "idle_power": 0.0, "max_power": 0.0,
        })
    cfg["vms"] = vm_specs
    cfg["hosts"] = hosts
    cfg["normalization_references"] = {
        "energy": float(sum(h["max_power"] for h in hosts)), "sla": 1.0, "makespan": 10.0
    }
    cfg["evaluation_budget"] = args.evaluation_budget
    cfg["hybrid_budget"] = {"hho_fraction": args.hybrid_hho_fraction, "gwo_fraction": args.hybrid_gwo_fraction}
    total_capacity = float(args.vm_count * 100.0)
    vms = [VM(**v) for v in vm_specs]
    out = ROOT / args.output
    out.mkdir(parents=True, exist_ok=True)
    protocol = {
        "benchmark_type": "synthetic scheduling benchmark; not Bitbrains performance",
        "task_counts": task_counts, "load_levels": {k: LOAD_LEVELS[k] for k in load_levels},
        "vm_count": args.vm_count, "vms_per_host": args.vms_per_host,
        "objective_profile": args.objective_profile,
        "host_count": host_count, "vm_specs": vm_specs,
        "seeds": list(range(args.seed_start, args.seed_start + args.seeds)), "algorithms": selected_algorithms,
        "hybrid_budget_fractions": {"hho": args.hybrid_hho_fraction, "gwo": args.hybrid_gwo_fraction, "local_refinement": 1.0 - args.hybrid_hho_fraction - args.hybrid_gwo_fraction},
        "hybrid_selection_policy": (
            "balanced epsilon-constraint: among candidates no more than 8% worse than the best observed composite fitness, select the lowest makespan, then fitness; this policy is specific to HHO-GWO and must be disclosed as a comparator asymmetry"
            if args.objective_profile == "balanced" else
            "pure objective incumbent: return the best candidate under the declared single-objective profile; no makespan trade-off for SLA/energy"
            if args.objective_profile in ("sla", "energy") else
            "makespan-focused candidate selection; see implementation and report for the exact selection policy"
        ),
        "evaluation_budget": cfg["evaluation_budget"], "objective": f"{args.objective_profile} profile using shared weights for all algorithms",
        "host_power_curve_exponent": args.power_curve_exponent,
        "host_power_formula": "P(u)=0 for inactive hosts; otherwise P_idle+(P_max-P_idle)*u**alpha, where u is aggregate host utilization clipped to [0,1] and alpha is host_power_curve_exponent",
        "weights": cfg["weights"], "normalization_references": cfg["normalization_references"],
        "metric_units_and_interpretation": {"energy": "synthetic host-power proxy units per scheduling interval; not measured joules or watts", "sla": "fraction of tasks violating declared synthetic SLA rules", "makespan": "normalized aggregate completion metric used by this simulator"},
        "host_model": cfg["hosts"], "vm_initial_state": "all VMs and hosts start empty",
        "demand_model": "predicted demand drawn to target offered-load ratio; actual demand is predicted demand multiplied by N(1, 0.08), clipped at zero",
        "limitations": ["synthetic workload only", "power parameters are declared simulation assumptions", "not a CloudSim validation"],
    }
    (out / "protocol.json").write_text(json.dumps(protocol, indent=2) + "\n", encoding="utf-8")

    run_rows = []
    seeds = protocol["seeds"]
    def fcfs_schedule(tasks, seed):
        # FCFS list scheduling: preserve arrival/task order; assign each task to the VM
        # that becomes available first (lowest accumulated normalized completion time).
        assignment = [-1] * len(tasks)
        vm_finish = [0.0] * len(vms)
        for task_index, task in enumerate(tasks):
            vm_index = min(range(len(vms)), key=lambda i: (vm_finish[i], i))
            assignment[task_index] = vm_index
            vm_finish[vm_index] += max(0.0, task.demand) / vms[vm_index].cpu_capacity
        return assignment, evaluate(tasks, assignment, vms, cfg), []

    def round_robin_schedule(tasks, seed):
        # Deterministic cyclic assignment in the input/arrival order.
        assignment = [i % len(vms) for i in range(len(tasks))]
        return assignment, evaluate(tasks, assignment, vms, cfg), []

    methods = {
        "FCFS": fcfs_schedule,
        "Round Robin": round_robin_schedule,
        "BFD": lambda tasks, seed: (*best_fit_decreasing(tasks, vms, cfg), []),
        "GWO": lambda tasks, seed: gwo(tasks, vms, cfg, seed, max_evaluations=cfg["evaluation_budget"])[:3],
        "HHO": lambda tasks, seed: hho(tasks, vms, cfg, seed, max_evaluations=cfg["evaluation_budget"])[:3],
        "HHO-GWO": lambda tasks, seed: hho_gwo(tasks, vms, cfg, seed, max_evaluations=cfg["evaluation_budget"])[:3],
        "GA": lambda tasks, seed: ga(tasks, vms, cfg, seed, max_evaluations=cfg["evaluation_budget"])[:3],
        "SA": lambda tasks, seed: simulated_annealing(tasks, vms, cfg, seed, max_evaluations=cfg["evaluation_budget"])[:3],
        "ACO": lambda tasks, seed: ant_colony(tasks, vms, cfg, seed, max_evaluations=cfg["evaluation_budget"])[:3],
        "DE": lambda tasks, seed: differential_evolution(tasks, vms, cfg, seed, max_evaluations=cfg["evaluation_budget"])[:3],
        "WOA": lambda tasks, seed: whale_optimization(tasks, vms, cfg, seed, max_evaluations=cfg["evaluation_budget"])[:3],
        "ABC": lambda tasks, seed: artificial_bee_colony(tasks, vms, cfg, seed, max_evaluations=cfg["evaluation_budget"])[:3],
        "NSGA-II": lambda tasks, seed: nsga2(tasks, vms, cfg, seed, max_evaluations=cfg["evaluation_budget"])[:3],
    }
    scenario_index = 0
    total_scenarios = len(task_counts) * len(load_levels)
    for count in task_counts:
        for load_name in load_levels:
            scenario_index += 1
            print(f"scenario {scenario_index}/{total_scenarios}: tasks={count}, load={load_name}", flush=True)
            for seed in seeds:
                tasks = make_synthetic_tasks(count, load_name, seed, total_capacity, 100.0)
                for algorithm in selected_algorithms:
                    reset_evaluation_count(limit=cfg["evaluation_budget"])
                    started = time.perf_counter()
                    assignment, predicted_metrics, history = methods[algorithm](tasks, seed)
                    runtime = time.perf_counter() - started
                    evaluations = get_evaluation_count()
                    if len(assignment) != len(tasks) or any(not 0 <= i < len(vms) for i in assignment):
                        raise RuntimeError(f"invalid assignment: {algorithm}, tasks={count}, load={load_name}, seed={seed}")
                    if algorithm != "BFD" and evaluations > cfg["evaluation_budget"]:
                        raise RuntimeError(f"evaluation budget exceeded by {algorithm}: {evaluations}")
                    realized = evaluate_realized(tasks, assignment, vms, cfg)
                    row = {
                        "scenario": f"n{count}_{load_name}", "task_count": count, "load_level": load_name,
                        "offered_load_ratio": LOAD_LEVELS[load_name], "seed": seed, "algorithm": algorithm,
                        "predicted_fitness": predicted_metrics.fitness, "predicted_energy": predicted_metrics.energy,
                        "predicted_sla_rate": predicted_metrics.sla_violation_count / count,
                        "predicted_makespan": predicted_metrics.makespan,
                        "realized_fitness": realized.fitness, "realized_energy": realized.energy,
                        "realized_sla_rate": realized.sla_violation_count / count,
                        "realized_makespan": realized.makespan, "load_imbalance": realized.load_imbalance,
                        "overloaded_vm_count": realized.overload_count, "runtime_seconds": runtime,
                        "objective_evaluations": evaluations,
                    }
                    run_rows.append(row)
    write_csv(out / "runs.csv", run_rows)

    # Pairing unit is a seed: average each algorithm over the same declared scenarios.
    grouped = defaultdict(list)
    for row in run_rows:
        grouped[(row["algorithm"], row["seed"])].append(row)
    per_seed = []
    metrics = ("realized_fitness", "realized_energy", "realized_sla_rate", "realized_makespan", "runtime_seconds", "objective_evaluations")
    for (algorithm, seed), rows in sorted(grouped.items()):
        per_seed.append({"algorithm": algorithm, "seed": seed, "scenario_count": len(rows),
                         **{metric: statistics.fmean(float(r[metric]) for r in rows) for metric in metrics}})
    write_csv(out / "per_seed.csv", per_seed)
    summary = []
    for algorithm in selected_algorithms:
        rows = [r for r in per_seed if r["algorithm"] == algorithm]
        rec = {"algorithm": algorithm, "seed_count": len(rows)}
        for metric in metrics:
            vals = [float(r[metric]) for r in rows]
            rec[f"{metric}_mean"] = statistics.fmean(vals)
            rec[f"{metric}_sd"] = statistics.stdev(vals) if len(vals) > 1 else 0.0
        summary.append(rec)
    write_csv(out / "summary.csv", summary)
    print(f"completed {len(run_rows)} runs; output: {out.relative_to(ROOT)}", flush=True)


if __name__ == "__main__":
    main()
