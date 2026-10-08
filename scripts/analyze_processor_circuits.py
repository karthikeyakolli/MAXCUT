"""CLI script to analyze and compare QAOA circuit compilation on Processor A and Processor B.

Extracts hardware-level resource metrics (depth, 2Q gates, SWAP overheads)
across optimization levels 1, 2, and 3 using current Qiskit transpilation APIs.
Generates machine-readable output files in results/data/.
"""

import json
from pathlib import Path
import sys

# Ensure src/ and repo root are on sys.path
ROOT_PATH = Path(__file__).resolve().parent.parent
SRC_PATH = ROOT_PATH / "src"
for p in [str(ROOT_PATH), str(SRC_PATH)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from maxcut.domain import MaxCutGraph
from maxcut.io import load_challenge_instance
from maxcut.metrics import ProcessorCircuitComparator
from maxcut.qaoa import build_qaoa_circuit
from processors.processor_a import ProcessorABackend
from processors.processor_b import ProcessorBBackend


def main():
    print("=" * 75)
    print("  PROCESSOR A & B CIRCUIT RESOURCE ANALYSIS (QAOA MAX-CUT)")
    print("=" * 75)

    # 1. Ingest official Challenge Kit instance
    instance_path = Path("instances/challenge/o1_maxcut_instance.json")
    if not instance_path.exists():
        print(f"[ERROR] Problem instance not found at: {instance_path.resolve()}")
        sys.exit(1)

    instance = load_challenge_instance(instance_path)
    graph = MaxCutGraph.from_challenge_instance(instance)
    print(f"Problem Instance: {graph.name} (|V|={graph.num_nodes}, |E|={graph.num_edges})")

    # 2. Build logical QAOA circuit (p=1, nominal/optimal angles)
    ansatz = build_qaoa_circuit(graph, p=1, include_measurements=True)
    # Using optimal parameters found in simulator run for concrete representation
    bound_qc = ansatz.bind(gamma_values=[2.4835], beta_values=[4.2540])

    print(f"Logical QAOA Circuit: {bound_qc.num_qubits} qubits, depth={bound_qc.depth()}, ops={dict(bound_qc.count_ops())}")

    # 3. Instantiate backends
    proc_a = ProcessorABackend(seed_transpiler=42)
    proc_b = ProcessorBBackend(seed_transpiler=42)

    comparator = ProcessorCircuitComparator(backend_a=proc_a, backend_b=proc_b, seed_transpiler=42)

    # 4. Execute symmetric transpilation across optimization levels 1, 2, 3
    print("\n[TRANSPILING] Running symmetric compilation across optimization levels [1, 2, 3] (seed=42)...")
    results = comparator.compare(bound_qc, optimization_levels=[1, 2, 3])

    # 5. Partition machine-readable outputs for Processor A and B
    results_dir = Path("results/data")
    results_dir.mkdir(parents=True, exist_ok=True)

    metrics_a = [r.to_dict() for r in results if r.backend_name == "Processor_A"]
    metrics_b = [r.to_dict() for r in results if r.backend_name == "Processor_B"]

    file_a = results_dir / "processor_a_circuit_metrics.json"
    file_b = results_dir / "processor_b_circuit_metrics.json"
    file_comp_json = results_dir / "processor_comparison_table.json"
    file_comp_csv = results_dir / "processor_comparison_table.csv"

    with open(file_a, "w", encoding="utf-8") as f:
        json.dump(metrics_a, f, indent=2)
    with open(file_b, "w", encoding="utf-8") as f:
        json.dump(metrics_b, f, indent=2)

    comparator.to_json(file_comp_json)
    comparator.to_csv(file_comp_csv)

    print(f"[SAVED] Processor A metrics: {file_a.resolve()}")
    print(f"[SAVED] Processor B metrics: {file_b.resolve()}")
    print(f"[SAVED] Unified comparison table JSON: {file_comp_json.resolve()}")
    print(f"[SAVED] Unified comparison table CSV:  {file_comp_csv.resolve()}")

    # 6. Display machine-readable markdown table
    print("\n--- COMPILED RESOURCE METRICS COMPARISON TABLE ---")
    print(comparator.to_markdown_table())
    print("\n[NOTE]: Empirical compilation metrics collected. No causal conclusions drawn at this stage.")


if __name__ == "__main__":
    main()
