# Progress Report

## Run

- `run_id`: `pi3k_alpha_inhibitor_resistance_sensitization_20260827`

## Current stage

- workflow is not complete because one or more controller loops are still triggered
- next stage: execute the triggered loop actions before treating the run as final
- full-text review completed for at least part of the normalized corpus
- final reading list updated

## Completion Gate

- workflow status: `loop_required`
- completion signal: ``
- next action: `loop_to_abstract_review`
- controller decision: `broad_abstract_promotion`
- validation result: `failed`
- `WORKFLOW_NOT_COMPLETE` present: `yes`
- remaining required stages: `completion gate`

Do not describe this run as `done`, `complete`, `final`, or `finished` unless `python3 scripts/completion_gate.py <run_id>` exits with code `0`.

## Counts

- papers retrieved: `614`
- abstract includes: `574`
- PMC usable: `288`
- PMC unusable: `23`
- no PMC access: `127`
- PDF needed: `150`
- PDF-needed papers deferred by PMC-learning phase: `150`
- PDF shortlist request count: `0`
- high-priority PDF requests: `0`
- PDF normalized: `0`
- final kept: `282`
- abstract-relevant unreadable papers included in final list: `0`

## Queues

- manual PDF queue: `runs/pi3k_alpha_inhibitor_resistance_sensitization_20260827/passes/pass_001/artifacts/fulltext_import/manual_pdf_queue.csv`
- PDF download shortlist: not generated before final PMC-satisfied loop
- PDF request shortlist: not generated before final PMC-satisfied loop

## Notes

- `access_phase` is `pmc_learning`.
- Completion gate has not passed; this report is a progress artifact, not a final workflow output.
- `abstractReviewer2` advanced `438` papers to import and stopped `176` papers.
- `fullTextImporter` currently has `288` usable PMC papers, `0` normalized PDF papers, and `150` papers still in the manual PDF queue.
- PDF download shortlist has not been generated because PMC learning has not yet reached `final_pdf_pass`.
- `288` normalized full texts are currently available in `runs/pi3k_alpha_inhibitor_resistance_sensitization_20260827/passes/pass_001/artifacts/fulltext_review/fulltext_review.csv`, and `0` unreadable papers are carried in the final list.
- Evidence tiers: `background`=1, `direct`=282, `exclude`=5.
- Manual PDFs are deferred in this phase; `150` PDF-needed papers are queued but are not requested from the user yet. Use PMC-readable full text for mechanism feedback and query reconstruction before final PDF access.
- PMC mechanism feedback reviewed `288` papers with PDF decision `defer_pdfs`. Query changes: For pass 2, retain named inhibitor queries but tighten combination retrieval by requiring PI3K-alpha/PIK3CA plus resistance, sensitivity, adaptive feedback, bypass, biomarker, or explicit sensitization terms. Add rescue terms for RTK/ERBB/HER3 feedback, insulin feedback, ESR1/PTEN/RB1/NF1 alterations, vertical pathway inhibition, mutant-selective, and allosteric PI3K-alpha inhibitor response. Exclude network pharmacology, docking, cost-effectiveness, formulation, and non-oncology overgrowth/vascular anomaly-only papers unless linked to resistance or sensitization mechanisms.
- Workflow loop triggered: `loop_to_abstract_review` from `abstract_review` because Abstract review included 93% of retrieved papers and reviewer 2 advanced 71%.; `loop_to_run_guidance_reviser` from `fulltext_review` because PMC mechanism feedback recommends run-guidance revision and query reconstruction before PDF effort.; `loop_to_run_guidance_reviser` from `fulltext_review` because Only 1 big PMC-learning pass has completed; the workflow requires at least 2 big passes before final PDF access.
