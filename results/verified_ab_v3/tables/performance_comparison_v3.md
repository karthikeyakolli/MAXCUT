# Version 3 Controlled A/B Experiment Performance Comparison

Evaluation across corrected Processor A (5 physical qubits) and Processor B (7 physical qubits heavy-hex) under controlled settings.

| Experiment Case | Target Backend | Architecture Family | Backend Physical Qubits | Active Physical Qubits | Mapped Qubits | Execution Mode | Noisy | Circuit Depth | Total Gates | Native 2Q Gate | Total 2Q Count | Basis 2Q Count | Routing 2Q Overhead | Routing SWAPs | Mean Cut <C> | Std Error | Approx Ratio | Success Prob P(opt) | Shots | Sim Time (s) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Processor A — ideal/reference | Processor_A | 5Q-Baseline-Tree | 5 | 5 | [0, 1, 2, 3, 4] | aer_hardware_topology_emulation | False | 69 | 116 | ecr | 18 | 12 | 6 | 2 | 5.0625 | 0.0229 | 0.8438 | 0.417 | 2048 | 3.507 |
| Processor A — noisy baseline | Processor_A | 5Q-Baseline-Tree | 5 | 5 | [0, 1, 2, 3, 4] | aer_noisy_simulation | True | 69 | 116 | ecr | 18 | 12 | 6 | 2 | 4.9399 | 0.0244 | 0.8233 | 0.376 | 2048 | 0.109 |
| Processor B — ideal/reference | Processor_B | Heavy-Hex-7 | 7 | 5 | [0, 1, 2, 3, 5] | aer_hardware_topology_emulation | False | 83 | 114 | cz | 18 | 12 | 6 | 2 | 5.0742 | 0.023 | 0.8457 | 0.4253 | 2048 | 0.049 |
| Processor B — noisy baseline | Processor_B | Heavy-Hex-7 | 7 | 5 | [0, 1, 2, 3, 5] | aer_noisy_simulation | True | 83 | 114 | cz | 18 | 12 | 6 | 2 | 4.9839 | 0.024 | 0.8306 | 0.3965 | 2048 | 0.109 |
