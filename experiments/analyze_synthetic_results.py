"""Validate and analyze a synthetic scheduler benchmark output directory.

The independent unit for paired inference is the seed-level mean across scenarios.
This script checks the algorithm x seed x scenario panel, rejects duplicate/missing
cells, writes summary tables, and applies Holm correction within each metric's
predeclared family of reference-vs-baseline comparisons.

Example:
  python experiments/analyze_synthetic_results.py results/final_convex_balanced --reference HHO-GWO
  python experiments/analyze_synthetic_results.py results/final_convex_sla --reference HHO-GWO --metrics realized_sla_rate --alternative less
"""
from __future__ import annotations
import argparse
import csv
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path

try:
    from scipy.stats import wilcoxon
except ImportError as exc:
    raise SystemExit("SciPy is required for paired inference. Install requirements with: python -m pip install -r requirements.txt") from exc

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_METRICS = "realized_fitness,realized_energy,realized_sla_rate,realized_makespan,load_imbalance"

def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def write_csv(path: Path, rows):
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

def holm_adjust(p_values):
    order = sorted(range(len(p_values)), key=lambda i: p_values[i])
    adjusted = [1.0] * len(p_values)
    running = 0.0
    m = len(p_values)
    for rank, idx in enumerate(order):
        running = max(running, min(1.0, (m - rank) * p_values[idx]))
        adjusted[idx] = running
    return adjusted

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result_dir", help="directory containing runs.csv and protocol.json")
    parser.add_argument("--reference", default="HHO-GWO", help="algorithm compared against every other algorithm")
    parser.add_argument("--metrics", default=DEFAULT_METRICS, help="comma-separated metric columns in runs.csv")
    parser.add_argument("--alternative", choices=("two-sided", "less"), default="two-sided",
                        help="Wilcoxon alternative; 'less' tests reference < baseline and must be predeclared")
    args = parser.parse_args()
    result_dir = Path(args.result_dir)
    if not result_dir.is_absolute():
        result_dir = result_dir if result_dir.exists() else ROOT / result_dir
    run_path, protocol_path = result_dir / "runs.csv", result_dir / "protocol.json"
    if not run_path.is_file() or not protocol_path.is_file():
        raise SystemExit(f"Expected both {run_path} and {protocol_path}")
    rows = read_csv(run_path)
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    if not rows:
        raise SystemExit("runs.csv is empty")
    algorithms = list(dict.fromkeys(r["algorithm"] for r in rows))
    declared = protocol.get("algorithms", [])
    if declared and set(algorithms) != set(declared):
        raise SystemExit(f"Algorithm mismatch: observed={algorithms}, protocol={declared}")
    if args.reference not in algorithms:
        raise SystemExit(f"Reference algorithm {args.reference!r} not found. Available: {algorithms}")
    metrics = [m.strip() for m in args.metrics.split(",") if m.strip()]
    missing_cols = [m for m in metrics if m not in rows[0]]
    if missing_cols:
        raise SystemExit(f"Missing requested metric columns: {missing_cols}")

    # Reject duplicate algorithm/scenario/seed observations and incomplete panels.
    keys = [(r["algorithm"], r["scenario"], int(r["seed"])) for r in rows]
    if len(keys) != len(set(keys)):
        raise SystemExit("Duplicate algorithm/scenario/seed rows found; fix the run data before inference")
    seeds = sorted({int(r["seed"]) for r in rows})
    scenarios = sorted({r["scenario"] for r in rows})
    expected = {(a, s, seed) for a in algorithms for s in scenarios for seed in seeds}
    missing = expected - set(keys)
    if missing:
        raise SystemExit(f"Incomplete paired panel: {len(missing)} algorithm/scenario/seed cells are missing")

    # Inferential units: per-algorithm means across the same scenario set for each seed.
    bucket = defaultdict(list)
    for r in rows:
        bucket[(r["algorithm"], int(r["seed"]))].append(r)
    per_seed = []
    for alg in algorithms:
        for seed in seeds:
            rr = bucket[(alg, seed)]
            if len(rr) != len(scenarios):
                raise SystemExit(f"Incomplete scenario set for {alg}, seed {seed}: {len(rr)} of {len(scenarios)}")
            record = {"algorithm": alg, "seed": seed, "scenario_count": len(rr)}
            for metric in metrics:
                values = [float(r[metric]) for r in rr]
                if not all(math.isfinite(x) for x in values):
                    raise SystemExit(f"Non-finite values in {metric} for {alg}, seed {seed}")
                record[metric] = statistics.fmean(values)
            per_seed.append(record)
    write_csv(result_dir / "audited_per_seed.csv", per_seed)

    # Summary across seed x scenario observations; rank lower-is-better.
    summary = []
    for alg in algorithms:
        rr = [r for r in rows if r["algorithm"] == alg]
        record = {"algorithm": alg, "runs": len(rr), "seed_count": len(seeds), "scenario_count": len(scenarios)}
        for metric in metrics:
            vals = [float(r[metric]) for r in rr]
            record[metric + "_mean"] = statistics.fmean(vals)
            record[metric + "_sd"] = statistics.stdev(vals) if len(vals) > 1 else 0.0
            record[metric + "_rank_lower_is_better"] = 1 + sum(
                statistics.fmean(float(r[metric]) for r in rows if r["algorithm"] == other) < statistics.fmean(vals)
                for other in algorithms if other != alg)
        summary.append(record)
    write_csv(result_dir / "audited_metric_summary.csv", summary)

    comparisons = []
    for metric in metrics:
        ref_map = {int(r["seed"]): float(r[metric]) for r in per_seed if r["algorithm"] == args.reference}
        metric_comparisons = []
        for baseline in algorithms:
            if baseline == args.reference:
                continue
            base_map = {int(r["seed"]): float(r[metric]) for r in per_seed if r["algorithm"] == baseline}
            paired = sorted(set(ref_map) & set(base_map))
            ref_values = [ref_map[s] for s in paired]
            base_values = [base_map[s] for s in paired]
            diffs = [x - y for x, y in zip(ref_values, base_values)]
            if all(abs(d) <= 1e-15 for d in diffs):
                stat, p = 0.0, 1.0
            else:
                try:
                    result = wilcoxon(ref_values, base_values, alternative=args.alternative,
                                      zero_method="wilcox", method="auto")
                    stat, p = float(result.statistic), float(result.pvalue)
                    if not math.isfinite(p):
                        stat, p = 0.0, 1.0
                except ValueError:
                    stat, p = 0.0, 1.0
            rec = {
                "metric": metric, "comparison": f"{args.reference} vs {baseline}",
                "n_paired_seeds": len(paired),
                "reference_mean_seed_average": statistics.fmean(ref_values),
                "baseline_mean_seed_average": statistics.fmean(base_values),
                "mean_paired_difference_reference_minus_baseline": statistics.fmean(diffs),
                "median_paired_difference": statistics.median(diffs),
                "reference_wins_lower_is_better": sum(d < 0 for d in diffs),
                "ties": sum(abs(d) <= 1e-15 for d in diffs),
                "reference_losses_lower_is_better": sum(d > 0 for d in diffs),
                "wilcoxon_alternative": args.alternative,
                "wilcoxon_p_value": p,
            }
            metric_comparisons.append(rec)
        adjusted = holm_adjust([r["wilcoxon_p_value"] for r in metric_comparisons])
        for rec, padj in zip(metric_comparisons, adjusted):
            rec["holm_adjusted_p_within_metric_family"] = padj
            rec["significant_at_0_05_after_holm"] = str(padj < 0.05).lower()
        comparisons.extend(metric_comparisons)
    write_csv(result_dir / "audited_paired_tests.csv", comparisons)

    print(f"Validated {len(rows)} rows: {len(algorithms)} algorithms x {len(seeds)} seeds x {len(scenarios)} scenarios")
    print(f"Reference={args.reference}; alternative={args.alternative}; Holm correction is within each metric's baseline family")
    print(f"Wrote {result_dir / 'audited_per_seed.csv'}")
    print(f"Wrote {result_dir / 'audited_metric_summary.csv'}")
    print(f"Wrote {result_dir / 'audited_paired_tests.csv'}")

if __name__ == "__main__":
    main()
