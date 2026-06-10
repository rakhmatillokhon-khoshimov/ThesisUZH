#!/usr/bin/env python3
"""Honest tiering of the 17 substantive divergences (core vs expected affordance).

Not every substantive divergence is equally interesting. Reporting all 17 as one
headline overstates the result, because several are expected access affordances
(the app knows the user's locale; the app renders source cards on an
already-answered prompt) rather than behavioral differences. This script splits
the 17 into honest tiers and reports the smaller non-trivial core with Wilson CIs.

  Tier 1  Behavioral divergence: a refusal-status flip, a factual/retrieval
          correction, or a verifiable format failure.
  Tier 2  Retrieval/source affordance: app renders visible sources but the
          answer category is unchanged.
  Tier 3  Locale affordance: app adds account/location context; expected and
          trivial.

Outputs under analysis_scaleup_cleaned/tiers/:
  divergence_tiers.json, divergence_tiers_memo.md, divergence_tiers.tex
"""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "results/analysis"
CODING = CLEAN / "scaleup_human_reviewed_coding_sheet.csv"
OUT = CLEAN / "tiers"
OUT.mkdir(parents=True, exist_ok=True)
N = 60


def wilson(k, n, z=1.959963984540054):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / d
    return (round(max(0, c - h), 3), round(min(1, c + h), 3))


def main():
    rows = [r for r in csv.DictReader(open(CODING)) if r["substantive_divergence"] == "yes"]
    tiers = {"tier1_behavioral": [], "tier2_source_affordance": [], "tier3_locale_affordance": []}
    detail = []
    for r in rows:
        t = r["final_divergence_type"]
        pid = r["prompt_id"]
        ui = r["app_ui_surface_signature"]
        behavioral = any(x in t for x in ("refusal_status", "factuality", "format_compliance"))
        if behavioral:
            kind = ("refusal" if "refusal_status" in t else
                    "factual" if "factuality" in t else "format")
            tiers["tier1_behavioral"].append(pid)
            tier = 1
        elif ui == "sources_visible":
            kind = "visible_sources"
            tiers["tier2_source_affordance"].append(pid)
            tier = 2
        else:
            kind = "locale_or_framing"
            tiers["tier3_locale_affordance"].append(pid)
            tier = 3
        detail.append({"prompt_id": pid, "tier": tier, "kind": kind, "final_type": t})

    t1 = tiers["tier1_behavioral"]
    refusal = [d["prompt_id"] for d in detail if d["kind"] == "refusal"]
    factual = [d["prompt_id"] for d in detail if d["kind"] == "factual"]
    fmt = [d["prompt_id"] for d in detail if d["kind"] == "format"]

    res = {
        "total_substantive": len(rows),
        "tier_counts": {k: len(v) for k, v in tiers.items()},
        "tier_members": tiers,
        "behavioral_core": {
            "n": len(t1), "rate": round(len(t1) / N, 3), "wilson95": wilson(len(t1), N),
            "refusal": {"ids": refusal, "n": len(refusal), "wilson95": wilson(len(refusal), N)},
            "factual": {"ids": factual, "n": len(factual)},
            "format": {"ids": fmt, "n": len(fmt)},
        },
        "affordance_only": {
            "n": len(tiers["tier2_source_affordance"]) + len(tiers["tier3_locale_affordance"]),
            "source": tiers["tier2_source_affordance"],
            "locale": tiers["tier3_locale_affordance"],
        },
        "detail": detail,
    }
    OUT.joinpath("divergence_tiers.json").write_text(json.dumps(res, indent=2))

    bc = res["behavioral_core"]
    m = ["# Honest Tiering of the 17 Substantive Divergences\n",
         "Reporting all 17 as a single headline overstates the result. Split by "
         "what actually differs:\n",
         f"- **Tier 1 -- behavioral divergence: {len(t1)}/60** "
         f"({bc['rate']:.2f}, Wilson 95% [{bc['wilson95'][0]}, {bc['wilson95'][1]}]). "
         f"A refusal-status flip ({len(refusal)}), a factual/retrieval correction "
         f"({len(factual)}), or a verifiable format failure ({len(fmt)}).",
         f"- **Tier 2 -- retrieval/source affordance: {len(tiers['tier2_source_affordance'])}/60.** "
         "The app shows visible sources but the answer category is unchanged.",
         f"- **Tier 3 -- locale affordance: {len(tiers['tier3_locale_affordance'])}/60.** "
         "The app adds account/location context; expected and largely trivial.\n",
         "The honest core of the thesis is the Tier-1 behavioral set "
         f"({len(t1)}/60), led by the {len(refusal)} refusal-style divergences "
         f"(Wilson 95% [{bc['refusal']['wilson95'][0]}, {bc['refusal']['wilson95'][1]}]) "
         f"and the {len(factual)} factual/retrieval corrections. The remaining "
         f"{res['affordance_only']['n']} cases are access affordances: real and "
         "user-relevant, but expected once the app has tools and locale, and not "
         "evidence of a deeper behavioral difference.\n",
         "## Members\n",
         f"- Tier 1 behavioral: {', '.join(t1)}",
         f"- Tier 2 source: {', '.join(tiers['tier2_source_affordance'])}",
         f"- Tier 3 locale: {', '.join(tiers['tier3_locale_affordance'])}\n",
         "### Interpretation\n",
         "This reframing makes the claim smaller but more defensible. The thesis "
         "should lead with the Tier-1 behavioral core and explicitly down-weight the "
         "locale cases, rather than presenting 17 equally-weighted findings.\n"]
    OUT.joinpath("divergence_tiers_memo.md").write_text("\n".join(m))

    tex = ["% Auto-generated by analyze_divergence_tiers.py",
           "\\begin{table}[t]\\centering\\small",
           "\\caption{Honest tiering of the 17 substantive divergences. The "
           "non-trivial behavioral core is %d/60; the remaining %d are expected "
           "access affordances (visible sources or locale context) that do not change "
           "the answer category.}" % (len(t1), res["affordance_only"]["n"]),
           "\\label{tab:tiers}",
           "\\begin{tabular}{llc}", "\\toprule",
           "Tier & Description & $n$/60 \\\\", "\\midrule",
           "1 & Behavioral (refusal %d, factual %d, format %d) & %d \\\\" % (
               len(refusal), len(factual), len(fmt), len(t1)),
           "2 & Retrieval/source affordance (category unchanged) & %d \\\\" % len(tiers["tier2_source_affordance"]),
           "3 & Locale affordance (expected, trivial) & %d \\\\" % len(tiers["tier3_locale_affordance"]),
           "\\midrule",
           "\\textbf{Total substantive} & & \\textbf{%d} \\\\" % len(rows),
           "\\bottomrule", "\\end{tabular}", "\\end{table}"]
    OUT.joinpath("divergence_tiers.tex").write_text("\n".join(tex))
    print(json.dumps({"tier_counts": res["tier_counts"],
                      "behavioral_core_n": len(t1),
                      "refusal": len(refusal), "factual": len(factual), "format": len(fmt)}, indent=2))


if __name__ == "__main__":
    main()
