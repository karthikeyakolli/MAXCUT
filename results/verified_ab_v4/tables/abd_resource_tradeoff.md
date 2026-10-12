# Processor A vs B vs D Resource Overhead & Solution Quality Trade-Off

| Processor Architecture | Target Qubits | Circuit Depth | 2Q Gates (CX) | Routing SWAPs | Noisy Mean Cut <C> | Noisy Approx Ratio | Noisy P(opt) | Relative Noise Degradation |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Processor A** (5Q Linear Chain) | 5 | 58 | 18 | 2 | 4.8784 | 81.31% | 38.09% | -3.51% (Cut), -10.81% (Popt) |
| **Processor B** (9Q Sparse Tree) | 9 | 52 | 15 | 1 | 4.8923 | 81.54% | 38.45% | -3.23% (Cut), -9.95% (Popt) |
| **Processor D** (8Q Chorded Mesh) | 8 | 36 | 12 | 0 | 4.9141 | 81.90% | 38.87% | 2.80% (Cut) |
