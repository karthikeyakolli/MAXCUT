"""Mathematical formulation layer: QUBO, Ising, and Quantum Cost Hamiltonian.

Defines:
- Binary variable convention: x_u in {0, 1}
- Spin transformation convention: x_u = (1 - s_u) / 2 <=> s_u = 1 - 2*x_u in {+1, -1}
- Minimization mapping: f_QUBO(x) = E_Ising(s) = <x| H_C |x> = - C(x)
- Quantum operator: H_C = 0.5 * sum_{(u,v) in E} w_{uv} Z_u Z_v - (0.5 * sum w_{uv}) I
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

import numpy as np
from qiskit.quantum_info import SparsePauliOp, Statevector

from maxcut.domain.model import MaxCutGraph


@dataclass(frozen=True)
class QUBOFormulation:
    """Quadratic Unconstrained Binary Optimization (QUBO) representation.

    Minimization convention:
    f_QUBO(x) = x^T Q x + offset = - C(x)
    """

    matrix: np.ndarray
    num_variables: int
    offset: float = 0.0
    variable_names: List[int] = field(default_factory=list)

    def evaluate(self, assignment: Union[str, Sequence[int], Dict[int, int]]) -> float:
        """Evaluates QUBO objective value x^T Q x + offset for a given assignment.

        Args:
            assignment: Binary assignment (dict, bitstring, or sequence of ints).

        Returns:
            float: Evaluated QUBO cost (equals -C(x)).
        """
        x_vec = self._parse_assignment_vector(assignment)
        val = float(x_vec.T @ self.matrix @ x_vec) + self.offset
        return val

    def _parse_assignment_vector(
        self, assignment: Union[str, Sequence[int], Dict[int, int]]
    ) -> np.ndarray:
        if isinstance(assignment, dict):
            vec = np.zeros(self.num_variables, dtype=float)
            for i, var_name in enumerate(self.variable_names):
                vec[i] = float(assignment[var_name])
            return vec
        elif isinstance(assignment, str):
            if len(assignment) != self.num_variables:
                raise ValueError(
                    f"Bitstring length ({len(assignment)}) != variables ({self.num_variables})"
                )
            return np.array([float(b) for b in assignment], dtype=float)
        elif isinstance(assignment, (list, tuple, np.ndarray)):
            if len(assignment) != self.num_variables:
                raise ValueError(
                    f"Vector length ({len(assignment)}) != variables ({self.num_variables})"
                )
            return np.array([float(b) for b in assignment], dtype=float)
        else:
            raise TypeError(f"Unsupported assignment type: {type(assignment)}")


@dataclass(frozen=True)
class IsingFormulation:
    """Classical Ising spin Hamiltonian representation.

    Spin convention:
    s_u = 1 - 2*x_u in {+1, -1}
    s_u = +1 corresponds to x_u = 0 (|0> state)
    s_u = -1 corresponds to x_u = 1 (|1> state)

    Energy convention:
    E_Ising(s) = sum_{u < v} J_{uv} s_u s_v + sum_u h_u s_u + offset
               = - C(x)
    """

    quadratic_couplings: Dict[Tuple[int, int], float]
    linear_fields: Dict[int, float]
    offset: float
    num_spins: int
    spin_names: List[int]

    def evaluate(self, assignment: Union[str, Sequence[int], Dict[int, int]]) -> float:
        """Evaluates Ising energy for a given binary assignment or spin configuration."""
        if isinstance(assignment, dict):
            # Check if values are {0, 1} or {+1, -1}
            first_val = next(iter(assignment.values()))
            if first_val in (-1, 1) and len(set(assignment.values()) - {-1, 1}) == 0:
                spins = {k: int(v) for k, v in assignment.items()}
            else:
                spins = {k: 1 - 2 * int(v) for k, v in assignment.items()}
        elif isinstance(assignment, str):
            # String of '0' and '1'
            spins = {
                self.spin_names[i]: (1 - 2 * int(b))
                for i, b in enumerate(assignment)
            }
        elif isinstance(assignment, (list, tuple, np.ndarray)):
            spins = {
                self.spin_names[i]: (1 - 2 * int(b))
                for i, b in enumerate(assignment)
            }
        else:
            raise TypeError(f"Unsupported assignment type: {type(assignment)}")

        energy = self.offset
        for (u, v), j_val in self.quadratic_couplings.items():
            energy += j_val * spins[u] * spins[v]
        for u, h_val in self.linear_fields.items():
            energy += h_val * spins[u]

        return float(energy)


@dataclass(frozen=True)
class QuantumCostHamiltonian:
    """Quantum Cost Hamiltonian representation using Qiskit SparsePauliOp.

    Cost operator:
    H_C = H_core + offset * I
    where:
    H_core = 0.5 * sum_{(u, v) in E} w_{uv} Z_u Z_v
    offset = - 0.5 * sum_{(u, v) in E} w_{uv}
    """

    cost_operator: SparsePauliOp
    core_operator: SparsePauliOp
    offset: float
    num_qubits: int
    node_to_qubit: Dict[int, int]
    qubit_to_node: Dict[int, int]

    def evaluate_bitstring(self, bitstring: str) -> float:
        """Evaluates the eigenvalue <x| H_C |x> on computational basis state |x>.

        In Qiskit's little-endian convention:
        bitstring = 'b_{n-1} ... b_1 b_0'
        where character at index (len - 1 - k) corresponds to qubit k.
        """
        if len(bitstring) != self.num_qubits:
            raise ValueError(
                f"Bitstring length ({len(bitstring)}) != qubits ({self.num_qubits})"
            )
        sv = Statevector.from_label(bitstring)
        val = sv.expectation_value(self.cost_operator).real
        return float(val)

    def evaluate_assignment(self, assignment: Union[str, Sequence[int], Dict[int, int]]) -> float:
        """Evaluates <x| H_C |x> for an assignment mapped to canonical qubit order.

        Args:
            assignment: Binary assignment.

        Returns:
            float: Energy eigenvalue (equals -C(x)).
        """
        if isinstance(assignment, dict):
            # Qubit k has value assignment[qubit_to_node[k]]
            qubit_vals = [int(assignment[self.qubit_to_node[k]]) for k in range(self.num_qubits)]
        elif isinstance(assignment, (str, list, tuple)):
            if len(assignment) != self.num_qubits:
                raise ValueError(
                    f"Assignment length ({len(assignment)}) != qubits ({self.num_qubits})"
                )
            qubit_vals = [int(b) for b in assignment]
        else:
            raise TypeError(f"Unsupported assignment type: {type(assignment)}")

        # Build Qiskit label: Qiskit label is 'q_{n-1} ... q_1 q_0'
        label = "".join(str(qubit_vals[k]) for k in reversed(range(self.num_qubits)))
        return self.evaluate_bitstring(label)


def build_maxcut_qubo(graph: MaxCutGraph) -> QUBOFormulation:
    """Constructs the QUBO minimization matrix Q such that x^T Q x = - C(x).

    Derivation:
    C(x) = sum_{(u, v) in E} w_{uv} (x_u + x_v - 2 x_u x_v)
    f_QUBO(x) = - C(x) = sum_{(u, v) in E} w_{uv} (2 x_u x_v - x_u - x_v)
    Using x_u^2 = x_u for binary variables:
    - Diagonal terms: Q_{uu} = - sum_{v in N(u)} w_{uv} = - weighted_degree(u)
    - Off-diagonal terms (symmetric): Q_{uv} = Q_{vu} = w_{uv} for (u, v) in E
    Then x^T Q x = sum_u Q_{uu} x_u + 2 * sum_{u < v} Q_{uv} x_u x_v = - C(x).
    """
    n = graph.num_nodes
    node_to_idx = {node: i for i, node in enumerate(graph.nodes)}
    q_mat = np.zeros((n, n), dtype=float)

    for edge in graph.edges:
        u_idx = node_to_idx[edge.u]
        v_idx = node_to_idx[edge.v]
        w = edge.weight

        # Linear penalties on diagonal: -w on u and -w on v
        q_mat[u_idx, u_idx] -= w
        q_mat[v_idx, v_idx] -= w

        # Quadratic coupling (symmetric): w on (u, v) and (v, u)
        q_mat[u_idx, v_idx] += w
        q_mat[v_idx, u_idx] += w

    return QUBOFormulation(
        matrix=q_mat,
        num_variables=n,
        offset=0.0,
        variable_names=graph.nodes,
    )


def build_maxcut_ising(graph: MaxCutGraph) -> IsingFormulation:
    """Converts the Max-Cut problem into a classical Ising Hamiltonian.

    Derivation:
    Binary to spin: x_u = (1 - s_u) / 2 with s_u in {+1, -1}
    x_u XOR x_v = (1 - s_u s_v) / 2
    C(s) = sum_{(u, v) in E} w_{uv} (1 - s_u s_v) / 2
         = 0.5 * W - 0.5 * sum_{(u, v) in E} w_{uv} s_u s_v
    E_Ising(s) = - C(s) = 0.5 * sum_{(u, v) in E} w_{uv} s_u s_v - 0.5 * W
    where W = sum_{(u, v) in E} w_{uv} is the total edge weight.

    Couplings:
    J_{uv} = 0.5 * w_{uv}
    h_u = 0.0
    offset = - 0.5 * W
    """
    couplings: Dict[Tuple[int, int], float] = {}
    linear_fields: Dict[int, float] = {node: 0.0 for node in graph.nodes}
    total_w = graph.total_weight

    for edge in graph.edges:
        key = (edge.u, edge.v) if edge.u < edge.v else (edge.v, edge.u)
        couplings[key] = 0.5 * edge.weight

    offset = -0.5 * total_w

    return IsingFormulation(
        quadratic_couplings=couplings,
        linear_fields=linear_fields,
        offset=offset,
        num_spins=graph.num_nodes,
        spin_names=graph.nodes,
    )


def build_cost_hamiltonian(
    graph: MaxCutGraph, include_offset: bool = True
) -> QuantumCostHamiltonian:
    """Builds the Qiskit SparsePauliOp Cost Hamiltonian from the Max-Cut graph.

    Operator mapping:
    s_u -> Z_u (where Z |0> = +1, Z |1> = -1)
    H_core = 0.5 * sum_{(u, v) in E} w_{uv} Z_u Z_v
    offset = - 0.5 * sum_{(u, v) in E} w_{uv}
    H_C = H_core + offset * I (if include_offset is True)
    """
    n = graph.num_nodes
    node_to_qubit = {node: i for i, node in enumerate(graph.nodes)}
    qubit_to_node = {i: node for i, node in enumerate(graph.nodes)}

    sparse_terms: List[Tuple[str, List[int], complex]] = []

    for edge in graph.edges:
        q_u = node_to_qubit[edge.u]
        q_v = node_to_qubit[edge.v]
        coeff = 0.5 * edge.weight
        sparse_terms.append(("ZZ", [q_u, q_v], coeff))

    core_op = SparsePauliOp.from_sparse_list(sparse_terms, num_qubits=n).simplify()

    offset = -0.5 * graph.total_weight

    if include_offset:
        identity_term = [("", [], complex(offset))]
        id_op = SparsePauliOp.from_sparse_list(identity_term, num_qubits=n).simplify()
        full_op = (core_op + id_op).simplify()
    else:
        full_op = core_op

    return QuantumCostHamiltonian(
        cost_operator=full_op,
        core_operator=core_op,
        offset=offset,
        num_qubits=n,
        node_to_qubit=node_to_qubit,
        qubit_to_node=qubit_to_node,
    )


def evaluate_all_representations(
    graph: MaxCutGraph, assignment: Union[str, Sequence[int], Dict[int, int]]
) -> Dict[str, Any]:
    """Evaluates classical cut, QUBO, Ising, and Quantum Cost Hamiltonian simultaneously.

    Verifies mathematical consistency across all representations:
    classical_cut == - qubo_cost == - ising_cost == - quantum_energy

    Returns:
        Dict[str, Any]: Values and consistency check.
    """
    cut_res = graph.compute_cut(assignment)
    classical_cut = cut_res.cut_value

    qubo = build_maxcut_qubo(graph)
    qubo_cost = qubo.evaluate(assignment)

    ising = build_maxcut_ising(graph)
    ising_cost = ising.evaluate(assignment)

    hamiltonian = build_cost_hamiltonian(graph, include_offset=True)
    quantum_energy = hamiltonian.evaluate_assignment(assignment)

    is_consistent = (
        abs(classical_cut - (-qubo_cost)) < 1e-9
        and abs(classical_cut - (-ising_cost)) < 1e-9
        and abs(classical_cut - (-quantum_energy)) < 1e-9
    )

    return {
        "assignment_bitstring": cut_res.bitstring,
        "classical_cut": classical_cut,
        "qubo_cost": qubo_cost,
        "ising_cost": ising_cost,
        "quantum_energy": quantum_energy,
        "expected_minimization_cost": -classical_cut,
        "is_consistent": is_consistent,
    }
