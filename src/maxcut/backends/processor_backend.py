"""Hardware processor backend runner for Processor A and Processor B.

Encapsulates transpilation targeting organizer-specified coupling maps,
basis gates, and qubit properties. Emulates execution locally via Aer
without calling external physical hardware. Supports both ideal topology
emulation and authentic noise-aware simulation when official noise configurations
are supplied.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from qiskit.circuit import QuantumCircuit
from qiskit.transpiler import CouplingMap
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, ReadoutError, depolarizing_error, thermal_relaxation_error

from maxcut.backends.base import BackendExecutionResult, BaseBackendRunner
from maxcut.io import ProcessorHardwareSpec, load_processor_spec


class MissingNoiseConfigurationError(ValueError):
    """Raised when noisy simulation is requested but no official noise configuration exists."""
    pass


def build_noise_model(
    spec: ProcessorHardwareSpec,
    noise_config: Dict[str, Any],
) -> NoiseModel:
    """Constructs a Qiskit Aer NoiseModel strictly targeted to processor native gates and topology.

    Args:
        spec: ProcessorHardwareSpec containing native basis gates and coupling map.
        noise_config: Dictionary containing noise rates:
            - "single_qubit_error": float (depolarizing probability for 1Q gates)
            - "two_qubit_error": float (depolarizing probability for native 2Q gates)
            - "readout_error": Optional[float] (symmetric bitflip probability on measurement)

    Returns:
        NoiseModel: Configured Qiskit Aer NoiseModel.
    """
    noise_model = NoiseModel()
    p1 = float(noise_config.get("single_qubit_error", 0.0))
    p2 = float(noise_config.get("two_qubit_error", 0.0))
    pro = float(noise_config.get("readout_error", 0.0))

    one_q_gates = [g for g in spec.basis_gates if g in {"sx", "x", "id"}]
    two_q_gate_candidates = [g for g in spec.basis_gates if g in {"ecr", "cz", "cx"}]
    native_2q_gate = two_q_gate_candidates[0] if two_q_gate_candidates else None

    # Attach 1Q depolarizing error to compiled native single-qubit gates
    if p1 > 0.0 and one_q_gates:
        error_1q = depolarizing_error(p1, 1)
        for g in one_q_gates:
            noise_model.add_all_qubit_quantum_error(error_1q, g)

    # Attach 2Q depolarizing error specifically to the native 2Q entangler across coupling edges
    if p2 > 0.0 and native_2q_gate:
        error_2q = depolarizing_error(p2, 2)
        # Add error only along valid coupling map connections
        for u, v in spec.coupling_map:
            noise_model.add_quantum_error(error_2q, native_2q_gate, [u, v])

    # Attach readout error to measurement instructions across all valid physical qubits
    if pro > 0.0:
        ro_matrix = [[1.0 - pro, pro], [pro, 1.0 - pro]]
        readout_err = ReadoutError(ro_matrix)
        for q in range(spec.num_qubits):
            noise_model.add_readout_error(readout_err, [q])

    return noise_model


@dataclass(frozen=True)
class ProcessorExecutionResult(BackendExecutionResult):
    """Encapsulates execution outcome and hardware-specific compilation metrics."""

    swap_count: int = 0
    hardware_spec: Optional[Dict[str, Any]] = None
    explicit_swap_count: int = 0
    routing_swap_count: int = 0
    basis_synthesis_2q_gates: int = 0
    routing_2q_gates: int = 0
    execution_mode: str = "aer_hardware_topology_emulation"
    noise_applied: bool = False
    noise_config: Optional[Dict[str, Any]] = None


class ProcessorBackendRunner(BaseBackendRunner):
    """Manages transpilation and emulation targeting Processor A or Processor B."""

    def __init__(
        self,
        spec: Union[ProcessorHardwareSpec, str, Path],
        seed_simulator: int = 42,
        seed_transpiler: int = 42,
        execution_mode: str = "ideal",
        noise_config: Optional[Dict[str, Any]] = None,
        noise_model: Optional[NoiseModel] = None,
    ) -> None:
        if isinstance(spec, (str, Path)):
            self._spec = load_processor_spec(spec)
        else:
            self._spec = spec

        self.seed_simulator: int = seed_simulator
        self.seed_transpiler: int = seed_transpiler
        self._coupling_map = CouplingMap(self._spec.coupling_map)

        # Normalize execution mode
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
        """Returns the organizer hardware specification."""
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

    def run_circuit(
        self,
        circuit: QuantumCircuit,
        shots: int = 2048,
        optimization_level: int = 1,
    ) -> ProcessorExecutionResult:
        """Transpiles circuit strictly against processor constraints and emulates shots.

        Args:
            circuit: Bound QuantumCircuit ready for compilation and measurement.
            shots: Total number of measurement shots.
            optimization_level: Transpiler preset optimization level (1-3).

        Returns:
            ProcessorExecutionResult: Real architecture compilation metrics and sampled counts.
        """
        # Build preset pass manager using processor topology and native basis gates
        pass_manager = generate_preset_pass_manager(
            coupling_map=self._coupling_map,
            basis_gates=self._spec.basis_gates,
            optimization_level=optimization_level,
            seed_transpiler=self.seed_transpiler,
        )

        state = {"max_swaps": 0}

        def _transpile_cb(**kwargs: Any) -> None:
            dag = kwargs.get("dag")
            if dag and hasattr(dag, "count_ops"):
                swaps = int(dag.count_ops().get("swap", 0))
                if swaps >= state["max_swaps"] and swaps > 0:
                    state["max_swaps"] = swaps

        transpiled_qc = pass_manager.run(circuit, callback=_transpile_cb)

        # Count 2-qubit gates and SWAPs
        op_counts = transpiled_qc.count_ops()
        two_qubit_gate_names = {"cx", "ecr", "cz", "rzz", "swap"}
        two_q_count = sum(
            count for gate, count in op_counts.items() if gate in two_qubit_gate_names
        )
        explicit_swap_count = int(op_counts.get("swap", 0))
        logical_swaps = int(circuit.count_ops().get("swap", 0))
        routing_swap_count = max(0, state["max_swaps"] - logical_swaps)
        total_gate_count = sum(op_counts.values())
        depth = transpiled_qc.depth()

        # Dynamically determine 2Q cost per SWAP for this target backend without hardcoding
        swap_test = QuantumCircuit(2)
        swap_test.swap(0, 1)
        if getattr(pass_manager, "translation", None):
            trans_swap = pass_manager.translation.run(swap_test)
        else:
            trans_swap = pass_manager.run(swap_test)
        two_q_per_swap = sum(c for g, c in trans_swap.count_ops().items() if g in two_qubit_gate_names)

        routing_2q_gates = routing_swap_count * two_q_per_swap
        basis_synthesis_2q_gates = two_q_count - routing_2q_gates

        # Emulate execution on local Aer simulator (no external hardware calls)
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
        }

        return ProcessorExecutionResult(
            backend_name=self.backend_name,
            raw_counts=raw_counts,
            shots=shots,
            transpiled_circuit=transpiled_qc,
            transpiled_depth=depth,
            transpiled_2q_gates=two_q_count,
            transpiled_total_gates=total_gate_count,
            transpilation_level=optimization_level,
            backend_metadata={
                "target_type": self.target_type,
                "num_qubits": self.num_qubits,
                "basis_gates": self._spec.basis_gates,
                "coupling_edges_count": len(self._spec.coupling_map),
                "qubit_properties": self._spec.qubit_properties,
            },
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
