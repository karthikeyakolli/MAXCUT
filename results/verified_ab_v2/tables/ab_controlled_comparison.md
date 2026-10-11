# Controlled Ideal vs. Noisy A/B Experiment Comparison (5Q Symmetry Reduced)

**Official Graph:** $|V|=6, |E|=8, W=8.00$, $C_{\max}=6.0000$

**Controlled Settings:** $p=1$, $\gamma^*=2.5270, \beta^*=2.6983$, shots=2048, level=1, seed=42

| Experiment Case | Backend | Architecture | Execution Mode | Noisy | Expected Cut <C> | Std Error | Approx Ratio | P(opt) | Best Cut | Best Bitstring | 2Q Gates | Routing SWAPs | Depth | Total Gates | Shots |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Processor A — ideal/reference | Processor_A | Falcon-H | aer_hardware_topology_emulation | False | 5.0742 | 0.023 | 0.8457 | 0.4253 | 6.0 | 011001 | 18 | 2 | 66 | 121 | 2048 |
| Processor A — noisy baseline | Processor_A | Falcon-H | aer_noisy_simulation | True | 4.9556 | 0.0245 | 0.8259 | 0.3892 | 6.0 | 011001 | 18 | 2 | 66 | 121 | 2048 |
| Processor B — ideal/reference | Processor_B | Ring-7 | aer_hardware_topology_emulation | False | 5.0337 | 0.0235 | 0.8389 | 0.4087 | 6.0 | 010011 | 21 | 3 | 81 | 122 | 2048 |
| Processor B — noisy baseline | Processor_B | Ring-7 | aer_noisy_simulation | True | 4.9346 | 0.0244 | 0.8224 | 0.3696 | 6.0 | 010011 | 21 | 3 | 81 | 122 | 2048 |
