"""Full configured comparison runner for BFD, GWO, HHO, HHO-GWO, PSO and GA."""
import csv
import statistics
import sys
import time
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.baseline import best_fit_decreasing
from src.data_adapter import horizons, load_and_validate
from src.demand_adapter import adapt, write_repair_log
from src.gwo import gwo
from src.hho import hho
from src.hybrid import hho_gwo
from src.pso import pso
from src.ga import ga
from src.models import VM
from src.fitness import reset_evaluation_count, get_evaluation_count


def write_csv(path, rows, fields):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def task_rows(tasks, assignment, vms, cfg, algorithm, horizon_id, trial, seed):
    predicted_loads = [vm.current_cpu_load for vm in vms]
    actual_loads = [vm.current_cpu_load for vm in vms]
    output = []
    for task, index in zip(tasks, assignment):
        vm = vms[index]
        predicted_loads[index] += task.demand
        predicted_util = predicted_loads[index] / vm.cpu_capacity
        predicted_execution = task.demand / vm.cpu_capacity
        predicted_violation = predicted_util > cfg["allowable_utilization"] or predicted_execution > cfg["execution_sla"]

        # Post-hoc diagnostic only: actual CPU is not passed to the optimizer or fitness.
        actual_demand = max(0.0, task.actual_cpu) / 100.0 * vms[0].cpu_capacity
        actual_loads[index] += actual_demand
        actual_util = actual_loads[index] / vm.cpu_capacity
        actual_execution = actual_demand / vm.cpu_capacity
        actual_violation = actual_util > cfg["allowable_utilization"] or actual_execution > cfg["execution_sla"]
        output.append({
            "task_id": task.task_id, "horizon_id": horizon_id, "timestamp_source_value": task.timestamp,
            "actual_cpu_evaluation_only": task.actual_cpu, "predicted_cpu": task.predicted_cpu,
            "p_overload_risk_score": task.p_overload, "predicted_overload": task.predicted_overload,
            "actual_overload_label": int(task.actual_cpu >= cfg["overload_threshold"]),
            "selected_vm_id": vm.vm_id, "host_id": vm.host_id,
            "predicted_resulting_utilization_proxy": predicted_util,
            "predicted_sla_violation_proxy": int(predicted_violation),
            "actual_resulting_utilization_posthoc_proxy": actual_util,
            "actual_sla_violation_posthoc_proxy": int(actual_violation),
            "algorithm": algorithm, "trial": trial, "seed": seed,
        })
    return output


def main():
    cfg = yaml.safe_load((ROOT / "config/config.yaml").read_text(encoding="utf-8"))
    seeds = cfg["seeds"][:cfg["trials"]]
    if len(seeds) != cfg["trials"]:
        raise ValueError("configuration has fewer seeds than trials")
    source = ROOT / cfg.get("input_file", "data/person2_scheduler_input.csv")
    rows, report = load_and_validate(source, expected_rows=cfg.get("expected_rows"),
                                     overload_threshold=cfg.get("overload_threshold", 80.0))
    if not report["valid"]:
        raise ValueError("Handoff validation failed: " + "; ".join(report["errors"]))
    (ROOT / "results").mkdir(exist_ok=True)
    (ROOT / "results" / "input_validation.txt").write_text(
        "Input validation report\n" + "\n".join(f"{k}: {v}" for k, v in report.items()) + "\n",
        encoding="utf-8")

    vms = [VM(**item) for item in cfg["vms"]]
    out = ROOT / "results"
    repairs, horizon_results, schedules = [], [], []
    convergence = {"GWO": [], "HHO": [], "HHO-GWO": [], "PSO": [], "GA": []}
    methods = {
        "BFD": lambda tasks, seed: (*best_fit_decreasing(tasks, vms, cfg), []),
        "GWO": lambda tasks, seed: gwo(tasks, vms, cfg, seed, max_evaluations=cfg.get("evaluation_budget"))[:3],
        "HHO": lambda tasks, seed: hho(tasks, vms, cfg, seed, max_evaluations=cfg.get("evaluation_budget"))[:3],
        "HHO-GWO": lambda tasks, seed: hho_gwo(tasks, vms, cfg, seed, max_evaluations=cfg.get("evaluation_budget"))[:3],
        "PSO": lambda tasks, seed: pso(tasks, vms, cfg, seed, max_evaluations=cfg.get("evaluation_budget"))[:3],
        "GA": lambda tasks, seed: ga(tasks, vms, cfg, seed, max_evaluations=cfg.get("evaluation_budget"))[:3],
    }
    all_horizons = horizons(rows, cfg["horizon_length"])
    for hid, batch in enumerate(all_horizons):
        if hid % 10 == 0:
            print(f"processing horizon {hid + 1}/{len(all_horizons)}", flush=True)
        before = len(repairs)
        tasks = adapt(batch, hid, vms[0].cpu_capacity, repairs)
        for algorithm, run in methods.items():
            for trial, seed in enumerate(seeds):
                reset_evaluation_count(limit=cfg.get("evaluation_budget"))
                started = time.perf_counter()
                assignment, metric, history = run(tasks, seed)
                runtime = time.perf_counter() - started
                evaluations = get_evaluation_count()
                if len(assignment) != len(tasks) or any(not 0 <= i < len(vms) for i in assignment):
                    raise RuntimeError(f"Invalid {algorithm} schedule in horizon {hid}, seed {seed}")
                horizon_results.append({
                    "horizon_id": hid, "algorithm": algorithm, "trial": trial, "seed": seed,
                    **metric.__dict__, "sla_violation_rate": metric.sla_violation_count / len(tasks) if tasks else 0.0,
                    "overload_rate": metric.overload_count / len(vms), "runtime": runtime,
                    "evaluations": evaluations, "prediction_repair_count": len(repairs) - before,
                })
                schedules.extend(task_rows(tasks, assignment, vms, cfg, algorithm, hid, trial, seed))
                if algorithm in convergence:
                    convergence[algorithm].extend({"horizon_id": hid, "trial": trial, "seed": seed,
                                                   "iteration": i + 1, "fitness": value}
                                                  for i, value in enumerate(history))

    if not horizon_results:
        raise RuntimeError("No horizons were produced from the input data")
    write_csv(out / "horizon_results.csv", horizon_results, list(horizon_results[0]))
    write_csv(out / "schedule_results.csv", schedules, list(schedules[0]))
    write_repair_log(out / "repair_log.csv", repairs)
    for algorithm, records in convergence.items():
        write_csv(out / f"convergence_{algorithm.lower().replace('-', '_')}.csv", records,
                  ["horizon_id", "trial", "seed", "iteration", "fitness"])

    fields = ("fitness", "energy", "makespan", "sla_violation_count", "load_imbalance",
              "average_utilization", "overload_count", "runtime", "evaluations")
    trials = []
    for algorithm in methods:
        for trial, seed in enumerate(seeds):
            group = [x for x in horizon_results if x["algorithm"] == algorithm and x["seed"] == seed]
            trials.append({"algorithm": algorithm, "trial": trial, "seed": seed,
                           **{name: statistics.fmean(x[name] for x in group) for name in fields}})
    comparison = []
    for algorithm in methods:
        group = [x for x in trials if x["algorithm"] == algorithm]
        record = {"algorithm": algorithm, "seed_count": len(group)}
        for name in fields:
            record[f"{name}_fmean"] = statistics.fmean(x[name] for x in group)
            record[f"{name}_stdev"] = statistics.stdev(x[name] for x in group) if len(group) > 1 else 0.0
        comparison.append(record)
    write_csv(out / "trial_results.csv", trials, list(trials[0]))
    write_csv(out / "algorithm_comparison.csv", comparison, list(comparison[0]))
    print(f"completed {len(horizon_results)} schedules across {len(methods)} algorithms using {len(seeds)} seeds")
    print(f"input rows: {len(rows)}; horizons: {len(horizons(rows, cfg['horizon_length']))}; schema: {report['schema']}")
    print(f"risk input: {report['risk_score_source']}")
    print(f"objective-evaluation cap per horizon/run: {cfg.get('evaluation_budget', 'unlimited')}")


if __name__ == "__main__":
    main()
