# Qiskit Fall Fest 2026 — Claim vs. Evidence Matrix

**Document Version:** 1.0.0  
**Audit Date:** 2026-10-09  
**Track:** Quantum Optimization — O1 Max-Cut  
**Auditor Role:** Senior Quantum-Computing Engineer & Hackathon Evaluator  
**Status:** COMPLETE (Read-Only Phase 0 Audit)  

---

## 1. Overview & Classification Schema

This matrix contains a line-by-line audit of every mathematical, experimental, architectural, and reporting claim made in the MAXCUT codebase, documentation, and result artifacts.

### Classification Categories:
1. **PASS**: Claim is verified by concrete mathematical derivations and reproducible experimental data.
2. **CONFIRMED DEFECT**: Claim is mathematically or empirically false, contradicted by code logic or data.
3. **MISSING REQUIREMENT**: Required element specified in guidelines that is absent from the repository.
4. **UNVERIFIED**: Claim cannot be validated due to lack of evidence or unrunnable dependencies.

### Severity Levels:
- **P0**: Critical correctness or mandatory competition compliance defect.
- **P1**: Material experimental, reporting, or dependency gap.
- **P2**: Presentation, naming, or low-risk enhancement.
- **NO ACTION**: Verified passing item.

---

## 2. Itemized Findings Matrix

### Finding AUD-01: Classical Ground Truth Optimum
- **ID:** AUD-01
- **Requirement or Claim:** Problem graph $|V|=6, |E|=8$ has exact maximum cut $C_{\max} = 6.0000$ with 10 degenerate optimal partitions.
- **Source File/Section:** [`PROJECT_SPEC.md`](file:///c:/Users/WIN_10/.gemini/antigravity/scratch/AXCUT/PROJECT_SPEC.md) Sec. 1; [`README.md`](file:///c:/Users/WIN_10/.gemini/antigravity/scratch/AXCUT/README.md) Sec. 3; [`report/analysis.md`](file:///c:/Users/WIN_10/.gemini/antigravity/scratch/AXCUT/report/analysis.md) Sec. 1.
- **Available Evidence:**
  - Evaluated exhaustive search over all $2^6 = 64$ configurations using [`src/maxcut/classical/solver.py`](file:///c:/Users/WIN_10/.gemini/antigravity/scratch/AXCUT/src/maxcut/classical/solver.py).
  - Minimum cut is $0.0$, maximum cut is strictly $6.0000$.
  - Exact 10 optimal bitstrings confirmed: `001100`, `101100`, `010010`, `110010`, `100110`, `011001`, `001101`, `101101`, `010011`, `110011` (5 complementary pairs).
- **Classification:** **PASS**
- **Severity:** NO ACTION
- **Proposed Correction:** None required.
- **Required Regression Test:** `tests/test_classical.py::TestClassicalReferenceSolver::test_result_serialization_and_validation`
- **Acceptance Criterion:** $C_{\max} = 6.0000$ across all 64 assignments.

---

### Finding AUD-02: State-by-State Hamiltonian & QUBO Equivalence
- **ID:** AUD-02
- **Requirement or Claim:** Exact energy equivalence between classical cut $C(x)$, QUBO objective $f(x)$, classical Ising energy $E_{\text{Ising}}(s)$, and quantum Cost Hamiltonian expectation $\langle x | H_C | x \rangle$:
  $$C(x) = - f_{\text{QUBO}}(x) = - E_{\text{Ising}}(s) = - \langle x | H_C | x \rangle$$
- **Source File/Section:** [`src/maxcut/formulation/qubo.py`](file:///c:/Users/WIN_10/.gemini/antigravity/scratch/AXCUT/src/maxcut/formulation/qubo.py) Lines 1-8; [`docs/validation_report.md`](file:///c:/Users/WIN_10/.gemini/antigravity/scratch/AXCUT/docs/validation_report.md) Sec. 3.
- **Available Evidence:**
  - Full Hilbert space verification across 16 states on diamond graph and 64 states on official challenge instance shows 0 mismatches.
  - Cost Hamiltonian $H_C = \frac{1}{2} \sum_{(u,v)\in E} Z_u Z_v - 4.0 I$ has ground state energy $E_0 = -6.0000$.
- **Classification:** **PASS**
- **Severity:** NO ACTION
- **Proposed Correction:** None required.
- **Required Regression Test:** `tests/test_formulation.py::TestMathematicalFormulation::test_ground_state_energy_matches_classical_optimum`
- **Acceptance Criterion:** Energy difference $< 10^{-9}$ across all $2^n$ basis states.

---

### Finding AUD-03: Routing SWAP Count Underreporting Bug
- **ID:** AUD-03
- **Requirement or Claim:** "For both Processor A and Processor B, the transpiler reported 0 SWAP gates (`swap_count = 0`) across Optimization Levels 1, 2, and 3... Neither processor required dynamic SWAP insertions (`swap_count = 0`) because the 6-vertex challenge graph could be embedded directly into a connected 6-node subgraph of both Falcon-H and Ring-7."
- **Source File/Section:** [`report/analysis.md`](file:///c:/Users/WIN_10/.gemini/antigravity/scratch/AXCUT/report/analysis.md) Sec. 2 (Table 1) and Sec. 4 (Question 3); [`README.md`](file:///c:/Users/WIN_10/.gemini/antigravity/scratch/AXCUT/README.md) Sec. 5; [`src/maxcut/metrics/circuit_metrics.py`](file:///c:/Users/WIN_10/.gemini/antigravity/scratch/AXCUT/src/maxcut/metrics/circuit_metrics.py) Line 105; [`processors/processor_a/adapter.py`](file:///c:/Users/WIN_10/.gemini/antigravity/scratch/AXCUT/processors/processor_a/adapter.py) Line 150.
- **Available Evidence:**
  1. **Graph Topological Impossibility:** The challenge graph has 6 nodes, 8 edges, and contains two triangles (`(0,1,2)` and `(3,4,5)`) and cycle `(1,2,4,3)`. Processor A is a tree (6 edges, 0 cycles, 0 triangles). Processor B is a simple 7-cycle (no triangles). It is mathematically impossible to embed a graph containing triangles into a tree or a 7-cycle as an induced subgraph with zero routing SWAPs.
  2. **Transpiler Inspection:** The code computed SWAP count via `transpiled_circuit.count_ops().get("swap", 0)`. However, the preset pass manager synthesizes all gates to the native basis (`ecr` for Processor A, `cz` for Processor B). Because `swap` is not in `basis_gates`, all SWAPs are decomposed into native basis gates and therefore never appear in `transpiled_circuit.count_ops()`.
  3. **Direct Compilation with SWAP Retained:** Executing the Qiskit pass manager with `swap` in the basis gate set proves that **exactly 4 SWAP gates** were inserted for Processor A and **exactly 4 SWAP gates** were inserted for Processor B:
     - Processor A: `{'ecr': 16, 'swap': 4, ...}`
     - Processor B: `{'cz': 16, 'swap': 4, ...}`
  4. **Two-Qubit Gate Decomposition:**
     - 8 logical $R_{ZZ}$ gates $\times 2$ basis 2Q gates = 16 basis 2Q gates.
     - 4 SWAP gates $\times 3$ basis 2Q gates = 12 basis 2Q gates.
     - Total: $16 + 12 = 28$ basis 2Q gates (`ecr` / `cz`).
     The expansion from 8 to 28 two-qubit gates is **43% routing overhead** (12 gates) and **57% basis synthesis overhead** (16 gates), NOT 0% routing overhead!
- **Classification:** **CONFIRMED DEFECT**
- **Severity:** **P0**
- **Proposed Correction:**
  1. Fix SWAP counting in `src/maxcut/metrics/circuit_metrics.py`, `processors/processor_a/adapter.py`, and `processors/processor_b/adapter.py` by:
     - Extracting SWAPs directly from the routing pass (`N layout changes` or transpiling with a pre-decomposition inspection step).
     - Or deducing `swap_count = (trans_2q - 2 * log_2q) // 3`.
  2. Correct `results/data/processor_a_circuit_metrics.json`, `processor_b_circuit_metrics.json`, `results/tables/processor_comparison_table.csv`, and `report/analysis.md` to accurately report `SWAP Count = 4`.
  3. Rewrite Question 3 and Table 1 in `report/analysis.md` and `README.md` to remove the false claim of "isomorphic subgraph embedding with zero SWAPs".
- **Required Regression Test:** Add test `test_routing_swap_detection` to `tests/test_circuit_metrics.py` asserting `swap_count == 4` on the challenge graph for both processors.
- **Acceptance Criterion:** Reported SWAP count equals 4; total 2Q gate inventory reconciles exactly ($16 + 12 = 28$).

---

### Finding AUD-04: Conflation of Basis Synthesis with Routing Overhead
- **ID:** AUD-04
- **Requirement or Claim:** `routing_overhead_ratio` defined as `trans_2q / log_2q` ($28 / 8 = 3.50\times$).
- **Source File/Section:** [`src/maxcut/metrics/circuit_metrics.py`](file:///c:/Users/WIN_10/.gemini/antigravity/scratch/AXCUT/src/maxcut/metrics/circuit_metrics.py) Line 109; [`report/analysis.md`](file:///c:/Users/WIN_10/.gemini/antigravity/scratch/AXCUT/report/analysis.md) Table 1.
- **Available Evidence:**
  - `routing_overhead_ratio` divides total transpiled 2Q gates (28) by logical 2Q gates (8).
  - Even with 0 SWAPs, synthesizing $R_{ZZ}$ from native `ecr` or `cz` requires 2 entangling gates per edge ($8 \times 2 = 16$), which is a $2.00\times$ basis synthesis ratio.
  - The actual routing overhead is the additional 12 gates inserted by 4 SWAPs ($12 / 16 = 75\%$ increase above native unrouted cost, or $12 / 28 = 42.8\%$ of total 2Q gates).
- **Classification:** **CONFIRMED DEFECT**
- **Severity:** **P0**
- **Proposed Correction:** Disentangle basis synthesis ratio ($16 / 8 = 2.0\times$) from routing overhead ratio ($(28 - 16) / 16 = 0.75\times$ or $4 \text{ SWAPs}$).
- **Required Regression Test:** `tests/test_circuit_metrics.py::TestCircuitMetricsAnalysis::test_circuit_resource_metrics_extraction` verifying isolated basis vs. routing components.
- **Acceptance Criterion:** Metrics clearly report both `basis_synthesis_ratio` (2.0x) and `routing_expansion_ratio` (1.75x).

---

### Finding AUD-05: Hardware Execution vs. Ideal Emulation
- **ID:** AUD-05
- **Requirement or Claim:** "All metrics below are derived from actual compiled circuits and executions... In our controlled, noise-free local emulation... execution was conducted on an ideal shot-sampling engine without physical gate infidelity, leakage, or decoherence."
- **Source File/Section:** [`README.md`](file:///c:/Users/WIN_10/.gemini/antigravity/scratch/AXCUT/README.md) Sec. 5; [`report/analysis.md`](file:///c:/Users/WIN_10/.gemini/antigravity/scratch/AXCUT/report/analysis.md) Sec. 1, 4.
- **Available Evidence:**
  - `processors/processor_a/adapter.py` and `processors/processor_b/adapter.py` instantiate `self._simulator = AerSimulator(seed_simulator=seed_simulator)` without any noise model.
  - `qubit_properties` in `data/hardware_specs/processor_a.json` ($T_1=210\mu s, T_2=140\mu s, \epsilon_{2Q}=0.0075$) and `processor_b.json` ($T_1=240\mu s, T_2=160\mu s, \epsilon_{2Q}=0.0050$) are saved in metadata but never converted to Qiskit `NoiseModel` objects.
  - The results are pure unitary shot sampling on transpiled circuits.
- **Classification:** **PASS** (Correctly disclosed as ideal emulation in text, but missing noisy simulation if organizer required noise).
- **Severity:** **P1**
- **Proposed Correction:** Maintain clear distinction in all documentation that executions are ideal architectural emulations (topological and gate synthesis only). If noisy simulation is requested, implement an optional `AerSimulator(noise_model=...)` built from `qubit_properties`.
- **Required Regression Test:** `tests/test_processor_experiments.py` ensuring execution mode metadata explicitly specifies `aer_hardware_topology_emulation`.
- **Acceptance Criterion:** All tables and charts explicitly annotate targets as "Noisy-Free Emulation (Hardware Topology & Basis)".

---

### Finding AUD-06: Empirical vs. Analytic Expectation Value Verification
- **ID:** AUD-06
- **Requirement or Claim:** Reported expected cut values $\langle C \rangle = 4.8931$ (Sim), $4.8901$ (Proc A), $4.9116$ (Proc B) and approximation ratios $\alpha \approx 81.50\%\text{--}81.86\%$.
- **Source File/Section:** [`report/analysis.md`](file:///c:/Users/WIN_10/.gemini/antigravity/scratch/AXCUT/report/analysis.md) Table 1; [`results/tables/processor_comparison_table.csv`](file:///c:/Users/WIN_10/.gemini/antigravity/scratch/AXCUT/results/tables/processor_comparison_table.csv).
- **Available Evidence:**
  - Recomputation from decoded measurement counts (`decoded_counts`) in result JSONs yields identical values:
    - Simulator: $\sum p(x) C(x) = 4.8930664$, $\alpha = 0.815511$, $P(\text{opt}) = 0.380371$
    - Processor A: $\sum p(x) C(x) = 4.8901367$, $\alpha = 0.815023$, $P(\text{opt}) = 0.393066$
    - Processor B: $\sum p(x) C(x) = 4.9116211$, $\alpha = 0.818604$, $P(\text{opt}) = 0.407227$
  - The optimizer objective in `QAOAOptimizer` computes the exact analytic statevector expectation $\langle \psi | H_C | \psi \rangle = -4.867127$ (analytic $\langle C \rangle = 4.8671$).
  - The reported numbers are finite-shot empirical estimates over $N = 2048$ shots.
  - The $+1.41\%$ difference in $P(\text{opt})$ between A and B is within multinomial sampling standard error ($1/\sqrt{2048} \approx 2.21\%$).
- **Classification:** **PASS**
- **Severity:** NO ACTION
- **Proposed Correction:** None required.
- **Required Regression Test:** `tests/test_processor_experiments.py::TestProcessorExperiments::test_processor_a_result_validity`
- **Acceptance Criterion:** Recomputed sample expectation values match stored results with 0.0 error.

---

### Finding AUD-07: Bell-Correlation / Error-Detection Material Applicability
- **ID:** AUD-07
- **Requirement or Claim:** Determine whether Bell-correlation and error-detection material from the general Qiskit Fall Fest participant guide is mandatory for the O1 Max-Cut deliverable.
- **Source File/Section:** Participant Guide vs. [`CHALLENGE_KIT.md`](file:///c:/Users/WIN_10/.gemini/antigravity/scratch/AXCUT/CHALLENGE_KIT.md) Sec. 3; [`PROJECT_SPEC.md`](file:///c:/Users/WIN_10/.gemini/antigravity/scratch/AXCUT/PROJECT_SPEC.md) Sec. 2.
- **Available Evidence:**
  - Review of `CHALLENGE_KIT.md` and `PROJECT_SPEC.md` shows the O1 track is strictly defined as "Quantum Optimization — O1 Max-Cut".
  - The required evaluation criteria are: Graph order/size, Classical ground truth, QAOA angles and $\alpha$, Hardware transpilation depth, 2Q gates, SWAPs, and processor trade-off analysis.
  - Bell states / CHSH tests and stabilizer error-detection circuits belong to general foundational tracks (e.g. F1/F2) and are not deliverables for O1 Max-Cut.
- **Classification:** **PASS** (Confirmed out-of-scope for O1)
- **Severity:** NO ACTION
- **Proposed Correction:** Do not introduce synthetic Bell tests or parity-check code to avoid diluting the optimization focus.
- **Required Regression Test:** None.
- **Acceptance Criterion:** Scope strictly restricted to O1 Max-Cut and Processor A/B benchmarking.

---

### Finding AUD-08: Unexecuted Narrative Notebook Deliverable
- **ID:** AUD-08
- **Requirement or Claim:** Self-contained executable narrative Jupyter notebook (`main.ipynb`) demonstrating the full reproducible workflow.
- **Source File/Section:** [`PROJECT_SPEC.md`](file:///c:/Users/WIN_10/.gemini/antigravity/scratch/AXCUT/PROJECT_SPEC.md) Sec. 1, 3 (Layer 10); [`README.md`](file:///c:/Users/WIN_10/.gemini/antigravity/scratch/AXCUT/README.md) Sec. 7; [`main.ipynb`](file:///c:/Users/WIN_10/.gemini/antigravity/scratch/AXCUT/main.ipynb).
- **Available Evidence:**
  - `main.ipynb` contains 10 code cells.
  - Inspection of `main.ipynb` shows all code cells have `"execution_count": null` and `"outputs": []`.
  - Zero figures, print statements, or data tables are pre-rendered in the notebook.
  - Hackathon evaluators opening the notebook see blank outputs.
- **Classification:** **CONFIRMED DEFECT**
- **Severity:** **P1**
- **Proposed Correction:** In Phase 1, execute `main.ipynb` end-to-end to capture all pre-rendered outputs, plots, and execution counts.
- **Required Regression Test:** Automated notebook execution validation script checking `execution_count is not None` for all code cells.
- **Acceptance Criterion:** All 10 code cells have non-null execution counts and rendered text/figure outputs.

---

### Finding AUD-09: Missing Interactive Notebook Dependencies in Requirements
- **ID:** AUD-09
- **Requirement or Claim:** Reproducibility instructions specify `pip install -r requirements.txt` followed by `jupyter notebook main.ipynb`.
- **Source File/Section:** [`README.md`](file:///c:/Users/WIN_10/.gemini/antigravity/scratch/AXCUT/README.md) Sec. 7; [`requirements.txt`](file:///c:/Users/WIN_10/.gemini/antigravity/scratch/AXCUT/requirements.txt).
- **Available Evidence:**
  - `requirements.txt` contains: `qiskit`, `qiskit-aer`, `qiskit-ibm-runtime`, `networkx`, `numpy`, `scipy`, `pandas`, `matplotlib`, `pytest`.
  - `jupyter`, `notebook`, `ipykernel`, and `nbformat` are absent.
  - A reviewer creating a clean virtual environment from `requirements.txt` encounters `jupyter: command not found`.
- **Classification:** **CONFIRMED DEFECT**
- **Severity:** **P1**
- **Proposed Correction:** In Phase 1, add optional/interactive dependencies or add `jupyterlab>=4.0` / `notebook>=7.0` to `requirements.txt` or a `requirements-dev.txt`.
- **Required Regression Test:** `pip check` or import test for jupyter environment.
- **Acceptance Criterion:** Running the README setup sequence in a fresh venv allows launching `main.ipynb`.

---

### Finding AUD-10: Automated Test Suite Robustness
- **ID:** AUD-10
- **Requirement or Claim:** Comprehensive automated test suite validating the entire software pipeline.
- **Source File/Section:** [`PROJECT_SPEC.md`](file:///c:/Users/WIN_10/.gemini/antigravity/scratch/AXCUT/PROJECT_SPEC.md) Sec. 7; [`tests/`](file:///c:/Users/WIN_10/.gemini/antigravity/scratch/AXCUT/tests/).
- **Available Evidence:**
  - Executed `pytest -v` across all 13 test files.
  - Exactly 56 tests collected.
  - 56 passed in 29.64 seconds (100% pass rate).
- **Classification:** **PASS**
- **Severity:** NO ACTION
- **Proposed Correction:** None required for existing tests; will add regression tests for AUD-03 and AUD-04 in Phase 1.
- **Required Regression Test:** `pytest -q`
- **Acceptance Criterion:** 56/56 passing tests maintained.

---

### Finding AUD-11: Processor Architecture Mismatch (5Q Overview vs. 7Q Hardware Spec) & 6-Vertex Graph Compatibility
- **ID:** AUD-11
- **Requirement or Claim:** Investigate reported mismatch: uploaded overview describes a 5-qubit Processor A and 7-qubit heavy-hex-inspired Processor B, while the project repository defines two 7-qubit targets, with heavy-hex assigned to Processor A (`Falcon-H`, native `ecr`) and a 7-qubit ring assigned to Processor B (`Ring-7`, native `cz`). Determine whether the 6-vertex challenge graph is compatible with Processor A.
- **Source File/Section:** Participant Instructions Overview vs. [`data/hardware_specs/processor_a.json`](file:///c:/Users/WIN_10/.gemini/antigravity/scratch/AXCUT/data/hardware_specs/processor_a.json), [`processors/processor_a/hardware_spec.json`](file:///c:/Users/WIN_10/.gemini/antigravity/scratch/AXCUT/processors/processor_a/hardware_spec.json), [`instances/challenge/o1_maxcut_instance.json`](file:///c:/Users/WIN_10/.gemini/antigravity/scratch/AXCUT/instances/challenge/o1_maxcut_instance.json).
- **Available Evidence:**
  1. **Strict Graph Size Constraint:** The official challenge problem instance [`instances/challenge/o1_maxcut_instance.json`](file:///c:/Users/WIN_10/.gemini/antigravity/scratch/AXCUT/instances/challenge/o1_maxcut_instance.json) contains exactly $|V| = 6$ vertices.
  2. **Topological Infeasibility of a 5-Qubit Target:** A 6-vertex graph strictly requires at least 6 qubits for standard QAOA embedding without graph reduction or multi-qubit virtualization. If Processor A were a 5-qubit processor, the 6-vertex problem could not be executed on it without dropping a vertex or altering the benchmark. Silently reducing the graph would violate the official competition rules.
  3. **Authoritative Challenge Kit Specifications:** Inspection of the authoritative Challenge Kit configuration files in the repository (`data/hardware_specs/processor_a.json` and `processors/processor_a/hardware_spec.json`) confirms that **Processor A has 7 physical qubits** (`num_qubits: 7`), structured as a Falcon-H heavy-hex tree subgraph (qubits 0–6) with native basis `[rz, sx, x, ecr]`. Processor B is a 7-qubit circular ring (`num_qubits: 7`, Ring-7) with native basis `[rz, sx, x, cz]`.
  4. **Graph Embedding Feasibility:** Both Processor A (7Q) and Processor B (7Q) successfully embed the 6-vertex challenge graph by allocating 6 active physical qubits and leaving 1 ancilla qubit idle (verified via Qiskit pass manager transpilation).
  5. **Resolution & Provenance Caveat:** While a 5-qubit processor cannot embed a 6-vertex QAOA instance without graph reduction, slide 4 of the quanTA overview deck explicitly specifies a 5-qubit Processor A and 7-qubit heavy-hex Processor B. Because the external Google Drive Challenge Kit is inaccessible offline, the repository's 7Q Falcon-H / 7Q Ring-7 definitions cannot be independently corroborated against the upstream source. Official processor provenance is therefore marked UNVERIFIED.
- **Classification:** **UNVERIFIED (EXTERNAL ACCESS REQUIRED)**
- **Severity:** **P1**
- **Proposed Correction:** Maintain repository specifications invariant (do not fabricate or substitute models), document the discrepancy with the overview slide, and seek official organizer confirmation before production release.
- **Required Regression Test:** `tests/test_processors_integration.py` ensuring full 6-node graph embeds on repository 7-qubit specifications without node truncation.
- **Acceptance Criterion:** Upstream organizer confirmation of authoritative processor definitions.
