# Run Setup Agent

## Purpose

Convert a free-form user request into run-specific workflow inputs.

## Responsibilities

- write `run_config.md`
- write a concrete `instruction.md`
- write a scoped `topic.md`
- optionally write `constraints.md`
- preserve the user's actual objective without over-narrowing it silently
- keep retrieval recall-first unless the user explicitly asks for a cap or a real runtime constraint requires one

## Inputs

- `request.md`

## Outputs

- `run_config.md`
- `instruction.md`
- `topic.md`
- optional `constraints.md`

## Required run settings

The run setup agent must make two operational settings explicit:

- `interaction_mode`
  - `human_facing`
  - `agent_facing`
- `pdf_policy`
  - `pause_for_user`
  - `continue_pmc_only`
  - `require_fulltext_completion`

Recommended defaults:

- `human_facing` + `pause_for_user`
- `agent_facing` + `continue_pmc_only`

When `interaction_mode` is `human_facing`, the workflow should treat "user provides PDFs" as a single continuation path.
It should not create separate workflow branches for "all PDFs" versus "some PDFs".

## Decision rule

The run setup agent may clarify and structure the request, but it must not change the reusable workflow definition.

Constraint rule:

- do not introduce low retrieval caps just to keep the cohort small
- search and abstract review should default to "as many potentially relevant papers as feasible"
- only write `max_results_per_query` or `max_total_results` when the user explicitly wants limits or the run has a real operational ceiling that should be documented
