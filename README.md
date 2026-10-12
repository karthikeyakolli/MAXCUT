# Qiskit Fall Fest 2026 — Track O1 Quantum Optimization (Max-Cut)
## Authoritative Comparative Architectural Benchmark: Processor A vs. Processor B vs. Custom Processor D

**Track Selection:** Quantum Optimization — **Problem Code: O1**  
**Selected Problem:** Maximum Cut (Max-Cut) on Canonical 6-Vertex Challenge Graph  
**Algorithm:** Quantum Approximate Optimization Algorithm (QAOA, $p=1$) vs. Exact Classical Exhaustive Ground Truth  
**Target Architectures:**
- **Processor A:** 5 Physical Qubits, Linear Chain, Native `cx` Entangler
- **Processor B:** 9 Physical Qubits, Sparse Tree, Native `cx` Entangler
- **Processor D (Custom):** 8 Physical Qubits, Chorded Ring Mesh (Degree $\le 3$), Native `cx` Entangler
**Logical Formulation:** 5-Qubit Exact $\mathbb{Z}_2$ Complement-Symmetry Reduced QAOA ($x_0 = 0$)  
**Benchmark Protocols:** 4096 shots per case, Seed 42, Uniform Synthetic Noise ($p_{1Q}=0.001, p_{CX}=0.005, p_{RO}=0.01$)  
**Automated Regression Suite:** 34 Passing Unit/Regression Tests (`python -m unittest discover -s tests -p "test_phase*.py"`)  
**Official Repository:** [https://github.com/karthikeyakolli/MAXCUT](https://github.com/karthikeyakolli/MAXCUT)  

---

> ### AI-Assistance Disclosure
> In compliance with hackathon submission guidelines: AI pair programming tools (Google Antigravity / Gemini) were utilized for code scaffolding, automated test generation, and documentation linting. All mathematical proofs, symmetry reductions, hardware adapter implementations, and empirical benchmark evaluations were designed, derived, and verified by the authors through deterministic test suites and direct data artifact audits.

---

## 1. Problem Definition & Canonical Instance

The **Maximum Cut (Max-Cut)** problem is a canonical NP-hard combinatorial optimization challenge. Given an undirected graph $G = (V, E)$ with edge weights $w_{uv}$, the objective is to partition the vertices $V$ into two complementary subsets $S$ and $\bar{S}$ to maximize the total weight of cut edges crossing the boundary:

$$C(x) = \sum_{(u, v) \in E} w_{uv} (x_u \oplus x_v) = \sum_{(u, v) \in E} w_{uv} [x_u(1 - x_v) + x_v(1 - x_u)]$$

where binary decision variable $x_u = 0$ denotes $u \in S$ and $x_u = 1$ denotes $u \in \bar{S}$.

For the **O1 Max-Cut** benchmark, the official organizer instance [`instances/challenge/o1_maxcut_instance.json`](instances/challenge/o1_maxcut_instance.json) is ingested directly without modification:
* **Vertices:** $|V| = 6$ ($V = \{0, 1, 2, 3, 4, 5\}$).
* **Edges:** $|E| = 8$ edges with uniform integer weights $w_{uv} = 1.0$ (total graph weight $W = 8.00$).
* **Edge Set:** $(0, 1), (0, 2), (1, 2), (1, 3), (2, 4), (3, 4), (3, 5), (4, 5)$.
* **Graph Structure:** Connected planar graph with maximum degree 4 (node 3) and minimum degree 2 (node 0, node 5).
* **Schema Integrity:** Preserved canonical JSON, 0 self-loops, 0 multigraph edges.

---

## 2. Exact Classical Reference Ground Truth

To establish an authoritative ground truth for quantum evaluation, an exact exhaustive combinatorial solver was executed across all $2^6 = 64$ computational states ([`results/data/classical_reference.json`](results/data/classical_reference.json)):
* **Exact Global Maximum Cut:** $C_{\max} = 6.0000$ (75.0% of total edge weight $W = 8.00$).
* **Classical Solution Runtime:** $< 0.5\text{ ms}$ on standard CPU ($0.000425\text{ s}$).
* **Optimal Subspace Degeneracy:** Exactly **10 bitstrings** achieve $C(x) = 6.0000$, forming 5 complementary pairs under bitwise spin inversion ($\mathbb{Z}_2$ symmetry):  
  `001100` / `110011`, `101100` / `010011`, `010010` / `101101`, `110010` / `001101`, `100110` / `011001`.
* **Primary Partition Assignment:** $S_1 = \{0, 1, 4, 5\}$ and $S_2 = \{2, 3\}$ (bitstring `001100`).

---

## 3. Five-Variable Reduction & Mathematical Justification

### Motivation & Physical Basis
The primary benchmark target (Processor A) provides 5 physical qubits. An unreduced 6-vertex formulation requires 6 physical qubits.

Because Max-Cut is strictly invariant under global bitwise spin inversion ($x \mapsto \mathbf{1} \oplus x$), fixing $x_0 = 0$ preserves the entire solution space while halving the computational Hilbert space from $2^6 = 64$ to $2^5 = 32$:
* The 5 remaining vertices $x_1, \dots, x_5$ map bijectively to 5 quantum variables $q_0, \dots, q_4$.
* Non-incident edges ($(u, v)$ with $u, v \ge 1$) remain standard two-body Ising terms: $x_u \oplus x_v = \frac{I - Z_u Z_v}{2}$.
* Incident edges ($(0, v)$ with $x_0 = 0$) simplify to linear longitudinal fields: $0 \oplus x_v = x_v = \frac{I - Z_v}{2}$.

Substituting into the minimization cost Hamiltonian ($H_C = -C(x)$):
$$H_C^{(5Q)} = \frac{1}{2} \sum_{(u, v) \in E, u, v \ge 1} Z_u Z_v + \frac{1}{2} Z_1 + \frac{1}{2} Z_2 - 4.0 \cdot I$$

The 10 global classical optima condense bijectively to exactly 5 unique 5-variable assignments, preserving $C_{\max} = 6.0000$ with $100\%$ mathematical equivalence.

---

## 4. Hardware Processor Architectures

All comparative evaluations target genuine physical topologies specified in [`processors/`](processors/):

```
+-----------------------------------------------------------------------------------------------------+
|                                   TARGET HARDWARE ARCHITECTURES                                     |
+-------------+----------------------+----------+---------+--------------------+---------+------------+
| Target      | Architecture Family  | Phys Q   | Act Q   | Physical Edges     | Max Deg | Spec Hash  |
+-------------+----------------------+----------+---------+--------------------+---------+------------+
| Processor A | 5Q Linear Chain CX   | 5        | 5       | 4 (8 CX pairs)     | 2       | aa9e30240a |
| Processor B | 9Q Sparse Tree CX    | 9        | 5       | 8 (16 CX pairs)    | 3       | 341d471380 |
| Processor D | 8Q Chorded Mesh CX   | 8        | 5       | 10 (20 CX pairs)   | 3       | a60ecf34eb |
+-------------+----------------------+----------+---------+--------------------+---------+------------+
```

### Processor D Design Rationale
Processor D was engineered to eliminate the **routing SWAP bottleneck** measured on Processors A and B:
- **Processor A (5Q Chain):** Requires 2 routing SWAPs (+6 CX gates, $+50\%$ 2Q overhead) and dilates depth to 58.
- **Processor B (9Q Tree):** Requires 1 routing SWAP (+3 CX gates, $+25\%$ 2Q overhead) and dilates depth to 52.
- **Processor D (8Q Chorded Mesh):** Embeds planar chords that directly match all 6 problem interactions, achieving **0 SWAPs, 12 CX gates, and depth 36** (a **$37.9\%$ depth reduction** vs A) while strictly respecting physical transmon degree $\le 3$.

---

## 5. Master Comparative Results

Evaluated with 4096 shots per case ($N = 24,576$ total shots), seed 42, native basis `["rz", "sx", "x", "cx"]`, and uniform synthetic noise ($p_{1Q}=0.001, p_{CX}=0.005, p_{RO}=0.01$):

| Experiment Case | Target Backend | Circuit Depth | 2Q Gates (CX) | Routing SWAPs | Mean Cut $\langle C \rangle$ | Standard Error | Approx Ratio $\alpha$ | Success Prob $P(\text{opt})$ | Relative Noise Degradation |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Processor A — Ideal** | `Processor_A` | 58 | 18 | 2 | 5.0557 | 0.0166 | 84.26% | 0.4270 (1749/4096) | Baseline |
| **Processor A — Noisy** | `Processor_A` | 58 | 18 | 2 | 4.8784 | 0.0187 | 81.31% | 0.3809 (1560/4096) | $-3.51\%$ ($\Delta = -0.1772$) |
| **Processor B — Ideal** | `Processor_B` | 52 | 15 | 1 | 5.0557 | 0.0166 | 84.26% | 0.4270 (1749/4096) | Baseline |
| **Processor B — Noisy** | `Processor_B` | 52 | 15 | 1 | 4.8923 | 0.0186 | 81.54% | 0.3845 (1575/4096) | $-3.23\%$ ($\Delta = -0.1633$) |
| **Processor D — Ideal** | `Processor_D` | 36 | 12 | 0 | 5.0557 | 0.0166 | 84.26% | 0.4270 (1749/4096) | Baseline |
| **Processor D — Noisy** | `Processor_D` | **36** | **12** | **0** | **4.9141** | **0.0183** | **81.90%** | **0.3887 (1592/4096)**| **$-2.80\%$ ($\Delta = -0.1416$)** |

---

## 6. Scientific Interpretation & Quantum Advantage Disclaimer

### Hardware Trade-Offs
1. **Depth vs Noise Resilience:** As circuit depth and CX counts drop from Processor A (58 depth, 18 CX) $\to$ Processor B (52 depth, 15 CX) $\to$ Processor D (36 depth, 12 CX), relative degradation under noise is reduced monotonically from $-3.51\% \to -3.23\% \to -2.80\%$.
2. **Fabrication Feasibility:** Processor D achieves zero SWAPs without unphysical all-to-all connectivity by keeping maximum physical vertex degree $\le 3$.

### Quantum Advantage Disclaimer
> [!IMPORTANT]
> **Definitive Quantum Advantage Disclaimer:**  
> This 6-vertex Max-Cut instance does **not** demonstrate quantum advantage over classical computation.  
> 
> The exact classical exhaustive solver evaluates all 64 partitions in **$0.425\,\text{ms}$**, certifying the global optimum with $100\%$ certainty. In contrast, QAOA on noisy quantum processors produces an approximation ratio of $81.9\%$ and requires substantial transpilation, routing, and error-mitigation overhead. This project demonstrates **architectural benchmarking and compilation optimization**, not quantum supremacy.

---

## 7. Historical Record Preservation

To maintain archival integrity, prior benchmark runs remain preserved in their respective directories:
- `results/verified_ab_v2/`: Historical version 2 runs (7-qubit ring Processor B, ECR basis, 1024 shots).
- `results/verified_ab_v3/`: Historical version 3 runs (9-qubit tree Processor B, ECR basis, asymmetric readout, 1024 shots).
- `results/verified_ab_v4/`: **Authoritative current benchmark** (CX basis, uniform synthetic noise, 4096 shots, custom Processor D).

---

## 8. Quickstart & Reproduction Commands

### Run Standalone Main Pipeline
```bash
python main.py
```

### Validate All Artifacts
```bash
python scripts/validate_artifacts.py
```

### Run Full Test Suite
```bash
python -m unittest discover -s tests -p "test_phase*.py"
```

---

## 9. Comprehensive Audit Deliverables

All phase audits and governance reports are documented in [`docs/audit/`](docs/audit/):
- [`PHASE_0_REQUIREMENT_FREEZE.md`](docs/audit/PHASE_0_REQUIREMENT_FREEZE.md): Source precedence and frozen requirements.
- [`PHASE_1_BASELINE_AUDIT.md`](docs/audit/PHASE_1_BASELINE_AUDIT.md): Initial code and architecture audit.
- [`PHASE_2_MATHEMATICAL_VALIDATION.md`](docs/audit/PHASE_2_MATHEMATICAL_VALIDATION.md): Problem instance and Ising/QUBO proof.
- [`PHASE_3_PROCESSOR_MIGRATION.md`](docs/audit/PHASE_3_PROCESSOR_MIGRATION.md): Processor A/B topology migration.
- [`PHASE_4_BENCHMARK_CONFIGURATION.md`](docs/audit/PHASE_4_BENCHMARK_CONFIGURATION.md): CX gate basis and synthetic noise calibration.
- [`PHASE_5_QAOA_VALIDATION.md`](docs/audit/PHASE_5_QAOA_VALIDATION.md): Shared variational parameter certification.
- [`PHASE_6_PRIMARY_EXPERIMENTS.md`](docs/audit/PHASE_6_PRIMARY_EXPERIMENTS.md): Primary A/B 4-case benchmark.
- [`PHASE_7_PROCESSOR_D.md`](docs/audit/PHASE_7_PROCESSOR_D.md): Custom Processor D design and evaluation.
- [`PHASE_8_ANALYSIS_VALIDATION.md`](docs/audit/PHASE_8_ANALYSIS_VALIDATION.md): Complete statistics, tables, and figures.
- [`FINAL_HACKATHON_READINESS_REPORT.md`](docs/audit/FINAL_HACKATHON_READINESS_REPORT.md): Final compliance verdict and submission checklist.
