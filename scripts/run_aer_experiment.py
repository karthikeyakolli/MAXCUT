"""CLI entry point to execute the end-to-end QAOA Aer experiment.

Orchestrates:
Official Challenge Kit instance -> Ising formulation -> QAOA ansatz ->
Classical parameter optimization -> Qiskit Aer simulation -> Decoded bitstrings ->
Solution evaluation -> Ground truth comparison -> Metric & plot export.
"""

import argparse
import json
from pathlib import Path
import sys

# Ensure src/ is on sys.path
SRC_PATH = Path(__file__).resolve().parent.parent / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from maxcut.classical import ExactExhaustiveSolver
from maxcut.domain import MaxCutGraph
from maxcut.experiments import QAOAAerExperiment
from maxcut.io import load_challenge_instance
from maxcut.visualization import plot_measurement_distribution


def main():
    parser = argparse.ArgumentParser(
        description="Run end-to-end QAOA simulation on Qiskit Aer."
    )
    parser.add_argument(
        "--config",
        type=str,
        default="configs/experiment.json",
        help="Path to experiment configuration JSON.",
    )
    parser.add_argument(
        "--depth",
        type=int,
        default=None,
        help="QAOA depth p (overrides config if set).",
    )
    parser.add_argument(
        "--shots",
        type=int,
        default=None,
        help="Number of measurement shots (overrides config if set).",
    )
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.exists():
        print(f"[ERROR] Config not found at '{config_path}'.")
        sys.exit(1)

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    # 1. Load problem instance
    instance_path = Path(config["challenge"]["instance_path"])
    if not instance_path.exists():
        print(f"[ERROR] Official problem instance not found at: {instance_path.resolve()}")
        sys.exit(1)

    print(f"[1/6] Ingesting official Challenge Kit instance: {instance_path.name}")
    problem_instance = load_challenge_instance(instance_path)
    graph = MaxCutGraph.from_challenge_instance(problem_instance)
    print(f"      Graph: {graph.num_nodes} nodes, {graph.num_edges} edges, Total Weight: {graph.total_weight:.1f}")

    # 2. Check / compute classical reference
    classical_ref_path = Path("results/data/classical_reference.json")
    if not classical_ref_path.exists():
        print("[2/6] Classical reference not found; running exact exhaustive solver...")
        classical_solver = ExactExhaustiveSolver(record_distribution=True)
        classical_res = classical_solver.solve(graph)
        classical_res.to_json(classical_ref_path)
        print(f"      Ground truth optimum C_max = {classical_res.optimal_cut_value:.1f} saved.")
    else:
        print(f"[2/6] Loaded classical reference ground truth from: {classical_ref_path.resolve()}")
        with open(classical_ref_path, "r", encoding="utf-8") as f:
            ref_data = json.load(f)
        print(f"      Ground truth optimum C_max = {ref_data.get('optimal_cut_value'):.1f}")

    # 3. Configure experiment parameters
    p = args.depth if args.depth is not None else config["qaoa"]["depth_p"][0]  # default to p=1 or user arg
    shots = args.shots if args.shots is not None else config["execution"]["shots"]
    seeds = config.get("reproducibility", {})
    seed_global = seeds.get("seed_global", 42)
    seed_sim = seeds.get("seed_simulator", 42)
    seed_trans = seeds.get("seed_transpiler", 42)
    optimizer_name = config["qaoa"].get("optimizer", "COBYLA")
    max_iter = config["qaoa"].get("max_iterations", 100)
    tol = config["qaoa"].get("tolerance", 1e-4)

    print(f"[3/6] Setting up QAOA on Qiskit Aer (p={p}, shots={shots}, optimizer={optimizer_name}, seed={seed_global})...")
    experiment = QAOAAerExperiment(
        seed_global=seed_global,
        seed_simulator=seed_sim,
        seed_transpiler=seed_trans,
    )

    # 4. Execute pipeline
    print("[4/6] Executing parameter optimization & Aer simulation...")
    result = experiment.run(
        graph=graph,
        depth_p=p,
        shots=shots,
        optimizer_name=optimizer_name,
        maxiter=max_iter,
        tol=tol,
        transpilation_level=1,
        classical_reference=classical_ref_path,
    )

    # 5. Serialize results
    results_dir = Path("results/data")
    results_dir.mkdir(parents=True, exist_ok=True)
    out_file = results_dir / "qaoa_aer_results.json"
    result.to_json(out_file)
    print(f"[5/6] Serialized experiment results to: {out_file.resolve()}")

    # 6. Generate and save probability distribution figure
    figures_dir = Path("results/figures")
    figures_dir.mkdir(parents=True, exist_ok=True)
    plot_file = figures_dir / "qaoa_aer_distribution.png"
    plot_measurement_distribution(
        decoded_counts=result.decoded_counts,
        graph=graph,
        classical_optimal_cut=result.classical_optimal_cut,
        classical_optimal_bitstrings=result.classical_optimal_bitstrings,
        top_k=16,
        save_path=plot_file,
    )
    print(f"[6/6] Saved probability distribution plot to: {plot_file.resolve()}")

    # Print executive summary
    print("\n" + result.summary() + "\n")


if __name__ == "__main__":
    main()
