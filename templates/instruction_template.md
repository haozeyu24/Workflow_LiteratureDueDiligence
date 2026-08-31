# Instruction Template

This file is a run-specific input, not part of the reusable workflow spec.

For each run, write a concrete instruction here that states:

1. what biological question the workflow is trying to support
2. what kinds of papers should be prioritized
3. what kinds of papers should be deprioritized or excluded
4. what counts as a useful final reading set
5. what mechanism classes are allowed to drive PubMed retrieval
6. what outcome, relationship, or evidence-claim terms must be present for abstract inclusion
7. what evidence is insufficient by itself, even if topically adjacent

This file should be generated or drafted by the `runSetupAgent` role from the user request.
Review-style framing that should mainly affect retention or synthesis belongs in
`review_frame.md`, not here, unless it defines explicit retrieval terms that
must be preserved.

## Reuse rule

This file may be highly specific for a given run.

That is acceptable because:

- `instruction.md` is a run input
- it is not part of the reusable workflow definition

Reusable scripts and role definitions must read this file as input rather than embedding its contents.

## Query Scope Contract

- primary entities:
- declared mechanism classes for PubMed retrieval:
- declared outcomes or required evidence claims:
- authorized comparator entities or systems:
- evidence insufficient by itself:
- secondary context for synthesis only:
- adjacent biology deferred from first-pass retrieval:
