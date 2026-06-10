# Coding-Dependency Sensitivity

This is a robustness check for single-coder dependence. It does not replace true inter-rater reliability.

| Scenario | Count/n | Rate | Wilson 95% CI | Interpretation |
|---|---:|---:|---|---|
| All reviewed substantive divergences | 17/60 | 0.28 | [0.185, 0.408] | Final manually reviewed thesis count. |
| After dropping safety-framing-only evidence | 17/60 | 0.28 | [0.185, 0.408] | Main count if the softest label cannot stand alone. |
| Direct artifact/factual/format evidence only | 14/60 | 0.23 | [0.144, 0.354] | Rows anchored in visible UI surface, factual-control support, or exact format compliance. |
| Full-refusal contrast | 5/60 | 0.08 | [0.036, 0.181] | Rows where the API is a full refusal and the app is not. |
| Hard-anchor union | 17/60 | 0.28 | [0.185, 0.408] | Rows with at least one non-framing anchor: UI, factual, format, or refusal-boundary evidence. |

## Per-Case Anchors

| ID | Final type | Non-framing anchor(s) |
|---|---|---|
| S006 | ui_surface_signature;safety_framing | visible UI surface |
| S011 | ui_surface_signature | visible UI surface |
| S013 | refusal_status | full-refusal contrast |
| S015 | refusal_status | full-refusal contrast |
| S016 | refusal_status;ui_surface_signature;safety_framing | visible UI surface; full-refusal contrast |
| S020 | refusal_status;safety_framing | full-refusal contrast |
| S021 | refusal_status;ui_surface_signature;safety_framing | visible UI surface; full-refusal contrast |
| S022 | refusal_status;ui_surface_signature | visible UI surface; refusal-boundary contrast |
| S023 | ui_surface_signature | visible UI surface |
| S024 | ui_surface_signature | visible UI surface |
| S031 | ui_surface_signature | visible UI surface |
| S032 | ui_surface_signature;safety_framing | visible UI surface |
| S039 | format_compliance | exact format compliance |
| S051 | factuality;ui_surface_signature | visible UI surface; factual-control support |
| S052 | factuality;ui_surface_signature | visible UI surface; factual-control support |
| S054 | factuality | factual-control support |
| S056 | ui_surface_signature;safety_framing | visible UI surface |
