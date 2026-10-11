"""Statistical analysis and publication figure generation for Version 3 (Corrected 5Q Proc A vs 7Q Heavy-Hex Proc B).

Recomputes directly from raw measurement counts in results/verified_ab_v3/:
1. Best sampled cut, sample mean cut, standard error (SE), 95% CI.
2. Finite-shot approximation ratio vs analytic expectation value.
3. Ground-state success probability P(opt) and Wilson score 95% CI.
4. Pairwise statistical hypothesis tests:
   - Comparison 1: Processor A Ideal vs Noisy (Welch t-test & two-proportion z-test)
   - Comparison 2: Processor B Ideal vs Noisy (Welch t-test & two-proportion z-test)
   - Comparison 3a: Processor A vs Processor B Controlled Ideal (Welch t-test & two-proportion z-test)
   - Comparison 3b: Processor A vs Processor B Controlled Noisy (Welch t-test & two-proportion z-test)
5. Resource overhead vs solution quality trade-off analysis.
6. Export CSV, Markdown, and JSON tables under results/verified_ab_v3/tables/ and data/.
7. Generate high-resolution publication figures under results/verified_ab_v3/figures/.
"""

import json
from pathlib import Path
import sys

# Ensure src/ and repo root are on sys.path
ROOT_PATH = Path(__file__).resolve().parent.parent
SRC_PATH = ROOT_PATH / "src"
for p in [str(ROOT_PATH), str(SRC_PATH)]:
    if p not in sys.path:
        sys.path.insert(0, p)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from maxcut.domain.model import MaxCutGraph
from maxcut.io import load_challenge_instance


def wilson_score_interval(k: int, n: int, confidence: float = 0.95) -> Tuple[float, float]:
    """Calculates the Wilson score confidence interval for a binomial proportion."""
    if n == 0:
        return (0.0, 0.0)
    z = stats.norm.ppf(1.0 - (1.0 - confidence) / 2.0)
    p_hat = k / n
    denominator = 1.0 + z**2 / n
    center_adj = p_hat + (z**2) / (2.0 * n)
    margin = z * np.sqrt((p_hat * (1.0 - p_hat) / n) + (z**2 / (4.0 * n**2)))
    low = max(0.0, (center_adj - margin) / denominator)
    high = min(1.0, (center_adj + margin) / denominator)
    return (float(low), float(high))


def write_markdown_table(df: pd.DataFrame, file_path: Path, title: str, subtitle: str = "") -> None:
    headers = list(df.columns)
    lines = [f"# {title}\n"]
    if subtitle:
        lines.append(f"{subtitle}\n")
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for _, row in df.iterrows():
        lines.append("| " + " | ".join(str(row[h]) for h in headers) + " |")
    lines.append("")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def run_v3_analysis(
    base_dir: Path = ROOT_PATH / "results" / "verified_ab_v3",
    instance_path: Path = ROOT_PATH / "instances" / "challenge" / "o1_maxcut_instance.json",
    ref_path: Path = ROOT_PATH / "results" / "data" / "classical_reference.json",
) -> None:
    data_dir = base_dir / "data"
    tables_dir = base_dir / "tables"
    figures_dir = base_dir / "figures"

    tables_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 75)
    print("  MAXCUT VERSION 3 — STATISTICAL ANALYSIS AND PUBLICATION TABLES/FIGURES")
    print("=" * 75)

    # 1. Load Ground Truth Reference
    instance = load_challenge_instance(instance_path)
    graph = MaxCutGraph.from_challenge_instance(instance)
    with open(ref_path, "r", encoding="utf-8") as f:
        ref_data = json.load(f)
    c_max = float(ref_data["optimal_cut_value"])
    optimal_bitstrings = set(ref_data["optimal_bitstrings"])

    # 2. Load Raw Experiment Artifacts
    case_keys = [
        "processor_a_ideal_reference",
        "processor_a_noisy_baseline",
        "processor_b_ideal_reference",
        "processor_b_noisy_baseline",
    ]
    raw_records = {}
    for key in case_keys:
        json_file = data_dir / f"{key}.json"
        with open(json_file, "r", encoding="utf-8") as f:
            raw_records[key] = json.load(f)

    analytic_expected_cut = raw_records["processor_a_ideal_reference"]["algorithm_parameters"]["analytic_expected_cut"]
    analytic_approx_ratio = analytic_expected_cut / c_max

    # 3. Recompute Empirical Cut Samples & Exact Uncertainty Metrics
    sample_data = {}
    summary_rows = []

    for key in case_keys:
        d = raw_records[key]
        case_name = d["experiment_case"]
        decoded_counts = d["decoded_counts"]
        shots = sum(decoded_counts.values())

        cuts_list = []
        opt_hits = 0
        cut_counts = {}

        for bs, count in decoded_counts.items():
            cut_val = graph.compute_cut(bs).cut_value
            cuts_list.extend([cut_val] * count)
            cut_counts[cut_val] = cut_counts.get(cut_val, 0) + count
            if bs in optimal_bitstrings:
                opt_hits += count

        cuts_arr = np.array(cuts_list, dtype=float)
        mean_c = float(np.mean(cuts_arr))
        var_c = float(np.var(cuts_arr, ddof=1))
        se_c = float(np.sqrt(var_c / shots))
        ci_c_low = mean_c - 1.96 * se_c
        ci_c_high = mean_c + 1.96 * se_c

        approx_ratio = mean_c / c_max
        ci_ar_low = approx_ratio - 1.96 * (se_c / c_max)
        ci_ar_high = approx_ratio + 1.96 * (se_c / c_max)

        p_opt = opt_hits / shots
        w_low, w_high = wilson_score_interval(opt_hits, shots, 0.95)

        circ_m = d["circuit_compilation_metrics"]
        backend_m = d["backend_metadata"]

        sample_data[key] = {
            "name": case_name,
            "cuts": cuts_arr,
            "mean": mean_c,
            "se": se_c,
            "var": var_c,
            "ci_mean": (ci_c_low, ci_c_high),
            "approx_ratio": approx_ratio,
            "ci_ar": (ci_ar_low, ci_ar_high),
            "p_opt": p_opt,
            "opt_hits": opt_hits,
            "wilson_ci": (w_low, w_high),
            "shots": shots,
            "depth": circ_m["transpiled_depth"],
            "total_gates": circ_m["transpiled_total_gates"],
            "2q_gates": circ_m["transpiled_2q_gates"],
            "basis_2q": circ_m["basis_synthesis_2q_gates"],
            "routing_2q": circ_m["routing_2q_gates"],
            "swaps": circ_m["routing_swap_count"],
            "backend_qubits": backend_m["backend_physical_qubits"],
            "active_qubits": backend_m["active_physical_qubits_count"],
            "used_qubits": backend_m["active_physical_qubits"],
            "cut_counts": cut_counts,
        }

        summary_rows.append({
            "Key": key,
            "Experiment Case": case_name,
            "Target": backend_m["backend_name"],
            "Architecture": backend_m["architecture_family"],
            "Backend Physical Qubits": backend_m["backend_physical_qubits"],
            "Active Qubits": backend_m["active_physical_qubits_count"],
            "Mapped Qubits": str(backend_m["active_physical_qubits"]),
            "Execution Mode": backend_m["execution_mode"],
            "Noisy": d["is_noisy_simulation"],
            "Best Cut": float(d["results"]["best_sampled_cut"]),
            "Mean Cut <C>": round(mean_c, 4),
            "Std Error": round(se_c, 4),
            "95% CI Mean Cut": f"[{ci_c_low:.4f}, {ci_c_high:.4f}]",
            "Sample Approx Ratio": round(approx_ratio, 4),
            "95% CI Approx Ratio": f"[{ci_ar_low:.4f}, {ci_ar_high:.4f}]",
            "Analytic <C>": round(analytic_expected_cut, 4),
            "Analytic Approx Ratio": round(analytic_approx_ratio, 4),
            "Optimal Hits": opt_hits,
            "Success Prob P(opt)": round(p_opt, 4),
            "Wilson 95% CI P(opt)": f"[{w_low*100:.2f}%, {w_high*100:.2f}%]",
            "Native 2Q Gates": circ_m["transpiled_2q_gates"],
            "Basis 2Q Gates": circ_m["basis_synthesis_2q_gates"],
            "Routing 2Q Gates": circ_m["routing_2q_gates"],
            "Routing SWAPs": circ_m["routing_swap_count"],
            "Circuit Depth": circ_m["transpiled_depth"],
            "Total Gates": circ_m["transpiled_total_gates"],
            "Shots": shots,
        })

    summary_df = pd.DataFrame(summary_rows)
    write_markdown_table(
        summary_df,
        tables_dir / "statistical_uncertainty_table.md",
        "Statistical Uncertainty & Solution Quality Table (Version 3)",
        "Derived directly from raw finite-shot measurement counts (N = 2048) under exact ground truth C_max = 6.0000.",
    )
    summary_df.to_csv(tables_dir / "statistical_uncertainty_table.csv", index=False)

    # 4. Pairwise Hypothesis Testing (Welch's t-test and Two-Proportion z-test)
    comp_defs = [
        ("Comparison 1: Processor A Ideal vs. Noisy", "processor_a_ideal_reference", "processor_a_noisy_baseline"),
        ("Comparison 2: Processor B Ideal vs. Noisy", "processor_b_ideal_reference", "processor_b_noisy_baseline"),
        ("Comparison 3a: Processor A vs. B (Controlled Ideal)", "processor_a_ideal_reference", "processor_b_ideal_reference"),
        ("Comparison 3b: Processor A vs. B (Controlled Noisy)", "processor_a_noisy_baseline", "processor_b_noisy_baseline"),
    ]

    hypothesis_rows = []
    for label, k1, k2 in comp_defs:
        s1 = sample_data[k1]
        s2 = sample_data[k2]

        # Welch's two-sample t-test on continuous cut samples
        t_stat, p_val_t = stats.ttest_ind(s1["cuts"], s2["cuts"], equal_var=False)
        delta_cut = s1["mean"] - s2["mean"]
        se_diff = np.sqrt(s1["var"] / s1["shots"] + s2["var"] / s2["shots"])
        ci_diff_cut = (delta_cut - 1.96 * se_diff, delta_cut + 1.96 * se_diff)
        cut_diff_detected = "Yes (p < 0.05)" if p_val_t < 0.05 else "No statistically significant difference detected"

        # Two-proportion pooled z-test on optimal success probability
        p_pool = (s1["opt_hits"] + s2["opt_hits"]) / (s1["shots"] + s2["shots"])
        se_prop = np.sqrt(p_pool * (1.0 - p_pool) * (1.0 / s1["shots"] + 1.0 / s2["shots"]))
        z_stat = (s1["p_opt"] - s2["p_opt"]) / se_prop if se_prop > 0 else 0.0
        p_val_z = 2.0 * (1.0 - stats.norm.cdf(abs(z_stat)))
        delta_prop = s1["p_opt"] - s2["p_opt"]
        se_prop_unpool = np.sqrt(s1["p_opt"] * (1.0 - s1["p_opt"]) / s1["shots"] + s2["p_opt"] * (1.0 - s2["p_opt"]) / s2["shots"])
        ci_diff_prop = (delta_prop - 1.96 * se_prop_unpool, delta_prop + 1.96 * se_prop_unpool)
        prop_diff_detected = "Yes (p < 0.05)" if p_val_z < 0.05 else "No statistically significant difference detected"

        hypothesis_rows.append({
            "Comparison": label,
            "Group 1": s1["name"],
            "Group 2": s2["name"],
            "Delta Mean Cut": round(delta_cut, 4),
            "95% CI Delta Cut": f"[{ci_diff_cut[0]:.4f}, {ci_diff_cut[1]:.4f}]",
            "Welch t-stat": round(t_stat, 3),
            "p-value (Mean Cut)": f"{p_val_t:.4e}",
            "Mean Cut Difference Detected?": cut_diff_detected,
            "Delta P(opt)": f"{delta_prop*100:+.2f}%",
            "95% CI Delta P(opt)": f"[{ci_diff_prop[0]*100:.2f}%, {ci_diff_prop[1]*100:.2f}%]",
            "Two-Prop z-stat": round(z_stat, 3),
            "p-value (Proportion)": f"{p_val_z:.4e}",
            "Proportion Difference Detected?": prop_diff_detected,
        })

    hyp_df = pd.DataFrame(hypothesis_rows)
    write_markdown_table(
        hyp_df,
        tables_dir / "pairwise_comparisons_table.md",
        "Pairwise Statistical Hypothesis Tests (Version 3)",
        "Tested at alpha = 0.05. Non-significant tests are strictly reported as 'No statistically significant difference detected' rather than proof of equivalence.",
    )
    hyp_df.to_csv(tables_dir / "pairwise_comparisons_table.csv", index=False)

    # 5. Resource Overhead vs Solution Quality Table
    res_rows = []
    for key in case_keys:
        s = sample_data[key]
        d = raw_records[key]
        bm = d["backend_metadata"]
        res_rows.append({
            "Experiment Case": s["name"],
            "Target Backend": bm["backend_name"],
            "Architecture Family": bm["architecture_family"],
            "Backend Physical Qubits": bm["backend_physical_qubits"],
            "Active Physical Qubits": bm["active_physical_qubits_count"],
            "Mapped Qubits": str(bm["active_physical_qubits"]),
            "Execution Mode": bm["execution_mode"],
            "Circuit Depth": s["depth"],
            "Total Gates": s["total_gates"],
            "Native 2Q Gate": bm["native_2q_gate"],
            "Total 2Q Count": s["2q_gates"],
            "Basis 2Q Count": s["basis_2q"],
            "Routing 2Q Overhead": s["routing_2q"],
            "Routing SWAPs": s["swaps"],
            "Approximation Ratio": round(s["approx_ratio"], 4),
            "Success Prob P(opt)": f"{s['p_opt']*100:.2f}%",
        })
    res_df = pd.DataFrame(res_rows)
    write_markdown_table(
        res_df,
        tables_dir / "resource_vs_quality_table.md",
        "Resource Overhead vs. Solution Quality Matrix (Version 3)",
        "Hardware-level resource consumption versus optimization quality across corrected architectures.",
    )
    res_df.to_csv(tables_dir / "resource_vs_quality_table.csv", index=False)

    # Also write table1, table2, table3 for canonical naming
    res_df.to_csv(tables_dir / "table1_circuit_compilation_breakdown.csv", index=False)
    write_markdown_table(res_df, tables_dir / "table1_circuit_compilation_breakdown.md", "Table 1: Circuit Compilation Breakdown (Version 3)")

    summary_df.to_csv(tables_dir / "table2_performance_comparison.csv", index=False)
    write_markdown_table(summary_df, tables_dir / "table2_performance_comparison.md", "Table 2: Performance Comparison (Version 3)")

    hyp_df.to_csv(tables_dir / "table3_statistical_hypothesis_tests.csv", index=False)
    write_markdown_table(hyp_df, tables_dir / "table3_statistical_hypothesis_tests.md", "Table 3: Statistical Hypothesis Tests (Version 3)")

    # 6. Save Complete Statistical Analysis JSON Summary
    full_summary = {
        "metadata": {
            "title": "Version 3 Statistical Analysis Summary",
            "formulation": "5_qubit_symmetry_reduced",
            "instance": graph.name,
            "c_max": c_max,
            "analytic_expected_cut": analytic_expected_cut,
            "analytic_approx_ratio": analytic_approx_ratio,
            "shots": 2048,
        },
        "case_summary": summary_rows,
        "pairwise_hypothesis_tests": hypothesis_rows,
        "resource_vs_quality": res_rows,
    }
    with open(data_dir / "statistical_analysis_summary.json", "w", encoding="utf-8") as f:
        json.dump(full_summary, f, indent=2)

    # 7. Generate High-Resolution Publication Figures
    plt.rcParams.update({"font.size": 11, "font.family": "sans-serif"})

    # --- Figure 1: Cut Sampling Distribution ---
    fig, axes = plt.subplots(2, 2, figsize=(14, 10), sharey=True)
    fig.suptitle("Figure 1: Measurement Cut Value Distributions across Corrected Targets (V3, N=2048)", fontsize=14, fontweight="bold")

    colors = {
        "processor_a_ideal_reference": "#1f77b4",
        "processor_a_noisy_baseline": "#aec7e8",
        "processor_b_ideal_reference": "#2ca02c",
        "processor_b_noisy_baseline": "#98df8a",
    }

    possible_cuts = sorted(list(set(c for s in sample_data.values() for c in s["cut_counts"].keys())))
    ax_map = {
        "processor_a_ideal_reference": axes[0, 0],
        "processor_a_noisy_baseline": axes[0, 1],
        "processor_b_ideal_reference": axes[1, 0],
        "processor_b_noisy_baseline": axes[1, 1],
    }

    for key, ax in ax_map.items():
        s = sample_data[key]
        counts = [s["cut_counts"].get(c, 0) for c in possible_cuts]
        probs = [cnt / s["shots"] for cnt in counts]
        bars = ax.bar(possible_cuts, probs, width=0.6, color=colors[key], edgecolor="black", alpha=0.85)

        # Highlight optimal cut C = 6.0
        for bar, cut_v in zip(bars, possible_cuts):
            if cut_v == c_max:
                bar.set_color("#d62728")
                bar.set_edgecolor("black")

        ax.set_title(f"{s['name']}\nMean = {s['mean']:.4f} +/- {s['se']:.4f} (SE) | P(opt) = {s['p_opt']*100:.1f}%", fontsize=11)
        ax.set_xlabel("Cut Value C(x)")
        ax.set_ylabel("Probability")
        ax.set_xticks(possible_cuts)
        ax.grid(axis="y", linestyle="--", alpha=0.5)

    plt.tight_layout()
    fig.savefig(figures_dir / "figure1_sampling_distribution.png", dpi=300)
    plt.close(fig)

    # --- Figure 2: Compilation & Resource Overhead Breakdown ---
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle("Figure 2: Architecture Compilation Resource Trade-Offs (Processor A 5Q vs. Processor B 7Q)", fontsize=14, fontweight="bold")

    labels = ["Proc A (5Q Tree)", "Proc B (7Q Heavy-Hex)"]
    x = np.arange(len(labels))
    width = 0.35

    basis_2q = [sample_data["processor_a_ideal_reference"]["basis_2q"], sample_data["processor_b_ideal_reference"]["basis_2q"]]
    routing_2q = [sample_data["processor_a_ideal_reference"]["routing_2q"], sample_data["processor_b_ideal_reference"]["routing_2q"]]

    ax1.bar(x, basis_2q, width, label="Basis Synthesis 2Q Gates", color="#1f77b4", edgecolor="black")
    ax1.bar(x, routing_2q, width, bottom=basis_2q, label="Routing Overhead 2Q Gates (SWAPs)", color="#ff7f0e", edgecolor="black")
    ax1.set_ylabel("Native Two-Qubit Gate Count")
    ax1.set_title("2Q Gate Decomposition Breakdown")
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels)
    ax1.legend(loc="upper left")
    ax1.grid(axis="y", linestyle="--", alpha=0.5)

    depths = [sample_data["processor_a_ideal_reference"]["depth"], sample_data["processor_b_ideal_reference"]["depth"]]
    bars_depth = ax2.bar(x, depths, width=0.4, color=["#1f77b4", "#2ca02c"], edgecolor="black")
    ax2.set_ylabel("Transpiled Circuit Depth (Cycles)")
    ax2.set_title("Transpiled Circuit Schedule Depth")
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels)
    ax2.grid(axis="y", linestyle="--", alpha=0.5)

    for bar, d_val in zip(bars_depth, depths):
        ax2.text(bar.get_x() + bar.get_width()/2, d_val + 1, f"{d_val} cycles", ha="center", va="bottom", fontweight="bold")

    plt.tight_layout()
    fig.savefig(figures_dir / "figure2_compilation_overhead_breakdown.png", dpi=300)
    plt.close(fig)

    # --- Figure 3: Metrics & Confidence Intervals ---
    fig, (ax_mean, ax_popt) = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle("Figure 3: Solution Quality Comparison with 95% Confidence Intervals", fontsize=14, fontweight="bold")

    plot_keys = case_keys
    plot_labels = [
        "Proc A\nIdeal",
        "Proc A\nNoisy",
        "Proc B\nIdeal",
        "Proc B\nNoisy",
    ]
    x_pos = np.arange(len(plot_keys))

    means = [sample_data[k]["mean"] for k in plot_keys]
    se_errs = [1.96 * sample_data[k]["se"] for k in plot_keys]

    ax_mean.errorbar(x_pos, means, yerr=se_errs, fmt="o", color="#1f77b4", ecolor="#1f77b4", elinewidth=2, capsize=5, markersize=8)
    ax_mean.axhline(analytic_expected_cut, color="gray", linestyle="--", label=f"Analytic Expectation (<C> = {analytic_expected_cut:.4f})")
    ax_mean.axhline(c_max, color="red", linestyle=":", label=f"Classical Optimum (C_max = {c_max:.1f})")
    ax_mean.set_ylabel("Expected Cut Value <C>")
    ax_mean.set_title("Mean Cut with 95% Wald CI")
    ax_mean.set_xticks(x_pos)
    ax_mean.set_xticklabels(plot_labels)
    ax_mean.legend(loc="lower left")
    ax_mean.grid(linestyle="--", alpha=0.5)

    popts = [sample_data[k]["p_opt"] * 100 for k in plot_keys]
    w_err_low = [popts[i] - sample_data[k]["wilson_ci"][0] * 100 for i, k in enumerate(plot_keys)]
    w_err_high = [sample_data[k]["wilson_ci"][1] * 100 - popts[i] for i, k in enumerate(plot_keys)]
    yerr_w = [w_err_low, w_err_high]

    ax_popt.errorbar(x_pos, popts, yerr=yerr_w, fmt="s", color="#2ca02c", ecolor="#2ca02c", elinewidth=2, capsize=5, markersize=8)
    ax_popt.set_ylabel("Ground State Success Probability P(opt) (%)")
    ax_popt.set_title("Success Probability with 95% Wilson Score Interval")
    ax_popt.set_xticks(x_pos)
    ax_popt.set_xticklabels(plot_labels)
    ax_popt.grid(linestyle="--", alpha=0.5)

    plt.tight_layout()
    fig.savefig(figures_dir / "figure3_metric_confidence_intervals.png", dpi=300)
    plt.close(fig)

    print(f"\n[COMPLETE] Statistical analysis, tables, and figures generated successfully!")
    print(f"  Tables written to: {tables_dir}")
    print(f"  Figures written to: {figures_dir}")


if __name__ == "__main__":
    run_v3_analysis()
