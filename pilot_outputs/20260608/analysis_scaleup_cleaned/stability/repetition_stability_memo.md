# Within-Channel Repetition Stability (r1/r2/r3)

Three independent repetitions per channel on the frozen 60-prompt bank. Each repetition's raw output is re-coded with the project's own automated classifiers; we report run-to-run agreement. High agreement means the coded behavior is reproducible and the cross-channel (API-vs-app) divergences are not explained by within-channel stochasticity.

| Channel | Label | Unanimous/n | Unanimous rate | Fleiss kappa |
|---|---|---|---|---|
| openai_gpt-4o | refusal_status | 60/60 | 1.00 | 1.00 |
| openai_gpt-4o | safety_framing | 38/60 | 0.63 | 0.55 |
| claude_sonnet-4 | refusal_status | 56/60 | 0.93 | 0.74 |
| claude_sonnet-4 | safety_framing | 36/60 | 0.60 | 0.57 |

| Channel | Mean answer-length CV |
|---|---|
| openai_gpt-4o | 0.10 |
| claude_sonnet-4 | 0.07 |

### Interpretation (claim-safe)

Refusal status is the audit's primary safety label. Its within-channel run-to-run agreement is the relevant noise floor for the cross-channel refusal divergences reported in the Results chapter. Length varies more than categorical labels, which is why verbosity is treated as a pilot-triage signal and not a substantive divergence label.
