# Run Guidance Reviser

## Purpose

Revise run-level guidance after PMC full-text learning and before a learned
query rerun.

## Responsibilities

- preserve `original_user_prompt.md` unchanged
- read the current pass `inputs/instruction.md`, `inputs/topic.md`, optional `inputs/review_frame.md`, and optional `inputs/constraints.md`
- read `artifacts/fulltext_review/pmc_mechanism_feedback.csv`
- verify that the configured PMC full-text review coverage gate passed before using PMC feedback to revise the next pass
- read prior `query_diagnostics.csv`, review/import outcomes, and pass snapshots when useful
- write revised guidance under the next pass, such as `passes/pass_002/inputs/instruction.md`, `passes/pass_002/inputs/topic.md`, and `passes/pass_002/inputs/review_frame.md`, so downstream reviewers and the query scout share the same learned criteria
- ensure the learned pass has its own `passes/pass_###/artifacts/` and `passes/pass_###/reports/` directories before rerun artifacts are written
- optionally write revised pass-scoped `constraints.md` when the PMC feedback identifies durable exclusions or scope boundaries
- record every revision in `artifacts/workflow_control/run_guidance_revision_log.csv`
- ensure the next `search_strategy.md` is generated from the revised guidance plus PMC feedback

## Inputs

- `original_user_prompt.md`
- current pass `passes/pass_###/inputs/instruction.md`
- current pass `passes/pass_###/inputs/topic.md`
- optional current pass `passes/pass_###/inputs/review_frame.md`
- optional current pass `passes/pass_###/inputs/constraints.md`
- `artifacts/fulltext_review/pmc_mechanism_feedback.csv`
- `artifacts/search_strategy/query_diagnostics.csv`
- `artifacts/workflow_control/workflow_loop_decision.csv`
- `passes/`

## Outputs

- revised `passes/pass_###/inputs/instruction.md`
- revised `passes/pass_###/inputs/topic.md`
- optional revised `passes/pass_###/inputs/review_frame.md`
- optional revised `passes/pass_###/inputs/constraints.md`
- `artifacts/workflow_control/run_guidance_revision_log.csv`

## Required revision logic

For each learned rerun, incorporate:

- retained mechanisms that should be prioritized
- missing terms or synonym families that should be added
- noise classes and durable exclusions that reviewers should apply
- reviewer-calibration changes that should affect abstract and full-text triage
- in-scope scope adjustments, including comparator logic, when supported by PMC full text and authorized by the query-scope contract
- review-frame calibration changes, such as better foundational terms to preserve or clearer perspective-gap categories

The revision must transform pass-1 observations into pass-2 operating rules.
Do not merely copy mechanism words from full text into a broader query. Separate
the learning into four buckets:

- `retain`: terms, assays, entities, or evidence patterns that repeatedly
  identified papers central to the user prompt
- `rescue`: in-scope aliases or under-retrieved mechanism/evidence language that
  should recover missed direct papers
- `demote`: terms that are useful only as context, modifiers, comparators,
  populations, interventions, outcomes, assays, or synthesis background
- `exclude`: repeated off-scope paper classes, ambiguous terms, or contexts that
  carried noise without supporting the declared objective

Pass-2 guidance should use `retain` and `rescue` terms only when they are paired
with the run's primary entity and declared mechanism/evidence requirements.
`demote` terms may appear in reviewer context or synthesis guidance, but they
must not become standalone query drivers. `exclude` terms should become durable
negative guidance when they can be applied without losing obvious direct papers.

For each `retain` or `rescue` item, write how it changes pass 2 behavior:

- replaces a broader pass-1 term
- becomes an additional required anchor
- creates a small targeted rescue query for a direct evidence gap
- changes abstract-review promotion criteria
- changes full-text keep/drop criteria

For each `demote` or `exclude` item, write where it is enforced:

- query construction
- abstract-review rules
- second abstract-review adjudication
- full-text review evidence tiers

The intended direction of pass 2 is focus. The guidance revision should make it
harder for weak contextual matches to advance while preserving direct papers
that pass 1 showed were central or under-retrieved. If the revision is expected
to produce a similar-sized or larger pass 2, the rationale must explain the
specific in-scope evidence class that was missing from pass 1 and why the added
rescue is worth the burden.

Before recording the revision, check whether the learned query and reviewer
criteria are expected to focus the next pass more tightly on the original user
prompt. If the expected pass-2 collection or promotion burden may remain similar
to pass 1, record why that is scientifically justified by in-scope learning.
Numeric shrinkage is a confirmation signal, not the definition of success, but a
larger learned rerun without this rationale is a failed revision.

PMC feedback may identify adjacent biology outside the declared mechanism
classes. Record that material as secondary context or downstream synthesis
guidance by default. Do not promote it into the learned PubMed query unless the
revision explicitly updates the query-scope contract and explains why the
original user request authorized that broader primary scope.

## Must not do

- rewrite or summarize `original_user_prompt.md`
- modify any completed pass's `inputs/instruction.md`, `inputs/topic.md`, `inputs/review_frame.md`, or `inputs/constraints.md`
- narrow the run only to make collection smaller
- broaden the run only because PMC full text exposed plausible adjacent biology
- convert contextual, comparator, assay, population, intervention, outcome, or
  synthesis terms into standalone query drivers unless the run contract marks
  them as primary
- add PubMed collection caps
- hide learned review criteria only in `search_strategy.md`
- run PubMed collection for a learned rerun before recording the guidance revision
- revise guidance from PMC feedback based on less than the configured PMC full-text review coverage gate
