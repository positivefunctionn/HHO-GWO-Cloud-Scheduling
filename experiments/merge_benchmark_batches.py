"""Merge seed-disjoint benchmark batch directories after validating their protocols.

Example:
  py experiments/merge_benchmark_batches.py results/reproduction_balanced_9601 results/reproduction_balanced_9701 --output results/reproduction_balanced_merged
"""
from __future__ import annotations
import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPARE_KEYS = (
    "benchmark_type", "task_counts", "load_levels", "vm_count", "vms_per_host",
    "objective_profile", "host_count", "algorithms", "evaluation_budget",
    "hybrid_budget_fractions", "objective", "weights", "normalization_references",
    "host_model", "vm_specs", "vm_initial_state", "demand_model",
    "hybrid_selection_policy", "metric_units_and_interpretation", "host_power_curve_exponent", "host_power_formula",
)

def resolve(p: str) -> Path:
    path = Path(p)
    return path if path.is_absolute() else (path if path.exists() else ROOT / path)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("batch_a")
    parser.add_argument("batch_b")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    dirs = [resolve(args.batch_a), resolve(args.batch_b)]
    out = resolve(args.output)
    protocols = []
    rows_by_batch = []
    for d in dirs:
        p = d / "protocol.json"
        r = d / "runs.csv"
        if not p.is_file() or not r.is_file():
            raise SystemExit(f"Expected protocol.json and runs.csv in {d}")
        protocols.append(json.loads(p.read_text(encoding="utf-8")))
        with r.open(newline="", encoding="utf-8-sig") as f:
            rows_by_batch.append(list(csv.DictReader(f)))
    for key in COMPARE_KEYS:
        if protocols[0].get(key) != protocols[1].get(key):
            raise SystemExit(f"Batch protocol mismatch for {key!r}; refusing to merge")
    seed_a, seed_b = set(map(int, protocols[0].get("seeds", []))), set(map(int, protocols[1].get("seeds", [])))
    if not seed_a or not seed_b:
        raise SystemExit("Both protocols must declare non-empty seed lists")
    overlap = seed_a & seed_b
    if overlap:
        raise SystemExit(f"Seed overlap detected; refusing duplicate paired observations: {sorted(overlap)}")
    rows = rows_by_batch[0] + rows_by_batch[1]
    keys = [(r["algorithm"], r["scenario"], int(r["seed"])) for r in rows]
    if len(keys) != len(set(keys)):
        raise SystemExit("Duplicate algorithm/scenario/seed key detected; refusing to merge")
    expected = len(protocols[0]["algorithms"]) * len(seed_a | seed_b) * len(protocols[0]["task_counts"]) * len(protocols[0]["load_levels"])
    if len(rows) != expected:
        raise SystemExit(f"Incomplete merged panel: expected {expected} rows from protocol, found {len(rows)}")
    out.mkdir(parents=True, exist_ok=False)
    with (out / "runs.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader(); writer.writerows(rows)
    protocol = dict(protocols[0])
    protocol["seeds"] = sorted(seed_a | seed_b)
    protocol["seed_count"] = len(protocol["seeds"])
    protocol["algorithm_runs"] = len(rows)
    protocol["runs_per_algorithm"] = len(rows) // len(protocol["algorithms"])
    protocol["merged_from_batches"] = [str(d) for d in dirs]
    (out / "protocol.json").write_text(json.dumps(protocol, indent=2) + "\n", encoding="utf-8")
    print(f"Merged {len(rows)} rows: {len(protocol['algorithms'])} algorithms x {len(protocol['seeds'])} seeds x {len(protocols[0]['task_counts']) * len(protocols[0]['load_levels'])} scenarios")
    print(f"Output: {out}")

if __name__ == "__main__":
    main()
