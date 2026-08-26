# Instruction Template

This file is a run-specific input, not part of the reusable workflow spec.

For each run, write a concrete instruction here that states:

1. what biological question the workflow is trying to support
2. what kinds of papers should be prioritized
3. what kinds of papers should be deprioritized or excluded
4. what counts as a useful final reading set

This file should be generated or drafted by the `runSetupAgent` role from the user request.

## Reuse rule

This file may be highly specific for a given run.

That is acceptable because:

- `instruction.md` is a run input
- it is not part of the reusable workflow definition

Reusable scripts and role definitions must read this file as input rather than embedding its contents.
