# Scripts

Scripts in this folder must be generic and reusable.

Prompt templates for judgment-heavy stages live under `templates/`.

## Rule

Scripts here must:

- accept run-specific inputs from a run folder
- write outputs using the shared workflow schemas
- avoid hardcoded topic logic
- avoid hardcoded references to Krogan, AP-MS, or any other specific example

## Allowed assumptions

Scripts may assume:

- a run folder exists under `runs/<run_id>/`
- standard input files such as `request.md`, `instruction.md`, and `topic.md` may exist
- output templates and schemas live in the workflow root
- run artifacts may live under `runs/<run_id>/artifacts/`

## Disallowed assumptions

Scripts must not assume:

- a fixed virus list
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
  Initialize a run folder with canonical artifact placeholders.
- `validate_run.py <run_id>`
  Check that a run has the expected inputs and outputs, valid schema values,
  complete review decisions, consistent stage handoffs, and readable normalized
  file pointers.
- `collect_pubmed.py <run_id>`
  Read the run search strategy and collect PubMed title/abstract metadata into the run artifact folder.
- `prepare_abstract_review.py <run_id>`
  Convert the collected paper manifest into an abstract review table for the reviewer role.
- `prepare_abstract_review2.py <run_id>`
  Convert the first abstract reviewer table into an `abstractReviewer2` table for second-pass review.
- `prepare_import_status.py <run_id>`
  Build the full-text import working set from `advance_to_import` papers and enrich PMCID coverage.
- `import_pmc_fulltext.py <run_id>`
  Download PMC XML for PMCID-backed papers, normalize usable XML to JSON, and emit a manual PDF queue for fallback.
- `prepare_fulltext_review.py <run_id>`
  Convert usable normalized full-text imports into the `fulltext_review.csv` working table.
- `build_pdf_intervention.py <run_id>`
  Build the PDF intervention state and user-facing prompt from `run_config.md`, `import_status.csv`, and the manual PDF queue.
- `stage_manual_pdfs.py <run_id> [downloads_dir]`
  Scan a user-provided PDF folder, move matched PDFs into the run-owned PDF store as `PMID <pmid>.pdf`, update `import_status.csv`, shrink `manual_pdf_queue.csv`, and write `manual_pdf_import_report.csv`.
- `ingest_manual_pdfs.py <run_id> [downloads_dir]`
  Run the full reusable manual-PDF ingest refresh: stage matching PDFs, parse newly staged PDFs through GROBID, rebuild `fulltext_review.csv`, regenerate reports, and report how many normalized papers still lack a final keep/drop judgment. In agent-driven use, ingest is only operationally complete when that pending count is driven to zero or the remaining unresolved papers are blocked by access rather than review.
- `parse_pdf_fulltext.py <run_id>`
  Parse staged PDFs through GROBID using `GROBID_URL` or `GROBID_BASE_URL` when set, normalize common URL variants such as `/api` or `/api/processFulltextDocument`, otherwise probe reachable local endpoints such as `http://localhost:8070`, normalize TEI to JSON, update `import_status.csv`, and write `pdf_parse_report.csv`.
- `generate_reports.py <run_id>`
  Build `progress_report.md` and `final_reading_list.csv` from the current run artifacts.
- `prescreen_abstracts.py <run_id>`
  Apply lightweight generic run-term overlap hints before deeper review.
  This script must not write `review_decision`; it only writes optional
  `prescreen_*` fields for reviewer context.

PubMed query refinement is intentionally part of the `pubmedKeywordScout` agent role, not a deterministic script.
