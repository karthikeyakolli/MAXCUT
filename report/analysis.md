# Scientific Report: Architectural Benchmarking of QAOA Max-Cut on Quantum Processors

**Competition Track:** Qiskit Fall Fest 2026 — Track O1 Quantum Optimization
**Problem Statement:** PS-O1 — Max-Cut on a Weighted Graph
**Benchmark Instance:** `O1_MaxCut_Challenge` ($|V|=6, |E|=8, W=8.00$)
**Target Architectures:** Processor A (5Q Linear Chain), Processor B (9Q Sparse Tree), Custom Processor D (8Q Chorded Mesh)
**Authoritative Benchmark Release:** Version 4.0.0 ([`results/verified_ab_v4/`](../results/verified_ab_v4/))
**Regression Test Suite:** 40/40 Passing Tests (`python -m unittest discover -s tests -p "test_phase*.py"`)
**Status:** Authoritative Judge-Ready Scientific Submission Report

---

> ### AI-Assistance Disclosure
> In compliance with hackathon submission guidelines: Generative AI tools (Google Antigravity / Gemini) were utilized for code scaffolding, linting, test suite generation, and documentation formatting. All mathematical proofs, symmetry reductions, hardware adapter implementations, and empirical benchmark evaluations were designed, derived, and verified by the authors through deterministic test suites and direct data artifact audits.

---

> [!IMPORTANT]
> ### Definitive Quantum Advantage Disclaimer: NOT DEMONSTRATED
> This 6-vertex Max-Cut instance does **not** demonstrate quantum advantage over classical computation.
>
> The exact classical exhaustive solver evaluates all 64 candidate partitions in **$0.425\,\text{ms}$** ($0.000425\,\text{s}$), certifying the global maximum cut $C_{\max} = 6.0000$ with $100\%$ certainty. In contrast, depth $p=1$ QAOA on noisy quantum processors produces approximation ratios of $81.3\%\text{--}81.9\%$ and requires substantial transpilation, routing, and error-mitigation overhead. This project demonstrates **architectural compilation and noise resilience trade-offs**, not quantum supremacy.

---

## 1. Executive Summary & Research Questions

In quantum combinatorial optimization via the Quantum Approximate Optimization Algorithm (QAOA), problem Hamiltonians must be compiled onto physical quantum processing units (QPUs) with restricted hardware connectivity and discrete native gate alphabets.

This investigation evaluates two primary research questions for the official Qiskit Fall Fest 2026 **O1 Max-Cut** benchmark:
1. **Topological Compilation Overhead:** How do restricted coupling topologies—specifically a 5-qubit nearest-neighbor linear chain (Processor A) versus a 9-qubit sparse tree (Processor B)—impact circuit depth, two-qubit entangling gate counts, and routing SWAP overhead when compiling identical logical QAOA problem interactions?
2. **Noise Resilience & Architectural Mitigation:** Under uniform synthetic depolarizing and readout noise, how does routing-induced depth dilation affect solution quality (mean cut $\langle C \rangle$, approximation ratio $\alpha$, and ground-state sampling probability $P(\text{opt})$), and can an optimized custom architecture (Processor D) eliminate SWAP overhead while strictly respecting physical transmon degree constraints?

---

## 2. Problem Statement & Benchmark Instance

### 2.1 Problem Definition
The **Maximum Cut (Max-Cut)** problem is a canonical NP-hard combinatorial optimization challenge. Given an undirected graph $G = (V, E)$ with edge weights $w_{uv}$, the goal is to partition vertices $V$ into two complementary subsets $S$ and $\bar{S}$ to maximize the total weight of cut edges crossing the boundary:

$$C(x) = \sum_{(u, v) \in E} w_{uv} (x_u \oplus x_v) = \sum_{(u, v) \in E} w_{uv} [x_u(1 - x_v) + x_v(1 - x_u)]$$

where binary decision variable $x_u = 0$ denotes $u \in S$ and $x_u = 1$ denotes $u \in \bar{S}$.

### 2.2 Canonical Challenge Instance Ingestion
The problem instance is ingested directly from [`instances/challenge/o1_maxcut_instance.json`](../instances/challenge/o1_maxcut_instance.json):
* **Order & Size:** $|V| = 6$ vertices (labeled $0, 1, 2, 3, 4, 5$) and $|E| = 8$ undirected edges.
* **Edge List:** $(0, 1), (0, 2), (1, 2), (1, 3), (2, 4), (3, 4), (3, 5), (4, 5)$.
* **Edge Weights:** Uniform unit values stored as floating-point `1.0` (total graph weight $W = 8.00$). The metadata contains `is_weighted: false`, indicating an unweighted graph where every edge has unit weight 1.
* **Graph Structure:** Connected planar graph containing intersecting 3-cycles and 4-cycles with maximum degree 4 (node 3) and minimum degree 2 (nodes 0 and 5). 0 self-loops and 0 multigraph edges detected.
* **Visual Asset:** [`results/verified_ab_v4/figures/figure1_maxcut_problem_graph.svg`](../results/verified_ab_v4/figures/figure1_maxcut_problem_graph.svg).

---

## 3. Exact Classical Ground Truth Baseline

To establish an authoritative ground truth for quantum evaluation, an exact exhaustive combinatorial solver was executed across all $2^6 = 64$ computational states ([`src/maxcut/classical/solver.py`](../src/maxcut/classical/solver.py), serialized in [`results/data/classical_reference.json`](../results/data/classical_reference.json)):
* **Exact Global Maximum Cut:** $C_{\max} = 6.0000$ (75.0% of total graph weight $W = 8.00$).
* **Classical Solution Runtime:** $0.000425\text{ seconds}$ ($0.425\text{ ms}$).
* **Optimal Subspace Degeneracy:** Exactly **10 bitstrings** achieve $C(x) = 6.0000$, forming 5 complementary pairs under bitwise spin inversion ($\mathbb{Z}_2$ symmetry):
  * `001100` $\leftrightarrow$ `110011`
  * `101100` $\leftrightarrow$ `010011`
  * `010010` $\leftrightarrow$ `101101`
  * `110010` $\leftrightarrow$ `001101`
  * `100110` $\leftrightarrow$ `011001`
* **Primary Representative Partition:** $S_1 = \{0, 1, 4, 5\}$ and $S_2 = \{2, 3\}$ (bitstring `001100`).

---

## 4. Five-Variable Symmetry Reduction & Mathematical Formulation

### 4.1 Physical Motivation
The primary baseline target (Processor A) provides exactly 5 physical qubits. Compiling an unreduced 6-vertex graph directly would require $\ge 6$ physical qubits.

### 4.2 Exact $\mathbb{Z}_2$ Spin-Inversion Symmetry Reduction
Because the Max-Cut value is strictly invariant under global bitwise inversion ($x \mapsto \mathbf{1} \oplus x$), fixing reference bit $x_0 = 0$ selects exactly one canonical representative from each complementary pair without altering cut values:
1. The 5 remaining vertices $x_1, \dots, x_5$ map bijectively to 5 quantum variables $q_0, \dots, q_4$.
2. Edges not incident to node 0 ($(u, v)$ with $u, v \ge 1$) map to standard two-body Ising terms:
   $$x_u \oplus x_v = \frac{I - Z_u Z_v}{2}$$
3. Edges incident to node 0 ($(0, 1)$ and $(0, 2)$ with $x_0 = 0$) simplify to linear longitudinal fields:
   $$0 \oplus x_v = x_v = \frac{I - Z_v}{2}$$

Substituting into the minimization cost Hamiltonian ($H_C = -C(x)$):
$$H_C^{(5Q)} = \frac{1}{2} \sum_{(u, v) \in E, u, v \ge 1} Z_u Z_v + \frac{1}{2} Z_1 + \frac{1}{2} Z_2 - 4.0 \cdot I$$

### 4.3 Spectral Equivalence & Invariants
* **State Space:** Condensed bijectively from $2^6 = 64$ to $2^5 = 32$ computational states.
* **Ground State Energy:** $E_0 = -6.0000$, exactly satisfying $E_0 = -C_{\max}$.
* **Optima Preservation:** The 10 original global optima map to exactly 5 unique 5-variable assignments, all achieving $C(x) = 6.0000$.
* **Full Operator Invariance:** Across all 32 basis states $|x\rangle$:
  $$C(x) = -f_{\text{QUBO}}(x) = -E_{\text{Ising}}(s) = -\langle x | H_C | x \rangle$$

### 4.4 Regulatory Policy Disclosure
> [!NOTE]
> **Regulatory Status:** The Updated Challenge Kit contains a general instruction: *"Do not delete variables or alter the objective function to force the problem onto smaller hardware unless that reduction is explicitly part of the problem statement or an approved technique."*
>
> We emphasize the critical distinction: graph vertex deletion (dropping a node and its edges) alters the problem and corrupts $C_{\max}$, whereas parity fixing ($x_0 = 0$) preserves the exact complete graph and all 8 edge interactions bijectively. However, because organizers have not issued a formal written ruling for Track O1, we report this reduction transparently and have submitted a clarification request.

---

## 5. QAOA Variational Protocol & Parameter Certification

* **Ansatz Structure:** Level-1 QAOA ansatz ($p=1$) alternating cost unitary $U(H_C, \gamma) = e^{-i \gamma H_C^{(5Q)}}$ and transverse mixer $U(H_M, \beta) = e^{-i \beta \sum_{u=0}^4 X_u}$:
  $$|\psi(\gamma, \beta)\rangle = U(H_M, \beta) U(H_C, \gamma) |+\rangle^{\otimes 5}$$
* **Shared Parameter Certification:** Variational angles were determined through deterministic multi-start optimization on the statevector simulator and held **strictly frozen** across all processors:
  $$\gamma^* = 2.527058\text{ rad}, \quad \beta^* = 2.698287\text{ rad}$$
* **Analytic Expectation Values (Statevector):**
  * Expected cut: $\langle C \rangle_{\text{analytic}} = 5.03998 \approx 5.0400$
  * Approximation ratio: $\alpha_{\text{analytic}} = \frac{5.0400}{6.0000} = 0.8400\text{ (84.00\%)}$
  * Optimal-bitstring probability: $P(\text{opt})_{\text{analytic}} = 0.41566\text{ (41.57\%)}$
* **Measurement Decoding Protocol:** Measurements recorded in Qiskit little-endian order ($q_4 q_3 q_2 q_1 q_0$) are reversed to canonical order $[q_0, q_1, q_2, q_3, q_4]$, augmented with fixed bit $x_0 = 0$, and evaluated against the 6-vertex cut objective.

---

## 6. Hardware Processor Specifications & Compilation Baseline

All evaluations target genuine physical processor topologies conforming to the Tier 1 *Updated Qiskit Fall Fest 2026 Challenge Kit*:

```
+------------------------------------------------------------------------------------------------------------------+
|                                        TARGET HARDWARE ARCHITECTURES                                             |
+-------------+----------------------+----------+---------+--------------------+---------+------------+------------+
| Target      | Architecture Family  | Phys Q   | Act Q   | Coupling Edges     | Max Deg | Spec Hash  | Transpiler |
+-------------+----------------------+----------+---------+--------------------+---------+------------+------------+
| Processor A | 5Q Linear Chain CX   | 5        | 5       | 4 (8 CX pairs)     | 2       | aa9e30240a | SABRE Lvl 1|
| Processor B | 9Q Sparse Tree CX    | 9        | 5       | 8 (16 CX pairs)    | 3       | 341d471380 | SABRE Lvl 1|
| Processor D | 8Q Chorded Mesh CX   | 8        | 5       | 10 (20 CX pairs)   | 3       | a60ecf34eb | SABRE Lvl 1|
+-------------+----------------------+----------+---------+--------------------+---------+------------+------------+
```

### 6.1 Processor A Specification
* **Topology:** 5-qubit linear chain: `{(0, 1), (1, 2), (2, 3), (3, 4)}`.
* **Basis Gates:** Native `["rz", "sx", "x", "cx"]` with bidirectional CX.
* **Coupling Diagram:** [`results/verified_ab_v4/figures/figure2_processor_a_coupling_map.svg`](../results/verified_ab_v4/figures/figure2_processor_a_coupling_map.svg).

### 6.2 Processor B Specification
* **Topology:** 9-qubit sparse tree: `{(0, 1), (1, 2), (2, 3), (2, 4), (4, 5), (5, 6), (4, 7), (7, 8)}`.
* **Basis Gates:** Native `["rz", "sx", "x", "cx"]` with bidirectional CX.
* **Active Allocation:** 5 active physical qubits `[1, 2, 3, 4, 5]` embedded within the 9-qubit lattice.
* **Coupling Diagram:** [`results/verified_ab_v4/figures/figure3_processor_b_coupling_map.svg`](../results/verified_ab_v4/figures/figure3_processor_b_coupling_map.svg).

### 6.3 Topology Conflict Register
> [!NOTE]
> **Source Conflict:** The companion document *Processor A/B Benchmark Configuration PDF* (labeled *"For Organizer Approval"*) specifies alternate coupling maps (a T-tree for A, and a 12-edge cyclic graph for B).
>
> Pursuant to the Phase 0 source hierarchy, the repository adheres to the **Tier 1 Updated Challenge Kit** as the operational baseline. The companion PDF is classified as an unratified provisional draft.

### 6.4 Transpilation Protocol & Common Noise Baseline
* **Transpiler Protocol:** Qiskit 2.x `generate_preset_pass_manager(optimization_level=1)` with SABRE layout and routing, fixed seed 42 (`seed_transpiler = 42`).
* **Noise Channel:** Uniform synthetic noise across all processors:
  * Single-qubit depolarizing error: $p_{1Q} = 0.001$ per single-qubit gate (`sx`, `x`).
  * Two-qubit depolarizing error: $p_{CX} = 0.005$ per CX gate.
  * Symmetric readout bit-flip error: $p_{RO} = 0.01$ per measured qubit.
* **Shot Budget:** Exactly **4096 shots** per experiment case ($N = 24,576$ total shots).

---

## 7. Master Benchmark Results (Version 4.0.0)

All results are directly extracted from serialized raw count distributions and transpiled circuits in [`results/verified_ab_v4/`](../results/verified_ab_v4/):

### Table 1: End-to-End Architectural and Solution Quality Performance Breakdown

| Experiment Case | Target Backend | Circuit Depth | Total Gates | 2Q Gates (CX) | Routing SWAPs | Mean Cut $\langle C \rangle$ | Standard Error | Approx Ratio $\alpha$ | Success Prob $P(\text{opt})$ | Wilson 95% CI | Relative Noise Loss |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Processor A — Ideal** | `Processor_A` | 58 | 84 | 18 | 2 | 5.0557 | 0.0166 | 84.26% | 0.4270 (1749/4096) | [0.412, 0.442] | Baseline |
| **Processor A — Noisy** | `Processor_A` | 58 | 84 | 18 | 2 | 4.8784 | 0.0187 | 81.31% | 0.3809 (1560/4096) | [0.366, 0.396] | $-3.51\%$ ($\Delta = -0.1772$) |
| **Processor B — Ideal** | `Processor_B` | 52 | 78 | 15 | 1 | 5.0557 | 0.0166 | 84.26% | 0.4270 (1749/4096) | [0.412, 0.442] | Baseline |
| **Processor B — Noisy** | `Processor_B` | 52 | 78 | 15 | 1 | 4.8923 | 0.0186 | 81.54% | 0.3845 (1575/4096) | [0.370, 0.400] | $-3.23\%$ ($\Delta = -0.1633$) |
| **Processor D — Ideal** | `Processor_D` | 36 | 66 | 12 | 0 | 5.0557 | 0.0166 | 84.26% | 0.4270 (1749/4096) | [0.412, 0.442] | Baseline |
| **Processor D — Noisy** | `Processor_D` | **36** | **66** | **12** | **0** | **4.9141** | **0.0183** | **81.90%** | **0.3887 (1592/4096)**| **[0.374, 0.404]** | **$-2.80\%$ ($\Delta = -0.1416$)** |

*Note: Approximation ratio is defined as $\alpha = \frac{\langle C \rangle}{C_{\max}}$ with denominator $C_{\max} = 6.0000$. Success probability is $P(\text{opt}) = \frac{N_{\text{opt}}}{4096}$.*

---

## 8. Custom Processor D Design & Evaluation (Extension)

### 8.1 Bottleneck Diagnosis on Processors A and B
Compilation analysis revealed the primary hardware bottleneck:
* **Processor A (Linear Chain):** Treewidth 1 forces 2 routing SWAPs (+6 CX gates, $+50\%$ 2Q overhead) and dilates depth to 58.
* **Processor B (Sparse Tree):** Branching treewidth 1 forces 1 routing SWAP (+3 CX gates, $+25\%$ 2Q overhead) and dilates depth to 52.

### 8.2 Processor D Architecture
Processor D ([`processors/processor_d/hardware_spec.json`](../processors/processor_d/hardware_spec.json)) was engineered to eliminate routing SWAPs:
* **Qubit Count:** 8 physical qubits (strictly $\le 12$ constraint).
* **Coupling Topology:** Chorded ring mesh with 10 physical edges: `{(0,1), (0,2), (1,3), (2,3), (2,4), (3,4), (4,5), (5,6), (6,7), (0,7)}`.
* **Degree Constraint:** Maximum physical degree $\le 3$ (ensuring realistic transmon planar layout).
* **Compilation Outcome:** Embeds all 6 problem interactions with **0 SWAPs, exactly 12 CX gates, and depth 36** (a **$37.9\%$ depth reduction** vs Processor A).
* **Coupling Diagram:** [`results/verified_ab_v4/figures/figure4_processor_d_coupling_map.svg`](../results/verified_ab_v4/figures/figure4_processor_d_coupling_map.svg).

### 8.3 Phasing Disclosure
The Updated Challenge Kit states Processor D is expected for quantum problem statements, while the Phase 1 Participant Instructions state Phase 1 evaluation terminates at A/B. We present Processor D as an evidence-supported custom extension while keeping A/B as the primary benchmark.

---

## 9. Statistical Hypothesis Testing & Rigorous Uncertainty Analysis

From [`results/verified_ab_v4/tables/statistical_hypothesis_tests_complete.csv`](../results/verified_ab_v4/tables/statistical_hypothesis_tests_complete.csv):

### Table 2: Pairwise Statistical Hypothesis Tests ($N = 4096$ shots, $\alpha = 0.05$)

| Hypothesis Test | Delta Mean $\Delta \langle C \rangle$ | Welch $t$-statistic | $p$-value ($t$-test) | Delta $P(\text{opt})$ | $z$-statistic | $p$-value ($z$-test) | Statistical Finding |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Processor A: Ideal vs Noisy** | $-0.1772$ | $+7.0974$ | $1.27 \times 10^{-12}$ | $-0.0461$ | $-4.2758$ | $1.90 \times 10^{-5}$ | Statistically Significant ($p < 0.05$) |
| **Processor B: Ideal vs Noisy** | $-0.1633$ | $+6.5609$ | $5.35 \times 10^{-11}$ | $-0.0425$ | $-3.9317$ | $8.43 \times 10^{-5}$ | Statistically Significant ($p < 0.05$) |
| **Processor D: Ideal vs Noisy** | $-0.1416$ | $+5.7362$ | $9.68 \times 10^{-9}$ | $-0.0383$ | $-3.5450$ | $3.93 \times 10^{-4}$ | Statistically Significant ($p < 0.05$) |
| **Noisy: Processor D vs Processor A** | $+0.0356$ | $+1.3642$ | $0.1725$ | $+0.0078$ | $+0.7267$ | $0.4674$ | No Significant Difference Detected |
| **Noisy: Processor D vs Processor B** | $+0.0217$ | $+0.8340$ | $0.4043$ | $+0.0042$ | $+0.3857$ | $0.6997$ | No Significant Difference Detected |

### Scientific Findings:
1. **Noise Impact:** Depolarizing and readout noise degrade mean cut value and ground-state success probability with overwhelming statistical significance ($p < 10^{-8}$) across all architectures.
2. **Monotonic Noise Damping:** Noise-induced degradation dampens monotonically as routing depth decreases:
   - Processor A (Depth 58): $-3.51\%$ mean cut degradation
   - Processor B (Depth 52): $-3.23\%$ mean cut degradation
   - Processor D (Depth 36): **$-2.80\%$** mean cut degradation
3. **Statistical Power Limitation:** The $+0.0356$ noisy cut advantage of Processor D over Processor A is physically consistent with shallow depth, but at $N = 4096$ shots, the margin is within the 95% confidence interval ($p = 0.1725 > 0.05$). We report this with scientific candor rather than asserting unproven equivalence.

---

## 10. Publication Figure Index

All figures are archived in publication-grade vector SVG format:
* [`Figure 1: Canonical Max-Cut Problem Graph`](../results/verified_ab_v4/figures/figure1_maxcut_problem_graph.svg)
* [`Figure 2: Processor A Linear Coupling Map`](../results/verified_ab_v4/figures/figure2_processor_a_coupling_map.svg)
* [`Figure 3: Processor B Sparse Tree Coupling Map`](../results/verified_ab_v4/figures/figure3_processor_b_coupling_map.svg)
* [`Figure 4: Processor D Chorded Mesh Coupling Map`](../results/verified_ab_v4/figures/figure4_processor_d_coupling_map.svg)
* [`Figure 5: Logical vs. Transpiled Circuit Schematics`](../results/verified_ab_v4/figures/figure5_logical_vs_transpiled_circuits.svg)
* [`Figure 6: Ideal vs. Noisy Cut Sampling Distributions`](../results/verified_ab_v4/figures/figure6_ideal_vs_noisy_distributions.svg)
* [`Figure 7: Architecture Compilation Resource Trade-Offs`](../results/verified_ab_v4/figures/figure7_architecture_resource_tradeoffs.svg)
* [`Figure 8: Combined A/B/D Performance & Noise Resilience`](../results/verified_ab_v4/figures/figure8_combined_abd_performance_comparison.svg)

---

## 11. Historical Record Preservation

To maintain complete scientific reproducibility and avoid data leakage:
* `results/verified_ab_v2/`: Preserved Version 2 runs (7Q ring, ECR basis, 1024 shots).
* `results/verified_ab_v3/`: Preserved Version 3 runs (7Q heavy-hex, ECR/CZ basis, 2048 shots).
* `results/verified_ab_v4/`: **Authoritative current benchmark** (4096 shots, CX basis, custom Processor D).
* Comparison table: [`results/verified_ab_v4/tables/historical_comparison_v2_v3_v4.md`](../results/verified_ab_v4/tables/historical_comparison_v2_v3_v4.md).

---

## 12. Reproduction Commands & Verification

```powershell
# 1. Run standalone main pipeline (zero external dependencies)
python main.py

# 2. Run artifact validation harness
python scripts/validate_artifacts.py

# 3. Run automated regression test suite
python -m unittest discover -s tests -p "test_phase*.py"

# 4. Re-execute Version 4 experiments (requires Qiskit 2.x)
python scripts/run_verified_ab_v4_experiments.py
```

---

## 13. Unresolved Organizer Questions

The following questions require formal organizer clarification:
1. **Symmetry Reduction:** *"For PS-O1 in Phase 1, is exact global-complement symmetry reduction ($x_0 = 0$) acceptable for implementing the six-vertex Max-Cut problem on five-qubit Processor A, provided the canonical graph and optimum are preserved? Or is a six-logical-variable formulation required despite Processor A having only five physical qubits?"*
2. **Coupling Map Discrepancy:** *"For Phase 1 PS-O1, should we use the Processor A linear chain and Processor B nine-qubit sparse tree specified in the Updated Challenge Kit, or the alternate A/B coupling maps in the companion PDF marked 'For Organizer Approval'?"*
3. **Processor D Phasing:** *"Is custom Processor D an expected Phase 1 deliverable under the Updated Challenge Kit workflow, or strictly reserved for Phase 2 under the Phase 1 Participant Instructions?"*
