# Run Guidance Reviser

## Purpose

Revise run-level guidance after PMC full-text learning and before a learned
query rerun.

## Responsibilities

- preserve `original_user_prompt.md` unchanged
- read the current pass `inputs/instruction.md`, `inputs/topic.md`, and optional `inputs/constraints.md`
- read `artifacts/fulltext_review/pmc_mechanism_feedback.csv`
- read prior `query_diagnostics.csv`, review/import outcomes, and pass snapshots when useful
- write revised guidance under the next pass, such as `passes/pass_002/inputs/instruction.md` and `passes/pass_002/inputs/topic.md`, so downstream reviewers and the query scout share the same learned criteria
- ensure the learned pass has its own `passes/pass_###/artifacts/` and `passes/pass_###/reports/` directories before rerun artifacts are written
- optionally write revised pass-scoped `constraints.md` when the PMC feedback identifies durable exclusions or scope boundaries
- record every revision in `artifacts/workflow_control/run_guidance_revision_log.csv`
- ensure the next `search_strategy.md` is generated from the revised guidance plus PMC feedback

## Inputs

- `original_user_prompt.md`
- current pass `passes/pass_###/inputs/instruction.md`
- current pass `passes/pass_###/inputs/topic.md`
- optional current pass `passes/pass_###/inputs/constraints.md`
- `artifacts/fulltext_review/pmc_mechanism_feedback.csv`
- `artifacts/search_strategy/query_diagnostics.csv`
- `artifacts/workflow_control/workflow_loop_decision.csv`
- `passes/`

## Outputs

- revised `passes/pass_###/inputs/instruction.md`
- revised `passes/pass_###/inputs/topic.md`
- optional revised `passes/pass_###/inputs/constraints.md`
- `artifacts/workflow_control/run_guidance_revision_log.csv`

## Required revision logic

For each learned rerun, incorporate:

- retained mechanisms that should be prioritized
- missing terms or synonym families that should be added
- noise classes and durable exclusions that reviewers should apply
- reviewer-calibration changes that should affect abstract and full-text triage
- in-scope scope adjustments, including comparator logic, when supported by PMC full text and authorized by the query-scope contract

PMC feedback may identify adjacent biology outside the declared mechanism
classes. Record that material as secondary context or downstream synthesis
guidance by default. Do not promote it into the learned PubMed query unless the
revision explicitly updates the query-scope contract and explains why the
original user request authorized that broader primary scope.

## Must not do

- rewrite or summarize `original_user_prompt.md`
- modify any completed pass's `inputs/instruction.md`, `inputs/topic.md`, or `inputs/constraints.md`
- narrow the run only to make collection smaller
- broaden the run only because PMC full text exposed plausible adjacent biology
- add PubMed collection caps
- hide learned review criteria only in `search_strategy.md`
- run PubMed collection for a learned rerun before recording the guidance revision
