"""Qiskit Aer backend runner and transpilation manager.

Provides reproducible local shot-based and statevector simulation workflows
using current Qiskit 2.x transpiler pass managers and AerSimulator.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from qiskit.circuit import QuantumCircuit
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit_aer import AerSimulator

from maxcut.backends.base import BackendExecutionResult, BaseBackendRunner


@dataclass(frozen=True)
class AerExecutionResult(BackendExecutionResult):
    """Encapsulates raw execution and transpilation metrics from Qiskit Aer."""

    seed_simulator: int = 42
    seed_transpiler: int = 42


class AerBackendRunner(BaseBackendRunner):
    """Executes quantum circuits on local Qiskit Aer with strict seed reproducibility."""

    def __init__(
        self,
        seed_simulator: int = 42,
        seed_transpiler: int = 42,
        backend_name: str = "aer_simulator",
    ) -> None:
        self._backend_name: str = backend_name
        self.seed_simulator: int = seed_simulator
        self.seed_transpiler: int = seed_transpiler
        self._simulator: AerSimulator = AerSimulator(seed_simulator=seed_simulator)

    @property
    def backend_name(self) -> str:
        return self._backend_name

    @property
    def target_type(self) -> str:
        return "simulator"

    @property
    def num_qubits(self) -> int:
        try:
            return self._simulator.configuration().n_qubits
        except Exception:
            return 32

    @property
    def simulator(self) -> AerSimulator:
        """Returns the underlying AerSimulator instance."""
        return self._simulator

    def run_circuit(
        self,
        circuit: QuantumCircuit,
        shots: int = 2048,
        optimization_level: int = 1,
    ) -> AerExecutionResult:
        """Transpiles and executes a circuit on AerSimulator.

        Args:
            circuit: Bound QuantumCircuit ready for measurement.
            shots: Number of measurement shots.
            optimization_level: Transpiler preset optimization level (0 to 3).

        Returns:
            AerExecutionResult: Output counts and hardware-level compilation metrics.
        """
        # Build preset pass manager targeting AerSimulator
        pass_manager = generate_preset_pass_manager(
            backend=self._simulator,
            optimization_level=optimization_level,
            seed_transpiler=self.seed_transpiler,
        )

        transpiled_qc = pass_manager.run(circuit)

        # Count 2-qubit entangling gates (cx, ecr, cz, rzz)
        two_qubit_gate_names = {"cx", "ecr", "cz", "rzz", "swap"}
        op_counts = transpiled_qc.count_ops()
        two_q_count = sum(
            count for gate, count in op_counts.items() if gate in two_qubit_gate_names
        )
        total_gate_count = sum(op_counts.values())
        depth = transpiled_qc.depth()

        # Execute on Aer
        job = self._simulator.run(transpiled_qc, shots=shots)
        result = job.result()
        raw_counts = result.get_counts()

        job_metadata = {
            "job_id": job.job_id(),
            "status": str(job.status()),
            "shots": shots,
            "seed_simulator": self.seed_simulator,
            "seed_transpiler": self.seed_transpiler,
            "execution_mode": "qiskit_aer_simulator",
            "backend_name": self._backend_name,
        }

        return AerExecutionResult(
            backend_name=self._backend_name,
            raw_counts=raw_counts,
            shots=shots,
            transpiled_circuit=transpiled_qc,
            transpiled_depth=depth,
            transpiled_2q_gates=two_q_count,
            transpiled_total_gates=total_gate_count,
            transpilation_level=optimization_level,
            backend_metadata={
                "seed_simulator": self.seed_simulator,
                "seed_transpiler": self.seed_transpiler,
                "target_type": self.target_type,
            },
            job_metadata=job_metadata,
            seed_simulator=self.seed_simulator,
            seed_transpiler=self.seed_transpiler,
        )
