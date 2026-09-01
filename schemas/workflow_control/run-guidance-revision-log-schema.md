# Run Guidance Revision Log Schema

One row per learned run-guidance revision before a learned rerun.

This artifact records how PMC full-text learning changed the run-facing guidance
that downstream roles consume.

## Fields

- `revision_id`
  Stable revision label, such as `guidance_revision_1`.
- `feedback_loop_id`
  The `pmc_mechanism_feedback.csv` `loop_id` that triggered this guidance revision.
- `feedback_source_path`
  Path to the PMC mechanism feedback artifact used for the revision.
- `prior_pass_snapshot`
  Path to the pass snapshot that preserves the pre-revision guidance and artifacts.
- `revised_instruction_path`
  Path to the revised `run_brief.md`.
- `revised_topic_path`
  Path to the revised `run_brief.md`.
- `revised_constraints_path`
  Path to revised `run_brief.md` constraints section, if changed.
- `search_strategy_path`
  Path to the learned `search_strategy.md` generated after revising guidance.
- `retained_mechanisms_added`
  PMC-derived mechanisms or evidence concepts added to run guidance.
- `noise_or_exclusions_added`
  PMC-derived noise classes or exclusion rules added to run guidance.
- `missing_terms_added`
  Missing mechanism, assay, entity, or synonym families added to run guidance.
- `terms_replaced_or_tightened`
  Broad pass-1 terms that learned evidence replaced, narrowed, paired with
  stronger anchors, or split into more focused query logic.
- `terms_demoted_to_context`
  Context, comparator, assay, population, intervention, outcome, or synthesis
  terms that may support interpretation but must not drive learned queries alone.
- `exclusion_enforcement_points`
  Where repeated noise classes are enforced: query construction, abstract
  review, second abstract-triage pass, full-text evidence tiers, or reporting.
- `reviewer_rule_changes`
  Reviewer calibration rules added or changed.
- `expected_burden_effect`
  Expected direction of pass-2 collection and abstract-promotion burden. If the
  burden may remain similar or increase, explain the in-scope evidence gap that
  justifies it.
- `revision_rationale`
  Brief evidence-grounded reason for the revision.
- `revised_by`
  Suggested: `agent`, `human`, `hybrid`.
- `created_at`
  Timestamp or date.

## Notes

`original_user_prompt.md` must remain immutable. Pass-1
`passes/pass_001/inputs/run_brief.md`, `run_brief.md`, and optional
`run_brief.md` constraints section are base guidance and should remain immutable once a run
starts. Learned revisions belong in
`passes/pass_###/inputs/` and are recorded here.
