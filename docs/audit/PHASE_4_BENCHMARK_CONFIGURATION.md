# MAXCUT PHASE 4 — GATE BASIS, NOISE AND TRANSPILE BASELINE

**Document Identifier:** `docs/audit/PHASE_4_BENCHMARK_CONFIGURATION.md`  
**Document Version:** 1.0.0  
**Phase:** Phase 4 — Gate Basis, Noise Calibration & Transpiler Baseline  
**Audit Date:** 2026-10-12  
**Auditor / Engineering Role:** Senior Qiskit Engineer & Hackathon Compliance Auditor  
**Track:** Quantum Optimization — O1 Max-Cut  
**Repository:** [MAXCUT (karthikeyakolli/MAXCUT)](file:///c:/Users/OMEN/.gemini/antigravity-ide/scratch/MAXCUT)  
**Status:** **BENCHMARK SPECIFICATIONS CONFIGURED & CERTIFIED**

---

## 1. Executive Summary & Verification Mandate

In accordance with the requirements frozen in **Phase 0** ([`docs/audit/PHASE_0_REQUIREMENT_FREEZE.md`](file:///c:/Users/OMEN/.gemini/antigravity-ide/scratch/MAXCUT/docs/audit/PHASE_0_REQUIREMENT_FREEZE.md)) and the architecture migration executed in **Phase 3** ([`docs/audit/PHASE_3_PROCESSOR_MIGRATION.md`](file:///c:/Users/OMEN/.gemini/antigravity-ide/scratch/MAXCUT/docs/audit/PHASE_3_PROCESSOR_MIGRATION.md)), Phase 4 implements the common benchmark execution settings defined in the **Updated Qiskit Fall Fest 2026 Challenge Kit**.

### Verification Highlights:
1. **Unified CX Basis Alphabet:** Both Processor A and Processor B strictly compile to the universal basis alphabet:
   $$\mathcal{B} = \{\text{rz}, \text{sx}, \text{x}, \text{cx}\}$$
   Legacy two-qubit entanglers (`ecr` on Processor A, `cz` on Processor B) have been completely removed from runtime compilation paths. They are **not** merely relabeled; fresh transpilation generates genuine CX decompositions.
2. **Standardized Synthetic Noise Calibration:** A uniform, hardware-agnostic synthetic error model is calibrated and applied equally across Processor A and Processor B:
   - Single-qubit depolarizing error: $p_{1Q} = 0.001$ ($0.1\%$) per native 1Q pulse (`sx`, `x`).
   - Two-qubit depolarizing error: $p_{CX} = 0.005$ ($0.5\%$) per native `cx` gate along directed coupling links.
   - Symmetric readout bit-flip error: $p_{RO} = 0.01$ ($1.0\%$) per measured physical qubit ($P(0|1) = P(1|0) = 0.01$).
   - Thermal relaxation ($T_1, T_2$) is explicitly excluded from the required baseline to prevent uncalibrated noise conflation.
3. **Rigorous Isolation of Ideal vs. Noisy Paths:** Ideal reference runs use pure unitary sampling (`noise_applied = False`, zero error channels attached to Aer). Noisy baseline runs use the verified synthetic channel (`noise_applied = True`).
4. **Deterministic SABRE Transpilation Baseline:** Pass managers enforce Qiskit 2.x preset level 1 with explicit SABRE layout, SABRE routing, and fixed random seeds (`seed_transpiler = 42`, `seed_simulator = 42`).
5. **Execution Budget Standard:** Default shot budget is certified at **$4096$ shots** per case.
6. **Strict Resource Accounting:** Total gate counts strictly encompass quantum unitary operations ($1\text{Q} + 2\text{Q}$). Measurement, reset, and barrier instructions are tracked in `gate_breakdown` but excluded from unitary gate counts. Circuit width, backend physical capacity, and active qubit counts remain cleanly separated.

---

## 2. Prescribed Basis Gate Configuration

### 2.1 Basis Alphabet Definition
Both Processor A (5Q linear chain) and Processor B (9Q sparse tree) compile strictly against the 4-gate basis:
$$\mathcal{B} = \{\text{rz}, \text{sx}, \text{x}, \text{cx}\}$$

```mermaid
flowchart LR
    subgraph Logical["Logical QAOA Ansatz"]
        RZZ["RZZ(w·γ) Interaction"]
        RX["RX(2β) Mixer"]
        H["Hadamard Init"]
    end

    subgraph Compiler["Preset Pass Manager (Level 1, SABRE)"]
        Decomp["Basis Translation & Routing"]
    end

    subgraph Native["Canonical Native Basis"]
        CX["cx (2Q Entangler)"]
        SX["sx (√X Pulse)"]
        X["x (π Pulse)"]
        RZ["rz (Virtual Phase)"]
    end

    Logical --> Compiler
    Compiler --> Native
```

### 2.2 Algebraic 2Q Gate Decompositions
In this canonical basis, all logical two-qubit interactions and routing permutations decompose into native CX gates:
1. **Logical Cost Unitary Decomposition ($R_{ZZ}$):**
   Each logical interaction $R_{ZZ}(\theta) = \exp(-i \frac{\theta}{2} Z \otimes Z)$ requires **exactly 2 native CX gates**:
   $$R_{ZZ}(\theta) \equiv \text{CX}(q_u, q_v) \cdot \left[ I \otimes R_Z(\theta) \right] \cdot \text{CX}(q_u, q_v)$$
   For our 5-qubit reduced problem instance ($6$ non-incident edges):
   $$\text{Basis Synthesis 2Q Gates} = 6 \times 2 = \mathbf{12 \text{ CX gates}}$$
2. **Routing Permutation Decomposition ($\text{SWAP}$):**
   Each routing SWAP gate decomposes into **exactly 3 native CX gates**:
   $$\text{SWAP}(q_u, q_v) \equiv \text{CX}(q_u, q_v) \cdot \text{CX}(q_v, q_u) \cdot \text{CX}(q_u, q_v)$$
   For SABRE routing inserting 2 SWAPs on linear or sparse tree topologies:
   $$\text{Routing 2Q Gates} = 2 \times 3 = \mathbf{6 \text{ CX gates}}$$
3. **Total Native Two-Qubit Gates:**
   $$\text{Transpiled 2Q Gates} = 12 + 6 = \mathbf{18 \text{ CX gates}}$$

### 2.3 Elimination of Legacy Bases
- **ECR Elimination:** Zero `ecr` gates appear in transpiled circuits or pass manager basis targets.
- **CZ Elimination:** Zero `cz` gates appear in transpiled circuits or pass manager basis targets.
- **Relabeling Prohibition:** Verification confirms that CX gates are native operations synthesized by the compiler pass manager, not renamed counts from legacy artifacts.

---

## 3. Canonical Synthetic Noise Model Calibration

### 3.1 Error Probability Specifications
To provide an apples-to-apples architectural comparison unclouded by disparate physical device variations, the Updated Challenge Kit specifies a uniform synthetic noise model across all processor targets:

| Error Channel | Mathematical Mechanism | Applied Instruction | Error Rate ($p$) | Qiskit Implementation |
| :--- | :--- | :---: | :---: | :--- |
| **1-Qubit Gate Noise** | Depolarizing Channel | `sx`, `x` | $p_{1Q} = 0.001$ ($0.1\%$) | `depolarizing_error(0.001, 1)` |
| **2-Qubit Gate Noise** | Depolarizing Channel | `cx` | $p_{CX} = 0.005$ ($0.5\%$) | `depolarizing_error(0.005, 2)` |
| **Readout Error** | Symmetric Bit-Flip | `measure` | $p_{RO} = 0.01$ ($1.0\%$) | `ReadoutError(ro_matrix)` |

### 3.2 Formal Noise Operator Mathematics
1. **Single-Qubit Depolarizing Superoperator:**
   Acting on single-qubit density matrix $\rho$ following an `sx` or `x` gate:
   $$\mathcal{E}_{1Q}(\rho) = (1 - p_{1Q}) \rho + \frac{p_{1Q}}{3} \left( X \rho X + Y \rho Y + Z \rho Z \right) \quad (p_{1Q} = 0.001)$$
   *Virtual $R_Z$ Exemption:* In accordance with superconducting transmon physics, single-qubit $R_Z$ rotations are implemented as instantaneous virtual Z-frame updates in software ($\theta$-phase shifts in microwave drives) and therefore incur zero physical depolarizing gate noise.
2. **Two-Qubit Depolarizing Superoperator:**
   Acting on two-qubit density matrix $\rho$ across valid coupling edge $(u, v)$ following a native `cx`:
   $$\mathcal{E}_{CX}(\rho) = (1 - p_{CX}) \rho + \frac{p_{CX}}{15} \sum_{P \in \{I, X, Y, Z\}^{\otimes 2} \setminus \{II\}} P \rho P \quad (p_{CX} = 0.005)$$
   Errors attach strictly along declared physical coupling map links:
   - Processor A: attached to all 8 directed pairs in $D_A$.
   - Processor B: attached to all 16 directed pairs in $D_B$.
3. **Symmetric Readout Bit-Flip Matrix:**
   Measurement on physical qubit $q$ produces classical bit $b \in \{0, 1\}$ according to transition probability matrix $\Lambda_{RO}$:
   $$\Lambda_{RO} = \begin{pmatrix} P(\text{meas}=0 \mid \text{state}=0) & P(\text{meas}=1 \mid \text{state}=0) \\ P(\text{meas}=0 \mid \text{state}=1) & P(\text{meas}=1 \mid \text{state}=1) \end{pmatrix} = \begin{pmatrix} 1 - p_{RO} & p_{RO} \\ p_{RO} & 1 - p_{RO} \end{pmatrix} = \begin{pmatrix} 0.99 & 0.01 \\ 0.01 & 0.99 \end{pmatrix}$$
   - State $|0\rangle$: $99.0\%$ probability of decoding `0`, $1.0\%$ probability of bit-flip to `1`.
   - State $|1\rangle$: $99.0\%$ probability of decoding `1`, $1.0\%$ probability of bit-flip to `0`.
   - **Contrast with Starter Guide:** The illustrative asymmetric matrix in early tutorials (e.g. $P(1|0)=0.02, P(0|1)=0.03$) is **not** used; the updated benchmark standard requires this certified symmetric matrix.

### 3.3 Thermal Relaxation & Non-Baseline Noise Policy
- **Thermal Relaxation ($T_1, T_2$):** Excluded from the required baseline noise model. Qubit properties in JSON specs record estimated mean coherence times ($T_1 \sim 210-240\ \mu\text{s}, T_2 \sim 140-160\ \mu\text{s}$) for reference, but thermal relaxation operators are not injected into baseline runs.
- **Ideal/Noisy Regime Separation:**
  - `execution_mode = "aer_hardware_topology_emulation"`: `noise_model = None`, `noise_applied = False`.
  - `execution_mode = "aer_noisy_simulation"`: `noise_model = build_noise_model(...)`, `noise_applied = True`.
  - No ideal simulation can accidentally ingest noise.

---

## 4. Prescribed Transpilation & Compiler Baseline

### 4.1 Compiler Pass Manager Specification
Circuits targeting all processors are compiled using Qiskit's preset pass manager configured as follows:
```python
pass_manager = generate_preset_pass_manager(
    coupling_map=self._coupling_map,
    basis_gates=self._spec.basis_gates,
    optimization_level=1,
    seed_transpiler=42,
    layout_method="sabre",
    routing_method="sabre",
)
```

### 4.2 Transpiler Parameter Invariance
1. **Optimization Level:** `optimization_level = 1` (Preset 1: standard unrolling, light single-qubit optimization, heuristic SABRE layout and routing).
2. **Layout Stage:** Explicitly forced to `"sabre"` (Stochastic Search Algorithm for Qubit Placement).
3. **Routing Stage:** Explicitly forced to `"sabre"` (SWAP-based heuristic distance minimizer).
4. **Seed Policy:**
   - Transpiler Seed: `seed_transpiler = 42` strictly fixed across all compilation calls.
   - Simulation Seed: `seed_simulator = 42` strictly fixed across all Aer simulator calls.
5. **Metadata Traceability:** Every compiled circuit record and job result dictionary explicitly serializes:
   - `"optimization_level": 1`
   - `"layout_method": "sabre"`
   - `"routing_method": "sabre"`
   - `"seed_transpiler": 42`
   - `"seed_simulator": 42`

---

## 5. Execution Budget & Resource Accounting Rules

### 5.1 Shot Budget Standard
- **Baseline Allocation:** Exactly **$4096$ shots** per experimental run.
- **Decoupling from Legacy Runs:** Replaces older v1/v2/v3 2048-shot datasets. All v4 benchmark evaluations will execute under the certified 4096-shot budget.

### 5.2 Resource Accounting & Non-Unitary Operation Handling
In accordance with Challenge Kit gate-cost reporting rules:
1. **Unitary Gate Count ($N_{\text{unitary}}$):**
   Only physical quantum unitary transformations are included in the primary gate count:
   $$N_{\text{total\_gates}} = N_{1Q} + N_{2Q} = \sum_{g \in \{\text{rz}, \text{sx}, \text{x}\}} \text{count}(g) + \sum_{g \in \{\text{cx}\}} \text{count}(g)$$
2. **Non-Unitary Instructions:**
   - `measure`: Excluded from unitary gate count; tracked in `gate_breakdown["measure"]`.
   - `barrier`: Excluded from unitary gate count; tracked in `gate_breakdown["barrier"]`.
   - `reset`: Excluded from unitary gate count; tracked in `gate_breakdown["reset"]` if present.
3. **Circuit Metric Decoupling:**
   - **Logical Circuit Width ($n_{\text{logical}}$):** Number of virtual qubits in ansatz ($5$ for reduced, $6$ for unreduced).
   - **Backend Physical Width ($N_{\text{phys}}$):** Total physical qubits supported on target ($5$ on A, $9$ on B).
   - **Actively Occupied Qubits ($N_{\text{active}}$):** Subset of physical qubits executing operations ($5$ on A, $5$ on B for reduced QAOA).
   - **Idle Qubits ($N_{\text{idle}} = N_{\text{phys}} - N_{\text{active}}$):** Unallocated hardware qubits ($0$ on A, $4$ on B). **Never labeled as active circuit ancillas.**
   - **Circuit Depth ($D$):** Critical path length in compiled hardware cycles.

---

## 6. Noise & Compiler Verification Test Suite

The configuration standards detailed in this report are formally certified by automated tests:

### 6.1 Test Suite Traceability

| Test Module / Function | Scope Verified | Result |
| :--- | :--- | :---: |
| [`tests/test_phase4_benchmark_configuration.py`](file:///c:/Users/OMEN/.gemini/antigravity-ide/scratch/MAXCUT/tests/test_phase4_benchmark_configuration.py) | Canonical noise rates ($p_1=0.001, p_2=0.005, p_{ro}=0.01$), symmetric readout matrix math, basis gates, 4096 shots budget. | **PASS (6/6 tests)** |
| [`tests/test_noise_backend.py`](file:///c:/Users/OMEN/.gemini/antigravity-ide/scratch/MAXCUT/tests/test_noise_backend.py) | Aer noise model construction, depolarizing error on native CX, missing noise config error blocking, ideal vs. noisy isolation. | **PASS** |
| [`tests/test_circuit_metrics.py`](file:///c:/Users/OMEN/.gemini/antigravity-ide/scratch/MAXCUT/tests/test_circuit_metrics.py) | Circuit resource metrics, native CX gate breakdown, routing SWAP decomposition, total gate reconciliation. | **PASS** |
| [`tests/test_processors_integration.py`](file:///c:/Users/OMEN/.gemini/antigravity-ide/scratch/MAXCUT/tests/test_processors_integration.py) | End-to-end integration with Processor A & B adapters, metadata extraction, pass manager compilation. | **PASS** |

### 6.2 Python AST Syntax Audit
All 21 test suites in `tests/` and all module files in `processors/` pass Python AST validation with zero errors.

---

## 7. Acceptance Gate Determination

### Phase 4 Verification Checklist:
- [x] Basis gates strictly set to `["rz", "sx", "x", "cx"]` across all targets.
- [x] Legacy entanglers (`ecr`, `cz`) eliminated from live execution paths.
- [x] Uniform synthetic noise rates ($p_{1Q}=0.001, p_{CX}=0.005, p_{RO}=0.01$) calibrated identically across A and B.
- [x] Symmetric readout bit-flip matrix ($P(0|1) = P(1|0) = 0.01$) certified.
- [x] Zero thermal relaxation mixed into the baseline error model.
- [x] Strict isolation of ideal reference (zero noise channels attached) maintained.
- [x] Preset pass manager configured with level 1, SABRE layout, SABRE routing, and seed 42.
- [x] 4096-shot execution budget declared in configuration files.
- [x] Resource accounting rules properly treat non-unitary operations and decouple widths from active qubits.
- [x] Deliverable `docs/audit/PHASE_4_BENCHMARK_CONFIGURATION.md` created.
- [x] Historical experiment outputs in `results/` preserved without modification.

**Phase 4 Acceptance Gate:** **SATISFIED AND LOCKED.**  
The gate basis, synthetic noise model, and compiler baseline are certified correct. The repository is ready to execute Phase 5 (4-Case Experimental Matrix Rebuild & Custom Processor D Architecture) upon user authorization.
