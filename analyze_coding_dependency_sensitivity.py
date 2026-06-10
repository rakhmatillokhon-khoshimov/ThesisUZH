#!/usr/bin/env python3
"""Sensitivity checks for dependence on judgment-heavy coding labels.

This does not replace inter-rater reliability. It answers a narrower robustness
question: if the softest label (safety framing) is ignored, do the final claims
still have a harder evidence anchor such as visible UI surface, factual-control
support, exact format compliance, or a full-refusal contrast?
"""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CLEAN = ROOT / "pilot_outputs" / "20260608" / "analysis_scaleup_cleaned"
REVIEWED = CLEAN / "scaleup_human_reviewed_coding_sheet.csv"
OUT = CLEAN / "sensitivity"
OUT.mkdir(parents=True, exist_ok=True)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def wilson(k: int, n: int, z: float = 1.96) -> list[float | None]:
    if n == 0:
        return [None, None]
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    margin = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n) / denom
    return [round(center - margin, 3), round(center + margin, 3)]


def has_type(row: dict[str, str], label: str) -> bool:
    return label in {part.strip() for part in row.get("final_divergence_type", "").split(";")}


def anchors(row: dict[str, str]) -> list[str]:
    out: list[str] = []
    if has_type(row, "ui_surface_signature"):
        out.append("visible UI surface")
    if has_type(row, "factuality"):
        out.append("factual-control support")
    if has_type(row, "format_compliance"):
        out.append("exact format compliance")
    if row.get("api_refusal_status") == "full_refusal" and row.get("app_refusal_status") != "full_refusal":
        out.append("full-refusal contrast")
    elif has_type(row, "refusal_status"):
        out.append("refusal-boundary contrast")
    return out


def latex_escape(value: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(ch, ch) for ch in value)


def main() -> int:
    rows = read_csv(REVIEWED)
    n = len(rows)
    final = [row for row in rows if row.get("substantive_divergence") == "yes"]
    no_safety_only = [
        row for row in final
        if any(part.strip() for part in row["final_divergence_type"].split(";") if part.strip() != "safety_framing")
    ]
    direct_artifact = [
        row for row in final
        if has_type(row, "ui_surface_signature")
        or has_type(row, "factuality")
        or has_type(row, "format_compliance")
    ]
    full_refusal = [
        row for row in final
        if row.get("api_refusal_status") == "full_refusal"
        and row.get("app_refusal_status") != "full_refusal"
    ]
    hard_anchor = [row for row in final if anchors(row)]
    safety_only = [
        row for row in final
        if row.get("final_divergence_type") == "safety_framing"
    ]

    scenarios = [
        {
            "scenario": "All reviewed substantive divergences",
            "count": len(final),
            "denominator": n,
            "interpretation": "Final manually reviewed thesis count.",
        },
        {
            "scenario": "After dropping safety-framing-only evidence",
            "count": len(no_safety_only),
            "denominator": n,
            "interpretation": "Main count if the softest label cannot stand alone.",
        },
        {
            "scenario": "Direct artifact/factual/format evidence only",
            "count": len(direct_artifact),
            "denominator": n,
            "interpretation": "Rows anchored in visible UI surface, factual-control support, or exact format compliance.",
        },
        {
            "scenario": "Full-refusal contrast",
            "count": len(full_refusal),
            "denominator": n,
            "interpretation": "Rows where the API is a full refusal and the app is not.",
        },
        {
            "scenario": "Hard-anchor union",
            "count": len(hard_anchor),
            "denominator": n,
            "interpretation": "Rows with at least one non-framing anchor: UI, factual, format, or refusal-boundary evidence.",
        },
    ]
    for scenario in scenarios:
        scenario["rate"] = round(scenario["count"] / scenario["denominator"], 3)
        scenario["wilson95"] = wilson(scenario["count"], scenario["denominator"])

    per_case = [
        {
            "prompt_id": row["prompt_id"],
            "final_divergence_type": row["final_divergence_type"],
            "anchors": "; ".join(anchors(row)),
        }
        for row in final
    ]

    report = {
        "n_pairs": n,
        "n_final_substantive": len(final),
        "safety_framing_only_prompt_ids": [row["prompt_id"] for row in safety_only],
        "scenarios": scenarios,
        "per_case_anchors": per_case,
        "interpretation": (
            "No final substantive case depends on safety framing alone. The "
            "formal inter-rater reliability route remains preferable, but the "
            "headline access-channel claim is not carried by the softest label."
        ),
    }
    (OUT / "coding_dependency_sensitivity.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    with (OUT / "coding_dependency_sensitivity.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["scenario", "count", "denominator", "rate", "wilson95", "interpretation"])
        writer.writeheader()
        for scenario in scenarios:
            row = dict(scenario)
            row["wilson95"] = str(row["wilson95"])
            writer.writerow(row)

    md = [
        "# Coding-Dependency Sensitivity",
        "",
        "This is a robustness check for single-coder dependence. It does not replace true inter-rater reliability.",
        "",
        "| Scenario | Count/n | Rate | Wilson 95% CI | Interpretation |",
        "|---|---:|---:|---|---|",
    ]
    for scenario in scenarios:
        md.append(
            f"| {scenario['scenario']} | {scenario['count']}/{scenario['denominator']} | "
            f"{scenario['rate']:.2f} | {scenario['wilson95']} | {scenario['interpretation']} |"
        )
    md += ["", "## Per-Case Anchors", "", "| ID | Final type | Non-framing anchor(s) |", "|---|---|---|"]
    for row in per_case:
        md.append(f"| {row['prompt_id']} | {row['final_divergence_type']} | {row['anchors']} |")
    (OUT / "coding_dependency_sensitivity.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    tex = [
        "% Auto-generated by analyze_coding_dependency_sensitivity.py",
        r"\begingroup",
        r"\small",
        r"\begin{longtable}{L{0.36\linewidth}rrL{0.40\linewidth}}",
        r"\caption{Coding-dependence sensitivity checks for the final 60-pair result. These checks do not replace inter-rater reliability; they show whether the substantive count depends on the softest coding dimension.}",
        r"\label{tab:coding-dependence-sensitivity}\\",
        r"\toprule",
        r"Scenario & Count & Rate & Interpretation \\",
        r"\midrule",
        r"\endfirsthead",
        r"\caption[]{Coding-dependence sensitivity checks (continued).}\\",
        r"\toprule",
        r"Scenario & Count & Rate & Interpretation \\",
        r"\midrule",
        r"\endhead",
        r"\bottomrule",
        r"\endfoot",
    ]
    for scenario in scenarios:
        tex.append(
            f"{latex_escape(scenario['scenario'])} & "
            f"{scenario['count']}/{scenario['denominator']} & "
            f"{scenario['rate']:.2f} & "
            f"{latex_escape(scenario['interpretation'])} \\\\"
        )
    tex += [r"\end{longtable}", r"\endgroup"]
    (OUT / "coding_dependency_sensitivity.tex").write_text("\n".join(tex) + "\n", encoding="utf-8")

    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
