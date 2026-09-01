# Full-Text Rescue Schema

One row per first-pass full-text drop reviewed by the rescue pass.

## Fields

- `paper_id`
- `pmid`
- `pmcid`
- `doi`
- `title`
- `normalized_source_type`
- `normalized_path`
- `original_fulltext_decision`
  Allowed: `drop`
- `original_fulltext_rationale`
- `rescue_decision`
  Allowed: `confirm_drop`, `overturn_to_keep`
- `final_fulltext_decision`
  Allowed: `keep`, `drop`
- `rescue_rationale`
- `positive_signal_found`
  Allowed: `yes`, `no`
- `negative_signal_overridden`
  Allowed: `yes`, `no`
- `supporting_text_locator`
- `review_confidence`
  Allowed: `high`, `medium`, `low`

## Notes

The full-text rescue pass is a second look at first-pass drops. It uses the same
active full-text review rules and the same promotion-first logic as the primary
full-text review: clear positive direct, indirect, comparator, or authorized
review-frame evidence overrides demotion signals. Confirm a drop only when the
paper still lacks sufficient positive full-text evidence.
