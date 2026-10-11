# Processor A/B Noise-Aware Benchmark Summary Table

| Experiment Case | Execution Mode | Best Cut | Expected Cut $\langle C \rangle$ (95% CI) | Approx Ratio $\alpha$ | Success Prob $P_{\text{opt}}$ (95% CI) | Circuit Depth | 2Q Gates | SWAP Count |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Processor A — ideal/reference** | `aer_hardware_topology_emulation` | 6.0 | 4.8901 [4.8384, 4.9419] | 0.8150 (81.50%) | 0.3931 [37.21%, 41.44%] | 84 | 28 | 4 |
| **Processor A — noisy baseline** | `aer_noisy_simulation` | 6.0 | 4.7373 [4.6830, 4.7916] | 0.7896 (78.96%) | 0.3564 [33.60%, 37.74%] | 84 | 28 | 4 |
| **Processor B — ideal/reference** | `aer_hardware_topology_emulation` | 6.0 | 4.9116 [4.8597, 4.9635] | 0.8186 (81.86%) | 0.4072 [38.61%, 42.87%] | 98 | 28 | 4 |
| **Processor B — noisy baseline** | `aer_noisy_simulation` | 6.0 | 4.8223 [4.7688, 4.8757] | 0.8037 (80.37%) | 0.3813 [36.06%, 40.26%] | 98 | 28 | 4 |
