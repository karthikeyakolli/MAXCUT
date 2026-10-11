"""Statistical analysis and artifact generation for Phase R3.

Computes:
1. Four-way comparison table (Processor A Ideal, Processor A Noisy, Processor B Ideal, Processor B Noisy).
2. Sample mean cut, standard error, 95% CI.
3. Success probability, standard error, Wilson 95% CI.
4. Pairwise statistical tests:
   - Processor A Ideal vs Processor A Noisy
   - Processor B Ideal vs Processor B Noisy
   - Processor A Noisy vs Processor B Noisy
5. Export tables to CSV, Markdown, and JSON.
6. Generate publication-quality visualization comparing ideal vs noisy distributions and metrics.
"""

import json
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

from maxcut.domain.model import MaxCutGraph
from maxcut.io import load_challenge_instance
from maxcut.qaoa.decoding import decode_qiskit_counts


def run_analysis():
    print("=" * 70)
    print("  PHASE R3 — NOISE ANALYSIS AND FINAL METRICS")
    print("=" * 70)

    results_dir = Path("results/data")
    tables_dir = Path("results/tables")
    figures_dir = Path("results/figures")
    tables_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    cases = {
        "proc_a_ideal": results_dir / "O1_MaxCut_Challenge_processor_a_ideal_reference.json",
        "proc_a_noisy": results_dir / "O1_MaxCut_Challenge_processor_a_noisy_baseline.json",
        "proc_b_ideal": results_dir / "O1_MaxCut_Challenge_processor_b_ideal_reference.json",
        "proc_b_noisy": results_dir / "O1_MaxCut_Challenge_processor_b_noisy_baseline.json",
    }

    data = {}
    for key, path in cases.items():
        with open(path, "r", encoding="utf-8") as f:
            data[key] = json.load(f)

    instance = load_challenge_instance("instances/challenge/o1_maxcut_instance.json")
    graph = MaxCutGraph.from_challenge_instance(instance)
    c_max = 6.0

    with open("results/data/classical_reference.json", "r", encoding="utf-8") as f:
        ref_data = json.load(f)
    optimal_bitstrings = set(ref_data["optimal_bitstrings"])

    # Extract cut distribution for each run
    summary_rows = []
    cut_samples = {}

    for key, d in data.items():
        name = d["experiment_case"]
        decoded = d["decoded_counts"]
        shots = sum(decoded.values())
        backend_name = d.get("backend_metadata", {}).get("backend_name", d.get("processor_target", "Unknown"))

        cuts = []
        hits = 0
        for bitstr, count in decoded.items():
            # compute cut value
            res = graph.compute_cut(bitstr)
            cut_val = res.cut_value
            cuts.extend([cut_val] * count)
            if bitstr in optimal_bitstrings:
                hits += count

        cuts = np.array(cuts)
        cut_samples[key] = cuts
        mean_cut = float(np.mean(cuts))
        std_cut = float(np.std(cuts, ddof=1))
        sem_cut = std_cut / np.sqrt(shots)
        ci_cut_low = mean_cut - 1.96 * sem_cut
        ci_cut_high = mean_cut + 1.96 * sem_cut

        approx_ratio = mean_cut / c_max

        p_success = hits / shots
        sem_p = np.sqrt(p_success * (1.0 - p_success) / shots)
        # Wilson score interval for proportion
        z = 1.96
        denom = 1.0 + (z**2) / shots
        center = (p_success + (z**2) / (2.0 * shots)) / denom
        diff = z * np.sqrt((p_success * (1.0 - p_success) / shots) + (z**2) / (4.0 * shots**2)) / denom
        ci_p_low = center - diff
        ci_p_high = center + diff

        cm = d["circuit_metrics"]
        summary_rows.append({
            "key": key,
            "case_name": name,
            "backend": backend_name,
            "execution_mode": d["execution_mode"],
            "shots": shots,
            "best_cut": float(np.max(cuts)),
            "mean_cut": mean_cut,
            "sem_cut": sem_cut,
            "ci_cut_95": f"[{ci_cut_low:.4f}, {ci_cut_high:.4f}]",
            "approx_ratio": approx_ratio,
            "p_success": p_success,
            "sem_p": sem_p,
            "ci_p_95": f"[{ci_p_low * 100:.2f}%, {ci_p_high * 100:.2f}%]",
            "depth": cm["transpiled_circuit_depth"],
            "two_qubit_gates": cm["transpiled_2q_gates"],
            "swap_count": cm["swap_count"],
            "total_gates": cm["transpiled_total_gates"],
            "physical_qubits": 6,
        })

    # Pairwise statistical comparisons
    comparisons = [
        ("proc_a_ideal", "proc_a_noisy", "Processor A: Ideal vs. Noisy"),
        ("proc_b_ideal", "proc_b_noisy", "Processor B: Ideal vs. Noisy"),
        ("proc_a_noisy", "proc_b_noisy", "Processor A Noisy vs. Processor B Noisy"),
        ("proc_a_ideal", "proc_b_ideal", "Processor A Ideal vs. Processor B Ideal"),
    ]

    comp_rows = []
    for k1, k2, comp_label in comparisons:
        c1 = cut_samples[k1]
        c2 = cut_samples[k2]
        m1, m2 = np.mean(c1), np.mean(c2)
        diff_mean = m1 - m2

        # Welch's t-test
        t_stat, p_val_t = stats.ttest_ind(c1, c2, equal_var=False)
        se_diff = np.sqrt(np.var(c1, ddof=1) / len(c1) + np.var(c2, ddof=1) / len(c2))
        ci_diff = (diff_mean - 1.96 * se_diff, diff_mean + 1.96 * se_diff)

        # Proportion test
        hits1 = sum(c1 == 6.0)
        hits2 = sum(c2 == 6.0)
        p1 = hits1 / len(c1)
        p2 = hits2 / len(c2)
        diff_p = p1 - p2
        se_p = np.sqrt(p1 * (1.0 - p1) / len(c1) + p2 * (1.0 - p2) / len(c2))
        z_stat = diff_p / se_p if se_p > 0 else 0.0
        p_val_z = 2.0 * (1.0 - stats.norm.cdf(abs(z_stat)))
        ci_diff_p = (diff_p - 1.96 * se_p, diff_p + 1.96 * se_p)

        is_sig_t = "Yes (p < 0.05)" if p_val_t < 0.05 else "No statistically significant difference detected"
        is_sig_z = "Yes (p < 0.05)" if p_val_z < 0.05 else "No statistically significant difference detected"

        comp_rows.append({
            "comparison": comp_label,
            "delta_mean_cut": diff_mean,
            "ci_delta_cut": f"[{ci_diff[0]:.4f}, {ci_diff[1]:.4f}]",
            "t_statistic": t_stat,
            "p_value_mean": p_val_t,
            "mean_significant": is_sig_t,
            "delta_success_prob": diff_p,
            "ci_delta_prob": f"[{ci_diff_p[0] * 100:.2f}%, {ci_diff_p[1] * 100:.2f}%]",
            "z_statistic": z_stat,
            "p_value_prob": p_val_z,
            "prob_significant": is_sig_z,
        })

    # Save summary table CSV and Markdown
    csv_path = tables_dir / "noise_aware_comparison_table.csv"
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write("Case,Backend,Mode,Shots,Best Cut,Mean Cut,SEM Cut,95% CI Cut,Approx Ratio,P(Opt),SEM P(Opt),95% CI P(Opt),Depth,2Q Gates,SWAPs,Total Gates\n")
        for r in summary_rows:
            f.write(f'"{r["case_name"]}","{r["backend"]}","{r["execution_mode"]}",{r["shots"]},{r["best_cut"]:.1f},{r["mean_cut"]:.4f},{r["sem_cut"]:.4f},"{r["ci_cut_95"]}",{r["approx_ratio"]:.4f},{r["p_success"]:.4f},{r["sem_p"]:.4f},"{r["ci_p_95"]}",{r["depth"]},{r["two_qubit_gates"]},{r["swap_count"]},{r["total_gates"]}\n')
    print(f"Saved: {csv_path}")

    md_path = tables_dir / "noise_aware_comparison_table.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# Processor A/B Noise-Aware Benchmark Summary Table\n\n")
        f.write("| Experiment Case | Execution Mode | Best Cut | Expected Cut $\\langle C \\rangle$ (95% CI) | Approx Ratio $\\alpha$ | Success Prob $P_{\\text{opt}}$ (95% CI) | Circuit Depth | 2Q Gates | SWAP Count |\n")
        f.write("| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |\n")
        for r in summary_rows:
            f.write(f"| **{r['case_name']}** | `{r['execution_mode']}` | {r['best_cut']:.1f} | {r['mean_cut']:.4f} {r['ci_cut_95']} | {r['approx_ratio']:.4f} ({r['approx_ratio']*100:.2f}%) | {r['p_success']:.4f} {r['ci_p_95']} | {r['depth']} | {r['two_qubit_gates']} | {r['swap_count']} |\n")
    print(f"Saved: {md_path}")

    comp_csv_path = tables_dir / "noise_statistical_uncertainty_table.csv"
    with open(comp_csv_path, "w", encoding="utf-8") as f:
        f.write("Comparison,Delta Mean Cut,95% CI Delta Cut,t-statistic,p-value (Cut),Cut Significance,Delta P(Opt),95% CI Delta P(Opt),z-statistic,p-value (P),Prob Significance\n")
        for cr in comp_rows:
            f.write(f'"{cr["comparison"]}",{cr["delta_mean_cut"]:.4f},"{cr["ci_delta_cut"]}",{cr["t_statistic"]:.4f},{cr["p_value_mean"]:.4e},"{cr["mean_significant"]}",{cr["delta_success_prob"]:.4f},"{cr["ci_delta_prob"]}",{cr["z_statistic"]:.4f},{cr["p_value_prob"]:.4e},"{cr["prob_significant"]}"\n')
    print(f"Saved: {comp_csv_path}")

    comp_md_path = tables_dir / "noise_statistical_uncertainty_table.md"
    with open(comp_md_path, "w", encoding="utf-8") as f:
        f.write("# Pairwise Statistical Comparison and Uncertainty Table\n\n")
        f.write("| Comparison | $\\Delta \\langle C \\rangle$ [95% CI] | $t$-statistic | $p$-value | Mean Cut Difference Detected? | $\\Delta P_{\\text{opt}}$ [95% CI] | $z$-statistic | $p$-value | Probability Difference Detected? |\n")
        f.write("| :--- | :---: | :---: | :---: | :--- | :---: | :---: | :---: | :--- |\n")
        for cr in comp_rows:
            f.write(f"| **{cr['comparison']}** | {cr['delta_mean_cut']:+.4f} {cr['ci_delta_cut']} | {cr['t_statistic']:.3f} | {cr['p_value_mean']:.3e} | {cr['mean_significant']} | {cr['delta_success_prob']:+.4f} {cr['ci_delta_prob']} | {cr['z_statistic']:.3f} | {cr['p_value_prob']:.3e} | {cr['prob_significant']} |\n")
    print(f"Saved: {comp_md_path}")

    # Generate comparative figure: Figure 6 (Ideal vs Noisy Comparison)
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    # Subplot 1: Expected Cut & Approx Ratio
    labels = ["A (Ideal)", "A (Noisy)", "B (Ideal)", "B (Noisy)"]
    means = [r["mean_cut"] for r in summary_rows]
    sems = [r["sem_cut"] for r in summary_rows]
    colors = ["#2563EB", "#93C5FD", "#059669", "#6EE7B7"]

    bars1 = axes[0].bar(labels, means, yerr=sems, capsize=5, color=colors, edgecolor="black", alpha=0.85)
    axes[0].axhline(6.0, color="crimson", linestyle="--", linewidth=1.5, label="Classical Optimum (C_max = 6.0)")
    axes[0].axhline(4.0, color="gray", linestyle=":", linewidth=1.0, label="Random Cut Expectation (4.0)")
    axes[0].set_ylabel("Expected Cut Value $\\langle C \\rangle$", fontsize=12)
    axes[0].set_title("Expected Cut Under Ideal vs. Noisy Emulation", fontsize=13, fontweight="bold")
    axes[0].set_ylim(0, 6.8)
    axes[0].legend(loc="upper right", fontsize=10)
    for bar in bars1:
        yval = bar.get_height()
        axes[0].text(bar.get_x() + bar.get_width() / 2.0, yval + 0.15, f"{yval:.4f}\n({yval/6.0*100:.1f}%)", ha="center", va="bottom", fontsize=10)

    # Subplot 2: Optimal Bitstring Success Probability
    probs = [r["p_success"] * 100 for r in summary_rows]
    sem_probs = [r["sem_p"] * 100 for r in summary_rows]
    bars2 = axes[1].bar(labels, probs, yerr=sem_probs, capsize=5, color=colors, edgecolor="black", alpha=0.85)
    axes[1].axhline(10.0 / 64.0 * 100, color="gray", linestyle=":", linewidth=1.0, label="Uniform Random Chance (15.63%)")
    axes[1].set_ylabel("Ground State Probability $P(x^*)$ (%)", fontsize=12)
    axes[1].set_title("Optimal Solution Probability $P_{\\text{opt}}$", fontsize=13, fontweight="bold")
    axes[1].set_ylim(0, 50)
    axes[1].legend(loc="upper right", fontsize=10)
    for bar in bars2:
        yval = bar.get_height()
        axes[1].text(bar.get_x() + bar.get_width() / 2.0, yval + 1.0, f"{yval:.2f}%", ha="center", va="bottom", fontsize=10)

    # Subplot 3: Circuit Resources (Depth and 2Q Gate Count)
    x = np.arange(len(labels))
    depths = [r["depth"] for r in summary_rows]
    two_q = [r["two_qubit_gates"] for r in summary_rows]
    width = 0.35

    axes[2].bar(x - width/2, depths, width, label="Circuit Depth", color="#6366F1", edgecolor="black", alpha=0.85)
    axes[2].bar(x + width/2, two_q, width, label="Native 2Q Gates", color="#F59E0B", edgecolor="black", alpha=0.85)
    axes[2].set_xticks(x)
    axes[2].set_xticklabels(labels)
    axes[2].set_ylabel("Resource Count", fontsize=12)
    axes[2].set_title("Compilation Resources (Invariance Under Noise)", fontsize=13, fontweight="bold")
    axes[2].legend(loc="upper right", fontsize=10)
    axes[2].set_ylim(0, 120)
    for i, (d, q) in enumerate(zip(depths, two_q)):
        axes[2].text(i - width/2, d + 1.5, f"{d}", ha="center", va="bottom", fontsize=9)
        axes[2].text(i + width/2, q + 1.5, f"{q}", ha="center", va="bottom", fontsize=9)

    plt.tight_layout()
    fig6_path = figures_dir / "figure6_ideal_vs_noisy_comparison.png"
    plt.savefig(fig6_path, dpi=150)
    plt.close()
    print(f"Saved: {fig6_path}")

    # JSON export of the full summary
    export_json = {
        "summary_rows": summary_rows,
        "pairwise_comparisons": comp_rows,
    }
    json_summary_path = results_dir / "noise_benchmark_summary.json"
    with open(json_summary_path, "w", encoding="utf-8") as f:
        json.dump(export_json, f, indent=2)
    print(f"Saved: {json_summary_path}")

    print("\n" + "=" * 70)
    print("  PHASE R3 STATISTICAL ANALYSIS COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    run_analysis()
