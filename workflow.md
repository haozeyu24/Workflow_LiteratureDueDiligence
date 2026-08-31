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
5. run a second abstract review over the same paper plus the first review opinion
6. acquire and normalize PMC full text first
7. use PMC full text to summarize mechanisms, noise, and query-feedback signals
8. require the configured PMC full-text review coverage gate to pass, then revise run guidance from PMC full-text learning, reconstruct the query, and rerun collection, abstract review, PMC import, and full-text review at least once using PMC-derived learning
9. decide whether additional learned loops are needed before spending effort on PDFs
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
- abstract review preserves plausible decision-relevant papers, not anything
  that could ever be related
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

- `python3 scripts/completion_gate.py <run_id>` exits with code `0`
- `python3 scripts/validate_run.py <run_id>` passes
- the active pass `artifacts/workflow_control/workflow_state.json` has `status = complete`
- `Phase1_PubmedCollection/WORKFLOW_NOT_COMPLETE` does not exist
- at least `min_big_workflow_loops` PMC-feedback passes exist
- every PMC-feedback pass used for a learned rerun satisfies the configured PMC full-text review coverage gate
- the latest PMC feedback marks `pdf_deferral_decision = final_pdf_pass`
- no controller loop action remains triggered
- earlier-pass PMC XML and PMC-normalized JSON payloads have been deleted

Agents and harnesses must not say `done`, `complete`, `final`, or `finished`
for the whole two-part workflow unless both parts are later defined and pass
their own gates. In the current structure they may only say that Part 1 is
complete, or that a specific stage is complete, such as `PubMed collection
complete`, `abstract review 1 complete`, or `PMC import complete`.

Every user-facing final response from an agent or harness must report:

- workflow status: `running`, `loop_required`, `awaiting_pdf_shortlist`, `blocked`, or `complete`
- current stage or next action
- validation result or reason validation was not yet eligible to pass
- controller decision
- remaining required stages when status is not `complete`

Part 1 should also preserve a user-visible transcript:

- path: `runs/<run_id>/Phase1_PubmedCollection/passes/phase1_transcript.md`
- scope: all user and agent words shown during Part 1 across all passes
- purpose: audit trail and troubleshooting when a decision path feels wrong
- rule: append chronological entries; do not replace the transcript with a polished retrospective summary

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
count mismatches, or incomplete paper-id coverage, the controller must emit an
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

### 1. Run Setup Agent

Transforms a user request into run-specific workflow inputs.

Input:

- free-form user request

Output:

- `run_config.md`
- `instruction.md`
- `topic.md`
- optional `review_frame.md`
- optional run constraints
- a query-scope contract, either inside `instruction.md`, `topic.md`, or `constraints.md`

The `runSetupAgent` role is required because the workflow is reusable but the scientific question changes from run to run.

The `runSetupAgent` must convert a user request into generic workflow inputs without changing the workflow definition itself.

The setup output must distinguish primary retrieval scope from secondary
synthesis context. Primary retrieval scope includes the named entities and the
mechanism classes the user actually asked to learn. Secondary context may include
adjacent pathways, phenotypes, disease settings, comparators, or downstream
interpretive biology, but secondary context must not become first-pass PubMed
query scope unless the user explicitly requested it.

When the downstream deliverable is review-like, the setup output should also
separate review-article framing from retrieval scope by writing
`review_frame.md`. That file should capture introduction obligations,
foundational field context, field-progress framing, and perspective questions.
It may justify targeted recall safeguards and a minority of retained background
papers, but it must not silently broaden first-pass PubMed retrieval.

### 2. PubMed Keyword Scout

Builds the PubMed search strategy from the current instruction and topic, then refines it after inspecting retrieval noise or coverage gaps when needed. In learned reruns, the scout must use the revised guidance plus PMC mechanism feedback, not the original guidance alone.

Output:

- search plan
- PubMed query strings
- search rationale
- query diagnostics
- query refinement report when revised

Working rule:

- derive and obey the run's query-scope contract before writing query strings
- first-pass query generation should be conservative and limited to the declared entities plus declared mechanism classes
- first-pass query generation should require claim-shaped retrieval logic:
  declared entity or system plus declared mechanism/evidence class plus required
  outcome, relationship, perturbation, response, or other evidence-claim term
- first-pass query generation should require claim-shaped retrieval logic:
  declared entity or system plus declared mechanism/evidence class plus required
  outcome, relationship, perturbation, response, or other evidence-claim term
- add synonyms, assays, and rescue terms only within declared mechanism classes
- do not expand into adjacent biology merely because it is plausibly related or compensatory
- refine based on sampled precision and coverage, not hit count alone
- retrieve broadly enough to capture direct and plausible decision-relevant papers inside the declared query scope
- do not narrow the collected cohort into a smaller pre-review working set
- if a paper is plausibly decision-relevant inside the declared scope at the scouting stage, it belongs in the collected cohort for abstract review
- PubMed collection is recall-first and must have no record cap
- agents and harnesses must not introduce per-query, total, date-sorted, top-N, or equivalent PubMed collection caps
- use query optimization, not hidden retrieval caps, to produce a reasonably accurate candidate cohort
- use batching for model context management, not for shrinking the search or abstract-review cohort

### 3. Run Guidance Reviser

Revises `instruction.md`, `topic.md`, optional `review_frame.md`, optional `constraints.md`, and reviewer-facing rules after PMC full-text learning and before a learned PubMed rerun.

Input:

- current `instruction.md`
- current `topic.md`
- optional `review_frame.md`
- optional `constraints.md`
- `pmc_mechanism_feedback.csv`
- `query_diagnostics.csv`
- review/import outcomes
- pass snapshots

Output:

- revised `instruction.md`
- revised `topic.md`
- optional revised `review_frame.md`
- optional revised `constraints.md`
- `artifacts/workflow_control/run_guidance_revision_log.csv`

Working rule:

- `original_user_prompt.md` is immutable
- `passes/pass_001/inputs/instruction.md`, `passes/pass_001/inputs/topic.md`, and optional `passes/pass_001/inputs/review_frame.md` are immutable base/pass-1 guidance after run setup
- learned guidance for later passes must be written under `passes/pass_###/inputs/`
- every guidance revision must cite the PMC feedback loop that triggered it
- learned `search_strategy.md` must be generated after this revision from the revised guidance plus PMC feedback
- PMC-derived changes may add in-scope synonyms, assays, entities, exclusions, or reviewer rules by default
- PMC-derived adjacent mechanism classes must remain secondary context unless the revision explicitly updates the query-scope contract and explains why the original user request authorizes the broader primary scope

### 4. PubMed Collector

Executes the search and downloads title, abstract, and metadata.

Output:

- paper manifest
- source metadata records

### 5. Abstract Reviewer

Reads title and abstract to judge topic relevance.

Output:

- abstract review table
- review-paper retention should preserve directly overlapping or bigger-field
  review papers when they can help Phase 2 position the new review against
  prior reviews

### 6. Abstract Reviewer 2

Reads the original abstract again together with the first abstract reviewer's decision and rationale, then makes a second-pass decision.

Output:

- second-pass abstract review table
- review-paper preservation check for Phase-2 introduction positioning

### 7. Full-Text Importer

Acquires full text, preferring PMC.
Before the final calibrated access pass, PDF fallback is recorded as deferred access work rather than acted on.

Output:

- PMC acquisition report
- manual PDF queue
- PDF download shortlist only in the final PMC-satisfied loop
- PDF import report
- PDF intervention status when user or parent-agent policy requires a decision

Completion rule:

- manual PDF ingest is not considered complete just because files were staged or parsed
- any newly readable normalized full text must be handed immediately to full-text review in the same agent-driven pass when possible
- the only acceptable post-ingest unresolved state is access-related, not "normalized but not yet judged"
- early PMC-learning loops must not ask the user to download PDFs unless `run_config.md` explicitly requires complete full-text access from the beginning
- a non-empty manual PDF queue after PMC-learning must remain deferred while controller feedback says another query loop is needed
- generate `pdf_download_shortlist.csv` only when the controller is satisfied with PMC learning and the latest PMC feedback says `final_pdf_pass`

### 8. Full-Text Reviewer

Reads normalized full text, extracts structured evidence, summarizes PMC mechanism/query feedback, and makes the final keep/drop judgment when the run reaches the final review pass.

Output:

- evidence extraction table
- PMC mechanism feedback table
- full-text review table
- final included set

Constraint:

- only papers with readable normalized full text are eligible for full-text review
- papers advanced from abstract review but lacking readable full text remain unresolved for access, not scientifically excluded
- when new readable full text appears after PMC import or manual PDF ingest, the workflow should continue directly into keep/drop review before reporting the ingest cycle as complete
- before the final access pass, the most important full-text output is query-learning feedback, not resolution of the PDF queue
- when PMC-learning feedback says `defer_pdfs`, use it to refine the next query/review loop rather than scoring PDFs for download
- when PMC-learning feedback says `final_pdf_pass`, score the remaining PDF queue into request/defer/do-not-request classes
- if user-provided PDFs are later normalized for review writing, apply the same keep/drop retention logic before counting them as part of the writing corpus
- the PDF shortlist should be recall-friendly because downloaded PDFs still face parsing, normalization, and full-text retention review later; papers that survived `abstractReviewer2` should usually remain `request_pdf` unless they are explicit learned-noise cases

### 10. Workflow Controller

Reads structured evidence and stage metrics, then decides whether the workflow should continue, pause, or loop back to an earlier stage.

Output:

- workflow loop decision table
- concrete revision instructions when a loop is triggered

Working rule:

- loops must be triggered by evidence-grounded failure modes, not by a generic desire for fewer papers
- the first PMC-learning pass must trigger a learned rerun of the whole query-to-full-text path
- final PDF access is blocked until at least `min_big_workflow_loops` PMC-feedback passes exist
- query loops should reduce predictable noise before additional PMC/PDF work when recall can be preserved
- pre-final loops should mine PMC full text for mechanism terms and noise patterns before any manual PDF effort
- after Part 1 completion, stop and request an explicit user decision about PMC-only writing versus waiting for downloaded PDFs
- after a `wait_for_downloaded_pdfs` decision, do not advance toward review writing until the user later provides a clear ready-to-write signal

### 11. Reporter

Produces user-facing summaries and status counts.

Output:

- progress report
- final reading list
- explicit post-Part-1 user checkpoint asking whether to write from PMC only or wait for downloaded PDFs
- after user-provided PDFs are parsed later, a retained-PDF count before any Phase-2 writing begins

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

### User -> Run Setup Agent

Required input:

- free-form user prompt

Required outputs:

- `runs/<run_id>/original_user_prompt.md`
- `runs/<run_id>/Phase1_PubmedCollection/passes/pass_001/inputs/run_config.md`
- `runs/<run_id>/Phase1_PubmedCollection/passes/pass_001/inputs/instruction.md`
- `runs/<run_id>/Phase1_PubmedCollection/passes/pass_001/inputs/topic.md`
- optional `runs/<run_id>/Phase1_PubmedCollection/passes/pass_001/inputs/review_frame.md`
- optional `runs/<run_id>/Phase1_PubmedCollection/passes/pass_001/inputs/constraints.md`
- `runs/<run_id>/Phase1_PubmedCollection/passes/phase1_transcript.md`

Promotion rule:

- `original_user_prompt.md` must preserve the exact starting prompt without rewriting
- the opening user request and the agent's visible setup guidance should be appended to `Phase1_PubmedCollection/passes/phase1_transcript.md`
- downstream stages must consume run files as inputs rather than rewriting reusable workflow files

### Run Setup Agent -> PubMed Keyword Scout

Required inputs:

- current pass `inputs/run_config.md`
- current pass `inputs/instruction.md`
- current pass `inputs/topic.md`
- optional current pass `inputs/review_frame.md`
- optional current pass `inputs/constraints.md`

Required outputs:

- a scoped search objective and query-design context captured in `search_strategy.md`
- a query-scope contract or equivalent section in `search_strategy.md` that states primary entities, declared mechanism classes, comparator scope, secondary context, and deferred adjacent biology
- if `review_frame.md` exists, only its explicit foundational recall terms or authorized comparator context may appear in first-pass query design

### Full-Text Reviewer / Workflow Controller -> Run Guidance Reviser

Required inputs:

- current pass `inputs/instruction.md`
- current pass `inputs/topic.md`
- optional current pass `inputs/review_frame.md`
- optional current pass `inputs/constraints.md`
- `artifacts/fulltext_review/pmc_mechanism_feedback.csv`
- `artifacts/search_strategy/query_diagnostics.csv`
- review/import artifacts from the completed pass
- `passes/`

Required outputs:

- revised `passes/pass_###/inputs/instruction.md`
- revised `passes/pass_###/inputs/topic.md`
- optional revised `passes/pass_###/inputs/review_frame.md`
- optional revised `passes/pass_###/inputs/constraints.md`
- `artifacts/workflow_control/run_guidance_revision_log.csv`

Promotion rule:

- this handoff is required before every learned rerun triggered by `pdf_deferral_decision = defer_pdfs`
- `original_user_prompt.md` must remain unchanged
- the revision log must name the feedback loop ID and the concrete retained mechanisms, missing terms, noise exclusions, review-frame changes, and reviewer rules added to guidance
- the next learned `search_strategy.md` must be generated from the revised `instruction.md`, revised `topic.md`, optional `review_frame.md`, optional constraints, and PMC feedback

### PubMed Keyword Scout -> PubMed Collector

Required inputs:

- current pass `inputs/instruction.md`
- current pass `inputs/topic.md`
- optional current pass `inputs/review_frame.md`
- optional current pass `inputs/constraints.md`
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

### PubMed Collector -> Abstract Reviewer

Required outputs:

- `artifacts/metadata_collection/paper_manifest.csv`
- one stable paper row per PMID
- title, abstract, PMID, DOI when present, year when present, and source-query provenance

Promotion rule:

- the collected cohort is the abstract-review cohort
- do not create a hidden shortlist between collection and abstract review

### Abstract Reviewer -> Abstract Reviewer 2

Required outputs:

- `artifacts/abstract_review/abstract_review.csv`
- per-paper `review_decision`
- per-paper rationale and confidence

Promotion rule:

- every collected paper must receive an abstract-stage decision before second-pass review begins

### Abstract Reviewer 2 -> Full-Text Importer

Required outputs:

- `artifacts/abstract_review/abstract_review2.csv`
- adjudicated second-pass decision
- per-paper `promotion_decision` resolved to either `advance_to_import` or `stop`
- original title and abstract retained in the second-pass table or equivalent
  reviewer packet so adjudication does not rely only on reviewer prose

Promotion rule:

- only `advance_to_import` papers move to the import stage
- `abstractReviewer2` is an adjudicator, not a stricter cost-control filter
- reviewer 2 must use the title, abstract, first decision, and first rationale together

### Full-Text Importer -> Full-Text Reviewer

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

- only papers with readable normalized full text advance to full-text review
- papers lacking readable full text remain unresolved for access, not scientifically excluded
- after manual PDF ingest, newly normalized full text should be reviewed before the ingest cycle is treated as complete
- before the final calibrated access pass, do not ask for manual PDFs; use PMC-readable papers to generate mechanism and query feedback first
- after PMC mechanism feedback, do not create a PDF download shortlist while the controller is still looping back to query/review
- in the final PMC-satisfied loop, create the PDF download shortlist regardless of whether the eventual downloader is a human or another agent
- the final-loop shortlist is required to explain which queued PDFs should be requested now, deferred, or not requested

### Full-Text Reviewer -> Reporter

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
- before the final calibrated access pass, `pmc_mechanism_feedback.csv` must be reviewed by the Workflow Controller before any PDF intervention is requested

### Workflow Controller -> Earlier Stage Or Reporter

Required inputs:

- `query_diagnostics.csv`
- `abstract_review.csv`
- `abstract_review2.csv`
- `import_status.csv`
- `evidence_extraction.csv`
- `pmc_mechanism_feedback.csv`
- `fulltext_review.csv`

Required outputs:

- `artifacts/workflow_control/workflow_loop_decision.csv`
- `artifacts/workflow_control/workflow_state.json`

Promotion rule:

- if no loop trigger fires, continue to Reporter
- if fewer than `min_big_workflow_loops` big passes have completed, loop to `pubmedKeywordScout` even when PMC feedback says `final_pdf_pass`
- if a query loop fires, send concrete query-revision instructions to `pubmedKeywordScout`
- if a reviewer-calibration loop fires, rerun the affected review stage with revised evidence definitions
- if a human PDF checkpoint fires, pause according to `run_config.md`, but only after PMC-learning loops are complete unless full-text completion was explicitly required from the start
- every loop must record a stop condition before it starts

### Reporter -> User

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
3. `passes/pass_NNN/artifacts/abstract_review/`
4. `passes/pass_NNN/artifacts/fulltext_import/`
5. `passes/pass_NNN/artifacts/fulltext_review/`
6. `passes/pass_NNN/artifacts/workflow_control/`
7. `passes/pass_NNN/reports/`

Scripts must resolve the active pass from `Phase1_PubmedCollection/passes/active_pass.json` and read or write inside that pass directory. The run root must not contain pass-neutral `artifacts/` or `reports/` folders or symlink pointers.

Expected canonical artifacts for each pass:

- `artifacts/search_strategy/search_strategy.md`
- `artifacts/metadata_collection/paper_manifest.csv`
- `artifacts/abstract_review/abstract_review.csv`
- `artifacts/abstract_review/abstract_review2.csv`
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

## Run layout

Each run should have its own folder:

`runs/<run_id>/`

Minimum expected files:

- `original_user_prompt.md`
- `passes/pass_001/inputs/request.md`
- `passes/pass_001/inputs/run_config.md`
- `passes/pass_001/inputs/instruction.md`
- `passes/pass_001/inputs/topic.md`
- optional `passes/pass_001/inputs/review_frame.md`
- `passes/pass_001/inputs/constraints.md` optional

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

Before a learned rerun starts, create or activate the next pass directory and write its revised inputs there. After the Workflow Controller evaluates a pass, write `snapshot_manifest.json` inside that pass directory.

Later passes are not scratch spaces for query correction. Pass `N+1` may be
activated only after pass `N` has completed collection, both abstract reviews,
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

The `abstractReviewer` and `abstractReviewer2` roles are expected to resolve every paper at their stage.

This is a brute-force review rule, not a shortlist rule.

If `pubmedKeywordScout` and `pubmedCollector` produce a cohort of potentially related papers, every paper in that cohort must pass through:

- `abstractReviewer`
- `abstractReviewer2`

Batching is allowed only for context management.
Batching must not be used to silently reduce the review cohort before abstract review.

At abstract stage, each paper must end in one of two actionable states:

- `advance_to_import`
- `stop`

Abstract promotion requires the run's claim shape. Entity-only, mechanism-only,
outcome-only, or context-only matches must stop unless the run contract
explicitly grants a review-frame retention role and the paper is needed as a
minority field-synthesis/background item.

At final output stage, retained papers may end in one of two states:

- `selected_for_reading`
- `abstract_relevant_fulltext_unavailable`

## Agentic loop rule

This workflow is not strictly linear.
After query optimization, abstract review, full-text import, and full-text review, the Workflow Controller must decide whether to continue, pause, or loop.

The workflow has a mandatory minimum of two big passes and a default maximum of five.
A big pass means an end-to-end run through query design or revision, PubMed collection, abstract review, second abstract review, PMC import, full-text review of readable normalized papers, and `pmc_mechanism_feedback.csv`.

PMC feedback must pass the configured full-text review gate before it can unlock a learned rerun. The strict default is `pmc_fulltext_review_gate_mode = all_available`, which requires every paper marked `pmc_access_status = available` in `import_status.csv` to have a normalized full text, a full-text review decision, and a matching evidence-extraction row. A partial PMC sample is allowed only as a progress checkpoint; it must not drive pass activation, run-guidance revision, or learned query reconstruction.

Mandatory pass structure:

- Pass 1: conservative PMC-learning pass. The query scout searches the user-declared entities and mechanism classes, plus only explicitly authorized comparator queries. The full-text reviewer writes `pmc_mechanism_feedback.csv` with `pdf_deferral_decision = defer_pdfs` unless `require_fulltext_completion` is set.
- Pass 2: learned in-scope rerun. The Run Guidance Reviser first applies Pass 1 retained in-scope mechanisms, noise families, missing terms, review-frame calibration, and reviewer-calibration changes to `instruction.md`, `topic.md`, and optional `review_frame.md`; then the query scout generates a learned search strategy from the revised guidance plus PMC feedback while staying inside the query-scope contract; then the workflow reruns collection, both abstract reviews, PMC import, and full-text review. This learned rerun should naturally reduce burden by applying full-text learning to focus the run on the user's prompt, but numeric shrinkage is a confirmation signal rather than a hard definition of success.
- If a learned rerun expands the collection or fails to substantially shorten abstract-review promotion, the controller records a confirmation signal. The run may proceed only if the revision log explains why the larger or similar-sized set is caused by newly learned in-scope vocabulary rather than secondary context, comparator, assay, population, intervention, or outcome terms becoming standalone drivers.
- The workflow philosophy is that pass 1 spends breadth to buy learning, and
  pass 2 spends that learning to buy focus. Pass 2 should therefore be written
  as a more discriminating strategy before it is measured. Count comparisons are
  sanity checks; the primary obligation is that learned terms, exclusions, and
  reviewer rules make weak contextual matches less likely to enter the next
  full-text burden.
- Pass 2 or later may emit `final_pdf_pass` only after evidence shows the query/review criteria have absorbed the PMC learning.
- Once `final_pdf_pass` is accepted after the minimum learned loops, the controller records the effective access phase as `final_access`.
- Passes 3-5 are triggered by persistent evidence-grounded failures such as missing concepts, recurrent query noise, reviewer drift, weak final keeps, or a large low-value PDF queue.
- After Pass 5, the controller must stop blocked or ask for human/parent-agent intervention rather than loop automatically.

Loops are allowed when an artifact shows a specific failure mode:

- query diagnostics show dominant noise classes that can be removed without obvious recall loss
- abstract review advances a very large fraction of the cohort with weak or generic rationales
- learned rerun collection or `advance_to_import` counts do not materially decrease relative to the previous pass and the revision log does not justify this with newly learned in-scope vocabulary
- reviewer 2 frequently overturns reviewer 1 for the same reason
- PMC full-text reading identifies in-scope mechanism terms that should replace vague query terms
- import creates a large PDF queue after PMC learning and the queued papers are traceable to a predictable query-noise pattern
- PMC-learning is marked `final_pdf_pass` and there is a non-empty PDF queue but no PDF download shortlist
- full-text evidence extraction shows many kept papers are indirect, background, expression-only, or marker-only without an authorized review-frame role
- full-text evidence extraction reveals a missing in-scope term family that should become a rescue query
- fewer than `min_big_workflow_loops` big passes have completed

Loops are not allowed for vague discomfort with cohort size.
Every loop decision must name:

- the triggering artifact
- the observed failure mode
- the earlier stage to revisit
- the concrete change to make
- the stop condition for the next pass

Default loop targets:

- query noise or missing concepts: loop to `pubmedKeywordScout`
- inconsistent abstract criteria: loop to `abstractReviewer` or `abstractReviewer2`
- overbroad full-text keeps: loop to `fullTextReviewer` with stricter evidence-tier rules
- large low-value PDF queue before final access: keep PDFs deferred, read PMC evidence, and loop to `pubmedKeywordScout`
- missing PDF download shortlist after final PMC-satisfied learning: build `pdf_download_shortlist.csv` before reporting completion

The controller must also write `workflow_state.json`.
This state file is the portable completion contract for agent harnesses.
It should say `status = complete` only when no loop is active and the final-loop PDF download shortlist exists for any remaining manual PDF queue.
It should record `access_phase = final_access` before any complete state.
It must not say `status = complete` until at least `min_big_workflow_loops` PMC-feedback passes exist.
Before the completion gate accepts that state, it must delete prior-pass PMC XML
and PMC-normalized JSON payloads while preserving structured pass artifacts.

## Batching rule

This workflow should process literature in bounded LLM batches.

Batch size should be chosen for stable judgment quality, not merely to fill the model context window.
Batching applies after collection and never authorizes capped PubMed retrieval.

These batches are execution batches only.
They are not permission to replace full abstract review with a smaller shortlist when the collected cohort is large.

Recommended defaults by model tier:

- frontier model
  - PubMed search inspection: `10-15` records per call
  - abstract review: `10-20` abstracts per call
  - second abstract review: `8-15` abstracts per call
  - full-text review: `2-5` papers per call
- solid mid-tier model
  - PubMed search inspection: `8-12` records per call
  - abstract review: `8-12` abstracts per call
  - second abstract review: `6-10` abstracts per call
  - full-text review: `1-3` papers per call
- smaller or weaker model
  - PubMed search inspection: `5-10` records per call
  - abstract review: `5-8` abstracts per call
  - second abstract review: `4-6` abstracts per call
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
After PMC mechanism feedback exists, build a ranked `pdf_download_shortlist.csv` only when the latest feedback says `final_pdf_pass`.
`final_pdf_pass` is ignored for PDF access until at least two big passes have completed.
This final-loop shortlist is generated regardless of whether the eventual downloader is a human user or another agent.
It should be much smaller than the raw queue because previous PMC-learning loops have already removed predictable noise.

- `human_facing` + `pause_for_user`
  pause and prompt the user with explicit choices only after PMC-learning loops have ended or been deliberately skipped and the final-loop PDF download shortlist exists
- `agent_facing` + `continue_pmc_only`
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
