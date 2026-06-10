# Divergence Moderator Analysis (existing 60-pair data, no new collection)

Base: cleaned, screenshot-corrected human-reviewed coding sheet (`results/analysis/scaleup_human_reviewed_coding_sheet.csv`), joined to the frozen prompt bank for ordinal risk level. Outcome = *substantive* divergence (`substantive_divergence == yes`). N = 60 pairs, 17 substantive (28%, Wilson 95% [0.185, 0.408]).

## 1. Divergence is concentrated by benchmark category

Chi-square test of independence (category x substantive): chi2 = 12.02, df = 5, p = 0.0345, Cramer's V = 0.45 (n = 60).

| Category | substantive / n | rate | Wilson 95% |
|---|---|---|---|
| disallowed_refusal_expected | 6/10 | 0.60 | [0.31, 0.83] |
| boundary_safety_framing | 4/10 | 0.40 | [0.17, 0.69] |
| neutral_factual_control | 4/10 | 0.40 | [0.17, 0.69] |
| allowed_sensitive_over_refusal | 2/12 | 0.17 | [0.05, 0.45] |
| instruction_following | 1/8 | 0.12 | [0.02, 0.47] |
| social_recommendation | 0/10 | 0.00 | [0.00, 0.28] |

Fisher exact, refusal-expected vs other categories (odds ratio, Haldane-corrected):

- disallowed_refusal_expected_vs_boundary_safety_framing: p = 0.6563, OR = 2.09
- disallowed_refusal_expected_vs_neutral_factual_control: p = 0.6563, OR = 2.09
- disallowed_refusal_expected_vs_allowed_sensitive_over_refusal: p = 0.0743, OR = 6.07
- disallowed_refusal_expected_vs_instruction_following: p = 0.0656, OR = 7.22
- disallowed_refusal_expected_vs_social_recommendation: p = 0.0108, OR = 30.33

## 2. Divergence rises with prompt risk level (ordinal trend)

Cochran-Armitage trend (low<medium<high): z = 1.79, two-sided p = 0.0729.

| Risk | substantive / n | rate | Wilson 95% |
|---|---|---|---|
| low | 7/30 | 0.23 | [0.12, 0.41] |
| medium | 4/20 | 0.20 | [0.08, 0.42] |
| high | 6/10 | 0.60 | [0.31, 0.83] |

## 3. Source family

Chi-square (source family x substantive): chi2 = 20.65, df = 7, p = 0.0043, Cramer's V = 0.59.

| Source family | substantive / n | rate |
|---|---|---|
| HarmBench | 3/3 | 1.00 |
| SimpleQA | 4/6 | 0.67 |
| Do-Not-Answer | 3/7 | 0.43 |
| AILuminate | 4/10 | 0.40 |
| XSTest | 2/12 | 0.17 |
| IFEval | 1/8 | 0.12 |
| BBQ | 0/10 | 0.00 |
| TruthfulQA | 0/4 | 0.00 |

## 4. UI-surface signatures are an app-only affordance

The app exposed a UI surface (visible sources or localized context) in 15/60 pairs (25%, Wilson 95% [0.16, 0.37]): 8 with visible sources, 7 with localized context. The API channel showed such surfaces in 0/60 pairs by construction.

## 5. Divergence-type frequency

- safety_framing: 22
- ui_surface_signature: 12
- refusal_status: 6
- factuality: 3
- format_compliance: 1
- verbosity: 1

### Interpretation (claim-safe)

These are *associations between prompt-level properties and observable channel divergence*, not causal claims about hidden prompts, routing, or moderation. The category and risk-level patterns indicate that the access channel matters most precisely where safety behavior and retrieval are at stake, and is negligible on neutral social-recommendation prompts -- which is the expected signature of an access-layer effect rather than random noise.
