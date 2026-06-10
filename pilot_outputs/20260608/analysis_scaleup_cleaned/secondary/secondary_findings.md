# Secondary Findings — Corrected 60-Pair Scale-Up

Generated from existing local artifacts; no new collection was performed.

## Thesis-Safe New Findings

### 1. Manual review was not cosmetic; it changed the evidentiary boundary.

- Automated visible-divergence flags covered 32 rows.
- Of those, 15 became final substantive cases and 17 became minor/non-claim cases.
- Two final substantive cases (S024, S031) were not automated visible-divergence flags; they were caught through UI-surface/manual review.
- No automated visible-divergence flag became fully clean after review; the scorer had high triage value but only 0.469 claim precision.

Interpretation: manual review is a real methods contribution. It both suppresses overclaiming and catches UI-surface cases the automated scorer under-detects.

### 2. The final 17 cases split into two mechanisms: response-core shifts and product-surface shifts.

- Non-UI response-core anchors, counting refusal/factuality/format even when a UI surface is also present: 10/60.
- Cases with no UI-surface label at all: 5/60.
- Pure UI-surface or UI-plus-safety-only cases: 7/60.
- Safety-framing-only cases: 0/60.

Interpretation: the thesis can now say the retained divergences are not a single phenomenon. Some cases are about the response itself; others are expected product affordances such as sources, local context, or the app surface.

### 3. Directionality is asymmetric but not one-dimensional.

- Refusal status: API higher/stricter in 5 rows; app higher/stricter in 1 row(s).
- Safety framing: API higher in 5 rows; app higher in 17 rows.
- Factuality among evaluated factual rows: app better in 3 rows; API better in 0 rows.
- Format compliance: API-only pass/app fail in 1 row; app-only pass/API fail in 0 row.

Interpretation: do not frame the result as simply app = lenient or API = safe. The app is often more contextual/source-supported, while the API can be more refusal-heavy and sometimes more format-compliant.

### 4. App verbosity is real, but verbosity is not the finding.

- App responses were longer in 51/60 pairs; exact sign-test p=3.09e-08.
- Median API output length: 91.5 words; median app output length: 178.5 words; median app-minus-API delta: 86.5 words.
- The social-recommendation negative-control category still had app-longer outputs in 9/10 rows, but 0 final substantive divergences.

Interpretation: length and helpfulness style are background deployment-surface differences, but they are not sufficient for a substantive divergence claim. This supports the conservative coding stance.

## Exploratory Only

- High small-cell rates appear in SimpleQA (4/6), HarmBench (3/3); these are useful for discussion but too small for independent claims.
- BBQ-adapted social rows produced 6 minor cases but 0 substantive cases, reinforcing their role as negative controls rather than positive findings.

## Generated Artifacts

- `secondary_findings.json`
- `mechanism_decomposition.csv`
- `manual_review_yield.csv`
- `directionality_summary.csv`
- `length_analysis.csv`
- `metadata_substantive_rates.csv`
- `secondary_findings_tables.tex`
