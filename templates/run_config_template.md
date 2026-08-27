# Run Config

- `interaction_mode`: `agent_facing`
- `pdf_policy`: `continue_pmc_only`
- `access_phase`: `pmc_learning`
- `query_optimization_mode`: `adaptive`
- `max_query_optimization_rounds`: `6`
- `min_big_workflow_loops`: `2`
- `max_workflow_loops`: `5`

## Allowed values

- `interaction_mode`
  - `human_facing`
  - `agent_facing`
- `pdf_policy`
  - `pause_for_user`
  - `continue_pmc_only`
  - `require_fulltext_completion`
- `access_phase`
  - `pmc_learning`
  - `final_access`
- `query_optimization_mode`
  - `adaptive`
  - `minimal`
  - `exploratory`
- `max_workflow_loops`
  - integer from 2 to 5
- `min_big_workflow_loops`
  - integer >= 2

## Notes

- default runs are `agent_facing` + `continue_pmc_only` so agent harnesses do not pause unless the user asks for a human checkpoint or full-text completion
- `human_facing` usually pairs with `pause_for_user` when a person explicitly wants to decide PDF download timing
- `pmc_learning` means read PMC-normalized full text to improve query terms and defer manual PDF action
- `final_access` means the query has been calibrated and PDF intervention may be surfaced according to `pdf_policy`
- `adaptive` query optimization usually means fewer rounds for clear topics and more rounds only when diagnostics show unresolved query defects
- `min_big_workflow_loops` forces at least one PMC-learning pass and one learned-query rerun before final PDF access
- `max_workflow_loops` limits loop-back attempts for the same failure mode
- `max_workflow_loops` must not exceed 5; after that, stop blocked or ask for intervention
- when a human chooses to provide PDFs, the pipeline should use the same import path whether the user provides a few PDFs or many PDFs
- PubMed collection caps are forbidden; use query refinement and downstream batching instead
