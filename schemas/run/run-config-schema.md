# Run Config Schema

`run_config.md` is the machine-readable workflow settings file for one pass. It should contain operational settings only; scientific scope belongs in `run_brief.md`.

Required or defaulted fields:

- `pdf_policy`
  Allowed: `pause_for_user`, `continue_pmc_only`, `require_fulltext_completion`
- `access_phase`
  Allowed: `pmc_learning`, `final_access`
- `query_optimization_mode`
  Allowed: `adaptive`, `minimal`, `exploratory`
- `artifact_policy`
  Allowed: `workflow_only`, `allow_user_requested_exports`
- `max_query_optimization_rounds`
  Optional integer. Limits query-optimization rounds, not PubMed collection size.
- `min_big_workflow_loops`
  Integer >= 2.
- `max_workflow_loops`
  Integer from 2 to 5 and >= `min_big_workflow_loops`.
- `pmc_fulltext_review_gate_mode`
  Allowed: `all_available`, `scaled`.
- `fulltext_lookup_mode`
  Allowed: `pmc_then_oa_final`, `pmc_only`, `exhaustive_oa`.

Rules:

- The workflow has one operating mode. Do not add `interaction_mode`, `human_facing`, or `agent_facing` branches.
- PDF behavior is controlled by `pdf_policy`.
- Scientific scope, exclusions, review framing, and notes belong in `run_brief.md`.
- Do not add `max_results_per_query`, `max_total_results`, `retmax`, or equivalent retrieval caps to `run_config.md` or `run_brief.md`.
