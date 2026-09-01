# Abstract Triage Second-Pass Schema

Required columns:

- `paper_id`
- `pmid`
- `doi`
- `title`
- `abstract`
- `publication_types`
- `year`
- `source_query`
- `first_pass_decision`
- `first_pass_rationale`
- `second_pass_decision`
  Allowed: `confirm_include`, `confirm_exclude`, `overturn_to_include`, `overturn_to_exclude`
- `second_pass_rationale`
- `second_pass_confidence`
  Allowed: `high`, `medium`, `low`
- `promotion_decision`
  Allowed: `advance_to_import`, `stop`
- `synthesis_role`
  Allowed: `none`, `foundational_background`, `field_synthesis`, `perspective_gap`

This table is self-contained so the rescue pass can reread the title and
abstract together with the first-pass decision before promotion. First-pass
includes should normally receive `confirm_include` and `advance_to_import`
without relitigating the original decision. The rescue pass should focus on
first-pass excludes and use `overturn_to_include` only when a high-value
clinical, mechanistic, comparator, or review-frame signal was plausibly missed.
