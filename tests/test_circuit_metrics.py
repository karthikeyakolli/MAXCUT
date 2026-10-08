"""Unit and integration tests for Processor A/B circuit resource analysis layer."""

import json
from pathlib import Path
import tempfile
import unittest

from qiskit.circuit import QuantumCircuit

from maxcut.domain.model import MaxCutGraph
from maxcut.metrics.circuit_metrics import (
    CircuitResourceMetrics,
    extract_circuit_metrics,
)
from maxcut.metrics.comparator import ProcessorCircuitComparator
from maxcut.qaoa.ansatz import build_qaoa_circuit
from processors.processor_a import ProcessorABackend
from processors.processor_b import ProcessorBBackend


class TestCircuitMetricsAnalysis(unittest.TestCase):
    """Test suite for circuit resource extraction and Processor A/B comparator."""

    def setUp(self):
        # 4-node cycle graph (0-1-2-3-0)
        self.c4_graph = MaxCutGraph(
            name="C4_Test",
            nodes=[0, 1, 2, 3],
            edges=[(0, 1, 1.0), (1, 2, 1.0), (2, 3, 1.0), (3, 0, 1.0)],
        )
        self.logical_qc = build_qaoa_circuit(self.c4_graph, p=1, include_measurements=True).bind([0.5], [1.0])

        self.proc_a = ProcessorABackend(seed_transpiler=42)
        self.proc_b = ProcessorBBackend(seed_transpiler=42)

    def test_circuit_resource_metrics_extraction(self):
        """Verify extraction of all logical, transpiled, gate, and routing overhead metrics."""
        transpiled_qc = self.proc_a.run_circuit(self.logical_qc, shots=100, optimization_level=1).transpiled_circuit
        metrics = extract_circuit_metrics(
            logical_circuit=self.logical_qc,
            transpiled_circuit=transpiled_qc,
            backend_runner=self.proc_a,
            optimization_level=1,
            seed_transpiler=42,
        )

        self.assertIsInstance(metrics, CircuitResourceMetrics)
        self.assertEqual(metrics.backend_name, "Processor_A")
        self.assertEqual(metrics.logical_qubit_count, 4)
        self.assertEqual(metrics.physical_qubit_count, 7)
        self.assertGreater(metrics.logical_circuit_depth, 0)
        self.assertGreater(metrics.transpiled_circuit_depth, 0)
        self.assertGreater(metrics.transpiled_2q_gates, 0)
        self.assertGreaterEqual(metrics.swap_count, 0)
        self.assertGreaterEqual(metrics.two_qubit_gate_overhead, 0)
        self.assertGreaterEqual(metrics.routing_overhead_ratio, 1.0)
        self.assertGreaterEqual(metrics.depth_expansion_ratio, 1.0)
        self.assertIn("ecr", metrics.gate_breakdown)
        self.assertEqual(metrics.native_2q_gate, "ecr")

    def test_comparator_symmetric_compilation(self):
        """Verify that comparator evaluates Processor A and B under strictly symmetric settings."""
        comparator = ProcessorCircuitComparator(
            backend_a=self.proc_a,
            backend_b=self.proc_b,
            seed_transpiler=42,
        )

        results = comparator.compare(self.logical_qc, optimization_levels=[1, 2])
        self.assertEqual(len(results), 4)  # 2 backends * 2 levels

        # Check optimization level pairing
        levels = [r.optimization_level for r in results]
        self.assertEqual(levels, [1, 1, 2, 2])
        backend_names = [r.backend_name for r in results]
        self.assertEqual(backend_names, ["Processor_A", "Processor_B", "Processor_A", "Processor_B"])

        # Check that both used seed 42
        for r in results:
            self.assertEqual(r.seed_transpiler, 42)

    def test_machine_readable_exports(self):
        """Verify export to DataFrame, JSON, CSV, and Markdown table formats."""
        comparator = ProcessorCircuitComparator(
            backend_a=self.proc_a,
            backend_b=self.proc_b,
            seed_transpiler=42,
        )
        comparator.compare(self.logical_qc, optimization_levels=[1])

        # 1. DataFrame export
        df = comparator.to_dataframe()
        self.assertEqual(len(df), 2)
        self.assertIn("Transpiled Depth", df.columns)
        self.assertIn("Routing Ratio", df.columns)
        self.assertIn("SWAP Count", df.columns)

        # 2. Markdown export
        md_table = comparator.to_markdown_table()
        self.assertIn("| Backend |", md_table)
        self.assertIn("Processor_A", md_table)
        self.assertIn("Processor_B", md_table)

        # 3. JSON and CSV file export
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f_json:
            json_path = f_json.name
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as f_csv:
            csv_path = f_csv.name

        try:
            comparator.to_json(json_path)
            comparator.to_csv(csv_path)

            with open(json_path, "r", encoding="utf-8") as f:
                loaded_json = json.load(f)
            self.assertEqual(len(loaded_json), 2)
            self.assertEqual(loaded_json[0]["backend_name"], "Processor_A")
            self.assertEqual(loaded_json[1]["backend_name"], "Processor_B")

            with open(csv_path, "r", encoding="utf-8") as f:
                csv_content = f.read()
            self.assertIn("Processor_A", csv_content)
            self.assertIn("Processor_B", csv_content)
        finally:
            Path(json_path).unlink(missing_ok=True)
            Path(csv_path).unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
