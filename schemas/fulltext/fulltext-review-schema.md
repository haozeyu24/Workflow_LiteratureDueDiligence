# Full-Text Review Schema

## Fields

- `paper_id`
- `pmid`
- `pmcid`
- `doi`
- `title`
- `normalized_source_type`
  Allowed: `pmc_xml`, `pdf_grobid`, `missing`
- `normalized_path`
- `fulltext_decision`
  Allowed: `keep`, `drop`
- `fulltext_rationale`
- `mechanistic_relevance`
  Allowed: `high`, `medium`, `low`
- `objective_relevance`
  Allowed: `high`, `medium`, `low`
- `topic_centrality`
  Allowed: `central`, `supporting`, `incidental`
- `review_confidence`
  Allowed: `high`, `medium`, `low`

## Notes

This schema is for final scientific triage after normalization.
The full-text stage is binary by design: every reviewed paper must resolve to `keep` or `drop`.
