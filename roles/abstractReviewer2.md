# Abstract Reviewer 2

## Purpose

Second-pass abstract review role for abstract triage decisions.

## Responsibilities

- inspect the original title and abstract again
- inspect `publication_types` and preserve review papers that clearly map to the topic or bigger review field
- inspect the first abstract reviewer's decision and rationale
- make an independent second-pass decision that either agrees with or overturns the first review
- follow the adjudication rules in `policy.md`

## Outputs

- `abstract_review2.csv`

## Inputs

- current pass `runs/<run_id>/Phase1_PubmedCollection/passes/pass_###/inputs/instruction.md`
- current pass `runs/<run_id>/Phase1_PubmedCollection/passes/pass_###/inputs/topic.md`
- current pass `runs/<run_id>/Phase1_PubmedCollection/passes/pass_###/inputs/review_frame.md` if present
- active pass `runs/<run_id>/Phase1_PubmedCollection/passes/pass_###/artifacts/abstract_review/abstract_review.csv`
- active pass `runs/<run_id>/Phase1_PubmedCollection/passes/pass_###/artifacts/abstract_review/abstract_review2.csv`
  This table must include the original title and abstract, not only the first
  reviewer's decision.

## Required output fields

For each row, populate:

- `title`
- `abstract`
- `abstract_reviewer_decision`
- `abstract_reviewer_rationale`
- `abstract_reviewer2_decision`
  Allowed:
  - `confirm_include`
  - `confirm_exclude`
  - `overturn_to_include`
  - `overturn_to_exclude`
- `abstract_reviewer2_rationale`
- `abstract_reviewer2_confidence`
  Allowed: `high`, `medium`, `low`
- `promotion_decision`
  Allowed:
  - `advance_to_import`
  - `stop`
- `review_frame_role`
  Optional. Suggested: `none`, `foundational_background`, `field_synthesis`, `perspective_gap`

## Local adjudication emphasis

- confirm when the first review is well-supported by the abstract
- overturn when the first review misreads topic relevance or contradicts the abstract
- reread the abstract before relying on the first review rationale
- use the second pass to reduce ambiguity from generic contextual overlap
  before import burden grows
- for learned reruns, apply the revised guidance as a narrowing calibration:
  papers with only generic contextual overlap should stop unless they satisfy
  the run's primary entity plus declared evidence/mechanism requirements
- use `review_frame.md` only as a secondary reason to preserve papers that clearly serve introduction, field-progress, or perspective functions
- for review papers, preserve those that would let Phase 2 explicitly say which angles have already been reviewed and how the new review extends them

## Promotion logic

- `confirm_include` or `overturn_to_include` usually maps to `advance_to_import`
- `confirm_exclude` or `overturn_to_exclude` usually maps to `stop`
- do not use cost, PDF availability, import burden, or a desired cohort size as a reason to stop a paper

## Batching note

Use workflow-level batch defaults unless smaller batches are needed for stability.
This role must still process the full promoted cohort rather than a hidden shortlist.

## Prompt engineering guidance

The prompt for this role should:

- restate the run objective
- include `review_frame.md` when present and remind the model it should not overwhelm direct topic relevance
- include the original abstract and the first reviewer's decision and rationale
- define the allowed second-pass decisions explicitly
- require short reasons for confirmation or overturning
- require a final actionable `promotion_decision`

The prompt should not:

- ask the model to merely rubber-stamp the first review
- hide the original abstract while showing only the first review prose
- mix second-pass adjudication with downstream full-text reasoning

## Priority

`abstractReviewer2` should reduce both overinclusive and underinclusive abstract triage errors by rereading the abstract rather than relying on the first review alone.
It should not be stricter by default.
Its job is independent adjudication over the title, abstract, and reviewer-1 opinion.

## Limits

- `abstractReviewer2` should inspect the paper abstract, not just the first reviewer's prose.
- `abstractReviewer2` is a quality-control role, not a retrieval role.
- `abstractReviewer2` must reread the abstract together with the first reviewer's opinion before deciding.
- `abstractReviewer2` must not act as a cost-control or full-text-access filter.
