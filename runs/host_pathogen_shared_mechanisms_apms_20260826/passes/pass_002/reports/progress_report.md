# Progress Report

## Run

- `run_id`: `host_pathogen_shared_mechanisms_apms_20260826`

## Current stage

- full-text review completed for at least part of the normalized corpus
- final reading list updated

## Completion Gate

- workflow status: `complete`
- completion signal: `pdf_download_shortlist_ready`
- next action: `report_final_loop`
- controller decision: `no active loop`
- validation result: `failed`
- `WORKFLOW_NOT_COMPLETE` present: `no`
- remaining required stages: `completion gate`

Do not describe this run as `done`, `complete`, `final`, or `finished` unless `python3 scripts/completion_gate.py <run_id>` exits with code `0`.

## Counts

- papers retrieved: `1441`
- abstract includes: `966`
- PMC usable: `515`
- PMC unusable: `270`
- no PMC access: `181`
- PDF needed: `451`
- PDF-needed papers deferred by PMC-learning phase: `0`
- PDF shortlist request count: `451`
- high-priority PDF requests: `451`
- PDF normalized: `0`
- final kept: `471`
- abstract-relevant unreadable papers included in final list: `451`

## Queues

- manual PDF queue: `runs/host_pathogen_shared_mechanisms_apms_20260826/passes/pass_002/artifacts/fulltext_import/manual_pdf_queue.csv`
- PDF download shortlist: `runs/host_pathogen_shared_mechanisms_apms_20260826/passes/pass_002/artifacts/fulltext_import/pdf_download_shortlist.csv`
- PDF request shortlist: `runs/host_pathogen_shared_mechanisms_apms_20260826/passes/pass_002/reports/pdf_request_shortlist.csv`

## Notes

- `access_phase` is `final_access`.
- Completion gate has not passed; this report is a progress artifact, not a final workflow output.
- `abstractReviewer2` advanced `966` papers to import and stopped `475` papers.
- `fullTextImporter` currently has `515` usable PMC papers, `0` normalized PDF papers, and `451` papers still in the manual PDF queue.
- Final-loop `pdf_download_shortlist.csv` requests `451` PDFs, including `451` high-priority PDFs.
- `515` normalized full texts are currently available in `runs/host_pathogen_shared_mechanisms_apms_20260826/passes/pass_002/artifacts/fulltext_review/fulltext_review.csv`, and `451` unreadable papers are carried in the final list.
- Evidence tiers: `background`=41, `direct`=348, `exclude`=3, `indirect`=123.
- Final-access PDF queue contains `451` papers; use the PDF shortlist as the calibrated access action list.
- PMC mechanism feedback reviewed `515` papers with PDF decision `final_pdf_pass`. Query changes: For final PDF triage, replace broad per-virus host pathway/proteomic queries with two-tier query families: (1) primary virus names paired with assay terms: interactome, AP-MS, affinity purification mass spectrometry, proximity proteomics, BioID, protein interaction mapping; (2) primary virus names paired with mechanistic host-factor terms plus action verbs: host factor, restriction factor, dependency factor, entry factor, viral protein-host protein, interacts, binds, recruits, cleaves, degrades, modulates. Keep pathway terms only when paired with a host-factor or viral-protein action anchor. Add rescue queries for CRISPR/RNAi functional genomics host-factor papers. Exclude or strongly downweight patient biomarker omics, plasma/serum proteomics, network pharmacology, molecular docking, vaccine, diagnostic, and epidemiology wording.
- Workflow controller did not trigger a loop.
