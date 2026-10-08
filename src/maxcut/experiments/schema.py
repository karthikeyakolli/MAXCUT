"""Unified experiment result schema, serializer, and loader.

Provides a single standard result container representing problem metadata, backend metadata,
algorithm parameters, cut metrics, probability metrics, runtimes, circuit metrics,
raw/decoded counts, timestamps, and full reproducibility info.
"""

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


@dataclass
class ExperimentResult:
    """Standardized schema for all QAOA Max-Cut experimental executions."""

    # 1. Problem metadata
    problem_metadata: Dict[str, Any]

    # 2. Backend metadata
    backend_metadata: Dict[str, Any]

    # 3. Algorithm parameters
    algorithm_parameters: Dict[str, Any]

    # 4. Cut values and primary metrics
    cut_value: float  # Best sampled cut value
    best_measured_bitstring: str
    most_frequent_bitstring: str
    most_frequent_cut: float
    expected_cut: float
    classical_optimal_cut: Optional[float]
    cut_values_by_bitstring: Dict[str, float] = field(default_factory=dict)

    # 5. Approximation ratio & quality metrics
    approximation_ratio: Optional[float] = None
    best_solution_ratio: Optional[float] = None
    is_classical_optimum_achieved: bool = False

    # 6. Probability / success metrics
    probability_metrics: Dict[str, Any] = field(default_factory=dict)

    # 7. Runtime performance
    runtime: Dict[str, float] = field(default_factory=dict)

    # 8. Circuit & compilation metrics
    circuit_metrics: Dict[str, Any] = field(default_factory=dict)

    # 9. Raw & decoded counts
    raw_counts: Dict[str, int] = field(default_factory=dict)
    decoded_counts: Dict[str, int] = field(default_factory=dict)

    # 10. Execution timestamps
    timestamps: Dict[str, str] = field(default_factory=dict)

    # 11. Reproducibility information
    reproducibility_information: Dict[str, Any] = field(default_factory=dict)

    # 12. Job metadata
    job_metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Converts result object to a JSON-serializable dictionary."""
        return asdict(self)

    def to_json(self, file_path: Union[str, Path], indent: int = 2) -> None:
        """Serializes the experiment result to a formatted JSON file."""
        save_experiment_result(self, file_path, indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExperimentResult":
        """Instantiates ExperimentResult from a dictionary."""
        allowed_keys = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in allowed_keys}
        return cls(**filtered)

    @classmethod
    def from_json(cls, file_path: Union[str, Path]) -> "ExperimentResult":
        """Loads and validates an ExperimentResult from a JSON file."""
        return load_experiment_result(file_path)

    def summary(self) -> str:
        """Generates a clean human-readable summary of the experiment."""
        prob_meta = self.problem_metadata
        b_meta = self.backend_metadata
        alg_meta = self.algorithm_parameters
        c_meta = self.circuit_metrics
        rt_meta = self.runtime

        ref_str = f"{self.classical_optimal_cut:.4f}" if self.classical_optimal_cut is not None else "N/A"
        alpha_str = f"{self.approximation_ratio:.4f} ({self.approximation_ratio*100:.2f}%)" if self.approximation_ratio is not None else "N/A"
        succ_val = self.probability_metrics.get("ground_state_success_probability")
        succ_str = f"{succ_val:.4f} ({succ_val*100:.2f}%)" if succ_val is not None else "N/A"

        return (
            "======================================================================\n"
            f"  Experiment Result: {prob_meta.get('name', 'Unknown')} on {b_meta.get('backend_name', 'Unknown')}\n"
            "======================================================================\n"
            f"Problem: {prob_meta.get('name')} | Nodes (|V|): {prob_meta.get('num_nodes')} | Edges (|E|): {prob_meta.get('num_edges')}\n"
            f"Backend: {b_meta.get('backend_name')} ({b_meta.get('target_type')}) | Qubits: {b_meta.get('num_qubits')}\n"
            f"Algorithm: QAOA depth p={alg_meta.get('depth_p')} | Shots: {alg_meta.get('shots')} | Optimizer: {alg_meta.get('optimizer_name')}\n"
            "----------------------------------------------------------------------\n"
            "CIRCUIT COMPILATION METRICS:\n"
            f"  Transpiled Depth: {c_meta.get('transpiled_depth')}\n"
            f"  2-Qubit Gates: {c_meta.get('transpiled_2q_gates')}\n"
            f"  Total Gates: {c_meta.get('transpiled_total_gates')}\n"
            f"  SWAP Gates: {c_meta.get('swap_count', 0)}\n"
            f"  Transpilation Level: {c_meta.get('transpilation_level', 1)}\n"
            "----------------------------------------------------------------------\n"
            "CUT & QUALITY EVALUATION:\n"
            f"  Best Measured Cut: {self.cut_value:.4f} (Bitstring: '{self.best_measured_bitstring}')\n"
            f"  Expected Cut <C>: {self.expected_cut:.4f}\n"
            f"  Classical Optimum: {ref_str}\n"
            f"  Approximation Ratio (alpha): {alpha_str}\n"
            f"  Ground State Success Probability: {succ_str}\n"
            f"  Classical Optimum Achieved: {'YES' if self.is_classical_optimum_achieved else 'NO'}\n"
            "----------------------------------------------------------------------\n"
            "EXECUTION TIMING:\n"
            f"  Optimization Time: {rt_meta.get('optimization_time_seconds', 0.0):.4f} s\n"
            f"  Simulation/Execution Time: {rt_meta.get('simulation_time_seconds', 0.0):.4f} s\n"
            f"  Total Wall-Clock Time: {rt_meta.get('total_pipeline_time_seconds', 0.0):.4f} s\n"
            "======================================================================"
        )


def save_experiment_result(
    result: ExperimentResult,
    file_path: Union[str, Path],
    indent: int = 2,
) -> None:
    """Serializes an ExperimentResult to disk."""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result.to_dict(), f, indent=indent)


def load_experiment_result(file_path: Union[str, Path]) -> ExperimentResult:
    """Loads and returns an ExperimentResult from a saved JSON file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Experiment result file not found at: '{path.resolve()}'")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return ExperimentResult.from_dict(data)
