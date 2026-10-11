# Qiskit Fall Fest 2026 — Five-Qubit Max-Cut Complement-Symmetry Reduction

**Document Version:** 1.0.0  
**Phase:** Phase 2 — Five-Qubit Symmetry Reduction  
**Date:** 2026-10-10  
**Track:** Quantum Optimization — O1 Max-Cut  
**Repository:** [https://github.com/karthikeyakolli/MAXCUT](https://github.com/karthikeyakolli/MAXCUT)  
**Status:** **MATHEMATICALLY FORMULATED & EXHAUSTIVELY TESTED (PASS)**

---

## 1. Executive Summary & Architectural Motivation

In the hackathon overview slide deck (`QFF_IBM_Hackathon_Guideline.pdf`, slide 4), **Processor A** is designated as a **5-qubit processor**. However, the official competition problem instance [`instances/challenge/o1_maxcut_instance.json`](file:///c:/Users/WIN_10/.gemini/antigravity/scratch/AXCUT/instances/challenge/o1_maxcut_instance.json) contains $|V| = 6$ vertices and $|E| = 8$ edges.

Under the naive 1-to-1 vertex-to-qubit compilation paradigm, a 6-vertex graph strictly requires 6 physical qubits. A 5-qubit processor cannot compile an unreduced 6-variable circuit without deleting vertices (which alters the problem and $C_{\max}$) or utilizing dynamic mid-circuit measurements with qubit reuse.

However, the **Maximum Cut (Max-Cut)** problem possesses an intrinsic exact $\mathbb{Z}_2$ global spin-flip symmetry (partition exchange invariance). By fixing the assignment of an arbitrary reference vertex (specifically $x_0 = 0$), the problem can be **isomorphically reduced from 6 binary variables to 5 quantum variables without removing any vertices, discarding any edges, or modifying the classical optimum $C_{\max} = 6.0000$**.

This document derives the exact mathematical reduction, proves state-by-state equivalence, and documents the exhaustive test results.

---

## 2. Mathematical Derivation of the Reduced Formulation

### 2.1 The Unreduced 6-Variable Objective
For an undirected graph $G = (V, E)$ with edge weights $w_{uv}$, the classical cut value is:
$$C(x) = \sum_{(u, v) \in E} w_{uv} (x_u \oplus x_v) = \sum_{(u, v) \in E} w_{uv} [x_u(1 - x_v) + x_v(1 - x_u)]$$
where $x \in \{0, 1\}^6$.

For any cut assignment $x = (x_0, x_1, \dots, x_5)$, its bitwise complement $\bar{x} = (1 - x_0, 1 - x_1, \dots, 1 - x_5)$ satisfies:
$$(1 - x_u) \oplus (1 - x_v) = x_u \oplus x_v \implies C(\bar{x}) = C(x)$$
Every cut partition $\{S, \bar{S}\}$ has exactly two bitstring representations ($x$ and $\bar{x}$). The 64 computational assignments of $\{0, 1\}^6$ partition into **exactly 32 complementary pairs**.

### 2.2 Fixing Reference Vertex $x_0 = 0$
Without loss of generality, fix $x_0 = 0$ (assigning vertex 0 to partition $S$). This selects the unique canonical representative for every complementary pair.

The remaining 5 vertices $V_{\text{red}} = \{1, 2, 3, 4, 5\}$ are represented by 5 binary decision variables $(x_1, x_2, x_3, x_4, x_5) \in \{0, 1\}^5$.

We partition the edges $E$ into two disjoint subsets:
1. **Edges incident to vertex 0:** $E_0 = \{(0, v) \in E\}$.
   Since $x_0 = 0$:
   $$w_{0v}(x_0 \oplus x_v) = w_{0v}(0 \oplus x_v) = w_{0v} x_v$$
   This transforms the quadratic interaction into a **purely linear term in $x_v$**.
2. **Edges not incident to vertex 0:** $E_{\setminus 0} = \{(u, v) \in E \mid u \ne 0, v \ne 0\}$.
   $$w_{uv}(x_u \oplus x_v) = w_{uv}[x_u + x_v - 2 x_u x_v]$$
   These remain quadratic interactions between variables $x_u$ and $x_v$.

The reduced cut function $C_{\text{red}}(x_1, \dots, x_5)$ across all 8 original edges is:
$$C_{\text{red}}(x_1, \dots, x_5) = \sum_{(0, v) \in E_0} w_{0v} x_v + \sum_{(u, v) \in E_{\setminus 0}} w_{uv} [x_u + x_v - 2 x_u x_v]$$

---

### 2.3 Reduced QUBO Minimization Objective
In our minimization convention $f_{\text{QUBO}}(x) = - C(x)$:
$$f_{\text{QUBO}}^{\text{red}}(x_1, \dots, x_5) = - \sum_{(0, v) \in E_0} w_{0v} x_v - \sum_{(u, v) \in E_{\setminus 0}} w_{uv} (x_u + x_v - 2 x_u x_v)$$

Using $x_v^2 = x_v$ for binary variables:
- **Diagonal linear penalties:** For each $v \in \{1, 2, 3, 4, 5\}$:
  $$Q_{vv} = - \sum_{u \in N(v)} w_{uv} = - \text{deg}_w(v)$$
- **Off-diagonal couplings:** For $(u, v) \in E_{\setminus 0}$:
  $$Q_{uv} = Q_{vu} = w_{uv}$$
For any reduced vector $x_{\text{red}} \in \{0, 1\}^5$:
$$x_{\text{red}}^T Q x_{\text{red}} = - C(0, x_1, x_2, x_3, x_4, x_5)$$

---

### 2.4 Reduced Classical Ising Hamiltonian
Mapping binary variables to classical spins $s_v = 1 - 2x_v \in \{+1, -1\}$ (where $x_v = 0 \iff s_v = +1$):
- Vertex 0 is fixed: $x_0 = 0 \iff s_0 = +1$.
- For incident edges $(0, v) \in E_0$:
  $$w_{0v} \frac{1 - s_0 s_v}{2} = w_{0v} \frac{1 - s_v}{2} = \frac{w_{0v}}{2} - \frac{w_{0v}}{2} s_v$$
  In $-C$, this induces a **longitudinal magnetic field**:
  $$h_v = + \frac{w_{0v}}{2}$$
- For non-incident edges $(u, v) \in E_{\setminus 0}$:
  $$w_{uv} \frac{1 - s_u s_v}{2} = \frac{w_{uv}}{2} - \frac{w_{uv}}{2} s_u s_v$$
  In $-C$, this induces quadratic coupling:
  $$J_{uv} = + \frac{w_{uv}}{2}$$
- Constant identity offset across all edges:
  $$\text{offset} = - \frac{1}{2} \sum_{e \in E} w_e = - \frac{W}{2} = -4.0$$

The reduced classical Ising Hamiltonian is:
$$E_{\text{Ising}}^{\text{red}}(s_1, \dots, s_5) = \sum_{(u, v) \in E_{\setminus 0}} \frac{w_{uv}}{2} s_u s_v + \sum_{(0, v) \in E_0} \frac{w_{0v}}{2} s_v - \frac{W}{2}$$

---

### 2.5 Reduced Quantum Cost Hamiltonian ($H_C^{\text{red}}$)
Promoting spins to Pauli operators $s_v \mapsto Z_v$ on 5 qubits ($q_0 \leftrightarrow v_1, q_1 \leftrightarrow v_2, q_2 \leftrightarrow v_3, q_3 \leftrightarrow v_4, q_4 \leftrightarrow v_5$):
$$H_C^{\text{red}} = \sum_{(u, v) \in E_{\setminus 0}} \frac{w_{uv}}{2} Z_u Z_v + \sum_{(0, v) \in E_0} \frac{w_{0v}}{2} Z_v - \frac{W}{2} I$$

The corresponding maximization cut operator is:
$$H_{\text{cut}}^{\text{red}} = - H_C^{\text{red}} = \frac{W}{2} I - \sum_{(u, v) \in E_{\setminus 0}} \frac{w_{uv}}{2} Z_u Z_v - \sum_{(0, v) \in E_0} \frac{w_{0v}}{2} Z_v$$

For any computational basis state $|x_1 x_2 x_3 x_4 x_5\rangle$:
$$\langle x_1 \dots x_5 | H_C^{\text{red}} | x_1 \dots x_5 \rangle = - C(0, x_1, x_2, x_3, x_4, x_5)$$
$$\langle x_1 \dots x_5 | H_{\text{cut}}^{\text{red}} | x_1 \dots x_5 \rangle = + C(0, x_1, x_2, x_3, x_4, x_5)$$

---

## 3. Five-Qubit QAOA Ansatz Architecture

Under the reduced formulation, the QAOA ansatz operates on **5 physical qubits**:

1. **Initial State:** $|+\rangle^{\otimes 5}$ via Hadamard on qubits 0 through 4.
2. **Cost Layer $U_C(\gamma)$:**
   - **Two-Qubit Gates:** For the 6 edges in $E_{\setminus 0} = \{(1,2), (1,3), (2,4), (3,4), (3,5), (4,5)\}$:
     $$\text{Apply } R_{ZZ}(\gamma \cdot w_{uv}) \text{ between qubit } u \text{ and qubit } v$$
   - **Single-Qubit $Z$-Rotations:** For the 2 edges in $E_0 = \{(0,1), (0,2)\}$:
     $$\text{Apply } R_Z(\gamma \cdot w_{0v}) \text{ on qubit } v$$
3. **Mixer Layer $U_M(\beta)$:**
   - For all 5 qubits: apply $R_X(2\beta)$.

### Resource Comparison: 6-Qubit Unreduced vs. 5-Qubit Reduced Logical Circuit
| Logical Resource | Unreduced 6-Qubit QAOA ($p=1$) | Reduced 5-Qubit QAOA ($p=1$) | Net Reduction |
| :--- | :---: | :---: | :---: |
| **Qubit Count** | 6 qubits | **5 qubits** | $-1$ qubit (Embeds on 5Q device) |
| **Two-Qubit Gates ($R_{ZZ}$)** | 8 gates | **6 gates** | $-2$ two-qubit interactions |
| **Single-Qubit $Z$ Rotations** | 0 gates | **2 gates** ($R_Z$ on nodes 1 and 2) | $+2$ virtual single-qubit rotations |
| **Mixer Gates ($R_X$)** | 6 gates | **5 gates** | $-1$ gate |
| **Total Logical Gates** | 20 gates | **18 gates** | $-2$ total gates |

---

## 4. Exhaustive Test Suite & Verification Results

All 7 test requirements specified in the Phase 2 prompt were implemented in [`tests/test_reduced_formulation.py`](file:///c:/Users/WIN_10/.gemini/antigravity/scratch/AXCUT/tests/test_reduced_formulation.py) and executed via `pytest`:

```text
tests/test_reduced_formulation.py::TestReducedFormulationExhaustive::test_01_evaluate_all_64_assignments PASSED
tests/test_reduced_formulation.py::TestReducedFormulationExhaustive::test_02_canonicalize_each_assignment_against_complement PASSED
tests/test_reduced_formulation.py::TestReducedFormulationExhaustive::test_03_verify_cut_value_is_unchanged PASSED
tests/test_reduced_formulation.py::TestReducedFormulationExhaustive::test_04_verify_32_reduced_assignments_cover_partition_classes PASSED
tests/test_reduced_formulation.py::TestReducedFormulationExhaustive::test_05_confirm_optimum_remains_6 PASSED
tests/test_reduced_formulation.py::TestReducedFormulationExhaustive::test_06_verify_10_optimal_bitstrings_form_5_complementary_pairs PASSED
tests/test_reduced_formulation.py::TestReducedFormulationExhaustive::test_07_qubo_ising_qaoa_objective_and_decoding_consistency PASSED

============================== 7 passed in 9.11s ==============================
```

### 4.1 Test Verification Summary
1. **Exhaustive 64-Assignment Evaluation:** All $2^6 = 64$ binary states evaluated; maximum cut is strictly $6.0$, minimum is $0.0$.
2. **Canonicalization Invariance:** For every state $x$, $\text{canonicalize}(x) = \text{canonicalize}(\bar{x})$, and the canonical bitstring always satisfies $x_0 = 0$.
3. **Cut Value Equality:** $C(x) = C(\bar{x}) = C(\text{canonicalize}(x))$ with zero difference across all 64 states.
4. **Partition Coverage:** The 32 reduced 5-bit assignments $\{x_1 \dots x_5\} \in \{0, 1\}^5$ uniquely cover all 32 partition classes of the 6-vertex graph.
5. **Optimum Invariance:** Under the reduced formulation, $\max C_{\text{red}} = 6.0000$, $\min f_{\text{QUBO}}^{\text{red}} = -6.0000$, $\min E_{\text{Ising}}^{\text{red}} = -6.0000$, and $\min \langle H_C^{\text{red}} \rangle = -6.0000$.
6. **Optimal Subspace Degeneracy:** The 10 optimal bitstrings of the official instance form exactly 5 complementary pairs. In the 5-qubit reduced space, exactly 5 optimal states exist:
   - `01100` $\to$ expanded `001100` (pair with `110011`)
   - `10010` $\to$ expanded `010010` (pair with `101101`)
   - `11001` $\to$ expanded `011001` (pair with `100110`)
   - `01101` $\to$ expanded `001101` (pair with `110010`)
   - `10011` $\to$ expanded `010011` (pair with `101100`)
   Each achieves $C = 6.0000$.
7. **Representation Consistency & Decoding:** Numerical difference $|C - (-f_{\text{QUBO}})| < 10^{-9}$, $|C - (-E_{\text{Ising}})| < 10^{-9}$, $|C - (-\langle H_C \rangle)| < 10^{-9}$ verified across all 32 assignments. Decoded counts map seamlessly back to canonical 6-vertex bitstrings.

---

## 5. Architectural Conflict & Official Requirement Traceability

### 5.1 Status of the Official Benchmark Target
- **Preservation of Existing 6-Qubit Benchmark Data:** In strict compliance with the benchmark protocol ("Do not reuse old six-qubit QAOA parameters or measurement data as new reduced-circuit results"), all existing 6-qubit benchmark results, angles ($\gamma^* = 2.4835, \beta^* = 4.2540$), circuit files, and 4-case tables for 7Q Falcon-H and 7Q Ring-7 remain **100% PRESERVED AND UNCHANGED**.
- **Conflict Documentation:**
  - If the organizers confirm that **Processor A is officially a 5-qubit device**, then this 5-qubit symmetry reduction provides the certified, mathematically lossless bridge to execute the 6-vertex challenge instance without vertex contraction.
  - If the organizers confirm that **Processor A is the 7-qubit Falcon-H** defined in the repository, the unreduced 6-qubit formulation remains the authoritative track evaluation.
- **Traceability:**
  - `src/maxcut/formulation/qubo.py`: Implements both unreduced and reduced formulations with zero interference.
  - `src/maxcut/qaoa/ansatz.py`: Exposes `build_reduced_qaoa_circuit`.
  - `src/maxcut/qaoa/decoding.py`: Exposes `decode_reduced_qiskit_counts`.
  - `tests/test_reduced_formulation.py`: 7 automated exhaustive regression tests.

---

## 6. Stop Directive

All mathematical derivations, formulation functions, decoding mappings, and exhaustive equivalence tests have been implemented and verified. The codebase is frozen pending organizer instruction.
