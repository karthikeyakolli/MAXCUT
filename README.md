# Qiskit Fall Fest 2026 — Track O1 Quantum Optimization (Max-Cut)
## PS-O1: Max-Cut on a Weighted Graph — Complete Authoritative Final Benchmark
### Controlled Hardware Comparison: Processor A vs. Processor B vs. Custom Processor D

**Competition Event:** Qiskit Fall Fest 2026
**Track:** Quantum Optimization — **Problem ID: PS-O1**
**Repository Owner / Team:** [Karthikeya Kolli](https://github.com/karthikeyakolli)
**Repository:** [https://github.com/karthikeyakolli/MAXCUT](https://github.com/karthikeyakolli/MAXCUT)
**Problem Statement:** PS-O1 — Max-Cut on a Weighted Graph
**Selected Problem Instance:** Canonical 6-Vertex Participant-Created Weighted Graph [`instances/participant/o1_maxcut_weighted_v5.json`](instances/participant/o1_maxcut_weighted_v5.json)
**Edge Weight Range & Sequence:** Nonuniform integer edge weights in $[1, 5]$ with reproducible sequence `[1, 2, 3, 4, 5, 2, 4, 3]`
**Exact Classical Ground Truth:** $C_{\max} = 20.0000$ (Optimal Cut Ratio: $83.33\%$, 2 optimal states: `001100`, `110011`)
**Primary Quantum Formulation:** Full 6-Variable Logical QAOA ($p=1$) with Multistart Classical Variational Optimization
**Evaluated Processor Architectures:**
- **Processor A:** 5 Physical Qubits, Nearest-Neighbor Linear Chain, Native `cx` Entangler — *Hardware Capacity Infeasible for Full 6Q Problem; strictly segregated auxiliary 5Q experiment*
- **Processor B:** 9 Physical Qubits, Sparse Tree, Native `cx` Entangler — *Updated Challenge Kit Topology, 6 Active Mapped Physical Qubits*
- **Processor D (Custom):** 8 Physical Qubits, Chorded Ring Mesh (Planar, Degree $\le 3$), Native `cx` Entangler — *Resolves Processor B tree routing bottleneck*
**Authoritative Result Suite:** `results/verified_o1_v5/` (All historical archives `v2`, `v3`, `v4` preserved intact)
**Automated Regression Suite:** 163 Passing Tests (`pytest -v tests`)
**Artifact Integrity Validation:** 100% Passing (`python scripts/validate_artifacts.py`)

---

> ### AI-Assistance Disclosure
> In compliance with hackathon submission guidelines: AI pair programming tools (Google Antigravity / Gemini) were utilized for code scaffolding, automated test generation, and documentation linting. All mathematical proofs, exact classical brute-force verifications, QAOA ansatz constructions, hardware adapter implementations, noise models, and empirical benchmark evaluations were designed, derived, executed, and verified by the authors through deterministic test suites and direct data artifact audits. All reported numbers originate directly from executed computational artifacts stored in `results/verified_o1_v5/`.

---

> [!IMPORTANT]
> ### Quantum Advantage Disclaimer: NOT DEMONSTRATED
> This 6-vertex weighted Max-Cut instance does **not** demonstrate quantum advantage over classical computation.
>
> The exact classical exhaustive solver evaluates all 64 candidate partitions in **$0.106\,\text{ms}$** ($0.000106\,\text{s}$), certifying the global maximum cut $C_{\max} = 20.0000$ with $100\%$ certainty. In contrast, depth $p=1$ QAOA on noisy quantum processors produces approximation ratios of $81.6\%\text{--}82.1\%$ and requires transpilation, routing, and error-mitigation overhead. This project demonstrates **architectural compilation and noise resilience trade-offs**, not quantum supremacy.

---

## 1. Problem Definition & Weighted Graph Instance

The **Maximum Cut (Max-Cut)** problem is a fundamental NP-hard combinatorial optimization challenge. Given an undirected weighted graph $G = (V, E, w)$ with vertex set $V$, edge set $E$, and integer edge weights $w_{ij}$, the objective is to partition $V$ into two complementary subsets $S_1$ and $S_2$ to maximize the total weight of cut edges crossing the partition boundary:

$$C(x) = \sum_{(i, j) \in E} w_{ij} (x_i \oplus x_j) = \sum_{(i, j) \in E} w_{ij} (x_i + x_j - 2x_i x_j)$$

where binary variable $x_i \in \{0, 1\}$ assigns vertex $i$ to subset $S_1$ ($x_i=0$) or $S_2$ ($x_i=1$).

### Canonical 6-Vertex Weighted Problem Graph
In accordance with updated PS-O1 requirements permitting participant-selected 6-vertex weighted graphs with integer edge weights in $[1, 5]$, we evaluate the canonical non-uniform instance [`instances/participant/o1_maxcut_weighted_v5.json`](instances/participant/o1_maxcut_weighted_v5.json):
* **Vertices ($|V|=6$):** $V = \{0, 1, 2, 3, 4, 5\}$
* **Edges ($|E|=8$):** Canonical sorted edge list with reproducible integer weights:
  $e_0 = (0, 1, 1), e_1 = (0, 2, 2), e_2 = (1, 2, 3), e_3 = (1, 3, 4), e_4 = (2, 4, 5), e_5 = (3, 4, 2), e_6 = (3, 5, 4), e_7 = (4, 5, 3)$
* **Total Graph Weight ($W$):** $W = \sum_{(i,j) \in E} w_{ij} = 24.0$
* **Schema Integrity:** 0 self-loops, 0 multigraph edges, integer weights $\in [1, 5]$, hash `e96147a93b3a72ab`.

---

## 2. Exact Classical Reference Ground Truth

To establish an authoritative ground truth for quantum evaluation, an exact exhaustive combinatorial solver was executed across all $2^6 = 64$ computational states ([`results/verified_o1_v5/data/classical_reference.json`](results/verified_o1_v5/data/classical_reference.json)):
* **Exact Global Maximum Cut:** $C_{\max} = 20.0000$ (Cut Ratio: $20.0 / 24.0 = 83.33\%$).
* **Classical Solution Runtime:** $0.106\,\text{ms}$ on standard CPU ($0.000106\text{ s}$).
* **Optimal Solution States (2):** Exactly two complementary assignments achieve $C(x) = 20.0000$:
  - `001100`: Partition $S_1 = \{0, 1, 4, 5\}$, $S_2 = \{2, 3\}$
  - `110011`: Partition $S_1 = \{2, 3\}$, $S_2 = \{0, 1, 4, 5\}$
* **Cut Edges (6 of 8 cut):**
  $(0,2)[w=2] + (1,2)[w=3] + (1,3)[w=4] + (2,4)[w=5] + (3,4)[w=2] + (3,5)[w=4] = 2 + 3 + 4 + 5 + 2 + 4 = 20.0$.
* **Uncut Edges (2 internal):** $(0,1)[w=1] + (4,5)[w=3] = 4.0$.
* **Global-Complement Symmetry:** Verified $\sim `001100` = `110011`$.

---

## 3. Mathematical Formulation: QUBO, Ising & QAOA Ansatz

### QUBO & Ising Minimization Mapping
1. **QUBO Objective (Minimization):**
   $$f_{\text{QUBO}}(x) = -C(x) = \sum_{(i,j) \in E} w_{ij} (2 x_i x_j - x_i - x_j)$$
2. **Ising Spin Transformation:**
   Substituting $x_i = \frac{I - Z_i}{2}$ into $-C(x)$ yields the Cost Hamiltonian:
   $$H_C = \sum_{(i,j) \in E} \frac{w_{ij}}{2} Z_i Z_j - \left(\frac{1}{2} \sum_{(i,j) \in E} w_{ij}\right) I = \sum_{(i,j) \in E} \frac{w_{ij}}{2} Z_i Z_j - 12.0 \cdot I$$
   For any computational basis state $|x\rangle$:
   $$\langle x | H_C | x \rangle = -C(x)$$
   Minimizing $\langle H_C \rangle$ directly maximizes expected cut $\langle C \rangle$. Exhaustive numerical verification confirms exact equivalence for all 64 assignments.

### QAOA Protocol ($p=1$)
1. **Ansatz State:** $|\psi(\gamma, \beta)\rangle = U_M(\beta) U_C(\gamma) |+\rangle^{\otimes 6} = \left(\prod_{i=0}^5 e^{-i \beta X_i}\right) \left(\prod_{(i,j) \in E} e^{-i \gamma \frac{w_{ij}}{2} Z_i Z_j}\right) |+\rangle^{\otimes 6}$
2. **Multistart Variational Optimization:**
   Executed 10 independent random restarts with classical optimizer COBYLA in $[0, 2\pi) \times [0, \pi)$ with base seed 42:
   - **Optimal Parameters:** $\gamma^* = 6.087282\,\text{rad}$, $\beta^* = 1.942981\,\text{rad}$
   - **Theoretical Expected Cut:** $\langle C \rangle = 16.8182$ (Approximation Ratio: $84.09\%$)
   - **Analytic Ground-State Probability:** $P(\text{opt}) = 13.57\%$

---

## 4. Hardware Processor Architectures & Capacity Analysis

```
+---------------------------------------------------------------------------------------------------------------+
|                                      TARGET HARDWARE ARCHITECTURES                                            |
+-------------+-----------------------+----------+--------------------+---------+---------+-------+-------------+
| Target      | Architecture Family   | Phys Q   | Mapped Core        | Phys L  | Max Deg | SWAPs | Status      |
+-------------+-----------------------+----------+--------------------+---------+---------+-------+-------------+
| Processor A | 5Q Linear Chain CX    | 5        | INFEASIBLE (6 > 5) | 4 links | 2       | N/A   | Capacity Ref|
| Processor B | 9Q Sparse Tree CX     | 9        | [2, 3, 4, 5, 6, 7] | 8 links | 3       | 3     | Compliant   |
| Processor D | 8Q Chorded Mesh CX    | 8        | [0, 1, 2, 3, 4, 7] | 10 links| 3       | 2     | Optimized   |
+-------------+-----------------------+----------+--------------------+---------+---------+-------+-------------+
```

### Processor A Capacity Constraint Handling
- **Hardware Limitation:** Processor A possesses 5 physical qubits arranged in a nearest-neighbor linear chain: `(0,1), (1,2), (2,3), (3,4)`.
- **Benchmark Policy:** The 6-variable problem strictly requires 6 physical qubits. The transpiler correctly raises `TranspilerError: More virtual qubits (6) exist than physical (5)`.
- **Honest Compliance:** We do not disguise a 5-variable circuit as a full 6-variable execution, nor do we alter Processor A's topology. Processor A serves as a capacity baseline.
- **Auxiliary Experiment:** A separate 5-variable symmetry-reduced experiment ($x_0=0$) is documented strictly as an auxiliary benchmark (transpiled depth 61, 21 CX, 3 SWAPs).

### Processor B Topology & Compilation
- **Specification:** Official 9-qubit sparse tree topology with bidirectional CX connectivity.
- **Compilation:** Virtual qubits mapped to active sub-tree `[2, 3, 4, 5, 6, 7]`. Incurs 3 routing SWAPs (9 routing CX gates, $+56.2\%$ CX overhead) due to cycle-closing edges, producing transpiled circuit depth of 52 and 25 CX gates.

### Processor D Custom Architecture Rationale
- **Design Budget:** 8 physical qubits ($\le 12$ budget rule compliant).
- **Topology:** Chorded ring mesh with outer ring `(0,1), (1,3), (3,4), (4,5), (5,6), (6,7), (7,0)` and planar internal chords `(0,2), (2,3), (2,4)`. Strictly maintains transmon maximum vertex degree $\le 3$.
- **Measured Advantage:** Directly eliminates routing bottlenecks, achieving transpiled depth **41** (**21.2% depth reduction** vs. B) and **22 CX gates** (**12.0% reduction** vs. B) with only 2 routing SWAPs.

---

## 5. Master Authoritative Benchmark Results (Version 5)

All experiments evaluated under frozen benchmark controls: 4096 shots per case, seed 42, transpiler optimization level 1 (SABRE), native basis `["rz", "sx", "x", "cx"]`, and uniform depolarizing noise ($p_{1Q}=0.001, p_{CX}=0.005, p_{RO}=0.01$):

| Experiment Case | Target Backend | Mode | Depth | 2Q CX | Routing SWAPs | Mean Cut $\langle C \rangle$ | Standard Error | Approx Ratio $\alpha$ | Success Prob $P(\text{opt})$ | 95% Wilson CI $P(\text{opt})$ |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Processor B — Ideal** | `Processor_B` (9Q) | Ideal | 52 | 25 | 3 | 16.9321 | 0.0512 | 84.66% | 0.1460 (598/4096) | [0.1355, 0.1571] |
| **Processor B — Noisy** | `Processor_B` (9Q) | Noisy | 52 | 25 | 3 | 16.4282 | 0.0560 | 82.14% | 0.1292 (529/4096) | [0.1192, 0.1398] |
| **Processor D — Ideal** | `Processor_D` (8Q) | Ideal | 41 | 22 | 2 | 16.7678 | 0.0529 | 83.84% | 0.1240 (508/4096) | [0.1143, 0.1345] |
| **Processor D — Noisy** | `Processor_D` (8Q) | Noisy | 41 | 22 | 2 | 16.3276 | 0.0567 | 81.64% | 0.1121 (459/4096) | [0.1028, 0.1221] |

*Serialized in [`results/verified_o1_v5/tables/master_version5_metrics.md`](results/verified_o1_v5/tables/master_version5_metrics.md) and [`master_version5_metrics.csv`](results/verified_o1_v5/tables/master_version5_metrics.csv).*

### Statistical Significance (Welch's $t$-test & 2-Proportion $z$-test)
- **Noise Impact on Processor B:** $\Delta \langle C \rangle = -0.5039$ ($t = 6.645$, $p = 3.25 \times 10^{-11}$, statistically significant at $\alpha = 0.05$).
- **Noise Impact on Processor D:** $\Delta \langle C \rangle = -0.4402$ ($t = 5.679$, $p = 1.40 \times 10^{-8}$, statistically significant at $\alpha = 0.05$).
- **Noisy Comparison (D vs. B):** Difference in mean cut $\Delta = -0.1006$ ($t = -1.263$, $p = 0.2066$) is not statistically significant, while Processor D delivers a 21.2% reduction in circuit depth and 12.0% reduction in 2Q gate overhead.

---

## 6. Scientific Interpretation & Quantum Advantage Disclaimer

### Hardware Architecture Trade-Offs
1. **Compilation Overhead:** On tree topologies like Processor B, cycle-closing problem interactions require routing SWAPs that significantly inflate circuit depth. Adding strategic chords in Processor D reduces routing overhead while preserving physical planar fabricability.
2. **Noise Resilience:** Noisy simulation demonstrates that both processors reliably identify the global optimum ($C_{\max} = 20.0$), sampling an optimal cut in over $11.2\%\text{--}12.9\%$ of shots ($>450$ counts out of 4096).

### Quantum Advantage Disclaimer
> [!IMPORTANT]
> **Definitive Quantum Advantage Disclaimer:**
> This 6-vertex Max-Cut instance does **not** demonstrate quantum advantage over classical computation.
>
> The exact classical exhaustive solver evaluates all 64 partitions in **$0.106\,\text{ms}$**, certifying the global optimum with $100\%$ certainty. Level-1 QAOA on NISQ hardware achieves an approximation ratio of $81.6\%\text{--}84.7\%$ and requires compilation, routing, and readout overhead. This project demonstrates **variational algorithm design, hardware mapping, and architectural benchmarking**, not quantum supremacy.

---

## 7. Historical Record Preservation

To maintain complete archival integrity, all historical benchmark runs remain preserved in their original directories:
- `results/verified_ab_v2/`: Historical version 2 runs (7-qubit ring Processor B, ECR basis, 1024 shots).
- `results/verified_ab_v3/`: Historical version 3 runs (9-qubit tree Processor B, ECR basis, asymmetric readout, 1024 shots).
- `results/verified_ab_v4/`: Historical version 4 runs (unit-weight graph, 5-qubit symmetry-reduced formulation, 4096 shots).
- `results/verified_o1_v5/`: **Authoritative current Version 5 benchmark** (PS-O1 compliant weighted graph, exact optimum $C_{\max}=20.0$, full 6-variable execution on B and D, honest capacity handling on A).

---

## 8. Quickstart & Reproduction Commands

### Environment Setup (Verified on Python 3.12)
```bash
# 1. Clone repository
git clone https://github.com/karthikeyakolli/MAXCUT.git
cd MAXCUT

# 2. Install dependencies and editable package
pip install -r requirements.txt
pip install -e .
```

### Reproduce Authoritative Version 5 Benchmarks
```powershell
# 1. Run Version 5 primary benchmark pipeline (generates results/verified_o1_v5/)
python scripts/run_verified_o1_v5_experiments.py

# 2. Generate publication vector SVG figures
python scripts/generate_v5_figures.py

# 3. Build and pre-render interactive notebook
python scripts/build_and_render_v5_notebook.py

# 4. Run standalone main entrypoint
python main.py

# 5. Run complete automated regression test suite (163 tests)
python -m pytest -v tests

# 6. Validate full artifact integrity
python scripts/validate_artifacts.py
```

---

## 9. Deliverables & Artifacts Index

- **Interactive Pre-Rendered Notebook:** [`main.ipynb`](main.ipynb)
- **Technical Report:** [`report/analysis.md`](report/analysis.md)
- **Submission Audit Report:** [`docs/audit/FINAL_HACKATHON_READINESS_REPORT.md`](docs/audit/FINAL_HACKATHON_READINESS_REPORT.md)
- **Problem Instance:** [`instances/participant/o1_maxcut_weighted_v5.json`](instances/participant/o1_maxcut_weighted_v5.json)
- **Publication Figures (8 SVGs):**
  - [`Figure 1: Problem Graph & Optimum`](results/verified_o1_v5/figures/figure1_maxcut_problem_graph.svg)
  - [`Figure 2: Processor A Capacity Analysis`](results/verified_o1_v5/figures/figure2_processor_a_coupling_map.svg)
  - [`Figure 3: Processor B Coupling Map`](results/verified_o1_v5/figures/figure3_processor_b_coupling_map.svg)
  - [`Figure 4: Processor D Custom Coupling Map`](results/verified_o1_v5/figures/figure4_processor_d_coupling_map.svg)
  - [`Figure 5: Logical vs Transpiled Circuits`](results/verified_o1_v5/figures/figure5_logical_vs_transpiled_circuits.svg)
  - [`Figure 6: Empirical Cut Distributions`](results/verified_o1_v5/figures/figure6_ideal_vs_noisy_distributions.svg)
  - [`Figure 7: Architecture Resource Trade-Offs`](results/verified_o1_v5/figures/figure7_architecture_resource_tradeoffs.svg)
  - [`Figure 8: Master Benchmark Summary`](results/verified_o1_v5/figures/figure8_combined_benchmark_performance.svg)
- **Raw Count Data:** [`results/verified_o1_v5/counts_*.json`](results/verified_o1_v5/) (4096 shots per file)
- **Compilation Circuits:** [`results/verified_o1_v5/circuits/`](results/verified_o1_v5/circuits/) (QASM export)
