# Policy

## Purpose

This file defines workflow-wide decision rules.

It does not define stage order or artifact naming.
Those belong in `workflow.md`.

## Conflict resolution

Use this precedence order when files overlap:

1. `workflow.md` for stage order, required artifacts, and promotion conditions
2. `policy.md` for workflow-wide review and acquisition rules
3. `roles/*.md` for local stage behavior

If a role file conflicts with this document, update the role file.
Do not create silent one-off exceptions during a run.

## Core principles

1. Separate retrieval failure from review failure.
2. Separate abstract-level plausibility from full-text inclusion.
3. Preserve provenance at every stage.
4. Prefer inclusive abstract triage over premature exclusion.
5. Keep the workflow reusable across topics and runtimes.
6. Treat batching as context management, not hidden filtering.
7. Treat access failure as distinct from scientific exclusion.
8. Prefer explicit state labels over ambiguous reviewer prose.

## Run-input policy

Run-specific files may define:

- the scientific objective
- topic scope
- desired evidence types
- explicit exclusions
- explicit operational limits

Reusable files must not silently introduce narrower biological scope or lower retrieval caps than the run inputs specify.

## Abstract review policy

At the abstract stage, papers should be labeled:

- `include`
- `exclude`

The abstract stage is allowed to identify plausible candidates.
It is not allowed to claim final mechanistic importance.

Decision interpretation:

- `include` means the paper is plausible enough to preserve
- `exclude` means the paper is clearly not worth carrying forward under the run objective

Default stance:

- borderline but plausible papers should usually remain in scope for later stages
- abstract review should be more inclusive than full-text review

## PubMed search refinement policy

Search refinement should be driven by sampled precision, not raw hit count alone.

Recall protection is equally important when the topic depends on older or foundational mechanistic papers.

Recommended retrieval inspection:

- inspect about `20-40` records when a query returns `<= 200` hits
- inspect about `30-50` records when a query returns `201-1000` hits
- inspect about `50-75` records when a query returns `> 1000` hits

Interpretation:

- sampled on-topic fraction `< 30%`: refine aggressively
- sampled on-topic fraction `30-60%`: usable but often still worth tightening
- sampled on-topic fraction `> 60%`: usually acceptable unless important concepts are missing

Additional recall safeguards:

- if a direct target-mechanism query returns `<= 150` records, prefer collecting the full query result rather than truncating it with a low per-query cap
- if collection must remain capped for practical reasons, inspect whether the tail likely contains older foundational papers before accepting the cap
- do not assume that PubMed date-sorted top `N` results are sufficient for mechanistic topics with older classic papers
- when a known direct paper or trusted seed paper exists, use it to stress-test recall and add a rescue query if the broad query does not reliably surface it
- if a retrieved paper explicitly points to an earlier direct mechanism paper, treat that citation as a retrieval failure signal and revise the query strategy for future runs

Sampling at this stage is only for query refinement.

After the search strategy is accepted:

- collect the full set of papers that remain potentially related under the run constraints
- send that full collected cohort through abstract review
- use batching only to manage context size while preserving exhaustive review of the collected cohort

Default expectation:

- absent an explicit user-requested or operationally necessary limit, retrieval should be effectively uncapped within the collector's technical bounds
- low caps are a design exception and should be justified, not the default

Collection interpretation:

- accepted query results define the candidate cohort
- exhaustive abstract review applies to that cohort even when it spans many batches

## Batching policy

Batching depends partly on context window, but it depends even more on judgment quality.

Use safe batch size rather than maximum batch size.

General rule:

- stronger models can usually handle larger batches
- weaker models should use smaller batches immediately
- full-text batches should remain small even for strong models because experiment-level detail is easy to lose

At abstract stage, batching is an execution detail, not a filtering step.
No role should reinterpret batching as permission to shortlist a large collected cohort before `abstractReviewer` or `abstractReviewer2`.

Reduce batch size if the model:

- confuses papers within a batch
- repeats generic rationales across rows
- omits obvious evidence present in the provided text
- starts comparing the batch globally instead of judging papers independently

Do not respond to large cohorts by:

- silently truncating the cohort before abstract review
- replacing per-paper review with global summary judgments
- dropping older records only because they fall outside a preferred top-ranked slice

## Abstract Reviewer 2 policy

`abstractReviewer2` must inspect:

- the original title and abstract
- the first abstract reviewer decision
- the first abstract reviewer rationale

`abstractReviewer2` may:

- confirm
- overturn

`abstractReviewer2` must not behave as a rubber stamp.
Its role is adjudication, not formatting.

## Full-text review policy

The full-text review stage may make final keep/drop judgments.

Inclusion should favor:

- mechanistic relevance
- objective-central biology
- topic-specific interaction, dependency, or regulation
- biologically specific evidence tied to the run objective
- likely usefulness for downstream synthesis

Exclusion should favor:

- methods-only papers
- generic resources
- incidental topic context
- descriptive papers with little mechanistic value

Interpretation:

- `keep` means the full text supports downstream reading or synthesis under the run objective
- `drop` means the paper is readable but does not merit final inclusion
- no readable full text is an access state, not a scientific drop

## Acquisition policy

Use PMC first.

If PMC is missing or unusable:

- add the paper to the manual PDF queue
- report that status clearly to the user
- delete unusable PMC XML artifacts after their failure is recorded

When manual PDFs are provided:

- stage them into the run-owned PDF store with stable naming
- preserve the original filename in import reports
- parse them through the shared parser path when available
- keep parse state explicit as `normalized`, `parser_pending`, or `parse_failed`
- update queue and import artifacts every time ingestion runs
- if normalized full text becomes available, continue into full-text review before treating the ingest cycle as complete unless the run is explicitly paused for user reasons

If `run_config.md` says `human_facing` + `pause_for_user`:

- pause after PMC import once the PDF queue is known
- surface an explicit intervention prompt
- let the user choose whether to continue PMC-only or provide PDFs
- use the same downstream PDF import path whether the user provides a few PDFs or many PDFs

If `run_config.md` says `agent_facing` + `continue_pmc_only`:

- continue automatically with PMC-normalized papers
- keep the PDF queue as deferred work

If `run_config.md` says `require_fulltext_completion`:

- do not treat the run as complete while PDF-required papers remain unresolved for access or pending review

## Final output policy

The final reading list must include:

- title
- PMID
- PMCID when present
- DOI when present
- final decision
- rationale
- normalized file location

The final output should also preserve unresolved but still relevant access cases as a distinct status such as `abstract_relevant_fulltext_unavailable`.
