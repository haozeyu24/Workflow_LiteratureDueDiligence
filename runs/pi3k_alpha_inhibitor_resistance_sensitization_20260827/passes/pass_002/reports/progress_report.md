# Progress Report

## Run

- `run_id`: `pi3k_alpha_inhibitor_resistance_sensitization_20260827`

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

- papers retrieved: `536`
- abstract includes: `426`
- PMC usable: `265`
- PMC unusable: `28`
- no PMC access: `133`
- PDF needed: `161`
- PDF-needed papers deferred by PMC-learning phase: `0`
- PDF shortlist request count: `12`
- high-priority PDF requests: `12`
- PDF normalized: `0`
- final kept: `265`
- abstract-relevant unreadable papers included in final list: `161`

## Queues

- manual PDF queue: `runs/pi3k_alpha_inhibitor_resistance_sensitization_20260827/passes/pass_002/artifacts/fulltext_import/manual_pdf_queue.csv`
- PDF download shortlist: `runs/pi3k_alpha_inhibitor_resistance_sensitization_20260827/passes/pass_002/artifacts/fulltext_import/pdf_download_shortlist.csv`
- PDF request shortlist: `runs/pi3k_alpha_inhibitor_resistance_sensitization_20260827/passes/pass_002/reports/pdf_request_shortlist.csv`

## Notes

- `access_phase` is `final_access`.
- Completion gate prerequisites appear satisfied; run completion_gate.py before final user-facing completion claims.
- `abstractReviewer2` advanced `426` papers to import and stopped `110` papers.
- `fullTextImporter` currently has `265` usable PMC papers, `0` normalized PDF papers, and `161` papers still in the manual PDF queue.
- Final-loop `pdf_download_shortlist.csv` requests `12` PDFs, including `12` high-priority PDFs.
- `265` normalized full texts are currently available in `runs/pi3k_alpha_inhibitor_resistance_sensitization_20260827/passes/pass_002/artifacts/fulltext_review/fulltext_review.csv`, and `161` unreadable papers are carried in the final list.
- Evidence tiers: `direct`=264, `indirect`=1.
- Final-access PDF queue contains `161` papers; use the PDF shortlist as the calibrated access action list.
- PMC mechanism feedback reviewed `265` papers with PDF decision `final_pdf_pass`. Query changes: No further PubMed rerun recommended. Advance to final PDF pass and prioritize PDF-only papers that mention acquired resistance, allosteric/mutant-selective inhibitors, HER3/ERBB3/IGF feedback, ESR1/PTEN/RB1/NF1 alterations, or sensitizing combinations.
- Workflow controller did not trigger a loop.
