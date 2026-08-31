# Abstract Reviewer

## Purpose

Judge abstract-level relevance to the run objective.

## Responsibilities

- read title and abstract
- use `publication_types` as an explicit signal when the paper is itself a review
- assign `include` or `exclude`
- provide concise rationale and confidence
- process every collected paper in `abstract_review.csv`
- follow the workflow-wide review policy in `policy.md`

## Outputs

- `abstract_review.csv`

## Inputs

- current pass `runs/<run_id>/Phase1_PubmedCollection/passes/pass_###/inputs/instruction.md`
- current pass `runs/<run_id>/Phase1_PubmedCollection/passes/pass_###/inputs/topic.md`
- current pass `runs/<run_id>/Phase1_PubmedCollection/passes/pass_###/inputs/review_frame.md` if present
- current pass `runs/<run_id>/Phase1_PubmedCollection/passes/pass_###/inputs/constraints.md` if present
- active pass `runs/<run_id>/Phase1_PubmedCollection/passes/pass_###/artifacts/abstract_review/abstract_review.csv`

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
- `review_frame_role`
  Optional. Suggested: `none`, `foundational_background`, `field_synthesis`, `perspective_gap`

## Local decision emphasis

- use the inclusion test: does this abstract plausibly answer the decision
  question defined by the run inputs?
- include papers only when the title/abstract shows the run's required claim
  shape: explicit primary entity or system, explicit declared mechanism or
  evidence class, and explicit outcome, relationship, perturbation, response, or
  other evidence-claim term from the run contract
- include authorized comparator papers only when the comparator is locally tied
  to the primary entity or system and the same mechanism/evidence plus outcome
  claim shape is present
- do not promote entity-only, mechanism-only, outcome-only, or context-only
  abstracts to full-text import
- do not use context, comparator, assay, population, intervention, or outcome
  terms as sufficient inclusion evidence unless the run contract explicitly
  marks that term class as primary
- use `exclude` when the abstract is clearly off-target for the run objective
- allow `review_frame.md` to preserve a minority of papers that are not direct mechanism papers but are clearly valuable for field introduction, field progress framing, or end-of-review perspective
- if `publication_types` indicates a review, retain topic-overlapping or bigger-field reviews only when they would help Phase 2 state what has already been reviewed, even when they are not primary mechanism papers
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
- include `review_frame.md` when present and tell the model it is a secondary retain signal rather than a primary retrieval contract
- define `include` and `exclude` explicitly
- tell the model to use only the provided title and abstract
- require short evidence-based rationales
- remind the model that abstract review is triage, not final inclusion
- remind the model that its main job is to preserve decision-relevant papers,
  not every paper that could ever be related

The prompt should not:

- ask for a narrative summary of the whole batch
- ask for cross-paper synthesis during per-paper triage
- encourage speculative mechanism claims beyond the abstract

## Limits

This role performs triage, not final mechanistic adjudication.

- Do not make final keep/drop judgments from abstracts alone.
- Do not infer more mechanism than the abstract supports.
- Prefer `exclude` when the abstract has only generic contextual overlap and
  does not satisfy the run's primary entity plus declared evidence/mechanism
  plus required outcome/evidence-claim requirements.
