# ThesisAlexandra — Navigation Index

*Last updated: 10 June 2026.* Map of the **canonical/current** artifacts so the
dated sprawl is navigable. When two files look similar, the one listed here is
the one to use.

---

## Start here
| Purpose | File |
|---------|------|
| **Newest: final hardening + 2 new findings (10 Jun)** | `FINAL_HARDENING_20260610.md` |
| Newest findings + your paste task (9 Jun) | `SESSION_FINDINGS_20260609.md` |
| Current unfinished jobs status | `CURRENT_UNFINISHED_JOBS_STATUS_20260609.md` |
| Deep state + plan to submission | `THESIS_STATE_AND_PLAN_20260608.md` |
| This map | `INDEX.md` |
| Latest scale-up status | `meeting_package/scaleup_status_memo_20260608.md` |
| Vendor extension run status | `extension_runs_status_20260608.md` |

## New analyses (9 Jun, no new collection)
| Analysis | Script | Outputs |
|----------|--------|---------|
| Divergence moderators (category/risk/source, Fisher/χ²/Cramér's V/trend) | `analyze_divergence_moderators.py` | `…/analysis_scaleup_cleaned/moderators/` |
| Coding-dependence sensitivity checks | `analyze_coding_dependency_sensitivity.py` | `…/analysis_scaleup_cleaned/sensitivity/` |
| Within-channel repetition stability (Fleiss κ across r1/r2/r3) | `analyze_repetition_stability.py` | `…/analysis_scaleup_cleaned/stability/` |
| Targeted persistence table for high-value rows | `build_targeted_persistence_table.py` | `…/analysis_scaleup_cleaned/stability/targeted_persistence_table.*` |
| Quote-level case-evidence audit for divergent cases | `build_case_evidence_table.py` | `…/analysis_scaleup_cleaned/evidence/`, `thesis_draft/generated/appendix_case_evidence_table.tex` |
| Private second-coder handoff packet | `build_second_coder_sheet.py`, `build_second_coder_handoff_package.py` | `…/analysis_scaleup_cleaned/reliability/second_coder_handoff_PRIVATE.zip` |
| API repetition collectors (resumable, concurrent) | `collect_openai_concurrent.py`, `collect_gemini_concurrent_reps.py` | `pilot_outputs/20260609/reps/` |
| Paste-ready cross-vendor app collection kit | `build_app_collection_kit.py` | `app_collection_kit/` |
| **Four-channel agreement (app's nearest neighbour)** | `analyze_channel_agreement.py` | `…/analysis_scaleup_cleaned/channel_agreement/` |
| **Objective lexical divergence (classifier-independent)** | `analyze_lexical_divergence.py` | `…/analysis_scaleup_cleaned/lexical/` |
| **Automated LLM second-rater (convergent reliability)** | `run_llm_second_coder.py` | `…/analysis_scaleup_cleaned/reliability/llm_second_coder/` |
| **Within- vs between-channel lexical divergence (10 Jun)** | `analyze_within_between_lexical.py` | `…/analysis_scaleup_cleaned/lexical_within_between/` |
| **Refusal-style markers, 4 channels on Category B (10 Jun)** | `analyze_refusal_style_markers.py` | `…/analysis_scaleup_cleaned/refusal_style/` |
| **Extra thesis figures: pipeline, scatter, heatmap (10 Jun)** | `make_additional_figures.py` | `meeting_visuals/*.png` |

Round-2 summary: `NEW_FINDINGS_ROUND2_20260609.md`.

## Supervisor meetings (canonical transcripts)
`AlexandraMeeting1.txt` · `AlexandraMeeting2.txt` · `AlexandraMeeting3.txt` (29 May)
Decision log: `meeting3_decision_log_20260605.md`

## Protocol & design (frozen)
| Thing | File |
|-------|------|
| Registered protocol text | `ThesisProtocol.txt` |
| Prompt taxonomy | `prompt_taxonomy.md` / `prompt_taxonomy.csv` |
| Coding guide (label definitions) | `taxonomy_coding_guide.md` |
| Scale-up plan | `scaleup_plan_20260605.md` |

## Prompt bank (FROZEN, 60 prompts)
| | File |
|-|------|
| Shared/redacted bank | `prompt_bank_60.csv` |
| Private bank (incl. Category B raw) | `prompt_bank_60_private.csv` |
| 20-prompt pilot bank | `pilot_prompt_bank.csv` / `_private.csv` |

## Data — current scale-up (use these)
| Channel | Location | Count |
|---------|----------|------:|
| OpenAI API (core) | `pilot_outputs/20260605/openai_api_scaleup_60/` | 60/60 |
| ChatGPT app (core, raw screenshot OCR) | `pilot_outputs/20260608/chatgpt_app_scaleup_60/` | **60/60** |
| ChatGPT app (cleaned analysis log) | `pilot_outputs/20260608/chatgpt_app_scaleup_60_cleaned/` | **60/60** |
| Claude API (ext) | `pilot_outputs/20260608/claude_api_scaleup_60/` | 60/60 |
| Gemini API (ext) | `pilot_outputs/20260608/gemini_api_scaleup_60/` | 60/60 (thinking disabled) |
| Final analysis output | `pilot_outputs/20260608/analysis_scaleup_cleaned/` | final cleaned scale-up pass (60 pairs) |
| Reliability (2nd coder) | `pilot_outputs/20260608/analysis_scaleup_cleaned/reliability/` | sheet ready; pending independent labels |

Pilot (20-prompt) data lives under `pilot_outputs/20260516`, `20260527`, `20260528`.

## Pipeline scripts (run order)
1. `import_manual_app_log.py` — merge manual app CSV
2. `qa_transcription_scaleup_app.py` — transcription QA
3. `validate_scaleup_app_log.py` — pre-analysis gate (`--allow-partial` for interim)
4. `run_scaleup_analysis_pipeline.py` — score → review → reliability → tables
5. **`run_scaleup_after_app_collection.sh`** — one-command wrapper for 2–4
6. `generate_scaleup_thesis_tables.py` — LaTeX tables for Results

Collection runners: `run_openai_api_pilot.py`, `run_claude_api_pilot.py`
(resumable), `run_gemini_api_pilot.py` (resumable; `GEMINI_DISABLE_THINKING=1`
optional), `collect_claude_concurrent.py` (fast parallel Claude).

Reliability: `build_second_coder_sheet.py` → (coder fills) →
`compute_inter_rater_reliability.py`. See `SECOND_CODER_README.md`.

Statistics & figure: `compute_scaleup_statistics.py` (McNemar exact + Wilson 95%
CIs) → `make_results_figure.py` (results figure). Both wired into
`run_scaleup_after_app_collection.sh` (Steps 5). QA: `clean_app_prompt_echo.py`.
Outputs: `analysis_scaleup_cleaned/scaleup_statistics.json`,
`…/thesis_tables/scaleup_statistics.tex`,
`meeting_visuals/results_divergence_summary.png`.

## Thesis document
`thesis_draft/main.tex` (+ `sections/*.tex`) → `thesis_draft/main.pdf`.
Build: `cd thesis_draft && pdflatex main.tex && pdflatex main.tex`.

## Runbooks
App collection: `scaleup_app_collection_user_runbook.md` ·
ChatGPT text protocol: `clean_chatgpt_text_collection_protocol.md` ·
Reliability protocol: `inter_rater_reliability_protocol.md`

---

## Housekeeping notes
- **Regenerable cruft** (`__pycache__/`, `*.pyc`, LaTeX `*.aux/.log/.out/.nav/.snm/.toc`)
  cannot be deleted from inside this session (mount is delete-protected). To clear it
  yourself: `find ThesisAlexandra -name '__pycache__' -o -name '*.pyc' | xargs rm -rf`
  and delete LaTeX intermediates; all regenerate.
- `meeting_package/` holds **dated snapshots** copied for supervisor review.
  Treat files dated `20260528`/`20260529`/`20260605` as historical; the
  `20260608` versions and the live `pilot_outputs/20260608/` are current.
- `meeting_package/*_template.csv` and `scaleup_templates/` are blank schemas, not data.
