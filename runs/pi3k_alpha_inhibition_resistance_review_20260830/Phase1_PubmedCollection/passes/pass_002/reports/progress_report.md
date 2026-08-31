# Progress Report

## Run

- `run_id`: `pi3k_alpha_inhibition_resistance_review_20260830`

## Current stage

- full-text review completed for at least part of the normalized corpus
- final reading list updated

## Completion Gate

- workflow status: `complete`
- completion signal: `pdf_download_shortlist_ready`
- next action: `report_final_loop`
- controller decision: `no active loop`
- validation result: `passed`
- `WORKFLOW_NOT_COMPLETE` present: `no`
- remaining required stages: `none`

Do not describe this run as `done`, `complete`, `final`, or `finished` unless `python3 scripts/completion_gate.py <run_id>` exits with code `0`.

## Counts

- papers retrieved: `854`
- abstract includes: `330`
- automated full-text usable: `211`
- automated full-text unusable: `33`
- no automated full-text access: `119`
- PDF needed: `43`
- PDF-needed papers deferred by PMC-learning phase: `0`
- PDF shortlist request count: `43`
- high-priority PDF requests: `43`
- PDF normalized: `76`
- final kept: `111`
- abstract-relevant unreadable papers included in final list: `43`

## Queues

- phase 1 transcript: `runs/pi3k_alpha_inhibition_resistance_review_20260830/Phase1_PubmedCollection/passes/phase1_transcript.md`
- manual PDF queue: `runs/pi3k_alpha_inhibition_resistance_review_20260830/Phase1_PubmedCollection/passes/pass_002/artifacts/fulltext_import/manual_pdf_queue.csv`
- PDF download shortlist: `runs/pi3k_alpha_inhibition_resistance_review_20260830/Phase1_PubmedCollection/passes/pass_002/artifacts/fulltext_import/pdf_download_shortlist.csv`
- PDF request shortlist: `runs/pi3k_alpha_inhibition_resistance_review_20260830/Phase1_PubmedCollection/passes/pass_002/reports/pdf_request_shortlist.csv`

## Notes

- `access_phase` is `final_access`.
- Completion gate prerequisites appear satisfied; run completion_gate.py before final user-facing completion claims.
- `abstractReviewer2` advanced `330` papers to import and stopped `524` papers.
- `fullTextImporter` currently has `211` usable automated full-text papers, `76` normalized PDF papers, and `43` papers still in the manual PDF queue.
- Final-loop `pdf_download_shortlist.csv` requests `43` PDFs, including `43` high-priority PDFs.
- `287` normalized full texts are currently available in `runs/pi3k_alpha_inhibition_resistance_review_20260830/Phase1_PubmedCollection/passes/pass_002/artifacts/fulltext_review/fulltext_review.csv`, and `43` unreadable papers are carried in the final list.
- Evidence tiers: `direct`=111, `exclude`=176.
- Final-access PDF queue contains `43` papers; use the PDF shortlist as the calibrated access action list.
- PMC mechanism feedback reviewed `287` papers with PDF decision `final_pdf_pass`. Query changes: Keep primary run terms paired with declared mechanism or evidence terms; use matched retained terms as in-scope anchors and apply noise terms only as safe exclusions.
- Workflow controller did not trigger a loop.
