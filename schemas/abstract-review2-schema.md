# Abstract Reviewer 2 Schema

## Fields

- `paper_id`
- `pmid`
- `doi`
- `title`
- `abstract`
- `publication_types`
  Semicolon-separated values from PubMed `PublicationTypeList`; reviewer 2 should preserve official clinical-trial metadata when adjudicating trial papers.
- `year`
- `source_query`
- `abstract_reviewer_decision`
- `abstract_reviewer_rationale`
- `abstract_reviewer2_decision`
  Allowed: `confirm_include`, `confirm_exclude`, `overturn_to_include`, `overturn_to_exclude`
- `abstract_reviewer2_rationale`
- `abstract_reviewer2_confidence`
  Allowed: `high`, `medium`, `low`
- `promotion_decision`
  Allowed: `advance_to_import`, `stop`
- `review_frame_role`
  Optional. Suggested: `none`, `foundational_background`, `field_synthesis`, `perspective_gap`

## Notes

This artifact is intentionally self-contained so `abstractReviewer2` can reread the
original title and abstract instead of relying only on the first reviewer's prose.
The second reviewer should still treat the first review as context, not authority.
