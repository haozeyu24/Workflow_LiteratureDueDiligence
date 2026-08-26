# Runs

This folder stores run-specific workflow inputs and outputs.

Rule:

- each subfolder under `runs/` is one concrete run
- the core workflow spec does not change across runs
- only the run inputs and run artifacts change

Recommended layout:

`runs/<run_id>/`

Suggested files:

- `request.md`
- `instruction.md`
- `topic.md`
- `constraints.md` optional
- `notes.md` optional

Example runs should also live here if they are meant to demonstrate how the reusable workflow is instantiated.
