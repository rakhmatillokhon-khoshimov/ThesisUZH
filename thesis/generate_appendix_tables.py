#!/usr/bin/env python3
"""Regenerate claim-safe appendix tables for the thesis source."""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent
ANALYSIS = PROJECT / "results" / "analysis"
OUT = ROOT / "generated"


CATEGORY_LABELS = {
    "allowed_sensitive_over_refusal": "Allowed-sensitive",
    "disallowed_refusal_expected": "Refusal-expected",
    "boundary_safety_framing": "Boundary safety",
    "instruction_following": "Instruction following",
    "social_recommendation": "Social control",
    "neutral_factual_control": "Factual control",
}

EXPECTED_LABELS = {
    "answer": "answer",
    "refuse_or_safe_redirect": "refuse/safe redirect",
    "answer_with_safety_framing": "answer + safety",
    "follow_format": "format",
    "avoid_unsupported_inference": "avoid inference",
    "direct_answer": "direct answer",
}

STATUS_LABELS = {
    "answered": "answered",
    "partial_refusal_or_safe_redirect": "partial/safe redirect",
    "full_refusal": "full refusal",
    "blocked_or_empty": "blocked/empty",
    "none": "none",
    "": "",
}

UI_LABELS = {
    "none": "none",
    "local_context": "local context",
    "sources_visible": "visible sources",
    "map_widget": "map widget",
    "file_or_canvas": "file/canvas",
    "other": "other",
    "": "",
}

DIV_LABELS = {
    "none": "none",
    "refusal_status": "refusal status",
    "ui_surface_signature": "UI surface",
    "safety_framing": "safety framing",
    "format_compliance": "format compliance",
    "factuality": "factuality",
    "verbosity": "verbosity",
    "unsupported_inference": "unsupported inference",
}

RISK_LABELS = {
    "low": "low",
    "medium": "med.",
    "high": "high",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def tex(value: str | None) -> str:
    value = "" if value is None else str(value)
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


def source_label(value: str) -> str:
    return value.replace("_", " ")


def category_label(row: dict[str, str], include_id: bool = False) -> str:
    label = CATEGORY_LABELS.get(row.get("category", ""), row.get("category", ""))
    if include_id:
        return f"{row.get('category_id', '')} {label}".strip()
    return label


def expected_label(value: str) -> str:
    return EXPECTED_LABELS.get(value, value.replace("_", " "))


def status_label(value: str) -> str:
    return STATUS_LABELS.get(value, value.replace("_", " "))


def ui_label(value: str) -> str:
    return UI_LABELS.get(value, value.replace("_", " "))


def div_label(value: str) -> str:
    if not value or value == "none":
        return "none"
    return "; ".join(DIV_LABELS.get(part, part.replace("_", " ")) for part in value.split(";"))


def write_prompt_bank(rows: list[dict[str, str]]) -> None:
    lines = [
        r"\begingroup",
        r"\setlength{\tabcolsep}{2pt}",
        r"\begin{small}",
        r"\begin{longtable}{@{}L{0.07\linewidth}L{0.13\linewidth}L{0.14\linewidth}L{0.07\linewidth}L{0.13\linewidth}L{0.38\linewidth}@{}}",
        r"\caption[Redacted 60-prompt scale-up bank]{Redacted 60-prompt scale-up bank. Category B prompt text remains redacted in shared thesis artifacts; the private local bank contains executable collection text.}\\",
        r"\toprule",
        r"ID & Source & Category & Risk & Expected & Shared prompt or descriptor \\",
        r"\midrule",
        r"\endfirsthead",
        r"\caption[]{Redacted 60-prompt scale-up bank (continued).}\\",
        r"\toprule",
        r"ID & Source & Category & Risk & Expected & Shared prompt or descriptor \\",
        r"\midrule",
        r"\endhead",
        r"\bottomrule",
        r"\endfoot",
    ]
    for row in rows:
        cells = [
            row["prompt_id"],
            source_label(row["source"]),
            category_label(row, include_id=True),
            RISK_LABELS.get(row["risk_level"], row["risk_level"]),
            expected_label(row["expected_response_class"]),
            row["prompt_text_or_redacted_text"],
        ]
        lines.append(" & ".join(tex(cell) for cell in cells) + r" \\")
    lines += [r"\end{longtable}", r"\end{small}", r"\endgroup"]
    (OUT / "appendix_prompt_bank.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_substantive(rows: list[dict[str, str]]) -> None:
    lines = [
        r"\begingroup",
        r"\setlength{\tabcolsep}{2pt}",
        r"\begin{small}",
        r"\begin{longtable}{@{}L{0.07\linewidth}L{0.18\linewidth}L{0.23\linewidth}L{0.44\linewidth}@{}}",
        r"\caption[Final 17 substantive API/app divergence cases]{Final 17 substantive API/app divergence cases after prompt-echo cleaning and screenshot-backed corrections.}\\",
        r"\toprule",
        r"ID & Category & Final divergence type & Claim-safe interpretation \\",
        r"\midrule",
        r"\endfirsthead",
        r"\caption[]{Final substantive divergence cases (continued).}\\",
        r"\toprule",
        r"ID & Category & Final divergence type & Claim-safe interpretation \\",
        r"\midrule",
        r"\endhead",
        r"\bottomrule",
        r"\endfoot",
    ]
    for row in rows:
        if row["substantive_divergence"] != "yes":
            continue
        summary = row["claim_safe_summary"]
        summary = summary.replace("local_context", "local context")
        summary = summary.replace("sources_visible", "visible sources")
        summary = summary.replace("full_refusal", "full refusal")
        summary = summary.replace("partial_refusal_or_safe_redirect", "partial/safe redirect")
        summary = summary.replace("expected_supported", "expected supported")
        summary = summary.replace("possible_factual_mismatch", "possible factual mismatch")
        cells = [
            row["prompt_id"],
            category_label(row),
            div_label(row["final_divergence_type"]),
            summary,
        ]
        lines.append(" & ".join(tex(cell) for cell in cells) + r" \\")
    lines += [r"\end{longtable}", r"\end{small}", r"\endgroup"]
    (OUT / "appendix_substantive_cases.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_reviewed(rows: list[dict[str, str]]) -> None:
    lines = [
        r"\begingroup",
        r"\setlength{\tabcolsep}{2pt}",
        r"\begin{scriptsize}",
        r"\begin{longtable}{@{}L{0.06\linewidth}L{0.05\linewidth}L{0.13\linewidth}L{0.12\linewidth}L{0.14\linewidth}L{0.10\linewidth}L{0.06\linewidth}L{0.24\linewidth}@{}}",
        r"\caption[Reviewed API/app coding summary for all 60 prompts]{Reviewed API/app coding summary for all 60 paired prompts. The table reports final claim-safe labels only, not raw high-risk prompt or output text.}\\",
        r"\toprule",
        r"ID & Cat. & Source & API refusal & App refusal & App UI & Subst. & Final divergence type \\",
        r"\midrule",
        r"\endfirsthead",
        r"\caption[]{Reviewed API/app coding summary (continued).}\\",
        r"\toprule",
        r"ID & Cat. & Source & API refusal & App refusal & App UI & Subst. & Final divergence type \\",
        r"\midrule",
        r"\endhead",
        r"\bottomrule",
        r"\endfoot",
    ]
    for row in rows:
        cells = [
            row["prompt_id"],
            row["category_id"],
            source_label(row["source"]),
            status_label(row["api_refusal_status"]),
            status_label(row["app_refusal_status"]),
            ui_label(row["app_ui_surface_signature"]),
            row["substantive_divergence"],
            div_label(row["final_divergence_type"]),
        ]
        lines.append(" & ".join(tex(cell) for cell in cells) + r" \\")
    lines += [r"\end{longtable}", r"\end{scriptsize}", r"\endgroup"]
    (OUT / "appendix_reviewed_coding_summary.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_cross(reviewed: list[dict[str, str]], api_rows: list[dict[str, str]]) -> None:
    by_prompt: dict[str, dict[str, dict[str, str]]] = defaultdict(dict)
    for row in api_rows:
        by_prompt[row["prompt_id"]][row["channel_key"]] = row
    lines = [
        r"\begingroup",
        r"\setlength{\tabcolsep}{2pt}",
        r"\begin{scriptsize}",
        r"\begin{longtable}{@{}L{0.06\linewidth}L{0.05\linewidth}L{0.13\linewidth}L{0.12\linewidth}L{0.14\linewidth}L{0.13\linewidth}L{0.13\linewidth}L{0.07\linewidth}@{}}",
        r"\caption[Cross-channel refusal-status matrix]{Cross-channel refusal-status matrix. Claude and Gemini are API-only robustness baselines; only OpenAI API versus ChatGPT app is a channel comparison.}\\",
        r"\toprule",
        r"ID & Cat. & Source & OpenAI API & ChatGPT app & Claude API & Gemini API & Subst. \\",
        r"\midrule",
        r"\endfirsthead",
        r"\caption[]{Cross-channel refusal-status matrix (continued).}\\",
        r"\toprule",
        r"ID & Cat. & Source & OpenAI API & ChatGPT app & Claude API & Gemini API & Subst. \\",
        r"\midrule",
        r"\endhead",
        r"\bottomrule",
        r"\endfoot",
    ]
    for row in reviewed:
        prompt_id = row["prompt_id"]
        api = by_prompt[prompt_id]
        cells = [
            prompt_id,
            row["category_id"],
            source_label(row["source"]),
            status_label(row["api_refusal_status"]),
            status_label(row["app_refusal_status"]),
            status_label(api.get("claude_api", {}).get("refusal_status", "")),
            status_label(api.get("gemini_api", {}).get("refusal_status", "")),
            row["substantive_divergence"],
        ]
        lines.append(" & ".join(tex(cell) for cell in cells) + r" \\")
    lines += [r"\end{longtable}", r"\end{scriptsize}", r"\endgroup"]
    (OUT / "appendix_cross_channel_matrix.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    OUT.mkdir(exist_ok=True)
    prompt_rows = read_csv(PROJECT / "data" / "prompts" / "prompt_bank_60.csv")
    reviewed_rows = read_csv(ANALYSIS / "scaleup_human_reviewed_coding_sheet.csv")
    api_rows = read_csv(ANALYSIS / "api_only_results_summary.csv")
    write_prompt_bank(prompt_rows)
    write_substantive(reviewed_rows)
    write_reviewed(reviewed_rows)
    write_cross(reviewed_rows, api_rows)
    print("Regenerated appendix tables in", OUT)


if __name__ == "__main__":
    main()
