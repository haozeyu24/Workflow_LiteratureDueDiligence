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
- `artifact_policy`
  Allowed: `workflow_only`, `allow_user_requested_exports`.
  Default: `workflow_only`.
  `workflow_only` forbids extra analyses, rankings, exports, scripts, dashboards, or summaries unless they are declared workflow artifacts or explicitly requested by the user in the current turn.
- `max_query_optimization_rounds`
  Optional integer. This controls query-design iteration, not PubMed collection size.
- `min_big_workflow_loops`
  Optional integer. Default: `2`. Minimum allowed: `2`. This requires at least one PMC-learning pass and one learned-query rerun before final PDF access or completion.
- `max_workflow_loops`
  Optional integer. Default and maximum: `5`. This limits expensive end-to-end workflow loop-back attempts. It does not limit local query-refinement rounds inside `pubmedKeywordScout`.
- `pmc_fulltext_review_gate_mode`
  Allowed: `all_available`, `scaled`.
  Default: `all_available`.
  `all_available` strictly requires every PMC-available paper to be normalized, full-text reviewed, and represented in evidence extraction before PMC feedback can unlock a learned rerun.

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
Under `workflow_only`, agents must not write side deliverables outside the active run/pass artifact contract.
PMC full-text learning must satisfy `pmc_fulltext_review_gate_mode` before `pmc_mechanism_feedback.csv` can trigger learned pass activation. The strict default is `all_available`.
