# Qiskit Fall Fest 2026 — Challenge Kit Integration (CHALLENGE_KIT.md)

**Document Version:** 1.0.0  
**Track:** Quantum Optimization — O1 Max-Cut  
**Integration Status:** Adapter & Interface Layer Ready (Awaiting Organizer Raw Assets)  
**Single Source of Truth:** Official Qiskit Fall Fest 2026 Challenge Kit  

---

## 1. Audit of Organizer-Provided Files

A thorough automated filesystem audit was performed across all workspace directories, parent directories, local drives (`C:\`, `D:\`), downloads, and user folders:

| Expected Organizer Asset | Target Location | Local Status | Policy Action |
| :--- | :--- | :--- | :--- |
| **Official O1 Max-Cut Instance** | `instances/challenge/` | **ABSENT** | Documented as external dependency. **Zero fabrication**; schema adapter created in `src/maxcut/io.py`. |
| **Processor A Hardware Specification** | `data/hardware_specs/processor_a.json` | **ABSENT** | Documented as external dependency. **Zero assumption**; adapter placeholder created. |
| **Processor B Hardware Specification** | `data/hardware_specs/processor_b.json` | **ABSENT** | Documented as external dependency. **Zero assumption**; adapter placeholder created. |
| **Official Starter Notebook** | `notebooks/starter_kit.ipynb` | **ABSENT** | Safe clean-room implementation conforming to Qiskit 2.x standards. |
| **Official Scoring / Metric Thresholds** | `docs/rules.md` | **ABSENT** | Mathematical standard criteria established in `PROJECT_SPEC.md`. |

> [!IMPORTANT]
> **Strict Competition Policy:** In accordance with the non-fabrication rule, synthetic graphs, speculative processor coupling maps, and arbitrary benchmark values have **NOT** been invented. The adapter is primed to ingest the raw organizer files the moment they are copied to `instances/challenge/`.

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

To supply the official organizer data:
1. Copy the challenge graph instance into:  
   `instances/challenge/` (e.g. `instances/challenge/o1_maxcut.json`).
2. Copy Processor A and Processor B specs into:  
   `data/hardware_specs/processor_a.json` and `data/hardware_specs/processor_b.json`.
3. Re-run `pytest tests/test_io.py` to confirm automatic loading and validation.
