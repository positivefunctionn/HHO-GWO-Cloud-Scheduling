"""Per-scenario summaries and two-sided paired tests for the expanded synthetic benchmark."""
import csv
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from scipy.stats import wilcoxon

ROOT = Path(__file__).resolve().parents[1]
RESULT_DIR = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "results/final_convex_balanced"


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows):
    if not rows:
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
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
    rows = read_csv(RESULT_DIR / "runs.csv")
    protocol_path = RESULT_DIR / "protocol.json"
    protocol = json.loads(protocol_path.read_text(encoding="utf-8")) if protocol_path.exists() else {}
    profile = protocol.get("objective_profile", "balanced")
    weights = protocol.get("weights", {"energy": 1 / 3, "sla": 1 / 3, "makespan": 1 / 3})
    budget_fractions = protocol.get("hybrid_budget_fractions", {"hho": 0.20, "gwo": 0.20, "local_refinement": 0.60})
    metrics = ("realized_fitness", "realized_energy", "realized_sla_rate", "realized_makespan", "runtime_seconds", "objective_evaluations")
    algs = tuple(protocol.get("algorithms", ("BFD", "GWO", "HHO", "HHO-GWO", "PSO", "GA")))
    scenarios = sorted({r["scenario"] for r in rows}, key=lambda x: (int(x.split("_")[0][1:]), x.split("_")[1]))
    grouped = defaultdict(list)
    for r in rows:
        grouped[(r["scenario"], r["algorithm"])].append(r)
    summary = []
    for scenario in scenarios:
        for metric in metrics:
            vals = {a: [float(r[metric]) for r in grouped[(scenario, a)]] for a in algs}
            best = min(algs, key=lambda a: statistics.fmean(vals[a]))
            # One summary row per metric and scenario, ranking methods by mean.
            ordered = sorted(algs, key=lambda a: statistics.fmean(vals[a]))
            rec = {"scenario": scenario, "metric": metric, "best_algorithm": best, "best_mean": statistics.fmean(vals[best])}
            for rank, alg in enumerate(ordered, 1):
                rec[f"rank_{rank}"] = alg
                rec[f"mean_{alg}"] = statistics.fmean(vals[alg])
                rec[f"sd_{alg}"] = statistics.stdev(vals[alg]) if len(vals[alg]) > 1 else 0.0
            summary.append(rec)
    write_csv(RESULT_DIR / "per_scenario_summary.csv", summary)

    # Paired two-sided Wilcoxon tests: hybrid against every comparator in every scenario.
    comparisons = []
    for scenario in scenarios:
        hybrid_rows = {int(r["seed"]): float(r["realized_fitness"]) for r in grouped[(scenario, "HHO-GWO")]}
        for baseline in (a for a in algs if a != "HHO-GWO"):
            base_rows = {int(r["seed"]): float(r["realized_fitness"]) for r in grouped[(scenario, baseline)]}
            seeds = sorted(set(hybrid_rows) & set(base_rows))
            h = [hybrid_rows[s] for s in seeds]
            b = [base_rows[s] for s in seeds]
            diffs = [x - y for x, y in zip(h, b)]
            try:
                if all(abs(x - y) <= 1e-12 for x, y in zip(h, b)):
                    stat, p = 0.0, 1.0
                else:
                    test = wilcoxon(h, b, alternative="two-sided", zero_method="wilcox", method="auto")
                    stat, p = float(test.statistic), float(test.pvalue)
                    if not (p == p):  # guard against a NaN from an all-zero/degenerate sample
                        stat, p = 0.0, 1.0
            except ValueError:
                stat, p = 0.0, 1.0
            hm, bm = statistics.fmean(h), statistics.fmean(b)
            comparisons.append({
                "scenario": scenario, "comparison": f"HHO-GWO_vs_{baseline}", "paired_seed_count": len(seeds),
                "hybrid_mean_fitness": hm, "baseline_mean_fitness": bm,
                "mean_difference_hybrid_minus_baseline": hm - bm,
                "median_paired_difference_hybrid_minus_baseline": statistics.median(diffs),
                "hybrid_better_seed_count": sum(d < 0 for d in diffs),
                "baseline_better_seed_count": sum(d > 0 for d in diffs),
                "ties_seed_count": sum(d == 0 for d in diffs),
                "wilcoxon_statistic": stat, "p_value_two_sided": p,
            })
    adjusted = holm_adjust([r["p_value_two_sided"] for r in comparisons])
    for row, p_adj in zip(comparisons, adjusted):
        row["p_value_holm_adjusted_across_all_scenario_comparisons"] = p_adj
        row["significant_at_0_05_after_holm"] = str(p_adj < 0.05).lower()
    write_csv(RESULT_DIR / "hybrid_two_sided_comparisons.csv", comparisons)

    # Compact, cautious report.
    fitness_rows = [r for r in summary if r["metric"] == "realized_fitness"]
    lines = [
        f"# Expanded 12-VM / 6-host synthetic benchmark results ({profile} objective profile)",
        "",
        "## Protocol",
        "- 12 VMs across 6 hosts (2 VMs per host), 20/50/100 tasks, low/moderate/high offered load.",
        f"- {len(protocol.get('seeds', []))} paired seeds per scenario; {len(algs)} algorithms; {len(rows)} algorithm-scenario-seed runs.",
        "- Metaheuristics use the same maximum of 300 objective evaluations; BFD is deterministic and uses one evaluation.",
        f"- Objective profile: {profile}; shared weights applied equally to every algorithm: {weights}.",
        f"- HHO-GWO budget split (fractions): {budget_fractions}.",
        "- Actual demand remains synthetic noise around predicted demand; these results do not validate BiLSTM forecasts or real-cloud energy savings.",
        "- Host power and capacity values are explicit simulation assumptions, not measurements from physical hosts.",
        "",
        "## Per-scenario fitness ranking",
        "| Scenario | Winner by mean fitness | HHO-GWO rank | Mean HHO-GWO fitness |",
        "|---|---|---:|---:|",
    ]
    for r in fitness_rows:
        ordered = [r[f"rank_{i}"] for i in range(1, len(algs) + 1)]
        lines.append(f"| {r['scenario']} | {r['best_algorithm']} | {ordered.index('HHO-GWO') + 1} / {len(algs)} | {float(r['mean_HHO-GWO']):.4f} |")
    lines += [
        "",
        "## Interpretation",
        f"The best method is identified separately for each scenario using mean realized fitness; lower is better for the configured objective profile. See `per_scenario_summary.csv` for all metrics and `hybrid_two_sided_comparisons.csv` for paired two-sided Wilcoxon tests with Holm correction across all {len(comparisons)} scenario-level comparisons.",
        "",
        "This is an expanded synthetic experiment, not proof of performance on real cloud traces. Do not claim that HHO-GWO is uniformly best unless the results support that claim across the declared scenarios and metrics.",
        "",
    ]
    (RESULT_DIR / "EXPANDED_RESULTS_REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {RESULT_DIR / 'per_scenario_summary.csv'}")
    print(f"Wrote {RESULT_DIR / 'hybrid_two_sided_comparisons.csv'}")
    print(f"Wrote {RESULT_DIR / 'EXPANDED_RESULTS_REPORT.md'}")


if __name__ == "__main__":
    main()
