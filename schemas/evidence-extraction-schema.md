# Evidence Extraction Schema

One row per readable full-text paper before final keep/drop reporting.

## Fields

- `paper_id`
- `pmid`
- `title`
- `evidence_tier`
  Allowed: `direct`, `indirect`, `comparator`, `background`, `exclude`
- `evidence_type`
  Allowed values include: `protein_folding_chaperone`, `stability_turnover`, `ptm_degradation`, `localization_retention`, `chromatin_binding`, `lineage_dependency`, `interaction_cofactor`, `expression_marker`, `methods_only`, `other`
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

## Notes

This table is the bridge between reading full text and changing workflow behavior.
It prevents a final list from depending only on a binary keep/drop decision.
