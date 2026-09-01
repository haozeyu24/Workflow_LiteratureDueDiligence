# Final Reading List Schema

## Fields

- `paper_id`
- `pmid`
- `pmcid`
- `doi`
- `title`
- `year`
- `publication_types`
  Semicolon-separated values from PubMed `PublicationTypeList`, preserved so clinical trial papers can be identified from final outputs.
- `final_decision`
  Allowed: `selected_for_reading`, `abstract_relevant_fulltext_unavailable`
- `final_rationale`
- `selection_basis`
  Allowed: `fulltext_review`, `abstract_triage_only`
- `fulltext_access_status`
  Allowed: `readable`, `unavailable`, `parser_pending`, `parse_failed`
- `normalized_source_type`
- `normalized_path`
- `review_confidence`

## Notes

This artifact is the main downstream deliverable for human reading and later analysis.
Papers that remain abstract-relevant but lack readable full text must stay visible here rather than being silently treated as irrelevant.
