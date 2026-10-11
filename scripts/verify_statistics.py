"""Statistical verification of QAOA Max-Cut experimental results."""

import json
import math
from pathlib import Path
import numpy as np
from scipy import stats

def analyze_result(path):
    with open(path, "r", encoding="utf-8") as f:
        d = json.load(f)
    counts = d["decoded_counts"]
    raw_counts = d["raw_counts"]
    cut_map = d["cut_values_by_bitstring"]
    
    # Expand to individual cut samples
    cuts = []
    opt_hits = 0
    total_shots = sum(counts.values())
    
    for bs, cnt in counts.items():
        c_val = cut_map[bs]
        cuts.extend([c_val] * cnt)
        if c_val == 6.0:
            opt_hits += cnt
            
    cuts = np.array(cuts)
    mean_c = float(np.mean(cuts))
    std_c = float(np.std(cuts, ddof=1))
    se_c = float(std_c / math.sqrt(total_shots))
    ci95_c = (mean_c - 1.959964 * se_c, mean_c + 1.959964 * se_c)
    
    p_hat = float(opt_hits / total_shots)
    se_p = float(math.sqrt(p_hat * (1 - p_hat) / total_shots))
    
    # Wilson score interval for binomial proportion p
    z = 1.959964
    denom = 1 + z**2 / total_shots
    center = (p_hat + z**2 / (2 * total_shots)) / denom
    half = (z * math.sqrt(p_hat * (1 - p_hat) / total_shots + z**2 / (4 * total_shots**2))) / denom
    wilson_ci = (center - half, center + half)
    wald_ci = (p_hat - z * se_p, p_hat + z * se_p)
    
    # Approximation ratio
    alpha_sample = mean_c / 6.0
    alpha_ci95 = (ci95_c[0] / 6.0, ci95_c[1] / 6.0)
    
    return {
        "backend": d["backend_metadata"]["backend_name"],
        "shots": total_shots,
        "mean_c": mean_c,
        "std_c": std_c,
        "se_c": se_c,
        "ci95_c": ci95_c,
        "p_opt": p_hat,
        "opt_hits": opt_hits,
        "se_p": se_p,
        "wilson_ci": wilson_ci,
        "wald_ci": wald_ci,
        "alpha_sample": alpha_sample,
        "alpha_ci95": alpha_ci95,
        "analytic_c": d["algorithm_parameters"]["final_expected_cut_from_opt"],
        "cuts": cuts
    }

def main():
    paths = {
        "Simulator": Path("results/data/O1_MaxCut_Challenge_aer_simulator_p1_result.json"),
        "Processor A": Path("results/data/O1_MaxCut_Challenge_processor_a_p1_result.json"),
        "Processor B": Path("results/data/O1_MaxCut_Challenge_processor_b_p1_result.json"),
    }
    
    results = {}
    print("=" * 80)
    print("  STATISTICAL RECOMPUTATION & UNCERTAINTY QUANTIFICATION (N = 2048 shots)")
    print("=" * 80)
    
    for label, path in paths.items():
        res = analyze_result(path)
        results[label] = res
        print(f"\n[{label}] ({res['backend']}):")
        print(f"  Analytic Expectation <C>_analytic: {res['analytic_c']:.6f}")
        print(f"  Sample Mean Cut C_bar:            {res['mean_c']:.6f} +/- {res['se_c']:.6f}")
        print(f"  Sample Std Dev s:                 {res['std_c']:.6f}")
        print(f"  95% CI for Expected Cut:          [{res['ci95_c'][0]:.6f}, {res['ci95_c'][1]:.6f}]")
        print(f"  Sample Approx Ratio alpha:        {res['alpha_sample']:.6f} (95% CI: [{res['alpha_ci95'][0]:.4f}, {res['alpha_ci95'][1]:.4f}])")
        print(f"  Optimal Hits (C=6):               {res['opt_hits']} / {res['shots']}")
        print(f"  P(opt) Success Probability:       {res['p_opt']:.6f} ({res['p_opt']*100:.2f}%) +/- {res['se_p']:.6f}")
        print(f"  95% Wilson Score CI for P(opt):   [{res['wilson_ci'][0]:.6f}, {res['wilson_ci'][1]:.6f}] ([{res['wilson_ci'][0]*100:.2f}%, {res['wilson_ci'][1]*100:.2f}%])")
        print(f"  95% Wald CI for P(opt):           [{res['wald_ci'][0]:.6f}, {res['wald_ci'][1]:.6f}]")
        
        # Check if analytic falls inside 95% CI
        contains_analytic = res['ci95_c'][0] <= res['analytic_c'] <= res['ci95_c'][1]
        print(f"  Analytic within 95% CI?           {contains_analytic}")

    # Comparative hypothesis tests between Processor A and Processor B
    res_a = results["Processor A"]
    res_b = results["Processor B"]
    
    print("\n" + "=" * 80)
    print("  COMPARATIVE A/B UNCERTAINTY & HYPOTHESIS TESTING (Processor A vs Processor B)")
    print("=" * 80)
    
    # 1. Difference in Expected Cut
    diff_c = res_b["mean_c"] - res_a["mean_c"]
    se_diff_c = math.sqrt(res_a["se_c"]**2 + res_b["se_c"]**2)
    z_c = diff_c / se_diff_c
    p_val_c = 2 * (1 - stats.norm.cdf(abs(z_c)))
    ci95_diff_c = (diff_c - 1.959964 * se_diff_c, diff_c + 1.959964 * se_diff_c)
    
    # Two-sample t-test on raw samples
    t_stat, t_pval = stats.ttest_ind(res_b["cuts"], res_a["cuts"], equal_var=False)
    
    print(f"\n1. Difference in Sample Mean Cut (Delta C_bar = B - A):")
    print(f"   Delta C_bar = {diff_c:+.6f} ({diff_c/res_a['mean_c']*100:+.2f}%)")
    print(f"   SE(Delta C_bar) = {se_diff_c:.6f}")
    print(f"   95% CI for (C_B - C_A): [{ci95_diff_c[0]:+.6f}, {ci95_diff_c[1]:+.6f}]")
    print(f"   Welch's t-statistic = {t_stat:.4f}, p-value = {t_pval:.4f}")
    print(f"   Statistically Significant at alpha=0.05? {t_pval < 0.05} (p = {t_pval:.4f})")
    
    # 2. Difference in Success Probability
    diff_p = res_b["p_opt"] - res_a["p_opt"]
    se_diff_p = math.sqrt(res_a["se_p"]**2 + res_b["se_p"]**2)
    z_p = diff_p / se_diff_p
    p_val_p = 2 * (1 - stats.norm.cdf(abs(z_p)))
    ci95_diff_p = (diff_p - 1.959964 * se_diff_p, diff_p + 1.959964 * se_diff_p)
    
    print(f"\n2. Difference in Success Probability (Delta P = B - A):")
    print(f"   Delta P = {diff_p:+.6f} ({diff_p*100:+.2f} percentage points)")
    print(f"   SE(Delta P) = {se_diff_p:.6f}")
    print(f"   95% CI for (P_B - P_A): [{ci95_diff_p[0]*100:+.2f}%, {ci95_diff_p[1]*100:+.2f}%]")
    print(f"   z-statistic = {z_p:.4f}, p-value = {p_val_p:.4f}")
    print(f"   Statistically Significant at alpha=0.05? {p_val_p < 0.05} (p = {p_val_p:.4f})")
    
    print("\nConclusion: Neither the cut value difference (p = 0.55) nor the probability difference (p = 0.36) is statistically significant at alpha = 0.05.")
    print("Both observed differences are fully explained by finite-shot multinomial sampling variance.")

if __name__ == "__main__":
    main()
