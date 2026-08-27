# Progress Report

## Run

- `run_id`: `host_pathogen_shared_mechanisms_apms_20260826`

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

- papers retrieved: `4575`
- abstract includes: `3198`
- PMC usable: `1580`
- PMC unusable: `605`
- no PMC access: `1013`
- PDF needed: `1618`
- PDF-needed papers deferred by PMC-learning phase: `1618`
- PDF shortlist request count: `0`
- high-priority PDF requests: `0`
- PDF normalized: `0`
- final kept: `1337`
- abstract-relevant unreadable papers included in final list: `0`

## Queues

- manual PDF queue: `runs/host_pathogen_shared_mechanisms_apms_20260826/passes/pass_001/artifacts/fulltext_import/manual_pdf_queue.csv`
- PDF download shortlist: not generated before final PMC-satisfied loop
- PDF request shortlist: not generated before final PMC-satisfied loop

## Notes

- `access_phase` is `pmc_learning`.
- Completion gate has not passed; this report is a progress artifact, not a final workflow output.
- `abstractReviewer2` advanced `3198` papers to import and stopped `1377` papers.
- `fullTextImporter` currently has `1580` usable PMC papers, `0` normalized PDF papers, and `1618` papers still in the manual PDF queue.
- PDF download shortlist has not been generated because PMC learning has not yet reached `final_pdf_pass`.
- `1580` normalized full texts are currently available in `runs/host_pathogen_shared_mechanisms_apms_20260826/passes/pass_001/artifacts/fulltext_review/fulltext_review.csv`, and `0` unreadable papers are carried in the final list.
- Evidence tiers: `background`=198, `direct`=964, `exclude`=45, `indirect`=373.
- Manual PDFs are deferred in this phase; `1618` PDF-needed papers are queued but are not requested from the user yet. Use PMC-readable full text for mechanism feedback and query reconstruction before final PDF access.
- PMC mechanism feedback reviewed `1580` papers with PDF decision `defer_pdfs`. Query changes: For pass 2, replace broad per-virus host pathway/proteomic queries with two-tier query families: (1) primary virus names paired with assay terms: interactome, AP-MS, affinity purification mass spectrometry, proximity proteomics, BioID, protein interaction mapping; (2) primary virus names paired with mechanistic host-factor terms plus action verbs: host factor, restriction factor, dependency factor, entry factor, viral protein-host protein, interacts, binds, recruits, cleaves, degrades, modulates. Keep pathway terms only when paired with a host-factor or viral-protein action anchor. Add rescue queries for CRISPR/RNAi functional genomics host-factor papers. Exclude or strongly downweight patient biomarker omics, plasma/serum proteomics, network pharmacology, molecular docking, vaccine, diagnostic, and epidemiology wording.
- Workflow loop triggered: `loop_to_run_guidance_reviser` from `fulltext_review` because PMC mechanism feedback recommends run-guidance revision and query reconstruction before PDF effort.; `loop_to_run_guidance_reviser` from `fulltext_review` because Only 1 big PMC-learning pass has completed; the workflow requires at least 2 big passes before final PDF access.; `loop_to_run_guidance_reviser` from `fulltext_import` because Manual PDF queue contains 1618 of 3198 advanced papers (51%) after PMC learning.
