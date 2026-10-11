# Pairwise Statistical Hypothesis Tests (Version 3)

Tested at alpha = 0.05. Non-significant tests are strictly reported as 'No statistically significant difference detected' rather than proof of equivalence.

| Comparison | Group 1 | Group 2 | Delta Mean Cut | 95% CI Delta Cut | Welch t-stat | p-value (Mean Cut) | Mean Cut Difference Detected? | Delta P(opt) | 95% CI Delta P(opt) | Two-Prop z-stat | p-value (Proportion) | Proportion Difference Detected? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Comparison 1: Processor A Ideal vs. Noisy | Processor A — ideal/reference | Processor A — noisy baseline | 0.1226 | [0.0570, 0.1881] | 3.665 | 2.5034e-04 | Yes (p < 0.05) | +4.10% | [1.11%, 7.10%] | 2.683 | 7.2936e-03 | Yes (p < 0.05) |
| Comparison 2: Processor B Ideal vs. Noisy | Processor B — ideal/reference | Processor B — noisy baseline | 0.0903 | [0.0252, 0.1555] | 2.718 | 6.5992e-03 | Yes (p < 0.05) | +2.88% | [-0.13%, 5.89%] | 1.874 | 6.0965e-02 | No statistically significant difference detected |
| Comparison 3a: Processor A vs. B (Controlled Ideal) | Processor A — ideal/reference | Processor B — ideal/reference | -0.0117 | [-0.0753, 0.0518] | -0.361 | 7.1784e-01 | No statistically significant difference detected | -0.83% | [-3.85%, 2.19%] | -0.538 | 5.9059e-01 | No statistically significant difference detected |
| Comparison 3b: Processor A vs. B (Controlled Noisy) | Processor A — noisy baseline | Processor B — noisy baseline | -0.0439 | [-0.1110, 0.0231] | -1.284 | 1.9919e-01 | No statistically significant difference detected | -2.05% | [-5.03%, 0.93%] | -1.348 | 1.7770e-01 | No statistically significant difference detected |
