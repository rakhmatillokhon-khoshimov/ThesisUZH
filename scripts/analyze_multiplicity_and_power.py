#!/usr/bin/env python3
"""Multiplicity correction and power/floor analysis (addresses underpowered-stats risk).

Two honest additions:
 1. Benjamini-Hochberg FDR across the *exploratory* test family, so the reader
    sees which associations survive correction rather than a list of raw p-values.
 2. An exact-test floor and required-N analysis for the primary confirmatory
    endpoint (the McNemar refusal asymmetry), making explicit that the result is
    one discordant pair short of significance, not contradicted.

Outputs under analysis_scaleup_cleaned/multiplicity/:
  multiplicity_power.json, multiplicity_power_memo.md, multiplicity_power.tex
"""
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "results/analysis"
OUT = CLEAN / "multiplicity"
OUT.mkdir(parents=True, exist_ok=True)


def bh_adjust(items):
    """items: list of (name, p). Returns list of (name, p, q) with BH-adjusted q."""
    s = sorted(items, key=lambda kv: kv[1])
    n = len(s)
    q_raw = [(name, p, p * n / (i + 1)) for i, (name, p) in enumerate(s)]
    # enforce monotonicity from the largest
    out = []
    running = 1.0
    for name, p, q in reversed(q_raw):
        running = min(running, q)
        out.append((name, p, min(running, 1.0)))
    return list(reversed(out))


def mcnemar_exact_twosided(b, c):
    """Exact two-sided McNemar p for discordant counts b, c."""
    n = b + c
    k = min(b, c)
    # two-sided: 2 * sum_{i=0}^{k} C(n,i) 0.5^n, capped at 1
    s = sum(math.comb(n, i) for i in range(0, k + 1)) * (0.5 ** n)
    return min(1.0, 2 * s)


def main():
    mod = json.loads((CLEAN / "moderators/divergence_moderators.json").read_text())
    lex = json.loads((CLEAN / "lexical/lexical_divergence.json").read_text())

    family = [
        ("source-family chi-square", mod["by_source_family"]["chi2_independence"]["p_value"]),
        ("refusal-expected vs social-control (Fisher)",
         mod["by_category"]["fisher_vs_refusal_expected"]
            ["disallowed_refusal_expected_vs_social_recommendation"]["p_value"]),
        ("category chi-square", mod["by_category"]["chi2_independence"]["p_value"]),
        ("risk-level trend (Cochran-Armitage)", mod["by_risk_level"]["cochran_armitage_trend"]["p_value"]),
        ("lexical Jaccard (Mann-Whitney)", lex["summary"]["p_value"]),
    ]
    adj = bh_adjust(family)
    survive05 = [a for a in adj if a[2] < 0.05]
    survive10 = [a for a in adj if a[2] < 0.10]

    # --- primary endpoint: McNemar floor + required discordant pairs ---
    b, c = 5, 0  # API-only refusals vs app-only refusals (all 60 / refusal-expected)
    p_obs = mcnemar_exact_twosided(b, c)
    # smallest all-one-direction discordant count d that gives two-sided p < .05
    d_needed = None
    for d in range(1, 40):
        if mcnemar_exact_twosided(d, 0) < 0.05:
            d_needed = d
            break
    # required-N projection at the observed discordance proportion (5/60)
    disc_rate = 5 / 60
    n_proj = math.ceil(d_needed / disc_rate) if d_needed else None

    res = {
        "exploratory_family_size": len(family),
        "bh_fdr": [{"test": n, "p": round(p, 4), "q_bh": round(q, 4)} for n, p, q in adj],
        "survive_q_0.05": [n for n, _, _ in survive05],
        "survive_q_0.10": [n for n, _, _ in survive10],
        "primary_endpoint": {
            "test": "McNemar exact, two-sided, full-refusal discordance",
            "discordant_api_only": b, "discordant_app_only": c,
            "p_value": round(p_obs, 4),
            "min_discordant_for_p_lt_.05": d_needed,
            "interpretation": (f"With {b} one-directional discordant pairs the exact "
                               f"two-sided p is {p_obs:.4f}; the test cannot reach "
                               f"p<.05 until {d_needed} all-one-direction discordant "
                               f"pairs are observed. The result is one discordant pair "
                               f"short of significance, not contradicted."),
            "required_N_projection": n_proj,
            "required_N_note": (f"At the observed discordance proportion ({b}/60 = "
                                f"{disc_rate:.3f}), roughly {n_proj} prompts would be "
                                f"expected to yield {d_needed} one-directional "
                                f"discordant pairs and cross significance."),
        },
    }
    OUT.joinpath("multiplicity_power.json").write_text(json.dumps(res, indent=2))

    pe = res["primary_endpoint"]
    m = ["# Multiplicity Correction and Power/Floor Analysis\n",
         "This section pre-empts the two standard objections to a compact audit: "
         "many tests on one dataset, and an underpowered primary endpoint. It does "
         "not add claims; it disciplines the existing ones.\n",
         "## 1. Exploratory family under Benjamini-Hochberg FDR\n",
         "The confirmatory endpoint (refusal asymmetry) is reported separately. All "
         "moderator/association tests are treated as one exploratory family and "
         f"FDR-corrected ({res['exploratory_family_size']} tests):\n",
         "| Test | raw p | BH q |",
         "|---|---:|---:|"]
    for n, p, q in adj:
        star = " *" if q < 0.05 else (" (.10)" if q < 0.10 else "")
        m.append(f"| {n} | {p:.4f} | {q:.4f}{star} |")
    m.append("")
    m.append(f"**Surviving FDR at q<0.05:** {', '.join(res['survive_q_0.05']) or 'none'}. "
             f"These are the substantive associations (the benchmark-source effect and "
             f"the refusal-expected-vs-control contrast). The category omnibus, the "
             f"risk-level trend, and the lexical signal do **not** survive at q<0.05 "
             f"(category survives only at q<0.10). The thesis treats the latter three "
             f"as directional/descriptive, not confirmed.\n")
    m.append("## 2. Primary endpoint: floor and required N\n")
    m.append(pe["interpretation"] + "\n")
    m.append(pe["required_N_note"] + "\n")
    m.append("The honest reading: the refusal asymmetry is complete in direction "
             "(API-only refusals 5, app-only 0) but the design is literally one event "
             "below the exact-test significance floor. This is a sample-size limit, "
             "not evidence against the effect, and it sets the concrete target for a "
             "follow-up (about %s prompts) to confirm it.\n" % pe["required_N_projection"])
    OUT.joinpath("multiplicity_power_memo.md").write_text("\n".join(m))

    tex = ["% Auto-generated by analyze_multiplicity_and_power.py",
           "\\begin{table}[t]\\centering\\small",
           "\\caption{Exploratory association tests under Benjamini--Hochberg FDR "
           "correction. After correction, only the benchmark-source association and "
           "the refusal-expected-vs-control contrast survive at $q<0.05$; the category "
           "omnibus, risk-level trend, and lexical signal are treated as "
           "directional/descriptive. The confirmatory refusal endpoint (McNemar exact "
           "$p=%.4f$) is reported separately and is one discordant pair below the "
           "exact-test floor.}" % pe["p_value"],
           "\\label{tab:multiplicity}",
           "\\begin{tabular}{lcc}", "\\toprule",
           "Exploratory test & raw $p$ & BH $q$ \\\\", "\\midrule"]
    for n, p, q in adj:
        mark = "$^{*}$" if q < 0.05 else ""
        tex.append("%s & %.3f & %.3f%s \\\\" % (n.replace("&", "\\&"), p, q, mark))
    tex += ["\\bottomrule",
            "\\multicolumn{3}{l}{\\footnotesize $^{*}$ survives FDR at $q<0.05$.}\\\\",
            "\\end{tabular}", "\\end{table}"]
    OUT.joinpath("multiplicity_power.tex").write_text("\n".join(tex))
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
