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
9. Use accessible full text as a learning signal before spending human effort on PDFs.

## Run-input policy

Run-specific files may define:

- the scientific objective
- topic scope
- declared mechanism classes for PubMed retrieval
- secondary context that may support synthesis but should not drive first-pass retrieval
- desired evidence types
- explicit exclusions

`original_user_prompt.md` is immutable provenance.
Pass-1 `instruction.md`, `topic.md`, and optional `constraints.md` belong in
`passes/pass_001/inputs/` and must remain immutable once the run starts.
Learned guidance belongs in pass-scoped files such as
`passes/pass_002/inputs/instruction.md`, `passes/pass_002/inputs/topic.md`, and
`passes/pass_002/inputs/constraints.md`.
Every learned guidance revision must be recorded in
`artifacts/workflow_control/run_guidance_revision_log.csv` and must cite the
`pmc_mechanism_feedback.csv` loop that triggered it.
The learned search strategy must be generated after this guidance revision, from
the pass-scoped revised guidance plus PMC feedback.

Reusable files must not silently introduce narrower biological scope than the run inputs specify.
Reusable files also must not silently introduce broader biological scope than the run inputs specify.
When a user names narrow mechanism classes, the first PubMed pass should search those classes conservatively rather than expanding into adjacent pathways, phenotypes, cofactors, regulatory programs, or disease contexts.
Default runs should be `agent_facing` with `continue_pmc_only` PDF behavior unless the user explicitly asks for a human-facing pause or full-text completion.
PubMed collection has no record cap. This is a hard workflow rule, not a default preference.
Run files, parent harnesses, agents, and scripts must not use `max_results_per_query`, `max_total_results`, top-N slices, date-sorted slices, or equivalent retrieval caps.
If a runtime cannot collect the full accepted PubMed result set, the correct action is to pause, split execution into durable batches, refine the query, or hand off to a more capable harness. It is not acceptable to run a capped collection and call the result scientifically valid.

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

Query expansion is scope-limited:

- pass 1 should use primary entities plus declared mechanism classes from the run inputs
- synonyms, assay names, and rescue terms may be added only within those declared classes
- comparator queries are allowed only when comparator evidence is explicit in the run inputs, and they must use the same declared mechanism classes
- adjacent biology discovered during sampling or PMC learning should be recorded as secondary context unless the run guidance explicitly promotes it to primary scope
- a learned rerun may narrow noise and add in-scope synonyms, but it must not broaden into new mechanism classes merely because they are plausible compensatory explanations

Every optimization round should record structured diagnostics:

- raw PubMed hit count
- sample size and sampling strategy
- sampled precision estimate
- dominant noise classes
- missing concepts or evidence types
- recall safeguards or failures
- decision to keep, revise, drop, merge, or add a rescue query

Recommended retrieval inspection:

- inspect about `20-40` records when a query returns `<= 200` hits
- inspect about `30-50` records when a query returns `201-1000` hits
- inspect about `50-75` records when a query returns `> 1000` hits

Interpretation:

- sampled on-topic fraction `< 30%`: refine aggressively
- sampled on-topic fraction `30-60%`: usable but often still worth tightening
- sampled on-topic fraction `> 60%`: usually acceptable unless important concepts are missing

Additional recall safeguards:

- collect the full result set for every accepted query
- if the full result set is too large for the current runtime, refine the query or use durable batched execution rather than truncating
- do not assume that PubMed date-sorted top `N` results are sufficient for mechanistic topics with older classic papers
- when a known direct paper or trusted seed paper exists, use it to stress-test recall and add a rescue query if the broad query does not reliably surface it
- if a retrieved paper explicitly points to an earlier direct mechanism paper, treat that citation as a retrieval failure signal and revise the query strategy for future runs

Sampling at this stage is only for query refinement.
It must not become a hidden abstract-review shortcut.

After the search strategy is accepted:

- collect the full set of papers that remain potentially related under the accepted query set
- send that full collected cohort through abstract review
- use batching only to manage context size while preserving exhaustive review of the collected cohort

Default expectation:

- retrieval is uncapped
- capped collection is a workflow violation, even when framed as operational convenience

Optimization should not be overdone:

- clear topics often need only `2-4` diagnostic rounds
- vague topics may need more exploratory rounds
- stop when sampled precision and missing-concept diagnostics plateau
- stop when further tightening would probably remove relevant papers faster than it removes noise
- continue beyond `6` rounds only when the diagnostics show a concrete unresolved failure mode

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
It is also not a stricter or cost-saving filter.
Reviewer 2 should not stop papers merely because too many papers passed reviewer 1; the decision must follow the title, abstract, reviewer-1 opinion, and the run objective.

## Full-text review policy

The full-text review stage must extract evidence before making final keep/drop judgments.

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

Evidence tiers:

- `direct`
  The paper directly studies the requested target or entity and the requested mechanism or evidence class.
- `indirect`
  The paper studies the requested target or entity but supports the mechanism indirectly, such as through lineage dependency, chromatin state, or regulatory network evidence.
- `comparator`
  The paper studies a clearly relevant homolog, family member, or model mechanism specified by the run scope.
- `background`
  The paper is useful context but does not itself justify final inclusion.
- `exclude`
  The paper is readable but off-target, expression-only, diagnostic-marker-only, methods-only, or too weak for the run objective.

Final `keep` should usually require `direct`, `indirect`, or run-authorized `comparator` evidence.
`background` and `exclude` evidence should usually map to `drop`.

If many final keeps are based on `background`, expression-only, marker-only, or weak indirect evidence, the workflow should trigger a reviewer-calibration loop before reporting the final list.

## Workflow loop policy

The workflow must treat later-stage evidence as feedback to earlier stages.
Loop decisions should be recorded in `workflow_loop_decision.csv`.

The workflow must execute at least two big passes before final PDF access or completion.
A big pass is complete when readable PMC full text has been reviewed and a row has been written to `pmc_mechanism_feedback.csv`.
The first big pass is always a learning pass; it must feed PMC-derived retained mechanisms, noise families, missing keyword families, and abstract-rule changes back to `pubmedKeywordScout`.
The second big pass must rerun query design, PubMed collection, both abstract reviews, PMC import, and full-text review using that learning.
Automatic big loops are capped at `max_workflow_loops`, default and maximum `5`.

Before the final access pass, loops should use PMC-readable full text to improve the search strategy.
The point of early full-text reading is to learn:

- mechanisms and assay language that truly match the user request
- in-scope synonyms for the declared mechanism classes
- repeated noise classes that title/abstract review did not remove
- keyword combinations that retrieve strong papers
- keyword combinations that mainly feed low-value PDF queues

PMC learning must not treat every useful full-text observation as a query-expansion target.
If PMC-readable papers reveal broader pathways, cofactors, developmental programs, disease contexts, or regulatory biology outside the declared mechanism classes, record those observations for synthesis or secondary context. Do not add them to the next PubMed query unless the run guidance revision explicitly changes the query-scope contract.

Early loops should not spend time requesting, staging, parsing, or reviewing manual PDFs.
PDF effort is reserved for the final calibrated cohort, unless the user explicitly requires complete full-text access from the beginning.

Trigger a query loop when:

- fewer than `min_big_workflow_loops` big passes have completed
- query diagnostics or reviewed papers reveal a repeated noise class that can be excluded safely
- full-text evidence shows that an accepted query family mostly retrieves background or marker-only papers
- PMC-readable full text reveals in-scope query terms that distinguish true mechanisms from incidental mentions
- the PDF queue is large after PMC learning and the queue is fed by a predictable low-value query family
- full text reveals missing in-scope vocabulary that would retrieve direct papers more reliably

Trigger a reviewer-calibration loop when:

- abstract reviewer 1 or reviewer 2 decisions conflict with the evidence-tier definitions
- reviewer rationales are generic enough that another agent could not reproduce the decision
- full-text review keeps many papers whose evidence tier is `background` or `exclude`

Do not trigger a loop merely because a result count is large.
Large counts are acceptable when precision and recall diagnostics justify them.

Every loop must have:

- a named trigger
- a target stage
- concrete changes to apply
- a stop condition
- a maximum number of expensive end-to-end attempts from `run_config.md` or a default of `5`

The controller must not accept `final_pdf_pass`, build a PDF shortlist, or report completion after only one PMC-feedback pass.
After five big passes, the controller must stop blocked or ask for human/parent-agent intervention rather than continuing automatically.

## Acquisition policy

Use PMC first.

If PMC is missing or unusable:

- add the paper to the manual PDF queue
- report that status clearly to the user
- delete unusable PMC XML artifacts after their failure is recorded

Before the final loop, manual PDF queue creation is a bookkeeping step, not an action request.
The workflow should continue with PMC-normalized papers, extract mechanism feedback, and let the Workflow Controller decide whether the query should be rebuilt before any PDF request is surfaced.

When manual PDFs are provided:

- stage them into the run-owned PDF store with stable naming
- preserve the original filename in import reports
- parse them through the shared parser path when available
- keep parse state explicit as `normalized`, `parser_pending`, or `parse_failed`
- update queue and import artifacts every time ingestion runs
- if normalized full text becomes available, continue into full-text review before treating the ingest cycle as complete unless the run is explicitly paused for user reasons

If `run_config.md` says `human_facing` + `pause_for_user`:

- pause after PMC import only in the final access pass, after PMC learning loops have completed or been deliberately skipped
- surface an explicit intervention prompt
- let the user choose whether to continue PMC-only or provide PDFs
- use the same downstream PDF import path whether the user provides a few PDFs or many PDFs

If `run_config.md` says `agent_facing` + `continue_pmc_only`:

- continue automatically with PMC-normalized papers
- keep the PDF queue as deferred work
- use PMC evidence to improve query strategy before treating the PDF queue as final
- explicitly report that some relevant papers may remain unresolved because their full text was behind a paywall, bot wall, or missing manual PDF input

If `run_config.md` says `require_fulltext_completion`:

- do not treat the final run as complete while PDF-required papers remain unresolved for access or pending review

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
