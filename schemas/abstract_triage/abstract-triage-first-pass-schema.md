# Abstract Triage First-Pass Schema

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
  Allowed: `include`, `exclude`
- `first_pass_rationale`
- `first_pass_confidence`
  Allowed: `high`, `medium`, `low`
- `topic_match_type`
  Suggested: `direct`, `indirect`, `background_only`
- `triage_actor`
  Suggested: `agent`, `human`, `hybrid`
- `synthesis_role`
  Allowed: `none`, `foundational_background`, `field_synthesis`, `perspective_gap`
- optional prescreen columns: `prescreen_hint`, `prescreen_rationale`, `prescreen_overlap_terms`
