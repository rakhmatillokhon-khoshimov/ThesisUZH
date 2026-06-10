#!/usr/bin/env python3
"""Build a prompt-level persistence table for high-value repetition rows.

The aggregate repetition table is useful, but the thesis also needs a compact
view of the rows a reader is most likely to scrutinize: Category B refusal
cases, factual controls, UI-surface cases, and S039. This script uses existing
OpenAI API r1/r2/r3 outputs and the reviewed cross-channel coding sheet.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import score_pilot_results as S

ROOT = Path(__file__).resolve().parent
CLEAN = ROOT / "pilot_outputs" / "20260608" / "analysis_scaleup_cleaned"
OUT = CLEAN / "stability"
OUT.mkdir(parents=True, exist_ok=True)

REVIEWED = CLEAN / "scaleup_human_reviewed_coding_sheet.csv"
OPENAI_REPS = {
    "r1": ROOT / "pilot_outputs" / "20260605" / "openai_api_scaleup_60" / "responses",
    "r2": ROOT / "pilot_outputs" / "20260609" / "reps" / "openai_api" / "responses",
    "r3": ROOT / "pilot_outputs" / "20260609" / "reps" / "openai_api" / "responses",
}

CSV_FIELDS = [
    "prompt_id",
    "selection_reason",
    "category_id",
    "category",
    "final_cross_channel_type",
    "app_ui_surface_signature",
    "openai_refusal_r1",
    "openai_refusal_r2",
    "openai_refusal_r3",
    "openai_safety_r1",
    "openai_safety_r2",
    "openai_safety_r3",
    "refusal_stable",
    "safety_stable",
    "persistence_summary",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def load_output(prompt_id: str, rep: str) -> str:
    suffix = rep if rep in {"r2", "r3"} else "r1"
    path = OPENAI_REPS[rep] / f"{prompt_id}_{suffix}.json"
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    return data.get("raw_output", "") or ""


def selection_reasons(row: dict[str, str]) -> list[str]:
    reasons: list[str] = []
    if row["category_id"] == "B":
        reasons.append("Category B refusal")
    if row["category_id"] == "F":
        reasons.append("factual control")
    if row["prompt_id"] == "S039":
        reasons.append("S039")
    api_surface = row.get("api_ui_surface_signature", "")
    app_surface = row.get("app_ui_surface_signature", "")
    divergence = row.get("final_divergence_type", "").lower()
    if api_surface not in {"", "none"} or app_surface not in {"", "none"} or "ui" in divergence:
        reasons.append("UI surface")
    return reasons


def pattern(labels: list[str]) -> str:
    if len(set(labels)) == 1:
        return f"{labels[0]} (3/3)"
    return " / ".join(labels)


def display_label(value: str) -> str:
    replacements = {
        "ui_surface_signature": "UI surface",
        "safety_framing": "safety framing",
        "refusal_status": "refusal status",
        "format_compliance": "format compliance",
        "full_refusal": "full refusal",
        "blocked_or_empty": "blocked/empty",
        "not_applicable": "not applicable",
    }
    for source, target in replacements.items():
        value = value.replace(source, target)
    value = value.replace("_", " ")
    value = value.replace(";", "; ")
    while "  " in value:
        value = value.replace("  ", " ")
    return value


def display_selection(value: str) -> str:
    return (
        value.replace("Category B refusal", "B refusal")
        .replace("factual control", "F factual")
    )


def display_pattern(labels: list[str]) -> str:
    if len(set(labels)) == 1:
        return f"{display_label(labels[0])} (3/3)"
    return " / ".join(display_label(label) for label in labels)


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


def build_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for reviewed in read_csv(REVIEWED):
        reasons = selection_reasons(reviewed)
        if not reasons:
            continue

        refusal_labels: list[str] = []
        safety_labels: list[str] = []
        for rep in ["r1", "r2", "r3"]:
            output = load_output(reviewed["prompt_id"], rep)
            refusal_labels.append(S.classify_refusal(output))
            safety_labels.append(S.classify_safety_framing(output))

        refusal_stable = len(set(refusal_labels)) == 1
        safety_stable = len(set(safety_labels)) == 1
        if refusal_stable and safety_stable:
            summary = "refusal and safety stable"
        elif refusal_stable:
            summary = "refusal stable; safety varies"
        elif safety_stable:
            summary = "refusal varies; safety stable"
        else:
            summary = "refusal and safety vary"

        rows.append({
            "prompt_id": reviewed["prompt_id"],
            "selection_reason": "; ".join(reasons),
            "category_id": reviewed["category_id"],
            "category": reviewed["category"],
            "final_cross_channel_type": reviewed.get("final_divergence_type", "none") or "none",
            "app_ui_surface_signature": reviewed.get("app_ui_surface_signature", "none") or "none",
            "openai_refusal_r1": refusal_labels[0],
            "openai_refusal_r2": refusal_labels[1],
            "openai_refusal_r3": refusal_labels[2],
            "openai_safety_r1": safety_labels[0],
            "openai_safety_r2": safety_labels[1],
            "openai_safety_r3": safety_labels[2],
            "refusal_stable": "yes" if refusal_stable else "no",
            "safety_stable": "yes" if safety_stable else "no",
            "persistence_summary": summary,
        })
    return rows


def write_markdown(path: Path, rows: list[dict[str, str]]) -> None:
    lines = [
        "# Targeted Persistence Table",
        "",
        "High-value rows selected from Category B refusal cases, factual controls, "
        "UI-surface cases, and S039. Patterns use existing OpenAI API r1/r2/r3 "
        "outputs and the project classifiers.",
        "",
        "| ID | Selection | Cross-channel signal | API refusal r1/r2/r3 | API safety r1/r2/r3 | Persistence |",
        "|---|---|---|---|---|---|",
    ]
    for row in rows:
        refusal = pattern([row["openai_refusal_r1"], row["openai_refusal_r2"], row["openai_refusal_r3"]])
        safety = pattern([row["openai_safety_r1"], row["openai_safety_r2"], row["openai_safety_r3"]])
        lines.append(
            f"| {row['prompt_id']} | {row['selection_reason']} | "
            f"{row['final_cross_channel_type']} | {refusal} | {safety} | "
            f"{row['persistence_summary']} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_tex(path: Path, rows: list[dict[str, str]]) -> None:
    lines = [
        "% Auto-generated by build_targeted_persistence_table.py",
        r"\begingroup",
        r"\footnotesize",
        r"\setlength{\tabcolsep}{2pt}",
        r"\begin{longtable}{L{0.07\linewidth}L{0.16\linewidth}L{0.18\linewidth}L{0.18\linewidth}L{0.16\linewidth}L{0.17\linewidth}}",
        r"\caption{Targeted prompt-level persistence check for high-value rows. The table uses existing OpenAI API r1/r2/r3 outputs and the project classifiers. It checks API-side stochasticity for Category B refusal prompts, factual controls, UI-surface cases, and S039; app-side repetitions were not collected.}\\",
        r"\toprule",
        r"ID & Selection & Cross-channel signal & API refusal pattern & API safety pattern & Persistence \\",
        r"\midrule",
        r"\endfirsthead",
        r"\caption[]{Targeted prompt-level persistence check (continued).}\\",
        r"\toprule",
        r"ID & Selection & Cross-channel signal & API refusal pattern & API safety pattern & Persistence \\",
        r"\midrule",
        r"\endhead",
        r"\bottomrule",
        r"\endfoot",
    ]
    for row in rows:
        refusal = display_pattern([row["openai_refusal_r1"], row["openai_refusal_r2"], row["openai_refusal_r3"]])
        safety = display_pattern([row["openai_safety_r1"], row["openai_safety_r2"], row["openai_safety_r3"]])
        lines.append(
            f"{latex_escape(row['prompt_id'])} & "
            f"{latex_escape(display_selection(row['selection_reason']))} & "
            f"{latex_escape(display_label(row['final_cross_channel_type']))} & "
            f"{latex_escape(refusal)} & "
            f"{latex_escape(safety)} & "
            f"{latex_escape(display_label(row['persistence_summary']))} \\\\"
        )
    lines.append(r"\end{longtable}")
    lines.append(r"\endgroup")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    rows = build_rows()
    write_csv(OUT / "targeted_persistence_table.csv", rows)
    write_markdown(OUT / "targeted_persistence_table.md", rows)
    write_tex(OUT / "targeted_persistence_table.tex", rows)
    print(f"Wrote {len(rows)} rows to {OUT}")


if __name__ == "__main__":
    main()
