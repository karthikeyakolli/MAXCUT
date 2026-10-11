# Resource Overhead vs. Solution Quality Matrix (Version 3)

Hardware-level resource consumption versus optimization quality across corrected architectures.

| Experiment Case | Target Backend | Architecture Family | Backend Physical Qubits | Active Physical Qubits | Mapped Qubits | Execution Mode | Circuit Depth | Total Gates | Native 2Q Gate | Total 2Q Count | Basis 2Q Count | Routing 2Q Overhead | Routing SWAPs | Approximation Ratio | Success Prob P(opt) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Processor A — ideal/reference | Processor_A | 5Q-Baseline-Tree | 5 | 5 | [0, 1, 2, 3, 4] | aer_hardware_topology_emulation | 69 | 116 | ecr | 18 | 12 | 6 | 2 | 0.8438 | 41.70% |
| Processor A — noisy baseline | Processor_A | 5Q-Baseline-Tree | 5 | 5 | [0, 1, 2, 3, 4] | aer_noisy_simulation | 69 | 116 | ecr | 18 | 12 | 6 | 2 | 0.8233 | 37.60% |
| Processor B — ideal/reference | Processor_B | Heavy-Hex-7 | 7 | 5 | [0, 1, 2, 3, 5] | aer_hardware_topology_emulation | 83 | 114 | cz | 18 | 12 | 6 | 2 | 0.8457 | 42.53% |
| Processor B — noisy baseline | Processor_B | Heavy-Hex-7 | 7 | 5 | [0, 1, 2, 3, 5] | aer_noisy_simulation | 83 | 114 | cz | 18 | 12 | 6 | 2 | 0.8306 | 39.65% |
