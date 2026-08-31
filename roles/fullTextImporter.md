# Full-Text Importer

## Purpose

Acquire, parse, and normalize full text.

## Responsibilities

- use PMC first
- record unusable PMC cases distinctly from missing PMC access
- delete unusable PMC XML artifacts after logging their failure state
- queue papers for manual PDF collection when needed
- build a ranked PDF download shortlist only after PMC-learning feedback marks the run ready for `final_pdf_pass`
- stage user-provided PDFs into the run when the user chooses to provide PDFs
- parse staged PDFs through the shared PDF parser hook when available
- reuse atlas import and normalization logic when available
- follow workflow and policy rules for intervention checkpoints and post-ingest continuation
- in `pmc_learning` mode, keep the PDF queue as deferred access work and continue with PMC-normalized papers for mechanism feedback
- by default, do not run alternate open-access lookup during `pmc_learning`; use
  NCBI PMCID/PMC XML first, and defer Europe PMC/OpenAlex-style PDF discovery
  until `final_access` unless `run_config.md` sets
  `fulltext_lookup_mode = exhaustive_oa` or `pdf_policy = require_fulltext_completion`
- after final PMC-satisfied mechanism feedback, convert the broad PDF queue into `pdf_download_shortlist.csv` regardless of human-facing or agent-facing mode
- in `final_access` + human-facing pause mode, stop after producing the PDF queue and intervention prompt until the user chooses whether to provide PDFs
- in `final_access` + agent-facing continue mode, keep the PDF queue as unresolved access work and continue with readable full text
- after Part 1 completion, do not parse user-provided PDFs for review writing until the user later gives a clear ready-to-write signal
- once that ready-to-write signal is given, parse and normalize the provided PDFs, then hand any newly readable papers back through the usual retention path before reporting how many PDFs were retained for writing

## Outputs

- `import_status.csv`
- `manual_pdf_queue.csv`
- `pdf_download_shortlist.csv`
- `manual_pdf_import_report.csv`
- `pdf_parse_report.csv`
- PMC XML files and normalized JSON when usable
- normalized file pointers

## Must report

- how many PMC papers were usable
- how many PMC papers were unusable
- how many papers lacked PMC access
- how many papers remain unresolved because manual PDF input was unavailable or parser access failed
- how many queued PDFs are recommended for request now versus deferred or not requested

## Must not do

- request, stage, parse, or review manual PDFs during `pmc_learning` unless `run_config.md` explicitly uses `require_fulltext_completion`
- perform exhaustive alternate open-access lookup during `pmc_learning` unless
  `run_config.md` explicitly opts into it
- treat a broad manual PDF queue as a user-facing download request before the controller marks PMC learning ready for `final_pdf_pass`
