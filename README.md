# Qiskit Fall Fest 2026 — Quantum Optimization (O1 Max-Cut)
## Architectural Benchmarking and Comparative QAOA Analysis: Processor A vs. Processor B

**Track Selection:** Quantum Optimization — **Problem Code: O1**  
**Selected Problem:** Maximum Cut (Max-Cut)  
**Algorithm:** Quantum Approximate Optimization Algorithm (QAOA) vs. Classical Ground Truth  
**Target Architectures:** Processor A (`Falcon-H`), Processor B (`Ring-7`), Ideal Simulator (`aer_simulator`)  
**Official Repository:** [https://github.com/karthikeyakolli/MAXCUT](https://github.com/karthikeyakolli/MAXCUT)  

---

## 1. Problem Statement & Mathematical Formulation

The **Maximum Cut (Max-Cut)** problem is a fundamental NP-hard combinatorial optimization challenge. Given an undirected graph $G = (V, E)$ with edge weights $w_{uv}$, the objective is to partition the vertices $V$ into two complementary subsets $S$ and $\bar{S}$ such that the sum of the weights of edges with endpoints in distinct subsets is maximized:

$$C(x) = \sum_{(u, v) \in E} w_{uv} (x_u \oplus x_v) = \sum_{(u, v) \in E} w_{uv} [x_u(1 - x_v) + x_v(1 - x_u)]$$

where binary variables $x_u \in \{0, 1\}$ assign vertex $u$ to partition $S$ ($x_u = 0$) or $\bar{S}$ ($x_u = 1$).

### Spin Mapping & Ising Cost Hamiltonian
By mapping binary variables $x_u$ to Pauli spin operators $s_u = 1 - 2x_u \in \{+1, -1\}$:
$$x_u \oplus x_v = \frac{I - Z_u Z_v}{2}$$

The Max-Cut problem is cast as finding the ground state of the Ising Cost Hamiltonian:
$$H_C = \sum_{(u, v) \in E} \frac{w_{uv}}{2} (I - Z_u Z_v)$$

Minimizing energy $E = \langle H_C \rangle$ directly maximizes the cut value $C = -E + \text{offset}$.

---

## 2. Project Objective

The goal of this project is to construct a rigorous, fully reproducible, and scientifically grounded quantum optimization solution for the **O1 Max-Cut** problem instance provided by the Qiskit Fall Fest 2026 organizers. 

The implementation:
1. Ingests and validates the official Challenge Kit instance without synthetic substitution.
2. Certifies an exact classical reference baseline ($C_{\max} = 6.0000$) via exhaustive search.
3. Formulates QUBO and Ising representations using modern Qiskit 2.x `SparsePauliOp` primitives.
4. Synthesizes a parameterized QAOA ansatz ($p = 1$) optimized variationally with COBYLA.
5. Transpiles and executes the identical logical circuit on **Processor A** (`Falcon-H` topology, native `ecr`) and **Processor B** (`Ring-7` topology, native `cz`) using Qiskit 2.x preset pass managers.
6. Conducts an evidence-based architectural comparison evaluating circuit depth, 2-qubit gate overhead, SWAP routing costs, approximation ratio ($\alpha = \langle C \rangle / C_{\max}$), and ground-state success probability $P(x^*)$.

---

## 3. Challenge Kit Dependencies & Instance Verification

The benchmark strictly evaluates the official organizer instance:
- **Location:** [`instances/challenge/o1_maxcut_instance.json`](instances/challenge/o1_maxcut_instance.json)
- **Parameters:** $|V| = 6$ vertices, $|E| = 8$ edges, unweighted ($W = 8.00$)
- **Classical Ground Truth:** $C_{\max} = 6.0000$ (certified in [`results/data/classical_reference.json`](results/data/classical_reference.json))
- **Processor A Definition:** [`processors/processor_a/hardware_spec.json`](processors/processor_a/hardware_spec.json) (7 physical qubits, Falcon-H heavy-hex subgraph, native basis `[rz, sx, x, ecr]`)
- **Processor B Definition:** [`processors/processor_b/hardware_spec.json`](processors/processor_b/hardware_spec.json) (7 physical qubits, Ring-7 circular ring, native basis `[rz, sx, x, cz]`)

---

## 4. Layered System Architecture

The project is structured into 10 decoupled, test-driven architectural layers:

```text
AXCUT/
├── src/maxcut/
│   ├── io.py                   # Layer 1: Challenge Kit ingestion & schema validation
│   ├── domain/                 # Layer 2: MaxCutGraph domain models & cut evaluation
│   ├── classical/              # Layer 3: Exhaustive reference solver (ground truth C_max)
│   ├── formulation/            # Layer 4: QUBO, Ising, and SparsePauliOp builder
│   ├── qaoa/                   # Layer 5: QAOA circuit ansatz & COBYLA parameter optimizer
│   ├── backends/               # Layer 6: Backend adapters & pass managers
│   ├── experiments/            # Layer 7: Reproducible experiment runner & schema
│   ├── metrics/                # Layer 8: Circuit resource metrics & processor comparator
│   └── visualization/          # Layer 9: Publication plotting & graph partition drawing
├── processors/                 # Official hardware adapters (Processor A & B)
├── notebooks/main.ipynb        # Layer 10: Complete narrative technical presentation
├── report/analysis.md          # Evidence-based architectural comparative report
├── results/                    # Serialized JSON data, CSV/Markdown tables, PNG figures
└── tests/                      # Automated pytest validation suite (56 tests)
```

---

## 5. Key Empirical Results

All metrics below are derived from actual compiled circuits and executions ($N = 2048$ shots, `seed_transpiler = 42`, Optimization Level 1):

| Metric | Ideal Aer Simulator | Processor A (`Falcon-H`) | Processor B (`Ring-7`) |
| :--- | :---: | :---: | :---: |
| **Native 2-Qubit Basis** | `cx` | `ecr` | `cz` |
| **Logical Qubits** | 6 | 6 | 6 |
| **Physical Qubits** | 32 (virtual) | 7 | 7 |
| **Logical Circuit Depth** | 10 | 10 | 10 |
| **Transpiled Circuit Depth** | **10** | **84** | **98** |
| **Logical 2-Qubit Gates** | 8 | 8 | 8 |
| **Transpiled 2-Qubit Gates** | **8** | **28** | **28** |
| **SWAP Count** | **0** | **0** | **0** |
| **Total Transpiled Gates** | **27** | **159** | **139** |
| **Best Measured Cut ($C_{\text{best}}$)** | **6.0000** | **6.0000** | **6.0000** |
| **Classical Optimum Hit** | **True** | **True** | **True** |
| **Expected Cut ($\langle C \rangle$)** | 4.8931 | 4.8901 | 4.9116 |
| **Approximation Ratio ($\alpha$)** | **81.55%** | **81.50%** | **81.86%** |
| **Ground State Probability $P(x^*)$** | **38.04%** | **39.31%** | **40.72%** |

### Summary of Architectural Insights:
1. **Solution Quality:** Both processors sampled the maximum cut $C_{\max} = 6.0000$. Expected cuts and approximation ratios were statistically indistinguishable ($\alpha \approx 81.50\%\text{--}81.86\%$, within multinomial shot noise $1/\sqrt{2048} \approx 2.21\%$).
2. **Resource Trade-off:** Processor B achieved a $12.58\%$ reduction in total gate count (139 vs. 159 gates) because synthesizing $R_{ZZ}$ interactions from native `cz` requires fewer single-qubit Euler rotations than from native `ecr`.
3. **Routing Overheads:** Neither processor required dynamic SWAP insertions (`swap_count = 0`) because the 6-vertex graph embedded isomorphically into connected 6-qubit subgraphs of both chips. The expansion from 8 to 28 two-qubit gates represents **basis decomposition overhead** rather than routing overhead.

---

## 6. Quantum Advantage Disclosure

> [!IMPORTANT]
> **Quantum Advantage Status:** **NOT DEMONSTRATED**  
> The classical exhaustive reference solver computed the exact certified optimum ($C_{\max} = 6.0000$, finding all 10 degenerate optimal assignments) in **0.0004 seconds** ($0.4\text{ ms}$). QAOA ($p=1$) verified functional quantum convergence across both target processors ($\alpha \approx 0.818$), but provides no computational speedup or solution superiority over classical methods at this problem scale.

---

## 7. Setup & Execution Instructions

### Prerequisites
- Python 3.10+ (tested on Python 3.14.6)
- Git

### Installation
```bash
# Clone the repository
git clone https://github.com/karthikeyakolli/MAXCUT.git
cd MAXCUT

# Create and activate virtual environment
python -m venv .venv

# Windows PowerShell:
.\.venv\Scripts\Activate.ps1

# Linux / macOS:
source .venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
```

### Reproducing Experiments & Validation
```bash
# 1. Run full test suite (56 unit and integration tests)
pytest -q

# 2. Run the classical exact solver
python scripts/run_classical_reference.py

# 3. Execute QAOA on Simulator, Processor A, and Processor B
python scripts/run_processor_experiments.py

# 4. Generate all comparison tables, statistics, and figures
python scripts/generate_analysis_artifacts.py

# 5. Open and run the complete interactive narrative notebook
jupyter notebook main.ipynb
```

---

## 8. Reproducibility & AI Assistance Disclosure

- **Software Stack:** Python 3.14.6, Qiskit 2.5.2, Qiskit-Aer 0.17.2, NetworkX 3.7, Matplotlib 3.11.2, Pandas 3.0.6.
- **Random Seeds:** Centralized RNG configuration (`seed_global = 42`, `seed_simulator = 42`, `seed_transpiler = 42`).
- **AI Assistance Disclosure:** In compliance with official Qiskit Fall Fest guidelines, generative AI (Google DeepMind Antigravity) was utilized as an engineering pair-programming assistant for code refactoring, test generation, and documentation drafting. All scientific formulations, problem definitions, mathematical transformations, data analyses, and conclusions were verified and validated against the official Challenge Kit.
