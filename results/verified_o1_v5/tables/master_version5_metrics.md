# Master Version 5 Benchmark Metrics (Authoritative Full-Size Primary Benchmarks)

**Graph Instance:** O1_MaxCut_Weighted_V5 (|V|=6, |E|=8, Total Weight W=24.0, C_max=20.0)  
**Frozen Baseline Controls:** 4096 shots/case | Transpiler Preset Level 1 (SABRE) | Seed 42 | QAOA Depth p=1  
**Optimized Angles:** gamma*=6.087282 rad, beta*=1.942981 rad  

| Experiment Case | Target Backend | Architecture Family | Physical Qubits | Active Qubits | Mapped Qubits | Mode | Circuit Depth | Total Gates | Native 2Q CX | Basis 2Q CX | Routing 2Q Overhead | Routing SWAPs | Mean Cut <C> | Std Error | Approx Ratio | Best Cut | P(opt) | P(opt) 95% CI | Shots |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Processor B — Ideal Reference | Processor_B | 9Q-Sparse-Tree | 9 | 6 | [2, 3, 4, 5, 6, 7] | ideal | 52 | 88 | 25 | 16 | 9 | 3 | 16.9321 | 0.0512 | 0.8466 | 20.0 | 0.146 | [0.1355, 0.1571] | 4096 |
| Processor B — Noisy Baseline | Processor_B | 9Q-Sparse-Tree | 9 | 6 | [2, 3, 4, 5, 6, 7] | noisy | 52 | 88 | 25 | 16 | 9 | 3 | 16.4282 | 0.056 | 0.8214 | 20.0 | 0.1292 | [0.1192, 0.1398] | 4096 |
| Processor D — Ideal Reference | Processor_D | 8Q Chorded Ring Mesh | 8 | 6 | [0, 1, 2, 3, 4, 7] | ideal | 41 | 85 | 22 | 16 | 6 | 2 | 16.7678 | 0.0529 | 0.8384 | 20.0 | 0.124 | [0.1143, 0.1345] | 4096 |
| Processor D — Noisy Baseline | Processor_D | 8Q Chorded Ring Mesh | 8 | 6 | [0, 1, 2, 3, 4, 7] | noisy | 41 | 85 | 22 | 16 | 6 | 2 | 16.3276 | 0.0567 | 0.8164 | 20.0 | 0.1121 | [0.1028, 0.1221] | 4096 |
