"""Executes the validated Max-Cut QAOA workflow on Processor A and Processor B.

Maintains identical experimental controls across all targets:
- Official problem instance (instances/challenge/o1_maxcut_instance.json)
- QAOA depth p = 1
- Optimizer: COBYLA (max_iterations=100, tol=1e-4)
- Shots: 2048
- Seeds: seed_global=42, seed_simulator=42, seed_transpiler=42
- Transpilation level: 1
- Canonical node order bitstring decoding
- Verified classical ground truth reference

Clearly distinguishes:
1. Simulator result: O1_MaxCut_Challenge_aer_simulator_p1_result.json
2. Processor A result: O1_MaxCut_Challenge_processor_a_p1_result.json
3. Processor B result: O1_MaxCut_Challenge_processor_b_p1_result.json
"""

import json
from pathlib import Path
import sys

from maxcut.backends.factory import create_backend_runner
from maxcut.domain.model import MaxCutGraph
from maxcut.experiments.config import ExperimentConfig
from maxcut.experiments.runner import ExperimentRunner
from maxcut.experiments.schema import ExperimentResult, load_experiment_result
from maxcut.io import load_challenge_instance


def main() -> int:
    print("======================================================================")
    print("  MAX-CUT QAOA EXPERIMENT EXECUTION: PROCESSOR A & PROCESSOR B")
    print("======================================================================")

    # 1. Ingest official Challenge Kit problem instance
    instance_path = Path("instances/challenge/o1_maxcut_instance.json")
    if not instance_path.exists():
        print(f"Error: Official problem instance not found at {instance_path}", file=sys.stderr)
        return 1

    problem_inst = load_challenge_instance(instance_path)
    graph = MaxCutGraph.from_challenge_instance(problem_inst)
    print(f"Problem Instance: {graph.name} (|V|={graph.num_nodes}, |E|={graph.num_edges}, W={graph.total_weight:.2f})")

    # 2. Ingest classical reference ground truth
    ref_path = Path("results/data/classical_reference.json")
    if not ref_path.exists():
        print(f"Error: Classical reference not found at {ref_path}", file=sys.stderr)
        return 1

    with open(ref_path, "r", encoding="utf-8") as f:
        ref_data = json.load(f)
    classical_opt_cut = float(ref_data["optimal_cut_value"])
    print(f"Classical Ground Truth Optimum: C_max = {classical_opt_cut:.4f}\n")

    # 3. Common experiment controls across all executions
    common_seeds = {
        "seed_global": 42,
        "seed_simulator": 42,
        "seed_transpiler": 42,
    }
    shots = 2048
    depth_p = 1
    transpilation_level = 1

    runner = ExperimentRunner()
    targets = [
        ("aer_simulator", "Ideal Aer Simulator"),
        ("processor_a", "Processor A (Falcon-H, ECR native)"),
        ("processor_b", "Processor B (Ring-7, CZ native)"),
    ]

    results = {}

    for backend_id, display_name in targets:
        print(f"--- Running Execution: {display_name} ---")
        cfg = ExperimentConfig(
            graph_name=graph.name,
            problem_instance_path=str(instance_path),
            depth_p=depth_p,
            shots=shots,
            optimizer="COBYLA",
            optimization_settings={"max_iterations": 100, "tolerance": 1e-4},
            random_seeds=common_seeds,
            backend_name=backend_id,
            transpilation_level=transpilation_level,
            classical_reference_path=str(ref_path),
            output_location="results/data",
        )

        backend = create_backend_runner(
            backend_name=backend_id,
            seed_simulator=common_seeds["seed_simulator"],
            seed_transpiler=common_seeds["seed_transpiler"],
        )

        res = runner.run(
            config=cfg,
            graph=graph,
            backend=backend,
            classical_reference=ref_path,
            save_result=True,
        )

        results[backend_id] = res

        print(f"  Target Type:         {res.backend_metadata.get('target_type')}")
        print(f"  Backend Name:        {res.backend_metadata.get('backend_name')}")
        print(f"  Job ID:              {res.job_metadata.get('job_id')}")
        print(f"  Transpiled Depth:    {res.circuit_metrics.get('transpiled_circuit_depth')}")
        print(f"  Transpiled 2Q Gates: {res.circuit_metrics.get('transpiled_2q_gates')}")
        print(f"  SWAP Count:          {res.circuit_metrics.get('swap_count')}")
        print(f"  Best Measured Cut:   {res.cut_value:.4f} (Optimal: {res.is_classical_optimum_achieved})")
        print(f"  Expected Cut <C>:    {res.expected_cut:.4f}")
        print(f"  Approximation Ratio: {res.approximation_ratio:.4f} ({res.approximation_ratio * 100:.2f}%)")
        print(f"  Success Probability: {res.probability_metrics.get('ground_state_success_probability', 0.0):.4f}")
        print()

    # 4. Generate summary comparative table
    print("======================================================================")
    print("  EXPERIMENT SUMMARY COMPARISON TABLE")
    print("======================================================================")
    header = (
        f"{'Target':<15} | {'Native 2Q':<10} | {'Depth':<6} | {'2Q Gates':<8} | "
        f"{'SWAPs':<6} | {'Best Cut':<9} | {'<C>':<7} | {'Approx Ratio':<12} | {'P(opt)':<8}"
    )
    print(header)
    print("-" * len(header))

    for backend_id, _ in targets:
        res = results[backend_id]
        bname = res.backend_metadata.get("backend_name", backend_id)
        native_2q = res.backend_metadata.get("native_2q_gate", "cx")
        c_depth = res.circuit_metrics.get("transpiled_circuit_depth", 0)
        two_q = res.circuit_metrics.get("transpiled_2q_gates", 0)
        swaps = res.circuit_metrics.get("swap_count", 0)
        best_c = res.cut_value
        exp_c = res.expected_cut
        ar = res.approximation_ratio or 0.0
        p_opt = res.probability_metrics.get("ground_state_success_probability", 0.0)

        print(
            f"{bname:<15} | {native_2q:<10} | {c_depth:<6} | {two_q:<8} | "
            f"{swaps:<6} | {best_c:<9.4f} | {exp_c:<7.4f} | {ar:<12.4f} | {p_opt:<8.4f}"
        )

    print("======================================================================")
    print("  Artifact Files Successfully Generated:")
    print("  - Simulator:   results/data/O1_MaxCut_Challenge_aer_simulator_p1_result.json")
    print("  - Processor A: results/data/O1_MaxCut_Challenge_processor_a_p1_result.json")
    print("  - Processor B: results/data/O1_MaxCut_Challenge_processor_b_p1_result.json")
    print("======================================================================")

    return 0


if __name__ == "__main__":
    sys.exit(main())
