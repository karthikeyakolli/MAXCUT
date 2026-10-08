"""Base abstractions for quantum backends and transpilation runners."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from qiskit.circuit import QuantumCircuit


@dataclass(frozen=True)
class BackendExecutionResult:
    """Standardized output container for any backend execution."""

    backend_name: str
    raw_counts: Dict[str, int]
    shots: int
    transpiled_circuit: QuantumCircuit
    transpiled_depth: int
    transpiled_2q_gates: int
    transpiled_total_gates: int
    transpilation_level: int
    backend_metadata: Dict[str, Any] = field(default_factory=dict)
    job_metadata: Dict[str, Any] = field(default_factory=dict)


class BaseBackendRunner(ABC):
    """Abstract interface defining the execution contract for any simulator or hardware target."""

    @property
    @abstractmethod
    def backend_name(self) -> str:
        """Unique identifier of the target backend."""
        pass

    @property
    @abstractmethod
    def target_type(self) -> str:
        """Target classification: 'simulator', 'hardware_processor', etc."""
        pass

    @property
    @abstractmethod
    def num_qubits(self) -> int:
        """Number of qubits supported by the target."""
        pass

    @abstractmethod
    def run_circuit(
        self,
        circuit: QuantumCircuit,
        shots: int = 2048,
        optimization_level: int = 1,
    ) -> BackendExecutionResult:
        """Compiles and executes a bound quantum circuit.

        Args:
            circuit: Bound QuantumCircuit ready for compilation and measurement.
            shots: Total number of measurement shots.
            optimization_level: Transpiler preset optimization level (0-3).

        Returns:
            BackendExecutionResult: Compilation metrics and measurement outcomes.
        """
        pass

    def get_metadata(self) -> Dict[str, Any]:
        """Returns standard backend metadata for experiment result serialization."""
        return {
            "backend_name": self.backend_name,
            "target_type": self.target_type,
            "num_qubits": self.num_qubits,
        }
