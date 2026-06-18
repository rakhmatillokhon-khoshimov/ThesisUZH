#!/usr/bin/env python3
"""Compute inter-rater reliability between the primary coder and a second coder.

Inputs:
  * the filled BLIND sheet (``second_coder_sheet_BLIND.csv`` with coder2 labels);
  * the private key (``second_coder_key_PRIVATE.csv`` with primary labels).

For each double-coded label it reports Cohen's kappa, percent agreement, N, and
a confusion table. ``safety_framing_strength`` is ordinal, so a linearly
weighted kappa is also reported. No external dependencies.

Safeguard: filled label columns are not enough to make the result true human
inter-rater reliability. By default this script writes a pending-status file if
second-coder labels are present but independence has not been explicitly
confirmed. Use ``--confirm-independent`` only after verifying that the coder did
not see the primary labels/key and did not participate in the primary analysis.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

LABELS = [
    "refusal_status",
    "safety_framing_strength",
    "format_compliance",
    "unsupported_inference",
    "factuality",
    "ui_surface_signature",
]
ORDINAL = {
    "safety_framing_strength": ["none", "light", "moderate", "strong"],
}


def read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


def cohen_kappa(pairs: list[tuple[str, str]]) -> float | None:
    """Unweighted Cohen's kappa for a list of (rater1, rater2) label pairs."""
    n = len(pairs)
    if n == 0:
        return None
    cats = sorted({a for a, _ in pairs} | {b for _, b in pairs})
    idx = {c: i for i, c in enumerate(cats)}
    k = len(cats)
    m = [[0] * k for _ in range(k)]
    for a, b in pairs:
        m[idx[a]][idx[b]] += 1
    po = sum(m[i][i] for i in range(k)) / n
    r = [sum(m[i]) for i in range(k)]
    c = [sum(m[i][j] for i in range(k)) for j in range(k)]
    pe = sum((r[i] / n) * (c[i] / n) for i in range(k))
    if pe == 1:
        return 1.0
    return (po - pe) / (1 - pe)


def weighted_kappa(pairs: list[tuple[str, str]], order: list[str]) -> float | None:
    """Linearly weighted kappa for ordinal labels (values outside order ignored)."""
    order_idx = {v: i for i, v in enumerate(order)}
    p = [(a, b) for a, b in pairs if a in order_idx and b in order_idx]
    n = len(p)
    if n == 0:
        return None
    k = len(order)
    maxd = k - 1
    obs = [[0] * k for _ in range(k)]
    for a, b in p:
        obs[order_idx[a]][order_idx[b]] += 1
    r = [sum(obs[i]) for i in range(k)]
    c = [sum(obs[i][j] for i in range(k)) for j in range(k)]
    num = den = 0.0
    for i in range(k):
        for j in range(k):
            w = abs(i - j) / maxd
            exp = r[i] * c[j] / n
            num += w * obs[i][j]
            den += w * exp
    if den == 0:
        return 1.0
    return 1 - num / den


def confusion(pairs: list[tuple[str, str]]) -> dict:
    cats = sorted({a for a, _ in pairs} | {b for _, b in pairs})
    table = {a: {b: 0 for b in cats} for a in cats}
    for a, b in pairs:
        table[a][b] += 1
    return table


def interpret(kappa: float | None) -> str:
    if kappa is None:
        return "no data"
    if kappa < 0.40:
        return "weak (revise coding guide)"
    if kappa < 0.60:
        return "moderate"
    if kappa < 0.80:
        return "acceptable for exploratory audit"
    return "strong"


def main() -> int:
    ap = argparse.ArgumentParser()
    d = ROOT / "results/analysis/reliability"
    default_blind = d / "second_coder_sheet_BLIND_CODER2.csv"
    if not default_blind.exists():
        default_blind = d / "second_coder_sheet_BLIND.csv"
    ap.add_argument("--blind", type=Path, default=default_blind)
    ap.add_argument("--key", type=Path, default=d / "second_coder_key_PRIVATE.csv")
    ap.add_argument("--out-json", type=Path, default=d / "inter_rater_reliability.json")
    ap.add_argument(
        "--confirm-independent",
        action="store_true",
        help=(
            "Report true human IRR. Use only after confirming the second coder "
            "was genuinely independent and blind to the primary labels/key."
        ),
    )
    args = ap.parse_args()

    blind = {r["coding_unit_id"]: r for r in read_csv(args.blind)}
    key = {r["coding_unit_id"]: r for r in read_csv(args.key)}

    report = {"labels": {}, "n_units_total": len(key)}
    any_coded = False
    for lab in LABELS:
        pairs = []
        for uid, krow in key.items():
            primary = (krow.get(f"primary_{lab}") or "").strip()
            second = (blind.get(uid, {}).get(lab) or "").strip()
            if primary and second:
                pairs.append((primary, second))
        if pairs:
            any_coded = True
        agree = sum(1 for a, b in pairs if a == b) / len(pairs) if pairs else None
        entry = {
            "n": len(pairs),
            "percent_agreement": round(agree, 3) if agree is not None else None,
            "cohen_kappa": None if not pairs else round(cohen_kappa(pairs), 3),
            "confusion": confusion(pairs) if pairs else {},
        }
        if lab in ORDINAL and pairs:
            wk = weighted_kappa(pairs, ORDINAL[lab])
            entry["weighted_kappa"] = round(wk, 3) if wk is not None else None
        entry["interpretation"] = interpret(entry["cohen_kappa"])
        report["labels"][lab] = entry

    if any_coded and not args.confirm_independent:
        report = {
            "method": "guarded_until_independence_confirmed",
            "status": "pending_independence_confirmation",
            "n_units_total": len(key),
            "labels": {},
            "note": (
                "Second-coder label columns are present, but true human IRR is "
                "not reported unless --confirm-independent is passed after "
                "verifying a genuinely blind independent coding process."
            ),
        }
    elif any_coded:
        report["method"] = "true_inter_rater"
        report["status"] = "reported_after_independence_confirmation"
    else:
        report["method"] = "pending_second_coder_labels"
        report["status"] = "pending_second_coder_labels"

    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"Method: {report['method']}")
    if report["labels"]:
        print(f"{'label':28} {'N':>4} {'%agree':>7} {'kappa':>7}  interpretation")
        for lab, e in report["labels"].items():
            pa = "" if e["percent_agreement"] is None else f"{e['percent_agreement']:.2f}"
            kp = "" if e["cohen_kappa"] is None else f"{e['cohen_kappa']:.2f}"
            print(f"{lab:28} {e['n']:>4} {pa:>7} {kp:>7}  {e['interpretation']}")
    else:
        print(report.get("note", "No reportable human IRR values."))
    print(f"\nWrote {args.out_json}")
    if not any_coded:
        print("\nNo second-coder labels found yet. Fill the BLIND sheet, then rerun.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
