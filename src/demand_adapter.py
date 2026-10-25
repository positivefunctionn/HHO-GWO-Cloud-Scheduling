"""Convert predicted CPU values into synthetic workload demand.

Original prediction values are retained on Task. Only the derived demand is
floored at zero when a negative prediction cannot represent nonnegative load.
"""
import csv
from .models import Task


def adapt(horizon_rows, horizon_id, reference_cpu_capacity, repair_log):
    tasks = []
    for offset, row in enumerate(horizon_rows):
        raw = float(row["predicted_cpu"])
        repaired = max(0.0, raw)
        task_id = (horizon_id * 100000) + offset
        if raw < 0:
            repair_log.append({"task_id": task_id, "horizon_id": horizon_id,
                               "original_predicted_cpu": raw, "repaired_predicted_cpu": repaired,
                               "reason": "negative prediction retained in source; derived demand floored to zero"})
        tasks.append(Task(task_id, horizon_id, raw, float(row["p_overload"]),
                          int(float(row["predicted_overload"])),
                          repaired / 100.0 * reference_cpu_capacity,
                          actual_cpu=float(row.get("actual_cpu", 0.0)),
                          timestamp=float(row.get("timestamp", 0.0))))
    return tasks


def write_repair_log(path, entries):
    fields = ["task_id", "horizon_id", "original_predicted_cpu", "repaired_predicted_cpu", "reason"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(entries)
