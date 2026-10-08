"""Hardware processor backend runner for Processor A and Processor B.

Encapsulates transpilation targeting organizer-specified coupling maps,
basis gates, and qubit properties. Emulates execution locally via Aer
without calling external physical hardware.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from qiskit.circuit import QuantumCircuit
from qiskit.transpiler import CouplingMap
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit_aer import AerSimulator

from maxcut.backends.base import BackendExecutionResult, BaseBackendRunner
from maxcut.io import ProcessorHardwareSpec, load_processor_spec


@dataclass(frozen=True)
class ProcessorExecutionResult(BackendExecutionResult):
    """Encapsulates execution outcome and hardware-specific compilation metrics."""

    swap_count: int = 0
    hardware_spec: Optional[Dict[str, Any]] = None


class ProcessorBackendRunner(BaseBackendRunner):
    """Manages transpilation and emulation targeting Processor A or Processor B."""

    def __init__(
        self,
        spec: Union[ProcessorHardwareSpec, str, Path],
        seed_simulator: int = 42,
        seed_transpiler: int = 42,
    ) -> None:
        if isinstance(spec, (str, Path)):
            self._spec = load_processor_spec(spec)
        else:
            self._spec = spec

        self.seed_simulator: int = seed_simulator
        self.seed_transpiler: int = seed_transpiler
        self._coupling_map = CouplingMap(self._spec.coupling_map)
        self._simulator = AerSimulator(seed_simulator=seed_simulator)

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

        transpiled_qc = pass_manager.run(circuit)

        # Count 2-qubit gates and SWAPs
        op_counts = transpiled_qc.count_ops()
        two_qubit_gate_names = {"cx", "ecr", "cz", "rzz", "swap"}
        two_q_count = sum(
            count for gate, count in op_counts.items() if gate in two_qubit_gate_names
        )
        swap_count = int(op_counts.get("swap", 0))
        total_gate_count = sum(op_counts.values())
        depth = transpiled_qc.depth()

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
            "execution_mode": "aer_hardware_topology_emulation",
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
            swap_count=swap_count,
            hardware_spec={
                "name": self._spec.name,
                "num_qubits": self._spec.num_qubits,
                "basis_gates": self._spec.basis_gates,
            },
        )
