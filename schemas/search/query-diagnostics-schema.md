# Query Diagnostics Schema

One row per query per optimization or collection round.

## Fields

- `round_id`
  Stable round label, such as `round_1`, `round_2`, or `collection`.
- `query_id`
  Stable query label within the round, such as `q1`.
- `query`
  PubMed query string evaluated.
- `raw_hit_count`
  PubMed hit count for the accepted query.
- `collected_count`
  Number of records collected for this query during collection. This must equal `raw_hit_count` for collection rows. It can be blank during scout-only diagnostics.
- `truncated_by_constraint`
  Allowed: `no`, blank when not applicable. A value of `yes` marks an invalid capped run.
- `sample_size`
  Number of title/abstract records inspected for query quality.
- `sample_strategy`
  Short description of how sampled records were chosen, such as `top_recent_plus_tail`.
- `sampled_on_topic_count`
  Number of sampled records judged plausibly on-topic for query-quality purposes.
- `sampled_noise_count`
  Number of sampled records judged off-topic or weakly connected.
- `estimated_precision`
  Approximate sampled precision, such as `0.62`.
- `dominant_noise_classes`
  Recurrent off-topic clusters discovered during sampling.
- `missing_concepts`
  Expected in-scope concepts, mechanisms, entities, or evidence classes not adequately represented.
- `recall_signals`
  Seed papers, older foundational concepts, citation clues, or other evidence that recall is acceptable or failing.
- `decision`
  Allowed: `keep`, `revise`, `drop`, `merge`, `rescue`, `accepted_for_collection`.
- `revision_rationale`
  Brief reason for the next query change or final acceptance.

## Notes

This artifact is not an abstract-triage table.
Its purpose is to justify query optimization before the full collected cohort is sent to abstract triage.

Diagnostics should flag adjacent out-of-scope concepts separately in
`dominant_noise_classes` or `revision_rationale`. Do not list adjacent biology
as a missing concept unless the query-scope contract makes it a declared
mechanism class.
