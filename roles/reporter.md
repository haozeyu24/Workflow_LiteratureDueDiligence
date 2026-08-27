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
- do not describe a run as complete while controller loop actions remain triggered
- in the final PMC-satisfied loop, treat `pdf_download_shortlist.csv` in the report folder as the completion signal before optional PDF ingestion
- follow workflow-required reporting fields and statuses

## Outputs

- `progress_report.md`
- `intervention_prompt.md` when PDF fallback requires a decision
- `pdf_download_shortlist.csv` summary when a PDF queue remains after PMC learning
- `final_reading_list.csv`
