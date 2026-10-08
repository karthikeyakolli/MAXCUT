"""Unified, reusable experiment runner for QAOA Max-Cut execution across all targets."""

from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import sys
import time
from typing import Any, Dict, List, Optional, Union

import qiskit
import qiskit_aer

from maxcut.backends.base import BaseBackendRunner
from maxcut.backends.factory import create_backend_runner
from maxcut.classical.solver import ClassicalMaxCutResult, ExactExhaustiveSolver
from maxcut.domain.model import MaxCutGraph
from maxcut.experiments.config import ExperimentConfig
from maxcut.experiments.schema import ExperimentResult, save_experiment_result
from maxcut.io import load_challenge_instance
from maxcut.metrics.circuit_metrics import extract_circuit_metrics
from maxcut.qaoa.ansatz import build_qaoa_circuit
from maxcut.qaoa.decoding import decode_qiskit_counts, evaluate_measurement_distribution
from maxcut.qaoa.optimizer import QAOAOptimizationResult, QAOAOptimizer


class ExperimentRunner:
    """Standardized orchestrator executing QAOA Max-Cut experiments.

    Reusable across Simulator, Processor A, and Processor B with zero logic duplication.
    """

    def __init__(self, default_backend: Optional[BaseBackendRunner] = None) -> None:
        self.default_backend = default_backend

    def run(
        self,
        config: ExperimentConfig,
        graph: Optional[MaxCutGraph] = None,
        backend: Optional[BaseBackendRunner] = None,
        classical_reference: Optional[Union[Path, str, ClassicalMaxCutResult]] = None,
        save_result: bool = True,
    ) -> ExperimentResult:
        """Executes the complete experimental pipeline according to ExperimentConfig.

        Args:
            config: Full experiment configuration.
            graph: Optional pre-loaded MaxCutGraph. If None, loaded from config.problem_instance_path.
            backend: Optional target backend runner. If None, instantiated from config.backend_name.
            classical_reference: Optional pre-computed classical ground truth.
            save_result: If True, writes JSON result artifact to config.output_location.

        Returns:
            ExperimentResult: Comprehensive standardized result artifact.
        """
        start_time_iso = datetime.now(timezone.utc).isoformat()
        pipeline_start = time.perf_counter()

        # 1. Ingest problem graph
        if graph is None:
            if not config.problem_instance_path:
                raise ValueError("Neither graph instance nor problem_instance_path was provided.")
            inst_path = Path(config.problem_instance_path)
            problem_inst = load_challenge_instance(inst_path)
            graph = MaxCutGraph.from_challenge_instance(problem_inst)

        # 2. Ingest or compute classical reference ground truth
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
        elif config.classical_reference_path and Path(config.classical_reference_path).exists():
            with open(Path(config.classical_reference_path), "r", encoding="utf-8") as f:
                ref_data = json.load(f)
            classical_opt_cut = float(ref_data.get("optimal_cut_value", 0.0))
            classical_opt_strings = list(ref_data.get("optimal_bitstrings", []))

        # 3. Resolve target backend runner
        active_backend: BaseBackendRunner
        if backend is not None:
            active_backend = backend
        elif self.default_backend is not None:
            active_backend = self.default_backend
        else:
            seeds = config.random_seeds
            active_backend = create_backend_runner(
                backend_name=config.backend_name,
                hardware_spec=config.hardware_spec_path,
                seed_simulator=seeds.get("seed_simulator", 42),
                seed_transpiler=seeds.get("seed_transpiler", 42),
            )

        # 4. Variational parameter optimization
        opt_start = time.perf_counter()
        opt_settings = config.optimization_settings
        optimizer = QAOAOptimizer(
            method=config.optimizer,
            maxiter=opt_settings.get("max_iterations", 100),
            tol=opt_settings.get("tolerance", 1e-4),
            seed=config.random_seeds.get("seed_global", 42),
        )
        opt_res: QAOAOptimizationResult = optimizer.optimize(
            graph=graph,
            p=config.depth_p,
            initial_point=config.initial_parameters,
        )
        opt_time = time.perf_counter() - opt_start

        # 5. Assemble and bind QAOA circuit
        ansatz = build_qaoa_circuit(graph, p=config.depth_p, include_measurements=True)
        bound_qc = ansatz.bind(
            gamma_values=opt_res.optimal_gamma,
            beta_values=opt_res.optimal_beta,
        )

        # 6. Execute backend transpilation and measurement sampling
        sim_start = time.perf_counter()
        exec_res = active_backend.run_circuit(
            circuit=bound_qc,
            shots=config.shots,
            optimization_level=config.transpilation_level,
        )
        sim_time = time.perf_counter() - sim_start

        # 7. Decode Qiskit little-endian measurement outcomes to canonical node order
        decoded_counts = decode_qiskit_counts(
            raw_counts=exec_res.raw_counts,
            node_to_qubit=ansatz.node_to_qubit,
            sorted_nodes=sorted(graph.nodes),
        )

        # 8. Statistical evaluation of solution distribution
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
            (expected_cut / classical_opt_cut)
            if (classical_opt_cut and classical_opt_cut > 0)
            else None
        )
        best_ratio = (
            (best_cut / classical_opt_cut)
            if (classical_opt_cut and classical_opt_cut > 0)
            else None
        )
        is_opt_achieved = (
            (best_cut >= classical_opt_cut)
            if classical_opt_cut is not None
            else False
        )

        pipeline_time = time.perf_counter() - pipeline_start
        end_time_iso = datetime.now(timezone.utc).isoformat()

        # 9. Assemble standardized result schema
        swap_count = getattr(exec_res, "swap_count", 0)

        if exec_res.transpiled_circuit is not None:
            c_dict = extract_circuit_metrics(
                logical_circuit=bound_qc,
                transpiled_circuit=exec_res.transpiled_circuit,
                backend_runner=active_backend,
                optimization_level=config.transpilation_level,
                seed_transpiler=config.random_seeds.get("seed_transpiler", 42),
            ).to_dict()
            c_dict["transpiled_depth"] = c_dict["transpiled_circuit_depth"]
            c_dict["transpilation_level"] = config.transpilation_level
            circuit_metrics_dict = c_dict
        else:
            circuit_metrics_dict = {
                "transpiled_depth": exec_res.transpiled_depth,
                "transpiled_circuit_depth": exec_res.transpiled_depth,
                "transpiled_2q_gates": exec_res.transpiled_2q_gates,
                "transpiled_total_gates": exec_res.transpiled_total_gates,
                "swap_count": swap_count,
                "transpilation_level": exec_res.transpilation_level,
            }

        job_meta = getattr(exec_res, "job_metadata", {})

        result = ExperimentResult(
            problem_metadata={
                "name": graph.name,
                "num_nodes": graph.num_nodes,
                "num_edges": graph.num_edges,
                "is_weighted": graph.is_weighted,
                "total_weight": graph.total_weight,
                "source_path": config.problem_instance_path,
            },
            backend_metadata={
                "backend_name": active_backend.backend_name,
                "target_type": active_backend.target_type,
                "num_qubits": active_backend.num_qubits,
                **exec_res.backend_metadata,
            },
            algorithm_parameters={
                "depth_p": config.depth_p,
                "shots": config.shots,
                "optimizer_name": config.optimizer,
                "initial_parameters": opt_res.initial_parameters,
                "optimal_parameters": opt_res.optimal_parameters,
                "optimal_gamma": opt_res.optimal_gamma,
                "optimal_beta": opt_res.optimal_beta,
                "optimizer_evaluations": opt_res.num_evaluations,
                "final_objective_value": opt_res.final_objective_value,
                "final_expected_cut_from_opt": opt_res.final_expected_cut,
            },
            cut_value=best_cut,
            best_measured_bitstring=best_str,
            most_frequent_bitstring=most_freq_str,
            most_frequent_cut=most_freq_cut,
            expected_cut=expected_cut,
            classical_optimal_cut=classical_opt_cut,
            cut_values_by_bitstring=eval_metrics.get("cut_values_by_bitstring", {}),
            approximation_ratio=approx_ratio,
            best_solution_ratio=best_ratio,
            is_classical_optimum_achieved=is_opt_achieved,
            probability_metrics={
                "ground_state_success_probability": eval_metrics.get(
                    "ground_state_success_probability"
                ),
                "num_unique_bitstrings": eval_metrics.get("num_unique_bitstrings"),
                "total_shots_sampled": exec_res.shots,
            },
            runtime={
                "optimization_time_seconds": opt_time,
                "simulation_time_seconds": sim_time,
                "total_pipeline_time_seconds": pipeline_time,
            },
            circuit_metrics=circuit_metrics_dict,
            raw_counts=exec_res.raw_counts,
            decoded_counts=decoded_counts,
            timestamps={
                "start_time_iso": start_time_iso,
                "end_time_iso": end_time_iso,
            },
            reproducibility_information={
                "random_seeds": config.random_seeds,
                "qiskit_version": qiskit.__version__,
                "qiskit_aer_version": qiskit_aer.__version__,
                "python_version": sys.version.split()[0],
                "platform": platform.platform(),
                "config_snapshot": config.to_dict(),
            },
            job_metadata=job_meta,
        )

        # 10. Persist result artifact
        if save_result:
            clean_bname = active_backend.backend_name.lower().replace("-", "_")
            out_filename = f"{graph.name}_{clean_bname}_p{config.depth_p}_result.json"
            out_path = Path(config.output_location) / out_filename
            save_experiment_result(result, out_path)

        return result
