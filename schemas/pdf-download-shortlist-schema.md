# PDF Download Shortlist Schema

One row per PDF-queued paper after PMC-learning has generated mechanism and noise feedback.

This artifact is required whenever `manual_pdf_queue.csv` is non-empty after the final PMC-satisfied full-text learning pass.
It converts the broad fallback queue into a ranked action list for either a human user or a parent agent.

## Fields

- `paper_id`
- `pmid`
- `doi`
- `title`
- `year`
- `publication_types`
  Semicolon-separated values from PubMed `PublicationTypeList`, preserved to identify trial papers in the final access queue.
- `priority`
  Allowed: `high`, `medium`, `low`, `exclude`
- `shortlist_decision`
  Allowed: `request_pdf`, `defer_pdf`, `do_not_request`
- `evidence_category`
  Allowed: `strong_learned_match`, `possible_learned_match`, `comparator_or_model_match`, `access_uncertain`, `noise`
- `learned_criteria_matched`
  Semicolon-separated criteria derived from PMC mechanism feedback.
- `shortlist_rationale`
  Brief explanation of why this paper should or should not be requested.
- `source_query`
- `abstract_reviewer2_decision`
- `promotion_decision`

## Notes

The shortlist is not a hidden filter before abstract review.
It is generated only after full-text learning has satisfied the controller, using the PMC-derived criteria and noise classes from the final loop.
The evidence categories must remain generic. Topic-specific examples belong in
`learned_criteria_matched` and `shortlist_rationale`, not in the reusable schema.

The shortlist should be recall-friendly at the access stage.
If a paper survived `abstractReviewer2` and entered `manual_pdf_queue.csv`, the
default should usually be `request_pdf` unless the final PMC learning indicates
that the paper is explicit noise or clearly outside the learned mechanistic
scope. Uncertain papers should prefer `request_pdf` or at worst `defer_pdf`,
not `do_not_request`, because the real scientific retention decision happens
later from parsed full text.

`manual_pdf_queue.csv` records access state.
`pdf_download_shortlist.csv` records the next access action.
