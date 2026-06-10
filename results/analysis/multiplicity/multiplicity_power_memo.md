# Multiplicity Correction and Power/Floor Analysis

This section pre-empts the two standard objections to a compact audit: many tests on one dataset, and an underpowered primary endpoint. It does not add claims; it disciplines the existing ones.

## 1. Exploratory diagnostics under a narrow FDR family

The primary endpoint (refusal asymmetry) is reported separately. The moderator/association tests below are one narrow exploratory family and are FDR-corrected only as a diagnostic. Because the thesis contains multiple descriptive looks at the same 60 prompts, these q-values are not used as confirmatory evidence.

| Test | raw p | BH q |
|---|---:|---:|
| source-family chi-square | 0.0043 | 0.0216 * |
| refusal-expected vs social-control (Fisher) | 0.0108 | 0.0270 * |
| category chi-square | 0.0345 | 0.0574 (.10) |
| risk-level trend (Cochran-Armitage) | 0.0729 | 0.0806 (.10) |
| lexical Jaccard (Mann-Whitney) | 0.0806 | 0.0806 (.10) |

**Below q<0.05 within this narrow diagnostic family:** source-family chi-square, refusal-expected vs social-control (Fisher). This does not turn them into thesis-confirming results. The category omnibus, the risk-level trend, and the lexical signal remain directional/descriptive. The main text treats all moderator p-values as small-cell, post-hoc pattern checks.

## 2. Primary endpoint: floor and required N

With 5 one-directional discordant pairs the exact two-sided p is 0.0625; the test cannot reach p<.05 until 6 all-one-direction discordant pairs are observed. The result is directional but below the conventional threshold.

At the observed discordance proportion (5/60 = 0.083), roughly 72 prompts would be expected to yield 6 one-directional discordant pairs and cross significance.

The honest reading: the refusal asymmetry is complete in direction (API-only refusals 5, app-only 0), but the design is one event below the exact-test significance floor. This sets a concrete target for a follow-up (about 72 prompts at the observed discordance proportion) without claiming the current endpoint is significant.
