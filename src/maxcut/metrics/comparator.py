"""Processor circuit comparison helper for Processor A and Processor B.

Executes strictly identical Qiskit transpilation passes on each processor target,
records empirical resource metrics, and exports machine-readable comparison tables.
Does NOT make unsupported causal claims or premature conclusions.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union

import pandas as pd
from qiskit.circuit import QuantumCircuit
from qiskit.transpiler import CouplingMap
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

from maxcut.backends.base import BaseBackendRunner
from maxcut.metrics.circuit_metrics import (
    CircuitResourceMetrics,
    extract_circuit_metrics,
)
from processors.processor_a import ProcessorABackend
from processors.processor_b import ProcessorBBackend


class ProcessorCircuitComparator:
    """Orchestrates identical transpilation of a logical circuit across Processor A and B."""

    def __init__(
        self,
        backend_a: Optional[BaseBackendRunner] = None,
        backend_b: Optional[BaseBackendRunner] = None,
        seed_transpiler: int = 42,
    ) -> None:
        self.backend_a: BaseBackendRunner = backend_a or ProcessorABackend(seed_transpiler=seed_transpiler)
        self.backend_b: BaseBackendRunner = backend_b or ProcessorBBackend(seed_transpiler=seed_transpiler)
        self.seed_transpiler: int = seed_transpiler
        self._results: List[CircuitResourceMetrics] = []

    def compare(
        self,
        logical_circuit: QuantumCircuit,
        optimization_levels: Sequence[int] = (1, 2, 3),
    ) -> List[CircuitResourceMetrics]:
        """Transpiles the exact same logical circuit across Processor A and B.

        Ensures 100% symmetric compilation configuration: identical pass manager,
        identical optimization levels, and identical transpiler random seed.

        Args:
            logical_circuit: Pre-compilation logical QuantumCircuit.
            optimization_levels: Sequence of optimization levels to sweep (e.g. [1, 2, 3]).

        Returns:
            List[CircuitResourceMetrics]: Resource metrics for each processor and level.
        """
        self._results.clear()

        backends = [self.backend_a, self.backend_b]

        for level in optimization_levels:
            for b in backends:
                coupling_map = CouplingMap(b.spec.coupling_map) if hasattr(b, "spec") else None
                basis_gates = list(b.spec.basis_gates) if hasattr(b, "spec") else None

                pass_manager = generate_preset_pass_manager(
                    coupling_map=coupling_map,
                    basis_gates=basis_gates,
                    optimization_level=level,
                    seed_transpiler=self.seed_transpiler,
                )

                transpiled_qc = pass_manager.run(logical_circuit)

                metrics = extract_circuit_metrics(
                    logical_circuit=logical_circuit,
                    transpiled_circuit=transpiled_qc,
                    backend_runner=b,
                    optimization_level=level,
                    seed_transpiler=self.seed_transpiler,
                )
                self._results.append(metrics)

        return list(self._results)

    def to_dict(self) -> List[Dict[str, Any]]:
        """Returns comparison records as a list of dictionaries."""
        return [r.to_dict() for r in self._results]

    def to_dataframe(self) -> pd.DataFrame:
        """Constructs a clean pandas DataFrame summarizing architectural comparison."""
        records = []
        for r in self._results:
            records.append({
                "Backend": r.backend_name,
                "Architecture": r.architecture_family,
                "Native 2Q": r.native_2q_gate,
                "Opt Level": r.optimization_level,
                "Logical Qubits": r.logical_qubit_count,
                "Physical Qubits": r.physical_qubit_count,
                "Logical Depth": r.logical_circuit_depth,
                "Transpiled Depth": r.transpiled_circuit_depth,
                "Depth Expansion": round(r.depth_expansion_ratio, 2),
                "Logical 2Q Gates": r.logical_2q_gates,
                "Transpiled 2Q Gates": r.transpiled_2q_gates,
                "2Q Overhead": r.two_qubit_gate_overhead,
                "Routing Ratio": round(r.routing_overhead_ratio, 2),
                "SWAP Count": r.swap_count,
                "Transpiled Total Gates": r.transpiled_total_gates,
            })
        return pd.DataFrame(records)

    def to_json(self, file_path: Union[str, Path], indent: int = 2) -> None:
        """Serializes comparison table to a JSON file."""
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=indent)

    def to_csv(self, file_path: Union[str, Path]) -> None:
        """Serializes comparison table to a CSV file."""
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        df = self.to_dataframe()
        df.to_csv(path, index=False)

    def to_markdown_table(self) -> str:
        """Formats the comparison as a clean GitHub-flavored markdown table."""
        df = self.to_dataframe()
        headers = list(df.columns)
        rows = df.values.tolist()

        header_line = "| " + " | ".join(str(h) for h in headers) + " |"
        separator_line = "| " + " | ".join("---" for _ in headers) + " |"
        row_lines = [
            "| " + " | ".join(str(val) for val in row) + " |" for row in rows
        ]
        return "\n".join([header_line, separator_line] + row_lines)
