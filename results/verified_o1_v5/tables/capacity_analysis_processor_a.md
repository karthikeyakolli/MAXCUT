# Processor A Capacity Limitation & Auxiliary Reduced Formulation Report

## 1. Architectural Capacity Limitation
The canonical Track O1 weighted Max-Cut problem instance contains **6 vertices** ($|V|=6$).
The primary submission benchmarks must solve the full 6-variable problem directly on the target hardware.

* **Processor A Physical Capacity:** 5 physical qubits arranged in a nearest-neighbor linear chain `0 - 1 - 2 - 3 - 4`.
* **Logical Circuit Requirement:** 6 logical qubits.
* **Compilation Outcome:** Transpilation strictly fails with `TranspilerError: More virtual qubits (6) exist than physical (5)`.
* **Compliance Policy:** In strict adherence to Section 7 and 9 of the challenge guidelines, Processor A is preserved in its authentic 5-qubit topology. We explicitly declare that Processor A cannot host the full-size 6-qubit benchmark without variable reduction.

## 2. Auxiliary Symmetry-Reduced Experiment (5 Qubits, x0 = 0)
To provide an architectural reference, an auxiliary 5-variable symmetry-reduced experiment was executed under identical baseline noise:
* **Variational Parameters:** gamma* = 6.090986 rad, beta* = 0.378749 rad
* **Ideal Circuit:** Depth = 38, 2Q CX Gates = 21, Routing SWAPs = 3
* **Noisy Circuit:** Depth = 38, 2Q CX Gates = 21, Routing SWAPs = 3

> [!IMPORTANT]
> This auxiliary 5-qubit experiment is strictly segregated from the primary full-size 6-qubit benchmark.