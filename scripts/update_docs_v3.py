"""Script to update README.md, report/analysis.md, CHALLENGE_KIT.md, and audit docs to v3."""
from pathlib import Path

def update_readme():
    readme_path = Path("README.md")
    text = readme_path.read_text(encoding="utf-8")
    
    # Update Section 51
    old_p51 = "The official Processor A hardware definition provides a **5-qubit** baseline topology (`[0, 1, 2, 3, 5]`)."
    new_p51 = "The official Processor A hardware definition provides a **5-qubit** baseline topology (`[0, 1, 2, 3, 4]`)."
    if old_p51 in text:
        text = text.replace(old_p51, new_p51)

    # Section 6 to 9 replacement
    sec6_header = "## 6. Official Processor A Definition, Compilation & Results"
    sec10_header = "## 10. Findings, Limitations & Conclusion"
    
    if sec6_header in text and sec10_header in text:
        idx6 = text.index(sec6_header)
        idx10 = text.index(sec10_header)
        
        new_sec6_to_9 = """## 6. Processor A Definition, Compilation & Results (v3 Corrected)

> [!NOTE]
> **Provisional Local Configuration:** Configured as a genuine 5-physical-qubit processor (`5Q-Baseline-Tree`) with topology `[0, 1, 2, 3, 4]`, labeled `PROVISIONAL — ORGANIZER CONFIRMATION REQUIRED` pending upstream challenge kit archive retrieval.

### Target Specification
* **Identifier:** `Processor_A` (`5Q-Baseline-Tree`)
* **Qubits:** Exactly 5 physical qubits: `[0, 1, 2, 3, 4]`.
* **Topology:** Fixed 5-node T-tree coupling graph (4 undirected edges, 8 directed pairs): `(0, 1), (1, 2), (1, 3), (3, 4)`.
* **Native Basis Gates:** `["rz", "sx", "x", "ecr"]` (native 2Q entangler: `ecr`).
* **Hardware Noise Parameters:** $T_1 = 210.0\\ \\mu\\text{s}, T_2 = 140.0\\ \\mu\\text{s}$, 1Q error $0.010\\%$, 2Q ECR error $0.75\\%$, readout error $1.50\\%$.

### Compilation & Empirical Results ($N = 2048$ shots)
* **Circuit Depth:** 69 cycles (116 total gates).
* **Native 2Q Gates:** 18 ECR gates (12 basis synthesis + 6 routing, **2 SWAPs**).
* **Ideal Reference Emulation:** $\\bar{C} = 5.0625 \\pm 0.0229$, $\\hat{\\alpha} = 0.8438$ ($84.38\\%$), $P_{\\text{opt}} = 41.70\\%$ (854 hits, Wilson 95% CI: $[39.58\\%, 43.85\\%]$).
* **Noisy Baseline Simulation:** $\\bar{C} = 4.9399 \\pm 0.0244$, $\\hat{\\alpha} = 0.8233$ ($82.33\\%$), $P_{\\text{opt}} = 37.60\\%$ (770 hits, Wilson 95% CI: $[35.52\\%, 39.72\\%]$).

Serialized in [`results/verified_ab_v3/data/processor_a_ideal_reference.json`](results/verified_ab_v3/data/processor_a_ideal_reference.json) and [`processor_a_noisy_baseline.json`](results/verified_ab_v3/data/processor_a_noisy_baseline.json).

---

## 7. Processor B Definition, Compilation & Results (v3 Corrected)

> [!NOTE]
> **Provisional Local Configuration:** Configured as a genuine 7-physical-qubit processor (`Heavy-Hex-7`) with sparse heavy-hex unit cell topology, labeled `PROVISIONAL — ORGANIZER CONFIRMATION REQUIRED` pending upstream challenge kit archive retrieval.

### Target Specification
* **Identifier:** `Processor_B` (`Heavy-Hex-7`)
* **Qubits:** Exactly 7 physical qubits: `[0, 1, 2, 3, 4, 5, 6]`. Active mapped qubits: `[0, 1, 2, 3, 5]`.
* **Topology:** Sparse heavy-hex-inspired unit cell graph (6 undirected edges, 12 directed pairs): `(0, 1), (1, 2), (1, 3), (3, 5), (4, 5), (5, 6)`.
* **Native Basis Gates:** `["rz", "sx", "x", "cz"]` (native 2Q entangler: `cz`).
* **Hardware Noise Parameters:** $T_1 = 240.0\\ \\mu\\text{s}, T_2 = 140.0\\ \\mu\\text{s}$, 1Q error $0.015\\%$, 2Q CZ error $0.50\\%$, readout error $1.00\\%$.

### Compilation & Empirical Results ($N = 2048$ shots)
* **Circuit Depth:** 83 cycles (114 total gates).
* **Native 2Q Gates:** 18 CZ gates (12 basis synthesis + 6 routing, **2 SWAPs**).
* **Ideal Reference Emulation:** $\\bar{C} = 5.0742 \\pm 0.0230$, $\\hat{\\alpha} = 0.8457$ ($84.57\\%$), $P_{\\text{opt}} = 42.53\\%$ (871 hits, Wilson 95% CI: $[40.40\\%, 44.68\\%]$).
* **Noisy Baseline Simulation:** $\\bar{C} = 4.9839 \\pm 0.0240$, $\\hat{\\alpha} = 0.8306$ ($83.06\\%$), $P_{\\text{opt}} = 39.65\\%$ (812 hits, Wilson 95% CI: $[37.55\\%, 41.78\\%]$).

Serialized in [`results/verified_ab_v3/data/processor_b_ideal_reference.json`](results/verified_ab_v3/data/processor_b_ideal_reference.json) and [`processor_b_noisy_baseline.json`](results/verified_ab_v3/data/processor_b_noisy_baseline.json).

---

## 8. Ideal/Noisy Experiment Comparison (v3 Empirical Matrix)

All statistical hypothesis tests were performed at the standard $\\alpha = 0.05$ significance level. **Nonsignificant tests are reported strictly as "No statistically significant difference detected" and never asserted as proof of physical equivalence:**

| Comparison | Group 1 | Group 2 | $\\Delta \\bar{C}$ [95% CI] | Welch $t$-stat | $p$-value ($\\bar{C}$) | $\\bar{C}$ Diff Detected? | $\\Delta P_{\\text{opt}}$ [95% CI] | Two-Prop $z$-stat | $p$-value ($P_{\\text{opt}}$) | Proportion Diff Detected? |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **1. Processor A: Ideal vs. Noisy** | Proc A Ideal | Proc A Noisy | +0.1226 [0.0570, 0.1881] | 3.665 | $2.50 \\times 10^{-4}$ | **Yes ($p < 0.05$)** | +4.10% [1.11%, 7.10%] | 2.683 | 0.0073 | **Yes ($p < 0.05$)** |
| **2. Processor B: Ideal vs. Noisy** | Proc B Ideal | Proc B Noisy | +0.0903 [0.0252, 0.1555] | 2.718 | $6.60 \\times 10^{-3}$ | **Yes ($p < 0.05$)** | +2.88% [-0.13%, 5.89%] | 1.874 | 0.0610 | No statistically significant difference detected |
| **3a. Proc A vs. B (Controlled Ideal)** | Proc A Ideal | Proc B Ideal | -0.0117 [-0.0753, 0.0518] | -0.361 | 0.7178 | No statistically significant difference detected | -0.83% [-3.85%, 2.19%] | -0.538 | 0.5906 | No statistically significant difference detected |
| **3b. Proc A vs. B (Controlled Noisy)** | Proc A Noisy | Proc B Noisy | -0.0439 [-0.1110, 0.0231] | -1.284 | 0.1992 | No statistically significant difference detected | -2.05% [-5.03%, 0.93%] | -1.348 | 0.1777 | No statistically significant difference detected |

Serialized in [`results/verified_ab_v3/tables/pairwise_comparisons_table.md`](results/verified_ab_v3/tables/pairwise_comparisons_table.md) and visualized in [Figure 1: Cut Sampling Distribution](results/verified_ab_v3/figures/figure1_sampling_distribution.png).

---

## 9. Resource Metrics & Statistical Uncertainty (v3 Corrected)

| Target Backend | Architecture | Circuit Depth (Cycles) | Total Gates | Native 2Q Gate | Total 2Q Count | Basis 2Q | Routing 2Q | Routing SWAPs | Mean 2Q Error | Compounded 2Q Survival | Approximation Ratio $\\hat{\\alpha}$ | Success Prob $P_{\\text{opt}}$ |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Processor A (Ideal)** | 5Q-Baseline-Tree | 69 | 116 | `ecr` | 18 | 12 | 6 | 2 | 0.75% | 87.3% | 0.8438 | 41.70% |
| **Processor A (Noisy)** | 5Q-Baseline-Tree | 69 | 116 | `ecr` | 18 | 12 | 6 | 2 | 0.75% | 87.3% | 0.8233 | 37.60% |
| **Processor B (Ideal)** | Heavy-Hex-7 | 83 | 114 | `cz` | 18 | 12 | 6 | 2 | 0.50% | 91.4% | 0.8457 | 42.53% |
| **Processor B (Noisy)** | Heavy-Hex-7 | 83 | 114 | `cz` | 18 | 12 | 6 | 2 | 0.50% | 91.4% | 0.8306 | 39.65% |

### Architectural Trade-Off Analysis:
1. **Depth Advantage (Processor A):** Processor A achieves a **16.9% depth reduction** (69 vs. 83 cycles) with identical SWAP count (2 SWAPs, 6 routing gates) due to compact T-tree topology layout.
2. **Gate Fidelity Counterbalance (Processor B):** Processor B's lower 2Q error rate ($\\bar{e}_{2Q} = 0.50\\%$ vs. $0.75\\%$) yields a higher compounded entangling survival probability (**91.4%** across 18 CZ gates vs. **87.3%** across 18 ECR gates on Processor A). This 4.1% fidelity margin counterbalances Processor B's depth overhead, resulting in slightly higher noisy expected cut ($4.9839$ vs. $4.9399$, with difference not reaching significance at $\\alpha = 0.05$).

Serialized in [`results/verified_ab_v3/tables/resource_vs_quality_table.md`](results/verified_ab_v3/tables/resource_vs_quality_table.md) and [`statistical_uncertainty_table.md`](results/verified_ab_v3/tables/statistical_uncertainty_table.md).

---

"""
        text = text[:idx6] + new_sec6_to_9 + text[idx10:]
        
    text = text.replace("python scripts/run_verified_ab_v2_experiments.py", "python scripts/run_verified_ab_v3_experiments.py")
    text = text.replace("python scripts/analyze_verified_ab_v2_statistics.py", "python scripts/analyze_verified_ab_v3_statistics.py")
    text = text.replace("105 Automated Tests Passing", "115 Automated Tests Passing")
    text = text.replace("105 automated tests", "115 automated tests")
    text = text.replace("105 tests passing", "115 tests passing")

    # Update Section 12 table
    old_sec12_table = """| Feature | Official Judge-Ready Benchmark (Phases 1–6) | Historical Baseline (Phase 0 / R1–R3) |
| :--- | :--- | :--- |
| **Formulation** | 5-Qubit Symmetry-Reduced ($x_0 = 0$, $q_0 \\dots q_4 \\leftrightarrow x_1 \\dots x_5$) | 6-Qubit Direct Formulation ($q_0 \\dots q_5 \\leftrightarrow x_0 \\dots x_5$) |
| **Processor A Physical Qubits** | 5 active physical qubits (`[0, 1, 2, 3, 5]`) | 6 physical qubits on 7Q hardware spec (`[0, 1, 2, 3, 4, 5]`) |
| **Processor B Physical Qubits** | 5 active physical qubits (`[0, 3, 4, 5, 6]`) | 6 physical qubits on 7Q hardware spec (`[0, 1, 2, 3, 4, 5]`) |
| **Target Transpiled Depth** | Proc A: 66 cycles; Proc B: 81 cycles | Proc A: 84 cycles; Proc B: 98 cycles |
| **Native 2Q Gates** | Proc A: 18 ECR (2 SWAPs); Proc B: 21 CZ (3 SWAPs) | Proc A: 28 ECR (4 SWAPs); Proc B: 28 CZ (4 SWAPs) |
| **Results Location** | [`results/verified_ab_v2/`](results/verified_ab_v2/) | [`results/data/`](results/data/) & [`results/tables/`](results/tables/) |
| **Traceability Status** | REQ-16 through REQ-19 (AUD-12 through AUD-15) | REQ-01 through REQ-15 (AUD-01 through AUD-11) |"""

    new_sec12_table = """| Feature | Corrected Target Benchmark (v3) | Historical 5Q-Subset Benchmark (v2) | Historical Direct Baseline (Phase 0 / v1) |
| :--- | :--- | :--- | :--- |
| **Formulation** | 5-Qubit Symmetry-Reduced ($x_0 = 0$) | 5-Qubit Symmetry-Reduced ($x_0 = 0$) | 6-Qubit Direct Formulation ($q_0 \\dots q_5 \\leftrightarrow x_0 \\dots x_5$) |
| **Processor A Architecture** | Genuine 5Q Baseline Tree (`[0..4]`) | 5 active physical qubits on 7Q Falcon-H | 6 physical qubits on 7Q Falcon-H |
| **Processor B Architecture** | Genuine 7Q Heavy-Hex (`[0..6]`, active 5Q) | 5 active physical qubits on 7Q Ring-7 | 6 physical qubits on 7Q Ring-7 |
| **Target Transpiled Depth** | Proc A: 69 cycles; Proc B: 83 cycles | Proc A: 66 cycles; Proc B: 81 cycles | Proc A: 84 cycles; Proc B: 98 cycles |
| **Native 2Q Gates** | Proc A: 18 ECR (2 SWAPs); Proc B: 18 CZ (2 SWAPs) | Proc A: 18 ECR (2 SWAPs); Proc B: 21 CZ (3 SWAPs) | Proc A: 28 ECR (4 SWAPs); Proc B: 28 CZ (4 SWAPs) |
| **Results Location** | [`results/verified_ab_v3/`](results/verified_ab_v3/) | [`results/verified_ab_v2/`](results/verified_ab_v2/) | [`results/data/`](results/data/) & [`results/tables/`](results/tables/) |
| **Traceability Status** | REQ-20 & REQ-21 (v3 Corrected Architectures) | REQ-16 through REQ-19 (AUD-12 through AUD-15) | REQ-01 through REQ-15 (AUD-01 through AUD-11) |"""

    if old_sec12_table in text:
        text = text.replace(old_sec12_table, new_sec12_table)
    else:
        print("Warning: old sec 12 table in README not matched exactly")

    readme_path.write_text(text, encoding="utf-8")
    print("README.md updated successfully!")

if __name__ == "__main__":
    update_readme()
