"""Backend adapter for Processor A (Falcon-H architecture, ECR native entangler).

Implements BaseBackendRunner to decouple the application from hardware-specific logic.
Provides architecture verification and metadata collection without submitting physical jobs.
"""

from pathlib import Path
from typing import Any, Dict, Optional

from qiskit.circuit import QuantumCircuit
from qiskit.transpiler import CouplingMap
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit_aer import AerSimulator

from maxcut.backends.base import BackendExecutionResult, BaseBackendRunner
from maxcut.backends.processor_backend import ProcessorExecutionResult
from maxcut.io import ProcessorHardwareSpec, load_processor_spec


class ProcessorABackend(BaseBackendRunner):
    """Adapter for official Processor A architecture definition."""

    SPEC_PATH = Path(__file__).resolve().parent / "hardware_spec.json"

    def __init__(
        self,
        spec_path: Optional[Path] = None,
        seed_simulator: int = 42,
        seed_transpiler: int = 42,
    ) -> None:
        target_path = spec_path or self.SPEC_PATH
        self._spec: ProcessorHardwareSpec = load_processor_spec(target_path)
        self.seed_simulator: int = seed_simulator
        self.seed_transpiler: int = seed_transpiler
        self._coupling_map = CouplingMap(self._spec.coupling_map)
        self._simulator = AerSimulator(seed_simulator=seed_simulator)

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
            "native_2q_gate": "ecr",
            "architecture_family": "Falcon-H",
            "spec_source": str(self.SPEC_PATH),
        }

    def verify_qaoa_circuit(
        self,
        circuit: QuantumCircuit,
        optimization_level: int = 1,
    ) -> Dict[str, Any]:
        """Verifies transpilation readiness, gate compliance, and routing overhead.

        Does NOT submit hardware jobs.

        Args:
            circuit: Bound or parameterized QAOA circuit.
            optimization_level: Transpiler optimization level (1-3).

        Returns:
            Dict[str, Any]: Compilation verification metrics.
        """
        pass_manager = generate_preset_pass_manager(
            coupling_map=self._coupling_map,
            basis_gates=self._spec.basis_gates,
            optimization_level=optimization_level,
            seed_transpiler=self.seed_transpiler,
        )

        transpiled_qc = pass_manager.run(circuit)
        op_counts = transpiled_qc.count_ops()

        # Check basis gate compliance (excluding layout barriers/measures)
        non_basis_gates = [
            gate for gate in op_counts
            if gate not in self._spec.basis_gates and gate not in {"barrier", "measure"}
        ]
        is_basis_compliant = (len(non_basis_gates) == 0)

        two_qubit_gate_names = {"cx", "ecr", "cz", "rzz", "swap"}
        two_q_count = sum(
            count for gate, count in op_counts.items() if gate in two_qubit_gate_names
        )

        return {
            "is_compilation_successful": True,
            "is_basis_compliant": is_basis_compliant,
            "non_basis_gates": non_basis_gates,
            "transpiled_depth": transpiled_qc.depth(),
            "transpiled_total_gates": sum(op_counts.values()),
            "transpiled_2q_gates": two_q_count,
            "ecr_gate_count": op_counts.get("ecr", 0),
            "swap_count": op_counts.get("swap", 0),
            "transpiled_qubit_count": transpiled_qc.num_qubits,
            "optimization_level": optimization_level,
        }

    def run_circuit(
        self,
        circuit: QuantumCircuit,
        shots: int = 2048,
        optimization_level: int = 1,
    ) -> ProcessorExecutionResult:
        """Transpiles circuit strictly against Processor A topology and emulates shots locally.

        Args:
            circuit: Bound QuantumCircuit ready for measurement.
            shots: Total measurement shots.
            optimization_level: Transpiler preset optimization level (1-3).

        Returns:
            ProcessorExecutionResult: Real architecture compilation metrics and sampled counts.
        """
        pass_manager = generate_preset_pass_manager(
            coupling_map=self._coupling_map,
            basis_gates=self._spec.basis_gates,
            optimization_level=optimization_level,
            seed_transpiler=self.seed_transpiler,
        )

        transpiled_qc = pass_manager.run(circuit)
        op_counts = transpiled_qc.count_ops()

        two_qubit_gate_names = {"cx", "ecr", "cz", "rzz", "swap"}
        two_q_count = sum(
            count for gate, count in op_counts.items() if gate in two_qubit_gate_names
        )
        swap_count = int(op_counts.get("swap", 0))

        # Local emulation on AerSimulator using the transpiled circuit
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
            "architecture_family": "Falcon-H",
            "native_2q_gate": "ecr",
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
            swap_count=swap_count,
            hardware_spec={
                "name": self._spec.name,
                "num_qubits": self._spec.num_qubits,
                "basis_gates": self._spec.basis_gates,
            },
        )
