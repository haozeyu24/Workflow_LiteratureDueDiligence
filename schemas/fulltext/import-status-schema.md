# Import Status Schema

## Fields

- `paper_id`
- `pmid`
- `pmcid`
- `doi`
- `title`
- `fulltext_access_route`
  Allowed: `ncbi_pmc_xml`, `europe_pmc_xml`, `oa_pdf`, `none`
- `fulltext_xml_url`
- `fulltext_pdf_url`
- `pmc_access_status`
  Allowed: `available`, `missing`, `not_applicable`
- `pmc_parse_status`
  Allowed: `usable`, `unusable`, `not_attempted`
- `pdf_needed`
  Allowed: `yes`, `no`
- `pdf_import_status`
  Allowed: `imported`, `staged_from_user_download`, `normalized`, `parser_pending`, `parse_failed`, `missing`, `not_attempted`
- `normalized_path`
- `notes`

## Notes

Keep `PMC missing` distinct from `PMC present but unusable`.
