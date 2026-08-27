# Progress Report

## Run

- `run_id`: `pax8_regulation_20260826`

## Current stage

- workflow is not complete because one or more controller loops are still triggered
- next stage: execute the triggered loop actions before treating the run as final
- full-text review completed for at least part of the normalized corpus
- final reading list updated

## Counts

- papers retrieved: `540`
- abstract includes: `120`
- PMC usable: `44`
- PMC unusable: `18`
- no PMC access: `56`
- PDF needed: `74`
- PDF-needed papers deferred by PMC-learning phase: `74`
- PDF shortlist request count: `0`
- high-priority PDF requests: `0`
- PDF normalized: `0`
- final kept: `16`
- abstract-relevant unreadable papers included in final list: `0`

## Queues

- manual PDF queue: `runs/pax8_regulation_20260826/passes/pass_001/artifacts/fulltext_import/manual_pdf_queue.csv`
- PDF download shortlist: not generated before final PMC-satisfied loop
- PDF request shortlist: not generated before final PMC-satisfied loop

## Notes

- `access_phase` is `pmc_learning`.
- `abstractReviewer2` advanced `118` papers to import and stopped `422` papers.
- `fullTextImporter` currently has `44` usable PMC papers, `0` normalized PDF papers, and `74` papers still in the manual PDF queue.
- PDF download shortlist has not been generated because PMC learning has not yet reached `final_pdf_pass`.
- `44` normalized full texts are currently available in `runs/pax8_regulation_20260826/passes/pass_001/artifacts/fulltext_review/fulltext_review.csv`, and `0` unreadable papers are carried in the final list.
- Evidence tiers: `comparator`=16.
- Manual PDFs are deferred in this phase; `74` PDF-needed papers are queued but are not requested from the user yet. Use PMC-readable full text for mechanism feedback and query reconstruction before final PDF access.
- PMC mechanism feedback reviewed `44` papers with PDF decision `defer_pdfs`. Query changes: For pass 2, split direct PAX8 rescue queries for SUMO/sumoylation and nuclear-localization/domain language; exclude PAX8-AS1; require PAX-family comparator queries to include phrases such as protein levels, degradation, ubiquitination, SUMOylation, phosphorylation, Hsp90, PROTAC, or nuclear localization near the PAX term; avoid generic paired-box and broad expression terms.
- Workflow loop triggered: `loop_to_run_guidance_reviser` from `fulltext_review` because PMC mechanism feedback recommends run-guidance revision and query reconstruction before PDF effort.; `loop_to_run_guidance_reviser` from `fulltext_review` because Only 1 big PMC-learning pass has completed; the workflow requires at least 2 big passes before final PDF access.; `loop_to_run_guidance_reviser` from `fulltext_import` because Manual PDF queue contains 74 of 118 advanced papers (63%) after PMC learning.
