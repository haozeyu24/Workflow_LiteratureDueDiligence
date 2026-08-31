# Scripts

Scripts in this folder must be generic and reusable.

Prompt templates for judgment-heavy stages live under `templates/`.

## Rule

Scripts here must:

- accept run-specific inputs from a run folder
- write outputs using the shared workflow schemas
- avoid hardcoded topic logic
- avoid hardcoded references to any specific example domain

## Allowed assumptions

Scripts may assume:

- a run folder exists under `runs/<run_id>/`
- standard input files such as `request.md`, `instruction.md`, `topic.md`, and optional `review_frame.md` may exist
- output templates and schemas live in the workflow root
- run artifacts live under `runs/<run_id>/Phase1_PubmedCollection/passes/pass_###/artifacts/`
- a cross-pass visible transcript may live at `runs/<run_id>/Phase1_PubmedCollection/passes/phase1_transcript.md`

## Disallowed assumptions

Scripts must not assume:

- a fixed entity list
- a fixed laboratory
- a fixed assay type
- a fixed biological question

## Practical interpretation

If a script needs topic-specific behavior, it should:

1. read that behavior from run inputs
2. derive parameters from those inputs
3. write derived artifacts without changing the script itself

## Current entrypoints

- `init_run.py <run_id>`
  Initialize a run folder with `Phase1_PubmedCollection/passes/pass_001/{inputs,artifacts,reports}`, record pass 1 as active, and create `Phase1_PubmedCollection/WORKFLOW_NOT_COMPLETE`.
- `activate_pass.py <run_id> <pass_number>`
  Create or activate a pass directory such as `Phase1_PubmedCollection/passes/pass_002/`, seed its inputs from the previous pass when available, and record it in `Phase1_PubmedCollection/passes/active_pass.json`. Use this only before a learned rerun writes pass-specific artifacts. For pass 2 or later, this entrypoint refuses activation until the previous pass has completed abstract review, second abstract review, and PMC feedback with `pdf_deferral_decision = defer_pdfs`.
- `validate_run.py <run_id>`
  Check that a run has the expected inputs and outputs, valid schema values,
  complete review decisions, consistent stage handoffs, and readable normalized
  file pointers. When `artifact_policy = workflow_only`, also reject undeclared
  active-pass artifacts such as ad hoc rankings, exports, helper scripts, or
  side summaries.
- `completion_gate.py <run_id>`
  The only approved workflow-completion check. It reruns the controller,
  regenerates reports, runs validation, requires `workflow_state.status =
  complete`, and requires `Phase1_PubmedCollection/WORKFLOW_NOT_COMPLETE` to be
  absent. Before final validation it deletes prior-pass PMC XML and
  PMC-normalized JSON payload files, while preserving structured pass artifacts.
  Use `completion_gate.py --check-only <run_id>` for read-only review of the
  current state without controller/report/sentinel/cleanup mutation. Agents and
  harnesses must not report the whole workflow as complete unless the mutating
  gate exits `0`.
- `collect_pubmed.py <run_id>`
  Read the active pass search strategy, page through the full PubMed result set for every accepted query, and collect title/abstract metadata into the active pass artifact folder. For learned reruns where the latest PMC feedback says `defer_pdfs`, this entrypoint refuses to run until `artifacts/workflow_control/run_guidance_revision_log.csv` records that the latest feedback was incorporated into pass-scoped guidance under `passes/pass_###/inputs/` and the learned `search_strategy.md`, including retained terms, rescue terms, demoted context, exclusion enforcement, reviewer-rule changes, and expected burden effect. PubMed collection caps are forbidden; the script refuses `max_results_per_query`, `max_total_results`, `retmax`, or equivalent cap constraints. Also writes query hit counts and non-truncation status to `query_diagnostics.csv`. Learned reruns that exceed the prior pass burden threshold emit confirmation warnings rather than hard failures.
  The collector also applies the reusable venue blacklist in
  `resources/journal_blocklist.csv` before writing `paper_manifest.csv`, and
  records blocked rows in `artifacts/metadata_collection/blocked_venue_records.csv`.

- `runGuidanceReviser` role
  Judgment-heavy agent stage, not a deterministic script. Before each learned rerun, write revised pass-scoped guidance under `passes/pass_###/inputs/` from `pmc_mechanism_feedback.csv`, then record the change in `artifacts/workflow_control/run_guidance_revision_log.csv`. The revision must transform pass-1 full-text observations into pass-2 focusing behavior: retain, rescue, demote, exclude, and reviewer-rule changes. The next `search_strategy.md` must be generated from this revised guidance plus PMC feedback while staying inside the run's query-scope contract. Do not modify a completed pass's `inputs/instruction.md`, `inputs/topic.md`, or `inputs/review_frame.md`.
- `prepare_abstract_review.py <run_id>`
  Convert the collected paper manifest into an abstract review table for the reviewer role.
- `prepare_abstract_review2.py <run_id>`
  Convert the first abstract reviewer table into an `abstractReviewer2` table for second-pass review.
- `prepare_import_status.py <run_id>`
  Build the full-text import working set from `advance_to_import` papers and enrich PMCID coverage. By default, `fulltext_lookup_mode = pmc_then_oa_final` uses NCBI PMCID/PMC XML only during early `pmc_learning` and defers slower alternate open-access lookup until `final_access` or `pdf_policy = require_fulltext_completion`. Use `fulltext_lookup_mode = exhaustive_oa` only when early non-PMC OA discovery is worth the extra runtime.
- `import_pmc_fulltext.py <run_id>`
  Download PMC XML for PMCID-backed papers, normalize usable XML to JSON, and emit a manual PDF queue for fallback.
- `prepare_fulltext_review.py <run_id>`
  Convert usable normalized full-text imports into the `fulltext_review.csv` working table.
- `build_pdf_intervention.py <run_id>`
  Build the PDF intervention state and user-facing prompt from `run_config.md`, `import_status.csv`, and the manual PDF queue. In `access_phase = pmc_learning`, this defers PDF action so the run can learn from PMC-normalized full text first.
- `stage_manual_pdfs.py <run_id> [downloads_dir]`
  Scan a user-provided PDF folder, move matched PDFs into the run-owned PDF store as `PMID <pmid>.pdf`, update `import_status.csv`, shrink `manual_pdf_queue.csv`, and write `manual_pdf_import_report.csv`. This entrypoint refuses to run during early `pmc_learning` unless `pdf_policy = require_fulltext_completion`, but allows staging after the latest PMC feedback says `final_pdf_pass` and `pdf_download_shortlist.csv` exists.
- `ingest_manual_pdfs.py <run_id> [downloads_dir]`
  Run the full reusable manual-PDF ingest refresh: stage matching PDFs, parse newly staged PDFs through GROBID, rebuild `fulltext_review.csv`, regenerate reports, and report how many normalized papers still lack a final keep/drop judgment. This entrypoint refuses to run during early `pmc_learning` unless `pdf_policy = require_fulltext_completion`, but allows ingest after the final-loop PDF shortlist exists. In agent-driven use, ingest is only operationally complete when that pending count is driven to zero or the remaining unresolved papers are blocked by access rather than review.
- `parse_pdf_fulltext.py <run_id>`
  Parse staged PDFs through GROBID using `GROBID_URL` or `GROBID_BASE_URL` when set, normalize common URL variants such as `/api` or `/api/processFulltextDocument`, otherwise probe reachable local endpoints such as `http://localhost:8070`, normalize TEI to JSON, update `import_status.csv`, and write `pdf_parse_report.csv`. This entrypoint refuses to run during early `pmc_learning` unless `pdf_policy = require_fulltext_completion`, but allows parsing after the final-loop PDF shortlist exists.
- `generate_reports.py <run_id>`
  Build `progress_report.md` and `final_reading_list.csv` from the current run
  artifacts, including evidence-tier and loop-decision summaries when those
  artifacts exist.
- `append_phase1_transcript.py <run_id> <speaker>`
  Append a timestamped user-visible message to `runs/<run_id>/Phase1_PubmedCollection/passes/phase1_transcript.md`. Use `--message-file` for multiline content, `--message` for short inline text, or pipe the content on stdin.
- `assess_workflow_loops.py <run_id>`
  Read stage artifacts, write `workflow_loop_decision.csv`, update `workflow_state.json`, and snapshot the current pass under `passes/pass_###/`. The controller requires at least two big PMC-feedback passes before final PDF access: one PMC-learning pass and one learned-query rerun. A run is not complete until this state is `complete`; for a final run with a non-empty PDF queue, the completion signal is the generated PDF download shortlist.
- `prescreen_abstracts.py <run_id>`
  Apply lightweight generic run-term overlap hints before deeper review.
  This script must not write `review_decision`; it only writes optional
  `prescreen_*` fields for reviewer context.

PubMed query refinement is intentionally part of the `pubmedKeywordScout` agent role, not a deterministic script.
The scout should record hit counts, sampled precision, noise classes, missing in-scope concepts, adjacent concepts kept as secondary context, and stop-rule reasoning in `artifacts/search_strategy/query_diagnostics.csv`.
The collector then fills collection counts and truncation status for the accepted query set.

Full-text review should write `artifacts/fulltext_review/evidence_extraction.csv` before final reporting.
Before final PDF access, it should also write `artifacts/fulltext_review/pmc_mechanism_feedback.csv` so the next query pass can retain useful in-scope mechanism terms and remove predictable noise. Broader adjacent mechanisms should be preserved as secondary synthesis context unless the run guidance explicitly promotes them to primary retrieval scope.
When `review_frame.md` exists, retrieval should use it sparingly as a recall
safeguard, while abstract and full-text review may use it more strongly to
retain a minority of foundational, field-synthesis, or perspective-gap papers.
The first PMC feedback pass must defer PDFs and trigger a learned rerun through query scout, collection, both abstract reviewers, PMC import, and full-text review. Only the second or later feedback pass can unlock `final_pdf_pass`.
The Workflow Controller should write `artifacts/workflow_control/workflow_loop_decision.csv` whenever a stage decides to continue, pause, or loop back.
