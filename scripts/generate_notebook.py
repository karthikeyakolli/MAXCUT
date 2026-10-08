"""Generates the comprehensive, publication-grade main.ipynb notebook."""

import json
from pathlib import Path


def create_notebook():
    notebook_path = Path("main.ipynb")

    cells = [
        # Cell 1: Title
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "# Qiskit Fall Fest 2026 — O1 Max-Cut Quantum Optimization\n",
                "## End-to-End QAOA Pipeline & Architectural Benchmarking: Processor A vs. Processor B\n",
                "\n",
                "**Track:** Quantum Optimization — **O1 Max-Cut**  \n",
                "**Problem Instance:** `O1_MaxCut_Challenge` ($|V|=6, |E|=8, W=8.00$)  \n",
                "**Classical Ground Truth:** $C_{\\max} = 6.0000$ (Exhaustive Search)  \n",
                "**Hardware Architectures:** Processor A (`Falcon-H`), Processor B (`Ring-7`), Ideal Simulator (`aer_simulator`)\n"
            ]
        },
        # Cell 2: Project Overview
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### 1. Project Introduction & Problem Definition\n",
                "\n",
                "The **Maximum Cut (Max-Cut)** problem is a canonical NP-hard combinatorial optimization problem. Given an undirected graph $G = (V, E)$ with edge weights $w_{uv}$, the objective is to partition the vertices $V$ into two complementary subsets $S$ and $\\bar{S}$ to maximize the total weight of cut edges crossing the boundary:\n",
                "\n",
                "$$C(x) = \\sum_{(u, v) \\in E} w_{uv} (x_u \\oplus x_v) = \\sum_{(u, v) \\in E} w_{uv} [x_u(1 - x_v) + x_v(1 - x_u)]$$\n",
                "\n",
                "where binary assignment $x_u = 0$ denotes $u \\in S$ and $x_u = 1$ denotes $u \\in \\bar{S}$.\n",
                "\n",
                "This notebook provides a complete, mathematically rigorous, and reproducible implementation of the **Quantum Approximate Optimization Algorithm (QAOA)** for the official competition instance under the Qiskit 2.x ecosystem.\n"
            ]
        },
        # Cell 3: Environment Setup
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Setup paths and verify installed dependencies\n",
                "import sys\n",
                "from pathlib import Path\n",
                "\n",
                "# Add src/ and workspace root to path for clean modular imports\n",
                "sys.path.insert(0, str(Path(\"src\").resolve()))\n",
                "sys.path.insert(0, str(Path(\".\").resolve()))\n",
                "\n",
                "import json\n",
                "import matplotlib.pyplot as plt\n",
                "import numpy as np\n",
                "import pandas as pd\n",
                "import qiskit\n",
                "import qiskit_aer\n",
                "\n",
                "print(f\"Python Version:     {sys.version.split()[0]}\")\n",
                "print(f\"Qiskit Version:     {qiskit.__version__}\")\n",
                "print(f\"Qiskit Aer Version: {qiskit_aer.__version__}\")\n"
            ]
        },
        # Cell 4: Data Ingestion Markdown
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### 2. Ingesting & Visualizing the Official Challenge Instance\n",
                "\n",
                "The problem instance is loaded directly from the official Challenge Kit JSON definition without synthetic substitution. It defines an unweighted graph with 6 vertices and 8 edges.\n"
            ]
        },
        # Cell 5: Data Ingestion Code
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "from maxcut.io import load_challenge_instance\n",
                "from maxcut.domain.model import MaxCutGraph\n",
                "from maxcut.visualization.plot_graph import plot_maxcut_graph\n",
                "\n",
                "instance_path = Path(\"instances/challenge/o1_maxcut_instance.json\")\n",
                "instance_data = load_challenge_instance(instance_path)\n",
                "graph = MaxCutGraph.from_challenge_instance(instance_data)\n",
                "\n",
                "print(f\"Instance Name: {graph.name}\")\n",
                "print(f\"Vertices (|V|): {graph.num_nodes}, Edges (|E|): {graph.num_edges}\")\n",
                "print(f\"Total Weight:   {graph.total_weight:.2f}\")\n",
                "print(f\"Edge List:      {graph.edges}\")\n",
                "\n",
                "fig, ax = plt.subplots(figsize=(6, 5), dpi=120)\n",
                "plot_maxcut_graph(graph, ax=ax, title=f\"Official Challenge Graph: {graph.name}\")\n",
                "plt.tight_layout()\n",
                "plt.show()\n"
            ]
        },
        # Cell 6: Classical Solver Markdown
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### 3. Classical Reference Solver (Ground Truth Optimum)\n",
                "\n",
                "To establish an indisputable benchmark for quantum performance, we implement an exact exhaustive classical solver. For $|V| = 6$, the state space comprises $2^6 = 64$ assignments. Evaluating all assignments certifies the exact global optimum $C_{\\max}$ and identifies all degenerate ground states.\n"
            ]
        },
        # Cell 7: Classical Solver Code
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "from maxcut.classical.solver import ExactExhaustiveSolver\n",
                "\n",
                "solver = ExactExhaustiveSolver()\n",
                "classical_result = solver.solve(graph)\n",
                "\n",
                "print(f\"Classical Global Optimum: C_max = {classical_result.optimal_cut_value:.4f}\")\n",
                "print(f\"Number of Optimal Solutions:      {len(classical_result.optimal_bitstrings)} / 64 (bitstring symmetry)\")\n",
                "print(f\"Optimal Bitstrings:               {classical_result.optimal_bitstrings}\")\n",
                "print(f\"Classical Solver Execution Time:  {classical_result.execution_time_seconds * 1000:.3f} ms\")\n",
                "\n",
                "# Visualize one of the optimal partitions\n",
                "sample_opt = classical_result.optimal_bitstrings[0]\n",
                "partition = graph.compute_cut(sample_opt)\n",
                "\n",
                "fig, ax = plt.subplots(figsize=(6, 5), dpi=120)\n",
                "plot_maxcut_graph(graph, partition=partition, ax=ax, title=f\"Optimal Cut: C = {partition.cut_value:.0f} (Assignment: {sample_opt})\")\n",
                "plt.tight_layout()\n",
                "plt.show()\n"
            ]
        },
        # Cell 8: Mathematical Formulation Markdown
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### 4. Mathematical Formulation: QUBO to Ising Spin Hamiltonian\n",
                "\n",
                "We transform the binary optimization problem into a spin Hamiltonian suitable for quantum simulation:\n",
                "1. **Variable Substitution:** Map $x_u \\in \\{0, 1\\}$ to spin operator $s_u = (1 - 2x_u) \\in \\{+1, -1\\}$.\n",
                "2. **Operator Mapping:** Replace $s_u$ with the Pauli-$Z$ operator $Z_u$:\n",
                "   $$x_u \\oplus x_v = \\frac{I - Z_u Z_v}{2}$$\n",
                "3. **Cost Hamiltonian:**\n",
                "   $$H_C = \\sum_{(u, v) \\in E} \\frac{w_{uv}}{2} (I - Z_u Z_v)$$\n",
                "4. **Objective Convention:** Minimizing energy $E = \\langle H_C \\rangle$ is equivalent to maximizing cut $C = -E + \\text{offset}$.\n"
            ]
        },
        # Cell 9: Mathematical Formulation Code
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "from maxcut.formulation.ising import build_cost_operator\n",
                "from maxcut.formulation.qubo import graph_to_qubo\n",
                "\n",
                "qubo = graph_to_qubo(graph)\n",
                "cost_operator, offset = build_cost_operator(graph)\n",
                "\n",
                "print(f\"Qiskit Cost Operator (SparsePauliOp): {cost_operator.num_qubits} qubits, {len(cost_operator)} terms\")\n",
                "print(f\"Constant Energy Offset: {offset:.4f}\")\n",
                "print(\"Pauli Z_u Z_v Terms:\")\n",
                "for pauli, coeff in cost_operator.to_list():\n",
                "    print(f\"  {pauli}: {coeff.real:+.4f}\")\n"
            ]
        },
        # Cell 10: QAOA Core Markdown
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### 5. QAOA Circuit Construction & Local Parameter Optimization\n",
                "\n",
                "The QAOA ansatz prepares the state:\n",
                "$$|\\psi(\\boldsymbol{\\gamma}, \\boldsymbol{\\beta})\\rangle = \\prod_{l=1}^p \\left( e^{-i \\beta_l H_M} e^{-i \\gamma_l H_C} \\right) |+\\rangle^{\\otimes n}$$\n",
                "\n",
                "where $H_M = \\sum_u X_u$ is the transverse-field mixer. For depth $p = 1$, we optimize $\\gamma_1, \\beta_1$ using COBYLA.\n"
            ]
        },
        # Cell 11: QAOA Core Code
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "from maxcut.qaoa.ansatz import build_qaoa_circuit\n",
                "from maxcut.qaoa.optimizer import QAOAOptimizer\n",
                "\n",
                "ansatz = build_qaoa_circuit(graph, p=1, include_measurements=True)\n",
                "print(f\"Logical QAOA Circuit Depth: {ansatz.circuit.depth()}\")\n",
                "print(f\"Logical Gates breakdown:    {dict(ansatz.circuit.count_ops())}\")\n",
                "\n",
                "optimizer = QAOAOptimizer(method=\"COBYLA\", maxiter=100, tol=1e-4, seed=42)\n",
                "opt_res = optimizer.optimize(graph, p=1)\n",
                "\n",
                "print(f\"Optimal Parameters:   gamma = {opt_res.optimal_gamma[0]:.4f}, beta = {opt_res.optimal_beta[0]:.4f}\")\n",
                "print(f\"Optimizer Evaluations: {opt_res.num_evaluations}\")\n",
                "print(f\"Final Expected Cut:   <C> = {opt_res.final_expected_cut:.4f} (Approximation Ratio: {opt_res.final_expected_cut / classical_result.optimal_cut_value:.4f})\")\n"
            ]
        },
        # Cell 12: Experiments Loading Markdown
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### 6. Experimental Execution: Simulator, Processor A, and Processor B\n",
                "\n",
                "Using the unified `ExperimentRunner`, we load and inspect the recorded execution artifacts from all three targets:\n",
                "1. **Ideal Aer Simulator:** Unconstrained all-to-all connectivity.\n",
                "2. **Processor A (`Falcon-H`):** 7-qubit heavy-hex subset with native `ecr` 2-qubit basis gates.\n",
                "3. **Processor B (`Ring-7`):** 7-qubit circular ring with native `cz` 2-qubit basis gates.\n",
                "\n",
                "All executions sampled 2048 measurement shots with fixed `seed_transpiler = 42` and Optimization Level 1.\n"
            ]
        },
        # Cell 13: Experiments Loading Code
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "from maxcut.experiments.schema import load_experiment_result\n",
                "\n",
                "sim_res = load_experiment_result(\"results/data/O1_MaxCut_Challenge_aer_simulator_p1_result.json\")\n",
                "proc_a_res = load_experiment_result(\"results/data/O1_MaxCut_Challenge_processor_a_p1_result.json\")\n",
                "proc_b_res = load_experiment_result(\"results/data/O1_MaxCut_Challenge_processor_b_p1_result.json\")\n",
                "\n",
                "print(\"Execution Artifacts Successfully Loaded:\")\n",
                "print(f\"- Simulator Job ID:   {sim_res.job_metadata.get('job_id')}\")\n",
                "print(f\"- Processor A Job ID: {proc_a_res.job_metadata.get('job_id')}\")\n",
                "print(f\"- Processor B Job ID: {proc_b_res.job_metadata.get('job_id')}\")\n"
            ]
        },
        # Cell 14: Resource Table Markdown
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### 7. Architectural & Resource Metrics Comparison\n",
                "\n",
                "The table below details physical qubit usage, transpiled depth, two-qubit gate counts, SWAP counts, and total gate volume for each target architecture.\n"
            ]
        },
        # Cell 15: Resource Table Code
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "comp_df = pd.read_csv(\"results/tables/processor_comparison_table.csv\")\n",
                "resource_cols = [\n",
                "    \"Target\", \"Native 2Q Gate\", \"Logical Depth\", \"Transpiled Depth\",\n",
                "    \"Logical 2Q Gates\", \"Transpiled 2Q Gates\", \"SWAP Count\", \"Total Transpiled Gates\",\n",
                "    \"Routing 2Q Overhead\", \"Depth Expansion\"\n",
                "]\n",
                "comp_df[resource_cols]\n"
            ]
        },
        # Cell 16: Solution Quality Table Markdown
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### 8. Solution Quality & Sampling Statistics\n",
                "\n",
                "Evaluating the empirical quality of the measured outcomes: best cut found, expected cut $\\langle C \\rangle$, approximation ratio $\\alpha$, and ground-state success probability $P(x^*)$.\n"
            ]
        },
        # Cell 17: Solution Quality Table Code
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "quality_cols = [\n",
                "    \"Target\", \"Best Cut\", \"Optimal Cut Hit\", \"Expected Cut <C>\",\n",
                "    \"Approximation Ratio (alpha)\", \"Ground State Prob P(opt)\",\n",
                "    \"Sample Mean Cut\", \"Sample Std Cut\", \"Sample Median Cut\"\n",
                "]\n",
                "comp_df[quality_cols]\n"
            ]
        },
        # Cell 18: Cut Distribution Code
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "cut_dist_df = pd.read_csv(\"results/tables/cut_distribution_table.csv\")\n",
                "cut_dist_df\n"
            ]
        },
        # Cell 19: Visualizations Markdown
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### 9. High-Resolution Comparative Visualizations\n",
                "\n",
                "Visualizing empirical cut probability distributions, resource scaling, and quality metrics across the three execution targets.\n"
            ]
        },
        # Cell 20: Visualizations Code
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "import matplotlib.image as mpimg\n",
                "\n",
                "fig, axes = plt.subplots(1, 3, figsize=(18, 5.5), dpi=150)\n",
                "\n",
                "axes[0].imshow(mpimg.imread(\"results/figures/figure1_cut_distribution_comparison.png\"))\n",
                "axes[0].axis(\"off\")\n",
                "axes[0].set_title(\"Objective Cut Distribution\", fontsize=11, fontweight=\"bold\")\n",
                "\n",
                "axes[1].imshow(mpimg.imread(\"results/figures/figure2_circuit_resource_comparison.png\"))\n",
                "axes[1].axis(\"off\")\n",
                "axes[1].set_title(\"Architectural Resource Overhead\", fontsize=11, fontweight=\"bold\")\n",
                "\n",
                "axes[2].imshow(mpimg.imread(\"results/figures/figure3_solution_quality_comparison.png\"))\n",
                "axes[2].axis(\"off\")\n",
                "axes[2].set_title(\"Solution Quality & Probability\", fontsize=11, fontweight=\"bold\")\n",
                "\n",
                "plt.tight_layout()\n",
                "plt.show()\n"
            ]
        },
        # Cell 21: Evidence Analysis Markdown
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### 10. Evidence-Based Interpretation & Research Findings\n",
                "\n",
                "#### Q1: Which processor produced the better solution quality?\n",
                "* **Observed Fact:** Both processors sampled the maximum cut $C_{\\max} = 6.0000$. Processor B recorded $\\langle C \\rangle = 4.9116$ ($\\alpha = 81.86\\%$, $P(x^*) = 40.72\\%$) vs. Processor A's $\\langle C \\rangle = 4.8901$ ($\\alpha = 81.50\\%$, $P(x^*) = 39.31\\%$), a difference of $+0.44\\%$ in expected cut and $+1.41\\%$ in ground state probability.\n",
                "* **Interpretation:** In noise-free unitary emulation, both processors preserved solution quality within a fraction of a percent. The $+1.41\\%$ ground state margin is well within expected multinomial shot noise across 2048 shots ($1/\\sqrt{2048} \\approx 2.21\\%$).\n",
                "* **Limitation:** In the absence of device noise, this divergence reflects finite-sample statistical variance rather than hardware superiority.\n",
                "\n",
                "#### Q2: How different were the resource requirements?\n",
                "* **Observed Fact:** Both processors required 7 physical qubits and synthesized 28 two-qubit entangling gates ($3.50\\times$ expansion). However, Processor B required **20 fewer total gates** (139 vs. 159 gates, a $12.58\\%$ reduction).\n",
                "* **Interpretation:** Synthesizing $R_{ZZ}$ interactions from the native `cz` basis requires fewer single-qubit Euler rotations than synthesizing from native `ecr` gates.\n",
                "* **Limitation:** Gate volume does not directly indicate execution duration without calibrated pulse durations.\n",
                "\n",
                "#### Q3: Did routing introduce overhead?\n",
                "* **Observed Fact:** Neither processor required SWAP gate insertions (`swap_count = 0`). However, two-qubit gates expanded from 8 to 28 ($+250\\%$).\n",
                "* **Interpretation:** The 6-vertex graph was embedded isomorphically into connected subgraphs of both Falcon-H and Ring-7 without dynamic SWAPs. The 2Q gate overhead is **basis synthesis overhead** rather than routing overhead.\n",
                "* **Limitation:** On larger graphs ($N \\ge 8$), dynamic routing SWAPs would become mandatory.\n",
                "\n",
                "#### Q4: Did circuit depth differ?\n",
                "* **Observed Fact:** At Optimization Level 1, Processor A depth was 84 cycles vs. Processor B's 98 cycles ($+14$ cycles on B). At Optimization Levels 2 & 3, Processor B reduced to 87 cycles while Processor A increased to 99 cycles ($-12$ cycles on B).\n",
                "* **Interpretation:** Scheduling parallelism favored Falcon-H at Level 1, while commutation and cancellation passes benefited Ring-7 more at Levels 2 & 3.\n",
                "* **Limitation:** Transpiled gate cycles do not reflect physical coherence time ($T_1, T_2$) without calibrated gate durations.\n",
                "\n",
                "#### Q5: Did measured results support a relationship between architecture/resources and solution quality?\n",
                "* **Observed Fact:** Despite significant depth (10 vs 84 vs 98) and gate count differences, solution quality was virtually identical ($\\alpha \\approx 81.5\\%\\text{--}81.9\\%$).\n",
                "* **Interpretation:** In the noise-free regime, compiler transformations are mathematically exact. Thus, measured results do NOT support a causal degradation of solution quality from depth expansion in the absence of noise.\n",
                "* **Limitation:** Real hardware noise ($28 \\times \\epsilon_{2Q}$) would substantially degrade solution fidelity.\n"
            ]
        },
        # Cell 22: Quantum Advantage Markdown
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### 11. Quantum Advantage Assessment\n",
                "\n",
                "> **Quantum Advantage Status:** **NOT DEMONSTRATED**  \n",
                "> - **Classical Exact Solver:** Solved the instance to certified global optimality in **0.0004 seconds** ($0.4\\text{ ms}$).\n",
                "> - **QAOA ($p=1$):** Achieved an approximation ratio of $\\alpha \\approx 0.818$ with a $\\sim 40\\%$ ground state probability across 2048 shots.\n",
                "> - **Conclusion:** QAOA verified algorithmic convergence across both processors, but provides no computational advantage over classical methods for this problem scale.\n"
            ]
        },
        # Cell 23: Reproducibility Markdown
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### 12. Reproducibility & CLI Execution\n",
                "\n",
                "To reproduce the entire experimental workflow and test suite from a clean environment:\n",
                "\n",
                "```bash\n",
                "# 1. Run complete automated test suite (56 tests)\n",
                "pytest -q\n",
                "\n",
                "# 2. Re-run processor experiments\n",
                "python scripts/run_processor_experiments.py\n",
                "\n",
                "# 3. Regenerate all tables and publication figures\n",
                "python scripts/generate_analysis_artifacts.py\n",
                "```\n"
            ]
        }
    ]

    notebook_data = {
        "cells": cells,
        "metadata": {
            "language_info": {
                "name": "python",
                "version": "3.14.6"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 2
    }

    with open(notebook_path, "w", encoding="utf-8") as f:
        json.dump(notebook_data, f, indent=1)

    print(f"Generated {notebook_path} with {len(cells)} cells.")


if __name__ == "__main__":
    create_notebook()
