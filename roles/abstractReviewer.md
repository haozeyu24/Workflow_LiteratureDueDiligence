# Abstract Reviewer

## Purpose

Judge abstract-level relevance to the run objective.

## Responsibilities

- read title and abstract
- assign `include` or `exclude`
- provide concise rationale and confidence
- process every collected paper in `abstract_review.csv`
- follow the workflow-wide review policy in `policy.md`

## Outputs

- `abstract_review.csv`

## Inputs

- `runs/<run_id>/instruction.md`
- `runs/<run_id>/topic.md`
- `runs/<run_id>/constraints.md` if present
- `runs/<run_id>/artifacts/abstract_review/abstract_review.csv`

## Required output fields

For each row, populate:

- `review_decision`
  Allowed: `include`, `exclude`
- `review_rationale`
- `review_confidence`
  Allowed: `high`, `medium`, `low`
- `topic_match_type`
  Suggested: `direct`, `indirect`, `background_only`
- `reviewer_type`
  Suggested default: `agent`

## Local decision emphasis

- favor `include` for borderline but plausible papers
- use `exclude` when the abstract is clearly off-target for the run objective
- apply per-paper judgment only; cohort-level filtering rules live in `workflow.md` and `policy.md`

## Rationale style

Keep rationale short and concrete.

Good examples:

- `Directly studies a core interaction or mechanism named in the run objective.`
- `Mentions a run-related term, but the paper is about a different problem space than the objective.`
- `Mechanism language is indirect, but the abstract is plausible enough to preserve for full-text screening.`

## Batching note

Use workflow-level batch defaults unless the harness needs smaller batches for stability.
Role-local batching should never override the exhaustive cohort-review rule in `workflow.md`.

## Prompt engineering guidance

The prompt for this role should:

- include the run objective from `instruction.md` and `topic.md`
- define `include` and `exclude` explicitly
- tell the model to use only the provided title and abstract
- require short evidence-based rationales
- remind the model that abstract review is triage, not final inclusion
- remind the model that its main job is to keep papers that are likely relevant to the topic and instruction

The prompt should not:

- ask for a narrative summary of the whole batch
- ask for cross-paper synthesis during per-paper triage
- encourage speculative mechanism claims beyond the abstract

## Limits

This role performs triage, not final mechanistic adjudication.

- Do not make final keep/drop judgments from abstracts alone.
- Do not infer more mechanism than the abstract supports.
- Prefer `include` over exclusion when the abstract is ambiguous but plausibly relevant.
