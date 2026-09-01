# Workflow

## Objective

Given an instruction and topic, the proposed workflow has two parts.

Part 1 is the current literature due-diligence workflow.
Part 2 is a later review-paper construction workflow that must not begin until
the user explicitly authorizes writing.

Part 1:

1. generate a PubMed search strategy
2. optimize the query set with hit counts, sampled precision, noise classes, and missing-concept diagnostics
3. collect title, abstract, and metadata for the accepted query set
4. review abstract-level relevance
5. run a rescue abstract-triage pass over first-pass excludes while carrying first-pass includes forward without relitigating them
6. acquire and normalize PMC full text first
7. use PMC full text to summarize mechanisms, noise, scientific notes, and query-feedback signals
8. require the configured PMC full-text review coverage gate to pass, then revise run guidance from PMC full-text learning, reconstruct the query, and rerun collection, abstract triage, PMC import, and full-text review at least once using PMC-derived learning
9. decide whether additional learned loops are needed before spending effort on PDFs
   by checking final-pass prompt-fit density in the retained full-text evidence,
   not by imposing a numeric paper-count cap
10. reserve manual PDF intervention for the final calibrated access pass unless the run explicitly requires full-text completion from the beginning
11. extract final full-text evidence and review normalized full text
12. produce a final reading list with metadata and file pointers
13. when Part 1 is complete, ask the user whether to:
   - write the review using PMC-readable full text only
   - wait for the user to provide downloaded PDFs before review writing
14. do not begin review writing, PDF parsing for writing, or any Phase-2 work until the user gives a clear ready-to-write signal
15. if the user chooses to provide PDFs for writing, parse and normalize them only after that ready-to-write signal, rerun retention on newly readable papers, and report how many PDFs were retained into the writing corpus

Part 2:

1. construct the review paper from the Part-1 retained corpus

Part 2 is intentionally left as a placeholder in this file for now.
Its detailed structure should be added later, after the Phase-1/Phase-2 boundary
and PDF decision checkpoint are working well.

## Workflow Immutability

This workflow is immutable during a run. Agents must not modify reusable workflow files to solve a run-specific scientific request. The reusable files are `workflow.md`, `policy.md`, `roles/`, `schemas/`, `templates/`, and `tools/`.

Run-specific adaptation belongs only under `runs/<run_id>/`: the immutable `original_user_prompt.md`, pass-scoped `inputs/run_brief.md`, pass-scoped `inputs/run_config.md`, artifacts, reports, snapshots, and workflow-control files. Learned reruns create revised `run_brief.md` files in later pass folders rather than editing completed pass inputs.

## Fixed workflow vs run-specific inputs

This document describes the fixed workflow.

The following are reusable across runs:

- role definitions
- stage order
- review schemas
- artifact types
- import and normalization logic

The following are run-specific:

- the exact original user prompt
- the user request
- the run configuration
- the generated instruction
- the generated topic
- the Phase-1 transcript log
- optional seed entities, systems, mechanisms, comparators, labs, or exclusions

Each run should live in its own folder under `runs/`.

## Generic workflow rule

All reusable workflow logic must be parameterized by run inputs.

That means:

- role behavior is generic
- artifact schemas are generic
- scripts are generic
- run folders carry topic-specific content
- the cross-pass transcript lives under `passes/phase1_transcript.md`

If a reusable component mentions a specific lab, entity list, assay family, or scientific question, it should be treated as a design mistake unless that component is clearly inside a run-specific folder.

## Due-Diligence Philosophy

This workflow optimizes for decision-grade coverage for biotech researchers,
academic researchers, investors, and consulting-style scientific diligence. A
good review is not a maximal literature sweep. It is a scoped, auditable account
of the major mechanisms, evidence strength, gaps, risks, and unresolved access
cases needed for decision-making.

The workflow's default priority is:

1. high user-prompt fidelity
2. recall-friendly retrieval inside the declared scope
3. early ambiguity reduction
4. progressively stricter full-text evidence gates

Operational interpretation:

- prompt fidelity defines what may drive retrieval
- recall-friendly behavior is concentrated in query design and abstract triage
- abstract triage preserves plausible decision-relevant papers, not anything
  that could ever be related
- the first PMC-learning pass may be slightly more permissive than later passes
  so full-text review can read enough papers to learn useful positive and
  negative scientific signals
- the second abstract-triage pass is a rescue review for first-pass excludes,
  not an independent duplicate reviewer confirming the same decision function
- full-text review narrows to papers with direct, indirect, or authorized
  comparator evidence, plus only explicitly justified review-frame background
- Phase 2 may synthesize more papers than a human must personally read, but
  every synthesized paper must have typed evidence, a retention role, and
  provenance

## Instruction hierarchy

When reusable files appear to disagree, resolve them in this order:

1. `workflow.md`
2. `policy.md`
3. `roles/*.md`
4. templates and helper prose

Interpretation:

- `workflow.md` defines stage order, required artifacts, and promotion conditions
- `policy.md` defines workflow-wide decision principles and guardrails
- role files define local responsibilities for one stage and must not override workflow-wide rules
- if a role file conflicts with `workflow.md` or `policy.md`, update the role file rather than inventing a special case

## Completion gate and anti-premature termination

Part-1 completion is not an agent judgment.

This file currently defines a strict completion gate only for Part 1.
The later review-writing phase remains intentionally deferred.

A run is Part-1-complete only when all of these conditions are true:

- `python3 tools/run/completion_gate.py <run_id>` exits with code `0`
- `python3 tools/run/validate_run.py <run_id>` passes
- the active pass `artifacts/workflow_control/workflow_state.json` has `status = complete`
- `Phase1_PubmedCollection/WORKFLOW_NOT_COMPLETE` does not exist
- at least `min_big_workflow_loops` PMC-feedback passes exist
- every PMC-feedback pass used for a learned rerun satisfies the configured PMC full-text review coverage gate
- the latest PMC feedback marks `pdf_deferral_decision = final_pdf_pass`
- no Run Manager loop action remains triggered
- the learned final pass has passed controller prompt-fit-density assessment:
  retained full-text papers are dominated by direct, strong indirect, or
  run-authorized comparator evidence for the user prompt rather than
  background, context-only, incidental, low-relevance, or missing-evidence keeps
- earlier-pass PMC XML and PMC-normalized JSON payloads have been deleted

Agents and harnesses must not say `done`, `complete`, `final`, or `finished`
for the whole two-part workflow unless both parts are later defined and pass
their own gates. In the current structure they may only say that Part 1 is
complete, or that a specific stage is complete, such as `PubMed collection
complete`, `abstract triage first pass complete`, or `PMC import complete`.

Every user-facing final response from an agent or harness must report:

- workflow status: `running`, `loop_required`, `awaiting_pdf_shortlist`, `blocked`, or `complete`
- current stage or next action
- validation result or reason validation was not yet eligible to pass
- Run Manager decision
- remaining required stages when status is not `complete`

Part 1 should also preserve a user-visible transcript:

- path: `runs/<run_id>/Phase1_PubmedCollection/passes/phase1_transcript.md`
- scope: all user and agent words shown during Part 1 across all passes
- purpose: audit trail and troubleshooting when a decision path feels wrong
- rule: append chronological entries; do not replace the transcript with a polished retrospective summary

Full-text review must create pass-to-pass learning, not merely binary
retention. `evidence_extraction.csv` should include per-paper scientific notes
for kept and dropped papers. `pmc_mechanism_feedback.csv` should summarize
topic learning, query-construction learning, abstract-review calibration, and
rescue-review guidance for the Run Manager before the next PubMed pass.

When Part 1 completes, the next required stage must be reported as the user
decision checkpoint:

- `write_from_pmc_now`
- `wait_for_downloaded_pdfs`

After the user chooses to wait for PDFs, the workflow must remain paused for
review writing until the user later gives a clear ready-to-write signal.

Producing a useful intermediate deliverable, ranked pool, summary, shortlist, or
report does not complete this workflow unless the completion gate passes.

The workflow controller must fail closed on incomplete stage handoffs. If an
upstream required artifact exists but has blank required decision fields, row
count mismatches, or incomplete paper-id coverage, the Run Manager must emit an
active loop decision for that exact pending stage before considering higher-level
scientific loop logic or reporting.

## Artifact Contract

The workflow is closed by default. With `artifact_policy = workflow_only`,
agents may write only declared run inputs, pass artifacts, reports, snapshots,
and workflow-control files. They must not create rankings, ad hoc summaries,
analysis scripts, spreadsheets, dashboards, or exports unless a workflow stage
declares them or the user explicitly asks for them in the current turn.

Unexpected active-pass files are validation failures. Side deliverables outside
the run tree are process violations unless explicitly user-requested.

## Roles

The workflow uses four consolidated operational roles. The roles are fewer than
the artifact stages on purpose: one role may own multiple adjacent stages while
the stage artifacts remain separate for auditability and clean workflow contracts.

### 1. Run Manager

Owns setup, orchestration, learned guidance revision, loop decisions, completion
state, and user-facing reporting.

Outputs include:

- pass-scoped run inputs: `run_config.md`, `run_brief.md`
- `artifacts/workflow_control/workflow_loop_decision.csv`
- `artifacts/workflow_control/workflow_state.json`
- `artifacts/workflow_control/run_guidance_revision_log.csv` when guidance changes
- `reports/progress_report.md`
- `reports/final_reading_list.csv`
- `reports/intervention_prompt.md` when PDF fallback requires a decision
- `Phase1_PubmedCollection/passes/phase1_transcript.md`

Working rules:

- preserve `original_user_prompt.md` unchanged
- convert user requests into generic workflow inputs without changing reusable workflow definitions
- distinguish primary retrieval scope from secondary synthesis context
- revise later-pass guidance only after PMC full-text learning satisfies the configured coverage gate
- write learned guidance into the next pass, not into completed pass inputs
- decide whether to continue, pause, loop, build a PDF shortlist, or stop blocked
- in the learned final pass, decide whether poor prompt-fit density requires
  another loop to query reconstruction, abstract-review rule tightening, or
  full-text review recalibration
- never mark Part 1 complete until validation, controller, sentinel, and completion-gate rules pass
- after Part 1 completion, stop for the explicit review-writing checkpoint

### 2. PubMed Search Agent

Owns PubMed query design, query-quality diagnostics, query refinement, exact
collection, deduplication, provenance, and venue-blocklist auditing.

Outputs include:

- `artifacts/search_strategy/search_strategy.md`
- `artifacts/search_strategy/query_diagnostics.csv`
- `artifacts/search_strategy/query_refinement_report.md` when revised
- `artifacts/metadata_collection/paper_manifest.csv`
- `artifacts/metadata_collection/blocked_venue_records.csv` when applicable
- raw metadata records when available

Working rules:

- pass-1 query strategy should be recall-friendly enough to create a useful
  PMC-learning set, while still requiring run-scope anchors
- learned reruns should use full-text scientific notes and PMC feedback to
  retain positive claim-shaped term combinations, rescue missed in-scope
  concepts, and demote terms that produced repeated weak-overlap papers

Working rules:

- derive and obey the run's query-scope contract before writing query strings
- keep first-pass queries recall-friendly but anchored to declared entities plus mechanism/evidence classes
- use sampling to detect precision, drift, missing concepts, and tail risk
- in learned reruns, use revised guidance plus PMC mechanism feedback
- collect every record from each accepted query without hidden caps
- do not filter scientific relevance between retrieval and abstract triage, except for cross-pass exclusion of papers already rejected and recorded in the run-level SQLite state

### 3. Abstract Triage Agent

Owns both abstract-triage passes: first-pass relevance triage and targeted
rescue review. The role is consolidated, but `first_pass.csv`
and `second_pass.csv` remain separate artifacts.

Outputs include:

- `artifacts/abstract_triage/first_pass.csv`
- `artifacts/abstract_triage/second_pass.csv`

Working rules:

- every collected paper must receive first-pass and second-pass abstract decisions
- first pass assigns `include` or `exclude` from title, abstract, publication type, and run guidance
- second pass carries first-pass includes forward and rereads first-pass excludes for rescue signals
- second pass may confirm or overturn, then writes `promotion_decision` as `advance_to_import` or `stop`
- the rescue-review output is recorded into the run-level SQLite database so rejected papers do not re-enter later passes by default
- review-frame retention can preserve a minority of field-synthesis, foundational, or perspective papers
- PDF availability, import burden, and desired cohort size are not abstract-stage exclusion reasons

### 4. Full-Text Evidence Agent

Owns PMC/PDF acquisition, parsing, normalization, access accounting, evidence
extraction, PMC mechanism feedback, PDF shortlisting, and full-text keep/drop
review.

Outputs include:

- `artifacts/fulltext_import/import_status.csv`
- `artifacts/fulltext_import/manual_pdf_queue.csv`
- `artifacts/fulltext_import/pdf_download_shortlist.csv`
- `artifacts/fulltext_import/manual_pdf_import_report.csv` when applicable
- `artifacts/fulltext_import/pdf_parse_report.csv` when applicable
- PMC XML and normalized JSON when usable
- `artifacts/fulltext_review/evidence_extraction.csv`
- `artifacts/fulltext_review/pmc_mechanism_feedback.csv`
- `artifacts/fulltext_review/fulltext_review.csv`

Working rules:

- use PMC first and record unusable PMC separately from missing PMC access
- queue manual PDFs when needed, but keep them deferred during PMC-learning unless policy requires full-text completion
- review every readable normalized full text before treating import as complete
- never treat unavailable full text as a scientific `drop`
- require sentence-level or local section-level evidence for final `keep` decisions
- before final access, use PMC-readable papers to learn mechanisms, noise families, missing terms, and query changes
- build `pdf_download_shortlist.csv` only when PMC learning reaches `final_pdf_pass`

## Proposed Part Boundary

Part 1 ends after the final reading list and PDF shortlist are ready.

At that point the workflow must pause and ask the user:

1. use only PMC full text to write the review now
2. wait for the user to provide downloaded PDFs first

If the user chooses option 2, the workflow must not:

- begin review writing
- treat the raw downloaded PDFs as automatically accepted
- parse and normalize those PDFs early just because a queue exists

Instead, the workflow must wait.
Only after the user later says they are ready to write should the workflow:

1. parse and normalize the user-provided PDFs
2. apply the usual full-text retention logic to those newly readable papers
3. report how many PDFs were retained into the writing corpus
4. begin the later Part-2 review-writing workflow

## Stage handoffs

### User -> Run Manager

Required input:

- free-form user prompt

Required outputs:

- `runs/<run_id>/original_user_prompt.md`
- `runs/<run_id>/Phase1_PubmedCollection/passes/pass_001/inputs/run_config.md`
- `runs/<run_id>/Phase1_PubmedCollection/passes/pass_001/inputs/run_brief.md`
- `runs/<run_id>/Phase1_PubmedCollection/passes/phase1_transcript.md`

Promotion rule:

- `original_user_prompt.md` must preserve the exact starting prompt without rewriting
- the opening user request and the agent's visible setup guidance should be appended to `Phase1_PubmedCollection/passes/phase1_transcript.md`
- downstream stages must consume run files as inputs rather than rewriting reusable workflow files

### Run Manager -> PubMed Search Agent

Required inputs:

- current pass `inputs/run_config.md`
- current pass `inputs/run_brief.md`

Required outputs:

- a scoped search objective and query-design context captured in `search_strategy.md`
- a query-scope contract or equivalent section in `search_strategy.md` that states primary entities, declared mechanism classes, comparator scope, secondary context, and deferred adjacent biology
- if `run_brief.md` review/synthesis framing section exists, only its explicit foundational recall terms or authorized comparator context may appear in first-pass query design

### Full-Text Evidence Agent + Run Manager -> Learned Guidance Revision

Required inputs:

- current pass `inputs/run_brief.md`
- `artifacts/fulltext_review/pmc_mechanism_feedback.csv`
- `artifacts/search_strategy/query_diagnostics.csv`
- review/import artifacts from the completed pass
- `passes/`

Required outputs:

- revised `passes/pass_###/inputs/run_brief.md`
- `artifacts/workflow_control/run_guidance_revision_log.csv`

Promotion rule:

- this handoff is required before every learned rerun triggered by `pdf_deferral_decision = defer_pdfs`
- `original_user_prompt.md` must remain unchanged
- the revision log must name the feedback loop ID and the concrete retained mechanisms, missing terms, noise exclusions, review/synthesis framing changes, and reviewer rules added to guidance
- the next learned `search_strategy.md` must be generated from the revised `run_brief.md` and PMC feedback

### PubMed Search Agent: Query Design -> Collection

Required inputs:

- current pass `inputs/run_brief.md`
- current pass `inputs/run_brief.md`
- current pass `inputs/run_brief.md` review/synthesis framing section
- current pass `inputs/run_brief.md` constraints section
- optional retrieval feedback from a previous pass
- for learned reruns, `run_guidance_revision_log.csv` row covering the latest `defer_pdfs` PMC feedback loop

Required outputs:

- one or more PubMed query strings
- rationale for each query
- search-strategy record at `artifacts/search_strategy/search_strategy.md`
- structured diagnostics at `artifacts/search_strategy/query_diagnostics.csv`
- `query_refinement_report.md` when the strategy changes after retrieval inspection

Promotion rule:

- if latest PMC feedback says `defer_pdfs`, PubMed collection must not run until guidance revision has been recorded for that feedback loop
- query refinement must respond to observed precision or recall problems, not an arbitrary desire for a smaller cohort
- query refinement must remain inside the declared mechanism classes unless the run guidance revision explicitly changes the query-scope contract
- clear topics should usually stop query optimization after a small number of productive rounds
- vague topics may need exploratory rounds, but optimization should stop when diagnostics plateau or further tightening would threaten recall

### PubMed Search Agent -> Abstract Triage Agent

Required outputs:

- `artifacts/metadata_collection/paper_manifest.csv`
- `artifacts/metadata_collection/blocked_venue_records.csv` when any collected
  paper matches the reusable venue blocklist
- one stable paper row per PMID
- title, abstract, PMID, DOI when present, year when present, and source-query provenance

Promotion rule:

- the reusable venue blocklist must be applied during collection, before papers
  enter `paper_manifest.csv`
- blocked venues must be recorded in `blocked_venue_records.csv`, not silently
  dropped
- the collected cohort is the abstract-triage cohort
- do not create a hidden shortlist between collection and abstract triage

### Abstract Triage Agent: First Pass -> Second Pass

Required outputs:

- `artifacts/abstract_triage/first_pass.csv`
- per-paper `first_pass_decision`
- per-paper rationale and confidence

Promotion rule:

- every collected paper must receive an abstract-stage decision before second-pass review begins

### Abstract Triage Agent -> Full-Text Evidence Agent

Required outputs:

- `artifacts/abstract_triage/second_pass.csv`
- adjudicated second-pass decision
- per-paper `promotion_decision` resolved to either `advance_to_import` or `stop`
- original title and abstract retained in the second-pass table or equivalent
  reviewer packet so adjudication does not rely only on reviewer prose

Promotion rule:

- only `advance_to_import` papers move to the import stage
- `Abstract Triage Agent` is an adjudicator, not a stricter cost-control filter
- the second internal abstract-triage pass must use the title, abstract, first decision, and first rationale together

### Full-Text Evidence Agent: Import -> Review

Required outputs:

- `artifacts/fulltext_import/import_status.csv`
- full-text availability state
- PMC usability state
- PDF fallback state
- normalized file path when parsing succeeds

Additional required outputs when applicable:

- `artifacts/fulltext_import/manual_pdf_queue.csv` when manual PDF fallback is needed
- `artifacts/fulltext_import/pdf_download_shortlist.csv` only when the latest PMC mechanism feedback says `final_pdf_pass`
- `artifacts/fulltext_import/pdf_parse_report.csv` when any staged PDF is parsed or attempted
- `artifacts/fulltext_import/manual_pdf_import_report.csv` when any user-provided PDF is staged
- `artifacts/fulltext_import/pdf_intervention_status.json` and `reports/intervention_prompt.md` when run policy requires a visible checkpoint

Promotion rule:

- when a later pass advances a paper whose PMC-normalized full text was already
  read in an earlier pass, reuse the prior normalized full-text artifact rather
  than downloading and normalizing PMC XML again
- reused normalized full text must still be reviewed under the active pass's
  current run guidance and final-pass evidence rules; prior review decisions
  are learning context, not automatic final-pass decisions
- only papers with readable normalized full text advance to full-text review
- papers lacking readable full text remain unresolved for access, not scientifically excluded
- after manual PDF ingest, newly normalized full text should be reviewed before the ingest cycle is treated as complete
- before the final calibrated access pass, do not ask for manual PDFs; use PMC-readable papers to generate mechanism and query feedback first
- after PMC mechanism feedback, do not create a PDF download shortlist while the controller is still looping back to query/review
- in the final PMC-satisfied loop, create the PDF download shortlist regardless of whether the eventual downloader is a human or another agent
- the final-loop shortlist is required to explain which queued PDFs should be requested now, deferred, or not requested

### Full-Text Evidence Agent -> Run Manager

Required outputs:

- `artifacts/fulltext_review/evidence_extraction.csv`
- `artifacts/fulltext_review/pmc_mechanism_feedback.csv`
- `artifacts/fulltext_review/fulltext_review.csv`
- per-paper evidence tier, evidence type, directness, centrality, and query-feedback signal
- summarized mechanisms, retained keyword families, noise keyword families, and recommended query changes
- per-paper final `keep` or `drop` decision
- rationale
- confidence
- normalized file path

Promotion rule:

- papers without readable full text are not converted into reviewer drops
- final `keep` should be supported by a non-background evidence tier, or by an explicit authorized review-frame role recorded for a minority of foundational/perspective papers
- final `keep` requires sentence-level or local section-level evidence that
  ties the mechanism/evidence claim to the target entity/system and required
  outcome/relationship. Whole-document co-occurrence may justify query feedback
  or background context, but not direct retention.
- before the final calibrated access pass, `pmc_mechanism_feedback.csv` must be reviewed by the Run Manager before any PDF intervention is requested

### Run Manager -> Earlier Stage Or Reporting

Required inputs:

- `query_diagnostics.csv`
- `first_pass.csv`
- `second_pass.csv`
- `import_status.csv`
- `evidence_extraction.csv`
- `pmc_mechanism_feedback.csv`
- `fulltext_review.csv`

Required outputs:

- `artifacts/workflow_control/workflow_loop_decision.csv`
- `artifacts/workflow_control/workflow_state.json`

Promotion rule:

- if no loop trigger fires, continue to Run Manager
- if fewer than `min_big_workflow_loops` big passes have completed, loop to `pubmedSearchAgent` even when PMC feedback says `final_pdf_pass`
- if a query loop fires, send concrete query-revision instructions to `pubmedSearchAgent`
- if a reviewer-calibration loop fires, rerun the affected review stage with revised evidence definitions
- if a human PDF checkpoint fires, pause according to `run_config.md`, but only after PMC-learning loops are complete unless full-text completion was explicitly required from the start
- every loop must record a stop condition before it starts

### Run Manager -> User

Required outputs:

- `reports/progress_report.md`
- `reports/final_reading_list.csv`
- `reports/intervention_prompt.md` when policy requires a pause or explicit user choice

Required reporting content:

- count of retained papers
- count of unusable PMC papers
- count of papers lacking PMC access
- manual PDF queue when needed
- abstract-relevant but full-text-unavailable papers when they remain unresolved

## Stage outputs

All stage outputs are pass-scoped. For pass `N`, the durable locations are:

1. `passes/pass_NNN/artifacts/search_strategy/`
2. `passes/pass_NNN/artifacts/metadata_collection/`
3. `passes/pass_NNN/artifacts/abstract_triage/`
4. `passes/pass_NNN/artifacts/fulltext_import/`
5. `passes/pass_NNN/artifacts/fulltext_review/`
6. `passes/pass_NNN/artifacts/workflow_control/`
7. `passes/pass_NNN/reports/`

Scripts must resolve the active pass from `Phase1_PubmedCollection/passes/active_pass.json` and read or write inside that pass directory. The run root must not contain pass-neutral `artifacts/` or `reports/` folders or symlink pointers.

Expected canonical artifacts for each pass:

- `artifacts/search_strategy/search_strategy.md`
- `artifacts/metadata_collection/paper_manifest.csv`
- `artifacts/metadata_collection/blocked_venue_records.csv` when venue policy
  blocks any papers during collection
- `artifacts/abstract_triage/first_pass.csv`
- `artifacts/abstract_triage/second_pass.csv`
- `artifacts/fulltext_import/import_status.csv`
- `artifacts/fulltext_import/manual_pdf_queue.csv`
- `artifacts/fulltext_import/pdf_parse_report.csv`
- `artifacts/fulltext_review/evidence_extraction.csv`
- `artifacts/fulltext_review/pmc_mechanism_feedback.csv`
- `artifacts/fulltext_review/fulltext_review.csv`
- `artifacts/workflow_control/workflow_loop_decision.csv`
- `reports/final_reading_list.csv`
- `reports/progress_report.md`

Optional but important control artifacts:

- `artifacts/fulltext_import/pdf_intervention_status.json`
- `artifacts/fulltext_import/manual_pdf_import_report.csv`
- `reports/intervention_prompt.md`

Run-level state:

- `Phase1_PubmedCollection/workflow_state.sqlite`

The SQLite database is a run-level control store, not a pass-specific
scientific artifact. It records stable paper identity, per-pass abstract-triage
decisions, and the latest cross-pass status for each paper. Learned PubMed
collections must consult this database before writing the active
`paper_manifest.csv` so papers rejected in earlier passes do not re-enter later
passes by default. Reopening a rejected paper requires an explicit future
workflow rule or user/Run Manager intervention; silent re-entry is not allowed.

## Run layout

Each run should have its own folder:

`runs/<run_id>/`

Minimum expected files:

- `original_user_prompt.md`
- `original_user_prompt.md` at the run root
- `passes/pass_001/inputs/run_config.md`
- `passes/pass_001/inputs/run_brief.md`
- `passes/pass_001/inputs/run_brief.md`
- optional `passes/pass_001/inputs/run_brief.md` review/synthesis framing section
- `passes/pass_001/inputs/run_brief.md` optional

Pass 1 must also contain:

- `passes/pass_001/artifacts/`
- `passes/pass_001/reports/`

Later passes must have the same three-part structure:

- `passes/pass_###/inputs/`
- `passes/pass_###/artifacts/`
- `passes/pass_###/reports/`

Each run must preserve durable pass snapshots under:

`runs/<run_id>/Phase1_PubmedCollection/passes/pass_###/`

Each pass directory should contain:

- `inputs/`
  Pass-specific guidance and run inputs.
- `artifacts/`
  Machine-readable artifacts for that pass.
- `reports/`
  User-facing reports for that pass.
- `snapshot_manifest.json`
  Pass counts, snapshot reason, latest PMC feedback state, and key stage row counts.

The run root must stay clean: Part-1 outputs belong only under `Phase1_PubmedCollection/passes/pass_###/artifacts/` and `Phase1_PubmedCollection/passes/pass_###/reports/`.

Before a learned rerun starts, create or activate the next pass directory and write its revised inputs there. After the Run Manager evaluates a pass, write `snapshot_manifest.json` inside that pass directory.

Later passes are not scratch spaces for query correction. Pass `N+1` may be
activated only after pass `N` has completed collection, both abstract-triage passes,
PMC/full-text import, full-text review of readable papers, and a
`pmc_mechanism_feedback.csv` row whose `pdf_deferral_decision = defer_pdfs`.
If pass `N` has not reached that point, agents must continue pass `N` rather
than activating pass `N+1`.

## Portability rule

Any model or harness may perform a role if it can:

- read the relevant input artifact
- write the required output artifact
- follow the schema and policy documents

The workflow contract is primary. The model runtime is replaceable.

## Resolution rule

The two internal passes of `Abstract Triage Agent` are expected to resolve every paper at their stage.

This is a brute-force review rule, not a shortlist rule.

If `pubmedSearchAgent` produces a cohort of potentially related papers, every paper in that cohort must pass through both abstract-triage passes:

- first-pass abstract triage
- second-pass abstract adjudication

Batching is allowed only for context management.
Batching must not be used to silently reduce the review cohort before abstract triage.

At abstract stage, each paper must end in one of two actionable states:

- `advance_to_import`
- `stop`

Abstract promotion requires the run's claim shape. Entity-only, mechanism-only,
outcome-only, or context-only matches must stop unless the run contract
explicitly grants a review/synthesis retention role and the paper is needed as a
minority field-synthesis/background item.

At final output stage, retained papers may end in one of two states:

- `selected_for_reading`
- `abstract_relevant_fulltext_unavailable`

## Agentic loop rule

This workflow is not strictly linear.
After query optimization, abstract triage, full-text import, and full-text review, the Run Manager must decide whether to continue, pause, or loop.

The workflow has exactly two big passes.
A big pass means an end-to-end run through query design or revision, PubMed collection, abstract triage, rescue abstract-triage pass, PMC import, full-text review of readable normalized papers, and `pmc_mechanism_feedback.csv`.

PMC feedback must pass the configured full-text review gate before it can unlock a learned rerun. The strict default is `pmc_fulltext_review_gate_mode = all_available`, which requires every paper marked `pmc_access_status = available` in `import_status.csv` to have a normalized full text, a full-text review decision, and a matching evidence-extraction row. A partial PMC sample is allowed only as a progress checkpoint; it must not drive pass activation, run-guidance revision, or learned query reconstruction.

Mandatory pass structure:

- Pass 1: slightly permissive PMC-learning pass. The PubMed Search Agent searches the user-declared entities and mechanism classes, plus only explicitly authorized comparator queries. Abstract triage may admit a bounded learning-probe set when abstracts contain a primary run anchor plus either declared mechanism/evidence terms or required outcome terms. The full-text reviewer writes per-paper scientific notes, `evidence_extraction.csv`, and `pmc_mechanism_feedback.csv` with `pdf_deferral_decision = defer_pdfs` unless `require_fulltext_completion` is set.
- Pass 2: final learned in-scope pass. The Run Manager first applies Pass 1 retained in-scope mechanisms, noise families, missing terms, review/synthesis framing calibration, scientific notes, rescue-review guidance, and reviewer-calibration changes to `run_brief.md`; then the PubMed Search Agent generates a stringent learned search strategy from the revised `run_brief.md` plus PMC feedback while staying inside the query-scope contract; then the workflow reruns collection, abstract triage, rescue review, PMC import, and full-text review. Pass 2 is the only learned rerun and must be written as the final calibrated pass.
- Pass 2 import should first check pass 1 usable PMC-normalized full text for
  papers that reappear. Reuse those normalized artifacts and then rerun
  full-text review under pass 2's stricter learned guidance.
- Pass 2 abstract triage is a learned final-pass adjudication, not a duplicate
  recall pass. It must re-evaluate first-pass includes against local,
  claim-shaped prompt-fit evidence and must treat prior-pass full-text drops as
  negative controller memory unless the active pass documents a stronger rescue
  signal.
- If pass 2 expands the collection or fails to substantially shorten abstract-triage promotion, the Run Manager records a confirmation signal. The run may proceed only if the revision log explains why the larger or similar-sized set is caused by newly learned in-scope vocabulary rather than secondary context, comparator, assay, population, intervention, or outcome terms becoming standalone drivers.
- The workflow philosophy is that pass 1 spends breadth to buy learning, and
  pass 2 spends that learning to buy focus. Pass 2 should therefore be written
  as a more discriminating strategy before it is measured. Count comparisons are
  sanity checks; the primary obligation is that learned terms, exclusions, and
  reviewer rules make weak contextual matches less likely to enter the next
  full-text burden.
- Pass 2 may emit `final_pdf_pass` only after evidence shows the query/review criteria have absorbed the PMC learning.
- Once `final_pdf_pass` is accepted after the minimum learned loops, the Run Manager records the effective access phase as `final_access`.
- If pass 2 still has persistent evidence-grounded failures such as missing concepts, recurrent query noise, reviewer drift, weak final keeps, or a large low-value PDF queue, the Run Manager must stop blocked or ask for human/parent-agent intervention. It must not activate pass 3 automatically.

Loops are allowed when an artifact shows a specific failure mode:

- query diagnostics show dominant noise classes that can be removed without obvious recall loss
- abstract triage advances a very large fraction of the cohort with weak or generic rationales
- pass 2 tries to reacquire papers that a prior pass already read as low-yield
  full text without documenting a stronger active-pass rescue signal
- learned rerun collection or `advance_to_import` counts do not materially decrease relative to the previous pass and the revision log does not justify this with newly learned in-scope vocabulary
- the second internal abstract-triage pass frequently overturns the first pass for the same reason
- PMC full-text reading identifies in-scope mechanism terms that should replace vague query terms
- import creates a large PDF queue after PMC learning and the queued papers are traceable to a predictable query-noise pattern
- PMC-learning is marked `final_pdf_pass` and there is a non-empty PDF queue but no PDF download shortlist
- full-text evidence extraction shows many kept papers are indirect, background, expression-only, or marker-only without an authorized review-frame role
- full-text evidence extraction reveals a missing in-scope term family that should become a rescue query
- fewer than the required two big passes have completed

Loops are not allowed for vague discomfort with cohort size. Discomfort becomes
actionable only when the controller can trace it to weak prompt-fit density,
generic promotion rationales, repeated prior full-text drops, or another named
artifact-level failure mode.
Every loop decision must name:

- the triggering artifact
- the observed failure mode
- the earlier stage to revisit
- the concrete change to make
- the stop condition for the next pass

Default loop targets:

- query noise or missing concepts: loop to `pubmedSearchAgent`
- inconsistent abstract criteria: loop to the appropriate internal pass of `Abstract Triage Agent`
- overbroad full-text keeps: loop to `fullTextEvidenceAgent` with stricter evidence-tier rules
- large low-value PDF queue before final access: keep PDFs deferred, read PMC evidence, and loop to `pubmedSearchAgent`
- missing PDF download shortlist after final PMC-satisfied learning: build `pdf_download_shortlist.csv` before reporting completion

The Run Manager must also write `workflow_state.json`.
This state file is the portable completion contract for agent harnesses.
It should say `status = complete` only when no loop is active and the final-loop PDF download shortlist exists for any remaining manual PDF queue.
It should record `access_phase = final_access` before any complete state.
It must not say `status = complete` until exactly two PMC-feedback passes exist and pass 2 feedback marks `final_pdf_pass`.
Before the completion gate accepts that state, it must delete prior-pass PMC XML
and PMC-normalized JSON payloads while preserving structured pass artifacts.

## Batching rule

This workflow should process literature in bounded LLM batches.

Batch size should be chosen for stable judgment quality, not merely to fill the model context window.
Batching applies after collection and never authorizes capped PubMed retrieval.

These batches are execution batches only.
They are not permission to replace full abstract triage with a smaller shortlist when the collected cohort is large.

Recommended defaults by model tier:

- frontier model
  - PubMed search inspection: `10-15` records per call
  - abstract triage: `10-20` abstracts per call
  - second abstract-triage pass: `8-15` abstracts per call
  - full-text review: `2-5` papers per call
- solid mid-tier model
  - PubMed search inspection: `8-12` records per call
  - abstract triage: `8-12` abstracts per call
  - second abstract-triage pass: `6-10` abstracts per call
  - full-text review: `1-3` papers per call
- smaller or weaker model
  - PubMed search inspection: `5-10` records per call
  - abstract triage: `5-8` abstracts per call
  - second abstract-triage pass: `4-6` abstracts per call
  - full-text review: `1-2` papers per call

Working sets may span hundreds or thousands of papers when the accepted query set justifies that breadth.
They should be split across multiple calls rather than pushed into one oversized context window.

Shrink the batch if the model:

- confuses one paper with another
- gives shallow or repetitive rationales
- misses obvious details present in the supplied text
- starts making batch-level rather than paper-level judgments

## PDF intervention rule

When the PDF queue is non-empty, behavior should follow `run_config.md`.

PDF intervention is a final-access behavior by default.
In earlier loops, preserve the queue as an access artifact while the workflow reads PMC-normalized papers, summarizes mechanisms and noise, and reconstructs the query.
After PMC mechanism feedback exists, build a ranked `pdf_download_shortlist.csv` only when pass 2 feedback says `final_pdf_pass`.
`final_pdf_pass` is ignored for PDF access in pass 1.
This final-loop shortlist is generated regardless of whether the eventual downloader is a human user or another agent.
It should be much smaller than the raw queue because previous PMC-learning loops have already removed predictable noise.

- `pause_for_user`
  pause and prompt the user with explicit choices only after PMC-learning loops have ended or been deliberately skipped and the final-loop PDF download shortlist exists
- `continue_pmc_only`
  continue with PMC-normalized papers, use them to improve the query, build the PDF shortlist only in the final PMC-satisfied loop, and preserve non-shortlisted PDF queue items as deferred work
  report that non-PMC full text may remain unresolved because of paywalls, bot walls, or unavailable manual PDF input
- `require_fulltext_completion`
  block downstream progression until the PDF queue is addressed

If the user chooses `provide_pdfs_then_continue`:

- scan the user-specified drop folder for PDFs
- match files to the queue by DOI, PMID, paper ID, or title overlap
- rename staged PDFs to stable run-local names
- record the original downloaded filename
- parse staged PDFs through the shared PDF parser hook when available
- normalize successful TEI output to the same JSON contract used by full-text review
- leave staged PDFs in explicit `parser_pending` or `parse_failed` state when parsing is not yet successful
- reduce the outstanding queue to unresolved papers
- continue with PMC-normalized papers plus any staged PDFs that later parse successfully

This is a single continuation path.
The workflow must not distinguish between "all PDFs" and "some PDFs" at the contract level.

Manual PDF staging and parsing are allowed after the final-loop shortlist exists,
even if the run began in `pmc_learning`.
The executable signal is the combination of latest PMC feedback `final_pdf_pass`
plus `pdf_download_shortlist.csv`.
