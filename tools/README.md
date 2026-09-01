# Tools

Tools in this folder must be generic and reusable.

Prompt templates for judgment-heavy stages live under `templates/`.

## Rule

Tools here must:

- accept run-specific inputs from a run folder
- write outputs using the shared workflow schemas
- avoid hardcoded topic logic
- avoid hardcoded references to any specific example domain

## Allowed assumptions

Scripts may assume:

- a run folder exists under `runs/<run_id>/`
- standard input files `run_config.md` and `run_brief.md` may exist
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

If a tool needs topic-specific behavior, it should:

1. read that behavior from run inputs
2. derive parameters from those inputs
3. write derived artifacts without changing the script itself

## Current entrypoints

- `run/init_run.py <run_id>`
  Initialize a run folder with `Phase1_PubmedCollection/passes/pass_001/{inputs,artifacts,reports}`, initialize `Phase1_PubmedCollection/workflow_state.sqlite`, record pass 1 as active, and create `Phase1_PubmedCollection/WORKFLOW_NOT_COMPLETE`.
- `run/activate_pass.py <run_id> <pass_number>`
  Create or activate a pass directory such as `Phase1_PubmedCollection/passes/pass_002/`, seed its inputs from the previous pass when available, and record it in `Phase1_PubmedCollection/passes/active_pass.json`. Use this only before a learned rerun writes pass-specific artifacts. For pass 2 or later, this entrypoint refuses activation until the previous pass has completed abstract triage, second abstract-triage pass, and PMC feedback with `pdf_deferral_decision = defer_pdfs`.
- `run/validate_run.py <run_id>`
  Check that a run has the expected inputs and outputs, valid schema values,
  complete review decisions, consistent stage handoffs, and readable normalized
  file pointers. When `artifact_policy = workflow_only`, also reject undeclared
  active-pass artifacts such as ad hoc rankings, exports, helper scripts, or
  side summaries.
- `run/completion_gate.py <run_id>`
  The only approved workflow-completion check. It reruns the Run Manager controller step,
  regenerates reports, runs validation, requires `workflow_state.status =
  complete`, and requires `Phase1_PubmedCollection/WORKFLOW_NOT_COMPLETE` to be
  absent. Before final validation it deletes prior-pass PMC XML and
  PMC-normalized JSON payload files, while preserving structured pass artifacts.
  Use `run/completion_gate.py --check-only <run_id>` for read-only review of the
  current state without Run Manager/report/sentinel/cleanup mutation. Agents and
  harnesses must not report the whole workflow as complete unless the mutating
  gate exits `0`.
- `collection/collect_pubmed.py <run_id>`
  Read the active pass search strategy, page through the full PubMed result set for every accepted query, and collect title/abstract metadata into the active pass artifact folder. For learned reruns where the latest PMC feedback says `defer_pdfs`, this entrypoint refuses to run until `artifacts/workflow_control/run_guidance_revision_log.csv` records that the latest feedback was incorporated into pass-scoped guidance under `passes/pass_###/inputs/` and the learned `search_strategy.md`, including retained terms, rescue terms, demoted context, exclusion enforcement, reviewer-rule changes, and expected burden effect. PubMed collection caps are forbidden; the script refuses `max_results_per_query`, `max_total_results`, `retmax`, or equivalent cap constraints. Also writes query hit counts and non-truncation status to `query_diagnostics.csv`. Learned reruns that exceed the prior pass burden threshold emit confirmation warnings rather than hard failures.
  In pass 2 or later, papers already recorded as rejected in `Phase1_PubmedCollection/workflow_state.sqlite` are filtered before the active pass `paper_manifest.csv` is written, so pass-1 rejected papers do not re-enter learned-pass triage by default.
  The PubMed Search Agent also applies the reusable venue blacklist in
  `resources/journal_blocklist.csv` before writing `paper_manifest.csv`, and
  records blocked rows in `artifacts/metadata_collection/blocked_venue_records.csv`.
  Per-paper PubMed metadata payloads are also stored in SQLite
  `pubmed_records`; `metadata_collection/records/*.json` files are only a
  temporary mirror and may be compacted after collection.
- `run/compact_metadata_records.py <run_id> [--all-passes]`
  Ingest per-paper PubMed JSON mirror files into SQLite `pubmed_records`, update
  manifest `record_path` values to `sqlite://pubmed_records/...`, verify row
  coverage, and remove the JSON mirrors.
- `run/summarize_workflow_db.py <run_id> [pass_number]`
  Print manifest, triage, SQLite PubMed-record, JSON-mirror, active-decision,
  and superseded-row counts so database/file drift is visible.

- `runManager` role
  Judgment-heavy agent stage, not a deterministic script. Before each learned rerun, write revised pass-scoped guidance under `passes/pass_###/inputs/` from `pmc_mechanism_feedback.csv`, then record the change in `artifacts/workflow_control/run_guidance_revision_log.csv`. The revision must transform pass-1 full-text observations into pass-2 focusing behavior: retain, rescue, demote, exclude, and reviewer-rule changes. The next `search_strategy.md` must be generated from this revised guidance plus PMC feedback while staying inside the run's query-scope contract. Do not modify a completed pass's `inputs/run_brief.md`.
- `abstract_triage/prepare_abstract_triage_first_pass.py <run_id>`
  Convert the collected paper manifest into an abstract triage table for the reviewer role.
- `abstract_triage/generate_abstract_review_rules.py <run_id>`
  Generate the active pass abstract-review rule artifact before title/abstract
  decisions are written. Pass 1 rules are derived from the active run inputs and
  search strategy. Later-pass rules additionally incorporate PMC full-text
  learning and run-guidance revision records.
- `abstract_triage/prepare_abstract_triage_second_pass.py <run_id>`
  Convert the first abstract-triage table into an `Abstract Triage Agent` rescue-review table. First-pass includes should advance without being relitigated; first-pass excludes receive a targeted rescue screen for high-value missed clinical, mechanistic, comparator, or review-frame signals.
- `core/workflow_db.py`
  Shared SQLite helper for run-level paper state. The database lives at
  `Phase1_PubmedCollection/workflow_state.sqlite` and records collected papers,
  abstract-triage decisions, and latest cross-pass paper status.
- `run/rebuild_workflow_db.py <run_id>`
  Rebuild `Phase1_PubmedCollection/workflow_state.sqlite` from existing pass
  manifests and rescue-review decisions without rerunning PubMed collection or
  abstract review.
- `fulltext/prepare_import_status.py <run_id>`
  Build the full-text import working set from `advance_to_import` papers and enrich PMCID coverage. By default, `fulltext_lookup_mode = pmc_then_oa_final` uses NCBI PMCID/PMC XML only during early `pmc_learning` and defers slower alternate open-access lookup until `final_access` or `pdf_policy = require_fulltext_completion`. Use `fulltext_lookup_mode = exhaustive_oa` only when early non-PMC OA discovery is worth the extra runtime.
  In later passes, this script first checks earlier-pass usable PMC-normalized
  full text for reappearing papers and reuses those normalized paths instead of
  redownloading PMC XML. The active pass still reruns full-text review under its
  own run guidance.
- `fulltext/import_pmc_fulltext.py <run_id>`
  Download PMC XML for PMCID-backed papers, normalize usable XML to JSON, and emit a manual PDF queue for fallback.
- `fulltext/prepare_fulltext_review.py <run_id>`
  Convert usable normalized full-text imports into the `fulltext_review.csv` working table.
- `fulltext/generate_fulltext_review_rules.py <run_id>`
  Generate the active pass full-text-review rule artifact before keep/drop
  decisions are written. Full-text review must evaluate positive promotion
  signals before demotion or exclusion signals. Clear direct, indirect,
  comparator, or authorized review-frame promotion signals override negative
  terms; papers should be dropped only when they lack sufficient positive
  full-text evidence under the active run brief.
- `fulltext/heuristic_fulltext_rescue_pass.py <run_id>`
  Re-review first-pass full-text drops using the same active full-text review
  rules and promotion-first logic. Write
  `artifacts/fulltext_review/fulltext_rescue.csv`, preserve the original drop
  rationale, record confirmed drops or overturned keeps, and update
  `fulltext_review.csv` plus `evidence_extraction.csv` so downstream reports use
  the rescued final decisions.
- `pdf/build_pdf_intervention.py <run_id>`
  Build the PDF intervention state and user-facing prompt from `run_config.md`, `import_status.csv`, and the manual PDF queue. In `access_phase = pmc_learning`, this defers PDF action so the run can learn from PMC-normalized full text first.
- `pdf/stage_manual_pdfs.py <run_id> [downloads_dir]`
  Scan a user-provided PDF folder, move matched PDFs into the run-owned PDF store as `PMID <pmid>.pdf`, update `import_status.csv`, shrink `manual_pdf_queue.csv`, and write `manual_pdf_import_report.csv`. This entrypoint refuses to run during early `pmc_learning` unless `pdf_policy = require_fulltext_completion`, but allows staging after the latest PMC feedback says `final_pdf_pass` and `pdf_download_shortlist.csv` exists.
- `pdf/ingest_manual_pdfs.py <run_id> [downloads_dir]`
  Run the full reusable manual-PDF ingest refresh: stage matching PDFs, parse newly staged PDFs through GROBID, rebuild `fulltext_review.csv`, regenerate reports, and report how many normalized papers still lack a final keep/drop judgment. This entrypoint refuses to run during early `pmc_learning` unless `pdf_policy = require_fulltext_completion`, but allows ingest after the final-loop PDF shortlist exists. In agent-driven use, ingest is only operationally complete when that pending count is driven to zero or the remaining unresolved papers are blocked by access rather than review.
- `pdf/parse_pdf_fulltext.py <run_id>`
  Parse staged PDFs through GROBID using `GROBID_URL` or `GROBID_BASE_URL` when set, normalize common URL variants such as `/api` or `/api/processFulltextDocument`, otherwise probe reachable local endpoints such as `http://localhost:8070`, normalize TEI to JSON, update `import_status.csv`, and write `pdf_parse_report.csv`. This entrypoint refuses to run during early `pmc_learning` unless `pdf_policy = require_fulltext_completion`, but allows parsing after the final-loop PDF shortlist exists.
- `reports/generate_reports.py <run_id>`
  Build `progress_report.md` and `final_reading_list.csv` from the current run
  artifacts, including evidence-tier and loop-decision summaries when those
  artifacts exist.
- `run/append_phase1_transcript.py <run_id> <speaker>`
  Append a timestamped user-visible message to `runs/<run_id>/Phase1_PubmedCollection/passes/phase1_transcript.md`. Use `--message-file` for multiline content, `--message` for short inline text, or pipe the content on stdin.
- `run/assess_workflow_loops.py <run_id>`
  Read stage artifacts, write `workflow_loop_decision.csv`, update `workflow_state.json`, and snapshot the current pass under `passes/pass_###/`. The Run Manager requires at least two big PMC-feedback passes before final PDF access: one PMC-learning pass and one learned-query rerun. A run is not complete until this state is `complete`; for a final run with a non-empty PDF queue, the completion signal is the generated PDF download shortlist.
- `abstract_triage/prescreen_abstracts.py <run_id>`
  Apply lightweight generic run-term overlap hints before deeper review.
  This script must not write `first_pass_decision`; it only writes optional
  `prescreen_*` fields for reviewer context.

PubMed query refinement is intentionally part of the `pubmedSearchAgent` agent role, not a deterministic script.
The scout should record hit counts, sampled precision, noise classes, missing in-scope concepts, adjacent concepts kept as secondary context, and stop-rule reasoning in `artifacts/search_strategy/query_diagnostics.csv`.
The PubMed Search Agent then fills collection counts and truncation status for the accepted query set.

Full-text review should first write
`artifacts/fulltext_review/fulltext_review_rules.md`, then write
`artifacts/fulltext_review/evidence_extraction.csv`, then run a rescue pass over
first-pass drops before final reporting.
The full-text reviewer must apply promotion-first logic: clear positive
evidence for direct, indirect, comparator, or authorized review-frame retention
overrides negative or demotion signals. Evidence-insufficient categories are
demotion rules, not hard exclusions, unless the paper lacks sufficient positive
evidence.
Before final PDF access, it should also write `artifacts/fulltext_review/pmc_mechanism_feedback.csv` so the next query pass can retain useful in-scope mechanism terms and remove predictable noise. Broader adjacent mechanisms should be preserved as secondary synthesis context unless the run guidance explicitly promotes them to primary retrieval scope.
The full-text review entrypoint should also print a concise scientific-learning
summary to the screen so retained mechanisms, supporting mechanisms, noise,
missing terms, query changes, abstract-review changes, and PDF deferral status
are visible during the run instead of being buried only in CSV artifacts.
The first PMC-learning pass should be slightly permissive at abstract triage so
the full-text reviewer can read enough papers to produce scientific learning.
That learning must include per-paper scientific notes and aggregate guidance for
query construction, abstract-review calibration, rescue-review behavior, and
term demotion in later passes.
When `run_brief.md` includes review/synthesis framing, retrieval should use it sparingly as a recall
safeguard, while abstract and full-text review may use it more strongly to
retain a minority of foundational, field-synthesis, or perspective-gap papers.
The first PMC feedback pass must defer PDFs and trigger a learned rerun through PubMed search, both abstract-triage passes, PMC import, and full-text review. Only the second or later feedback pass can unlock `final_pdf_pass`.
The Run Manager should write `artifacts/workflow_control/workflow_loop_decision.csv` whenever a stage decides to continue, pause, or loop back.
