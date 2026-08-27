# Workflow Controller

## Purpose

Decide whether a run should continue, pause, or loop back after evidence-bearing stages.

## Responsibilities

- read stage metrics and structured artifacts
- identify repeated failure modes
- decide whether the next action is continuation, user pause, or loop-back
- write `workflow_loop_decision.csv`
- give concrete revision instructions to the target role when a loop is triggered
- avoid loops that are only motivated by discomfort with cohort size
- enforce at least two big query-to-PMC-feedback passes before final PDF access
- manage the run-root `WORKFLOW_NOT_COMPLETE` sentinel through `assess_workflow_loops.py`
- never mark `workflow_state.status = complete` unless all completion-gate conditions are satisfied
- fail closed on missing or incomplete required handoff artifacts before evaluating higher-level loop logic

## Inputs

- `run_config.md`
- `constraints.md`
- `artifacts/search_strategy/query_diagnostics.csv`
- `artifacts/abstract_review/abstract_review.csv`
- `artifacts/abstract_review/abstract_review2.csv`
- `artifacts/fulltext_import/import_status.csv`
- `artifacts/fulltext_review/evidence_extraction.csv`
- `artifacts/fulltext_review/pmc_mechanism_feedback.csv`
- `artifacts/fulltext_review/fulltext_review.csv`

## Outputs

- `artifacts/workflow_control/workflow_loop_decision.csv`
- `artifacts/workflow_control/workflow_state.json`
- run-root `WORKFLOW_NOT_COMPLETE` present for incomplete runs and absent only for complete runs

## Decision Actions

- `continue`
  Proceed to the next planned stage.
- `pause_for_user`
  Stop for a human decision, usually for PDF fallback or scope clarification.
- `build_pdf_shortlist`
  Score the manual PDF queue using PMC-learned criteria before any user or parent-agent download request.
- `loop_to_query_scout`
  Revisit query design with explicit PMC-derived mechanism terms, noise classes, missing concepts, or rescue terms.
- `loop_to_run_guidance_reviser`
  Revisit run guidance before query design. Use this when PMC feedback should change `instruction.md`, `topic.md`, reviewer rules, constraints, and then the learned search strategy.
- `loop_to_abstract_review`
  Rerun abstract review when the review criteria were misapplied or too vague.
- `loop_to_fulltext_review`
  Rerun full-text evidence extraction when final keeps/drops are not supported by evidence tiers.
- `stop_blocked`
  Stop when access or external dependencies prevent useful progress.

## Loop Triggers

Trigger a loop only when at least one artifact shows a concrete failure mode:

- `query_noise`
  A query family repeatedly retrieves marker-only, expression-only, clinical-only, or unrelated papers.
- `missing_concept`
  Included or cited papers reveal a concept family missing from the query.
- `reviewer_drift`
  Reviewer rationales are generic, inconsistent, or not reproducible from the provided evidence.
- `weak_final_keeps`
  Many final keeps have `background`, `exclude`, or weak `indirect` evidence tiers.
- `pdf_queue_noise`
  The manual PDF queue is large after PMC learning and the queue is fed by a low-value query family.
- `pmc_learning_query_feedback`
  PMC full-text evidence identifies useful mechanism terms, noise terms, or missing vocabulary that should change the query before PDF effort.
- `access_blocked_high_value`
  High-priority direct papers are unavailable and require human PDF action.
- `missing_pdf_shortlist`
  PMC-learning feedback exists, the manual PDF queue is non-empty, and no learned PDF download shortlist exists.
- `minimum_big_loop_not_satisfied`
  Fewer than `min_big_workflow_loops` PMC-feedback passes exist. This trigger fires even if the latest feedback says `final_pdf_pass`.

## Loop Contract

Every loop decision must include:

- the triggering artifact
- the observed failure mode
- the target stage
- the exact change requested
- the stop condition for the next pass

Do not loop forever.
Use `min_big_workflow_loops` from `run_config.md` when present, but never below `2`.
Use `max_workflow_loops` from `run_config.md` when present; otherwise default to at most `5` expensive end-to-end loop attempts. Values above `5` are invalid.
This limit does not apply to small local refinement loops inside a role, such as query hit-count diagnostics before collection.

## PDF Deferral Rule

Before the final calibrated access pass, a large PDF queue should usually trigger PMC learning and query reconstruction, not a user PDF request.
The controller may ask for PDFs early only when `run_config.md` requires full-text completion or when a small number of high-value unavailable papers are essential to the run objective.
After PMC-learning feedback exists, the controller must require another query/review loop while the latest feedback says `defer_pdfs`.
That loop must target `runGuidanceReviser` first so the revised run guidance and learned search strategy are synchronized.
The controller must also require another query/review loop while fewer than `min_big_workflow_loops` PMC-feedback passes exist, regardless of whether the latest feedback says `final_pdf_pass`.
Require `pdf_download_shortlist.csv` only when the latest PMC feedback says `final_pdf_pass`; the shortlist is the completion signal for the final loop before optional PDF ingestion.

## Completion Rule

The controller owns workflow completion.

It may write `workflow_state.status = complete` only when:

- at least `min_big_workflow_loops` PMC-feedback passes exist
- the latest feedback says `final_pdf_pass`
- no loop trigger remains active
- stage handoff artifacts are complete enough for `validate_run.py` to pass
- the final PDF queue condition is resolved by either no queue or a learned `pdf_download_shortlist.csv`

After writing any non-complete state, `WORKFLOW_NOT_COMPLETE` must exist in the
run root. After writing `complete`, the sentinel must be removed.
