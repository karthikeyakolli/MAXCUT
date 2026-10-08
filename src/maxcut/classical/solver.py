"""Exact exhaustive classical reference solver for Max-Cut instances.

Provides certified ground-truth solutions for benchmark validation against QAOA.
Documents mathematical complexity and symmetry invariance.
"""

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
import time
from typing import Any, Dict, List, Optional, Tuple, Union

from maxcut.domain.model import Edge, MaxCutGraph, Partition


@dataclass(frozen=True)
class ClassicalMaxCutResult:
    """Certified exact reference result from classical exhaustive search.

    Contains exhaustive metrics and solution partition details needed for
    subsequent direct comparison with quantum QAOA executions.
    """

    graph_name: str
    num_nodes: int
    num_edges: int
    total_weight: float
    optimal_cut_value: float
    primary_bitstring: str
    primary_assignment: Dict[int, int]
    optimal_bitstrings: List[str]
    cut_edges: List[Tuple[int, int, float]]
    uncut_edges: List[Tuple[int, int, float]]
    num_cut_edges: int
    cut_ratio: float
    execution_time_seconds: float
    total_assignments_evaluated: int
    cut_value_distribution: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serializes result into a clean dictionary format."""
        return {
            "graph_name": self.graph_name,
            "num_nodes": self.num_nodes,
            "num_edges": self.num_edges,
            "total_weight": self.total_weight,
            "optimal_cut_value": self.optimal_cut_value,
            "primary_bitstring": self.primary_bitstring,
            "primary_assignment": self.primary_assignment,
            "optimal_bitstrings": self.optimal_bitstrings,
            "num_optimal_bitstrings": len(self.optimal_bitstrings),
            "num_cut_edges": self.num_cut_edges,
            "cut_ratio": self.cut_ratio,
            "execution_time_seconds": self.execution_time_seconds,
            "total_assignments_evaluated": self.total_assignments_evaluated,
            "cut_edges": self.cut_edges,
            "uncut_edges": self.uncut_edges,
            "cut_value_distribution": self.cut_value_distribution,
        }

    def to_json(self, path: Optional[Union[str, Path]] = None, indent: int = 2) -> str:
        """Serializes result to JSON string and optionally writes to disk."""
        data_str = json.dumps(self.to_dict(), indent=indent)
        if path is not None:
            out_file = Path(path)
            out_file.parent.mkdir(parents=True, exist_ok=True)
            with open(out_file, "w", encoding="utf-8") as f:
                f.write(data_str)
        return data_str

    def validate_solution(self, graph: MaxCutGraph) -> bool:
        """Validates that the primary solution re-evaluates to the optimal cut value."""
        recomputed = graph.compute_cut(self.primary_assignment)
        if abs(recomputed.cut_value - self.optimal_cut_value) > 1e-9:
            return False
        # Verify that all optimal bitstrings achieve this cut value
        for bitstring in self.optimal_bitstrings:
            res = graph.compute_cut(bitstring)
            if abs(res.cut_value - self.optimal_cut_value) > 1e-9:
                return False
        return True

    def summary(self) -> str:
        """Returns a clear, publication-grade solution summary."""
        symmetry_note = (
            f"Found {len(self.optimal_bitstrings)} optimal assignment(s). "
            f"Due to global Z2 spin-flip symmetry (C(x) = C(1-x)), optimal solutions occur in complementary pairs."
        )
        return (
            f"======================================================================\n"
            f"  Classical Reference Solver: {self.graph_name}\n"
            f"======================================================================\n"
            f"Graph Order (|V|): {self.num_nodes} | Graph Size (|E|): {self.num_edges}\n"
            f"Total Graph Weight: {self.total_weight:.4f}\n"
            f"Ground Truth Optimum (C_max): {self.optimal_cut_value:.4f}\n"
            f"Optimal Cut Ratio: {self.cut_ratio:.2%}\n"
            f"Primary Optimal Bitstring: '{self.primary_bitstring}'\n"
            f"All Optimal Bitstrings: {self.optimal_bitstrings}\n"
            f"Cut Edges: {self.num_cut_edges} cut / {len(self.uncut_edges)} uncut\n"
            f"Total Evaluated Assignments: {self.total_assignments_evaluated} (2^{self.num_nodes})\n"
            f"Wall-Clock Execution Time: {self.execution_time_seconds:.6f} seconds\n"
            f"Symmetry: {symmetry_note}\n"
            f"======================================================================"
        )


class ExactExhaustiveSolver:
    """Exact exhaustive search solver for Max-Cut instances.

    COMPUTATIONAL COMPLEXITY:
    -------------------------
    1. Time Complexity:
       - Search space: For an undirected graph G = (V, E) with n = |V| vertices,
         there are 2^n possible binary assignments x in {0, 1}^n.
       - Each assignment cut evaluation inspects m = |E| edges.
       - Worst-case time complexity: O(m * 2^n).
       - For n <= 20, 2^20 approx 1.05 * 10^6 configurations, well within practical
         classical memory and sub-second CPU limits.
    2. Space Complexity:
       - O(n + m) auxiliary space to track state, best partitions, and graph structure.
    3. Global Spin-Flip (Z2) Symmetry:
       - Every cut satisfies C(x) = C(1 - x) because (x_u XOR x_v) = ((1 - x_u) XOR (1 - x_v)).
       - Complementary solutions are explicitly preserved and returned, as quantum QAOA
         sampling naturally generates population on both symmetric ground-state branches.
    """

    def __init__(self, record_distribution: bool = True) -> None:
        self.record_distribution: bool = record_distribution

    def solve(self, graph: MaxCutGraph) -> ClassicalMaxCutResult:
        """Executes exhaustive search over all 2^n binary vertex assignments.

        Args:
            graph: The MaxCutGraph instance to solve.

        Returns:
            ClassicalMaxCutResult: Certified exact optimum and partition data.
        """
        n = graph.num_nodes
        nodes = graph.nodes
        edges = [(e.u, e.v, e.weight) for e in graph.edges]
        total_assignments = 1 << n  # 2^n

        start_time = time.perf_counter()

        max_cut_val: float = -float("inf")
        optimal_bitstrings: List[str] = []
        cut_distribution: Dict[str, int] = {}

        # Pre-map node IDs to index 0..n-1 for ultra-fast bit extraction
        node_to_idx = {node: i for i, node in enumerate(nodes)}
        indexed_edges = [(node_to_idx[u], node_to_idx[v], w) for u, v, w in edges]

        for int_assignment in range(total_assignments):
            # Compute cut for this integer configuration
            current_cut: float = 0.0
            for u_idx, v_idx, w in indexed_edges:
                bit_u = (int_assignment >> u_idx) & 1
                bit_v = (int_assignment >> v_idx) & 1
                if bit_u != bit_v:
                    current_cut += w

            # Record distribution if enabled
            if self.record_distribution:
                cut_key = f"{current_cut:.4f}"
                cut_distribution[cut_key] = cut_distribution.get(cut_key, 0) + 1

            # Check maximum
            if current_cut > max_cut_val:
                max_cut_val = current_cut
                # Format bitstring ordered by sorted nodes: node_0, node_1, ..., node_{n-1}
                bitstring = "".join(str((int_assignment >> i) & 1) for i in range(n))
                optimal_bitstrings = [bitstring]
            elif abs(current_cut - max_cut_val) < 1e-9:
                bitstring = "".join(str((int_assignment >> i) & 1) for i in range(n))
                optimal_bitstrings.append(bitstring)

        elapsed_time = time.perf_counter() - start_time

        # Pick primary bitstring
        primary_bitstring = optimal_bitstrings[0]
        primary_eval = graph.compute_cut(primary_bitstring)

        cut_edges_repr = [(e.u, e.v, e.weight) for e in primary_eval.cut_edges]
        uncut_edges_repr = [(e.u, e.v, e.weight) for e in primary_eval.uncut_edges]

        result = ClassicalMaxCutResult(
            graph_name=graph.name,
            num_nodes=n,
            num_edges=graph.num_edges,
            total_weight=graph.total_weight,
            optimal_cut_value=max_cut_val,
            primary_bitstring=primary_bitstring,
            primary_assignment=primary_eval.assignment,
            optimal_bitstrings=optimal_bitstrings,
            cut_edges=cut_edges_repr,
            uncut_edges=uncut_edges_repr,
            num_cut_edges=len(cut_edges_repr),
            cut_ratio=primary_eval.cut_ratio,
            execution_time_seconds=elapsed_time,
            total_assignments_evaluated=total_assignments,
            cut_value_distribution=cut_distribution,
        )

        return result
