# Qiskit Fall Fest 2026 — Official Processor A/B Integration (5-Qubit Reduced QAOA)

**Document Version:** 1.0.0  
**Phase:** Phase 3 — Official Processor A/B Integration  
**Date:** 2026-10-10  
**Evaluator:** Quantum-Computing Benchmark & Compilation Engineer  
**Track:** Quantum Optimization — O1 Max-Cut  
**Repository:** [https://github.com/karthikeyakolli/MAXCUT](https://github.com/karthikeyakolli/MAXCUT)  
**Status:** **INTEGRATED, COMPILED, VERIFIED & REGRESSION TESTED (PASS)**

---

## 1. Executive Summary

This document establishes the official compilation integration of the 5-qubit symmetry-reduced QAOA formulation (from Phase 2) targeting the verified hardware definitions for **Processor A** (Falcon-H, native `ecr`) and **Processor B** (Ring-7, native `cz`).

### Key Highlights:
1. **Mathematical Invariance Preserved:** The official 6-vertex, 8-edge unweighted challenge graph ($W = 8.00$, exact classical optimum $C_{\max} = 6.0000$) is solved using exact $\mathbb{Z}_2$ complement symmetry fixing $x_0 = 0$. No vertices were deleted, no edges were removed, and no processor specifications were invented.
2. **Qubit Allocation:**
   - **Processor A:** Compiles onto **exactly 5 physical qubits** (`[0, 1, 2, 3, 5]`), utilizing a connected 5-qubit tree subgraph of Falcon-H while leaving ancilla qubits `[4, 6]` idle.
   - **Processor B:** Compiles onto a **valid 5-qubit subset** (`[0, 3, 4, 5, 6]`), forming a connected path `3-4-5-6-0` on Ring-7 while leaving ancilla qubits `[1, 2]` idle.
3. **100% Architecture Compliance:**
   - **Connectivity:** 0 coupling map violations on both targets (every two-qubit gate is mapped to a valid directed physical link).
   - **Native Gate Set:** 0 unsupported gates (Processor A uses strictly `["rz", "sx", "x", "ecr"]`; Processor B uses strictly `["rz", "sx", "x", "cz"]`).
4. **Older Results Preserved:** All existing 6-qubit experimental records, tables, figures, and circuit files remain untouched in their canonical locations. New 5-qubit artifacts are saved to distinct dedicated files prefixed with `reduced_5q_`.
5. **Regression Suite:** 8 new regression tests in `tests/test_reduced_processor_integration.py` pass cleanly (95 tests total across the repository).

---

## 2. Hardware Processor Configurations

| Parameter | Processor A (`Falcon-H`) | Processor B (`Ring-7`) |
| :--- | :--- | :--- |
| **Identifier** | `Processor_A` | `Processor_B` |
| **Physical Qubit Count** | 7 physical qubits | 7 physical qubits |
| **Native 2Q Entangler** | `ecr` (Echoed Cross-Resonance) | `cz` (Controlled-Z) |
| **Native 1Q Basis Gates** | `["rz", "sx", "x"]` | `["rz", "sx", "x"]` |
| **Topology** | Falcon-H heavy-hex tree subgraph | Simple cycle $C_7$ |
| **Coupling Edges** | 12 directed edges (6 bidirectional pairs) | 14 directed edges (7 bidirectional pairs) |
| **Coupling Map** | `[[0,1],[1,0],[1,2],[2,1],[1,3],[3,1],[3,5],[5,3],[4,5],[5,4],[5,6],[6,5]]` | `[[0,1],[1,0],[1,2],[2,1],[2,3],[3,2],[3,4],[4,3],[4,5],[5,4],[5,6],[6,5],[6,0],[0,6]]` |
| **Compilation API** | Qiskit 2.x `generate_preset_pass_manager` | Qiskit 2.x `generate_preset_pass_manager` |
| **Compiler Seed** | `seed_transpiler = 42` | `seed_transpiler = 42` |

---

## 3. Logical Circuit vs. Transpiled Circuit Metrics

### 3.1 Logical 5-Qubit Reduced QAOA ($p=1$)
- **Active Qubits:** 5 ($q_0 \dots q_4$, representing vertices $1 \dots 5$)
- **Fixed Node:** $x_0 = 0$
- **Total Gates:** 18 gates (excluding measurement and barrier):
  - 6 two-qubit $R_{ZZ}$ interactions for non-incident edges $\{(1,2), (1,3), (2,4), (3,4), (3,5), (4,5)\}$
  - 2 single-qubit $R_Z$ rotations for incident edges $\{(0,1), (0,2)\}$
  - 5 single-qubit $R_X$ mixer rotations
  - 5 Hadamard initializations
- **Logical Circuit Depth:** 9 cycles

### 3.2 Compilation Metrics Across Optimization Levels

| Target | Architecture | Opt Level | Native 2Q Gate | Active Physical Qubits | Physical Qubits Used | Basis Synthesis 2Q | Routing SWAPs | Routing 2Q Overhead | Total Native 2Q Gates | Circuit Depth | Total Gates | Connectivity Compliant | Basis Compliant |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Processor A** | Falcon-H | **1** | `ecr` | **5** | `[0, 1, 2, 3, 5]` | 12 | 2 | 6 | **18** | **66** | **121** | **True** (0 violations) | **True** |
| Processor A | Falcon-H | 2 | `ecr` | 5 | `[1, 3, 4, 5, 6]` | 12 | 2 | 6 | 18 | 76 | 131 | True (0 violations) | True |
| Processor A | Falcon-H | 3 | `ecr` | 5 | `[1, 3, 4, 5, 6]` | 12 | 2 | 6 | 18 | 76 | 131 | True (0 violations) | True |
| **Processor B** | Ring-7 | **1** | `cz` | **5** | `[0, 3, 4, 5, 6]` | 12 | 3 | 9 | **21** | **81** | **122** | **True** (0 violations) | **True** |
| Processor B | Ring-7 | 2 | `cz` | 5 | `[0, 3, 4, 5, 6]` | 8 | 3 | 9 | 17 | 58 | 111 | True (0 violations) | True |
| Processor B | Ring-7 | 3 | `cz` | 5 | `[0, 3, 4, 5, 6]` | 8 | 3 | 9 | 17 | 58 | 111 | True (0 violations) | True |

---

## 4. Layout Mappings & Physical Qubit Allocation

### 4.1 Processor A (Falcon-H Baseline Level 1)
- **Active Physical Qubits:** `[0, 1, 2, 3, 5]`
- **Idle Ancilla Qubits:** `[4, 6]`
- **Virtual-to-Physical Initial Layout:**
  - $q_0 \mapsto \text{phys\_0}$
  - $q_1 \mapsto \text{phys\_1}$
  - $q_2 \mapsto \text{phys\_2}$
  - $q_3 \mapsto \text{phys\_3}$
  - $q_4 \mapsto \text{phys\_5}$
- **Final Permutation (after 2 SWAPs):** `[0, 2, 1, 5, 3]`
- **Gate Breakdown:**
  - `rz`: 59
  - `sx`: 30
  - `ecr`: 18
  - `x`: 8
  - `measure`: 5
  - `barrier`: 1
  - **Total Instructions:** 121

### 4.2 Processor B (Ring-7 Baseline Level 1)
- **Active Physical Qubits:** `[0, 3, 4, 5, 6]` (Connected 5-path `3-4-5-6-0`)
- **Idle Ancilla Qubits:** `[1, 2]`
- **Virtual-to-Physical Initial Layout:**
  - $q_0 \mapsto \text{phys\_5}$
  - $q_1 \mapsto \text{phys\_4}$
  - $q_2 \mapsto \text{phys\_6}$
  - $q_3 \mapsto \text{phys\_3}$
  - $q_4 \mapsto \text{phys\_0}$
- **Final Permutation (after 3 SWAPs):** `[4, 3, 0, 5, 6]`
- **Gate Breakdown:**
  - `rz`: 51
  - `sx`: 44
  - `cz`: 21
  - `measure`: 5
  - `barrier`: 1
  - **Total Instructions:** 122

---

## 5. Mathematical Decomposition of Native Two-Qubit Gates

In accordance with strict quantum compilation accounting:
$$\text{Total Native 2Q Gates} = \text{Basis Synthesis 2Q Gates} + \text{Routing 2Q Gates}$$

1. **Basis Synthesis:**
   - Every logical $R_{ZZ}(\theta)$ gate requires 2 native entanglers (`ecr` on A, `cz` on B):
     $$6 \text{ logical } R_{ZZ} \times 2 = 12 \text{ basis synthesis 2Q gates}$$
2. **Routing Overhead:**
   - On Processor A: 2 SWAP operations inserted. Each SWAP synthesizes into 3 ECR gates:
     $$2 \text{ SWAP} \times 3 \text{ ECR/SWAP} = 6 \text{ routing 2Q gates}$$
     $$\text{Total ECR} = 12 + 6 = 18$$
   - On Processor B: 3 SWAP operations inserted. Each SWAP synthesizes into 3 CZ gates:
     $$3 \text{ SWAP} \times 3 \text{ CZ/SWAP} = 9 \text{ routing 2Q gates}$$
     $$\text{Total CZ} = 12 + 9 = 21$$

Arithmetic consistency holds exactly with zero discrepancies.

---

## 6. Generated Circuit Artifacts

All circuits and serialized metric tables are exported and committed:

1. **Logical Circuit:**
   - [`results/circuits/reduced_5q_logical_qaoa_p1.qasm`](file:///c:/Users/WIN_10/.gemini/antigravity/scratch/AXCUT/results/circuits/reduced_5q_logical_qaoa_p1.qasm)
   - [`results/circuits/reduced_5q_logical_qaoa_p1.txt`](file:///c:/Users/WIN_10/.gemini/antigravity/scratch/AXCUT/results/circuits/reduced_5q_logical_qaoa_p1.txt)
2. **Processor A Transpiled Circuits:**
   - [`results/circuits/reduced_5q_processor_a_opt1_transpiled.qasm`](file:///c:/Users/WIN_10/.gemini/antigravity/scratch/AXCUT/results/circuits/reduced_5q_processor_a_opt1_transpiled.qasm)
   - [`results/circuits/reduced_5q_processor_a_opt1_transpiled.txt`](file:///c:/Users/WIN_10/.gemini/antigravity/scratch/AXCUT/results/circuits/reduced_5q_processor_a_opt1_transpiled.txt)
   - Canonical alias: [`results/circuits/reduced_5q_processor_a_transpiled.qasm`](file:///c:/Users/WIN_10/.gemini/antigravity/scratch/AXCUT/results/circuits/reduced_5q_processor_a_transpiled.qasm)
3. **Processor B Transpiled Circuits:**
   - [`results/circuits/reduced_5q_processor_b_opt1_transpiled.qasm`](file:///c:/Users/WIN_10/.gemini/antigravity/scratch/AXCUT/results/circuits/reduced_5q_processor_b_opt1_transpiled.qasm)
   - [`results/circuits/reduced_5q_processor_b_opt1_transpiled.txt`](file:///c:/Users/WIN_10/.gemini/antigravity/scratch/AXCUT/results/circuits/reduced_5q_processor_b_opt1_transpiled.txt)
   - Canonical alias: [`results/circuits/reduced_5q_processor_b_transpiled.qasm`](file:///c:/Users/WIN_10/.gemini/antigravity/scratch/AXCUT/results/circuits/reduced_5q_processor_b_transpiled.qasm)
4. **Machine-Readable Metrics & Tables:**
   - [`results/data/reduced_5q_processor_a_circuit_metrics.json`](file:///c:/Users/WIN_10/.gemini/antigravity/scratch/AXCUT/results/data/reduced_5q_processor_a_circuit_metrics.json)
   - [`results/data/reduced_5q_processor_b_circuit_metrics.json`](file:///c:/Users/WIN_10/.gemini/antigravity/scratch/AXCUT/results/data/reduced_5q_processor_b_circuit_metrics.json)
   - [`results/tables/reduced_5q_compilation_breakdown.md`](file:///c:/Users/WIN_10/.gemini/antigravity/scratch/AXCUT/results/tables/reduced_5q_compilation_breakdown.md)
   - [`results/tables/reduced_5q_compilation_breakdown.csv`](file:///c:/Users/WIN_10/.gemini/antigravity/scratch/AXCUT/results/tables/reduced_5q_compilation_breakdown.csv)

---

## 7. Regression Test Evidence

All 8 automated regression tests in [`tests/test_reduced_processor_integration.py`](file:///c:/Users/WIN_10/.gemini/antigravity/scratch/AXCUT/tests/test_reduced_processor_integration.py) passed:

```text
tests/test_reduced_processor_integration.py::TestReducedProcessorIntegration::test_01_target_configurations_match_verified_source PASSED
tests/test_reduced_processor_integration.py::TestReducedProcessorIntegration::test_02_logical_circuit_architecture_and_objective_invariance PASSED
tests/test_reduced_processor_integration.py::TestReducedProcessorIntegration::test_03_compilation_success_both_processors PASSED
tests/test_reduced_processor_integration.py::TestReducedProcessorIntegration::test_04_connectivity_compliance_zero_violations PASSED
tests/test_reduced_processor_integration.py::TestReducedProcessorIntegration::test_05_native_basis_compliance_zero_violations PASSED
tests/test_reduced_processor_integration.py::TestReducedProcessorIntegration::test_06_physical_qubit_mapping_and_subsets PASSED
tests/test_reduced_processor_integration.py::TestReducedProcessorIntegration::test_07_metrics_derived_from_artifacts_and_decomposition PASSED
tests/test_reduced_processor_integration.py::TestReducedProcessorIntegration::test_08_exported_artifacts_and_schema_integrity PASSED

============================= 8 passed in 11.10s ==============================
```

Full regression suite:
```text
95 passed, 10 subtests passed in 32.62s
```
Artifact validator:
```text
[SUCCESS] All required configuration, result, table, figure, and notebook artifacts are verified!
```
