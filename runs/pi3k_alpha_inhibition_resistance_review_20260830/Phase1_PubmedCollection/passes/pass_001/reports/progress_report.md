# Progress Report

## Run

- `run_id`: `pi3k_alpha_inhibition_resistance_review_20260830`

## Current stage

- workflow is not complete because one or more controller loops are still triggered
- next stage: execute the triggered loop actions before treating the run as final
- full-text review completed for at least part of the normalized corpus
- final reading list updated

## Completion Gate

- workflow status: `loop_required`
- completion signal: ``
- next action: `loop_to_run_guidance_reviser`
- controller decision: `pmc_learning_query_feedback`
- validation result: `failed`
- `WORKFLOW_NOT_COMPLETE` present: `yes`
- remaining required stages: `completion gate`

Do not describe this run as `done`, `complete`, `final`, or `finished` unless `python3 scripts/completion_gate.py <run_id>` exits with code `0`.

## Counts

- papers retrieved: `3681`
- abstract includes: `777`
- automated full-text usable: `488`
- automated full-text unusable: `64`
- no automated full-text access: `289`
- PDF needed: `289`
- PDF-needed papers deferred by PMC-learning phase: `289`
- PDF shortlist request count: `0`
- high-priority PDF requests: `0`
- PDF normalized: `0`
- final kept: `128`
- abstract-relevant unreadable papers included in final list: `0`

## Queues

- phase 1 transcript: `runs/pi3k_alpha_inhibition_resistance_review_20260830/Phase1_PubmedCollection/passes/phase1_transcript.md`
- manual PDF queue: `runs/pi3k_alpha_inhibition_resistance_review_20260830/Phase1_PubmedCollection/passes/pass_001/artifacts/fulltext_import/manual_pdf_queue.csv`
- PDF download shortlist: not generated before final PMC-satisfied loop
- PDF request shortlist: not generated before final PMC-satisfied loop

## Notes

- `access_phase` is `pmc_learning`.
- Completion gate has not passed; this report is a progress artifact, not a final workflow output.
- `abstractReviewer2` advanced `777` papers to import and stopped `2904` papers.
- `fullTextImporter` currently has `488` usable automated full-text papers, `0` normalized PDF papers, and `289` papers still in the manual PDF queue.
- PDF download shortlist has not been generated because PMC learning has not yet reached `final_pdf_pass`.
- `488` normalized full texts are currently available in `runs/pi3k_alpha_inhibition_resistance_review_20260830/Phase1_PubmedCollection/passes/pass_001/artifacts/fulltext_review/fulltext_review.csv`, and `0` unreadable papers are carried in the final list.
- Evidence tiers: `direct`=128, `exclude`=360.
- Manual PDFs are deferred in this phase; `289` PDF-needed papers are queued but are not requested from the user yet. Use PMC-readable full text for mechanism feedback and query reconstruction before final PDF access.
- PMC mechanism feedback reviewed `488` papers with PDF decision `defer_pdfs`. Query changes: Keep primary run terms paired with declared mechanism or evidence terms; use matched retained terms as in-scope anchors and apply noise terms only as safe exclusions.
- Workflow loop triggered: `loop_to_run_guidance_reviser` from `fulltext_review` because PMC mechanism feedback recommends run-guidance revision and query reconstruction before PDF effort.; `loop_to_run_guidance_reviser` from `fulltext_review` because Only 1 big PMC-learning pass has completed; the workflow requires at least 2 big passes before final PDF access.
