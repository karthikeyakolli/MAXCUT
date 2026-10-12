"""Backend adapter for Processor A (5Q linear-chain architecture, CX native entangler).

Implements BaseBackendRunner to decouple the application from hardware-specific logic.
Provides architecture verification and metadata collection without submitting physical jobs.
Supports both ideal topology emulation and authentic noise-aware simulation.
"""

from pathlib import Path
from typing import Any, Dict, Optional

from qiskit.circuit import QuantumCircuit
from qiskit.transpiler import CouplingMap
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel

from maxcut.backends.base import BackendExecutionResult, BaseBackendRunner
from maxcut.backends.processor_backend import (
    MissingNoiseConfigurationError,
    ProcessorExecutionResult,
    build_noise_model,
)
from maxcut.io import ProcessorHardwareSpec, load_processor_spec


class ProcessorABackend(BaseBackendRunner):
    """Adapter for official Processor A architecture definition."""

    SPEC_PATH = Path(__file__).resolve().parent / "hardware_spec.json"

    def __init__(
        self,
        spec_path: Optional[Path] = None,
        seed_simulator: int = 42,
        seed_transpiler: int = 42,
        execution_mode: str = "ideal",
        noise_config: Optional[Dict[str, Any]] = None,
        noise_model: Optional[NoiseModel] = None,
    ) -> None:
        target_path = spec_path or self.SPEC_PATH
        self._spec: ProcessorHardwareSpec = load_processor_spec(target_path)
        self.seed_simulator: int = seed_simulator
        self.seed_transpiler: int = seed_transpiler
        self._coupling_map = CouplingMap(self._spec.coupling_map)

        is_noisy = execution_mode in {"noisy", "aer_noisy_simulation"}
        self._execution_mode = "aer_noisy_simulation" if is_noisy else "aer_hardware_topology_emulation"
        self._noise_config = noise_config
        self._noise_model = noise_model

        if is_noisy:
            if self._noise_model is None:
                if self._noise_config is None:
                    raise MissingNoiseConfigurationError(
                        f"Cannot run noisy execution for '{self._spec.name}': "
                        "official noise configuration is missing or unverified. "
                        "Do not invent synthetic noise rates."
                    )
                self._noise_model = build_noise_model(self._spec, self._noise_config)
            self._simulator = AerSimulator(
                noise_model=self._noise_model,
                seed_simulator=seed_simulator,
            )
            self._noise_applied = True
        else:
            self._simulator = AerSimulator(seed_simulator=seed_simulator)
            self._noise_applied = False

    @property
    def spec(self) -> ProcessorHardwareSpec:
        return self._spec

    @property
    def backend_name(self) -> str:
        return self._spec.name

    @property
    def target_type(self) -> str:
        return "hardware_processor"

    @property
    def num_qubits(self) -> int:
        return self._spec.num_qubits

    @property
    def execution_mode(self) -> str:
        return self._execution_mode

    @property
    def noise_applied(self) -> bool:
        return self._noise_applied

    @property
    def native_2q_gate(self) -> str:
        return self._spec.metadata.get("native_2q_gate", "cx")

    def get_metadata(self) -> Dict[str, Any]:
        """Collects exhaustive architectural metadata."""
        return {
            "backend_name": self.backend_name,
            "target_type": self.target_type,
            "num_qubits": self.num_qubits,
            "basis_gates": list(self._spec.basis_gates),
            "coupling_map": list(self._spec.coupling_map),
            "coupling_edge_count": len(self._spec.coupling_map),
            "qubit_properties": dict(self._spec.qubit_properties),
            "native_2q_gate": self.native_2q_gate,
            "architecture_family": self._spec.metadata.get("architecture_family", "5Q-Linear-Chain"),
            "spec_source": str(self.SPEC_PATH),
            "execution_mode": self._execution_mode,
            "noise_applied": self._noise_applied,
        }

    def verify_qaoa_circuit(
        self,
        circuit: QuantumCircuit,
        optimization_level: int = 1,
    ) -> Dict[str, Any]:
        """Verifies transpilation readiness, gate compliance, and routing overhead."""
        pass_manager = generate_preset_pass_manager(
            coupling_map=self._coupling_map,
            basis_gates=self._spec.basis_gates,
            optimization_level=optimization_level,
            seed_transpiler=self.seed_transpiler,
            layout_method="sabre",
            routing_method="sabre",
        )

        state = {"max_swaps": 0}

        def _transpile_cb(**kwargs: Any) -> None:
            dag = kwargs.get("dag")
            if dag and hasattr(dag, "count_ops"):
                swaps = int(dag.count_ops().get("swap", 0))
                if swaps >= state["max_swaps"] and swaps > 0:
                    state["max_swaps"] = swaps

        transpiled_qc = pass_manager.run(circuit, callback=_transpile_cb)
        op_counts = transpiled_qc.count_ops()

        non_basis_gates = [
            gate for gate in op_counts
            if gate not in self._spec.basis_gates and gate not in {"barrier", "measure"}
        ]
        is_basis_compliant = (len(non_basis_gates) == 0)

        # Coupling map connectivity compliance check
        cmap_set = set(tuple(e) for e in self._spec.coupling_map)
        coupling_violations = []
        for inst in transpiled_qc.data:
            if len(inst.qubits) == 2:
                q0 = transpiled_qc.find_bit(inst.qubits[0]).index
                q1 = transpiled_qc.find_bit(inst.qubits[1]).index
                if (q0, q1) not in cmap_set:
                    coupling_violations.append((inst.operation.name, q0, q1))
        is_connectivity_compliant = (len(coupling_violations) == 0)

        # Physical qubit usage
        physical_qubits_used = sorted(list(set(
            transpiled_qc.find_bit(q).index
            for inst in transpiled_qc.data
            if inst.operation.name != "barrier"
            for q in inst.qubits
        )))

        # Layout extraction
        initial_layout: Dict[int, int] = {}
        final_layout: Optional[List[int]] = None
        if getattr(transpiled_qc, "layout", None) is not None:
            init_v = transpiled_qc.layout.initial_virtual_layout()
            if init_v:
                for phys, virt in init_v.get_physical_bits().items():
                    if hasattr(virt, "_index") and getattr(getattr(virt, "_register", None), "name", None) == "q":
                        initial_layout[virt._index] = phys
            final_layout = transpiled_qc.layout.final_index_layout()

        two_qubit_gate_names = {"cx", "ecr", "cz", "rzz", "swap"}
        two_q_count = sum(
            count for gate, count in op_counts.items() if gate in two_qubit_gate_names
        )

        swap_test = QuantumCircuit(2)
        swap_test.swap(0, 1)
        if getattr(pass_manager, "translation", None):
            trans_swap = pass_manager.translation.run(swap_test)
        else:
            trans_swap = pass_manager.run(swap_test)
        two_q_per_swap = sum(c for g, c in trans_swap.count_ops().items() if g in two_qubit_gate_names)

        explicit_swap_count = int(op_counts.get("swap", 0))
        logical_swaps = int(circuit.count_ops().get("swap", 0))
        routing_swap_count = max(0, state["max_swaps"] - logical_swaps)
        routing_2q_gates = routing_swap_count * two_q_per_swap
        basis_synthesis_2q_gates = two_q_count - routing_2q_gates

        return {
            "is_compilation_successful": True,
            "is_basis_compliant": is_basis_compliant,
            "non_basis_gates": non_basis_gates,
            "is_connectivity_compliant": is_connectivity_compliant,
            "coupling_violations": coupling_violations,
            "physical_qubits_used": physical_qubits_used,
            "physical_qubits_active_count": len(physical_qubits_used),
            "initial_layout": initial_layout,
            "final_layout": final_layout,
            "gate_breakdown": dict(op_counts),
            "transpiled_depth": transpiled_qc.depth(),
            "transpiled_total_gates": sum(op_counts.values()),
            "transpiled_2q_gates": two_q_count,
            "basis_synthesis_2q_gates": basis_synthesis_2q_gates,
            "routing_2q_gates": routing_2q_gates,
            "explicit_swap_count": explicit_swap_count,
            "routing_swap_count": routing_swap_count,
            "cx_gate_count": op_counts.get("cx", 0),
            "ecr_gate_count": op_counts.get("ecr", 0),
            "swap_count": routing_swap_count,
            "transpiled_qubit_count": transpiled_qc.num_qubits,
            "optimization_level": optimization_level,
            "layout_method": "sabre",
            "routing_method": "sabre",
            "seed_transpiler": self.seed_transpiler,
        }

    def transpile_circuit(
        self,
        circuit: QuantumCircuit,
        optimization_level: int = 1,
    ) -> Tuple[QuantumCircuit, Dict[str, Any]]:
        """Transpiles a circuit targeting Processor A and returns (transpiled_qc, metrics)."""
        pass_manager = generate_preset_pass_manager(
            coupling_map=self._coupling_map,
            basis_gates=self._spec.basis_gates,
            optimization_level=optimization_level,
            seed_transpiler=self.seed_transpiler,
            layout_method="sabre",
            routing_method="sabre",
        )

        state = {"max_swaps": 0}

        def _transpile_cb(**kwargs: Any) -> None:
            dag = kwargs.get("dag")
            if dag and hasattr(dag, "count_ops"):
                swaps = int(dag.count_ops().get("swap", 0))
                if swaps >= state["max_swaps"] and swaps > 0:
                    state["max_swaps"] = swaps

        transpiled_qc = pass_manager.run(circuit, callback=_transpile_cb)
        op_counts = transpiled_qc.count_ops()

        non_basis_gates = [
            gate for gate in op_counts
            if gate not in self._spec.basis_gates and gate not in {"barrier", "measure"}
        ]
        is_basis_compliant = (len(non_basis_gates) == 0)

        cmap_set = set(tuple(e) for e in self._spec.coupling_map)
        coupling_violations = []
        for inst in transpiled_qc.data:
            if len(inst.qubits) == 2:
                q0 = transpiled_qc.find_bit(inst.qubits[0]).index
                q1 = transpiled_qc.find_bit(inst.qubits[1]).index
                if (q0, q1) not in cmap_set:
                    coupling_violations.append((inst.operation.name, q0, q1))
        is_connectivity_compliant = (len(coupling_violations) == 0)

        physical_qubits_used = sorted(list(set(
            transpiled_qc.find_bit(q).index
            for inst in transpiled_qc.data
            if inst.operation.name != "barrier"
            for q in inst.qubits
        )))

        initial_layout: Dict[int, int] = {}
        final_layout: Optional[List[int]] = None
        if getattr(transpiled_qc, "layout", None) is not None:
            init_v = transpiled_qc.layout.initial_virtual_layout()
            if init_v:
                for phys, virt in init_v.get_physical_bits().items():
                    if hasattr(virt, "_index") and getattr(getattr(virt, "_register", None), "name", None) == "q":
                        initial_layout[virt._index] = phys
            final_layout = transpiled_qc.layout.final_index_layout()

        two_qubit_gate_names = {"cx", "ecr", "cz", "rzz", "swap"}
        two_q_count = sum(
            count for gate, count in op_counts.items() if gate in two_qubit_gate_names
        )

        swap_test = QuantumCircuit(2)
        swap_test.swap(0, 1)
        if getattr(pass_manager, "translation", None):
            trans_swap = pass_manager.translation.run(swap_test)
        else:
            trans_swap = pass_manager.run(swap_test)
        two_q_per_swap = sum(c for g, c in trans_swap.count_ops().items() if g in two_qubit_gate_names)

        explicit_swap_count = int(op_counts.get("swap", 0))
        logical_swaps = int(circuit.count_ops().get("swap", 0))
        routing_swap_count = max(0, state["max_swaps"] - logical_swaps)
        routing_2q_gates = routing_swap_count * two_q_per_swap
        basis_synthesis_2q_gates = two_q_count - routing_2q_gates

        metrics = {
            "is_compilation_successful": True,
            "is_basis_compliant": is_basis_compliant,
            "non_basis_gates": non_basis_gates,
            "is_connectivity_compliant": is_connectivity_compliant,
            "coupling_violations": coupling_violations,
            "physical_qubits_used": physical_qubits_used,
            "physical_qubits_active_count": len(physical_qubits_used),
            "initial_layout": initial_layout,
            "final_layout": final_layout,
            "gate_breakdown": dict(op_counts),
            "transpiled_depth": transpiled_qc.depth(),
            "transpiled_total_gates": sum(op_counts.values()),
            "transpiled_2q_gates": two_q_count,
            "basis_synthesis_2q_gates": basis_synthesis_2q_gates,
            "routing_2q_gates": routing_2q_gates,
            "explicit_swap_count": explicit_swap_count,
            "routing_swap_count": routing_swap_count,
            "cx_gate_count": op_counts.get("cx", 0),
            "ecr_gate_count": op_counts.get("ecr", 0),
            "swap_count": routing_swap_count,
            "transpiled_qubit_count": transpiled_qc.num_qubits,
            "optimization_level": optimization_level,
            "layout_method": "sabre",
            "routing_method": "sabre",
            "seed_transpiler": self.seed_transpiler,
        }
        return transpiled_qc, metrics

    def run_circuit(
        self,
        circuit: QuantumCircuit,
        shots: int = 2048,
        optimization_level: int = 1,
    ) -> ProcessorExecutionResult:
        """Transpiles circuit strictly against Processor A topology and emulates shots locally."""
        pass_manager = generate_preset_pass_manager(
            coupling_map=self._coupling_map,
            basis_gates=self._spec.basis_gates,
            optimization_level=optimization_level,
            seed_transpiler=self.seed_transpiler,
            layout_method="sabre",
            routing_method="sabre",
        )

        state = {"max_swaps": 0}

        def _transpile_cb(**kwargs: Any) -> None:
            dag = kwargs.get("dag")
            if dag and hasattr(dag, "count_ops"):
                swaps = int(dag.count_ops().get("swap", 0))
                if swaps >= state["max_swaps"] and swaps > 0:
                    state["max_swaps"] = swaps

        transpiled_qc = pass_manager.run(circuit, callback=_transpile_cb)
        op_counts = transpiled_qc.count_ops()

        two_qubit_gate_names = {"cx", "ecr", "cz", "rzz", "swap"}
        two_q_count = sum(
            count for gate, count in op_counts.items() if gate in two_qubit_gate_names
        )

        swap_test = QuantumCircuit(2)
        swap_test.swap(0, 1)
        if getattr(pass_manager, "translation", None):
            trans_swap = pass_manager.translation.run(swap_test)
        else:
            trans_swap = pass_manager.run(swap_test)
        two_q_per_swap = sum(c for g, c in trans_swap.count_ops().items() if g in two_qubit_gate_names)

        explicit_swap_count = int(op_counts.get("swap", 0))
        logical_swaps = int(circuit.count_ops().get("swap", 0))
        routing_swap_count = max(0, state["max_swaps"] - logical_swaps)
        routing_2q_gates = routing_swap_count * two_q_per_swap
        basis_synthesis_2q_gates = two_q_count - routing_2q_gates

        job = self._simulator.run(transpiled_qc, shots=shots)
        result = job.result()
        raw_counts = result.get_counts()

        job_metadata = {
            "job_id": job.job_id(),
            "status": str(job.status()),
            "shots": shots,
            "seed_simulator": self.seed_simulator,
            "seed_transpiler": self.seed_transpiler,
            "execution_mode": self._execution_mode,
            "noise_applied": self._noise_applied,
            "backend_name": self.backend_name,
            "architecture_family": self._spec.metadata.get("architecture_family", "5Q-Linear-Chain"),
            "native_2q_gate": self.native_2q_gate,
            "optimization_level": optimization_level,
            "layout_method": "sabre",
            "routing_method": "sabre",
        }

        return ProcessorExecutionResult(
            backend_name=self.backend_name,
            raw_counts=raw_counts,
            shots=shots,
            transpiled_circuit=transpiled_qc,
            transpiled_depth=transpiled_qc.depth(),
            transpiled_2q_gates=two_q_count,
            transpiled_total_gates=sum(op_counts.values()),
            transpilation_level=optimization_level,
            backend_metadata=self.get_metadata(),
            job_metadata=job_metadata,
            swap_count=routing_swap_count,
            explicit_swap_count=explicit_swap_count,
            routing_swap_count=routing_swap_count,
            basis_synthesis_2q_gates=basis_synthesis_2q_gates,
            routing_2q_gates=routing_2q_gates,
            hardware_spec={
                "name": self._spec.name,
                "num_qubits": self._spec.num_qubits,
                "basis_gates": self._spec.basis_gates,
            },
            execution_mode=self._execution_mode,
            noise_applied=self._noise_applied,
            noise_config=self._noise_config,
        )
