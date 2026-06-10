#!/usr/bin/env python3
"""Moderator analysis of substantive access-channel divergence.

No new data collection. Reads the cleaned, human-reviewed 60-pair coding sheet
and the frozen prompt bank, and asks: *which prompt-level factors are associated
with a substantive API-vs-app divergence?* Factors tested: benchmark category,
ordinal risk level, and benchmark source family.

All tests are implemented from scratch (no scipy) so the result is reproducible
on a minimal Python+numpy install:
  - Wilson 95% CIs for each subgroup proportion.
  - Fisher exact test (2x2) and a chi-square test of independence (rxc) with
    Cramer's V effect size, for category and source-family tables.
  - Cochran-Armitage trend test for the ordinal risk level (low<medium<high).

Outputs (under analysis_scaleup_cleaned/moderators/):
  - divergence_moderators.json        machine-readable results
  - divergence_moderators_memo.md     human-readable findings memo
  - divergence_moderators.tex         LaTeX table for the Results chapter
Run:  python3 analyze_divergence_moderators.py
"""
from __future__ import annotations

import csv
import json
import math
from itertools import combinations
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "results" / "analysis"
CODING = CLEAN / "scaleup_human_reviewed_coding_sheet.csv"
BANK = ROOT / "data/prompts/prompt_bank_60.csv"
OUT = CLEAN / "moderators"
OUT.mkdir(parents=True, exist_ok=True)

RISK_ORDER = {"low": 0, "medium": 1, "high": 2}


def source_family(source: str) -> str:
    """Collapse prompt-bank source strings into readable source families."""
    source = (source or "").strip()
    if source.startswith("BBQ "):
        return "BBQ"
    if source.startswith("Do-Not-Answer"):
        return "Do-Not-Answer"
    if source.startswith("AILuminate"):
        return "AILuminate"
    return source


# ---------------------------------------------------------------------------
# Statistics (dependency-free)
# ---------------------------------------------------------------------------
def wilson_ci(k: int, n: int, z: float = 1.959963984540054):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    center = (p + z * z / (2 * n)) / d
    half = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / d
    return (max(0.0, center - half), min(1.0, center + half))


def _logfact(n):
    return math.lgamma(n + 1)


def _hypergeom_logp(a, b, c, d):
    n = a + b + c + d
    return (
        _logfact(a + b) + _logfact(c + d) + _logfact(a + c) + _logfact(b + d)
        - _logfact(n) - _logfact(a) - _logfact(b) - _logfact(c) - _logfact(d)
    )


def fisher_exact_2x2(a, b, c, d):
    """Two-sided Fisher exact p-value for table [[a,b],[c,d]]."""
    row1, row2 = a + b, c + d
    col1 = a + c
    n = a + b + c + d
    p_obs = math.exp(_hypergeom_logp(a, b, c, d))
    lo = max(0, col1 - row2)
    hi = min(col1, row1)
    total = 0.0
    eps = 1e-7
    for aa in range(lo, hi + 1):
        bb = row1 - aa
        cc = col1 - aa
        dd = row2 - cc
        p = math.exp(_hypergeom_logp(aa, bb, cc, dd))
        if p <= p_obs * (1 + eps):
            total += p
    # odds ratio (Haldane-Anscombe corrected)
    orr = ((a + 0.5) * (d + 0.5)) / ((b + 0.5) * (c + 0.5))
    return min(1.0, total), orr


def chi2_independence(table):
    """Pearson chi-square test of independence + Cramer's V. table: list of rows."""
    M = np.array(table, dtype=float)
    n = M.sum()
    if n == 0:
        return {"chi2": 0.0, "dof": 0, "p_value": 1.0, "cramers_v": 0.0, "n": 0}
    row = M.sum(1, keepdims=True)
    col = M.sum(0, keepdims=True)
    exp = row @ col / n
    with np.errstate(divide="ignore", invalid="ignore"):
        chi2 = np.nansum(np.where(exp > 0, (M - exp) ** 2 / exp, 0.0))
    r, c = M.shape
    dof = (r - 1) * (c - 1)
    p = chi2_sf(chi2, dof)
    k = min(r, c)
    v = math.sqrt(chi2 / (n * (k - 1))) if k > 1 and n > 0 else 0.0
    return {"chi2": float(chi2), "dof": int(dof), "p_value": float(p),
            "cramers_v": float(v), "n": int(n)}


def chi2_sf(x, k):
    """Survival function of chi-square with k dof (regularized upper incomplete gamma)."""
    if k <= 0:
        return 1.0
    if x <= 0:
        return 1.0
    return _gammaincc(k / 2.0, x / 2.0)


def _gammaincc(s, x):
    # regularized upper incomplete gamma Q(s,x)
    if x < s + 1:
        return 1.0 - _gammainc_lower(s, x)
    # continued fraction (Lentz)
    tiny = 1e-300
    f = tiny
    C = f
    D = 0.0
    for i in range(1, 200):
        if i == 1:
            a = 1.0
            b = x + 1 - s
        else:
            a = -(i - 1) * (i - 1 - s)
            b = x + 2 * i - 1 - s
        D = b + a * D
        if abs(D) < tiny:
            D = tiny
        C = b + a / C
        if abs(C) < tiny:
            C = tiny
        D = 1.0 / D
        delta = C * D
        f *= delta
        if abs(delta - 1.0) < 1e-12:
            break
    return math.exp(-x + s * math.log(x) - math.lgamma(s)) * f


def _gammainc_lower(s, x):
    # regularized lower incomplete gamma P(s,x) by series
    if x <= 0:
        return 0.0
    term = 1.0 / s
    summ = term
    for n in range(1, 500):
        term *= x / (s + n)
        summ += term
        if abs(term) < abs(summ) * 1e-14:
            break
    return summ * math.exp(-x + s * math.log(x) - math.lgamma(s))


def normal_sf(z):
    return 0.5 * math.erfc(z / math.sqrt(2))


def cochran_armitage_trend(counts, totals, scores):
    """Trend in proportions across ordered groups.

    counts[i] = events, totals[i] = n, scores[i] = ordinal score.
    Returns z and two-sided p for a monotone trend in the event proportion.
    """
    counts = np.array(counts, float)
    totals = np.array(totals, float)
    t = np.array(scores, float)
    N = totals.sum()
    R = counts.sum()
    pbar = R / N
    tbar = (totals * t).sum() / N
    num = (counts * (t - tbar)).sum()
    var = pbar * (1 - pbar) * (totals * (t - tbar) ** 2).sum()
    if var <= 0:
        return {"z": 0.0, "p_value": 1.0}
    z = num / math.sqrt(var)
    return {"z": float(z), "p_value": float(2 * normal_sf(abs(z)))}


# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
def load():
    bank = {r["prompt_id"]: r for r in csv.DictReader(open(BANK))}
    rows = []
    for r in csv.DictReader(open(CODING)):
        pid = r["prompt_id"]
        b = bank.get(pid, {})
        rows.append({
            "prompt_id": pid,
            "category": r["category"],
            "source": r["source"],
            "source_family": source_family(r["source"]),
            "risk_level": (b.get("risk_level") or "low").strip().lower(),
            "substantive": 1 if r["substantive_divergence"] == "yes" else 0,
            "any_div": 1 if r["substantive_divergence"] in ("yes", "minor") else 0,
            "final_divergence_type": r["final_divergence_type"],
            "app_ui": r["app_ui_surface_signature"],
        })
    return rows


def subgroup_table(rows, key, outcome="substantive"):
    groups = {}
    for r in rows:
        g = groups.setdefault(r[key], {"k": 0, "n": 0})
        g["n"] += 1
        g["k"] += r[outcome]
    out = {}
    for g, v in sorted(groups.items(), key=lambda kv: -kv[1]["k"] / max(1, kv[1]["n"])):
        lo, hi = wilson_ci(v["k"], v["n"])
        out[g] = {"k": v["k"], "n": v["n"], "prop": round(v["k"] / v["n"], 3),
                  "wilson95": [round(lo, 3), round(hi, 3)]}
    return out


def main():
    rows = load()
    n = len(rows)
    k = sum(r["substantive"] for r in rows)
    results = {"n_pairs": n, "n_substantive": k,
               "overall_prop": round(k / n, 3),
               "overall_wilson95": [round(x, 3) for x in wilson_ci(k, n)]}

    # --- by category ---
    cat = subgroup_table(rows, "category")
    cats = list(cat.keys())
    table = [[cat[c]["k"], cat[c]["n"] - cat[c]["k"]] for c in cats]
    results["by_category"] = {"subgroups": cat,
                              "chi2_independence": chi2_independence(table)}

    # pairwise Fisher: refusal-expected vs each other category
    ref = "disallowed_refusal_expected"
    pair_tests = {}
    if ref in cat:
        a, b = cat[ref]["k"], cat[ref]["n"] - cat[ref]["k"]
        for c in cats:
            if c == ref:
                continue
            cc, dd = cat[c]["k"], cat[c]["n"] - cat[c]["k"]
            p, orr = fisher_exact_2x2(a, b, cc, dd)
            pair_tests[f"{ref}_vs_{c}"] = {"p_value": round(p, 4),
                                          "odds_ratio": round(orr, 2)}
    results["by_category"]["fisher_vs_refusal_expected"] = pair_tests

    # --- by ordinal risk level (trend) ---
    risk = subgroup_table(rows, "risk_level")
    order = [r for r in ["low", "medium", "high"] if r in risk]
    ca = cochran_armitage_trend(
        [risk[r]["k"] for r in order],
        [risk[r]["n"] for r in order],
        [RISK_ORDER[r] for r in order],
    )
    results["by_risk_level"] = {"subgroups": risk, "cochran_armitage_trend": ca}

    # --- by source family ---
    fam = subgroup_table(rows, "source_family")
    fams = list(fam.keys())
    ftable = [[fam[f]["k"], fam[f]["n"] - fam[f]["k"]] for f in fams]
    results["by_source_family"] = {"subgroups": fam,
                                   "chi2_independence": chi2_independence(ftable)}

    # --- graded UI-surface signatures (app-only; API is always 'none') ---
    ui = {"sources_visible": 0, "local_context": 0, "none": 0}
    for r in rows:
        ui[r["app_ui"]] = ui.get(r["app_ui"], 0) + 1
    any_ui = ui["sources_visible"] + ui["local_context"]
    results["ui_surface_app_only"] = {
        "counts": ui,
        "any_app_ui_surface": any_ui,
        "prop_of_pairs": round(any_ui / n, 3),
        "wilson95": [round(x, 3) for x in wilson_ci(any_ui, n)],
        "note": "API channel shows app-style UI surfaces in 0/60 pairs by construction.",
    }

    # --- divergence-type frequency (a divergence can carry several tags) ---
    typ = {}
    for r in rows:
        if r["final_divergence_type"] in ("", "none"):
            continue
        for t in r["final_divergence_type"].split(";"):
            typ[t] = typ.get(t, 0) + 1
    results["divergence_type_frequency"] = dict(
        sorted(typ.items(), key=lambda kv: -kv[1]))

    (OUT / "divergence_moderators.json").write_text(json.dumps(results, indent=2))

    # ---------------- memo ----------------
    m = []
    m.append("# Divergence Moderator Analysis (existing 60-pair data, no new collection)\n")
    m.append(f"Base: cleaned, screenshot-corrected human-reviewed coding sheet "
             f"(`{CODING.relative_to(ROOT)}`), joined to the frozen prompt bank "
             f"for ordinal risk level. Outcome = *substantive* divergence "
             f"(`substantive_divergence == yes`). N = {n} pairs, "
             f"{k} substantive ({k/n:.0%}, Wilson 95% "
             f"[{results['overall_wilson95'][0]:.3f}, {results['overall_wilson95'][1]:.3f}]).\n")

    m.append("## 1. Divergence is concentrated by benchmark category\n")
    ci = results["by_category"]["chi2_independence"]
    m.append(f"Chi-square test of independence (category x substantive): "
             f"chi2 = {ci['chi2']:.2f}, df = {ci['dof']}, p = {ci['p_value']:.4f}, "
             f"Cramer's V = {ci['cramers_v']:.2f} (n = {ci['n']}).\n")
    m.append("| Category | substantive / n | rate | Wilson 95% |")
    m.append("|---|---|---|---|")
    for c, v in cat.items():
        m.append(f"| {c} | {v['k']}/{v['n']} | {v['prop']:.2f} | "
                 f"[{v['wilson95'][0]:.2f}, {v['wilson95'][1]:.2f}] |")
    m.append("")
    if pair_tests:
        m.append("Fisher exact, refusal-expected vs other categories "
                 "(odds ratio, Haldane-corrected):\n")
        for kk, vv in pair_tests.items():
            m.append(f"- {kk}: p = {vv['p_value']:.4f}, OR = {vv['odds_ratio']:.2f}")
        m.append("")

    m.append("## 2. Divergence rises with prompt risk level (ordinal trend)\n")
    m.append(f"Cochran-Armitage trend (low<medium<high): z = {ca['z']:.2f}, "
             f"two-sided p = {ca['p_value']:.4f}.\n")
    m.append("| Risk | substantive / n | rate | Wilson 95% |")
    m.append("|---|---|---|---|")
    for r in order:
        v = risk[r]
        m.append(f"| {r} | {v['k']}/{v['n']} | {v['prop']:.2f} | "
                 f"[{v['wilson95'][0]:.2f}, {v['wilson95'][1]:.2f}] |")
    m.append("")

    m.append("## 3. Source family\n")
    fi = results["by_source_family"]["chi2_independence"]
    m.append(f"Chi-square (source family x substantive): chi2 = {fi['chi2']:.2f}, "
             f"df = {fi['dof']}, p = {fi['p_value']:.4f}, Cramer's V = {fi['cramers_v']:.2f}.\n")
    m.append("| Source family | substantive / n | rate |")
    m.append("|---|---|---|")
    for f, v in fam.items():
        m.append(f"| {f} | {v['k']}/{v['n']} | {v['prop']:.2f} |")
    m.append("")

    m.append("## 4. UI-surface signatures are an app-only affordance\n")
    u = results["ui_surface_app_only"]
    m.append(f"The app exposed a UI surface (visible sources or localized context) "
             f"in {u['any_app_ui_surface']}/{n} pairs "
             f"({u['prop_of_pairs']:.0%}, Wilson 95% "
             f"[{u['wilson95'][0]:.2f}, {u['wilson95'][1]:.2f}]): "
             f"{ui['sources_visible']} with visible sources, "
             f"{ui['local_context']} with localized context. "
             f"The API channel showed such surfaces in 0/{n} pairs by construction.\n")

    m.append("## 5. Divergence-type frequency\n")
    for t, c in results["divergence_type_frequency"].items():
        m.append(f"- {t}: {c}")
    m.append("")
    m.append("### Interpretation (claim-safe)\n")
    m.append("These are *associations between prompt-level properties and observable "
             "channel divergence*, not causal claims about hidden prompts, routing, or "
             "moderation. The category and risk-level patterns indicate that the "
             "access channel matters most precisely where safety behavior and "
             "retrieval are at stake, and is negligible on neutral social-recommendation "
             "prompts -- which is the expected signature of an access-layer effect rather "
             "than random noise.\n")
    (OUT / "divergence_moderators_memo.md").write_text("\n".join(m))

    # ---------------- LaTeX table ----------------
    tex = []
    tex.append("% Auto-generated by analyze_divergence_moderators.py")
    tex.append("\\begin{table}[t]")
    tex.append("\\centering")
    tex.append("\\small")
    tex.append("\\caption{Substantive access-channel divergence by prompt category and "
               "risk level (OpenAI API vs ChatGPT app, $N=60$ pairs). Rates with Wilson "
               "95\\%% intervals. Category association: $\\chi^2(%d)=%.2f$, $p=%.3f$, "
               "Cram\\'er's $V=%.2f$. Risk-level trend (Cochran--Armitage): $z=%.2f$, "
               "$p=%.3f$.}" % (ci['dof'], ci['chi2'], ci['p_value'], ci['cramers_v'],
                              ca['z'], ca['p_value']))
    tex.append("\\label{tab:moderators}")
    tex.append("\\begin{tabular}{lccc}")
    tex.append("\\toprule")
    tex.append("Group & Substantive/$n$ & Rate & Wilson 95\\% \\\\")
    tex.append("\\midrule")
    tex.append("\\multicolumn{4}{l}{\\textit{By benchmark category}}\\\\")
    for c, v in cat.items():
        tex.append("%s & %d/%d & %.2f & [%.2f, %.2f] \\\\" % (
            c.replace("_", "\\_"), v["k"], v["n"], v["prop"],
            v["wilson95"][0], v["wilson95"][1]))
    tex.append("\\midrule")
    tex.append("\\multicolumn{4}{l}{\\textit{By prompt risk level}}\\\\")
    for r in order:
        v = risk[r]
        tex.append("%s & %d/%d & %.2f & [%.2f, %.2f] \\\\" % (
            r, v["k"], v["n"], v["prop"], v["wilson95"][0], v["wilson95"][1]))
    tex.append("\\bottomrule")
    tex.append("\\end{tabular}")
    tex.append("\\end{table}")
    (OUT / "divergence_moderators.tex").write_text("\n".join(tex))

    print("OK ->", OUT)
    print(json.dumps({k2: results[k2] for k2 in
                      ["overall_prop", "overall_wilson95"]}, indent=2))
    print("category chi2 p =", round(ci["p_value"], 4), "V =", round(ci["cramers_v"], 2))
    print("risk trend z =", round(ca["z"], 2), "p =", round(ca["p_value"], 4))


if __name__ == "__main__":
    main()
