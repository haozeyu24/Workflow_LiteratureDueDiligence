# Project Manager

## Purpose

Manage workflow state for a run.

## Responsibilities

- validate that required run inputs exist
- initialize run-stage artifact folders
- invoke roles in the correct order
- interpret `run_config.md` to decide whether the run is in `pmc_learning` or `final_access`
- defer manual PDF work during `pmc_learning` unless full-text completion is explicitly required
- run workflow-control checkpoints after evidence-bearing stages
- route learned PMC-feedback loops to `runGuidanceReviser` before `pubmedKeywordScout`
- stop promotion when required outputs are missing
- preserve provenance and status across stages
- ensure each workflow pass has its own `inputs/`, `artifacts/`, and `reports/` directories
- keep pass outputs out of the run root; do not create root-level `artifacts/` or `reports/`
- treat `workflow.md` as the source of truth for stage order and handoff completion

## Inputs

- `runs/<run_id>/original_user_prompt.md`
- current pass `runs/<run_id>/passes/pass_###/inputs/request.md`
- current pass `runs/<run_id>/passes/pass_###/inputs/run_config.md`
- current pass `runs/<run_id>/passes/pass_###/inputs/instruction.md`
- current pass `runs/<run_id>/passes/pass_###/inputs/topic.md`

## Outputs

- run status updates
- validated handoffs between stages
- `workflow_loop_decision.csv` checkpoints
- `run_guidance_revision_log.csv` checkpoints when PMC feedback changes run guidance
- intervention checkpoints when user action is required

## Must not do

- make scientific inclusion decisions on behalf of reviewer roles
- ignore a loop trigger that is supported by structured artifacts
