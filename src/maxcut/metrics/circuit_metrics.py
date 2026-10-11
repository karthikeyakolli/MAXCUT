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

    # Gate inventory and fine-grained decompositions
    gate_breakdown: Dict[str, int] = field(default_factory=dict)
    compilation_metadata: Dict[str, Any] = field(default_factory=dict)
    basis_synthesis_2q_gates: int = 0
    routing_2q_gates: int = 0
    explicit_swap_count: int = 0
    routing_swap_count: int = 0
    initial_layout: Dict[int, int] = field(default_factory=dict)
    final_layout: Dict[int, int] = field(default_factory=dict)

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
            f"SWAP Operations: {self.routing_swap_count} routing SWAPs ({self.explicit_swap_count} explicit in final basis)\n"
            f"2Q Decomposition: {self.basis_synthesis_2q_gates} basis synthesis + {self.routing_2q_gates} routing = {self.transpiled_2q_gates} total 2Q\n"
            f"Transpiled Total Gates: {self.transpiled_total_gates} (1Q: {self.transpiled_1q_gates}, 2Q: {self.transpiled_2q_gates})\n"
            f"Native 2Q Gate: '{self.native_2q_gate}' | Breakdown: {dict(self.gate_breakdown)}\n"
            f"Initial Layout: {self.initial_layout}\n"
        )


def extract_circuit_metrics(
    logical_circuit: QuantumCircuit,
    transpiled_circuit: QuantumCircuit,
    backend_runner: BaseBackendRunner,
    optimization_level: int,
    seed_transpiler: int = 42,
    routed_circuit: Optional[QuantumCircuit] = None,
    pass_manager: Optional[Any] = None,
    routing_swap_count: Optional[int] = None,
) -> CircuitResourceMetrics:
    """Extracts comparative resource metrics between logical and compiled circuits.

    All metrics are directly derived from concrete QuantumCircuit instances.

    Args:
        logical_circuit: High-level pre-compilation QAOA QuantumCircuit.
        transpiled_circuit: Hardware-targeted compiled QuantumCircuit.
        backend_runner: Target backend runner containing architectural specs.
        optimization_level: Prescribed preset pass manager optimization level.
        seed_transpiler: RNG seed used for compiler routing.
        routed_circuit: Optional routed circuit before basis translation to extract explicit SWAP count.
        pass_manager: Optional staged pass manager used to compile the circuit.
        routing_swap_count: Optional precomputed routing SWAP count introduced during routing.

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

    # Explicit SWAP gates in final compiled circuit
    explicit_swap_count = int(trans_ops.get("swap", 0))

    # Exact SWAP-equivalent operations introduced by routing:
    if routing_swap_count is None:
        if routed_circuit is not None:
            routing_swap_count = int(routed_circuit.count_ops().get("swap", 0))
        elif hasattr(backend_runner, "spec") and backend_runner.spec.coupling_map:
            from qiskit.transpiler import CouplingMap
            from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
            state = {"max_swaps": 0}
            def _cb(**kwargs: Any) -> None:
                dag = kwargs.get("dag")
                if dag and hasattr(dag, "count_ops"):
                    swaps = int(dag.count_ops().get("swap", 0))
                    if swaps >= state["max_swaps"] and swaps > 0:
                        state["max_swaps"] = swaps
            pm = pass_manager or generate_preset_pass_manager(
                coupling_map=CouplingMap(backend_runner.spec.coupling_map),
                basis_gates=backend_runner.spec.basis_gates,
                optimization_level=optimization_level,
                seed_transpiler=seed_transpiler,
            )
            pm.run(logical_circuit, callback=_cb)
            logical_swaps = int(logical_circuit.count_ops().get("swap", 0))
            routing_swap_count = max(0, state["max_swaps"] - logical_swaps)
        else:
            routing_swap_count = explicit_swap_count

    # Dynamically determine native 2Q cost per SWAP for this target backend without hardcoding
    swap_test = QuantumCircuit(2)
    swap_test.swap(0, 1)
    if pass_manager is not None and getattr(pass_manager, "translation", None):
        trans_swap = pass_manager.translation.run(swap_test)
        two_q_per_swap = sum(c for g, c in trans_swap.count_ops().items() if g in two_qubit_names)
    elif hasattr(backend_runner, "spec") and getattr(backend_runner.spec, "basis_gates", None):
        from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
        pm_trans = generate_preset_pass_manager(
            basis_gates=backend_runner.spec.basis_gates,
            optimization_level=optimization_level,
            seed_transpiler=seed_transpiler,
        )
        if pm_trans.translation:
            trans_swap = pm_trans.translation.run(swap_test)
        else:
            trans_swap = pm_trans.run(swap_test)
        two_q_per_swap = sum(c for g, c in trans_swap.count_ops().items() if g in two_qubit_names)
    else:
        two_q_per_swap = 0 if "swap" in trans_ops else 3

    # Fine-grained 2Q gate decomposition accounting:
    routing_2q = routing_swap_count * two_q_per_swap
    basis_synthesis_2q = trans_2q - routing_2q

    # Overhead metrics: do not infer routing overhead by subtracting unrelated gate counts (AUD-03)
    overhead_2q = routing_2q
    routing_ratio = (trans_2q / basis_synthesis_2q) if basis_synthesis_2q > 0 else 1.0
    depth_ratio = (trans_depth / log_depth) if log_depth > 0 else 1.0

    backend_meta = backend_runner.get_metadata()
    arch_family = str(backend_meta.get("architecture_family", backend_runner.target_type))
    native_2q = str(backend_meta.get("native_2q_gate", "unknown"))

    # Layout extraction
    initial_layout_dict: Dict[int, int] = {}
    final_layout_dict: Dict[int, int] = {}
    if getattr(transpiled_circuit, "layout", None) is not None:
        try:
            init_v = transpiled_circuit.layout.initial_virtual_layout()
            if init_v:
                for phys, virt in init_v.get_physical_bits().items():
                    if hasattr(virt, "_index"):
                        initial_layout_dict[virt._index] = phys
        except Exception:
            pass
        try:
            final_idx = transpiled_circuit.layout.final_index_layout()
            if final_idx:
                final_layout_dict = {i: phys for i, phys in enumerate(final_idx)}
        except Exception:
            pass

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
        swap_count=routing_swap_count,
        two_qubit_gate_overhead=overhead_2q,
        routing_overhead_ratio=routing_ratio,
        depth_expansion_ratio=depth_ratio,
        gate_breakdown=trans_ops,
        compilation_metadata=backend_meta,
        basis_synthesis_2q_gates=basis_synthesis_2q,
        routing_2q_gates=routing_2q,
        explicit_swap_count=explicit_swap_count,
        routing_swap_count=routing_swap_count,
        initial_layout=initial_layout_dict,
        final_layout=final_layout_dict,
    )
