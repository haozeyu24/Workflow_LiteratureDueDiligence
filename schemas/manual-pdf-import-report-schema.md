# Manual PDF Import Report Schema

One row per paper from the manual PDF queue after scanning a user-provided PDF drop folder.

Required columns:

- `paper_id`
- `pmid`
- `doi`
- `title`
- `import_status`
  Allowed: `staged`, `missing`
- `match_method`
  Allowed when staged: `paper_id`, `pmid`, `pmcid`, `doi`,
  `pdf_metadata_pmcid`, `pdf_metadata_doi`, `title_overlap`,
  `pdf_metadata_title`, `author_year_journal`
- `match_score`
- `source_filename`
- `staged_pdf_path`
- `notes`
