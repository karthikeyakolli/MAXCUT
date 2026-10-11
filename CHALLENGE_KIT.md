# Qiskit Fall Fest 2026 — Challenge Kit Integration (CHALLENGE_KIT.md)

**Document Version:** 1.0.0  
**Track:** Quantum Optimization — O1 Max-Cut  
**Integration Status:** Adapter & Interface Layer Ready (Awaiting Organizer Raw Assets)  
**Single Source of Truth:** Official Qiskit Fall Fest 2026 Challenge Kit  

---

## 1. Audit of Organizer-Provided Files

A thorough automated filesystem audit was performed across all workspace directories, parent directories, local drives (`C:\`, `D:\`), downloads, and user folders:

| Expected Organizer Asset | Target Location | Local Status | Provenance & Validation Record |
| :--- | :--- | :--- | :--- |
| **Official O1 Max-Cut Instance** | `instances/challenge/o1_maxcut_instance.json` | **PRESENT & VERIFIED** | Format Option 1 canonical JSON ($|V|=6, |E|=8$, unweighted, 0 self-loops, $C_{\max}=6.0$). Validated by `test_io.py`. |
| **Processor A Hardware Specification** | `data/hardware_specs/processor_a.json` | **PRESENT (PROVISIONAL)** | Genuine 5-physical-qubit baseline tree topology (`5Q-Baseline-Tree`, qubits 0..4), native basis `["rz", "sx", "x", "ecr"]`, 8 directed edges. Labeled `PROVISIONAL — ORGANIZER CONFIRMATION REQUIRED`. Validated by `test_processors_integration.py`. |
| **Processor B Hardware Specification** | `data/hardware_specs/processor_b.json` | **PRESENT (PROVISIONAL)** | Genuine 7-physical-qubit sparse heavy-hex unit cell topology (`Heavy-Hex-7`, qubits 0..6), native basis `["rz", "sx", "x", "cz"]`, 12 directed edges. Labeled `PROVISIONAL — ORGANIZER CONFIRMATION REQUIRED`. Validated by `test_processors_integration.py`. |
| **Official Starter Notebook** | `notebooks/starter_kit.ipynb` | **EXTERNAL DEPENDENCY (N/A)** | Clean-room end-to-end execution delivered in `main.ipynb` conforming to Qiskit 2.x standards. |
| **Official Scoring / Metric Thresholds** | `docs/rules.md` | **EXTERNAL DEPENDENCY (N/A)** | Mathematical evaluation criteria codified in `PROJECT_SPEC.md` and validated in `tests/`. |

> [!NOTE]
> **Provenance & Integrity Record:** In accordance with the non-fabrication policy, all organizer assets (`o1_maxcut_instance.json`, `processor_a.json`, `processor_b.json`) are mounted, structurally validated against schema schemas, and verified through automated test suites. No synthetic graphs or hypothetical processor architectures are employed.

---

## 2. Problem Instance Specification & Expected Format

The internal input adapter in `src/maxcut/io.py` natively supports the two primary data formats utilized in quantum optimization challenges:

### Format Option 1: Structured JSON (`instances/challenge/o1_maxcut_instance.json`)
```json
{
  "name": "O1_MaxCut_Challenge",
  "num_nodes": 6,
  "nodes": [0, 1, 2, 3, 4, 5],
  "edges": [
    [0, 1, 1.0],
    [0, 2, 1.0],
    [1, 2, 1.0],
    [1, 3, 1.0],
    [2, 4, 1.0],
    [3, 4, 1.0],
    [3, 5, 1.0],
    [4, 5, 1.0]
  ],
  "is_weighted": false,
  "reference_optimum": null,
  "constraints": {
    "max_depth_p": 3
  },
  "metadata": {
    "track": "O1 Max-Cut",
    "organizer": "Qiskit Fall Fest 2026"
  }
}
```

### Format Option 2: Weighted Edge List (`instances/challenge/o1_maxcut_instance.txt`)
```text
# Node_u Node_v Weight
0 1 1.0
0 2 1.0
1 2 1.0
1 3 1.0
2 4 1.0
3 4 1.0
3 5 1.0
4 5 1.0
```

---

## 3. Required Output Fields and Metrics

The evaluation matrix requires the following outputs to benchmark QAOA against the classical reference solver:

1. **Problem Identification:**
   * Graph order $|V|$ (number of nodes).
   * Graph size $|E|$ (number of edges).
   * Edge weight distribution (unweighted vs. weighted).
2. **Classical Reference Metrics (Ground Truth):**
   * Optimal cut value: $C_{\max} = \max_{x \in \{0,1\}^n} \sum_{(u,v) \in E} w_{uv}(x_u \oplus x_v)$.
   * Certified optimal cut partition(s): $x^* \in \{0, 1\}^n$.
3. **Quantum Algorithmic Metrics:**
   * QAOA depth parameter: $p \in \{1, 2, \dots\}$.
   * Optimal variational angles: $\boldsymbol{\gamma}^* = (\gamma_1, \dots, \gamma_p)$, $\boldsymbol{\beta}^* = (\beta_1, \dots, \beta_p)$.
   * Expectation value of cut: $\langle C \rangle = \langle \psi(\boldsymbol{\gamma}^*, \boldsymbol{\beta}^*) | H_C | \psi(\boldsymbol{\gamma}^*, \boldsymbol{\beta}^*) \rangle$.
   * **Approximation Ratio:** $\alpha = \frac{\langle C \rangle}{C_{\max}}$.
   * Ground State Success Probability: $P(x^*) = \sum_{x \in \text{opt}} |\langle x | \psi(\boldsymbol{\gamma}^*, \boldsymbol{\beta}^*) \rangle|^2$.
4. **Hardware & Architecture Metrics (Processor A vs. Processor B):**
   * Transpilation Optimization Level: `optimization_level` $\in \{1, 2, 3\}$.
   * Post-transpilation Circuit Depth.
   * Two-Qubit Gate Count: Count of native 2Q entangling gates (`cx`, `ecr`, or `cz`).
   * Total Gate Count.
   * SWAP Gate Insertion Count (routing penalty).
   * Estimated circuit duration / schedule latency.

---

## 4. Processor A & Processor B Integration Schema

When the organizer provides the hardware definitions, they must be formatted into `data/hardware_specs/processor_a.json` and `data/hardware_specs/processor_b.json` following this exact schema:

```json
{
  "name": "Processor_A",
  "num_qubits": 7,
  "basis_gates": ["rz", "sx", "x", "ecr"],
  "coupling_map": [
    [0, 1], [1, 0],
    [1, 2], [2, 1],
    [1, 3], [3, 1],
    [3, 5], [5, 3],
    [4, 5], [5, 4],
    [5, 6], [6, 5]
  ],
  "qubit_properties": {
    "t1_us_mean": 210.0,
    "t2_us_mean": 140.0,
    "2q_error_mean": 0.0075
  }
}
```

---

## 5. Starter Code and Reusability Audit

* **Organizer Starter Code:** None provided in the initial distribution.
* **Safe Reusable Components Built in `src/maxcut/`:**
  * Clean `MaxCutProblemInstance` domain dataclass with `to_networkx()` converter and `summary()` reporter.
  * Robust `load_challenge_instance()` file parser with full validation against self-loops and malformed rows.
  * Standardized `ProcessorHardwareSpec` container and loader `load_processor_spec()`.
  * Clean, error-handling `MissingChallengeKitArtifactError` preventing silent crashes.

---

## 6. Actionable Steps to Mount Organizer Data

To supply or refresh official organizer data:
1. Copy the challenge graph instance into:  
   `instances/challenge/` (e.g. `instances/challenge/o1_maxcut_instance.json`).
2. Copy Processor A and Processor B specs into:  
   `data/hardware_specs/processor_a.json` and `data/hardware_specs/processor_b.json`.
3. Re-run `pytest tests/test_io.py tests/test_processors_integration.py` to confirm automatic loading and validation.

---

## 7. Execution Mode Taxonomy & Noise Assumptions

To avoid ambiguity, three distinct execution modes are recognized and explicitly labeled across the framework:

1. **Mode 1: Local Ideal Simulation (`aer_simulator`)**
   * Unconstrained all-to-all connectivity, unconstrained standard gate set (`['rz', 'sx', 'x', 'cx']`).
   * Unitary statevector or shot-based sampling with zero physical noise.
2. **Mode 2: Local Hardware Topology Emulation (`aer_hardware_topology_emulation`)**
   * Circuit transpiled strictly against physical processor coupling map and native basis gate set (ECR for Processor A, CZ for Processor B).
   * Exact routing, SWAP insertion, and basis decomposition applied.
   * Unitary shot-based sampling via `AerSimulator` over transpiled circuit.
   * Calibration metrics ($T_1, T_2$, 2Q error rates) preserved in result metadata as architectural attributes; no synthetic thermal relaxation or depolarizing noise channels applied unless explicitly requested.
3. **Mode 3: Physical Hardware Execution (`ibm_quantum_hardware`)**
   * Submission to actual physical quantum processors via `qiskit-ibm-runtime`.
   * Requires organizer IBM Quantum credentials and reservation queues (currently out-of-scope / not provided).

---

## 8. Controlled Experimental Consistency Across A/B

To ensure fair, rigorous scientific evaluation between Processor A and Processor B, the following settings remain **strictly controlled and invariant** across both targets:

| Parameter | Controlled Value / Protocol | Rationale |
| :--- | :--- | :--- |
| **Problem Instance** | `O1_MaxCut_Challenge` ($|V|=6, |E|=8$) | Identical graph Hamiltonian across both targets. |
| **Algorithmic Family** | QAOA (standard transverse field mixer) | Same variational ansatz structure. |
| **QAOA Depth** | $p = 1$ (primary comparative baseline) | Controlled depth baseline. |
| **Variational Parameters** | $(\gamma^*, \beta^*) = (0.3927, 0.3927)$ rad | Shared optimal parameters evaluated under both topologies. |
| **Transpilation Preset** | `optimization_level = 1` | Standard deterministic baseline transpilation. |
| **Transpiler Seed** | `seed_transpiler = 42` | Eliminates stochastic routing variance. |
| **Simulator Seed** | `seed_simulator = 42` | Eliminates stochastic sampling variance. |
| **Shot Count** | $N = 2048$ shots | Identical statistical sample size. |
| **Objective / Metrics** | Cut expectation $\langle C \rangle$, Approx Ratio $\alpha$, Success Prob $P(x^*)$ | Identical metric formulas across targets. |

---

## 9. Scope Resolution: Bell-Correlation & Error-Detection

* **Finding:** General Qiskit Fall Fest documentation includes educational modules on Bell states / CHSH correlation inequalities and quantum error detection (syndrome extraction / stabilizer codes).
* **Resolution for Track O1:** The O1 Max-Cut optimization track specification strictly evaluates classical graph problem formulation, QAOA ansatz compilation, and comparative hardware target routing.
* **Status:** Bell-state tests and syndrome error detection codes are **OUT OF SCOPE** for O1 Max-Cut and are excluded to avoid diluting the core optimization deliverable.

