# Progress Report

## Run

- `run_id`: `pax8_regulation_20260826`

## Current stage

- full-text review completed for at least part of the normalized corpus
- final reading list updated

## Counts

- papers retrieved: `799`
- abstract includes: `71`
- PMC usable: `25`
- PMC unusable: `13`
- no PMC access: `32`
- PDF needed: `45`
- PDF-needed papers deferred by PMC-learning phase: `45`
- PDF shortlist request count: `45`
- high-priority PDF requests: `45`
- PDF normalized: `0`
- final kept: `22`
- abstract-relevant unreadable papers included in final list: `0`

## Queues

- manual PDF queue: `runs/pax8_regulation_20260826/passes/pass_002/artifacts/fulltext_import/manual_pdf_queue.csv`
- PDF download shortlist: `runs/pax8_regulation_20260826/passes/pass_002/artifacts/fulltext_import/pdf_download_shortlist.csv`
- PDF request shortlist: `runs/pax8_regulation_20260826/passes/pass_002/reports/pdf_request_shortlist.csv`

## Notes

- `access_phase` is `pmc_learning`.
- `abstractReviewer2` advanced `70` papers to import and stopped `729` papers.
- `fullTextImporter` currently has `25` usable PMC papers, `0` normalized PDF papers, and `45` papers still in the manual PDF queue.
- Final-loop `pdf_download_shortlist.csv` requests `45` PDFs, including `45` high-priority PDFs.
- `25` normalized full texts are currently available in `runs/pax8_regulation_20260826/passes/pass_002/artifacts/fulltext_review/fulltext_review.csv`, and `0` unreadable papers are carried in the final list.
- Evidence tiers: `comparator`=22.
- Manual PDFs are deferred in this phase; `45` PDF-needed papers are queued but are not requested from the user yet. Use PMC-readable full text for mechanism feedback and query reconstruction before final PDF access.
- PMC mechanism feedback reviewed `25` papers with PDF decision `final_pdf_pass`. Query changes: No additional query loop recommended. Build final PDF shortlist prioritizing direct PAX8 sumoylation/protein stability, stabilization, and nuclear localization/domain papers, plus highest-value comparator degrader/chaperone/PTM papers not PMC-readable.
- Workflow controller did not trigger a loop.
