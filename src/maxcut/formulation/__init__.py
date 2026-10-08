"""Layer 4: QUBO & Ising Formulation.

Transforms graph specifications into Ising spin Hamiltonians using Qiskit 2.x SparsePauliOp.
"""

from maxcut.formulation.qubo import (
    IsingFormulation,
    QUBOFormulation,
    QuantumCostHamiltonian,
    build_cost_hamiltonian,
    build_maxcut_ising,
    build_maxcut_qubo,
    evaluate_all_representations,
)

__all__ = [
    "QUBOFormulation",
    "IsingFormulation",
    "QuantumCostHamiltonian",
    "build_maxcut_qubo",
    "build_maxcut_ising",
    "build_cost_hamiltonian",
    "evaluate_all_representations",
]
