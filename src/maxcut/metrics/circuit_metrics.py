"""Circuit resource metrics collection and analysis layer.

Extracts hardware-level resource consumption metrics from logical and compiled
circuits according to Qiskit 2.x standards.
"""

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from qiskit.circuit import QuantumCircuit

from maxcut.backends.base import BaseBackendRunner


@dataclass(frozen=True)
class CircuitResourceMetrics:
    """Standardized resource and architectural metrics for a compiled quantum circuit."""

    backend_name: str
    architecture_family: str
    native_2q_gate: str
    optimization_level: int
    seed_transpiler: int

    # Logical circuit properties
    logical_qubit_count: int
    logical_circuit_depth: int
    logical_total_gates: int
    logical_1q_gates: int
    logical_2q_gates: int

    # Physical / Transpiled circuit properties
    physical_qubit_count: int
    transpiled_circuit_depth: int
    transpiled_total_gates: int
    transpiled_1q_gates: int
    transpiled_2q_gates: int
    swap_count: int

    # Routing & overhead ratios
    two_qubit_gate_overhead: int
    routing_overhead_ratio: float
    depth_expansion_ratio: float

    # Gate inventory
    gate_breakdown: Dict[str, int] = field(default_factory=dict)
    compilation_metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Converts metrics to a serializable dictionary."""
        return asdict(self)

    def summary(self) -> str:
        """Produces a clean text summary of resource metrics."""
        return (
            f"=== Circuit Resource Metrics: {self.backend_name} (Level {self.optimization_level}) ===\n"
            f"Logical Qubits: {self.logical_qubit_count} -> Physical Qubits: {self.physical_qubit_count}\n"
            f"Logical Depth:  {self.logical_circuit_depth} -> Transpiled Depth: {self.transpiled_circuit_depth} (x{self.depth_expansion_ratio:.2f})\n"
            f"Logical 2Q Gates: {self.logical_2q_gates} -> Transpiled 2Q Gates: {self.transpiled_2q_gates} (x{self.routing_overhead_ratio:.2f})\n"
            f"SWAP Gates: {self.swap_count} | 2Q Overhead: +{self.two_qubit_gate_overhead} gates\n"
            f"Transpiled Total Gates: {self.transpiled_total_gates} (1Q: {self.transpiled_1q_gates}, 2Q: {self.transpiled_2q_gates})\n"
            f"Native 2Q Gate: '{self.native_2q_gate}' | Breakdown: {dict(self.gate_breakdown)}\n"
        )


def extract_circuit_metrics(
    logical_circuit: QuantumCircuit,
    transpiled_circuit: QuantumCircuit,
    backend_runner: BaseBackendRunner,
    optimization_level: int,
    seed_transpiler: int = 42,
) -> CircuitResourceMetrics:
    """Extracts comparative resource metrics between logical and compiled circuits.

    All metrics are directly derived from the concrete QuantumCircuit instances.

    Args:
        logical_circuit: High-level pre-compilation QAOA QuantumCircuit.
        transpiled_circuit: Hardware-targeted compiled QuantumCircuit.
        backend_runner: Target backend runner containing architectural specs.
        optimization_level: Prescribed preset pass manager optimization level.
        seed_transpiler: RNG seed used for compiler routing.

    Returns:
        CircuitResourceMetrics: Verified resource metrics.
    """
    two_qubit_names = {"cx", "ecr", "cz", "rzz", "swap", "cp", "iswap"}
    one_qubit_names = {"rz", "sx", "x", "h", "u", "u1", "u2", "u3", "rx", "ry", "id"}

    # Logical counts
    log_ops = logical_circuit.count_ops()
    log_depth = logical_circuit.depth()
    log_qubits = logical_circuit.num_qubits
    log_2q = sum(count for gate, count in log_ops.items() if gate in two_qubit_names)
    log_1q = sum(count for gate, count in log_ops.items() if gate in one_qubit_names)
    log_total = sum(count for gate, count in log_ops.items() if gate not in {"barrier", "measure"})

    # Transpiled counts
    trans_ops = dict(transpiled_circuit.count_ops())
    trans_depth = transpiled_circuit.depth()
    trans_qubits = transpiled_circuit.num_qubits
    trans_2q = sum(count for gate, count in trans_ops.items() if gate in two_qubit_names)
    trans_1q = sum(count for gate, count in trans_ops.items() if gate in one_qubit_names)
    trans_total = sum(count for gate, count in trans_ops.items() if gate not in {"barrier", "measure"})
    swap_count = int(trans_ops.get("swap", 0))

    # Overhead metrics
    overhead_2q = trans_2q - log_2q
    routing_ratio = (trans_2q / log_2q) if log_2q > 0 else 1.0
    depth_ratio = (trans_depth / log_depth) if log_depth > 0 else 1.0

    backend_meta = backend_runner.get_metadata()
    arch_family = str(backend_meta.get("architecture_family", backend_runner.target_type))
    native_2q = str(backend_meta.get("native_2q_gate", "unknown"))

    return CircuitResourceMetrics(
        backend_name=backend_runner.backend_name,
        architecture_family=arch_family,
        native_2q_gate=native_2q,
        optimization_level=optimization_level,
        seed_transpiler=seed_transpiler,
        logical_qubit_count=log_qubits,
        logical_circuit_depth=log_depth,
        logical_total_gates=log_total,
        logical_1q_gates=log_1q,
        logical_2q_gates=log_2q,
        physical_qubit_count=trans_qubits,
        transpiled_circuit_depth=trans_depth,
        transpiled_total_gates=trans_total,
        transpiled_1q_gates=trans_1q,
        transpiled_2q_gates=trans_2q,
        swap_count=swap_count,
        two_qubit_gate_overhead=overhead_2q,
        routing_overhead_ratio=routing_ratio,
        depth_expansion_ratio=depth_ratio,
        gate_breakdown=trans_ops,
        compilation_metadata=backend_meta,
    )
