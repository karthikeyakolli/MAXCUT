# Qiskit Fall Fest 2026 — Quantum Optimization (O1 Max-Cut)
## Official Judge-Ready Technical Narrative & Comparative Architectural Benchmark: Processor A vs. Processor B

**Track Selection:** Quantum Optimization — **Problem Code: O1**  
**Selected Problem:** Maximum Cut (Max-Cut) on Official 6-Vertex Challenge Graph  
**Algorithm:** Quantum Approximate Optimization Algorithm (QAOA) vs. Classical Exhaustive Ground Truth  
**Target Architectures (v3 Corrected):** Processor A (`5Q-Baseline-Tree`, 5 physical qubits), Processor B (`Heavy-Hex-7`, 7 physical qubits), and Unconstrained Simulator  
**Formulation:** 5-Qubit Exact $\mathbb{Z}_2$ Complement-Symmetry Reduced QAOA (Official Benchmark) alongside Preserved Historical Baseline Runs  
**Execution Modes:** `aer_hardware_topology_emulation` (Ideal Reference) & `aer_noisy_simulation` (Prescribed Noise Baseline)  
**Regression Test Suite:** 115 Automated Tests Passing (`pytest`)  
**Official Repository:** [https://github.com/karthikeyakolli/MAXCUT](https://github.com/karthikeyakolli/MAXCUT)  

---

> ### AI-Assistance Disclosure
> In compliance with hackathon submission guidelines: AI pair programming tools (Google Antigravity / Gemini) were utilized for code scaffolding, automated test generation, and documentation linting. All mathematical proofs, symmetry reductions, hardware adapter implementations, and empirical benchmark evaluations were designed, derived, and verified by the authors through deterministic test suites and direct data artifact audits.

---

## 1. Official O1 Problem and Graph

The **Maximum Cut (Max-Cut)** problem is a canonical NP-hard combinatorial optimization challenge. Given an undirected graph $G = (V, E)$ with edge weights $w_{uv}$, the objective is to partition the vertices $V$ into two complementary subsets $S$ and $\bar{S}$ such that the sum of the weights of edges crossing the cut boundary is maximized:

$$C(x) = \sum_{(u, v) \in E} w_{uv} (x_u \oplus x_v) = \sum_{(u, v) \in E} w_{uv} [x_u(1 - x_v) + x_v(1 - x_u)]$$

where binary decision variable $x_u = 0$ denotes $u \in S$ and $x_u = 1$ denotes $u \in \bar{S}$.

For the **O1 Max-Cut** benchmark, the official organizer instance [`instances/challenge/o1_maxcut_instance.json`](instances/challenge/o1_maxcut_instance.json) is ingested directly without synthetic substitution:
* **Vertices:** $|V| = 6$ ($V = \{0, 1, 2, 3, 4, 5\}$).
* **Edges:** $|E| = 8$ unweighted edges ($w_{uv} = 1.0$, total graph weight $W = 8.00$).
* **Edge Set:** $(0, 1), (0, 2), (1, 3), (1, 4), (2, 4), (2, 5), (3, 4), (4, 5)$.
* **Degree Distribution:** Nodes 0, 1, 3, 4 have degree 3; nodes 2, 5 have degree 2.
* **Integrity:** Zero self-loops detected and strictly validated by schema tests.

---

## 2. Classical Reference Optimum

To establish an authoritative ground truth for quantum evaluation, an exact exhaustive combinatorial solver was executed across all $2^6 = 64$ computational states ([`src/maxcut/classical/solver.py`](src/maxcut/classical/solver.py)):
* **Exact Global Optimum:** $C_{\max} = 6.0000$ (75.0% of total edge weight $W = 8.00$).
* **Classical Solution Runtime:** $0.0004\text{ seconds}$ ($0.4\text{ ms}$).
* **Optimal Subspace Degeneracy:** Exactly **10 bitstrings** achieve $C(x) = 6.0000$, forming 5 complementary pairs under bitwise spin inversion ($\mathbb{Z}_2$ symmetry):  
  `001101` / `110010`, `011001` / `100110`, `010011` / `101100`, `110011` / `001100`, `101101` / `010010`.

Serialized in [`results/data/classical_reference.json`](results/data/classical_reference.json).

---

## 3. Five-Variable Reduction & Mathematical Justification

### Problem Motivation
The official Processor A hardware definition provides a **5-qubit** baseline topology (`[0, 1, 2, 3, 4]`). An unreduced 6-vertex QAOA circuit requires $\ge 6$ physical qubits and cannot be compiled directly onto 5 physical qubits.

### Mathematical Symmetry Reduction
Because Max-Cut is invariant under global spin inversion ($x \mapsto \mathbf{1} \oplus x$, interchanging subsets $S$ and $\bar{S}$ leaves cut weight unchanged), we fix vertex $x_0 = 0$ without loss of generality:
* The 5 remaining vertices $x_1, \dots, x_5$ are represented by 5 quantum variables $q_0, \dots, q_4$.
* Edges not incident to vertex 0 ($(u, v)$ with $u, v \ge 1$) remain standard two-body Ising terms:
  $$x_u \oplus x_v = \frac{I - Z_u Z_v}{2}$$
* Edges incident to vertex 0 ($(0, v)$ with $x_0 = 0$) simplify to linear longitudinal fields:
  $$0 \oplus x_v = x_v = \frac{I - Z_v}{2}$$

Substituting into the minimization cost Hamiltonian ($H_C = -C(x)$):
$$H_C^{(5Q)} = \frac{1}{2} \sum_{(u, v) \in E, u, v \ge 1} Z_u Z_v + \frac{1}{2} Z_1 + \frac{1}{2} Z_2 - 4.0 \cdot I$$

### Exhaustive Proof of Equivalence
Exhaustively verified in [`tests/test_reduced_formulation.py`](tests/test_reduced_formulation.py):
1. All 32 reduced assignments map bijectively to canonical 6-vertex states with identical cut values.
2. The global optimum remains strictly $C_{\max} = 6.0000$.
3. The 10 optimal bitstrings condense to exactly 5 unique optimal reduced assignments.

---

## 4. QUBO and Ising Conventions

To preserve rigorous mathematical consistency across all representations:
1. **Classical Cut:** $C(x) = \sum_{(u, v) \in E} w_{uv} (x_u + x_v - 2 x_u x_v)$ (Maximization)
2. **QUBO Cost:** $f_{\text{QUBO}}(x) = -C(x) = x^T Q x$ (Minimization)
3. **Ising Hamiltonian:** $E_{\text{Ising}}(s) = s^T J s + h^T s = -C(x)$ (Minimization)
4. **Quantum Cost Operator:** $\langle x | H_C | x \rangle = -C(x)$ (Minimization)

Therefore, across all computational basis states $|x\rangle$:
$$C(x) = -f_{\text{QUBO}}(x) = -E_{\text{Ising}}(s) = -\langle x | H_C | x \rangle$$

Spectral equivalence across all representations is certified by [`tests/test_formulation.py`](tests/test_formulation.py).

---

## 5. QAOA Circuit, Parameter Selection & Decoding

The level-1 QAOA ansatz alternates problem cost unitary $e^{-i \gamma H_C}$ and transverse mixer unitary $e^{-i \beta H_M}$:
$$|\psi(\gamma, \beta)\rangle = e^{-i \beta \sum_{u=0}^4 X_u} e^{-i \gamma H_C^{(5Q)}} |+\rangle^{\otimes 5}$$

* **Optimal Variational Angles:** Classical optimization over the 5Q reduced Hamiltonian yields:
  $$\gamma^* = 2.5270\text{ rad}, \quad \beta^* = 2.6983\text{ rad}$$
* **Analytic Expected Cut (Statevector):** $\langle C \rangle_{\text{analytic}} = 5.0400$
* **Analytic Approximation Ratio:** $\alpha_{\text{analytic}} = \frac{5.0400}{6.0000} = 0.8400$ ($84.00\%$)
* **Measurement Decoding Protocol:** Qiskit measurement registers are recorded in little-endian order ($q_4 q_3 q_2 q_1 q_0$). The decoder reverses bitstrings to canonical index order $[q_0, q_1, q_2, q_3, q_4]$, prepends fixed bit $x_0 = 0$, and evaluates the canonical cut.

---

## 6. Processor A Definition, Compilation & Results (v3 Corrected)

> [!NOTE]
> **Provisional Local Configuration:** Configured as a genuine 5-physical-qubit processor (`5Q-Baseline-Tree`) with topology `[0, 1, 2, 3, 4]`, labeled `PROVISIONAL — ORGANIZER CONFIRMATION REQUIRED` pending upstream challenge kit archive retrieval.

### Target Specification
* **Identifier:** `Processor_A` (`5Q-Baseline-Tree`)
* **Qubits:** Exactly 5 physical qubits: `[0, 1, 2, 3, 4]`.
* **Topology:** Fixed 5-node T-tree coupling graph (4 undirected edges, 8 directed pairs): `(0, 1), (1, 2), (1, 3), (3, 4)`.
* **Native Basis Gates:** `["rz", "sx", "x", "ecr"]` (native 2Q entangler: `ecr`).
* **Hardware Noise Parameters:** $T_1 = 210.0\ \mu\text{s}, T_2 = 140.0\ \mu\text{s}$, 1Q error $0.010\%$, 2Q ECR error $0.75\%$, readout error $1.50\%$.

### Compilation & Empirical Results ($N = 2048$ shots)
* **Circuit Depth:** 69 cycles (116 total gates).
* **Native 2Q Gates:** 18 ECR gates (12 basis synthesis + 6 routing, **2 SWAPs**).
* **Ideal Reference Emulation:** $\bar{C} = 5.0625 \pm 0.0229$, $\hat{\alpha} = 0.8438$ ($84.38\%$), $P_{\text{opt}} = 41.70\%$ (854 hits, Wilson 95% CI: $[39.58\%, 43.85\%]$).
* **Noisy Baseline Simulation:** $\bar{C} = 4.9399 \pm 0.0244$, $\hat{\alpha} = 0.8233$ ($82.33\%$), $P_{\text{opt}} = 37.60\%$ (770 hits, Wilson 95% CI: $[35.52\%, 39.72\%]$).

Serialized in [`results/verified_ab_v3/data/processor_a_ideal_reference.json`](results/verified_ab_v3/data/processor_a_ideal_reference.json) and [`processor_a_noisy_baseline.json`](results/verified_ab_v3/data/processor_a_noisy_baseline.json).

---

## 7. Processor B Definition, Compilation & Results (v3 Corrected)

> [!NOTE]
> **Provisional Local Configuration:** Configured as a genuine 7-physical-qubit processor (`Heavy-Hex-7`) with sparse heavy-hex unit cell topology, labeled `PROVISIONAL — ORGANIZER CONFIRMATION REQUIRED` pending upstream challenge kit archive retrieval.

### Target Specification
* **Identifier:** `Processor_B` (`Heavy-Hex-7`)
* **Qubits:** Exactly 7 physical qubits: `[0, 1, 2, 3, 4, 5, 6]`. Active mapped qubits: `[0, 1, 2, 3, 5]`.
* **Topology:** Sparse heavy-hex-inspired unit cell graph (6 undirected edges, 12 directed pairs): `(0, 1), (1, 2), (1, 3), (3, 5), (4, 5), (5, 6)`.
* **Native Basis Gates:** `["rz", "sx", "x", "cz"]` (native 2Q entangler: `cz`).
* **Hardware Noise Parameters:** $T_1 = 240.0\ \mu\text{s}, T_2 = 140.0\ \mu\text{s}$, 1Q error $0.015\%$, 2Q CZ error $0.50\%$, readout error $1.00\%$.

### Compilation & Empirical Results ($N = 2048$ shots)
* **Circuit Depth:** 83 cycles (114 total gates).
* **Native 2Q Gates:** 18 CZ gates (12 basis synthesis + 6 routing, **2 SWAPs**).
* **Ideal Reference Emulation:** $\bar{C} = 5.0742 \pm 0.0230$, $\hat{\alpha} = 0.8457$ ($84.57\%$), $P_{\text{opt}} = 42.53\%$ (871 hits, Wilson 95% CI: $[40.40\%, 44.68\%]$).
* **Noisy Baseline Simulation:** $\bar{C} = 4.9839 \pm 0.0240$, $\hat{\alpha} = 0.8306$ ($83.06\%$), $P_{\text{opt}} = 39.65\%$ (812 hits, Wilson 95% CI: $[37.55\%, 41.78\%]$).

Serialized in [`results/verified_ab_v3/data/processor_b_ideal_reference.json`](results/verified_ab_v3/data/processor_b_ideal_reference.json) and [`processor_b_noisy_baseline.json`](results/verified_ab_v3/data/processor_b_noisy_baseline.json).

---

## 8. Ideal/Noisy Experiment Comparison (v3 Empirical Matrix)

All statistical hypothesis tests were performed at the standard $\alpha = 0.05$ significance level. **Nonsignificant tests are reported strictly as "No statistically significant difference detected" and never asserted as proof of physical equivalence:**

| Comparison | Group 1 | Group 2 | $\Delta \bar{C}$ [95% CI] | Welch $t$-stat | $p$-value ($\bar{C}$) | $\bar{C}$ Diff Detected? | $\Delta P_{\text{opt}}$ [95% CI] | Two-Prop $z$-stat | $p$-value ($P_{\text{opt}}$) | Proportion Diff Detected? |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **1. Processor A: Ideal vs. Noisy** | Proc A Ideal | Proc A Noisy | +0.1226 [0.0570, 0.1881] | 3.665 | $2.50 \times 10^{-4}$ | **Yes ($p < 0.05$)** | +4.10% [1.11%, 7.10%] | 2.683 | 0.0073 | **Yes ($p < 0.05$)** |
| **2. Processor B: Ideal vs. Noisy** | Proc B Ideal | Proc B Noisy | +0.0903 [0.0252, 0.1555] | 2.718 | $6.60 \times 10^{-3}$ | **Yes ($p < 0.05$)** | +2.88% [-0.13%, 5.89%] | 1.874 | 0.0610 | No statistically significant difference detected |
| **3a. Proc A vs. B (Controlled Ideal)** | Proc A Ideal | Proc B Ideal | -0.0117 [-0.0753, 0.0518] | -0.361 | 0.7178 | No statistically significant difference detected | -0.83% [-3.85%, 2.19%] | -0.538 | 0.5906 | No statistically significant difference detected |
| **3b. Proc A vs. B (Controlled Noisy)** | Proc A Noisy | Proc B Noisy | -0.0439 [-0.1110, 0.0231] | -1.284 | 0.1992 | No statistically significant difference detected | -2.05% [-5.03%, 0.93%] | -1.348 | 0.1777 | No statistically significant difference detected |

Serialized in [`results/verified_ab_v3/tables/pairwise_comparisons_table.md`](results/verified_ab_v3/tables/pairwise_comparisons_table.md) and visualized in [Figure 1: Cut Sampling Distribution](results/verified_ab_v3/figures/figure1_sampling_distribution.png).

---

## 9. Resource Metrics & Statistical Uncertainty (v3 Corrected)

| Target Backend | Architecture | Circuit Depth (Cycles) | Total Gates | Native 2Q Gate | Total 2Q Count | Basis 2Q | Routing 2Q | Routing SWAPs | Mean 2Q Error | Compounded 2Q Survival | Approximation Ratio $\hat{\alpha}$ | Success Prob $P_{\text{opt}}$ |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Processor A (Ideal)** | 5Q-Baseline-Tree | 69 | 116 | `ecr` | 18 | 12 | 6 | 2 | 0.75% | 87.3% | 0.8438 | 41.70% |
| **Processor A (Noisy)** | 5Q-Baseline-Tree | 69 | 116 | `ecr` | 18 | 12 | 6 | 2 | 0.75% | 87.3% | 0.8233 | 37.60% |
| **Processor B (Ideal)** | Heavy-Hex-7 | 83 | 114 | `cz` | 18 | 12 | 6 | 2 | 0.50% | 91.4% | 0.8457 | 42.53% |
| **Processor B (Noisy)** | Heavy-Hex-7 | 83 | 114 | `cz` | 18 | 12 | 6 | 2 | 0.50% | 91.4% | 0.8306 | 39.65% |

### Architectural Trade-Off Analysis:
1. **Depth Advantage (Processor A):** Processor A achieves a **16.9% depth reduction** (69 vs. 83 cycles) with identical SWAP count (2 SWAPs, 6 routing gates) due to compact T-tree topology layout.
2. **Gate Fidelity Counterbalance (Processor B):** Processor B's lower 2Q error rate ($\bar{e}_{2Q} = 0.50\%$ vs. $0.75\%$) yields a higher compounded entangling survival probability (**91.4%** across 18 CZ gates vs. **87.3%** across 18 ECR gates on Processor A). This 4.1% fidelity margin counterbalances Processor B's depth overhead, resulting in slightly higher noisy expected cut ($4.9839$ vs. $4.9399$, with difference not reaching significance at $\alpha = 0.05$).

Serialized in [`results/verified_ab_v3/tables/resource_vs_quality_table.md`](results/verified_ab_v3/tables/resource_vs_quality_table.md) and [`statistical_uncertainty_table.md`](results/verified_ab_v3/tables/statistical_uncertainty_table.md).

---

## 10. Findings, Limitations & Conclusion

> [!IMPORTANT]
> ### Quantum Advantage Status: NOT DEMONSTRATED
> - **Classical Baseline:** The exact classical brute-force solver evaluates all candidate states in **0.0004 seconds** ($0.4\text{ ms}$), finding the proven global optimum $C_{\max} = 6.0000$.
> - **Quantum Sampling Performance:** Level-1 QAOA achieves approximation ratios $\hat{\alpha} \approx 0.822\text{--}0.846$, sampling the global optimum with $36.9\%\text{--}42.5\%$ probability across 2048 shots.
> - **Scalability Limitations:** On small benchmark instances ($|V| \le 20$), classical solvers (including branch-and-bound and Goemans-Williamson SDP) outperform NISQ heuristics by several orders of magnitude in both runtime and solution certifiability.
> - **Scientific Conclusion:** Both Processor A and Processor B compile and execute the benchmark instance reliably. Processor A provides depth efficiency, while Processor B provides basis economy and lower degradation under the prescribed noise model. Neither architecture is universally superior.

---

## 11. Environment Setup & Reproducibility Instructions

### Clean Virtual Environment Setup
```powershell
# 1. Clone repository and navigate to workspace
git clone https://github.com/karthikeyakolli/MAXCUT.git
cd MAXCUT

# 2. Create isolated Python virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Install pinned dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
```

### Complete Reproduction Workflow
```powershell
# 1. Run complete automated regression test suite (115 tests passing)
pytest -v

# 2. Execute official 5Q reduced hardware adapter integration
python scripts/run_reduced_5q_integration.py

# 3. Execute controlled 4-case empirical benchmark matrix
python scripts/run_verified_ab_v3_experiments.py

# 4. Generate all statistical tables, hypothesis tests, and publication figures
python scripts/analyze_verified_ab_v3_statistics.py

# 5. Build and pre-render the judge-ready interactive notebook
python scripts/build_and_render_notebook.py

# 6. Validate artifact presence, non-emptiness, and notebook completeness
python scripts/validate_artifacts.py
```

---

## 12. Distinguishing Official Benchmark from Historical 6-Qubit Baseline

To ensure transparency across audit phases, the repository maintains clear isolation between experiment iterations:

| Feature | Corrected Target Benchmark (v3) | Historical 5Q-Subset Benchmark (v2) | Historical Direct Baseline (Phase 0 / v1) |
| :--- | :--- | :--- | :--- |
| **Formulation** | 5-Qubit Symmetry-Reduced ($x_0 = 0$) | 5-Qubit Symmetry-Reduced ($x_0 = 0$) | 6-Qubit Direct Formulation ($q_0 \dots q_5 \leftrightarrow x_0 \dots x_5$) |
| **Processor A Architecture** | Genuine 5Q Baseline Tree (`[0..4]`) | 5 active physical qubits on 7Q Falcon-H | 6 physical qubits on 7Q Falcon-H |
| **Processor B Architecture** | Genuine 7Q Heavy-Hex (`[0..6]`, active 5Q) | 5 active physical qubits on 7Q Ring-7 | 6 physical qubits on 7Q Ring-7 |
| **Target Transpiled Depth** | Proc A: 69 cycles; Proc B: 83 cycles | Proc A: 66 cycles; Proc B: 81 cycles | Proc A: 84 cycles; Proc B: 98 cycles |
| **Native 2Q Gates** | Proc A: 18 ECR (2 SWAPs); Proc B: 18 CZ (2 SWAPs) | Proc A: 18 ECR (2 SWAPs); Proc B: 21 CZ (3 SWAPs) | Proc A: 28 ECR (4 SWAPs); Proc B: 28 CZ (4 SWAPs) |
| **Results Location** | [`results/verified_ab_v3/`](results/verified_ab_v3/) | [`results/verified_ab_v2/`](results/verified_ab_v2/) | [`results/data/`](results/data/) & [`results/tables/`](results/tables/) |
| **Traceability Status** | REQ-20 & REQ-21 (v3 Corrected Architectures) | REQ-16 through REQ-19 (AUD-12 through AUD-15) | REQ-01 through REQ-15 (AUD-01 through AUD-11) |

Historical baseline artifacts are preserved without modification in `results/data/`, `results/tables/`, and Sections 8 & 9 of `report/analysis.md`.
