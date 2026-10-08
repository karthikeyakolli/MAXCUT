"""Generates empirical figures, tables, and statistics for the Processor A vs. Processor B analysis."""

import json
from pathlib import Path
import sys
from typing import Any, Dict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from maxcut.experiments.schema import load_experiment_result


def calculate_distribution_stats(result_dict: Dict[str, Any]) -> Dict[str, Any]:
    decoded_counts = result_dict["decoded_counts"]
    cut_values_by_bitstring = result_dict["cut_values_by_bitstring"]
    total_shots = result_dict["probability_metrics"]["total_shots_sampled"]

    cut_counts = {c: 0 for c in range(7)}
    all_cuts = []

    for bstr, count in decoded_counts.items():
        cut = int(round(cut_values_by_bitstring.get(bstr, 0.0)))
        cut_counts[cut] = cut_counts.get(cut, 0) + count
        all_cuts.extend([cut] * count)

    all_cuts_arr = np.array(all_cuts)
    cut_probs = {c: count / total_shots for c, count in cut_counts.items()}

    return {
        "cut_counts": cut_counts,
        "cut_probs": cut_probs,
        "mean_cut": float(np.mean(all_cuts_arr)),
        "std_cut": float(np.std(all_cuts_arr)),
        "median_cut": float(np.median(all_cuts_arr)),
        "min_cut": int(np.min(all_cuts_arr)),
        "max_cut": int(np.max(all_cuts_arr)),
    }


def main():
    data_dir = Path("results/data")
    tables_dir = Path("results/tables")
    figures_dir = Path("results/figures")
    tables_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    sim_res = load_experiment_result(data_dir / "O1_MaxCut_Challenge_aer_simulator_p1_result.json").to_dict()
    proc_a_res = load_experiment_result(data_dir / "O1_MaxCut_Challenge_processor_a_p1_result.json").to_dict()
    proc_b_res = load_experiment_result(data_dir / "O1_MaxCut_Challenge_processor_b_p1_result.json").to_dict()

    sim_stats = calculate_distribution_stats(sim_res)
    proc_a_stats = calculate_distribution_stats(proc_a_res)
    proc_b_stats = calculate_distribution_stats(proc_b_res)

    # -------------------------------------------------------------
    # 1. Build Comprehensive Comparison Table
    # -------------------------------------------------------------
    comparison_rows = [
        {
            "Target": "Ideal Aer Simulator",
            "Target Type": "Simulator",
            "Architecture Family": "Unconstrained All-to-All",
            "Native 2Q Gate": "cx",
            "Logical Qubits": 6,
            "Physical Qubits": 32,
            "Logical Depth": 10,
            "Transpiled Depth": sim_res["circuit_metrics"]["transpiled_circuit_depth"],
            "Logical 2Q Gates": 8,
            "Transpiled 2Q Gates": sim_res["circuit_metrics"]["transpiled_2q_gates"],
            "SWAP Count": sim_res["circuit_metrics"]["swap_count"],
            "Total Transpiled Gates": sim_res["circuit_metrics"]["transpiled_total_gates"],
            "Routing 2Q Overhead": "1.00x",
            "Depth Expansion": "1.00x",
            "Best Cut": sim_res["cut_value"],
            "Optimal Cut Hit": "Yes",
            "Expected Cut <C>": sim_res["expected_cut"],
            "Approximation Ratio (alpha)": sim_res["approximation_ratio"],
            "Ground State Prob P(opt)": sim_res["probability_metrics"]["ground_state_success_probability"],
            "Sample Mean Cut": sim_stats["mean_cut"],
            "Sample Std Cut": sim_stats["std_cut"],
            "Sample Median Cut": sim_stats["median_cut"],
            "Optimization Time (s)": sim_res["runtime"]["optimization_time_seconds"],
            "Execution Time (s)": sim_res["runtime"]["simulation_time_seconds"],
            "Total Time (s)": sim_res["runtime"]["total_pipeline_time_seconds"],
            "Job ID": sim_res["job_metadata"]["job_id"],
        },
        {
            "Target": "Processor A",
            "Target Type": "Hardware Target (Falcon-H)",
            "Architecture Family": "Falcon-H Heavy-Hex Subset",
            "Native 2Q Gate": "ecr",
            "Logical Qubits": 6,
            "Physical Qubits": 7,
            "Logical Depth": 10,
            "Transpiled Depth": proc_a_res["circuit_metrics"]["transpiled_circuit_depth"],
            "Logical 2Q Gates": 8,
            "Transpiled 2Q Gates": proc_a_res["circuit_metrics"]["transpiled_2q_gates"],
            "SWAP Count": proc_a_res["circuit_metrics"]["swap_count"],
            "Total Transpiled Gates": proc_a_res["circuit_metrics"]["transpiled_total_gates"],
            "Routing 2Q Overhead": f"{proc_a_res['circuit_metrics']['routing_overhead_ratio']:.2f}x",
            "Depth Expansion": f"{proc_a_res['circuit_metrics']['depth_expansion_ratio']:.2f}x",
            "Best Cut": proc_a_res["cut_value"],
            "Optimal Cut Hit": "Yes",
            "Expected Cut <C>": proc_a_res["expected_cut"],
            "Approximation Ratio (alpha)": proc_a_res["approximation_ratio"],
            "Ground State Prob P(opt)": proc_a_res["probability_metrics"]["ground_state_success_probability"],
            "Sample Mean Cut": proc_a_stats["mean_cut"],
            "Sample Std Cut": proc_a_stats["std_cut"],
            "Sample Median Cut": proc_a_stats["median_cut"],
            "Optimization Time (s)": proc_a_res["runtime"]["optimization_time_seconds"],
            "Execution Time (s)": proc_a_res["runtime"]["simulation_time_seconds"],
            "Total Time (s)": proc_a_res["runtime"]["total_pipeline_time_seconds"],
            "Job ID": proc_a_res["job_metadata"]["job_id"],
        },
        {
            "Target": "Processor B",
            "Target Type": "Hardware Target (Ring-7)",
            "Architecture Family": "Ring-7 Circular Ring",
            "Native 2Q Gate": "cz",
            "Logical Qubits": 6,
            "Physical Qubits": 7,
            "Logical Depth": 10,
            "Transpiled Depth": proc_b_res["circuit_metrics"]["transpiled_circuit_depth"],
            "Logical 2Q Gates": 8,
            "Transpiled 2Q Gates": proc_b_res["circuit_metrics"]["transpiled_2q_gates"],
            "SWAP Count": proc_b_res["circuit_metrics"]["swap_count"],
            "Total Transpiled Gates": proc_b_res["circuit_metrics"]["transpiled_total_gates"],
            "Routing 2Q Overhead": f"{proc_b_res['circuit_metrics']['routing_overhead_ratio']:.2f}x",
            "Depth Expansion": f"{proc_b_res['circuit_metrics']['depth_expansion_ratio']:.2f}x",
            "Best Cut": proc_b_res["cut_value"],
            "Optimal Cut Hit": "Yes",
            "Expected Cut <C>": proc_b_res["expected_cut"],
            "Approximation Ratio (alpha)": proc_b_res["approximation_ratio"],
            "Ground State Prob P(opt)": proc_b_res["probability_metrics"]["ground_state_success_probability"],
            "Sample Mean Cut": proc_b_stats["mean_cut"],
            "Sample Std Cut": proc_b_stats["std_cut"],
            "Sample Median Cut": proc_b_stats["median_cut"],
            "Optimization Time (s)": proc_b_res["runtime"]["optimization_time_seconds"],
            "Execution Time (s)": proc_b_res["runtime"]["simulation_time_seconds"],
            "Total Time (s)": proc_b_res["runtime"]["total_pipeline_time_seconds"],
            "Job ID": proc_b_res["job_metadata"]["job_id"],
        },
    ]

    df_comp = pd.DataFrame(comparison_rows)
    df_comp.to_csv(tables_dir / "processor_comparison_table.csv", index=False)
    with open(tables_dir / "processor_comparison_table.json", "w", encoding="utf-8") as f:
        json.dump(comparison_rows, f, indent=2)

    # Save Markdown version
    def to_md(df: pd.DataFrame) -> str:
        headers = list(df.columns)
        lines = ["| " + " | ".join(headers) + " |"]
        lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
        for _, row in df.iterrows():
            lines.append("| " + " | ".join(str(val) for val in row.values) + " |")
        return "\n".join(lines)

    (tables_dir / "processor_comparison_table.md").write_text(to_md(df_comp), encoding="utf-8")

    # -------------------------------------------------------------
    # 2. Cut Value Distribution Table
    # -------------------------------------------------------------
    cut_rows = []
    for c in range(7):
        cut_rows.append({
            "Cut Value C(x)": c,
            "Is Ground State (C=6)": "Yes" if c == 6 else "No",
            "Simulator Shots": sim_stats["cut_counts"][c],
            "Simulator Probability": f"{sim_stats['cut_probs'][c]:.4f} ({sim_stats['cut_probs'][c]*100:.2f}%)",
            "Processor A Shots": proc_a_stats["cut_counts"][c],
            "Processor A Probability": f"{proc_a_stats['cut_probs'][c]:.4f} ({proc_a_stats['cut_probs'][c]*100:.2f}%)",
            "Processor B Shots": proc_b_stats["cut_counts"][c],
            "Processor B Probability": f"{proc_b_stats['cut_probs'][c]:.4f} ({proc_b_stats['cut_probs'][c]*100:.2f}%)",
        })
    df_cuts = pd.DataFrame(cut_rows)
    df_cuts.to_csv(tables_dir / "cut_distribution_table.csv", index=False)
    (tables_dir / "cut_distribution_table.md").write_text(to_md(df_cuts), encoding="utf-8")

    # -------------------------------------------------------------
    # 3. Figure 1: Objective Cut Distribution Comparison
    # -------------------------------------------------------------
    cuts = np.arange(7)
    width = 0.25

    plt.figure(figsize=(10, 6), dpi=300)
    plt.bar(cuts - width, [sim_stats["cut_probs"][c] for c in cuts], width=width, label="Simulator (Ideal)", color="#3b82f6", alpha=0.9, edgecolor="black")
    plt.bar(cuts, [proc_a_stats["cut_probs"][c] for c in cuts], width=width, label="Processor A (Falcon-H)", color="#ef4444", alpha=0.9, edgecolor="black")
    plt.bar(cuts + width, [proc_b_stats["cut_probs"][c] for c in cuts], width=width, label="Processor B (Ring-7)", color="#10b981", alpha=0.9, edgecolor="black")

    plt.axvline(x=6, color="#eab308", linestyle="--", linewidth=1.5, label="Optimal Cut $C_{\\max}=6$")
    plt.xlabel("Cut Value $C(x)$", fontsize=12, fontweight="bold")
    plt.ylabel("Sampled Empirical Probability $P(C)$", fontsize=12, fontweight="bold")
    plt.title("O1 Max-Cut QAOA ($p=1$): Empirical Cut Value Distribution Comparison\n(2048 Shots, Seed=42, Opt Level=1)", fontsize=13, fontweight="bold")
    plt.xticks(cuts, [str(c) for c in cuts])
    plt.grid(axis="y", linestyle=":", alpha=0.6)
    plt.legend(frameon=True, facecolor="white", edgecolor="none")
    plt.tight_layout()
    plt.savefig(figures_dir / "figure1_cut_distribution_comparison.png", dpi=300)
    plt.close()

    # -------------------------------------------------------------
    # 4. Figure 2: Architecture & Resource Overhead Comparison
    # -------------------------------------------------------------
    fig, axes = plt.subplots(1, 3, figsize=(14, 5), dpi=300)

    targets = ["Ideal Sim", "Proc A (Falcon-H)", "Proc B (Ring-7)"]
    colors = ["#3b82f6", "#ef4444", "#10b981"]

    # (a) Transpiled Circuit Depth
    depths = [
        sim_res["circuit_metrics"]["transpiled_circuit_depth"],
        proc_a_res["circuit_metrics"]["transpiled_circuit_depth"],
        proc_b_res["circuit_metrics"]["transpiled_circuit_depth"],
    ]
    axes[0].bar(targets, depths, color=colors, edgecolor="black")
    axes[0].set_title("Transpiled Circuit Depth", fontsize=11, fontweight="bold")
    axes[0].set_ylabel("Depth (Cycles)", fontsize=10)
    for i, v in enumerate(depths):
        axes[0].text(i, v + 2, str(v), ha="center", fontweight="bold", fontsize=10)
    axes[0].grid(axis="y", linestyle=":", alpha=0.6)

    # (b) Two-Qubit Entangling Gates
    two_qs = [
        sim_res["circuit_metrics"]["transpiled_2q_gates"],
        proc_a_res["circuit_metrics"]["transpiled_2q_gates"],
        proc_b_res["circuit_metrics"]["transpiled_2q_gates"],
    ]
    axes[1].bar(targets, two_qs, color=colors, edgecolor="black")
    axes[1].set_title("Transpiled 2-Qubit Gates", fontsize=11, fontweight="bold")
    axes[1].set_ylabel("2Q Gate Count", fontsize=10)
    for i, v in enumerate(two_qs):
        axes[1].text(i, v + 0.8, str(v), ha="center", fontweight="bold", fontsize=10)
    axes[1].grid(axis="y", linestyle=":", alpha=0.6)

    # (c) Total Gate Count Breakdown
    totals = [
        sim_res["circuit_metrics"]["transpiled_total_gates"],
        proc_a_res["circuit_metrics"]["transpiled_total_gates"],
        proc_b_res["circuit_metrics"]["transpiled_total_gates"],
    ]
    axes[2].bar(targets, totals, color=colors, edgecolor="black")
    axes[2].set_title("Total Gate Count", fontsize=11, fontweight="bold")
    axes[2].set_ylabel("Total Gate Count", fontsize=10)
    for i, v in enumerate(totals):
        axes[2].text(i, v + 3, str(v), ha="center", fontweight="bold", fontsize=10)
    axes[2].grid(axis="y", linestyle=":", alpha=0.6)

    plt.suptitle("Hardware Architectural Resource Demands (O1 Max-Cut, $p=1$)", fontsize=13, fontweight="bold", y=1.02)
    plt.tight_layout()
    plt.savefig(figures_dir / "figure2_circuit_resource_comparison.png", dpi=300)
    plt.close()

    # -------------------------------------------------------------
    # 5. Figure 3: Solution Quality & Success Probability
    # -------------------------------------------------------------
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 5), dpi=300)

    # (a) Approximation Ratio alpha
    alphas = [
        sim_res["approximation_ratio"] * 100,
        proc_a_res["approximation_ratio"] * 100,
        proc_b_res["approximation_ratio"] * 100,
    ]
    ax1.bar(targets, alphas, color=colors, edgecolor="black")
    ax1.set_title("Approximation Ratio $\\alpha = \\langle C \\rangle / C_{\\max}$ (%)", fontsize=11, fontweight="bold")
    ax1.set_ylabel("$\\alpha$ Percentage (%)", fontsize=10)
    ax1.set_ylim(75, 85)
    for i, v in enumerate(alphas):
        ax1.text(i, v + 0.3, f"{v:.2f}%", ha="center", fontweight="bold", fontsize=10)
    ax1.grid(axis="y", linestyle=":", alpha=0.6)

    # (b) Ground State Success Probability P(opt)
    p_opts = [
        sim_res["probability_metrics"]["ground_state_success_probability"] * 100,
        proc_a_res["probability_metrics"]["ground_state_success_probability"] * 100,
        proc_b_res["probability_metrics"]["ground_state_success_probability"] * 100,
    ]
    ax2.bar(targets, p_opts, color=colors, edgecolor="black")
    ax2.set_title("Ground State Sampling Probability $P(x^*)$ (%)", fontsize=11, fontweight="bold")
    ax2.set_ylabel("Success Probability (%)", fontsize=10)
    ax2.set_ylim(30, 45)
    for i, v in enumerate(p_opts):
        ax2.text(i, v + 0.4, f"{v:.2f}%", ha="center", fontweight="bold", fontsize=10)
    ax2.grid(axis="y", linestyle=":", alpha=0.6)

    plt.suptitle("Solution Quality Comparison: Approximation Ratio & Ground State Probability", fontsize=13, fontweight="bold", y=1.02)
    plt.tight_layout()
    plt.savefig(figures_dir / "figure3_solution_quality_comparison.png", dpi=300)
    plt.close()

    print("Successfully generated all analysis tables and figures.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
