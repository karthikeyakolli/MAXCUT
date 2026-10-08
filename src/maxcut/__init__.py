"""Max-Cut QAOA Optimization Package.

Qiskit Fall Fest 2026 — Track: O1 Max-Cut.
Modular architectural package adhering to PROJECT_SPEC.md.
"""

from typing import List

from maxcut.backends import (
    AerBackendRunner,
    AerExecutionResult,
    BackendExecutionResult,
    BaseBackendRunner,
    ProcessorBackendRunner,
    ProcessorExecutionResult,
    create_backend_runner,
)
from maxcut.classical import (
    ClassicalMaxCutResult,
    ExactExhaustiveSolver,
)
from maxcut.domain import (
    CutResult,
    Edge,
    GraphValidationError,
    InvalidAssignmentError,
    MaxCutGraph,
    Partition,
)
from maxcut.experiments import (
    ExperimentConfig,
    ExperimentResult,
    ExperimentRunner,
    QAOAAerExperiment,
    QAOAAerExperimentResult,
    load_experiment_result,
    save_experiment_result,
)
from maxcut.formulation import (
    IsingFormulation,
    QUBOFormulation,
    QuantumCostHamiltonian,
    build_cost_hamiltonian,
    build_maxcut_ising,
    build_maxcut_qubo,
    evaluate_all_representations,
)
from maxcut.io import (
    ChallengeKitValidationError,
    MaxCutProblemInstance,
    MissingChallengeKitArtifactError,
    ProcessorHardwareSpec,
    load_challenge_instance,
    load_processor_spec,
)
from maxcut.qaoa import (
    QAOAAnsatz,
    QAOAOptimizationResult,
    QAOAOptimizer,
    build_qaoa_circuit,
    decode_qiskit_counts,
    evaluate_measurement_distribution,
)
from maxcut.metrics import (
    CircuitResourceMetrics,
    ProcessorCircuitComparator,
    extract_circuit_metrics,
)
from maxcut.visualization import (
    plot_maxcut_graph,
    plot_measurement_distribution,
    plot_qaoa_circuit,
)

__version__ = "0.1.0"
__all__: List[str] = [
    "io",
    "domain",
    "classical",
    "formulation",
    "qaoa",
    "backends",
    "experiments",
    "metrics",
    "visualization",
    "MaxCutProblemInstance",
    "ProcessorHardwareSpec",
    "MissingChallengeKitArtifactError",
    "ChallengeKitValidationError",
    "load_challenge_instance",
    "load_processor_spec",
    "MaxCutGraph",
    "Partition",
    "Edge",
    "CutResult",
    "InvalidAssignmentError",
    "GraphValidationError",
    "ExactExhaustiveSolver",
    "ClassicalMaxCutResult",
    "QUBOFormulation",
    "IsingFormulation",
    "QuantumCostHamiltonian",
    "build_maxcut_qubo",
    "build_maxcut_ising",
    "build_cost_hamiltonian",
    "evaluate_all_representations",
    "QAOAAnsatz",
    "build_qaoa_circuit",
    "decode_qiskit_counts",
    "evaluate_measurement_distribution",
    "QAOAOptimizer",
    "QAOAOptimizationResult",
    "BaseBackendRunner",
    "BackendExecutionResult",
    "AerBackendRunner",
    "AerExecutionResult",
    "ProcessorBackendRunner",
    "ProcessorExecutionResult",
    "create_backend_runner",
    "ExperimentConfig",
    "ExperimentResult",
    "ExperimentRunner",
    "save_experiment_result",
    "load_experiment_result",
    "QAOAAerExperiment",
    "QAOAAerExperimentResult",
    "CircuitResourceMetrics",
    "extract_circuit_metrics",
    "ProcessorCircuitComparator",
    "plot_maxcut_graph",
    "plot_qaoa_circuit",
    "plot_measurement_distribution",
]
