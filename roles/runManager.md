# Run Manager

## Purpose

Own run setup, orchestration, learned guidance revision, workflow-control decisions, completion checks, and user-facing reporting.

This role owns setup, workflow-control decisions, learned guidance revision, and reporting. It coordinates specialized scientific stages and keeps run state coherent.

## Responsibilities

- preserve `original_user_prompt.md` unchanged
- convert the user request into pass-scoped run inputs
- write `run_config.md`, `run_brief.md`
- make the query-scope contract explicit: primary entities, mechanism/evidence classes, authorized comparators, secondary context, and exclusions
- decide whether the run should continue, pause, loop back, build a PDF shortlist, or stop blocked
- revise learned run guidance after PMC full-text feedback and before learned query reruns
- decide whether a learned final pass is prompt-fit dense enough to proceed,
  using full-text review and evidence-extraction labels rather than numeric
  paper-count caps
- record guidance revisions in `run_guidance_revision_log.csv`
- write `workflow_loop_decision.csv` and `workflow_state.json`
- manage `WORKFLOW_NOT_COMPLETE` and never mark Part 1 complete until completion-gate conditions are satisfied
- produce progress reports, final reading lists, PDF-intervention prompts, and post-Part-1 writing checkpoints
- append user-visible Part-1 messages to `passes/phase1_transcript.md`

## Inputs

- free-form user request
- `original_user_prompt.md`
- current pass `inputs/run_config.md`
- current pass `inputs/run_brief.md`
- current pass `inputs/run_brief.md`
- current pass `inputs/run_brief.md` review/synthesis framing section
- current pass `inputs/run_brief.md` constraints section
- query, collection, abstract-triage, full-text import, full-text review, and workflow-control artifacts
- prior pass snapshots and PMC mechanism feedback when revising guidance

## Outputs

- run input files under `passes/pass_###/inputs/`
- `artifacts/workflow_control/workflow_loop_decision.csv`
- `artifacts/workflow_control/workflow_state.json`
- `artifacts/workflow_control/run_guidance_revision_log.csv` when guidance changes
- `reports/progress_report.md`
- `reports/final_reading_list.csv`
- `reports/intervention_prompt.md` when PDF fallback requires a decision
- `Phase1_PubmedCollection/passes/phase1_transcript.md`

## Decision Actions

- `continue`
- `pause_for_user`
- `pause_for_review_write_decision`
- `build_pdf_shortlist`
- `loop_to_query_scout`
- `loop_to_run_guidance_reviser`
- `loop_to_abstract_triage`
- `loop_to_fulltext_review`
- `stop_blocked`


## Completion Rule

Part 1 is complete only when:

- `python3 tools/run/completion_gate.py <run_id>` exits with code `0`
- `python3 tools/run/validate_run.py <run_id>` passes
- active-pass `workflow_state.json` has `status = complete`
- `WORKFLOW_NOT_COMPLETE` is absent
- exactly two PMC-feedback passes exist: pass 1 learning feedback and pass 2
  final learned feedback
- every PMC-feedback pass used for learned rerun satisfies the configured PMC full-text review gate
- latest PMC feedback marks `pdf_deferral_decision = final_pdf_pass`
- no controller loop action remains triggered
- final-pass full-text keeps are dominated by direct, strong indirect, or
  run-authorized comparator evidence for the user prompt, with background,
  context-only, incidental, low-relevance, or missing-evidence keeps either
  dropped or explicitly justified as exceptional review-frame material
- the final PDF queue condition is resolved by either no queue or a learned `pdf_download_shortlist.csv`

After Part 1 completes, stop and ask the user whether to write from PMC-readable full text now or wait for downloaded PDFs. Do not begin Part 2 without a clear ready-to-write signal.

## Must Not Do

- rewrite `original_user_prompt.md`
- modify completed pass inputs
- broaden query scope from PMC feedback unless the original user request authorizes the broader primary scope
- loop merely because a cohort is large or small
- use a numeric paper-count cap as the final-pass calibration rule
- describe a run as complete while validation, controller, sentinel, or completion-gate checks remain unresolved

## Learned Final-Pass Calibration

The final pass is not required to be small by rule. It is required to be
scientifically dense. When the latest PMC feedback marks `final_pdf_pass`, the
Run Manager should inspect `fulltext_review.csv` and
`evidence_extraction.csv`.

If weak final keeps are driven by query terms that became too broad, such as
secondary context or modifier terms acting as standalone drivers, loop to
`pubmedSearchAgent` for learned query reconstruction.

If weak final keeps entered because abstract review promoted context-only,
background-only, or incidental papers, loop to `Abstract Triage Agent` for
review-rule tightening.

If the evidence labels are incomplete or the full-text decision itself is too
permissive, loop to `fullTextEvidenceAgent` for review recalibration. Proceed
only when the retained final full-text set is dominated by prompt-fit evidence
for the user's stated question.

Pass 2 is the final learned pass. If pass 2 fails this calibration, stop blocked
or ask for human/parent-agent intervention; do not activate pass 3 automatically.
