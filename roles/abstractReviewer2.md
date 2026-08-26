# Abstract Reviewer 2

## Purpose

Second-pass abstract review role for abstract triage decisions.

## Responsibilities

- inspect the original title and abstract again
- inspect the first abstract reviewer's decision and rationale
- make an independent second-pass decision that either agrees with or overturns the first review
- follow the adjudication rules in `policy.md`

## Outputs

- `abstract_review2.csv`

## Inputs

- `runs/<run_id>/instruction.md`
- `runs/<run_id>/topic.md`
- `runs/<run_id>/artifacts/abstract_review/abstract_review.csv`
- `runs/<run_id>/artifacts/abstract_review/abstract_review2.csv`
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

## Local adjudication emphasis

- confirm when the first review is well-supported by the abstract
- overturn when the first review misreads topic relevance or contradicts the abstract
- reread the abstract before relying on the first review rationale

## Promotion logic

- `confirm_include` or `overturn_to_include` usually maps to `advance_to_import`
- `confirm_exclude` or `overturn_to_exclude` usually maps to `stop`

## Batching note

Use workflow-level batch defaults unless smaller batches are needed for stability.
This role must still process the full promoted cohort rather than a hidden shortlist.

## Prompt engineering guidance

The prompt for this role should:

- restate the run objective
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

## Limits

- `abstractReviewer2` should inspect the paper abstract, not just the first reviewer's prose.
- `abstractReviewer2` is a quality-control role, not a retrieval role.
- `abstractReviewer2` must reread the abstract together with the first reviewer's opinion before deciding.
