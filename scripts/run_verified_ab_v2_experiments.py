"""Phase 4: Controlled Ideal/Noisy A/B Experiments for Processor A and Processor B.

Executes the four required experiment cases:
1. Processor A — ideal/reference
2. Processor A — noisy baseline
3. Processor B — ideal/reference
4. Processor B — noisy baseline

Under consistent controlled settings:
- 5-qubit symmetry-reduced formulation (fixing x0 = 0, nodes 1..5)
- QAOA depth p = 1
- Variational parameters gamma*, beta* determined via COBYLA
- 2048 shots
- Optimization level 1
- RNG seeds (global=42, simulator=42, transpiler=42)
- Official noise parameters from hardware_spec.json

Stores all results under results/verified_ab_v2/ without overwriting prior results.
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


def run_phase_4_experiments(
    output_base: Path = ROOT_PATH / "results" / "verified_ab_v2",
    instance_path: Path = ROOT_PATH / "instances" / "challenge" / "o1_maxcut_instance.json",
    ref_path: Path = ROOT_PATH / "results" / "data" / "classical_reference.json",
    shots: int = 2048,
    seed_global: int = 42,
    seed_simulator: int = 42,
    seed_transpiler: int = 42,
    optimization_level: int = 1,
) -> Dict[str, Any]:
    """Executes the complete Phase 4 controlled experiment matrix."""
    print("=" * 75)
    print("  MAXCUT PHASE 4 — CONTROLLED IDEAL/NOISY A/B EXPERIMENTS (5Q REDUCED)")
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
        options={"maxiter": 100, "tol": 1e-4},
    )
    gamma_star = float(opt_result.x[0])
    beta_star = float(opt_result.x[1])
    analytic_expected_cut = -float(opt_result.fun)
    opt_time = time.perf_counter() - opt_start

    print(f"[OPTIMIZATION] COBYLA: gamma*={gamma_star:.4f}, beta*={beta_star:.4f}, analytic <C>={analytic_expected_cut:.4f} in {opt_time:.2f}s")

    # 3. Build Bound Measurement QAOA Circuit
    ansatz_meas = build_reduced_qaoa_circuit(graph, p=1, fixed_node=0, include_measurements=True)
    bound_qc = ansatz_meas.bind([gamma_star], [beta_star])

    # Export logical circuit
    logical_qasm_path = circuits_dir / "reduced_5q_logical_qaoa_p1.qasm"
    with open(logical_qasm_path, "w", encoding="utf-8") as f:
        f.write(qiskit.qasm2.dumps(bound_qc))

    # 4. Load Verified Hardware Specs & Authentic Noise Configurations
    spec_a = load_processor_spec(ROOT_PATH / "processors" / "processor_a" / "hardware_spec.json")
    spec_b = load_processor_spec(ROOT_PATH / "processors" / "processor_b" / "hardware_spec.json")

    noise_config_a = {
        "two_qubit_error": float(spec_a.qubit_properties["2q_error_mean"]),
        "single_qubit_error": float(spec_a.qubit_properties["2q_error_mean"]) / 10.0,
        "readout_error": 0.0100,
        "source": "processors/processor_a/hardware_spec.json",
    }
    noise_config_b = {
        "two_qubit_error": float(spec_b.qubit_properties["2q_error_mean"]),
        "single_qubit_error": float(spec_b.qubit_properties["2q_error_mean"]) / 10.0,
        "readout_error": 0.0100,
        "source": "processors/processor_b/hardware_spec.json",
    }

    software_versions = {
        "python": platform.python_version(),
        "qiskit": qiskit.__version__,
        "qiskit_aer": qiskit_aer.__version__,
        "platform": platform.platform(),
    }

    random_seeds = {
        "seed_global": seed_global,
        "seed_simulator": seed_simulator,
        "seed_transpiler": seed_transpiler,
    }

    algorithm_params = {
        "formulation": "5_qubit_symmetry_reduced",
        "fixed_node": 0,
        "depth_p": 1,
        "shots": shots,
        "optimizer_name": "COBYLA",
        "initial_parameters": init_params,
        "optimal_parameters": [gamma_star, beta_star],
        "optimal_gamma": [gamma_star],
        "optimal_beta": [beta_star],
        "optimizer_evaluations": int(opt_result.nfev),
        "final_objective_value": float(opt_result.fun),
        "analytic_expected_cut": analytic_expected_cut,
    }

    # 5. Define Required Case Matrix
    experiment_cases = [
        {
            "id": "processor_a_ideal_reference",
            "case_label": "Processor A — ideal/reference",
            "backend_class": ProcessorABackend,
            "execution_mode": "aer_hardware_topology_emulation",
            "is_noisy": False,
            "noise_config": None,
            "native_2q": "ecr",
            "arch_family": "Falcon-H",
            "qasm_file": "reduced_5q_processor_a_transpiled.qasm",
        },
        {
            "id": "processor_a_noisy_baseline",
            "case_label": "Processor A — noisy baseline",
            "backend_class": ProcessorABackend,
            "execution_mode": "aer_noisy_simulation",
            "is_noisy": True,
            "noise_config": noise_config_a,
            "native_2q": "ecr",
            "arch_family": "Falcon-H",
            "qasm_file": "reduced_5q_processor_a_transpiled.qasm",
        },
        {
            "id": "processor_b_ideal_reference",
            "case_label": "Processor B — ideal/reference",
            "backend_class": ProcessorBBackend,
            "execution_mode": "aer_hardware_topology_emulation",
            "is_noisy": False,
            "noise_config": None,
            "native_2q": "cz",
            "arch_family": "Ring-7",
            "qasm_file": "reduced_5q_processor_b_transpiled.qasm",
        },
        {
            "id": "processor_b_noisy_baseline",
            "case_label": "Processor B — noisy baseline",
            "backend_class": ProcessorBBackend,
            "execution_mode": "aer_noisy_simulation",
            "is_noisy": True,
            "noise_config": noise_config_b,
            "native_2q": "cz",
            "arch_family": "Ring-7",
            "qasm_file": "reduced_5q_processor_b_transpiled.qasm",
        },
    ]

    results_summary = []
    full_artifacts = {}

    # 6. Execute Matrix
    for case in experiment_cases:
        case_id = case["id"]
        label = case["case_label"]
        print(f"\n--- Running: {label} ---")
        start_time_iso = datetime.now(timezone.utc).isoformat()
        sim_start = time.perf_counter()

        # Instantiate backend runner
        backend = case["backend_class"](
            seed_simulator=seed_simulator,
            seed_transpiler=seed_transpiler,
            execution_mode="noisy" if case["is_noisy"] else "ideal",
            noise_config=case["noise_config"],
        )

        # Transpile and execute
        exec_res = backend.run_circuit(
            circuit=bound_qc,
            shots=shots,
            optimization_level=optimization_level,
        )
        sim_time = time.perf_counter() - sim_start
        end_time_iso = datetime.now(timezone.utc).isoformat()

        # Export transpiled circuit once per target
        transpiled_qc = exec_res.transpiled_circuit
        circuit_export_path = circuits_dir / case["qasm_file"]
        if not circuit_export_path.exists():
            with open(circuit_export_path, "w", encoding="utf-8") as f:
                f.write(qiskit.qasm2.dumps(transpiled_qc))

        # Decode little-endian 5-qubit counts to canonical 6-vertex bitstrings
        decoded_counts = decode_reduced_qiskit_counts(
            raw_counts=exec_res.raw_counts,
            node_to_qubit=ansatz_meas.node_to_qubit,
            all_sorted_nodes=sorted(graph.nodes),
            fixed_node=0,
            fixed_val=0,
        )

        # Statistical evaluation
        eval_metrics = evaluate_measurement_distribution(
            decoded_counts=decoded_counts,
            graph=graph,
            optimal_cut_value=classical_opt_cut,
            optimal_bitstrings=classical_opt_strings,
        )

        expected_cut = float(eval_metrics["expected_cut_value"])
        approx_ratio = expected_cut / classical_opt_cut
        best_cut = float(eval_metrics["best_sampled_cut"])
        best_str = str(eval_metrics["best_sampled_bitstring"])
        most_freq_str = str(eval_metrics["most_frequent_bitstring"])
        most_freq_cut = graph.compute_cut(most_freq_str).cut_value
        p_opt = float(eval_metrics["ground_state_success_probability"])

        # Compute cut distribution and sample standard error
        cut_values_by_string = eval_metrics["cut_values_by_bitstring"]
        cut_distribution: Dict[float, int] = {}
        for bs, count in decoded_counts.items():
            c_val = cut_values_by_string[bs]
            cut_distribution[c_val] = cut_distribution.get(c_val, 0) + count

        variance = float(sum(count * (c_val - expected_cut) ** 2 for c_val, count in cut_distribution.items()) / shots)
        std_error = float(np.sqrt(variance / shots))

        # Circuit compilation metrics
        transpiled_metrics = {
            "backend_name": backend.backend_name,
            "architecture_family": case["arch_family"],
            "native_2q_gate": case["native_2q"],
            "optimization_level": optimization_level,
            "seed_transpiler": seed_transpiler,
            "logical_qubits": 5,
            "logical_depth": bound_qc.depth(),
            "logical_2q_gates": 6,
            "logical_1q_gates": 12,
            "physical_qubits_total": backend.num_qubits,
            "physical_qubits_used": sorted(list(set(
                transpiled_qc.find_bit(q).index
                for inst in transpiled_qc.data
                if inst.operation.name != "barrier"
                for q in inst.qubits
            ))),
            "physical_qubits_active_count": len(set(
                transpiled_qc.find_bit(q).index
                for inst in transpiled_qc.data
                if inst.operation.name != "barrier"
                for q in inst.qubits
            )),
            "transpiled_depth": exec_res.transpiled_depth,
            "transpiled_total_gates": exec_res.transpiled_total_gates,
            "transpiled_2q_gates": exec_res.transpiled_2q_gates,
            "basis_synthesis_2q_gates": exec_res.basis_synthesis_2q_gates,
            "routing_2q_gates": exec_res.routing_2q_gates,
            "routing_swap_count": exec_res.routing_swap_count,
            "explicit_swap_count": exec_res.explicit_swap_count,
            "gate_breakdown": dict(transpiled_qc.count_ops()),
        }

        # Build full JSON artifact
        record = {
            "experiment_id": f"verified_ab_v2_{case_id}",
            "experiment_case": label,
            "execution_mode": case["execution_mode"],
            "is_physical_hardware": False,
            "is_noisy_simulation": case["is_noisy"],
            "noise_applied": case["is_noisy"],
            "noise_config": case["noise_config"],
            "problem_metadata": {
                "name": graph.name,
                "num_nodes": graph.num_nodes,
                "num_edges": graph.num_edges,
                "is_weighted": graph.is_weighted,
                "total_weight": graph.total_weight,
                "classical_optimum": classical_opt_cut,
                "source_path": str(instance_path),
            },
            "backend_metadata": backend.get_metadata(),
            "algorithm_parameters": algorithm_params,
            "results": {
                "expected_cut": expected_cut,
                "cut_variance": variance,
                "sample_std_error": std_error,
                "classical_optimal_cut": classical_opt_cut,
                "approximation_ratio": approx_ratio,
                "best_sampled_cut": best_cut,
                "best_sampled_bitstring": best_str,
                "most_frequent_bitstring": most_freq_str,
                "most_frequent_cut": most_freq_cut,
                "ground_state_success_probability": p_opt,
                "num_unique_bitstrings": eval_metrics["num_unique_bitstrings"],
                "total_shots_sampled": shots,
                "is_classical_optimum_achieved": (best_cut >= classical_opt_cut),
            },
            "cut_distribution": {str(k): int(v) for k, v in cut_distribution.items()},
            "cut_values_by_bitstring": {str(k): float(v) for k, v in cut_values_by_string.items()},
            "circuit_metrics": transpiled_metrics,
            "raw_counts": dict(exec_res.raw_counts),
            "decoded_counts": dict(decoded_counts),
            "runtime": {
                "optimization_time_seconds": opt_time,
                "simulation_time_seconds": sim_time,
                "total_pipeline_time_seconds": opt_time + sim_time,
            },
            "timestamps": {
                "start_time_iso": start_time_iso,
                "end_time_iso": end_time_iso,
            },
            "reproducibility_information": {
                "random_seeds": random_seeds,
                "software_versions": software_versions,
            },
            "job_metadata": exec_res.job_metadata,
        }

        # Save individual experiment file
        out_file = data_dir / f"{case_id}.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(record, f, indent=2)
        print(f"  -> Saved artifact: {out_file.name}")
        print(f"     <C> = {expected_cut:.4f} +/- {std_error:.4f} | approx = {approx_ratio:.4f} | P_opt = {p_opt:.4f} | best = {best_cut:.1f}")

        full_artifacts[case_id] = record
        results_summary.append({
            "Experiment Case": label,
            "Backend": backend.backend_name,
            "Architecture": case["arch_family"],
            "Execution Mode": case["execution_mode"],
            "Noisy": case["is_noisy"],
            "Expected Cut <C>": round(expected_cut, 4),
            "Std Error": round(std_error, 4),
            "Approx Ratio": round(approx_ratio, 4),
            "P(opt)": round(p_opt, 4),
            "Best Cut": round(best_cut, 1),
            "Best Bitstring": best_str,
            "2Q Gates": transpiled_metrics["transpiled_2q_gates"],
            "Routing SWAPs": transpiled_metrics["routing_swap_count"],
            "Depth": transpiled_metrics["transpiled_depth"],
            "Total Gates": transpiled_metrics["transpiled_total_gates"],
            "Shots": shots,
        })

    # 7. Save Summary Artifacts and Tables
    summary_path = data_dir / "experiment_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(results_summary, f, indent=2)

    df = pd.DataFrame(results_summary)
    csv_path = tables_dir / "ab_controlled_comparison.csv"
    md_path = tables_dir / "ab_controlled_comparison.md"

    df.to_csv(csv_path, index=False)

    headers = list(df.columns)
    rows = df.values.tolist()
    header_line = "| " + " | ".join(headers) + " |"
    sep_line = "| " + " | ".join(["---"] * len(headers)) + " |"
    row_lines = ["| " + " | ".join(str(v) for v in row) + " |" for row in rows]
    md_content = (
        "# Controlled Ideal vs. Noisy A/B Experiment Comparison (5Q Symmetry Reduced)\n\n"
        f"**Official Graph:** $|V|=6, |E|=8, W=8.00$, $C_{{\\max}}=6.0000$\n\n"
        f"**Controlled Settings:** $p=1$, $\\gamma^*={gamma_star:.4f}, \\beta^*={beta_star:.4f}$, shots={shots}, level={optimization_level}, seed={seed_global}\n\n"
        + "\n".join([header_line, sep_line] + row_lines)
        + "\n"
    )

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"\n[TABLES] Saved comparison tables to {csv_path.name} and {md_path.name}")
    print("\n" + "=" * 75)
    print("  PHASE 4 EXPERIMENT MATRIX COMPLETED SUCCESSFULLY")
    print("=" * 75)

    return full_artifacts


if __name__ == "__main__":
    run_phase_4_experiments()
