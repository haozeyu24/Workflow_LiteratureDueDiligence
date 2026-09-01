# Workflow Loop Decision Schema

One row per checkpoint where the workflow decides whether to continue, pause, or loop back.

## Fields

- `loop_id`
  Stable identifier such as `loop_1`.
- `source_stage`
  Stage that produced the signal, such as `query_optimization`, `abstract_triage`, `fulltext_import`, or `fulltext_review`.
- `trigger`
  Short name of the rule or observed failure mode.
- `triggered`
  Allowed: `yes`, `no`
- `action`
  Allowed: `continue`, `pause_for_user`, `build_pdf_shortlist`, `loop_to_run_guidance_reviser`, `loop_to_query_scout`, `loop_to_abstract_triage`, `loop_to_fulltext_review`, `stop_blocked`
- `target_stage`
  Stage to run next.
- `rationale`
  Evidence-grounded reason for the decision.
- `required_changes`
  Concrete changes required before the target stage runs.
- `stop_condition`
  Condition that will end the loop or prove that another loop is not useful.

## Notes

Loop decisions must cite structured artifacts such as `query_diagnostics.csv`, `first_pass.csv`, `second_pass.csv`, `import_status.csv`, `evidence_extraction.csv`, or `pmc_mechanism_feedback.csv`.
They must not be based on a vague desire for fewer papers.

Before the final access pass, a large PDF queue should usually trigger PMC mechanism feedback and query reconstruction rather than a manual PDF request.

When PMC feedback triggers a learned rerun, the target stage should usually be
`runManager` before `pubmedSearchAgent`, so `run_brief.md`,
`run_brief.md`, reviewer rules, and `search_strategy.md` all reflect the same
full-text learning.
