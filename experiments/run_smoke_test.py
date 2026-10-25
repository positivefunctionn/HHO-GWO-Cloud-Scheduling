"""Quick validation run on the supplied Person 1 CSV; not the final experiment."""
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

SMOKE_SEEDS = (11, 23)
SMOKE_POPULATION = 4
SMOKE_ITERATIONS = 3


def write_csv(path, rows, fields):
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main():
    cfg = yaml.safe_load((ROOT / "config/config.yaml").read_text(encoding="utf-8"))
    cfg["trials"] = len(SMOKE_SEEDS)
    cfg["seeds"] = list(SMOKE_SEEDS)
    for key in ("hho", "gwo", "pso", "ga"):
        cfg[key] = {**cfg[key], "population_size": SMOKE_POPULATION, "iterations": SMOKE_ITERATIONS}
    source = ROOT / cfg.get("input_file", "data/person2_scheduler_input.csv")
    rows, report = load_and_validate(source, expected_rows=None,
                                     overload_threshold=cfg.get("overload_threshold", 80.0))
    if not report["valid"]:
        raise ValueError("Handoff validation failed: " + "; ".join(report["errors"]))
    vms = [VM(**item) for item in cfg["vms"]]
    output = ROOT / "results" / "smoke_test"
    output.mkdir(parents=True, exist_ok=True)
    (output / "input_validation.txt").write_text(
        "Input validation report\n" + "\n".join(f"{k}: {v}" for k, v in report.items()) + "\n", encoding="utf-8")
    repairs, horizon_results, schedule_results = [], [], []
    convergence = {"GWO": [], "HHO": [], "HHO-GWO": [], "PSO": [], "GA": []}
    methods = {
        "BFD": lambda tasks, seed: (*best_fit_decreasing(tasks, vms, cfg), []),
        "GWO": lambda tasks, seed: gwo(tasks, vms, cfg, seed)[:3],
        "HHO": lambda tasks, seed: hho(tasks, vms, cfg, seed)[:3],
        "HHO-GWO": lambda tasks, seed: hho_gwo(tasks, vms, cfg, seed)[:3],
        "PSO": lambda tasks, seed: pso(tasks, vms, cfg, seed)[:3],
        "GA": lambda tasks, seed: ga(tasks, vms, cfg, seed)[:3],
    }
    for hid, batch in enumerate(horizons(rows, cfg["horizon_length"])):
        before = len(repairs)
        tasks = adapt(batch, hid, vms[0].cpu_capacity, repairs)
        repair_count = len(repairs) - before
        for algorithm, run in methods.items():
            for trial, seed in enumerate(SMOKE_SEEDS):
                reset_evaluation_count()
                started = time.perf_counter()
                assignment, metrics, history = run(tasks, seed)
                elapsed = time.perf_counter() - started
                evaluations = get_evaluation_count()
                if len(assignment) != len(tasks) or any(not 0 <= i < len(vms) for i in assignment):
                    raise RuntimeError(f"Invalid {algorithm} schedule in horizon {hid}, seed {seed}")
                horizon_results.append({"horizon_id": hid, "algorithm": algorithm, "trial": trial, "seed": seed,
                                       **metrics.__dict__, "sla_violation_rate": metrics.sla_violation_count / len(tasks) if tasks else 0,
                                       "overload_rate": metrics.overload_count / len(vms), "runtime": elapsed,
                                       "evaluations": evaluations, "prediction_repair_count": repair_count})
                # The prediction is the scheduler input. Actual CPU is only written as a post-hoc audit field.
                loads = [vm.current_cpu_load for vm in vms]
                for task, vm_index in zip(tasks, assignment):
                    vm = vms[vm_index]
                    loads[vm_index] += task.demand
                    schedule_result = loads[vm_index] / vm.cpu_capacity
                    schedule_results.append({"task_id": task.task_id, "horizon_id": hid,
                                             "timestamp_source_value": task.timestamp,
                                             "actual_cpu_evaluation_only": task.actual_cpu,
                                             "predicted_cpu": task.predicted_cpu,
                                             "p_overload_risk_score": task.p_overload,
                                             "predicted_overload": task.predicted_overload,
                                             "actual_overload_label": int(task.actual_cpu >= cfg["overload_threshold"]),
                                             "selected_vm_id": vm.vm_id, "host_id": vm.host_id,
                                             "predicted_resulting_utilization_proxy": schedule_result,
                                             "algorithm": algorithm, "trial": trial, "seed": seed})
                if algorithm in convergence:
                    convergence[algorithm].extend({"horizon_id": hid, "trial": trial, "seed": seed,
                                                   "iteration": i + 1, "fitness": value}
                                                  for i, value in enumerate(history))
    write_csv(output / "horizon_results.csv", horizon_results, list(horizon_results[0]))
    write_csv(output / "schedule_results.csv", schedule_results, list(schedule_results[0]))
    write_repair_log(output / "repair_log.csv", repairs)
    for algorithm, records in convergence.items():
        write_csv(output / f"convergence_{algorithm.lower().replace('-', '_')}.csv", records,
                  ["horizon_id", "trial", "seed", "iteration", "fitness"])
    fields = ("fitness", "energy", "makespan", "sla_violation_count", "load_imbalance", "average_utilization", "overload_count", "runtime", "evaluations")
    trials = []
    for algorithm in methods:
        for trial, seed in enumerate(SMOKE_SEEDS):
            group = [row for row in horizon_results if row["algorithm"] == algorithm and row["seed"] == seed]
            trials.append({"algorithm": algorithm, "trial": trial, "seed": seed,
                           **{name: statistics.fmean(row[name] for row in group) for name in fields}})
    comparison = []
    for algorithm in methods:
        group = [row for row in trials if row["algorithm"] == algorithm]
        record = {"algorithm": algorithm, "seed_count": len(group)}
        for name in fields:
            record[f"{name}_fmean"] = statistics.fmean(row[name] for row in group)
            record[f"{name}_stdev"] = statistics.stdev(row[name] for row in group) if len(group) > 1 else 0.0
        comparison.append(record)
    write_csv(output / "trial_results.csv", trials, list(trials[0]))
    write_csv(output / "algorithm_comparison.csv", comparison, list(comparison[0]))
    print(f"smoke test completed: {len(horizon_results)} schedules across {len(methods)} algorithms; output={output}")
    print(f"validated {len(rows)} rows; schema={report['schema']}; risk input={report['risk_score_source']}")


if __name__ == "__main__":
    main()
