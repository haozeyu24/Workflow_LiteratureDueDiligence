# Evidence Extraction Schema

One row per readable full-text paper before final keep/drop reporting.

## Fields

- `paper_id`
- `pmid`
- `title`
- `evidence_tier`
  Allowed: `direct`, `indirect`, `comparator`, `background`, `exclude`
- `evidence_type`
  Run-defined evidence class from the current `topic.md` or `constraints.md`; use a short generic label when the run does not define a vocabulary.
- `directness`
  Allowed: `direct_target`, `same_family_comparator`, `pathway_or_context`, `incidental`
- `target_centrality`
  Allowed: `central`, `supporting`, `incidental`
- `evidence_summary`
  Brief statement of the actual evidence found in the normalized full text.
- `supporting_text_locator`
  Section name, paragraph label, figure/table reference, or short locator that lets a reviewer find the evidence again.
- `query_feedback_signal`
  Allowed: `none`, `tighten_query`, `expand_query`, `add_rescue_query`, `change_scope`, `reviewer_calibration`
- `review_confidence`
  Allowed: `high`, `medium`, `low`
- `retention_role`
  Optional. Suggested: `direct_mechanistic`, `clinical_translational`,
  `foundational_background`, `field_synthesis`, `perspective_gap`, `exclude`

## Notes

This table is the bridge between reading full text and changing workflow behavior.
It prevents a final list from depending only on a binary keep/drop decision.
When a paper is kept partly for review architecture rather than direct
mechanistic evidence, `retention_role` should make that choice auditable.
