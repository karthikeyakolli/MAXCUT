"""Measurement decoding and statistical evaluation of sampled Max-Cut bitstrings.

Handles Qiskit little-endian measurement convention and translates outcomes
to canonical node-ordered bitstrings.
"""

from typing import Any, Dict, List, Optional

from maxcut.domain.model import MaxCutGraph


def decode_qiskit_counts(
    raw_counts: Dict[str, int],
    node_to_qubit: Dict[int, int],
    sorted_nodes: List[int],
) -> Dict[str, int]:
    """Translates Qiskit little-endian measurement counts to canonical node-ordered counts.

    In Qiskit, a measurement bitstring is formatted as 'c_{n-1} ... c_1 c_0', where:
    - Character at index (n - 1 - k) corresponds to qubit k.
    - We map each node u to its measured value via bitstring[n - 1 - node_to_qubit[u]].
    - The output bitstring is ordered by sorted_nodes: 'b_{node_0} b_{node_1} ... b_{node_{n-1}}'.

    Args:
        raw_counts: Counts dictionary from Qiskit measurement {'01...': count}.
        node_to_qubit: Mapping from graph node ID to circuit qubit index.
        sorted_nodes: List of graph node IDs in canonical sorted order.

    Returns:
        Dict[str, int]: Decoded counts keyed by canonical node-ordered bitstrings.
    """
    n = len(sorted_nodes)
    decoded_counts: Dict[str, int] = {}

    for raw_bitstring, count in raw_counts.items():
        # Remove any whitespace (e.g. from multiple classical registers)
        clean_raw = str(raw_bitstring).replace(" ", "")
        if len(clean_raw) != n:
            raise ValueError(
                f"Raw bitstring length ({len(clean_raw)}) does not match node count ({n})."
            )

        # Extract bit for each node in sorted order
        node_bits = []
        for node in sorted_nodes:
            qubit_idx = node_to_qubit[node]
            # In Qiskit little-endian, qubit_idx is at index (n - 1 - qubit_idx)
            char = clean_raw[n - 1 - qubit_idx]
            node_bits.append(char)

        canonical_bitstring = "".join(node_bits)
        decoded_counts[canonical_bitstring] = (
            decoded_counts.get(canonical_bitstring, 0) + int(count)
        )

    return decoded_counts


def decode_reduced_qiskit_counts(
    raw_counts: Dict[str, int],
    node_to_qubit: Dict[int, int],
    all_sorted_nodes: List[int],
    fixed_node: int = 0,
    fixed_val: int = 0,
) -> Dict[str, int]:
    """Translates reduced Qiskit measurement counts into full canonical node-ordered counts.

    For an (n-1)-qubit circuit where node `fixed_node` is fixed to `fixed_val` (0),
    this extracts measured bits for active nodes and inserts `fixed_val` at `fixed_node`.

    Args:
        raw_counts: Counts dictionary from Qiskit measurement {'01...': count}.
        node_to_qubit: Mapping from active graph node ID to circuit qubit index.
        all_sorted_nodes: Full list of all n graph node IDs in canonical sorted order.
        fixed_node: Node ID that was fixed during symmetry reduction (default 0).
        fixed_val: Fixed binary assignment (default 0).

    Returns:
        Dict[str, int]: Decoded counts keyed by full n-variable bitstrings.
    """
    n_red = len(node_to_qubit)
    decoded_counts: Dict[str, int] = {}

    for raw_bitstring, count in raw_counts.items():
        clean_raw = str(raw_bitstring).replace(" ", "")
        if len(clean_raw) != n_red:
            raise ValueError(
                f"Raw bitstring length ({len(clean_raw)}) does not match active qubit count ({n_red})."
            )

        node_bits = []
        for node in all_sorted_nodes:
            if node == fixed_node:
                node_bits.append(str(fixed_val))
            else:
                qubit_idx = node_to_qubit[node]
                # In Qiskit little-endian:
                char = clean_raw[n_red - 1 - qubit_idx]
                node_bits.append(char)

        full_bitstring = "".join(node_bits)
        decoded_counts[full_bitstring] = (
            decoded_counts.get(full_bitstring, 0) + int(count)
        )

    return decoded_counts


def evaluate_measurement_distribution(
    decoded_counts: Dict[str, int],
    graph: MaxCutGraph,
    optimal_cut_value: Optional[float] = None,
    optimal_bitstrings: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Computes cut statistics, expectation value, and ground-state success probability.

    Args:
        decoded_counts: Canonical node-ordered counts.
        graph: MaxCutGraph domain instance.
        optimal_cut_value: Optional exact ground truth C_max.
        optimal_bitstrings: Optional list of certified optimal bitstrings.

    Returns:
        Dict[str, Any]: Comprehensive sampling statistics.
    """
    total_shots = sum(decoded_counts.values())
    if total_shots <= 0:
        raise ValueError("Total shots must be greater than 0.")

    expected_cut = 0.0
    best_cut = -float("inf")
    best_bitstring = ""
    most_frequent_bitstring = ""
    max_count = -1

    cut_values_by_string: Dict[str, float] = {}
    optimal_shots = 0
    optimal_set = set(optimal_bitstrings) if optimal_bitstrings else set()

    for bitstring, count in decoded_counts.items():
        cut_res = graph.compute_cut(bitstring)
        cut_val = cut_res.cut_value
        cut_values_by_string[bitstring] = cut_val

        prob = count / total_shots
        expected_cut += prob * cut_val

        if cut_val > best_cut:
            best_cut = cut_val
            best_bitstring = bitstring

        if count > max_count:
            max_count = count
            most_frequent_bitstring = bitstring

        if bitstring in optimal_set:
            optimal_shots += count

    approx_ratio = (
        (expected_cut / optimal_cut_value) if optimal_cut_value and optimal_cut_value > 0 else None
    )
    success_prob = (optimal_shots / total_shots) if optimal_bitstrings else None

    return {
        "total_shots": total_shots,
        "expected_cut_value": expected_cut,
        "best_sampled_cut": best_cut,
        "best_sampled_bitstring": best_bitstring,
        "most_frequent_bitstring": most_frequent_bitstring,
        "approximation_ratio": approx_ratio,
        "ground_state_success_probability": success_prob,
        "num_unique_bitstrings": len(decoded_counts),
        "cut_values_by_bitstring": cut_values_by_string,
    }
