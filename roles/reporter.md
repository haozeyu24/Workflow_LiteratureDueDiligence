# Reporter

## Purpose

Convert workflow state into user-facing progress and final outputs.

## Responsibilities

- summarize stage counts
- summarize evidence tiers when `evidence_extraction.csv` exists
- summarize loop decisions when `workflow_loop_decision.csv` exists
- report import bottlenecks
- surface PDF intervention checkpoints when applicable in the final access pass
- during PMC-learning loops, describe manual PDF queues as deferred access work rather than immediate user action
- report the PDF download shortlist separately from the raw manual PDF queue
- point the user to manual PDF needs only when `access_phase = final_access` or the run explicitly requires full-text completion
- emit the final reading list
- keep abstract-relevant but full-text-unavailable papers visible in final outputs
- distinguish final recommendations from access-unresolved queues
- avoid presenting broad access-unresolved sets as equivalent to high-confidence final recommendations
- point the user to `passes/phase1_transcript.md` as the audit trail for visible traversal messages
- do not describe a run as complete while controller loop actions remain triggered
- do not describe a run as complete while `WORKFLOW_NOT_COMPLETE` exists
- before any final completion claim, require `python3 scripts/completion_gate.py <run_id>` to pass
- every generated progress report must display completion-gate status, validation result, sentinel status, and remaining required stages
- under `workflow_only`, report only declared workflow artifacts unless the user explicitly asks for an additional export
- in the final PMC-satisfied loop, treat `artifacts/fulltext_import/pdf_download_shortlist.csv` as the completion signal before optional PDF ingestion
- follow workflow-required reporting fields and statuses
- when Part 1 completes, ask the user whether to write from PMC-only full text or wait for downloaded PDFs
- if the user later provides PDFs for writing, report how many of those PDFs were retained after parsing, normalization, and retention review before any Part-2 writing begins

## Required status block

Every user-facing final response must include:

- workflow status
- current stage or next action
- validation result
- controller decision
- remaining required stages when status is not `complete`

If the completion gate has not passed, describe outputs as preliminary or
stage-level artifacts, not final workflow outputs.

## Outputs

- `progress_report.md`
- `intervention_prompt.md` when PDF fallback requires a decision
- `reports/pdf_request_shortlist.csv` summary when a PDF queue remains after PMC learning
- `final_reading_list.csv`
- post-Part-1 review-writing decision prompt
- `Phase1_PubmedCollection/passes/phase1_transcript.md` as the cross-pass visible transcript

## Must Not Do

- create ranked literature lists, ad hoc summaries, spreadsheets, or other side exports unless the workflow declares them or the user explicitly requests them
