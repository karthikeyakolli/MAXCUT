"""Unit tests for mathematical formulation: QUBO, Ising, and Quantum Cost Hamiltonian."""

import unittest

from qiskit.quantum_info import Statevector

from maxcut.classical import ExactExhaustiveSolver
from maxcut.domain import MaxCutGraph
from maxcut.formulation import (
    IsingFormulation,
    QUBOFormulation,
    QuantumCostHamiltonian,
    build_cost_hamiltonian,
    build_maxcut_ising,
    build_maxcut_qubo,
    evaluate_all_representations,
)


class TestMathematicalFormulation(unittest.TestCase):
    """Test suite verifying mathematical equivalence across classical, QUBO, Ising, and quantum operators."""

    def test_exhaustive_equivalence_tiny_triangle(self):
        """Verify for every assignment in K_3 that classical cut == -QUBO == -Ising == -Quantum energy."""
        # 3-node unweighted triangle: 8 total assignments
        graph = MaxCutGraph.from_edges([(0, 1), (1, 2), (2, 0)], name="K3_Triangle")
        qubo = build_maxcut_qubo(graph)
        ising = build_maxcut_ising(graph)
        hamiltonian = build_cost_hamiltonian(graph, include_offset=True)

        for i in range(1 << graph.num_nodes):  # 0 to 7
            bitstring = f"{i:03b}"
            cut_res = graph.compute_cut(bitstring)
            c_val = cut_res.cut_value

            q_val = qubo.evaluate(bitstring)
            is_val = ising.evaluate(bitstring)
            h_val = hamiltonian.evaluate_assignment(bitstring)

            # Strict mathematical assertions
            self.assertAlmostEqual(
                c_val,
                -q_val,
                places=9,
                msg=f"QUBO mismatch on bitstring {bitstring}: C={c_val}, QUBO={q_val}",
            )
            self.assertAlmostEqual(
                c_val,
                -is_val,
                places=9,
                msg=f"Ising mismatch on bitstring {bitstring}: C={c_val}, Ising={is_val}",
            )
            self.assertAlmostEqual(
                c_val,
                -h_val,
                places=9,
                msg=f"Quantum Hamiltonian mismatch on {bitstring}: C={c_val}, H_C={h_val}",
            )

    def test_exhaustive_equivalence_weighted_4cycle(self):
        """Verify for all 16 assignments in a weighted 4-cycle that all representations agree."""
        edges = [
            (0, 1, 2.5),
            (1, 2, 1.2),
            (2, 3, 3.4),
            (3, 0, 4.1),
        ]
        graph = MaxCutGraph.from_edges(edges, name="Weighted_C4")

        for i in range(1 << graph.num_nodes):
            bitstring = f"{i:04b}"
            eval_dict = evaluate_all_representations(graph, bitstring)
            self.assertTrue(
                eval_dict["is_consistent"],
                f"Inconsistency detected on assignment {bitstring}: {eval_dict}",
            )
            self.assertAlmostEqual(
                eval_dict["classical_cut"],
                -eval_dict["qubo_cost"],
                places=9,
            )
            self.assertAlmostEqual(
                eval_dict["classical_cut"],
                -eval_dict["ising_cost"],
                places=9,
            )
            self.assertAlmostEqual(
                eval_dict["classical_cut"],
                -eval_dict["quantum_energy"],
                places=9,
            )

    def test_ground_state_energy_matches_classical_optimum(self):
        """Verify that minimum eigenvalue of H_C equals -C_max from the classical solver."""
        edges = [(0, 1, 2.0), (1, 2, 3.0), (2, 3, 1.0), (3, 0, 5.0), (0, 2, 4.0)]
        graph = MaxCutGraph.from_edges(edges, name="Pentagon_Diagonal")

        # 1. Classical exact solver
        classical_solver = ExactExhaustiveSolver()
        classical_result = classical_solver.solve(graph)
        c_max = classical_result.optimal_cut_value

        # 2. Quantum Cost Hamiltonian
        hamiltonian = build_cost_hamiltonian(graph, include_offset=True)

        # Compute ground state energy by evaluating all basis states
        min_quantum_energy = float("inf")
        for i in range(1 << graph.num_nodes):
            bitstring = f"{i:04b}"
            energy = hamiltonian.evaluate_assignment(bitstring)
            if energy < min_quantum_energy:
                min_quantum_energy = energy

        self.assertAlmostEqual(
            min_quantum_energy,
            -c_max,
            places=9,
            msg=f"Ground state energy ({min_quantum_energy}) does not equal -C_max ({-c_max})",
        )

    def test_qubit_indexing_and_endianness_asymmetry(self):
        """Verify that asymmetric weights correctly differentiate qubit 0 vs qubit n-1 (no endianness inversion)."""
        # Linear path 0 - 1 - 2
        # Edge (0, 1) has weight 10.0
        # Edge (1, 2) has weight 1.0
        edges = [(0, 1, 10.0), (1, 2, 1.0)]
        graph = MaxCutGraph.from_edges(edges, name="AsymmetricPath")
        hamiltonian = build_cost_hamiltonian(graph, include_offset=True)

        # Assignment A: node 0 is 1, nodes 1 and 2 are 0 -> cut = 10.0 (edge 0-1 cut, edge 1-2 uncut)
        # Expected energy: -10.0
        res_a = graph.compute_cut("100")
        self.assertEqual(res_a.cut_value, 10.0)
        energy_a = hamiltonian.evaluate_assignment("100")
        self.assertAlmostEqual(energy_a, -10.0, places=9)

        # Assignment B: node 2 is 1, nodes 0 and 1 are 0 -> cut = 1.0 (edge 0-1 uncut, edge 1-2 cut)
        # Expected energy: -1.0
        res_b = graph.compute_cut("001")
        self.assertEqual(res_b.cut_value, 1.0)
        energy_b = hamiltonian.evaluate_assignment("001")
        self.assertAlmostEqual(energy_b, -1.0, places=9)

        # Direct verification with Qiskit Statevector label:
        # In Qiskit, label 'q2 q1 q0':
        # For Assignment A (q0=1, q1=0, q2=0): Qiskit label is '001'
        sv_a = Statevector.from_label("001")
        self.assertAlmostEqual(sv_a.expectation_value(hamiltonian.cost_operator).real, -10.0, places=9)

        # For Assignment B (q0=0, q1=0, q2=1): Qiskit label is '100'
        sv_b = Statevector.from_label("100")
        self.assertAlmostEqual(sv_b.expectation_value(hamiltonian.cost_operator).real, -1.0, places=9)

    def test_core_hamiltonian_and_offset(self):
        """Verify that H_C = H_core + offset * I."""
        edges = [(0, 1, 3.0), (1, 2, 4.0)]
        graph = MaxCutGraph.from_edges(edges, name="OffsetTest")

        hamiltonian = build_cost_hamiltonian(graph, include_offset=True)
        hamiltonian_no_offset = build_cost_hamiltonian(graph, include_offset=False)

        expected_offset = -0.5 * (3.0 + 4.0)  # -3.5
        self.assertEqual(hamiltonian.offset, expected_offset)

        # Difference between full and core operator must be constant offset
        for i in range(1 << 3):
            bs = f"{i:03b}"
            e_full = hamiltonian.evaluate_assignment(bs)
            e_core = hamiltonian_no_offset.evaluate_assignment(bs)
            self.assertAlmostEqual(e_full - e_core, expected_offset, places=9)


if __name__ == "__main__":
    unittest.main()
