# Inter-Rater Reliability - One-Page Plan for Aleksandra

## Goal

Measure whether behavioral coding labels are applied consistently on the final
60-prompt access-channel audit.

## What Gets Double-Coded

Six labels on each response:

- `refusal_status`
- `safety_framing_strength`
- `format_compliance`
- `unsupported_inference`
- `factuality` (factual controls only)
- `ui_surface_signature` (consumer app only)

## Current Sampling

- **Prepared sample:** 27 prompts / 54 coding units from the cleaned 60-prompt
  scale-up.
- Includes all final substantive divergence prompts.
- Adds non-divergent controls and oversamples judgement-heavy categories
  (A, B, C, E).
- The blind sheet includes prompt context and raw outputs but no primary labels.

## Coders

1. **Preferred:** Tillo + SCG-approved second coder (Aleksandra or designated group member).
2. **Fallback:** Tillo delayed self-recoding after at least 7 days (report as intra-coder reliability, not true IRR).

## Metric

Cohen's kappa per label. Report weighted kappa for ordered labels (safety framing).

| Kappa | Interpretation |
| ---: | --- |
| < 0.40 | Weak - revise coding guide |
| 0.40-0.60 | Moderate - report limitations |
| 0.60-0.80 | Acceptable for exploratory audit |
| > 0.80 | Strong |

## Process

1. Code independently.
2. Compare and document disagreements.
3. Discuss and resolve.
4. Report reliability on **pre-resolution** labels.
5. Use **resolved** labels in final analysis.

## Current Status

- `second_coder_sheet_BLIND.csv` is ready for an independent coder.
- `second_coder_key_PRIVATE.csv` must stay private until scoring.
- Run `compute_inter_rater_reliability.py` only after the second coder fills the
  six label columns.

Full protocol: `inter_rater_reliability_protocol.md`
