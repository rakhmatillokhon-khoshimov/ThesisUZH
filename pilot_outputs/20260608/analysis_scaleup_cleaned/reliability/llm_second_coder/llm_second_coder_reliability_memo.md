# Automated LLM Second-Rater Reliability (convergent check)

**Not a substitute for human inter-rater reliability.** An independent model applied the same fixed rubric to the blind coding sheet; its labels are scored against the primary human labels with Cohen's kappa and percent agreement over 54 coding units.

| Label | % agreement | Cohen kappa | n |
|---|---:|---:|---:|
| refusal_status | 0.98 | 0.95 | 54 |
| safety_framing_strength | 0.54 | 0.23 | 54 |
| format_compliance | 0.81 | 0.51 | 54 |
| unsupported_inference | 0.85 | 0.53 | 54 |
| factuality | 0.61 | 0.28 | 54 |
| ui_surface_signature | 0.80 | 0.23 | 54 |
| **pooled** | **0.77** | **0.70** | 324 |

### Interpretation

The decisive refusal-status label is almost perfectly reproducible by an independent rater following the written rubric (Cohen's $\kappa\approx$0.95), which directly supports the core refusal findings; format and unsupported-inference agreement is moderate. The lower agreement on safety-framing strength and especially ui_surface_signature is expected and informative: framing strength is an ordinal judgement, and ui_surface_signature is a *visual* feature the primary coder read from screenshots, whereas this automated rater saw only transcribed text and therefore cannot see source cards or localized UI. Because the second rater is a model, this is reported as convergent validity, not as the human inter-rater reliability the protocol still requires.
