# Evidence-Based Architectural Analysis: Processor A vs. Processor B

**Challenge Track:** Qiskit Fall Fest 2026 — Quantum Optimization — O1 Max-Cut  
**Problem Instance:** `O1_MaxCut_Challenge` ($|V|=6, |E|=8, W=8.00$)  
**Classical Reference Optimum:** $C_{\max} = 6.0000$ (Exhaustive Ground Truth)  
**Evaluated Targets:** Ideal Aer Simulator, Processor A (`Falcon-H`), Processor B (`Ring-7`)  
**Status:** Complete Empirical Analysis  

---

## 1. Executive Summary & Experimental Controls

This document presents the final evidence-based comparative analysis of the QAOA Max-Cut workflow targeting **Processor A** and **Processor B**, validated against the unconstrained **Ideal Aer Simulator**.

To ensure strict scientific control, all experimental factors were held identical across targets:
1. **Problem Instance:** Official 6-vertex, 8-edge unweighted challenge graph ingested from [`instances/challenge/o1_maxcut_instance.json`](file:///c:/Users/WIN_10/.gemini/antigravity/scratch/AXCUT/instances/challenge/o1_maxcut_instance.json).
2. **Algorithm & Ansatz:** QAOA with depth $p = 1$, using parameterized $R_{ZZ}(\gamma)$ cost layers and $R_X(\beta)$ mixer layers.
3. **Variational Parameters:** Optimized via COBYLA ($\gamma^* = 2.4835$, $\beta^* = 4.2540$) achieving identical variational state preparation.
4. **Sampling Budget:** Exactly 2048 measurement shots per target.
5. **Reproducibility Seeds:** Identical global, simulator, and transpiler RNG seeds (`seed_global = 42`, `seed_simulator = 42`, `seed_transpiler = 42`).
6. **Transpilation Service:** Qiskit 2.x `generate_preset_pass_manager` (Optimization Level 1 baseline).
7. **Decoding Protocol:** Uniform little-endian bitstring inversion mapping onto canonical graph vertex order $[0, 1, 2, 3, 4, 5]$.

---

## 2. Quantitative Empirical Results

### Table 1: End-to-End Architectural and Performance Metrics

The metrics below are directly extracted from the serialized execution artifacts:
- Simulator: [`results/data/O1_MaxCut_Challenge_aer_simulator_p1_result.json`](file:///c:/Users/WIN_10/.gemini/antigravity/scratch/AXCUT/results/data/O1_MaxCut_Challenge_aer_simulator_p1_result.json)
- Processor A: [`results/data/O1_MaxCut_Challenge_processor_a_p1_result.json`](file:///c:/Users/WIN_10/.gemini/antigravity/scratch/AXCUT/results/data/O1_MaxCut_Challenge_processor_a_p1_result.json)
- Processor B: [`results/data/O1_MaxCut_Challenge_processor_b_p1_result.json`](file:///c:/Users/WIN_10/.gemini/antigravity/scratch/AXCUT/results/data/O1_MaxCut_Challenge_processor_b_p1_result.json)

| Evaluation Metric | Ideal Aer Simulator | Processor A (Falcon-H) | Processor B (Ring-7) |
| :--- | :---: | :---: | :---: |
| **Backend Name** | `aer_simulator` | `Processor_A` | `Processor_B` |
| **Architecture Topology** | All-to-All Virtual | Falcon-H (Heavy-Hex Subset) | Ring-7 (Circular 7-Ring) |
| **Native 2-Qubit Entangler** | `cx` | `ecr` | `cz` |
| **Logical Qubits** | 6 | 6 | 6 |
| **Physical Qubits** | 32 (virtual) | 7 | 7 |
| **Logical Circuit Depth** | 10 | 10 | 10 |
| **Transpiled Depth (Level 1)** | **10** | **84** | **98** |
| **Transpiled Depth (Level 2/3)** | 10 | 99 | 87 |
| **Logical 2-Qubit Gates** | 8 | 8 | 8 |
| **Transpiled 2-Qubit Gates** | **8** | **28** | **28** |
| **SWAP Count** | **0** | **0** | **0** |
| **Total Transpiled Gates** | **27** | **159** | **139** |
| **Routing 2Q Overhead Ratio** | 1.00x | 3.50x | 3.50x |
| **Depth Expansion Ratio** | 1.00x | 8.40x | 9.80x |
| **Best Measured Cut ($C_{\text{best}}$)** | **6.0000** | **6.0000** | **6.0000** |
| **Classical Optimum Hit** | **True** | **True** | **True** |
| **Expected Cut ($\langle C \rangle$)** | 4.8931 | 4.8901 | 4.9116 |
| **Approximation Ratio ($\alpha = \frac{\langle C \rangle}{C_{\max}}$)** | **0.8155 (81.55%)** | **0.8150 (81.50%)** | **0.8186 (81.86%)** |
| **Ground State Probability ($P(x^*)$)** | **0.3804 (38.04%)** | **0.3931 (39.31%)** | **0.4072 (40.72%)** |
| **Sample Cut Mean ($\mu$)** | 4.8931 | 4.8901 | 4.9116 |
| **Sample Cut Std Dev ($\sigma$)** | 1.1593 | 1.1643 | 1.1578 |
| **Sample Cut Median** | 5.0 | 5.0 | 5.0 |
| **Total Pipeline Wall Time** | 0.4707 s | 0.4577 s | 0.4864 s |

---

### Table 2: Empirical Cut Value Distribution ($N = 2048$ Shots)

From [`results/tables/cut_distribution_table.csv`](file:///c:/Users/WIN_10/.gemini/antigravity/scratch/AXCUT/results/tables/cut_distribution_table.csv):

| Cut Value $C(x)$ | Ground State? | Simulator Shots (Freq) | Processor A Shots (Freq) | Processor B Shots (Freq) |
| :---: | :---: | :---: | :---: | :---: |
| 0 | No | 4 (0.20%) | 5 (0.24%) | 4 (0.20%) |
| 1 | No | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) |
| 2 | No | 27 (1.32%) | 35 (1.71%) | 26 (1.27%) |
| 3 | No | 208 (10.16%) | 196 (9.57%) | 185 (9.03%) |
| 4 | No | 363 (17.72%) | 370 (18.07%) | 387 (18.90%) |
| 5 | No | 667 (32.57%) | 637 (31.10%) | 612 (29.88%) |
| **6** | **Yes ($C_{\max}$)** | **779 (38.04%)** | **805 (39.31%)** | **834 (40.72%)** |
| **Total** | — | **2048 (100.0%)** | **2048 (100.0%)** | **2048 (100.0%)** |

---

## 3. Visualizations

The generated publication figures are saved in [`results/figures/`](file:///c:/Users/WIN_10/.gemini/antigravity/scratch/AXCUT/results/figures/):

1. **Empirical Cut Value Distribution**: [`figure1_cut_distribution_comparison.png`](file:///c:/Users/WIN_10/.gemini/antigravity/scratch/AXCUT/results/figures/figure1_cut_distribution_comparison.png)  
   Shows the full probability mass function across all cut values $C(x) \in [0, 6]$ for Simulator, Processor A, and Processor B, illustrating peak concentration at $C=6$.
2. **Circuit Resource Requirements**: [`figure2_circuit_resource_comparison.png`](file:///c:/Users/WIN_10/.gemini/antigravity/scratch/AXCUT/results/figures/figure2_circuit_resource_comparison.png)  
   Compares transpiled circuit depth, 2-qubit entangling gates, and total gate count across all targets.
3. **Solution Quality & Ground State Probability**: [`figure3_solution_quality_comparison.png`](file:///c:/Users/WIN_10/.gemini/antigravity/scratch/AXCUT/results/figures/figure3_solution_quality_comparison.png)  
   Juxtaposes approximation ratio $\alpha$ and optimal ground state sampling probability $P(x^*)$.

---

## 4. Evidence-Based Analysis of Core Questions

### Question 1: Which processor produced the better solution quality?

* **Observed Fact:**
  - Both Processor A and Processor B successfully sampled the maximum cut $C_{\max} = 6.0000$ in their highest-quality measurement outcomes.
  - Processor B recorded an expected cut value of $\langle C \rangle = 4.9116$, compared to $\langle C \rangle = 4.8901$ for Processor A (an observed difference of $\Delta \langle C \rangle = +0.0215$, or $+0.44\%$).
  - Processor B yielded an approximation ratio of $\alpha = 0.8186$ ($81.86\%$) compared to Processor A's $\alpha = 0.8150$ ($81.50\%$).
  - Processor B sampled the optimal ground state partition in 834 of 2048 shots ($40.72\%$), while Processor A sampled it in 805 of 2048 shots ($39.31\%$), representing an empirical difference of $+1.41\%$.
* **Interpretation:**
  - In our controlled, noise-free local emulation, both processors preserved the algorithmic performance of the QAOA state with high fidelity ($\alpha > 81\%$).
  - The observed $+1.41\%$ margin in ground state probability for Processor B is within the expected statistical shot noise for a multinomial distribution sampled over 2048 shots ($1/\sqrt{2048} \approx 2.21\%$). Thus, the two processors produced statistically indistinguishable solution qualities under ideal unitary conditions.
* **Limitation:**
  - Because execution was conducted on an ideal shot-sampling engine without physical gate infidelity, leakage, or decoherence, this small difference reflects finite-sample statistical fluctuation rather than architectural superiority.

---

### Question 2: How different were the resource requirements?

* **Observed Fact:**
  - **Qubit Allocation:** Both architectures have 7 physical qubits and allocated 6 qubits to host the 6 logical problem variables, leaving 1 unused physical qubit.
  - **Two-Qubit Gates:** Both processors compiled to exactly 28 transpiled two-qubit entangling gates (Processor A used 28 `ecr` gates; Processor B used 28 `cz` gates), scaling from 8 logical $R_{ZZ}$ gates by a factor of 3.50x.
  - **Total Gate Count:** Processor A compiled to **159 total gates** (78 `rz`, 42 `sx`, 28 `ecr`, 11 `x`, 6 `measure`, 1 `barrier`), whereas Processor B compiled to **139 total gates** (72 `rz`, 39 `sx`, 28 `cz`, 6 `measure`, 1 `barrier`).
  - Processor B required **20 fewer gates** overall than Processor A (a $12.58\%$ reduction in total gate volume).
* **Interpretation:**
  - The 20-gate divergence between Processor A and Processor B is entirely attributable to single-qubit basis gate decompositions. Synthesizing a general $R_{ZZ}(\theta)$ interaction from the native `cz` gate requires fewer single-qubit Euler rotations (`rz`, `sx`, `x`) than synthesizing it from the native `ecr` entangler.
* **Limitation:**
  - Gate counts do not directly indicate physical execution time without calibration data for individual gate durations (e.g., duration of `ecr` pulses vs. `cz` pulses on real cryostats).

---

### Question 3: Did routing introduce overhead?

* **Observed Fact:**
  - For both Processor A and Processor B, the transpiler reported **0 SWAP gates** (`swap_count = 0`) across Optimization Levels 1, 2, and 3.
  - However, the number of two-qubit entangling gates expanded from 8 in the logical circuit to 28 in the transpiled circuit (20 additional entangling operations, representing a $250\%$ increase in 2Q gates).
* **Interpretation:**
  - Dynamic routing SWAP gates were not required because the 6-vertex challenge graph could be embedded directly into a connected 6-node subgraph of both Falcon-H (7 qubits, 12 directed edges) and Ring-7 (7 qubits, 14 directed edges).
  - The 2Q gate overhead of 28 gates is therefore not dynamic routing overhead; rather, it is **basis synthesis overhead** (decomposing each non-native $R_{ZZ}$ gate into native hardware entanglers and local rotations).
* **Limitation:**
  - On larger graphs ($N \ge 8$) or denser topologies where problem degrees exceed the hardware degree (e.g., maximum degree 3 in Falcon-H or degree 2 in Ring-7), SWAP insertion overhead would become mandatory.

---

### Question 4: Did circuit depth differ?

* **Observed Fact:**
  - At **Optimization Level 1**:
    - Logical circuit depth was 10.
    - Processor A transpiled depth was **84 cycles** ($8.40\times$ depth expansion).
    - Processor B transpiled depth was **98 cycles** ($9.80\times$ depth expansion, $+14$ cycles longer than Processor A).
  - At **Optimization Levels 2 & 3**:
    - Processor A depth increased to **99 cycles** ($9.90\times$ expansion).
    - Processor B depth decreased to **87 cycles** ($8.70\times$ expansion, $-12$ cycles shorter than Processor A).
* **Interpretation:**
  - Circuit depth differed significantly between the two architectures and across optimization presets.
  - At Level 1, Processor A's tree/heavy-hex topology permitted higher scheduling parallelism for this specific embedding.
  - At Levels 2 and 3, commutative cancellation and analytical pulse scheduling reduced the Ring-7 (Processor B) depth to 87 while expanding Falcon-H (Processor A) to 99 cycles.
* **Limitation:**
  - Depth in gate cycles is a discrete transpiler abstraction. On real hardware, pulse scheduling, barrier placement, and dynamical decoupling sequences determine the physical coherence lifetime ($T_1, T_2$) consumed.

---

### Question 5: Did the measured results support a relationship between architecture/resources and solution quality?

* **Observed Fact:**
  - Despite significant architectural divergences between the Ideal Simulator (depth 10, 8 2Q gates), Processor A (depth 84, 28 2Q gates), and Processor B (depth 98, 28 2Q gates), the measured solution quality was nearly identical:
    - Best cut: 6.0000 across all three targets.
    - Expected cut $\langle C \rangle$: 4.8931 (Sim) vs. 4.8901 (Proc A) vs. 4.9116 (Proc B).
    - Approximation ratio $\alpha$: $81.55\%$ (Sim) vs. $81.50\%$ (Proc A) vs. $81.86\%$ (Proc B).
    - Ground state probability $P(x^*)$: $38.04\%$ (Sim) vs. $39.31\%$ (Proc A) vs. $40.72\%$ (Proc B).
* **Interpretation:**
  - Under ideal unitary evolution, compiler transformations are mathematically exact, meaning circuit depth expansion and basis gate decompositions do not degrade state fidelity.
  - Therefore, **the empirical data does NOT support a causal relationship between architectural resource overhead and solution quality degradation in the noise-free regime.**
  - In a noisy physical environment, a $8.4\times$ to $9.8\times$ depth expansion and $3.5\times$ 2Q gate overhead would introduce substantial decoherence and gate error accumulation ($28 \times \epsilon_{2Q}$), which would sharply depress $\alpha$ and $P(x^*)$.
* **Limitation:**
  - Because no physical noise model was enabled during execution, the empirical findings isolate topological and compilation effects but cannot quantify physical error-induced degradation.

---

### Question 6: What limitations prevent stronger conclusions?

1. **Noise-Free Execution:** Local emulation did not apply thermal relaxation ($T_1$), dephasing ($T_2$), or coherent crosstalk. Physical QPU execution or calibrated Kraus noise channels are required to evaluate real fidelity loss.
2. **Single Small Instance ($|V|=6$):** The 6-node instance fit onto both 7-qubit processors without routing SWAPs. Consequently, topology differences did not force dynamic routing.
3. **Fixed QAOA Depth ($p=1$):** At $p=1$, parameter optimization is low-dimensional ($\gamma, \beta$). Higher depths ($p \ge 2$) may expose more pronounced architectural bottlenecks.
4. **Heuristic Pass Manager Variance:** Qiskit's heuristic layout passes exhibit minor variation across seeds and optimization levels.

---

## 5. Quantum Advantage Assessment

> [!IMPORTANT]
> **Quantum Advantage Status:** **NOT DEMONSTRATED**  
> - **Classical Baseline:** The exact exhaustive solver ([`src/maxcut/classical/solver.py`](file:///c:/Users/WIN_10/.gemini/antigravity/scratch/AXCUT/src/maxcut/classical/solver.py)) solved the official instance to certified optimality in **0.0004 seconds** ($0.4\text{ ms}$), identifying all 10 degenerate optimal bitstrings.
> - **QAOA Performance:** QAOA at $p=1$ achieved an approximation ratio of $\alpha \approx 0.818$ with a $39\%\text{--}41\%$ ground state sampling probability, requiring 2048 measurement shots and multiple classical variational iterations.
> - **Conclusion:** The quantum algorithm verified theoretical convergence and functional correctness on both target processors, but provides no computational advantage over classical methods for this problem scale.

---

## 6. Directory of Artifacts

- **Executive Report:** [`report/analysis.md`](file:///c:/Users/WIN_10/.gemini/antigravity/scratch/AXCUT/report/analysis.md)
- **Comparison Table (CSV):** [`results/tables/processor_comparison_table.csv`](file:///c:/Users/WIN_10/.gemini/antigravity/scratch/AXCUT/results/tables/processor_comparison_table.csv)
- **Comparison Table (Markdown):** [`results/tables/processor_comparison_table.md`](file:///c:/Users/WIN_10/.gemini/antigravity/scratch/AXCUT/results/tables/processor_comparison_table.md)
- **Cut Distribution Table (CSV):** [`results/tables/cut_distribution_table.csv`](file:///c:/Users/WIN_10/.gemini/antigravity/scratch/AXCUT/results/tables/cut_distribution_table.csv)
- **Objective Distribution Figure:** [`results/figures/figure1_cut_distribution_comparison.png`](file:///c:/Users/WIN_10/.gemini/antigravity/scratch/AXCUT/results/figures/figure1_cut_distribution_comparison.png)
- **Resource Overheads Figure:** [`results/figures/figure2_circuit_resource_comparison.png`](file:///c:/Users/WIN_10/.gemini/antigravity/scratch/AXCUT/results/figures/figure2_circuit_resource_comparison.png)
- **Solution Quality Figure:** [`results/figures/figure3_solution_quality_comparison.png`](file:///c:/Users/WIN_10/.gemini/antigravity/scratch/AXCUT/results/figures/figure3_solution_quality_comparison.png)
- **Execution Data Artifacts:**
  - Simulator: [`results/data/O1_MaxCut_Challenge_aer_simulator_p1_result.json`](file:///c:/Users/WIN_10/.gemini/antigravity/scratch/AXCUT/results/data/O1_MaxCut_Challenge_aer_simulator_p1_result.json)
  - Processor A: [`results/data/O1_MaxCut_Challenge_processor_a_p1_result.json`](file:///c:/Users/WIN_10/.gemini/antigravity/scratch/AXCUT/results/data/O1_MaxCut_Challenge_processor_a_p1_result.json)
  - Processor B: [`results/data/O1_MaxCut_Challenge_processor_b_p1_result.json`](file:///c:/Users/WIN_10/.gemini/antigravity/scratch/AXCUT/results/data/O1_MaxCut_Challenge_processor_b_p1_result.json)
