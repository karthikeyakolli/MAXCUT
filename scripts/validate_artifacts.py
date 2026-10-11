"""Validates presence and schema integrity of all required configuration, result, table, and figure artifacts."""

import json
from pathlib import Path
import nbformat


def validate_artifacts():
    print("[1/4] Checking required configuration and hardware specifications...")
    required_configs = [
        Path("instances/challenge/o1_maxcut_instance.json"),
        Path("processors/processor_a/hardware_spec.json"),
        Path("processors/processor_b/hardware_spec.json"),
        Path("data/hardware_specs/processor_a.json"),
        Path("data/hardware_specs/processor_b.json"),
    ]
    for p in required_configs:
        assert p.exists(), f"Missing configuration artifact: {p}"
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
            assert isinstance(data, dict), f"Config file {p} is not a valid JSON dict"
    print(f"  -> All {len(required_configs)} configuration files verified.")

    print("[2/4] Checking required result data artifacts...")
    required_results = [
        Path("results/data/classical_reference.json"),
        Path("results/data/processor_a_circuit_metrics.json"),
        Path("results/data/processor_b_circuit_metrics.json"),
        Path("results/data/processor_comparison_table.json"),
        Path("results/data/processor_comparison_table.csv"),
        Path("results/data/O1_MaxCut_Challenge_processor_a_ideal_reference.json"),
        Path("results/data/O1_MaxCut_Challenge_processor_b_ideal_reference.json"),
        Path("results/data/O1_MaxCut_Challenge_processor_a_noisy_baseline.json"),
        Path("results/data/O1_MaxCut_Challenge_processor_b_noisy_baseline.json"),
        Path("results/data/noise_benchmark_summary.json"),
    ]
    for p in required_results:
        assert p.exists(), f"Missing result artifact: {p}"
        assert p.stat().st_size > 0, f"Result file {p} is empty"
        if p.suffix == ".json":
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
                assert isinstance(data, (dict, list)), f"JSON file {p} does not contain valid dict or list"
    print(f"  -> All {len(required_results)} result data files verified.")

    print("[3/4] Checking required tables and publication figures...")
    required_tables = [
        Path("results/tables/processor_comparison_table.md"),
        Path("results/tables/gate_level_breakdown.md"),
        Path("results/tables/compilation_comparison_opt1_2_3.md"),
        Path("results/tables/statistical_uncertainty_table.md"),
        Path("results/tables/noise_aware_comparison_table.md"),
        Path("results/tables/noise_statistical_uncertainty_table.md"),
        Path("results/verified_ab_v3/tables/table1_circuit_compilation_breakdown.md"),
        Path("results/verified_ab_v3/tables/table2_performance_comparison.md"),
        Path("results/verified_ab_v3/tables/table3_statistical_hypothesis_tests.md"),
        Path("results/verified_ab_v3/tables/statistical_uncertainty_table.md"),
        Path("results/verified_ab_v3/tables/pairwise_comparisons_table.md"),
        Path("results/verified_ab_v3/tables/resource_vs_quality_table.md"),
    ]
    for p in required_tables:
        assert p.exists(), f"Missing table artifact: {p}"
        assert p.stat().st_size > 0, f"Table file {p} is empty"

    required_figures = [
        Path("results/figures/figure1_cut_distribution_comparison.png"),
        Path("results/figures/figure2_circuit_resource_comparison.png"),
        Path("results/figures/figure3_solution_quality_comparison.png"),
        Path("results/figures/figure4_compilation_overhead_breakdown.png"),
        Path("results/figures/figure5_topology_qubit_mapping.png"),
        Path("results/figures/figure6_ideal_vs_noisy_comparison.png"),
        Path("results/verified_ab_v3/figures/figure1_sampling_distribution.png"),
        Path("results/verified_ab_v3/figures/figure2_compilation_overhead_breakdown.png"),
        Path("results/verified_ab_v3/figures/figure3_metric_confidence_intervals.png"),
    ]
    for p in required_figures:
        assert p.exists(), f"Missing figure artifact: {p}"
        assert p.stat().st_size > 1000, f"Figure file {p} is suspiciously small ({p.stat().st_size} bytes)"
    print(f"  -> All {len(required_tables)} tables and {len(required_figures)} publication figures verified.")

    print("[4/4] Validating pre-rendered notebook execution and cell completeness...")
    nb_path = Path("main.ipynb")
    assert nb_path.exists(), "main.ipynb does not exist"
    with open(nb_path, "r", encoding="utf-8") as f:
        nb = nbformat.read(f, as_version=4)

    code_cells = [cell for cell in nb.cells if cell.cell_type == "code"]
    assert len(code_cells) >= 10, f"Expected at least 10 code cells, found {len(code_cells)}"

    for idx, cell in enumerate(code_cells):
        assert cell.execution_count is not None, f"Code cell {idx} has unexecuted execution_count: null"
        assert len(cell.outputs) > 0, f"Code cell {idx} has empty outputs list"

    print(f"  -> Validated {len(code_cells)} pre-rendered code cells in main.ipynb.")
    print("\n[SUCCESS] All required configuration, result, table, figure, and notebook artifacts are verified!")


if __name__ == "__main__":
    validate_artifacts()
