"""End-to-end QAOA execution pipeline using Qiskit Aer simulator.

Orchestrates:
Problem Instance -> Formulation -> QAOA Ansatz -> Parameter Optimization ->
Aer Simulation -> Measurement Decoding -> Cut Evaluation -> Classical Benchmark Comparison.
"""

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
import time
from typing import Any, Dict, List, Optional, Sequence, Union

from maxcut.backends.aer_backend import AerBackendRunner
from maxcut.classical.solver import ClassicalMaxCutResult
from maxcut.domain.model import MaxCutGraph
from maxcut.formulation.qubo import build_cost_hamiltonian
from maxcut.qaoa.ansatz import build_qaoa_circuit
from maxcut.qaoa.decoding import decode_qiskit_counts, evaluate_measurement_distribution
from maxcut.qaoa.optimizer import QAOAOptimizationResult, QAOAOptimizer


@dataclass(frozen=True)
class QAOAAerExperimentResult:
    """Encapsulates all results, artifacts, and parameters of an end-to-end QAOA Aer run."""

    # Instance & Experiment Metadata
    problem_name: str
    num_nodes: int
    num_edges: int
    depth_p: int
    shots: int
    seeds: Dict[str, int]

    # Classical Parameter Optimization Details
    optimizer_name: str
    initial_parameters: List[float]
    optimal_parameters: List[float]
    optimal_gamma: List[float]
    optimal_beta: List[float]
    optimizer_evaluations: int
    final_objective_value: float  # Energy E = - <C>
    final_expected_cut_from_opt: float

    # Raw & Decoded Measurements
    raw_counts: Dict[str, int]
    decoded_counts: Dict[str, int]
    total_shots_sampled: int

    # Quality Metrics
    best_measured_bitstring: str
    best_measured_cut: float
    most_frequent_bitstring: str
    most_frequent_cut: float
    expected_cut_sampled: float

    # Classical Ground Truth Comparison
    classical_optimal_cut: Optional[float]
    classical_optimal_bitstrings: Optional[List[str]]
    approximation_ratio: Optional[float]  # expected_cut / classical_optimum
    best_solution_ratio: Optional[float]   # best_measured_cut / classical_optimum
    ground_state_success_probability: Optional[float]

    # Compilation & Circuit Metrics
    transpiled_depth: int
    transpiled_2q_gates: int
    transpiled_total_gates: int
    transpilation_level: int

    # Timing
    optimization_time_seconds: float
    simulation_time_seconds: float
    total_pipeline_time_seconds: float

    # Solution verification
    is_classical_optimum_achieved: bool

    def to_dict(self) -> Dict[str, Any]:
        """Converts result object to a serializable dictionary."""
        return asdict(self)

    def to_json(self, file_path: Union[str, Path], indent: int = 2) -> None:
        """Serializes result to a JSON file."""
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=indent)

    def summary(self) -> str:
        """Produces a comprehensive human-readable summary of the experiment."""
        gamma_str = ", ".join(f"{g:.4f}" for g in self.optimal_gamma)
        beta_str = ", ".join(f"{b:.4f}" for b in self.optimal_beta)
        
        ref_cut_str = f"{self.classical_optimal_cut:.4f}" if self.classical_optimal_cut is not None else "N/A"
        approx_str = f"{self.approximation_ratio:.4f} ({self.approximation_ratio * 100:.2f}%)" if self.approximation_ratio is not None else "N/A"
        best_ratio_str = f"{self.best_solution_ratio:.4f}" if self.best_solution_ratio is not None else "N/A"
        succ_str = f"{self.ground_state_success_probability:.4f} ({self.ground_state_success_probability * 100:.2f}%)" if self.ground_state_success_probability is not None else "N/A"
        opt_achieved_str = "YES (Optimal cut found in sampled distribution)" if self.is_classical_optimum_achieved else "NO"

        return (
            "======================================================================\n"
            f"  End-to-End QAOA Aer Simulation: {self.problem_name}\n"
            "======================================================================\n"
            f"Graph Order (|V|): {self.num_nodes} qubits | Graph Size (|E|): {self.num_edges} edges\n"
            f"QAOA Depth (p): {self.depth_p} | Measurement Shots: {self.shots}\n"
            f"Random Seeds: {json.dumps(self.seeds)}\n"
            "----------------------------------------------------------------------\n"
            "VARIATIONAL PARAMETER OPTIMIZATION:\n"
            f"  Optimizer: {self.optimizer_name}\n"
            f"  Evaluations: {self.optimizer_evaluations}\n"
            f"  Optimization Time: {self.optimization_time_seconds:.4f} s\n"
            f"  Final Energy (Minimization Objective): {self.final_objective_value:.4f}\n"
            f"  Optimal Gamma: [{gamma_str}]\n"
            f"  Optimal Beta:  [{beta_str}]\n"
            "----------------------------------------------------------------------\n"
            "AER SIMULATION & TRANSPILATION:\n"
            f"  Transpilation Level: {self.transpilation_level}\n"
            f"  Transpiled Circuit Depth: {self.transpiled_depth}\n"
            f"  2-Qubit Entangling Gates: {self.transpiled_2q_gates}\n"
            f"  Total Transpiled Gates: {self.transpiled_total_gates}\n"
            f"  Simulation Time: {self.simulation_time_seconds:.4f} s\n"
            "----------------------------------------------------------------------\n"
            "MEASUREMENT & SAMPLING RESULTS:\n"
            f"  Best Measured Bitstring: '{self.best_measured_bitstring}' (Cut: {self.best_measured_cut:.4f})\n"
            f"  Most Frequent Bitstring: '{self.most_frequent_bitstring}' (Cut: {self.most_frequent_cut:.4f})\n"
            f"  Expected Cut <C> (Sampled): {self.expected_cut_sampled:.4f}\n"
            "----------------------------------------------------------------------\n"
            "BENCHMARK COMPARISON AGAINST CLASSICAL GROUND TRUTH:\n"
            f"  Classical Optimum (C_max): {ref_cut_str}\n"
            f"  Approximation Ratio (alpha = <C> / C_max): {approx_str}\n"
            f"  Best Sampled Cut Ratio (C_best / C_max): {best_ratio_str}\n"
            f"  Ground State Success Probability P(C_max): {succ_str}\n"
            f"  Optimal Cut Achieved in Simulation: {opt_achieved_str}\n"
            "----------------------------------------------------------------------\n"
            "NOTE ON BENCHMARKING:\n"
            "  This experiment utilizes ideal shot-based simulation on Qiskit Aer as\n"
            "  an algorithmic baseline. No quantum advantage or hardware superiority is\n"
            "  claimed. This baseline anchors upcoming compilation onto Processors A & B.\n"
            "======================================================================"
        )


class QAOAAerExperiment:
    """Executes a fully reproducible end-to-end QAOA workflow on Qiskit Aer."""

    def __init__(
        self,
        seed_global: int = 42,
        seed_simulator: int = 42,
        seed_transpiler: int = 42,
    ) -> None:
        self.seed_global: int = seed_global
        self.seed_simulator: int = seed_simulator
        self.seed_transpiler: int = seed_transpiler

    def run(
        self,
        graph: MaxCutGraph,
        depth_p: int = 1,
        shots: int = 2048,
        optimizer_name: str = "COBYLA",
        maxiter: int = 100,
        tol: float = 1e-4,
        initial_point: Optional[Sequence[float]] = None,
        transpilation_level: int = 1,
        classical_reference: Optional[Union[Path, str, ClassicalMaxCutResult]] = None,
    ) -> QAOAAerExperimentResult:
        """Executes the complete QAOA pipeline on Qiskit Aer.

        Args:
            graph: MaxCutGraph problem instance.
            depth_p: QAOA depth p (reps).
            shots: Measurement shots on simulator.
            optimizer_name: Classical optimizer method ('COBYLA', 'SLSQP', etc.).
            maxiter: Maximum iterations for classical parameter optimizer.
            tol: Convergence tolerance for optimizer.
            initial_point: Optional initial variational parameters.
            transpilation_level: Preset pass manager optimization level (0-3).
            classical_reference: Optional ClassicalMaxCutResult or path to JSON file.

        Returns:
            QAOAAerExperimentResult: Complete verified experiment outcome.
        """
        pipeline_start = time.perf_counter()

        # 1. Parse classical reference if provided
        classical_opt_cut: Optional[float] = None
        classical_opt_strings: Optional[List[str]] = None

        if isinstance(classical_reference, ClassicalMaxCutResult):
            classical_opt_cut = classical_reference.optimal_cut_value
            classical_opt_strings = classical_reference.optimal_bitstrings
        elif isinstance(classical_reference, (str, Path)):
            ref_path = Path(classical_reference)
            if ref_path.exists():
                with open(ref_path, "r", encoding="utf-8") as f:
                    ref_data = json.load(f)
                classical_opt_cut = float(ref_data.get("optimal_cut_value", 0.0))
                classical_opt_strings = list(ref_data.get("optimal_bitstrings", []))

        # 2. Optimize variational parameters
        opt_start = time.perf_counter()
        optimizer = QAOAOptimizer(
            method=optimizer_name,
            maxiter=maxiter,
            tol=tol,
            seed=self.seed_global,
        )
        opt_result: QAOAOptimizationResult = optimizer.optimize(
            graph=graph,
            p=depth_p,
            initial_point=initial_point,
        )
        opt_time = time.perf_counter() - opt_start

        # 3. Build bound QAOA circuit with measurements
        ansatz = build_qaoa_circuit(graph, p=depth_p, include_measurements=True)
        bound_circuit = ansatz.bind(
            gamma_values=opt_result.optimal_gamma,
            beta_values=opt_result.optimal_beta,
        )

        # 4. Transpile and simulate on Qiskit Aer
        sim_start = time.perf_counter()
        runner = AerBackendRunner(
            seed_simulator=self.seed_simulator,
            seed_transpiler=self.seed_transpiler,
        )
        exec_result = runner.run_circuit(
            circuit=bound_circuit,
            shots=shots,
            optimization_level=transpilation_level,
        )
        sim_time = time.perf_counter() - sim_start

        # 5. Decode measurement counts from Qiskit little-endian
        node_to_qubit = ansatz.node_to_qubit
        sorted_nodes = sorted(graph.nodes)
        decoded_counts = decode_qiskit_counts(
            raw_counts=exec_result.raw_counts,
            node_to_qubit=node_to_qubit,
            sorted_nodes=sorted_nodes,
        )

        # 6. Evaluate sampled measurement distribution
        eval_metrics = evaluate_measurement_distribution(
            decoded_counts=decoded_counts,
            graph=graph,
            optimal_cut_value=classical_opt_cut,
            optimal_bitstrings=classical_opt_strings,
        )

        best_cut = float(eval_metrics["best_sampled_cut"])
        best_str = str(eval_metrics["best_sampled_bitstring"])
        most_freq_str = str(eval_metrics["most_frequent_bitstring"])
        most_freq_cut = graph.compute_cut(most_freq_str).cut_value
        expected_cut = float(eval_metrics["expected_cut_value"])

        approx_ratio = (
            (expected_cut / classical_opt_cut) if (classical_opt_cut and classical_opt_cut > 0) else None
        )
        best_ratio = (
            (best_cut / classical_opt_cut) if (classical_opt_cut and classical_opt_cut > 0) else None
        )
        is_opt_achieved = (
            (best_cut >= classical_opt_cut) if classical_opt_cut is not None else False
        )

        pipeline_time = time.perf_counter() - pipeline_start

        return QAOAAerExperimentResult(
            problem_name=graph.name,
            num_nodes=graph.num_nodes,
            num_edges=graph.num_edges,
            depth_p=depth_p,
            shots=shots,
            seeds={
                "seed_global": self.seed_global,
                "seed_simulator": self.seed_simulator,
                "seed_transpiler": self.seed_transpiler,
            },
            optimizer_name=optimizer_name,
            initial_parameters=opt_result.initial_parameters,
            optimal_parameters=opt_result.optimal_parameters,
            optimal_gamma=opt_result.optimal_gamma,
            optimal_beta=opt_result.optimal_beta,
            optimizer_evaluations=opt_result.num_evaluations,
            final_objective_value=opt_result.final_objective_value,
            final_expected_cut_from_opt=opt_result.final_expected_cut,
            raw_counts=exec_result.raw_counts,
            decoded_counts=decoded_counts,
            total_shots_sampled=exec_result.shots,
            best_measured_bitstring=best_str,
            best_measured_cut=best_cut,
            most_frequent_bitstring=most_freq_str,
            most_frequent_cut=most_freq_cut,
            expected_cut_sampled=expected_cut,
            classical_optimal_cut=classical_opt_cut,
            classical_optimal_bitstrings=classical_opt_strings,
            approximation_ratio=approx_ratio,
            best_solution_ratio=best_ratio,
            ground_state_success_probability=eval_metrics["ground_state_success_probability"],
            transpiled_depth=exec_result.transpiled_depth,
            transpiled_2q_gates=exec_result.transpiled_2q_gates,
            transpiled_total_gates=exec_result.transpiled_total_gates,
            transpilation_level=transpilation_level,
            optimization_time_seconds=opt_time,
            simulation_time_seconds=sim_time,
            total_pipeline_time_seconds=pipeline_time,
            is_classical_optimum_achieved=is_opt_achieved,
        )
