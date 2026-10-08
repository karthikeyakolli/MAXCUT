"""QAOA circuit and ansatz construction for Max-Cut.

Constructs parameterized QAOA circuits adhering to Qiskit 2.x standards.
Decouples circuit construction from parameter optimization.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Union

from qiskit.circuit import Parameter, QuantumCircuit

from maxcut.domain.model import MaxCutGraph


@dataclass(frozen=True)
class QAOAAnsatz:
    """Encapsulates a parameterized QAOA circuit and its parameter mappings."""

    circuit: QuantumCircuit
    p: int
    num_qubits: int
    gamma_parameters: List[Parameter]
    beta_parameters: List[Parameter]
    node_to_qubit: Dict[int, int]
    qubit_to_node: Dict[int, int]

    @property
    def num_parameters(self) -> int:
        """Total variational parameters = 2 * p (p gammas + p betas)."""
        return len(self.gamma_parameters) + len(self.beta_parameters)

    def bind(
        self,
        gamma_values: Sequence[float],
        beta_values: Sequence[float],
        with_measurements: bool = False,
    ) -> QuantumCircuit:
        """Binds numerical angles to gamma and beta parameters.

        Args:
            gamma_values: Sequence of length p.
            beta_values: Sequence of length p.
            with_measurements: If True, adds measurement operations to a new classical register.

        Returns:
            QuantumCircuit: Bound executable quantum circuit.
        """
        if len(gamma_values) != self.p:
            raise ValueError(f"Expected {self.p} gamma values, got {len(gamma_values)}.")
        if len(beta_values) != self.p:
            raise ValueError(f"Expected {self.p} beta values, got {len(beta_values)}.")

        param_dict = {}
        for param, val in zip(self.gamma_parameters, gamma_values):
            param_dict[param] = float(val)
        for param, val in zip(self.beta_parameters, beta_values):
            param_dict[param] = float(val)

        bound_circuit = self.circuit.assign_parameters(param_dict)

        if with_measurements:
            meas_circuit = bound_circuit.copy()
            meas_circuit.measure_all()
            return meas_circuit

        return bound_circuit

    def draw_ascii(self) -> str:
        """Returns ASCII text drawing of the circuit."""
        return self.circuit.draw(output="text").single_string()


def build_qaoa_circuit(
    graph: MaxCutGraph,
    p: int = 1,
    include_measurements: bool = False,
) -> QAOAAnsatz:
    """Constructs a parameterized QAOA circuit for Max-Cut on graph G.

    Circuit Architecture:
    1. Initialize: |+>^{\\otimes n} via Hadamard gate H on every qubit.
    2. For l = 0, ..., p - 1:
       a. Cost unitary U_C(gamma_l) = e^{-i gamma_l H_C}:
          For each edge (u, v) with weight w_{uv}:
          Apply RZZ(gamma_l * w_{uv}) between qubit(u) and qubit(v).
       b. Mixer unitary U_M(beta_l) = e^{-i beta_l H_M}:
          For each qubit u:
          Apply RX(2 * beta_l) on qubit(u).
    3. Optional: Measurements into classical register.

    Args:
        graph: MaxCutGraph domain instance.
        p: QAOA depth (number of alternating layers, p >= 1).
        include_measurements: Whether to append measurement gates.

    Returns:
        QAOAAnsatz: Parametric ansatz container.
    """
    if p < 1:
        raise ValueError(f"QAOA depth p must be >= 1, got {p}.")

    n = graph.num_nodes
    node_to_qubit = {node: i for i, node in enumerate(graph.nodes)}
    qubit_to_node = {i: node for i, node in enumerate(graph.nodes)}

    qc = QuantumCircuit(n, name=f"QAOA_MaxCut_p{p}")

    # Parameters: p gammas and p betas
    gamma_params = [Parameter(f"gamma_{l}") for l in range(p)]
    beta_params = [Parameter(f"beta_{l}") for l in range(p)]

    # 1. Initial State: |+>^{\otimes n}
    for q in range(n):
        qc.h(q)

    # 2. Alternating layers of U_C and U_M
    for l in range(p):
        gamma_l = gamma_params[l]
        beta_l = beta_params[l]

        # --- Cost Layer ---
        for edge in graph.edges:
            q_u = node_to_qubit[edge.u]
            q_v = node_to_qubit[edge.v]
            # RZZ(theta) implements exp(-i * theta/2 * Z_u Z_v)
            # We want exp(-i * gamma_l * (w_{uv} / 2) * Z_u Z_v) => theta = w_{uv} * gamma_l
            theta = edge.weight * gamma_l
            qc.rzz(theta, q_u, q_v)

        # --- Mixer Layer ---
        # RX(theta) implements exp(-i * theta/2 * X_u)
        # We want exp(-i * beta_l * X_u) => theta = 2 * beta_l
        for q in range(n):
            qc.rx(2.0 * beta_l, q)

    if include_measurements:
        qc.measure_all()

    return QAOAAnsatz(
        circuit=qc,
        p=p,
        num_qubits=n,
        gamma_parameters=gamma_params,
        beta_parameters=beta_params,
        node_to_qubit=node_to_qubit,
        qubit_to_node=qubit_to_node,
    )
