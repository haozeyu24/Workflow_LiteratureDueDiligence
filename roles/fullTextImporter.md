# Full-Text Importer

## Purpose

Acquire, parse, and normalize full text.

## Responsibilities

- use PMC first
- record unusable PMC cases distinctly from missing PMC access
- delete unusable PMC XML artifacts after logging their failure state
- queue papers for manual PDF collection when needed
- stage user-provided PDFs into the run when the user chooses to provide PDFs
- parse staged PDFs through the shared PDF parser hook when available
- reuse atlas import and normalization logic when available
- follow workflow and policy rules for intervention checkpoints and post-ingest continuation

## Outputs

- `import_status.csv`
- `manual_pdf_queue.csv`
- `manual_pdf_import_report.csv`
- `pdf_parse_report.csv`
- PMC XML files and normalized JSON when usable
- normalized file pointers

## Must report

- how many PMC papers were usable
- how many PMC papers were unusable
- how many papers lacked PMC access
