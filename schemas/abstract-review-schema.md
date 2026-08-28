# Abstract Review Schema

## Fields

- `paper_id`
- `pmid`
- `doi`
- `title`
- `abstract`
- `publication_types`
  Semicolon-separated values from PubMed `PublicationTypeList`; use this to preserve clinical-trial publication-type evidence during abstract triage.
- `year`
- `source_query`
- `review_decision`
  Allowed: `include`, `exclude`
- `review_rationale`
- `review_confidence`
  Allowed: `high`, `medium`, `low`
- `topic_match_type`
  Suggested: `direct`, `indirect`, `background_only`
- `reviewer_type`
  Suggested: `agent`, `human`, `hybrid`
- `prescreen_hint`
  Optional. Suggested: `possible_include`
- `prescreen_rationale`
  Optional.
- `prescreen_overlap_terms`
  Optional semicolon-separated run-term overlaps.

## Notes

This schema is optimized for title-and-abstract triage, not final scientific truth.
Pre-screening may add hints, but it must not populate or override reviewer
decisions. Only an abstract reviewer should write `review_decision`.
