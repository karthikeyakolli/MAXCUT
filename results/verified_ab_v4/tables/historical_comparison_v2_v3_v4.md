# Historical Repository Run Comparison: v2 vs v3 vs v4

This table documents the evolution of the experimental setups and metrics across benchmark versions, preserving historical integrity while segregating superseded runs.

| Specification Feature | Benchmark Version 2 (`verified_ab_v2`) | Benchmark Version 3 (`verified_ab_v3`) | Benchmark Version 4 (`verified_ab_v4` — CURRENT AUTHORITATIVE) |
| :--- | :--- | :--- | :--- |
| **Audit Status** | Historical / Superseded | Historical / Superseded | **Current Canonical / Fully Certified** |
| **Processor A Topology** | 5Q Linear Chain | 5Q Linear Chain | **5Q Linear Chain** (Hardware spec hash `aa9e30240af51a17`) |
| **Processor B Topology** | 7Q Ring (Stale Starter Guide) | 9Q Sparse Tree (Tier 1 Kit) | **9Q Sparse Tree** (Hardware spec hash `341d471380e28d49`) |
| **Processor D Custom** | Not Implemented | Not Implemented | **8Q Chorded Ring Mesh** (Hash `a60ecf34eb463a10`) |
| **Native 2Q Gate Basis** | ECR (`["rz", "sx", "x", "ecr"]`) | ECR (`["rz", "sx", "x", "ecr"]`) | **CX** (`["rz", "sx", "x", "cx"]` — Tier 1 Mandated) |
| **Noise Model** | Custom / Synthetic Asymmetric Readout | Custom / Asymmetric Readout | **Uniform Synthetic Benchmark Noise** ($p_{1Q}=0.001, p_{CX}=0.005, p_{RO}=0.01$) |
| **Shot Budget per Case**| 1024 shots | 1024 shots | **4096 shots** (16,384 total A/B; 24,576 total A/B/D) |
| **Shared Parameters** | Heuristic Search | Heuristic Search | **Deterministic Multistart Certified** ($\gamma^*=2.527058, \beta^*=2.698287$) |
| **Processor A Noisy <C>**| 4.6982 (Approx: 78.30%) | 4.7412 (Approx: 79.02%) | **4.8784** (Approx: **81.31%**) |
| **Processor B Noisy <C>**| 4.8828 (Approx: 81.38% on 7Q Ring) | 4.7646 (Approx: 79.41% on 9Q Tree) | **4.8923** (Approx: **81.54%**) |
| **Processor D Noisy <C>**| N/A | N/A | **4.9141** (Approx: **81.90%**) |
| **Processor A Depth** | 42 (ECR basis) | 42 (ECR basis) | **58** (CX basis, 2 SWAPs, 18 CX) |
| **Processor B Depth** | 33 (7Q Ring, 0 SWAPs) | 40 (9Q Tree, 1 SWAP) | **52** (CX basis, 1 SWAP, 15 CX) |
| **Processor D Depth** | N/A | N/A | **36** (CX basis, 0 SWAPs, 12 CX) |
