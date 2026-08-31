# Run Setup Agent

## Purpose

Convert a free-form user request into run-specific workflow inputs.

## Responsibilities

- write `run_config.md`
- preserve the exact starting prompt in `original_user_prompt.md`
- write a concrete `instruction.md`
- write a scoped `topic.md`
- write `review_frame.md` when the downstream deliverable is review-like
- optionally write `constraints.md`
- preserve the user's actual objective without over-narrowing it silently
- preserve high prompt fidelity before broadening recall
- keep retrieval recall-friendly inside declared scope and never add PubMed collection caps

## Inputs

- `request.md`
- `original_user_prompt.md`
- optional upstream handoff following `templates/upstream_prompt_protocol_template.md`

## Outputs

- `run_config.md`
- `original_user_prompt.md`
- `instruction.md`
- `topic.md`
- optional `review_frame.md`
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
- `artifact_policy`
  - `workflow_only`
  - `allow_user_requested_exports`
- `max_query_optimization_rounds`
  This limits keyword-optimization rounds, not PubMed collection size.
- `min_big_workflow_loops`
  This requires at least one PMC-learning pass and one learned-query rerun before final PDF access. Default to `2`; do not set below `2`.
- `max_workflow_loops`
  This limits expensive end-to-end loops, not local query-refinement rounds. Default to `5`; never set above `5`.

Default:

- `agent_facing` + `continue_pmc_only`
- `artifact_policy = workflow_only`

Use `human_facing` + `pause_for_user` only when the user explicitly wants a human checkpoint for PDF download timing.

For the proposed two-part structure, the run setup agent should also preserve
that Part 2 review writing cannot start automatically after Part 1. The runtime
must ask the user whether to write from PMC-only full text or wait for
downloaded PDFs, then wait again for a clear ready-to-write signal before any
review-writing work begins.

When `interaction_mode` is `human_facing`, the workflow should treat "user provides PDFs" as a single continuation path.
It should not create separate workflow branches for "all PDFs" versus "some PDFs".

## Prompt Scope Assessment

Before writing run inputs, judge whether the prompt gives enough structure for
the workflow to search without silently inventing scope.

Classify the prompt internally as:

- `clear`: primary entities, evidence goal, and context are explicit enough to proceed
- `broad_but_workable`: proceed, but make the query-scope contract especially explicit
- `exploratory`: run only diagnostic scouting unless the parent agent authorizes a broader literature map
- `too_vague`: ask for clarification before PubMed collection

Do not use this assessment to narrow the run silently.
Use it to preserve the original objective, ask for missing scope, or write a
transparent query-scope contract.

For due-diligence runs, prefer decision-grade scope over exhaustive bibliography
scope. If the prompt is broad, preserve the breadth explicitly, but separate:

- what must drive PubMed retrieval
- what should shape retention or synthesis
- what is adjacent context only
- what would create avoidable ambiguity or reading burden

If an upstream agent is preparing the request, ask it to use
`templates/upstream_prompt_protocol_template.md`.

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
- evidence that is not sufficient by itself for abstract inclusion or full-text keep

Do not treat every phrase in the user's motivation as a PubMed retrieval class.
If the user names a narrow mechanism and gives a broader reason for caring
about it, make the narrow mechanism primary and keep the broader reason as
secondary context.

## Review-frame rule

When the user is gathering literature for a review article or review-like
synthesis, write a separate `review_frame.md` that captures:

- the parent field or larger area this topic belongs to
- background obligations for the introduction
- bigger-field progress the final review should summarize
- foundational concepts, older terminology, or landmark paper types worth preserving
- perspective questions, unresolved gaps, and translational outlook

Use this file to shape downstream retention and writing more than first-pass
retrieval. Only let `review_frame.md` expand PubMed queries when it names
explicit foundational terms, field aliases, or run-authorized comparator
concepts needed as recall safeguards.
