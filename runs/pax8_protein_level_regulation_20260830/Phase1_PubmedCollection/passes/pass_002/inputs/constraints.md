# Constraints

- PubMed collection caps are forbidden by workflow policy.
- Do not add `max_results_per_query`, `max_total_results`, `retmax`, or equivalent collection-cap settings.
- Use scope constraints, query refinement, and downstream batching instead.
- Learned reruns may add safe negative filters for driver nomenclature,
  diagnostic-marker language, and target-gene/promoter noise, but must not
  eliminate family-wide comparator recall.
