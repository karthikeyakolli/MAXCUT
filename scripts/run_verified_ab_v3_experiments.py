"""Phase 4 & Architecture Correction Rebuild: Controlled Ideal/Noisy A/B Experiments (Version 3).

Executes the four required experiment cases:
1. Processor A — ideal/reference (5 physical qubits, baseline T-tree)
2. Processor A — noisy baseline (5 physical qubits, baseline T-tree, synthetic noise)
3. Processor B — ideal/reference (7 physical qubits, heavy-hex-inspired baseline)
4. Processor B — noisy baseline (7 physical qubits, heavy-hex-inspired baseline, synthetic noise)

Under consistent controlled settings:
- 5-qubit symmetry-reduced formulation (fixing x0 = 0, nodes 1..5)
- QAOA depth p = 1
- Shared optimal variational parameters gamma*, beta* determined via COBYLA
- 2048 shots across all cases
- Optimization level 1
- RNG seeds (global=42, simulator=42, transpiler=42)
- Explicit provisional noise parameters from hardware_spec.json

Stores all results cleanly under results/verified_ab_v3/ without mixing into v2 historical data.
"""

from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import sys
import time
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
import qiskit
import qiskit.qasm2
import qiskit_aer
from qiskit.quantum_info import Statevector
from scipy.optimize import minimize

# Ensure src/ and repo root are on sys.path
ROOT_PATH = Path(__file__).resolve().parent.parent
SRC_PATH = ROOT_PATH / "src"
for p in [str(ROOT_PATH), str(SRC_PATH)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from maxcut.domain.model import MaxCutGraph
from maxcut.formulation.qubo import build_reduced_cost_hamiltonian
from maxcut.io import load_challenge_instance, load_processor_spec
from maxcut.qaoa.ansatz import build_reduced_qaoa_circuit
from maxcut.qaoa.decoding import decode_reduced_qiskit_counts, evaluate_measurement_distribution
from processors.processor_a.adapter import ProcessorABackend
from processors.processor_b.adapter import ProcessorBBackend


def run_phase_4_experiments_v3(
    output_base: Path = ROOT_PATH / "results" / "verified_ab_v3",
    instance_path: Path = ROOT_PATH / "instances" / "challenge" / "o1_maxcut_instance.json",
    ref_path: Path = ROOT_PATH / "results" / "data" / "classical_reference.json",
    shots: int = 2048,
    seed_global: int = 42,
    seed_simulator: int = 42,
    seed_transpiler: int = 42,
    optimization_level: int = 1,
) -> Dict[str, Any]:
    """Executes the complete Version 3 controlled experiment matrix."""
    print("=" * 75)
    print("  MAXCUT VERSION 3 — CONTROLLED IDEAL/NOISY A/B EXPERIMENTS (5Q A vs 7Q B)")
    print("=" * 75)

    data_dir = output_base / "data"
    circuits_dir = output_base / "circuits"
    tables_dir = output_base / "tables"

    data_dir.mkdir(parents=True, exist_ok=True)
    circuits_dir.mkdir(parents=True, exist_ok=True)
    tables_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load Problem Instance and Classical Reference
    problem_inst = load_challenge_instance(instance_path)
    graph = MaxCutGraph.from_challenge_instance(problem_inst)
    print(f"[INSTANCE] Loaded {graph.name}: |V|={graph.num_nodes}, |E|={graph.num_edges}, W={graph.total_weight:.2f}")

    with open(ref_path, "r", encoding="utf-8") as f:
        ref_data = json.load(f)
    classical_opt_cut = float(ref_data["optimal_cut_value"])
    classical_opt_strings = list(ref_data["optimal_bitstrings"])
    print(f"[GROUND TRUTH] Classical Optimum: C_max = {classical_opt_cut:.4f} ({len(classical_opt_strings)} optimal bitstrings)")

    # 2. Build 5-Qubit Reduced Cost Hamiltonian & Optimize Parameters via COBYLA
    opt_start = time.perf_counter()
    ansatz_opt = build_reduced_qaoa_circuit(graph, p=1, fixed_node=0, include_measurements=False)
    h_cost = build_reduced_cost_hamiltonian(graph, fixed_node=0, include_offset=True)

    def objective(params: Tuple[float, float]) -> float:
        qc = ansatz_opt.bind([params[0]], [params[1]])
        sv = Statevector.from_instruction(qc)
        return float(sv.expectation_value(h_cost.cost_operator).real)

    rng = np.random.RandomState(seed_global)
    init_params = [float(rng.uniform(0.0, 2.0 * np.pi)), float(rng.uniform(0.0, np.pi))]
    opt_result = minimize(
        objective,
        init_params,
        method="COBYLA",
        options={"maxiter": 200, "rhobeg": 0.5, "tol": 1e-4},
    )
    opt_duration = time.perf_counter() - opt_start

    optimal_gamma = float(opt_result.x[0])
    optimal_beta = float(opt_result.x[1])
    analytic_min_val = float(opt_result.fun)
    analytic_exp_cut = -analytic_min_val
    analytic_approx_ratio = analytic_exp_cut / classical_opt_cut

    print(f"[OPTIMIZATION] Converged in {opt_result.nfev} evals ({opt_duration:.3f}s)")
    print(f"  gamma* = {optimal_gamma:.6f} rad, beta* = {optimal_beta:.6f} rad")
    print(f"  Analytic <C> = {analytic_exp_cut:.6f}, alpha = {analytic_approx_ratio:.4f} ({analytic_approx_ratio*100:.2f}%)")

    # 3. Construct Bound 5-Qubit QAOA Circuit with Measurements
    ansatz_exec = build_reduced_qaoa_circuit(graph, p=1, fixed_node=0, include_measurements=True)
    bound_circuit = ansatz_exec.bind([optimal_gamma], [optimal_beta])

    # 4. Load Hardware Specifications
    spec_a = load_processor_spec(ROOT_PATH / "processors" / "processor_a" / "hardware_spec.json")
    spec_b = load_processor_spec(ROOT_PATH / "processors" / "processor_b" / "hardware_spec.json")

    # Define provisional noise configurations from specifications
    noise_cfg_a = {
        "single_qubit_error": float(spec_a.qubit_properties.get("1q_error_mean", 0.0005)),
        "two_qubit_error": float(spec_a.qubit_properties.get("2q_error_mean", 0.0075)),
        "readout_error": float(spec_a.qubit_properties.get("readout_error_mean", 0.015)),
        "source": "processors/processor_a/hardware_spec.json",
        "provenance_status": "PROVISIONAL — ORGANIZER CONFIRMATION REQUIRED",
    }
    noise_cfg_b = {
        "single_qubit_error": float(spec_b.qubit_properties.get("1q_error_mean", 0.0003)),
        "two_qubit_error": float(spec_b.qubit_properties.get("2q_error_mean", 0.0050)),
        "readout_error": float(spec_b.qubit_properties.get("readout_error_mean", 0.010)),
        "source": "processors/processor_b/hardware_spec.json",
        "provenance_status": "PROVISIONAL — ORGANIZER CONFIRMATION REQUIRED",
    }

    # 5. Define the 4 Required Experiment Cases
    experiment_cases = [
        {
            "id": "verified_ab_v3_processor_a_ideal_reference",
            "key": "processor_a_ideal_reference",
            "name": "Processor A — ideal/reference",
            "backend_class": ProcessorABackend,
            "backend_name": "Processor_A",
            "spec": spec_a,
            "architecture_family": "5Q-Baseline-Tree",
            "backend_physical_qubits": 5,
            "execution_mode": "ideal",
            "noisy": False,
            "noise_cfg": None,
            "count_file": "counts_processor_a_ideal.json",
        },
        {
            "id": "verified_ab_v3_processor_a_noisy_baseline",
            "key": "processor_a_noisy_baseline",
            "name": "Processor A — noisy baseline",
            "backend_class": ProcessorABackend,
            "backend_name": "Processor_A",
            "spec": spec_a,
            "architecture_family": "5Q-Baseline-Tree",
            "backend_physical_qubits": 5,
            "execution_mode": "noisy",
            "noisy": True,
            "noise_cfg": noise_cfg_a,
            "count_file": "counts_processor_a_noisy.json",
        },
        {
            "id": "verified_ab_v3_processor_b_ideal_reference",
            "key": "processor_b_ideal_reference",
            "name": "Processor B — ideal/reference",
            "backend_class": ProcessorBBackend,
            "backend_name": "Processor_B",
            "spec": spec_b,
            "architecture_family": "Heavy-Hex-7",
            "backend_physical_qubits": 7,
            "execution_mode": "ideal",
            "noisy": False,
            "noise_cfg": None,
            "count_file": "counts_processor_b_ideal.json",
        },
        {
            "id": "verified_ab_v3_processor_b_noisy_baseline",
            "key": "processor_b_noisy_baseline",
            "name": "Processor B — noisy baseline",
            "backend_class": ProcessorBBackend,
            "backend_name": "Processor_B",
            "spec": spec_b,
            "architecture_family": "Heavy-Hex-7",
            "backend_physical_qubits": 7,
            "execution_mode": "noisy",
            "noisy": True,
            "noise_cfg": noise_cfg_b,
            "count_file": "counts_processor_b_noisy.json",
        },
    ]

    results_summary = []
    case_data_records = {}

    # 6. Execute Each Case Under Controlled Conditions
    for case in experiment_cases:
        cid = case["id"]
        cname = case["name"]
        print(f"\n[RUNNING] {cname} (Mode: {case['execution_mode']}, Backend Qubits: {case['backend_physical_qubits']})...")

        backend = case["backend_class"](
            seed_simulator=seed_simulator,
            seed_transpiler=seed_transpiler,
            execution_mode=case["execution_mode"],
            noise_config=case["noise_cfg"],
        )

        sim_start = time.perf_counter()
        exec_result = backend.run_circuit(
            bound_circuit,
            shots=shots,
            optimization_level=optimization_level,
        )
        sim_duration = time.perf_counter() - sim_start

        # Transpiled circuit metrics
        trans_qc, trans_metrics = backend.transpile_circuit(
            bound_circuit, optimization_level=optimization_level
        )
        raw_counts = exec_result.raw_counts
        total_shots = sum(raw_counts.values())
        assert total_shots == shots, f"Shot mismatch: got {total_shots}, expected {shots}"

        # Save raw measurement counts in results/verified_ab_v3/
        count_path = output_base / case["count_file"]
        with open(count_path, "w", encoding="utf-8") as f:
            json.dump(raw_counts, f, indent=2, sort_keys=True)
        print(f"  -> Saved raw counts to {count_path.name} (Total shots = {total_shots})")

        # Save transpiled QASM artifact
        qasm_path = circuits_dir / f"{case['key']}_transpiled.qasm"
        with open(qasm_path, "w", encoding="utf-8") as f:
            f.write(qiskit.qasm2.dumps(trans_qc))

        # Decode reduced 5-qubit bitstrings back to canonical 6-vertex assignments
        decoded_counts = decode_reduced_qiskit_counts(
            raw_counts,
            node_to_qubit=ansatz_exec.node_to_qubit,
            all_sorted_nodes=sorted(graph.nodes),
            fixed_node=0,
            fixed_val=0,
        )

        # Evaluate cut distribution on original graph
        eval_metrics = evaluate_measurement_distribution(
            decoded_counts,
            graph,
            optimal_cut_value=classical_opt_cut,
            optimal_bitstrings=classical_opt_strings,
        )
        mean_cut = float(eval_metrics["expected_cut_value"])
        approx_ratio = float(eval_metrics["approximation_ratio"])
        p_opt = float(eval_metrics["ground_state_success_probability"])

        # Calculate sample variance and std_error
        var_cut = sum(
            count * (eval_metrics["cut_values_by_bitstring"][bs] - mean_cut) ** 2
            for bs, count in decoded_counts.items()
        ) / (total_shots - 1)
        std_error = float(np.sqrt(var_cut / total_shots))

        cut_distribution = {}
        for bs, count in decoded_counts.items():
            cval = eval_metrics["cut_values_by_bitstring"][bs]
            cut_distribution[str(cval)] = cut_distribution.get(str(cval), 0) + count

        # Collect physical qubit mapping data
        used_physical_qubits = trans_metrics["physical_qubits_used"]
        physical_qubit_count = len(used_physical_qubits)

        print(f"  -> Physical Qubits Used: {used_physical_qubits} (Active: {physical_qubit_count}/{case['backend_physical_qubits']})")
        print(f"  -> Depth: {trans_metrics['transpiled_depth']}, 2Q Gates: {trans_metrics['transpiled_2q_gates']} ({trans_metrics['basis_synthesis_2q_gates']} basis + {trans_metrics['routing_2q_gates']} routing), SWAPs: {trans_metrics['routing_swap_count']}")
        print(f"  -> Mean Cut <C>: {mean_cut:.4f} +/- {std_error:.4f} (SE), Approx Ratio: {approx_ratio:.4f}")
        print(f"  -> P(opt): {p_opt:.4f} ({p_opt*100:.2f}%), Best Cut: {eval_metrics['best_sampled_cut']:.1f}")

        # Construct comprehensive metadata record
        case_record = {
            "experiment_id": cid,
            "experiment_case": cname,
            "execution_mode": backend.execution_mode,
            "is_physical_hardware": False,
            "is_noisy_simulation": case["noisy"],
            "noise_applied": backend.noise_applied,
            "noise_config": case["noise_cfg"],
            "problem_metadata": {
                "name": graph.name,
                "num_nodes": graph.num_nodes,
                "num_edges": graph.num_edges,
                "is_weighted": graph.is_weighted,
                "total_weight": graph.total_weight,
                "classical_optimum": classical_opt_cut,
                "source_path": str(instance_path),
            },
            "backend_metadata": {
                "backend_name": backend.backend_name,
                "target_type": backend.target_type,
                "backend_physical_qubits": case["backend_physical_qubits"],
                "active_physical_qubits_count": physical_qubit_count,
                "active_physical_qubits": used_physical_qubits,
                "logical_circuit_width": 5,
                "basis_gates": list(case["spec"].basis_gates),
                "coupling_map": list(case["spec"].coupling_map),
                "coupling_edge_count": len(case["spec"].coupling_map),
                "qubit_properties": dict(case["spec"].qubit_properties),
                "native_2q_gate": trans_metrics.get("native_2q_gate", case["spec"].metadata.get("native_2q_gate", "ecr")),
                "architecture_family": case["architecture_family"],
                "spec_source": str(ROOT_PATH / "processors" / case["spec"].name.lower() / "hardware_spec.json"),
                "execution_mode": backend.execution_mode,
                "noise_applied": backend.noise_applied,
                "provenance_status": case["spec"].metadata.get("status", "PROVISIONAL — ORGANIZER CONFIRMATION REQUIRED"),
            },
            "algorithm_parameters": {
                "formulation": "5_qubit_symmetry_reduced",
                "fixed_node": 0,
                "depth_p": 1,
                "shots": shots,
                "optimizer_name": "COBYLA",
                "initial_parameters": init_params,
                "optimal_parameters": [optimal_gamma, optimal_beta],
                "optimal_gamma": [optimal_gamma],
                "optimal_beta": [optimal_beta],
                "optimizer_evaluations": int(opt_result.nfev),
                "final_objective_value": analytic_min_val,
                "analytic_expected_cut": analytic_exp_cut,
            },
            "results": {
                "expected_cut": mean_cut,
                "cut_variance": float(var_cut),
                "sample_std_error": std_error,
                "classical_optimal_cut": classical_opt_cut,
                "approximation_ratio": approx_ratio,
                "best_sampled_cut": float(eval_metrics["best_sampled_cut"]),
                "best_sampled_bitstring": eval_metrics["best_sampled_bitstring"],
                "most_frequent_bitstring": eval_metrics["most_frequent_bitstring"],
                "ground_state_success_probability": p_opt,
                "num_unique_bitstrings": eval_metrics["num_unique_bitstrings"],
                "total_shots_sampled": total_shots,
                "is_classical_optimum_achieved": (eval_metrics["best_sampled_cut"] == classical_opt_cut),
            },
            "cut_distribution": cut_distribution,
            "circuit_compilation_metrics": {
                "logical_qubits": 5,
                "backend_physical_qubits": case["backend_physical_qubits"],
                "active_physical_qubits_used": used_physical_qubits,
                "active_physical_qubits_count": physical_qubit_count,
                "transpiled_depth": trans_metrics["transpiled_depth"],
                "transpiled_total_gates": trans_metrics["transpiled_total_gates"],
                "transpiled_2q_gates": trans_metrics["transpiled_2q_gates"],
                "basis_synthesis_2q_gates": trans_metrics["basis_synthesis_2q_gates"],
                "routing_2q_gates": trans_metrics["routing_2q_gates"],
                "routing_swap_count": trans_metrics["routing_swap_count"],
                "gate_breakdown": trans_metrics["gate_breakdown"],
                "initial_layout": trans_metrics["initial_layout"],
                "final_layout": trans_metrics["final_layout"],
                "optimization_level": optimization_level,
            },
            "raw_counts": raw_counts,
            "decoded_counts": decoded_counts,
            "execution_metadata": {
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "simulation_duration_seconds": sim_duration,
                "platform": platform.platform(),
                "python_version": sys.version,
                "qiskit_version": qiskit.__version__,
                "qiskit_aer_version": qiskit_aer.__version__,
                "seed_simulator": seed_simulator,
                "seed_transpiler": seed_transpiler,
                "seed_global": seed_global,
            },
        }

        # Save individual experiment record
        record_file = data_dir / f"{case['key']}.json"
        with open(record_file, "w", encoding="utf-8") as f:
            json.dump(case_record, f, indent=2)

        case_data_records[case["key"]] = case_record

        # Append row for summary table
        summary_rows = {
            "Experiment Case": cname,
            "Target Backend": case["backend_name"],
            "Architecture Family": case["architecture_family"],
            "Backend Physical Qubits": case["backend_physical_qubits"],
            "Active Physical Qubits": physical_qubit_count,
            "Mapped Qubits": str(used_physical_qubits),
            "Execution Mode": backend.execution_mode,
            "Noisy": case["noisy"],
            "Circuit Depth": trans_metrics["transpiled_depth"],
            "Total Gates": trans_metrics["transpiled_total_gates"],
            "Native 2Q Gate": case["spec"].basis_gates[-1],
            "Total 2Q Count": trans_metrics["transpiled_2q_gates"],
            "Basis 2Q Count": trans_metrics["basis_synthesis_2q_gates"],
            "Routing 2Q Overhead": trans_metrics["routing_2q_gates"],
            "Routing SWAPs": trans_metrics["routing_swap_count"],
            "Mean Cut <C>": round(mean_cut, 4),
            "Std Error": round(std_error, 4),
            "Approx Ratio": round(approx_ratio, 4),
            "Success Prob P(opt)": round(p_opt, 4),
            "Shots": total_shots,
            "Sim Time (s)": round(sim_duration, 3),
        }
        results_summary.append(summary_rows)

    # 7. Export High-Level Summary Artifacts
    summary_df = pd.DataFrame(results_summary)
    summary_csv = tables_dir / "performance_comparison_v3.csv"
    summary_md = tables_dir / "performance_comparison_v3.md"
    summary_df.to_csv(summary_csv, index=False)

    md_headers = list(summary_df.columns)
    md_lines = [
        "# Version 3 Controlled A/B Experiment Performance Comparison\n",
        "Evaluation across corrected Processor A (5 physical qubits) and Processor B (7 physical qubits heavy-hex) under controlled settings.\n",
        "| " + " | ".join(md_headers) + " |",
        "| " + " | ".join(["---"] * len(md_headers)) + " |",
    ]
    for _, row in summary_df.iterrows():
        md_lines.append("| " + " | ".join(str(row[col]) for col in md_headers) + " |")
    md_lines.append("")

    with open(summary_md, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    summary_json_path = data_dir / "experiment_summary.json"
    with open(summary_json_path, "w", encoding="utf-8") as f:
        json.dump({
            "version": "v3",
            "execution_date_utc": datetime.now(timezone.utc).isoformat(),
            "problem_instance": graph.name,
            "c_max": classical_opt_cut,
            "shots_per_case": shots,
            "summary": results_summary,
        }, f, indent=2)

    print(f"\n[COMPLETE] All 4 Version 3 experiment cases executed successfully!")
    print(f"  Artifacts saved under: {output_base}")
    return case_data_records


if __name__ == "__main__":
    run_phase_4_experiments_v3()
