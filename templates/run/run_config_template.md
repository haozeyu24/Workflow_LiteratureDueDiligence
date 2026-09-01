# Run Config

- `pdf_policy`: `continue_pmc_only`
- `access_phase`: `pmc_learning`
- `query_optimization_mode`: `adaptive`
- `artifact_policy`: `workflow_only`
- `max_query_optimization_rounds`: `6`
- `min_big_workflow_loops`: `2`
- `max_workflow_loops`: `2`
- `pmc_fulltext_review_gate_mode`: `all_available`
- `fulltext_lookup_mode`: `pmc_then_oa_final`

## Allowed values

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
- `artifact_policy`
  - `workflow_only`
  - `allow_user_requested_exports`
- `max_workflow_loops`
  - fixed value `2`
- `min_big_workflow_loops`
  - fixed value `2`
- `pmc_fulltext_review_gate_mode`
  - `scaled`
  - `all_available`
- `fulltext_lookup_mode`
  - `pmc_then_oa_final`
  - `pmc_only`
  - `exhaustive_oa`

## Notes

- The workflow has one operating mode. It does not branch into human-facing versus agent-facing variants.
- `pdf_policy = pause_for_user` means pause at the PDF checkpoint after PMC-learning gates allow final access.
- `pdf_policy = continue_pmc_only` means continue with readable PMC/full-text evidence while preserving unresolved PDF needs as access work.
- `pdf_policy = require_fulltext_completion` blocks downstream progression until PDF fallback is addressed.
- `pmc_learning` means read PMC-normalized full text to improve query terms and defer manual PDF action.
- `final_access` means the query has been calibrated and PDF intervention may be surfaced according to `pdf_policy`.
- `adaptive` query optimization usually means fewer rounds for clear topics and more rounds only when diagnostics show unresolved query defects.
- `workflow_only` means agents may write only declared workflow artifacts unless the user explicitly requests a side export in the current turn.
- `min_big_workflow_loops` forces pass 1 as the PMC-learning pass and pass 2 as the learned final pass before final PDF access.
- `max_workflow_loops` is fixed at 2; the workflow does not continue into pass 3+ automatically.
- PubMed collection caps are forbidden; use query refinement and downstream batching instead.
- `all_available` PMC full-text review gating means every paper marked `pmc_access_status = available` in `import_status.csv` must have normalized full text, a full-text review decision, and an evidence-extraction row before `pmc_mechanism_feedback.csv` can trigger a learned rerun.
- `pmc_then_oa_final` means early `pmc_learning` import uses NCBI PMCID/PMC XML only, then alternate open-access PDF lookup may run in `final_access` or when `pdf_policy = require_fulltext_completion`.
