# Statistical Uncertainty and Metric Verification Table

| Target | Execution Mode | Shots | Analytic <C> | Empirical Mean Cut | Cut Std Dev (s) | Cut SE | Cut 95% CI | Analytic In CI | Analytic Approx Ratio | Empirical Approx Ratio | Approx Ratio 95% CI | Opt Hits (C=6) | P(opt) Cumulative | P(opt) SE | P(opt) 95% Wilson CI |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Ideal Simulator | qiskit_aer_simulator | 2048 | 4.8671 | 4.8931 | 1.184 | 0.0262 | [4.8418, 4.9443] | True | 0.8112 | 0.8155 | [0.8070, 0.8241] | 779 | 0.3804 | 0.0107 | [35.96%, 40.16%] |
| Processor A (Falcon-H) | aer_hardware_topology_emulation | 2048 | 4.8671 | 4.8901 | 1.1956 | 0.0264 | [4.8384, 4.9419] | True | 0.8112 | 0.815 | [0.8064, 0.8237] | 805 | 0.3931 | 0.0108 | [37.21%, 41.44%] |
| Processor B (Ring-7) | aer_hardware_topology_emulation | 2048 | 4.8671 | 4.9116 | 1.1986 | 0.0265 | [4.8597, 4.9635] | True | 0.8112 | 0.8186 | [0.8100, 0.8273] | 834 | 0.4072 | 0.0109 | [38.61%, 42.87%] |
