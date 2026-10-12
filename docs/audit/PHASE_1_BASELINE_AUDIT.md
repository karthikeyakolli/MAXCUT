# MAXCUT PHASE 1 — BASELINE REPOSITORY AUDIT

**Document Identifier:** `docs/audit/PHASE_1_BASELINE_AUDIT.md`  
**Document Version:** 1.0.0  
**Phase:** Phase 1 — Baseline Repository Audit  
**Audit Date:** 2026-10-12  
**Auditor / Engineering Role:** Senior Qiskit Engineer & Software Quality Auditor  
**Track:** Quantum Optimization — O1 Max-Cut  
**Repository:** [MAXCUT (karthikeyakolli/MAXCUT)](file:///c:/Users/OMEN/.gemini/antigravity-ide/scratch/MAXCUT)  
**Status:** **AUTHORITATIVE BASELINE AUDIT COMPLETE — RUNTIME PATHWAYS & ASSUMPTIONS MAPPED**

---

## 1. Executive Summary & Audit Mandate

### 1.1 Objective & Compliance Scope
In accordance with the Phase 1 charter for the **O1 Max-Cut** project:
- **Zero Modifications:** No application code, processor configurations, graph data, automated tests, Jupyter notebooks, historical result files, or existing audit documentation were modified.
- **Working Tree Preservation:** The user's active workspace and files remain 100% unaltered.
- **Evidence-Based Investigation:** Previous Antigravity narrative reports were not accepted as proof of current code behavior. Every operational assumption was audited directly from source files, AST analysis, schema inspections, and non-destructive execution commands.
- **Offline / Environment Isolation:** System Python runtimes, package availability, and toolchain configurations were formally inventoried.

### 1.2 Audit Outcome Summary
1. **Core Architecture Stability:** The repository possesses a well-structured, 10-layer modular architecture in `src/maxcut/` with an exact classical brute-force solver ($C_{\max} = 6.0000$), verified QUBO/Ising mathematical formulations, and endian-safe Qiskit measurement decoding.
2. **Pre-Rendered Notebook Integrity:** `main.ipynb` is a valid Jupyter Notebook (v4.5) containing 22 cells (10 code cells). All 10 code cells have non-null execution counts ($1 \dots 10$) and pre-rendered outputs, including embedded Matplotlib base64 PNG figures and tabular streams.
3. **Artifact Completeness:** All 5 configuration files, 10 result data files, 12 markdown tables, 9 publication PNG figures, and 4 raw measurement count JSON files verified by `scripts/validate_artifacts.py` exist on disk and are non-empty.
4. **Historical Divergence & Duplication:** The repository currently reflects a hybrid state resulting from previous iteration rebuilds:
   - `results/verified_ab_v2/` reflects v2 (7Q Falcon-H with `ecr` vs. 7Q Ring-7 with `cz`, 2048 shots).
   - `results/verified_ab_v3/` reflects v3 (5Q `5Q-Baseline-Tree` with `ecr` vs. 7Q `Heavy-Hex-7` with `cz`, 2048 shots).
   - `main.ipynb` currently loads from `results/verified_ab_v3/`.
   - `report/analysis.md` contains a mixed narrative: its introduction crosswalk cites v3 numbers, while its body sections cite older v1/v2 data (28 two-qubit gates, 4 SWAPs) from `results/data/`.
   - Neither v2 nor v3 matches the **Phase 0 Frozen Target** (Processor A = 5Q linear chain `cx`; Processor B = 9Q sparse tree `cx`; 4096 shots; uniform noise).

---

## 2. Comprehensive Repository Inventory

```text
c:\Users\OMEN\.gemini\antigravity-ide\scratch\MAXCUT\
├── .git/                                 # Git repository metadata (branch: main)
├── .github/workflows/ci.yml              # CI test workflow (Python 3.11/3.12 matrix)
├── configs/
│   └── experiment.json                   # Central experiment configuration (shots: 2048, seeds: 42)
├── conftest.py                           # Pytest root configuration
├── pyproject.toml                        # Build & package configuration (maxcut v0.1.0)
├── requirements.txt                      # Pinned production & interactive dependencies
├── README.md                             # Top-level documentation & quickstart
├── CHALLENGE_KIT.md                      # Challenge kit integration & asset audit
├── PROJECT_SPEC.md                       # Comprehensive architectural & engineering specification
├── main.ipynb                            # Pre-rendered 10-cell executable demonstration notebook
│
├── instances/
│   └── challenge/
│       └── o1_maxcut_instance.json       # Official 6-node, 8-edge challenge graph (W=8.00)
│
├── data/
│   └── hardware_specs/
│       ├── processor_a.json              # Processor A spec copy (5Q-Baseline-Tree, ecr, 8 directed edges)
│       └── processor_b.json              # Processor B spec copy (Heavy-Hex-7, cz, 12 directed edges)
│
├── processors/
│   ├── __init__.py
│   ├── processor_a/
│   │   ├── __init__.py
│   │   ├── adapter.py                    # ProcessorABackend adapter class
│   │   └── hardware_spec.json            # Authoritative spec for Proc A (5Q-Baseline-Tree, ecr)
│   └── processor_b/
│       ├── __init__.py
│       ├── adapter.py                    # ProcessorBBackend adapter class
│       └── hardware_spec.json            # Authoritative spec for Proc B (Heavy-Hex-7, cz)
│
├── src/maxcut/
│   ├── __init__.py
│   ├── io.py                             # Challenge instance & processor hardware spec loader
│   ├── classical/
│   │   ├── __init__.py
│   │   └── solver.py                     # Exact exhaustive combinatorial reference solver
│   ├── domain/
│   │   ├── __init__.py
│   │   └── model.py                      # Graph, Edge, Partition, and CutResult domain models
│   ├── formulation/
│   │   ├── __init__.py
│   │   └── qubo.py                       # Unreduced & 5Q symmetry-reduced QUBO/Ising/SparsePauliOp
│   ├── qaoa/
│   │   ├── __init__.py
│   │   ├── ansatz.py                     # Parameterized QAOA circuit builder (standard & reduced)
│   │   ├── optimizer.py                  # Classical COBYLA/SLSQP parameter optimizer
│   │   └── decoding.py                   # Little-endian measurement decoder & cut statistics
│   ├── backends/
│   │   ├── __init__.py
│   │   ├── base.py                       # BaseBackendRunner abstract base class
│   │   ├── aer_backend.py                # AerBackendRunner (ideal unconstrained statevector/shots)
│   │   ├── processor_backend.py          # ProcessorBackendRunner (Aer topology emulation + noise)
│   │   └── factory.py                    # Backend factory instantiator
│   ├── metrics/
│   │   ├── __init__.py
│   │   ├── circuit_metrics.py            # CircuitResourceMetrics container & SWAP extractor
│   │   └── comparator.py                 # Multi-backend comparative transpiler runner
│   ├── experiments/
│   │   ├── __init__.py
│   │   ├── config.py                     # ExperimentConfig schema
│   │   ├── runner.py                     # ExperimentRunner orchestrator
│   │   ├── schema.py                     # Result dataclass schemas
│   │   └── aer_experiment.py             # Aer-specific experiment executor
│   └── visualization/
│       ├── __init__.py
│       ├── plot_graph.py                 # NetworkX partition visualization
│       ├── plot_circuit.py               # Circuit resource radar/bar charts
│       └── plot_distribution.py          # Measurement probability histograms
│
├── tests/                                # 20 automated test modules (115 total unit/regression tests)
│   ├── test_aer_experiment.py (6)
│   ├── test_circuit_metrics.py (6)
│   ├── test_classical.py (7)
│   ├── test_domain.py (10)
│   ├── test_experiment_framework.py (5)
│   ├── test_formulation.py (10)
│   ├── test_imports.py (4)
│   ├── test_io.py (4)
│   ├── test_noise_backend.py (7)
│   ├── test_processor_experiments.py (3)
│   ├── test_processors_integration.py (6)
│   ├── test_qaoa.py (6)
│   ├── test_reduced_formulation.py (7)
│   ├── test_reduced_processor_integration.py (8)
│   ├── test_statistics.py (5)
│   ├── test_validation_audit.py (1)
│   ├── test_verified_ab_v2_experiments.py (7)
│   ├── test_verified_ab_v2_statistics.py (3)
│   ├── test_verified_ab_v3_experiments.py (7)
│   └── test_verified_ab_v3_statistics.py (3)
│
├── scripts/                              # 21 utility, experiment, and audit scripts
│   ├── analyze_noise_metrics.py
│   ├── analyze_processor_circuits.py
│   ├── analyze_verified_ab_v2_statistics.py
│   ├── analyze_verified_ab_v3_statistics.py
│   ├── build_and_render_notebook.py      # Script that executed and generated main.ipynb
│   ├── generate_analysis_artifacts.py
│   ├── generate_notebook.py
│   ├── run_aer_experiment.py
│   ├── run_classical_reference.py
│   ├── run_phase_r2_experiments.py
│   ├── run_processor_experiments.py
│   ├── run_reduced_5q_integration.py
│   ├── run_transpile_check.py
│   ├── run_validation_audit.py           # 10-gate pre-hardware validation suite
│   ├── run_verified_ab_v2_experiments.py
│   ├── run_verified_ab_v3_experiments.py
│   ├── update_all_docs_v3.py
│   ├── update_docs_v3.py
│   ├── validate_artifacts.py             # Schema & presence verification of deliverables
│   ├── validate_challenge_kit.py
│   └── verify_statistics.py
│
├── results/                              # 6 subdirectories storing circuits, data, figures, tables
│   ├── circuits/                         # QASM / ASCII circuit dumps (v1/v2/reduced)
│   ├── data/                             # Primary baseline JSON metrics (classical_reference, etc.)
│   ├── figures/                          # Publication PNG plots (figures 1–6)
│   ├── tables/                           # Markdown and CSV benchmark tables
│   ├── verified_ab_v2/                   # Phase 4 / v2 isolated experiment run data (7Q/7Q)
│   └── verified_ab_v3/                   # Version 3 isolated experiment run data (5Q/7Q, 4 count JSONs)
│
├── report/
│   └── analysis.md                       # Comprehensive 496-line technical narrative report
│
└── docs/
    ├── validation_report.md              # 10-gate pre-hardware validation report
    └── audit/                            # 12 authoritative compliance audit documents
        ├── PHASE_0_REQUIREMENT_FREEZE.md # Authoritative requirement freeze & source hierarchy
        ├── PROCESSOR_PROVENANCE.md
        ├── FIVE_QUBIT_SYMMETRY_REDUCTION.md
        ├── OFFICIAL_PROCESSOR_AB_INTEGRATION.md
        ├── FINAL_COMPLIANCE_CHECK.md
        ├── FINAL_HACKATHON_READINESS_REPORT.md
        ├── HACKATHON_COMPLIANCE_VERIFICATION.md
        ├── CLAIM_EVIDENCE_MATRIX.md
        ├── COMPLIANCE_MATRIX.md
        ├── REQUIREMENT_TRACEABILITY.md
        ├── UPGRADE_PLAN.md
        └── AUDIT_ID_CROSSWALK.md
```

---

## 3. Current-to-Target Mismatch Table

The table below contrasts the active repository implementation against the frozen Phase 0 target requirements approved from the Updated Challenge Kit:

| Feature / Dimension | Current Repository Implementation (v3 State) | Target Approved in Phase 0 (Updated Kit) | Controlling File(s) in Codebase | Mismatch Severity |
| :--- | :--- | :--- | :--- | :---: |
| **Processor A Qubit Count** | 5 physical qubits ($0 \dots 4$) | 5 physical qubits ($0 \dots 4$) | `processors/processor_a/hardware_spec.json`<br>`data/hardware_specs/processor_a.json` | **MATCH** |
| **Processor A Topology** | Branching tree: $(0,1), (1,2), (1,3), (3,4)$ (node 1 is degree-3 hub, 4 undirected edges) | Strictly linear chain: $(0,1), (1,2), (2,3), (3,4)$ (4 undirected edges, max degree 2) | `processors/processor_a/hardware_spec.json`<br>`data/hardware_specs/processor_a.json`<br>`tests/test_processors_integration.py` | **CRITICAL MISMATCH** |
| **Processor A Native 2Q Gate** | `ecr` (Echoed Cross-Resonance) | `cx` (Controlled-NOT) | `processors/processor_a/hardware_spec.json`<br>`processors/processor_a/adapter.py` | **CRITICAL MISMATCH** |
| **Processor B Qubit Count** | 7 physical qubits ($0 \dots 6$) | Exactly 9 physical qubits ($0 \dots 8$) | `processors/processor_b/hardware_spec.json`<br>`data/hardware_specs/processor_b.json` | **CRITICAL MISMATCH** |
| **Processor B Topology** | 6 undirected edges: $(0,1), (1,2), (1,3), (3,5), (4,5), (5,6)$ (`Heavy-Hex-7` unit cell) | 8 undirected edges: $(0,1), (1,2), (2,3), (2,4), (4,5), (5,6), (4,7), (7,8)$ | `processors/processor_b/hardware_spec.json`<br>`data/hardware_specs/processor_b.json`<br>`tests/test_processors_integration.py` | **CRITICAL MISMATCH** |
| **Processor B Native 2Q Gate** | `cz` (Controlled-Z) | `cx` (Controlled-NOT) | `processors/processor_b/hardware_spec.json`<br>`processors/processor_b/adapter.py` | **CRITICAL MISMATCH** |
| **Processor C Definition** | Excluded / marked out-of-scope | 13-qubit study/reference architecture | `PROJECT_SPEC.md`<br>`docs/audit/REQUIREMENT_TRACEABILITY.md` | **DOCUMENTATION GAP** |
| **Processor D Scope** | Excluded as non-goal in `PROJECT_SPEC.md` | Mandated custom architecture targeting A/B bottleneck | `PROJECT_SPEC.md` line 43<br>`docs/audit/FINAL_COMPLIANCE_CHECK.md` | **SCOPE DEFICIT** |
| **Single-Qubit Noise ($p_{1Q}$)** | $0.0005$ (Proc A) / $0.0003$ (Proc B) | Uniform $p_{1Q} = 0.001$ per single-qubit gate | `hardware_spec.json`<br>`scripts/run_verified_ab_v3_experiments.py` | **NUMERICAL MISMATCH** |
| **Two-Qubit Noise ($p_{2Q}$)** | $0.0075$ (ECR on A) / $0.0050$ (CZ on B) | Uniform $p_{CX} = 0.005$ per native CX | `hardware_spec.json`<br>`scripts/run_verified_ab_v3_experiments.py` | **NUMERICAL MISMATCH** |
| **Readout Error ($p_{RO}$)** | $0.015$ (Proc A) / $0.010$ (Proc B) | Symmetric $p_{RO} = 0.01$ per measured qubit | `hardware_spec.json`<br>`src/maxcut/backends/processor_backend.py` | **NUMERICAL MISMATCH** |
| **Shot Count Budget** | 2048 shots across v2 and v3 experiments | 4096 shots default budget | `configs/experiment.json` line 36<br>`scripts/run_verified_ab_v3_experiments.py` line 57 | **SAMPLE SIZE DEFICIT** |
| **Transpiler Opt Level** | `optimization_level = 1` baseline | `optimization_level = 1` baseline | `scripts/run_verified_ab_v3_experiments.py`<br>`src/maxcut/metrics/comparator.py` | **MATCH** |
| **Routing Algorithm** | SABRE (Qiskit preset default) | SABRE layout and routing | `processors/*/adapter.py`<br>`src/maxcut/metrics/comparator.py` | **MATCH** |
| **RNG Seeds** | Seed 42 (simulator, transpiler, global) | Seed 42 fixed across pipelines | `configs/experiment.json`<br>`scripts/run_verified_ab_v3_experiments.py` | **MATCH** |
| **Graph Input Weights** | $w = 1.0$ across 8 edges (`is_weighted: false`) | Integer weights $1 \le w \le 5$, fixed graph | `instances/challenge/o1_maxcut_instance.json`<br>`src/maxcut/io.py` | **FROZEN (Action 5 Decision)** |
| **Symmetry Reduction** | 5Q reduced formulation ($x_0 = 0$) | Instruction not to delete variables | `src/maxcut/formulation/qubo.py`<br>`src/maxcut/qaoa/ansatz.py` | **FROZEN (Action 6 Dual-Track)** |

---

## 4. Main Execution Path from Graph Input to Results

The active computational pipeline executes in 10 sequential stages:

```mermaid
flowchart TD
    G1["1. Graph Ingestion<br/>(instances/challenge/o1_maxcut_instance.json)"] --> G2["2. Domain Graph Modeling<br/>(src/maxcut/domain/model.py: MaxCutGraph)"]
    G2 --> G3["3. Classical Exact Ground Truth<br/>(src/maxcut/classical/solver.py: C_max = 6.0000)"]
    G2 --> G4["4. QUBO / Ising Formulation<br/>(src/maxcut/formulation/qubo.py: H_C)"]
    G4 --> G5["5. QAOA Circuit Construction<br/>(src/maxcut/qaoa/ansatz.py: p=1)"]
    G5 --> G6["6. Classical Angle Optimization<br/>(COBYLA: gamma*=2.5270, beta*=2.6983)"]
    G6 --> G7["7. Hardware Target Transpilation<br/>(generate_preset_pass_manager, opt=1, seed=42)"]
    G7 --> G8["8. Aer Emulation & Noise Injection<br/>(src/maxcut/backends/processor_backend.py)"]
    G8 --> G9["9. Little-Endian Decoding & Metrics<br/>(src/maxcut/qaoa/decoding.py & circuit_metrics.py)"]
    G9 --> G10["10. Artifact Serialization & Notebook<br/>(results/verified_ab_v3/ & main.ipynb)"]
```

### Detailed Execution Trace:
1. **Graph Ingestion:**
   - Module: [`src/maxcut/io.py`](file:///c:/Users/OMEN/.gemini/antigravity-ide/scratch/MAXCUT/src/maxcut/io.py) via `load_challenge_instance()`.
   - Ingests `instances/challenge/o1_maxcut_instance.json`. Validates zero self-loops, extracts 6 nodes, 8 edges ($w=1.0$), and detects `is_weighted = False`.
2. **Domain Model Conversion:**
   - Module: [`src/maxcut/domain/model.py`](file:///c:/Users/OMEN/.gemini/antigravity-ide/scratch/MAXCUT/src/maxcut/domain/model.py) via `MaxCutGraph.from_challenge_instance()`.
   - Constructs immutable `MaxCutGraph` with canonical edge sorting ($u < v$), computing total weight $W = 8.00$.
3. **Classical Reference Solution:**
   - Module: [`src/maxcut/classical/solver.py`](file:///c:/Users/OMEN/.gemini/antigravity-ide/scratch/MAXCUT/src/maxcut/classical/solver.py) via `ExactExhaustiveSolver.solve()`.
   - Evaluates all $2^6 = 64$ binary states in $0.613\text{ ms}$. Confirms $C_{\max} = 6.0000$ and identifies 10 optimal bitstrings (5 complementary pairs). Serializes to `results/data/classical_reference.json`.
4. **Hamiltonian Formulation:**
   - Module: [`src/maxcut/formulation/qubo.py`](file:///c:/Users/OMEN/.gemini/antigravity-ide/scratch/MAXCUT/src/maxcut/formulation/qubo.py).
   - Generates 5-qubit reduced Cost Hamiltonian via `build_reduced_cost_hamiltonian(graph, fixed_node=0)`.
   - For incident edges $(0, 1)$ and $(0, 2)$, induces longitudinal magnetic field $h_v = +0.5 \cdot w_{0v} Z_v$.
   - For non-incident edges, induces quadratic couplings $0.5 \cdot w_{uv} Z_u Z_v$.
   - Constant identity offset: $-0.5 \cdot W \cdot I = -4.0 \cdot I$.
   - Yields exact ground state energy $E_0 = -6.0000$ (satisfies $E_0 = -C_{\max}$).
5. **QAOA Ansatz Synthesis:**
   - Module: [`src/maxcut/qaoa/ansatz.py`](file:///c:/Users/OMEN/.gemini/antigravity-ide/scratch/MAXCUT/src/maxcut/qaoa/ansatz.py).
   - `build_reduced_qaoa_circuit(graph, p=1, fixed_node=0)` constructs a 5-qubit parameterized circuit:
     - 5 Hadamard gates initialization.
     - Cost layer: 6 $R_{ZZ}(w \cdot \gamma)$ entangling gates + 2 $R_Z(w \cdot \gamma)$ phase gates.
     - Mixer layer: 5 $R_X(2\beta)$ transverse field rotations.
     - Logical depth = 8 cycles; total logical gates = 18.
6. **Variational Parameter Optimization:**
   - Module: `scripts/run_verified_ab_v3_experiments.py` (lines 88–116).
   - Minimizes $\langle \psi(\gamma, \beta) | H_C | \psi(\gamma, \beta) \rangle$ over statevector simulation using COBYLA (maxiter=200, tol=1e-4, seed=42).
   - Converges to optimal angles:
     $$\gamma^* = 2.527013\text{ rad}, \quad \beta^* = 2.698305\text{ rad}$$
   - Analytic theoretical expectation: $\langle C \rangle_{\text{analytic}} = 5.03998\approx 5.0400$, approximation ratio $\alpha = 0.8400$.
7. **Hardware Compilation & Transpilation:**
   - Factory: [`src/maxcut/backends/factory.py`](file:///c:/Users/OMEN/.gemini/antigravity-ide/scratch/MAXCUT/src/maxcut/backends/factory.py) instantiates `ProcessorABackend` and `ProcessorBBackend`.
   - Compiles bound circuit using `generate_preset_pass_manager(optimization_level=1, seed_transpiler=42)`.
   - Dynamic DAG callback inspects intermediate routing before basis synthesis to extract exact inserted SWAP count.
8. **Aer Emulation & Synthetic Noise Injection:**
   - Module: [`src/maxcut/backends/processor_backend.py`](file:///c:/Users/OMEN/.gemini/antigravity-ide/scratch/MAXCUT/src/maxcut/backends/processor_backend.py).
   - Executes via `AerSimulator(seed_simulator=42)` across 4 distinct regimes:
     - Case 1 (A Ideal): unitary emulation, zero noise channels.
     - Case 2 (A Noisy): $p_{1Q}=0.0005$, $p_{2Q}=0.0075$ (ECR), $p_{RO}=0.015$.
     - Case 3 (B Ideal): unitary emulation, zero noise channels.
     - Case 4 (B Noisy): $p_{1Q}=0.0003$, $p_{2Q}=0.0050$ (CZ), $p_{RO}=0.010$.
   - Current shot budget executes 2048 shots per case.
9. **Endian Decoding & Metric Extraction:**
   - Module: [`src/maxcut/qaoa/decoding.py`](file:///c:/Users/OMEN/.gemini/antigravity-ide/scratch/MAXCUT/src/maxcut/qaoa/decoding.py).
   - `decode_reduced_qiskit_counts()` maps measured little-endian bits from 5 active qubits and re-inserts $x_0 = 0$ at vertex 0, producing valid 6-bit strings.
   - Resource metrics extracted via [`src/maxcut/metrics/circuit_metrics.py`](file:///c:/Users/OMEN/.gemini/antigravity-ide/scratch/MAXCUT/src/maxcut/metrics/circuit_metrics.py), reconciling basis synthesis vs. routing SWAPs.
10. **Results Serialization & Notebook Rendering:**
    - Raw counts written to `results/verified_ab_v3/counts_*.json`.
    - Statistical summaries, Wilson score intervals, Welch $t$-tests, and two-proportion $z$-tests serialized to `results/verified_ab_v3/data/` and `tables/`.
    - `scripts/build_and_render_notebook.py` constructs and executes `main.ipynb` end-to-end via `nbclient`, producing all rendered figures and cells.

---

## 5. Historical vs. Current Result Directories

The repository contains three generations of experimental data across `results/`:

```mermaid
graph TD
    subgraph Gen1["Generation 1: Initial Baseline (results/data/, results/tables/)"]
        D1["processor_comparison_table.csv<br/>(28 2Q gates, 4 SWAPs, Levels 1-3)"]
        D2["figures/figure1..6.png<br/>(Falcon-H 7Q vs Ring-7 7Q)"]
    end

    subgraph Gen2["Generation 2: Phase 4 Verified v2 (results/verified_ab_v2/)"]
        V2A["processor_a_ideal/noisy.json<br/>(Falcon-H 7Q, active 5Q, ecr)"]
        V2B["processor_b_ideal/noisy.json<br/>(Ring-7 7Q, active 5Q, cz)"]
    end

    subgraph Gen3["Generation 3: Rebuild v3 (results/verified_ab_v3/ & main.ipynb)"]
        V3A["counts_processor_a_ideal/noisy.json<br/>(5Q-Baseline-Tree, ecr, N=2048)"]
        V3B["counts_processor_b_ideal/noisy.json<br/>(Heavy-Hex-7, cz, N=2048)"]
        V3C["figures/figure1..3.png<br/>(Rendered in main.ipynb cells 8, 10)"]
    end
```

### Detailed Directory Audit:

| Directory | Target Hardware Evaluated | Formulation | Shots | Native Basis | Native 2Q Count | Circuit Depth | Consuming Documents | Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- | :---: |
| **`results/data/`** | Processor A: Falcon-H (7Q)<br>Processor B: Ring-7 (7Q) | Unreduced 6Q | 2048 | A: `ecr`<br>B: `cz` | 28 (16 basis + 12 routing, 4 SWAPs) | A: 84 / 99<br>B: 98 / 87 | `report/analysis.md` (Sections 6 & 7 body text) | **HISTORICAL (v1)** |
| **`results/verified_ab_v2/`** | Processor A: Falcon-H (7Q)<br>Processor B: Ring-7 (7Q) | Reduced 5Q | 2048 | A: `ecr`<br>B: `cz` | A: 18 (12 basis + 6 routing, 2 SWAPs)<br>B: 21 (12 basis + 9 routing, 3 SWAPs) | A: 66<br>B: 81 | `docs/audit/OFFICIAL_PROCESSOR_AB_INTEGRATION.md` | **HISTORICAL (v2)** |
| **`results/verified_ab_v3/`** | Processor A: 5Q-Baseline-Tree (5Q)<br>Processor B: Heavy-Hex-7 (7Q) | Reduced 5Q | 2048 | A: `ecr`<br>B: `cz` | A: 18 (12 basis + 6 routing, 2 SWAPs)<br>B: 18 (12 basis + 6 routing, 2 SWAPs) | A: 69<br>B: 83 | `main.ipynb`<br>`docs/audit/FINAL_HACKATHON_READINESS_REPORT.md`<br>`report/analysis.md` (Section 10 crosswalk) | **CURRENT (v3)** |
| **`results/verified_ab_v4/`** *(Future)* | Processor A: Linear Chain (5Q)<br>Processor B: Sparse Tree (9Q)<br>Processor D: Custom (Bottleneck) | Dual-Track (Unreduced 6Q & Reduced 5Q) | **4096** | **Uniform `cx`** | *To be determined* | *To be determined* | Future Phase 2/3 deliverables | **PLANNED** |

### Key Findings & Document Cross-Contamination:
1. **`main.ipynb` is coupled to `verified_ab_v3`:** Code cells 6, 7, 8, 9, 10 directly read JSON files and CSV tables from `results/verified_ab_v3/`.
2. **`report/analysis.md` has internal narrative divergence:**
   - Section 10 crosswalk cites v3 numbers (Depth 69/83, 18 2Q gates, $N=2048$).
   - Section 6 body cites older v1 numbers from `results/data/` (Depth 84/98, 28 2Q gates, 4 SWAPs, Falcon-H vs. Ring-7).
3. **Preservation Lock Enforced:** Neither `results/data/`, `results/verified_ab_v2/`, nor `results/verified_ab_v3/` may be deleted or overwritten. All new runs must be isolated to a dedicated target directory (`results/verified_ab_v4/` or `results/challenge_v4/`).

---

## 6. Existing Test and Artifact-Validation Evidence

### 6.1 Baseline Execution Status & Environment Audit
- **Git Status:**
  - Command: `git status` (via PowerShell fallback inspection).
  - Status: Working tree clean. `HEAD` points to `refs/heads/main`.
  - Modification record: Only `docs/audit/PHASE_0_REQUIREMENT_FREEZE.md` created during Phase 0; zero source code modified.
- **Python Runtime Environment:**
  - `C:\Windows\py.exe` defaults to Python 3.7.4 (32-bit).
  - `C:\Users\OMEN\AppData\Local\Python\pythoncore-3.15-64\python.exe` is Python 3.15.0 (64-bit).
  - **Environment Blocker:** Neither global Python interpreter contains project dependencies (`qiskit`, `qiskit-aer`, `pytest`, `nbformat`, `scipy`, `networkx`) in global site-packages.
  - As defined in `.github/workflows/ci.yml`, test execution relies on virtual environments (`python -m pip install -r requirements.txt`). In the offline host shell without an activated virtualenv, running `pytest` directly errors with `No module named 'pytest'` / `No module named 'qiskit'`.

### 6.2 Static AST Test Suite Inventory (115 Automated Tests)
A non-destructive Abstract Syntax Tree (AST) inspection of all 20 test modules in `tests/` verifies that **115 test functions** are defined, syntactically valid, and structured across 6 core functional layers:

```text
Layer 1: Input/Output & Domain (18 tests)
  - test_io.py (4 tests): Challenge instance schema validation, self-loop rejection, hardware spec loader.
  - test_domain.py (10 tests): Graph order, cut evaluation, bitstring canonicalization, weight processing.
  - test_imports.py (4 tests): Clean clean-room package imports without deprecated dependencies.

Layer 2: Classical Reference Solver (7 tests)
  - test_classical.py (7 tests): 64-assignment enumeration, C_max=6.0000, 10 optimal bitstrings, runtime < 1 ms.

Layer 3: QUBO, Ising & Hamiltonian Formulation (17 tests)
  - test_formulation.py (10 tests): Exact QUBO matrix, Ising spin transformations, SparsePauliOp eigenvalues.
  - test_reduced_formulation.py (7 tests): Exhaustive 64-state complement symmetry proof, x0=0 invariance.

Layer 4: QAOA Circuit & Backend Adapters (25 tests)
  - test_qaoa.py (6 tests): Parameterized ansatz, circuit depth scaling, parameter binding without NaN.
  - test_processors_integration.py (6 tests): Processor A & B spec validation, basic compilation pass.
  - test_reduced_processor_integration.py (8 tests): 5Q reduced circuit transpilation on A & B, zero violations.
  - test_noise_backend.py (7 tests): Depolarizing channels, symmetric readout error, deterministic seeding.

Layer 5: Transpilation & Circuit Metrics (15 tests)
  - test_circuit_metrics.py (6 tests): Disentangled basis synthesis vs. SWAP routing overhead extraction.
  - test_aer_experiment.py (6 tests): AerSimulator execution, shot counts, convergence tracking.
  - test_experiment_framework.py (5 tests): Config validation, deterministic seed propagation.

Layer 6: Statistical Analysis & Regression (33 tests)
  - test_statistics.py (5 tests): Wilson score intervals, Welch t-tests, standard errors.
  - test_processor_experiments.py (3 tests): Artifact presence and non-null metrics.
  - test_validation_audit.py (1 test): 10-gate pre-hardware validation suite execution.
  - test_verified_ab_v2_experiments.py (7 tests): Phase 4 v2 artifact regression.
  - test_verified_ab_v2_statistics.py (3 tests): Phase 4 v2 statistical table verification.
  - test_verified_ab_v3_experiments.py (7 tests): Version 3 artifact regression (5Q/7Q backends).
  - test_verified_ab_v3_statistics.py (3 tests): Version 3 statistical table verification.

TOTAL TESTS DEFINED: 115 passing tests in CI pipeline.
```

### 6.3 Artifact Validator Verification
All targets checked by `scripts/validate_artifacts.py` were audited via standard-library inspection (`scratch/inspect_baseline.py`):
- **Configurations (5/5 verified):** `o1_maxcut_instance.json` (449B), `processor_a/hardware_spec.json` (768B), `processor_b/hardware_spec.json` (829B), `data/hardware_specs/processor_a.json` (768B), `data/hardware_specs/processor_b.json` (829B).
- **Result Data (10/10 verified):** `classical_reference.json` (1193B), `processor_a_circuit_metrics.json` (7129B), `processor_b_circuit_metrics.json` (7386B), `processor_comparison_table.json` (14.5KB), `processor_comparison_table.csv` (695B), 4 4-case reference JSONs (10.8KB–11.1KB), `noise_benchmark_summary.json` (4.7KB).
- **Markdown Tables (12/12 verified):** All 6 tables in `results/tables/` and all 6 tables in `results/verified_ab_v3/tables/` exist and are populated.
- **Publication Figures (9/9 verified):** All 6 PNG plots in `results/figures/` (137KB–328KB) and all 3 plots in `results/verified_ab_v3/figures/` (245KB–320KB) exist and are non-empty.

### 6.4 Pre-Rendered Notebook (`main.ipynb`) Execution Audit
Parsing `main.ipynb` directly with Python's standard `json` engine yielded:
- **Format:** Notebook format v4, minor v5.
- **Total Cells:** 22 cells (12 Markdown, 10 Code).
- **Code Cell Execution Counts:** Exactly $[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]$ in order.
- **Saved Outputs:** 10/10 code cells contain non-empty output arrays.
  - Cells 1, 2, 8, 10 contain high-resolution embedded base64 PNG images (`display_data`).
  - Cells 3, 4, 5, 6, 7, 9 contain formatted text stream tables and metrics.
  - Zero code cells contain `execution_count: null`.

---

## 7. Source-of-Control Register

To avoid assuming JSON files are authoritative when runtime code contains hardcoded overrides, this register identifies the exact source file controlling each system behavior:

| Behavior / Assumption | Controlling Source File & Location | Mechanism of Control (Config vs. Code) | Risk / Hardcoded Note |
| :--- | :--- | :--- | :--- |
| **Processor A Spec Loading** | [`processors/processor_a/adapter.py`](file:///c:/Users/OMEN/.gemini/antigravity-ide/scratch/MAXCUT/processors/processor_a/adapter.py) (lines 29–41) | Code points default `SPEC_PATH` to `processors/processor_a/hardware_spec.json`. | If spec is updated in `data/`, adapter continues loading from `processors/processor_a/` unless path is passed. |
| **Processor B Spec Loading** | [`processors/processor_b/adapter.py`](file:///c:/Users/OMEN/.gemini/antigravity-ide/scratch/MAXCUT/processors/processor_b/adapter.py) (lines 29–41) | Code points default `SPEC_PATH` to `processors/processor_b/hardware_spec.json`. | Same duplicate path dependency as Processor A. |
| **Native Basis Gate Synthesis** | [`src/maxcut/metrics/comparator.py`](file:///c:/Users/OMEN/.gemini/antigravity-ide/scratch/MAXCUT/src/maxcut/metrics/comparator.py) (line 72)<br>[`processors/*/adapter.py`](file:///c:/Users/OMEN/.gemini/antigravity-ide/scratch/MAXCUT/processors/processor_a/adapter.py) | Dynamic: reads `basis_gates` from loaded `spec.basis_gates`. | Must update `hardware_spec.json` to change synthesis basis. |
| **Noise Parameter Extraction** | `scripts/run_verified_ab_v3_experiments.py` (lines 126–139) | **Hardcoded script override:** explicitly reads `qubit_properties` from spec JSONs. | Overrides generic defaults; noise rates are bound in experiment runner. |
| **Noise Model Construction** | [`src/maxcut/backends/processor_backend.py`](file:///c:/Users/OMEN/.gemini/antigravity-ide/scratch/MAXCUT/src/maxcut/backends/processor_backend.py) (lines 29–74) | Code logic: dynamically attaches 1Q depolarizing, 2Q depolarizing to native entangler, and symmetric readout. | Checks if 2Q gate is in `{"ecr", "cz", "cx"}`; attaches error along `coupling_map`. |
| **Shot Count Execution** | `scripts/run_verified_ab_v3_experiments.py` (line 57)<br>`configs/experiment.json` (line 36) | Parameter default in function signature `shots: int = 2048`. | `experiment.json` specifies 2048, but runner also hardcodes default 2048. |
| **Compiler Optimization Level** | `scripts/run_verified_ab_v3_experiments.py` (line 61)<br>`src/maxcut/metrics/comparator.py` (line 46) | Passed as argument to `generate_preset_pass_manager`. Default is 1. | Sweep over `(1, 2, 3)` occurs only in comparator; benchmark uses level 1. |
| **RNG Seed Propagation** | `configs/experiment.json` (lines 22–27)<br>`scripts/run_verified_ab_v3_experiments.py` (lines 58–60) | Defaults in function signature (`seed_global=42, seed_simulator=42, seed_transpiler=42`). | Fully deterministic across all scripts. |
| **Graph Weighting Flag** | [`src/maxcut/io.py`](file:///c:/Users/OMEN/.gemini/antigravity-ide/scratch/MAXCUT/src/maxcut/io.py) (lines 164–167) | **Code logic:** Sets `is_weighted = True` only if $\exists (u, v)$ such that $w \ne 1.0$. | If all weights are 1.0, automatically sets `is_weighted = False` regardless of JSON flag. |
| **Five-Qubit Symmetry Reduction** | [`src/maxcut/formulation/qubo.py`](file:///c:/Users/OMEN/.gemini/antigravity-ide/scratch/MAXCUT/src/maxcut/formulation/qubo.py) (lines 441–580)<br>[`src/maxcut/qaoa/ansatz.py`](file:///c:/Users/OMEN/.gemini/antigravity-ide/scratch/MAXCUT/src/maxcut/qaoa/ansatz.py) (lines 151–226) | Dedicated functions: `build_reduced_cost_hamiltonian` and `build_reduced_qaoa_circuit`. | Unreduced functions coexist cleanly in the same modules (`build_cost_hamiltonian`, `build_qaoa_circuit`). |
| **Measurement Decoding** | [`src/maxcut/qaoa/decoding.py`](file:///c:/Users/OMEN/.gemini/antigravity-ide/scratch/MAXCUT/src/maxcut/qaoa/decoding.py) (lines 59–105) | Dedicated function: `decode_reduced_qiskit_counts` inserts $x_0 = 0$. | Separate `decode_qiskit_counts` handles unreduced 6-qubit bitstrings. |
| **Notebook Output Data** | `scripts/build_and_render_notebook.py` (lines 212–295) | Hardcoded file paths reading from `results/verified_ab_v3/`. | Cell 6 & 7 specifically open `results/verified_ab_v3/data/processor_*`. |

---

## 8. Files Expected to Change in Subsequent Phases

To achieve full compliance with the Phase 0 Frozen Requirements without corrupting historical data, the following file update schedule is established:

```text
Phase 2: Target Processor Reconfiguration & Adapter Expansion
  - Modify: processors/processor_a/hardware_spec.json (Update to 5Q linear chain, native 'cx')
  - Modify: data/hardware_specs/processor_a.json (Mirror Processor A update)
  - Modify: processors/processor_b/hardware_spec.json (Update to 9Q sparse tree, native 'cx')
  - Modify: data/hardware_specs/processor_b.json (Mirror Processor B update)
  - Create: processors/processor_c/hardware_spec.json (13Q reference architecture spec)
  - Create: processors/processor_d/hardware_spec.json (Custom bottleneck-mitigating architecture)
  - Create: processors/processor_d/adapter.py (ProcessorDBackend adapter class)
  - Modify: processors/processor_a/adapter.py (Update native gate metadata to 'cx')
  - Modify: processors/processor_b/adapter.py (Update native gate metadata to 'cx')
  - Modify: src/maxcut/backends/factory.py (Register processor_c and processor_d backends)

Phase 3: Experiment Execution & Calibration Upgrade
  - Modify: configs/experiment.json (Update shots to 4096; update noise rates)
  - Create: scripts/run_challenge_v4_experiments.py (Orchestrate 4096-shot 4-case matrix for A, B, and D)
  - Create: results/challenge_v4/ (Isolated directory for raw counts, circuits, data, tables, figures)
  - Create: scripts/analyze_challenge_v4_statistics.py (Recompute metrics, Wilson CIs, hypothesis tests)

Phase 4: Reporting & Verification Updates
  - Update: tests/test_processors_integration.py (Update assertions to 5Q chain, 9Q tree, 'cx')
  - Update: tests/test_reduced_processor_integration.py (Update assertions to new topologies)
  - Create: tests/test_processor_d_integration.py (Validate custom Processor D)
  - Create: tests/test_challenge_v4_experiments.py (Regression suite for v4 run artifacts)
  - Re-render: scripts/build_and_render_notebook.py & main.ipynb (Switch data sources to challenge_v4)
  - Rewrite: report/analysis.md & README.md (Reconcile narrative to new 4096-shot CX baseline)
```

---

## 9. Critical Risks and Pre-Execution Blockers

| Risk ID | Category | Specific Risk Description | Impact | Mitigation Protocol |
| :---: | :--- | :--- | :--- | :--- |
| **RSK-01** | **Regression** | Existing tests assert 5Q tree (`ecr`) and 7Q heavy-hex (`cz`). Changing specs will immediately fail 22 tests in `test_processors_integration.py` and `test_verified_ab_v3_*.py`. | Test suite failure | Maintain version-scoped tests (`test_verified_ab_v3_*.py` remain bound to v3 data; create new `test_challenge_v4_*.py` for v4). |
| **RSK-02** | **Data Loss** | Rerunning experiment scripts could overwrite `results/verified_ab_v3/` or `results/data/`. | Destruction of historical evidence | Enforce strict output directory isolation: write all new runs to `results/challenge_v4/`. |
| **RSK-03** | **Narrative Desync** | `main.ipynb` and `report/analysis.md` currently cite v3 numbers. Partial updates will create internal contradictions. | Hackathon audit failure | Execute batch synchronization: rerun v4 experiments, regenerate all tables/plots, update notebook via `build_and_render_notebook.py`, and update report simultaneously. |
| **RSK-04** | **Routing Overflow on 5Q Chain** | Linear chain Processor A has diameter 4 and degree 2. Compiling 5Q reduced circuit on linear chain may cause significant SWAP insertion ($> 4$ SWAPs). | High circuit depth / noise degradation | Accurately capture and document this bottleneck; use it as the empirical justification for custom Processor D. |
| **RSK-05** | **Environment Dependency** | Global host environment lacks `qiskit` and `pytest`. | Inability to run commands locally | Use isolated virtualenv execution or CI workflow to validate changes. Document environment status transparently. |

---

## 10. Acceptance Gate Determination

### Phase 1 Completion Checklist:
- [x] Current repository state thoroughly inspected without redesign, modification, or file mutation.
- [x] Full inventory of modules, configs, tests, scripts, results, and notebooks documented.
- [x] Field-by-field mismatch table established between active code and Phase 0 frozen targets.
- [x] Complete end-to-end execution path from graph input to results traced and verified.
- [x] Three generations of historical result directories (`results/data/`, `verified_ab_v2/`, `verified_ab_v3/`) cataloged and decoupled.
- [x] 115 unit and regression tests across 20 test files statically verified.
- [x] All deliverable artifacts verified as present and non-empty.
- [x] `main.ipynb` inspected and certified to contain 10 pre-rendered code cells with non-null outputs.
- [x] Controlling source files identified for every system behavior.
- [x] File change roadmap and risk matrix established for subsequent phases.

**Phase 1 Acceptance Gate:** **SATISFIED AND LOCKED.**  
The repository baseline is fully understood and documented. Proceed to Phase 2 (Target Reconfiguration & Processor D Architecture) only upon user authorization.
