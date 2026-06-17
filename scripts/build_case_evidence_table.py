#!/usr/bin/env python3
"""Build quote-level evidence tables for the final substantive cases.

The table is an audit aid, not a new scorer. It joins:
  * final human-reviewed case labels;
  * OpenAI API raw outputs;
  * cleaned ChatGPT app outputs;
  * screenshot paths.

Outputs:
  * results/analysis/evidence/case_evidence_table.csv
  * results/analysis/evidence/case_evidence_table.md
  * thesis/generated/appendix_case_evidence_table.tex

High-risk prompt text is never written. Evidence excerpts are short and
claim-oriented so the table can be shared as a verification record without
reproducing unsafe prompts.
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "results" / "analysis"
REVIEWED = ANALYSIS / "scaleup_human_reviewed_coding_sheet.csv"
APP_LOG = ROOT / "data" / "private" / "20260608" / "chatgpt_app_scaleup_60_cleaned" / "chatgpt_app_log_private.csv"
API_RESPONSES = ROOT / "data" / "private" / "20260605" / "openai_api_scaleup_60" / "responses"
OUT = ANALYSIS / "evidence"
TEX_OUT = ROOT / "thesis" / "generated" / "appendix_case_evidence_table.tex"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


def clean_text(text: str) -> str:
    text = (text or "").replace("\n", " ")
    replacements = {
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2013": "-",
        "\u2014": "-",
        "\u2026": "...",
        "\u20ac": "EUR",
        "\u00a0": " ",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    # Common OCR artifact in the app transcripts: a capital I read as a pipe.
    text = re.sub(r"(^|\s)\|\s+(?=can|can't|cannot|would|will|am|was|have|do)\b", r"\1I ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def excerpt(text: str, max_words: int = 18) -> str:
    words = clean_text(text).split()
    if not words:
        return "[empty]"
    out = " ".join(words[:max_words])
    if len(words) > max_words:
        out += " ..."
    return out


def tex_escape(text: str) -> str:
    return (
        text.replace("\\", "\\textbackslash{}")
        .replace("&", "\\&")
        .replace("%", "\\%")
        .replace("$", "\\$")
        .replace("#", "\\#")
        .replace("_", "\\_")
        .replace("{", "\\{")
        .replace("}", "\\}")
        .replace("~", "\\textasciitilde{}")
        .replace("^", "\\textasciicircum{}")
    )


def label(text: str) -> str:
    return (text or "none").replace("_", " ")


def claim(row: dict[str, str]) -> str:
    parts = set(filter(None, row["final_divergence_type"].split(";")))
    claims: list[str] = []
    if "refusal_status" in parts:
        claims.append(
            f"refusal boundary differs: API {label(row['api_refusal_status'])}, "
            f"app {label(row['app_refusal_status'])}"
        )
    if "ui_surface_signature" in parts:
        claims.append(f"app-only UI surface: {label(row['app_ui_surface_signature'])}")
    if "safety_framing" in parts:
        claims.append(
            f"safety framing differs: API {label(row['api_safety_framing'])}, "
            f"app {label(row['app_safety_framing'])}"
        )
    if "factuality" in parts:
        claims.append(
            f"factuality/support differs: API {label(row['api_factuality'])}, "
            f"app {label(row['app_factuality'])}"
        )
    if "format_compliance" in parts:
        claims.append(
            f"format compliance differs: API {label(row['api_format_compliance'])}, "
            f"app {label(row['app_format_compliance'])}"
        )
    return "; ".join(claims) if claims else "substantive observable divergence"


def api_output(prompt_id: str) -> str:
    path = API_RESPONSES / f"{prompt_id}_r1.json"
    if not path.exists():
        return ""
    with path.open(encoding="utf-8", errors="replace") as f:
        return json.load(f).get("raw_output", "") or ""


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    app_by_id = {r["prompt_id"]: r for r in read_csv(APP_LOG)}
    reviewed = [r for r in read_csv(REVIEWED) if r.get("substantive_divergence") == "yes"]
    reviewed.sort(key=lambda r: r["prompt_id"])

    rows: list[dict[str, str]] = []
    for r in reviewed:
        pid = r["prompt_id"]
        app = app_by_id.get(pid, {})
        screenshot = r.get("app_screenshot_path") or app.get("screenshot_path", "")
        screenshot_path = ROOT.parent / screenshot if screenshot and not Path(screenshot).is_absolute() else Path(screenshot)
        api_text = api_output(pid)
        app_text = app.get("raw_output", "")
        rows.append({
            "prompt_id": pid,
            "category": r["category"],
            "final_divergence_type": r["final_divergence_type"],
            "screenshot_path": screenshot,
            "screenshot_exists": str(screenshot_path.exists()).lower(),
            "api_evidence_excerpt": excerpt(api_text),
            "app_evidence_excerpt": excerpt(app_text),
            "final_claim_sentence": claim(r),
        })

    csv_path = OUT / "case_evidence_table.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    md = [
        "# Quote-Level Case Evidence Table",
        "",
        "Short verification table for the 17 final substantive API/app divergence cases. "
        "High-risk prompt text is not reproduced.",
        "",
        "| Prompt | Type | Screenshot | API evidence | App evidence | Final claim |",
        "|---|---|---|---|---|---|",
    ]
    for r in rows:
        md.append(
            f"| {r['prompt_id']} | {r['final_divergence_type']} | "
            f"`{r['screenshot_path']}` ({r['screenshot_exists']}) | "
            f"{r['api_evidence_excerpt']} | {r['app_evidence_excerpt']} | "
            f"{r['final_claim_sentence']} |"
        )
    (OUT / "case_evidence_table.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    tex = [
        "% Script-produced by build_case_evidence_table.py",
        "\\begingroup",
        "\\setlength{\\tabcolsep}{2pt}",
        "\\begin{scriptsize}",
        "\\begin{longtable}{@{}L{0.06\\linewidth}L{0.18\\linewidth}L{0.20\\linewidth}L{0.20\\linewidth}L{0.28\\linewidth}@{}}",
        "\\caption{Quote-level evidence audit for the 17 final substantive cases. Full screenshot paths are stored in the CSV evidence table; this appendix shows shortened verification evidence.}\\\\",
        "\\toprule",
        "ID & Type & API evidence & App evidence & Final checked claim \\\\",
        "\\midrule",
        "\\endfirsthead",
        "\\caption[]{Quote-level evidence audit (continued).}\\\\",
        "\\toprule",
        "ID & Type & API evidence & App evidence & Final checked claim \\\\",
        "\\midrule",
        "\\endhead",
        "\\bottomrule",
        "\\endfoot",
    ]
    for r in rows:
        tex.append(
            f"{tex_escape(r['prompt_id'])} & {tex_escape(label(r['final_divergence_type']))} & "
            f"{tex_escape(r['api_evidence_excerpt'])} & "
            f"{tex_escape(r['app_evidence_excerpt'])} & "
            f"{tex_escape(r['final_claim_sentence'])} \\\\"
        )
    tex.extend(["\\end{longtable}", "\\end{scriptsize}", "\\endgroup"])
    TEX_OUT.write_text("\n".join(tex) + "\n", encoding="utf-8")

    print(f"Wrote {csv_path}")
    print(f"Wrote {OUT / 'case_evidence_table.md'}")
    print(f"Wrote {TEX_OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
