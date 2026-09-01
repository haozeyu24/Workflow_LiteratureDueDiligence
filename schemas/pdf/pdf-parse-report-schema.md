# PDF Parse Report Schema

One row per staged PDF considered for parser-based normalization.

Required columns:

- `paper_id`
- `pmid`
- `doi`
- `title`
- `pdf_path`
- `tei_path`
- `normalized_path`
- `parse_status`
  Allowed: `normalized`, `parser_pending`, `parse_failed`, `missing_pdf`
- `notes`
