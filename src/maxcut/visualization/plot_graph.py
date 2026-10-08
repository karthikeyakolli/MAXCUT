"""Visualization helpers for Max-Cut graphs and partition cuts."""

from pathlib import Path
from typing import Dict, Optional, Union

import matplotlib.pyplot as plt
import networkx as nx

from maxcut.domain.model import CutResult, MaxCutGraph, Partition


def plot_maxcut_graph(
    graph: MaxCutGraph,
    partition: Optional[Union[Partition, CutResult, Dict[int, int], str]] = None,
    title: Optional[str] = None,
    save_path: Optional[Union[str, Path]] = None,
    ax: Optional[plt.Axes] = None,
    seed: int = 42,
) -> plt.Figure:
    """Renders a MaxCutGraph with optional partition cut highlighting.

    Args:
        graph: MaxCutGraph domain instance.
        partition: Optional Partition, CutResult, assignment dict, or bitstring.
        title: Plot title.
        save_path: Optional path to save image (PNG/PDF).
        ax: Existing Matplotlib Axes to draw on.
        seed: Deterministic layout seed.

    Returns:
        plt.Figure: The Matplotlib Figure object.
    """
    nx_g = graph.to_networkx()
    pos = nx.spring_layout(nx_g, seed=seed)

    created_fig = False
    if ax is None:
        fig, ax = plt.subplots(figsize=(7, 6), dpi=120)
        created_fig = True
    else:
        fig = ax.get_figure()

    # Determine partition assignment if provided
    cut_res: Optional[CutResult] = None
    if partition is not None:
        if isinstance(partition, CutResult):
            cut_res = partition
        elif isinstance(partition, Partition):
            cut_res = graph.compute_cut(partition.to_assignment_dict())
        else:
            cut_res = graph.compute_cut(partition)

    # Node coloring
    if cut_res is not None:
        node_colors = [
            "#FF7043" if node in cut_res.partition.set_s else "#29B6F6"
            for node in graph.nodes
        ]
    else:
        node_colors = ["#ECEFF1" for _ in graph.nodes]

    # Draw nodes
    nx.draw_networkx_nodes(
        nx_g,
        pos,
        ax=ax,
        node_color=node_colors,
        node_size=650,
        edgecolors="#263238",
        linewidths=1.8,
    )

    # Draw node labels
    nx.draw_networkx_labels(
        nx_g,
        pos,
        ax=ax,
        font_size=11,
        font_weight="bold",
        font_color="#212121",
    )

    # Draw edges
    if cut_res is not None:
        cut_edge_tuples = [e.endpoints() for e in cut_res.cut_edges]
        uncut_edge_tuples = [e.endpoints() for e in cut_res.uncut_edges]

        # Draw uncut edges (solid gray)
        if uncut_edge_tuples:
            nx.draw_networkx_edges(
                nx_g,
                pos,
                ax=ax,
                edgelist=uncut_edge_tuples,
                edge_color="#B0BEC5",
                width=1.5,
                style="solid",
                alpha=0.7,
            )

        # Draw cut edges (dashed crimson)
        if cut_edge_tuples:
            nx.draw_networkx_edges(
                nx_g,
                pos,
                ax=ax,
                edgelist=cut_edge_tuples,
                edge_color="#E53935",
                width=2.5,
                style="dashed",
                alpha=0.9,
            )
    else:
        # Neutral edges
        nx.draw_networkx_edges(
            nx_g,
            pos,
            ax=ax,
            edge_color="#78909C",
            width=1.8,
            style="solid",
        )

    # Edge weight labels if weighted or when requested
    if graph.is_weighted:
        edge_labels = {
            (e.u, e.v): f"{e.weight:g}"
            for e in graph.edges
        }
        nx.draw_networkx_edge_labels(
            nx_g,
            pos,
            edge_labels=edge_labels,
            font_size=9,
            font_color="#37474F",
            ax=ax,
        )

    # Title & decorations
    if title is None:
        if cut_res is not None:
            title = f"{graph.name} — Cut Value: {cut_res.cut_value:g} (Cut Edges: {cut_res.num_cut_edges}/{graph.num_edges})"
        else:
            title = f"{graph.name} (|V|={graph.num_nodes}, |E|={graph.num_edges})"

    ax.set_title(title, fontsize=12, fontweight="bold", pad=12)
    ax.axis("off")

    if save_path is not None:
        out_path = Path(save_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_path, bbox_inches="tight")

    return fig
