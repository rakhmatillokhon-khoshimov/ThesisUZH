# Order, Prompt-Feature, Style, and Bootstrap Checks — 10 June 2026

Existing data only; exploratory/descriptive. Script: `analyze_order_features_readability.py`.

## 1. Collection-order confound check
- Median session order index: substantive 23 vs other 34.
- Mann-Whitney p = 0.594; first/second-half Fisher p = 0.568.
- No detectable association between collection order and substantive divergence; session drift does not explain the cases.

## 2. Prompt-feature moderators
- Prompt length: median 13 vs 19 words, p = 0.253.
- Interrogative phrasing: 12/17 vs 34/43, Fisher p = 0.511.
- Divergence is carried by prompt *content category*, not by shallow surface features.

## 3. Channel style profile (all 60 prompts)
| Channel | Words | Sentences | Words/sent | Flesch RE | TTR |
|---|---|---|---|---|---|
| OpenAI API | 123 | 9 | 20.0 | 46 | 0.76 |
| ChatGPT app | 241 | 10 | 35.7 | 26 | 0.65 |
| Claude API | 156 | 5 | 47.1 | 11 | 0.70 |
| Gemini API | 436 | 28 | 22.4 | 43 | 0.58 |

## 4. Bootstrap robustness
- Overall 17/60: bootstrap 95% [0.183, 0.4] vs Wilson [0.185, 0.408].
- Tier-1 10/60: bootstrap 95% [0.083, 0.267] vs Wilson [0.093, 0.28].
- Percentile bootstrap and Wilson agree closely; the headline rates are not an
  artifact of the interval method.
