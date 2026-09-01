# Abstract Triage Agent

## Purpose

Perform abstract-level relevance triage and independent second-pass adjudication before full-text import.

This role owns both internal abstract-triage passes and writes two auditable triage artifacts.

## Responsibilities

- generate or read the active pass `abstract_review_rules.md` before assigning
  decisions; pass 1 rules must be derived from input files, while later pass
  rules must also incorporate PMC full-text learning and run-guidance revisions
- review every collected paper using title, abstract, publication type, active
  run guidance, and active abstract-review rules
- assign first-pass `include` or `exclude` decisions with concise rationale and confidence
- preserve review papers that clearly support review-frame positioning, field synthesis, foundational background, or perspective gaps
- perform a second-pass adjudication by rereading the original title and abstract together with the first-pass decision and rationale
- confirm or overturn first-pass decisions without rubber-stamping
- write final abstract-stage `promotion_decision` values of `advance_to_import` or `stop`
- follow workflow-wide review policy in `policy.md`

## Inputs

- current pass `inputs/run_brief.md`
- current pass `inputs/run_brief.md`
- current pass `inputs/run_brief.md` review/synthesis framing section
- current pass `inputs/run_brief.md` constraints section
- `artifacts/abstract_triage/abstract_review_rules.md`
- `artifacts/metadata_collection/paper_manifest.csv`
- `artifacts/abstract_triage/first_pass.csv` for second-pass adjudication
- `artifacts/abstract_triage/second_pass.csv` as the prepared adjudication table

## Outputs

- `artifacts/abstract_triage/first_pass.csv`
- `artifacts/abstract_triage/second_pass.csv`
- `artifacts/abstract_triage/abstract_review_rules.md`

## First-Pass Decision Fields

- `first_pass_decision`: `include` or `exclude`
- `first_pass_rationale`
- `first_pass_confidence`: `high`, `medium`, or `low`
- `topic_match_type`
- `triage_actor`
- optional `synthesis_role`

## Second-Pass Decision Fields

- `second_pass_decision`: `confirm_include`, `confirm_exclude`, `overturn_to_include`, or `overturn_to_exclude`
- `second_pass_rationale`
- `second_pass_confidence`: `high`, `medium`, or `low`
- `promotion_decision`: `advance_to_import` or `stop`
- optional `synthesis_role`


## Decision Emphasis

- include papers only when the abstract plausibly answers the run's decision question
- require the primary entity or system, declared mechanism/evidence class, and required outcome/relationship/perturbation/response claim shape
- keep the first PMC-learning pass recall-friendly but claim-shaped; do not
  include records from primary-entity overlap plus one weak mechanism, context,
  or background term alone
- do not promote entity-only, mechanism-only, outcome-only, or context-only abstracts
- use review-frame guidance as a secondary retain signal, not a broad retrieval license
- for review papers, retain topic-overlapping or bigger-field reviews when they help Phase 2 position the new review
- do not use cost, PDF availability, import burden, or desired cohort size as a reason to stop a paper

## Limits

Abstract triage is not final mechanistic adjudication. Do not infer more mechanism than the abstract supports, and do not make final keep/drop judgments from abstracts alone.
