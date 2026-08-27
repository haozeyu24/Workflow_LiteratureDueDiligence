# Run Config Schema

## Fields

- `interaction_mode`
  Allowed: `human_facing`, `agent_facing`
- `pdf_policy`
  Allowed: `pause_for_user`, `continue_pmc_only`, `require_fulltext_completion`
- `access_phase`
  Allowed: `pmc_learning`, `final_access`.
  Default: `pmc_learning`.
- `query_optimization_mode`
  Allowed: `adaptive`, `minimal`, `exploratory`
- `max_query_optimization_rounds`
  Optional integer. This controls query-design iteration, not PubMed collection size.
- `min_big_workflow_loops`
  Optional integer. Default: `2`. Minimum allowed: `2`. This requires at least one PMC-learning pass and one learned-query rerun before final PDF access or completion.
- `max_workflow_loops`
  Optional integer. Default and maximum: `5`. This limits expensive end-to-end workflow loop-back attempts. It does not limit local query-refinement rounds inside `pubmedKeywordScout`.

## Notes

This file tells the workflow whether it should pause for user action or continue automatically when PDF fallback is needed.
Default runs are `agent_facing` + `continue_pmc_only`; human-facing pauses are opt-in.
During `pmc_learning`, PDF fallback is recorded but not requested; PMC-normalized full text is used to improve the query first.
During `final_access`, PDF fallback follows `pdf_policy`.
If the user later provides PDFs, the same downstream import path should be used whether the user provides a subset or the whole queue.
PubMed collection has no record cap.
Do not add `max_results_per_query`, `max_total_results`, or equivalent retrieval caps to `constraints.md`.
`final_pdf_pass` and `pdf_download_shortlist.csv` are invalid until at least `min_big_workflow_loops` PMC-feedback passes exist.
Values above `5` for `max_workflow_loops` are invalid; after five big passes the workflow must stop blocked or ask for human/parent-agent intervention.
