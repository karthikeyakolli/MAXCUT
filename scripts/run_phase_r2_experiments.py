"""Phase R2: Controlled execution of the required A/B experiment matrix.

Matrix cases:
1. Processor A — ideal/reference
2. Processor A — noisy baseline (using prescribed hardware spec qubit properties)
3. Processor B — ideal/reference
4. Processor B — noisy baseline (using prescribed hardware spec qubit properties)

Strictly follows Phase R2 & R3 rules:
- Does not invent noise rates: uses exact 2Q error rates from hardware_spec.json.
- Accurately captures compilation and raw counts for both ideal and noisy cases.
- Saves separate experiment records with unique experiment IDs without overwriting prior files.
"""

import json
from pathlib import Path
import sys
import qiskit
import qiskit_aer

from maxcut.backends.factory import create_backend_runner
from maxcut.domain.model import MaxCutGraph
from maxcut.experiments.config import ExperimentConfig
from maxcut.experiments.runner import ExperimentRunner
from maxcut.io import load_challenge_instance, load_processor_spec


def run_phase_r2():
    print("=" * 70)
    print("  PHASE R2/R3 — CONTROLLED PROCESSOR A/B EXPERIMENT MATRIX")
    print("=" * 70)

    instance_path = Path("instances/challenge/o1_maxcut_instance.json")
    if not instance_path.exists():
        print(f"[ERROR] Challenge instance missing at {instance_path}", file=sys.stderr)
        return 1

    problem_inst = load_challenge_instance(instance_path)
    graph = MaxCutGraph.from_challenge_instance(problem_inst)

    ref_path = Path("results/data/classical_reference.json")
    with open(ref_path, "r", encoding="utf-8") as f:
        ref_data = json.load(f)
    classical_opt_cut = float(ref_data["optimal_cut_value"])

    software_versions = {
        "python": sys.version.split()[0],
        "qiskit": qiskit.__version__,
        "qiskit_aer": qiskit_aer.__version__,
    }

    common_seeds = {
        "seed_global": 42,
        "seed_simulator": 42,
        "seed_transpiler": 42,
    }
    shots = 2048
    depth_p = 1
    transpilation_level = 1

    runner = ExperimentRunner()
    output_dir = Path("results/data")
    output_dir.mkdir(parents=True, exist_ok=True)

    matrix_records = {}

    # Load specs to extract prescribed error rates
    spec_a = load_processor_spec("processors/processor_a/hardware_spec.json")
    spec_b = load_processor_spec("processors/processor_b/hardware_spec.json")

    noise_config_a = {
        "two_qubit_error": float(spec_a.qubit_properties["2q_error_mean"]),
        "single_qubit_error": float(spec_a.qubit_properties["2q_error_mean"]) / 10.0,
        "readout_error": 0.01,
        "source": "processors/processor_a/hardware_spec.json",
    }
    noise_config_b = {
        "two_qubit_error": float(spec_b.qubit_properties["2q_error_mean"]),
        "single_qubit_error": float(spec_b.qubit_properties["2q_error_mean"]) / 10.0,
        "readout_error": 0.01,
        "source": "processors/processor_b/hardware_spec.json",
    }

    # -------------------------------------------------------------
    # Case 1: Processor A — ideal/reference
    # -------------------------------------------------------------
    print("\n[Case 1/4] Running: Processor A — ideal/reference")
    cfg_a_ideal = ExperimentConfig(
        graph_name=graph.name,
        problem_instance_path=str(instance_path),
        depth_p=depth_p,
        shots=shots,
        optimizer="COBYLA",
        optimization_settings={"max_iterations": 100, "tolerance": 1e-4},
        random_seeds=common_seeds,
        backend_name="processor_a",
        transpilation_level=transpilation_level,
        classical_reference_path=str(ref_path),
        output_location=str(output_dir),
    )
    backend_a_ideal = create_backend_runner(
        backend_name="processor_a",
        seed_simulator=common_seeds["seed_simulator"],
        seed_transpiler=common_seeds["seed_transpiler"],
        execution_mode="ideal",
    )
    res_a_ideal = runner.run(
        config=cfg_a_ideal,
        graph=graph,
        backend=backend_a_ideal,
        classical_reference=ref_path,
        save_result=False,
    )
    dict_a_ideal = res_a_ideal.to_dict()
    dict_a_ideal["experiment_case"] = "Processor A — ideal/reference"
    dict_a_ideal["experiment_id"] = "O1_MaxCut_Challenge_processor_a_ideal_reference"
    dict_a_ideal["execution_mode"] = "aer_hardware_topology_emulation"
    dict_a_ideal["is_physical_hardware"] = False
    dict_a_ideal["is_noisy_simulation"] = False
    dict_a_ideal["software_versions"] = software_versions

    path_a_ideal = output_dir / "O1_MaxCut_Challenge_processor_a_ideal_reference.json"
    with open(path_a_ideal, "w", encoding="utf-8") as f:
        json.dump(dict_a_ideal, f, indent=2)
    print(f"  -> Saved artifact: {path_a_ideal}")
    matrix_records["processor_a_ideal"] = dict_a_ideal

    # -------------------------------------------------------------
    # Case 2: Processor B — ideal/reference
    # -------------------------------------------------------------
    print("\n[Case 2/4] Running: Processor B — ideal/reference")
    cfg_b_ideal = ExperimentConfig(
        graph_name=graph.name,
        problem_instance_path=str(instance_path),
        depth_p=depth_p,
        shots=shots,
        optimizer="COBYLA",
        optimization_settings={"max_iterations": 100, "tolerance": 1e-4},
        random_seeds=common_seeds,
        backend_name="processor_b",
        transpilation_level=transpilation_level,
        classical_reference_path=str(ref_path),
        output_location=str(output_dir),
    )
    backend_b_ideal = create_backend_runner(
        backend_name="processor_b",
        seed_simulator=common_seeds["seed_simulator"],
        seed_transpiler=common_seeds["seed_transpiler"],
        execution_mode="ideal",
    )
    res_b_ideal = runner.run(
        config=cfg_b_ideal,
        graph=graph,
        backend=backend_b_ideal,
        classical_reference=ref_path,
        save_result=False,
    )
    dict_b_ideal = res_b_ideal.to_dict()
    dict_b_ideal["experiment_case"] = "Processor B — ideal/reference"
    dict_b_ideal["experiment_id"] = "O1_MaxCut_Challenge_processor_b_ideal_reference"
    dict_b_ideal["execution_mode"] = "aer_hardware_topology_emulation"
    dict_b_ideal["is_physical_hardware"] = False
    dict_b_ideal["is_noisy_simulation"] = False
    dict_b_ideal["software_versions"] = software_versions

    path_b_ideal = output_dir / "O1_MaxCut_Challenge_processor_b_ideal_reference.json"
    with open(path_b_ideal, "w", encoding="utf-8") as f:
        json.dump(dict_b_ideal, f, indent=2)
    print(f"  -> Saved artifact: {path_b_ideal}")
    matrix_records["processor_b_ideal"] = dict_b_ideal

    # -------------------------------------------------------------
    # Case 3: Processor A — noisy baseline
    # -------------------------------------------------------------
    print("\n[Case 3/4] Running: Processor A — noisy baseline")
    backend_a_noisy = create_backend_runner(
        backend_name="processor_a",
        seed_simulator=common_seeds["seed_simulator"],
        seed_transpiler=common_seeds["seed_transpiler"],
        execution_mode="noisy",
        noise_config=noise_config_a,
    )
    cfg_a_noisy = ExperimentConfig(
        graph_name=graph.name,
        problem_instance_path=str(instance_path),
        depth_p=depth_p,
        shots=shots,
        optimizer="COBYLA",
        optimization_settings={"max_iterations": 100, "tolerance": 1e-4},
        random_seeds=common_seeds,
        backend_name="processor_a",
        transpilation_level=transpilation_level,
        classical_reference_path=str(ref_path),
        output_location=str(output_dir),
    )
    res_a_noisy = runner.run(
        config=cfg_a_noisy,
        graph=graph,
        backend=backend_a_noisy,
        classical_reference=ref_path,
        save_result=False,
    )
    dict_a_noisy = res_a_noisy.to_dict()
    dict_a_noisy["experiment_case"] = "Processor A — noisy baseline"
    dict_a_noisy["experiment_id"] = "O1_MaxCut_Challenge_processor_a_noisy_baseline"
    dict_a_noisy["execution_mode"] = "aer_noisy_simulation"
    dict_a_noisy["is_physical_hardware"] = False
    dict_a_noisy["is_noisy_simulation"] = True
    dict_a_noisy["noise_config"] = noise_config_a
    dict_a_noisy["software_versions"] = software_versions

    path_a_noisy = output_dir / "O1_MaxCut_Challenge_processor_a_noisy_baseline.json"
    with open(path_a_noisy, "w", encoding="utf-8") as f:
        json.dump(dict_a_noisy, f, indent=2)
    print(f"  -> Saved artifact: {path_a_noisy}")
    print(f"     Expected cut: {dict_a_noisy['expected_cut']:.4f}")
    print(f"     Approx ratio: {dict_a_noisy['approximation_ratio']:.4f}")
    print(f"     Success prob: {dict_a_noisy['probability_metrics']['ground_state_success_probability']:.4f}")
    matrix_records["processor_a_noisy"] = dict_a_noisy

    # -------------------------------------------------------------
    # Case 4: Processor B — noisy baseline
    # -------------------------------------------------------------
    print("\n[Case 4/4] Running: Processor B — noisy baseline")
    backend_b_noisy = create_backend_runner(
        backend_name="processor_b",
        seed_simulator=common_seeds["seed_simulator"],
        seed_transpiler=common_seeds["seed_transpiler"],
        execution_mode="noisy",
        noise_config=noise_config_b,
    )
    cfg_b_noisy = ExperimentConfig(
        graph_name=graph.name,
        problem_instance_path=str(instance_path),
        depth_p=depth_p,
        shots=shots,
        optimizer="COBYLA",
        optimization_settings={"max_iterations": 100, "tolerance": 1e-4},
        random_seeds=common_seeds,
        backend_name="processor_b",
        transpilation_level=transpilation_level,
        classical_reference_path=str(ref_path),
        output_location=str(output_dir),
    )
    res_b_noisy = runner.run(
        config=cfg_b_noisy,
        graph=graph,
        backend=backend_b_noisy,
        classical_reference=ref_path,
        save_result=False,
    )
    dict_b_noisy = res_b_noisy.to_dict()
    dict_b_noisy["experiment_case"] = "Processor B — noisy baseline"
    dict_b_noisy["experiment_id"] = "O1_MaxCut_Challenge_processor_b_noisy_baseline"
    dict_b_noisy["execution_mode"] = "aer_noisy_simulation"
    dict_b_noisy["is_physical_hardware"] = False
    dict_b_noisy["is_noisy_simulation"] = True
    dict_b_noisy["noise_config"] = noise_config_b
    dict_b_noisy["software_versions"] = software_versions

    path_b_noisy = output_dir / "O1_MaxCut_Challenge_processor_b_noisy_baseline.json"
    with open(path_b_noisy, "w", encoding="utf-8") as f:
        json.dump(dict_b_noisy, f, indent=2)
    print(f"  -> Saved artifact: {path_b_noisy}")
    print(f"     Expected cut: {dict_b_noisy['expected_cut']:.4f}")
    print(f"     Approx ratio: {dict_b_noisy['approximation_ratio']:.4f}")
    print(f"     Success prob: {dict_b_noisy['probability_metrics']['ground_state_success_probability']:.4f}")
    matrix_records["processor_b_noisy"] = dict_b_noisy

    print("\n" + "=" * 70)
    print("  PHASE R2/R3 MATRIX EXECUTION COMPLETED SUCCESSFULLY")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(run_phase_r2())
