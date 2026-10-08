"""Visualization helper for QAOA measurement probability distributions.

Plots sampled bitstring probabilities, annotates individual cut values,
and highlights certified classical ground truth optimal partitions.
"""

from pathlib import Path
from typing import Dict, List, Optional, Union

import matplotlib.pyplot as plt
import numpy as np

from maxcut.domain.model import MaxCutGraph


def plot_measurement_distribution(
    decoded_counts: Dict[str, int],
    graph: MaxCutGraph,
    classical_optimal_cut: Optional[float] = None,
    classical_optimal_bitstrings: Optional[List[str]] = None,
    top_k: int = 16,
    title: Optional[str] = None,
    save_path: Optional[Union[str, Path]] = None,
) -> plt.Figure:
    """Plots the sampled bitstring probability distribution with cut annotations.

    Args:
        decoded_counts: Dictionary of canonical bitstring -> shot counts.
        graph: MaxCutGraph instance to evaluate cut values.
        classical_optimal_cut: Optional ground truth optimum C_max.
        classical_optimal_bitstrings: Optional list of certified optimal bitstrings.
        top_k: Maximum number of top-probability bitstrings to display.
        title: Optional custom chart title.
        save_path: Optional file path to save the generated figure.

    Returns:
        plt.Figure: Matplotlib figure object.
    """
    total_shots = sum(decoded_counts.values())
    if total_shots == 0:
        raise ValueError("Cannot plot distribution with zero total shots.")

    optimal_set = set(classical_optimal_bitstrings) if classical_optimal_bitstrings else set()

    # Sort bitstrings by frequency descending
    sorted_items = sorted(decoded_counts.items(), key=lambda kv: kv[1], reverse=True)
    display_items = sorted_items[:top_k]

    bitstrings = [item[0] for item in display_items]
    counts = [item[1] for item in display_items]
    probabilities = [c / total_shots for c in counts]
    cut_values = [graph.compute_cut(bs).cut_value for bs in bitstrings]

    # Color mapping: Green for optimal cuts, Slate blue for suboptimal
    bar_colors = []
    for bs, cut in zip(bitstrings, cut_values):
        if classical_optimal_cut is not None and cut >= classical_optimal_cut:
            bar_colors.append("#10b981")  # Emerald Green for Optimal
        elif bs in optimal_set:
            bar_colors.append("#10b981")
        else:
            bar_colors.append("#3b82f6")  # Primary Blue for Suboptimal

    # Set up figure
    fig, ax = plt.subplots(figsize=(12, 6), dpi=300)
    bars = ax.bar(range(len(bitstrings)), probabilities, color=bar_colors, width=0.65, edgecolor="#1e293b", linewidth=1.0)

    # Annotate bars with probability and cut value
    for i, (bar, prob, cut) in enumerate(zip(bars, probabilities, cut_values)):
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2.0,
            height + 0.005,
            f"{prob * 100:.1f}%\n(Cut={int(cut) if cut.is_integer() else cut})",
            ha="center",
            va="bottom",
            fontsize=8,
            fontweight="bold" if bar_colors[i] == "#10b981" else "normal",
            color="#0f172a",
        )

    # Configure axes
    ax.set_xticks(range(len(bitstrings)))
    ax.set_xticklabels(bitstrings, rotation=45, ha="right", fontsize=9, fontfamily="monospace")
    ax.set_ylabel("Sampling Probability", fontsize=11, fontweight="bold")
    ax.set_xlabel("Decoded Bitstring (Node Assignment Order)", fontsize=11, fontweight="bold")
    
    chart_title = title or f"QAOA Aer Sampling Distribution — {graph.name} (Top {len(bitstrings)} States)"
    ax.set_title(chart_title, fontsize=13, fontweight="bold", pad=15)
    
    max_prob = max(probabilities) if probabilities else 0.1
    ax.set_ylim(0, max_prob * 1.30)
    ax.grid(axis="y", linestyle="--", alpha=0.35)

    # Informational annotation box
    expected_cut = sum(c / total_shots * graph.compute_cut(bs).cut_value for bs, c in decoded_counts.items())
    opt_str = f"{classical_optimal_cut:.2f}" if classical_optimal_cut is not None else "N/A"
    approx_ratio_str = f"{expected_cut / classical_optimal_cut:.3f}" if classical_optimal_cut else "N/A"
    
    info_lines = [
        f"Total Shots: {total_shots}",
        f"Expected Cut <C>: {expected_cut:.2f}",
        f"Classical Optimum: {opt_str}",
        f"Approx Ratio (alpha): {approx_ratio_str}",
    ]
    if optimal_set:
        opt_shots = sum(count for bs, count in decoded_counts.items() if bs in optimal_set)
        info_lines.append(f"Optimal Probability: {opt_shots / total_shots * 100:.1f}%")

    info_box_text = "\n".join(info_lines)
    ax.text(
        0.98,
        0.95,
        info_box_text,
        transform=ax.transAxes,
        fontsize=9,
        verticalalignment="top",
        horizontalalignment="right",
        bbox=dict(boxstyle="round,pad=0.5", facecolor="#f8fafc", edgecolor="#cbd5e1", alpha=0.9),
    )

    # Custom legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor="#10b981", edgecolor="#1e293b", label=f"Optimal Cut (C = {opt_str})"),
        Patch(facecolor="#3b82f6", edgecolor="#1e293b", label="Sub-optimal Cut"),
    ]
    ax.legend(handles=legend_elements, loc="upper left", framealpha=0.9)

    plt.tight_layout()

    if save_path:
        out_p = Path(save_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_p, dpi=300, bbox_inches="tight")

    return fig
