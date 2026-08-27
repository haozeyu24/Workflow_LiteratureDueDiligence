# Run Setup Agent

## Purpose

Convert a free-form user request into run-specific workflow inputs.

## Responsibilities

- write `run_config.md`
- preserve the exact starting prompt in `original_user_prompt.md`
- write a concrete `instruction.md`
- write a scoped `topic.md`
- optionally write `constraints.md`
- preserve the user's actual objective without over-narrowing it silently
- keep retrieval recall-first and never add PubMed collection caps

## Inputs

- `request.md`
- `original_user_prompt.md`

## Outputs

- `run_config.md`
- `original_user_prompt.md`
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
- `query_optimization_mode`
  - `adaptive`
  - `minimal`
  - `exploratory`
- `max_query_optimization_rounds`
  This limits keyword-optimization rounds, not PubMed collection size.
- `min_big_workflow_loops`
  This requires at least one PMC-learning pass and one learned-query rerun before final PDF access. Default to `2`; do not set below `2`.
- `max_workflow_loops`
  This limits expensive end-to-end loops, not local query-refinement rounds. Default to `5`; never set above `5`.

Default:

- `agent_facing` + `continue_pmc_only`

Use `human_facing` + `pause_for_user` only when the user explicitly wants a human checkpoint for PDF download timing.

When `interaction_mode` is `human_facing`, the workflow should treat "user provides PDFs" as a single continuation path.
It should not create separate workflow branches for "all PDFs" versus "some PDFs".

## Decision rule

The run setup agent may clarify and structure the request, but it must not change the reusable workflow definition.

Constraint rule:

- do not introduce PubMed retrieval caps
- search and abstract review should default to "as many potentially relevant papers as feasible"
- never write `max_results_per_query`, `max_total_results`, or equivalent collection-cap constraints
- prefer query-optimization controls in `run_config.md` over retrieval caps in `constraints.md`
- when the current harness cannot process the full collected cohort, pause, split downstream review into batches, or refine the query without sacrificing recall
- enforce `min_big_workflow_loops >= 2` so the workflow always learns from PMC full text and then applies that learning to a full rerun

## Query Scope Contract

The run setup agent must write a query-scope contract into `instruction.md`,
`topic.md`, or `constraints.md`.

The contract should identify:

- primary entities
- declared mechanism classes that may drive PubMed queries
- explicitly authorized comparator entities or model systems
- secondary context that may inform synthesis but must not drive first-pass retrieval
- adjacent biology that is deferred unless later promoted with explicit rationale

Do not treat every phrase in the user's motivation as a PubMed retrieval class.
If the user names a narrow mechanism and gives a broader reason for caring
about it, make the narrow mechanism primary and keep the broader reason as
secondary context.
