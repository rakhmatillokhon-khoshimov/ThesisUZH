#!/usr/bin/env python3
"""Statistical summary for the access-channel scale-up (paired design).

The 60 prompts are submitted through two channels (OpenAI API vs ChatGPT app),
so channel comparisons are PAIRED on prompt_id. This computes:

  * McNemar's exact test on full-refusal discordance (API vs app), overall and
    for the refusal-expected category --- the appropriate paired test for a
    binary label measured twice on the same item;
  * Wilson 95% confidence intervals for the substantive-divergence proportion,
    overall and per category.

No SciPy dependency: McNemar uses an exact two-sided binomial; Wilson is closed
form. Outputs JSON and a LaTeX table fragment for the Results chapter.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_csv(p: Path):
    with p.open(newline="", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


def binom_two_sided_p(b: int, c: int) -> float:
    """Exact two-sided McNemar p-value: binomial(min(b,c); n=b+c, p=0.5)."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    # P(X <= k) under Binomial(n, 0.5), doubled, capped at 1.
    cdf = sum(math.comb(n, i) for i in range(0, k + 1)) / (2 ** n)
    return min(1.0, 2 * cdf)


def wilson_ci(k: int, n: int, z: float = 1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def main() -> int:
    ap = argparse.ArgumentParser()
    base = ROOT / "results/analysis"
    ap.add_argument("--pairwise", type=Path, default=base / "pairwise_results.csv")
    ap.add_argument("--coding-sheet", type=Path, default=base / "scaleup_human_reviewed_coding_sheet.csv")
    ap.add_argument("--out-json", type=Path, default=base / "scaleup_statistics.json")
    ap.add_argument("--out-tex", type=Path, default=base / "thesis_tables/scaleup_statistics.tex")
    args = ap.parse_args()

    pw = read_csv(args.pairwise)
    sheet = read_csv(args.coding_sheet)

    def is_full(x): return (x or "").strip() == "full_refusal"

    def mcnemar(subset):
        b = sum(1 for r in subset if is_full(r["api_refusal_status"]) and not is_full(r["app_refusal_status"]))
        c = sum(1 for r in subset if is_full(r["app_refusal_status"]) and not is_full(r["api_refusal_status"]))
        return {"api_only_refuse": b, "app_only_refuse": c,
                "discordant": b + c, "p_value_exact": round(binom_two_sided_p(b, c), 4)}

    catB = [r for r in pw if r["category"] == "disallowed_refusal_expected"]
    refusal = {"all_60": mcnemar(pw), "category_B_refusal_expected": mcnemar(catB)}

    # substantive divergence proportion (overall + per category)
    def is_sub(r): return (r.get("substantive_divergence") or "").strip().lower() in ("yes", "true", "1", "substantive")
    cat_tot = Counter(r["category"] for r in sheet)
    cat_sub = Counter(r["category"] for r in sheet if is_sub(r))
    n = len(sheet)
    k = sum(cat_sub.values())
    lo, hi = wilson_ci(k, n)
    proportions = {"overall": {"k": k, "n": n, "prop": round(k / n, 3),
                               "wilson95": [round(lo, 3), round(hi, 3)]}}
    for cat in sorted(cat_tot):
        kk, nn = cat_sub.get(cat, 0), cat_tot[cat]
        clo, chi = wilson_ci(kk, nn)
        proportions[cat] = {"k": kk, "n": nn, "prop": round(kk / nn, 3),
                            "wilson95": [round(clo, 3), round(chi, 3)]}

    report = {"refusal_mcnemar": refusal, "substantive_proportions": proportions,
              "note": "Paired design (prompt_id). McNemar exact two-sided binomial; Wilson 95% CI."}
    args.out_json.write_text(json.dumps(report, indent=2), encoding="utf-8")

    # LaTeX fragment
    a = refusal["all_60"]; bb = refusal["category_B_refusal_expected"]
    ov = proportions["overall"]
    lines = []
    lines.append("% Script-produced statistical summary")
    lines.append("\\begin{longtable}{lrrr}")
    lines.append("\\toprule")
    lines.append("Full-refusal discordance & API-only & App-only & McNemar $p$ \\\\")
    lines.append("\\midrule")
    lines.append(f"All 60 prompts & {a['api_only_refuse']} & {a['app_only_refuse']} & {a['p_value_exact']:.3f} \\\\")
    lines.append(f"Refusal-expected (B) & {bb['api_only_refuse']} & {bb['app_only_refuse']} & {bb['p_value_exact']:.3f} \\\\")
    lines.append("\\bottomrule")
    lines.append("\\end{longtable}")
    lines.append("")
    lines.append("\\begin{longtable}{lrrl}")
    lines.append("\\toprule")
    lines.append("Substantive divergence & $k$ & $n$ & Wilson 95\\% CI \\\\")
    lines.append("\\midrule")
    namemap = {"allowed_sensitive_over_refusal": "A allowed-sensitive",
               "disallowed_refusal_expected": "B refusal-expected",
               "boundary_safety_framing": "C boundary/framing",
               "instruction_following": "D instruction",
               "social_recommendation": "E social rec.",
               "neutral_factual_control": "F factual control"}
    lines.append(f"Overall & {ov['k']} & {ov['n']} & [{ov['wilson95'][0]:.2f}, {ov['wilson95'][1]:.2f}] \\\\")
    for cat in ["allowed_sensitive_over_refusal","disallowed_refusal_expected","boundary_safety_framing",
                "instruction_following","social_recommendation","neutral_factual_control"]:
        if cat in proportions:
            d = proportions[cat]
            lines.append(f"{namemap.get(cat,cat)} & {d['k']} & {d['n']} & [{d['wilson95'][0]:.2f}, {d['wilson95'][1]:.2f}] \\\\")
    lines.append("\\bottomrule")
    lines.append("\\end{longtable}")
    args.out_tex.parent.mkdir(parents=True, exist_ok=True)
    args.out_tex.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps(report, indent=2))
    print(f"\nWrote {args.out_json}\nWrote {args.out_tex}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
