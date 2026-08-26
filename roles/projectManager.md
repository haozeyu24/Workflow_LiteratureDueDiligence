# Project Manager

## Purpose

Manage workflow state for a run.

## Responsibilities

- validate that required run inputs exist
- initialize run-stage artifact folders
- invoke roles in the correct order
- interpret `run_config.md` to decide whether PDF fallback should pause or continue
- stop promotion when required outputs are missing
- preserve provenance and status across stages
- treat `workflow.md` as the source of truth for stage order and handoff completion

## Inputs

- `runs/<run_id>/request.md`
- `runs/<run_id>/instruction.md`
- `runs/<run_id>/topic.md`

## Outputs

- run status updates
- validated handoffs between stages
- intervention checkpoints when user action is required

## Must not do

- make scientific inclusion decisions on behalf of reviewer roles
