# Primary Benchmark Comparative Performance Metrics (Version 4)

**Instance:** O1_MaxCut_Challenge (|V|=6, |E|=8, W=8.00, C_max=6.0000)  
**Shot Budget:** 4096 shots per case | **Seeds:** 42 | **Transpiler:** SABRE Level 1  

| Experiment Case | Target Backend | Architecture Family | Backend Physical Qubits | Active Physical Qubits | Mapped Qubits | Execution Mode | Noisy | Circuit Depth | Total Gates | Native 2Q Gate | Total 2Q Count | Basis 2Q Count | Routing 2Q Overhead | Routing SWAPs | Mean Cut <C> | Std Error | Approx Ratio | Success Prob P(opt) | Shots | Sim Time (s) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Processor A — Ideal Reference | Processor_A | 5Q Linear Chain CX | 5 | 5 | [0, 1, 2, 3, 4] | aer_hardware_topology_emulation | False | 58 | 84 | cx | 18 | 12 | 6 | 2 | 5.0557 | 0.0166 | 0.8426 | 0.427 | 4096 | 0.0033 |
| Processor A — Noisy Baseline | Processor_A | 5Q Linear Chain CX | 5 | 5 | [0, 1, 2, 3, 4] | aer_noisy_simulation | True | 58 | 84 | cx | 18 | 12 | 6 | 2 | 4.8784 | 0.0187 | 0.8131 | 0.3809 | 4096 | 0.003 |
| Processor B — Ideal Reference | Processor_B | 9Q Sparse Tree CX | 9 | 5 | [1, 2, 3, 4, 5] | aer_hardware_topology_emulation | False | 52 | 78 | cx | 15 | 12 | 3 | 1 | 5.0557 | 0.0166 | 0.8426 | 0.427 | 4096 | 0.0022 |
| Processor B — Noisy Baseline | Processor_B | 9Q Sparse Tree CX | 9 | 5 | [1, 2, 3, 4, 5] | aer_noisy_simulation | True | 52 | 78 | cx | 15 | 12 | 3 | 1 | 4.8923 | 0.0186 | 0.8154 | 0.3845 | 4096 | 0.0022 |
