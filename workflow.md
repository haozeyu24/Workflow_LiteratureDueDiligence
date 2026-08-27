# Workflow

## Objective

Given an instruction and topic:

1. generate a PubMed search strategy
2. optimize the query set with hit counts, sampled precision, noise classes, and missing-concept diagnostics
3. collect title, abstract, and metadata for the accepted query set
4. review abstract-level relevance
5. run a second abstract review over the same paper plus the first review opinion
6. acquire and normalize PMC full text first
7. use PMC full text to summarize mechanisms, noise, and query-feedback signals
8. revise run guidance from PMC full-text learning, then reconstruct the query and rerun collection, abstract review, PMC import, and full-text review at least once using PMC-derived learning
9. decide whether additional learned loops are needed before spending effort on PDFs
10. reserve manual PDF intervention for the final calibrated access pass unless the run explicitly requires full-text completion from the beginning
11. extract final full-text evidence and review normalized full text
12. produce a final reading list with metadata and file pointers

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
- optional seed entities, pathogens, pathways, labs, or exclusions

Each run should live in its own folder under `runs/`.

## Generic workflow rule

All reusable workflow logic must be parameterized by run inputs.

That means:

- role behavior is generic
- artifact schemas are generic
- scripts are generic
- run folders carry topic-specific content

If a reusable component mentions a specific lab, virus list, assay, or biological question, it should be treated as a design mistake unless that component is clearly inside a run-specific folder.

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

## Roles

### 1. Project Manager

Owns the run state, artifact naming, stage order, loop decisions, and handoff validation.

### 2. Run Setup Agent

Transforms a user request into run-specific workflow inputs.

Input:

- free-form user request

Output:

- `run_config.md`
- `instruction.md`
- `topic.md`
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

### 3. PubMed Keyword Scout

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
- add synonyms, assays, and rescue terms only within declared mechanism classes
- do not expand into adjacent biology merely because it is plausibly related or compensatory
- refine based on sampled precision and coverage, not hit count alone
- retrieve broadly enough to capture anything potentially related to the run objective
- do not narrow the collected cohort into a smaller pre-review working set
- if a paper is potentially related at the scouting stage, it belongs in the collected cohort for abstract review
- PubMed collection is recall-first and must have no record cap
- agents and harnesses must not introduce per-query, total, date-sorted, top-N, or equivalent PubMed collection caps
- use query optimization, not hidden retrieval caps, to produce a reasonably accurate candidate cohort
- use batching for model context management, not for shrinking the search or abstract-review cohort

### 4. Run Guidance Reviser

Revises `instruction.md`, `topic.md`, optional `constraints.md`, and reviewer-facing rules after PMC full-text learning and before a learned PubMed rerun.

Input:

- current `instruction.md`
- current `topic.md`
- optional `constraints.md`
- `pmc_mechanism_feedback.csv`
- `query_diagnostics.csv`
- review/import outcomes
- pass snapshots

Output:

- revised `instruction.md`
- revised `topic.md`
- optional revised `constraints.md`
- `artifacts/workflow_control/run_guidance_revision_log.csv`

Working rule:

- `original_user_prompt.md` is immutable
- `passes/pass_001/inputs/instruction.md` and `passes/pass_001/inputs/topic.md` are immutable base/pass-1 guidance after run setup
- learned guidance for later passes must be written under `passes/pass_###/inputs/`
- every guidance revision must cite the PMC feedback loop that triggered it
- learned `search_strategy.md` must be generated after this revision from the revised guidance plus PMC feedback
- PMC-derived changes may add in-scope synonyms, assays, entities, exclusions, or reviewer rules by default
- PMC-derived adjacent mechanism classes must remain secondary context unless the revision explicitly updates the query-scope contract and explains why the original user request authorizes the broader primary scope

### 5. PubMed Collector

Executes the search and downloads title, abstract, and metadata.

Output:

- paper manifest
- source metadata records

### 6. Abstract Reviewer

Reads title and abstract to judge topic relevance.

Output:

- abstract review table

### 7. Abstract Reviewer 2

Reads the original abstract again together with the first abstract reviewer's decision and rationale, then makes a second-pass decision.

Output:

- second-pass abstract review table

### 8. Full-Text Importer

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

### 9. Full-Text Reviewer

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

### 11. Reporter

Produces user-facing summaries and status counts.

Output:

- progress report
- final reading list

## Stage handoffs

### User -> Run Setup Agent

Required input:

- free-form user prompt

Required outputs:

- `runs/<run_id>/original_user_prompt.md`
- `runs/<run_id>/passes/pass_001/inputs/run_config.md`
- `runs/<run_id>/passes/pass_001/inputs/instruction.md`
- `runs/<run_id>/passes/pass_001/inputs/topic.md`
- optional `runs/<run_id>/passes/pass_001/inputs/constraints.md`

Promotion rule:

- `original_user_prompt.md` must preserve the exact starting prompt without rewriting
- downstream stages must consume run files as inputs rather than rewriting reusable workflow files

### Run Setup Agent -> PubMed Keyword Scout

Required inputs:

- current pass `inputs/run_config.md`
- current pass `inputs/instruction.md`
- current pass `inputs/topic.md`
- optional current pass `inputs/constraints.md`

Required outputs:

- a scoped search objective and query-design context captured in `search_strategy.md`
- a query-scope contract or equivalent section in `search_strategy.md` that states primary entities, declared mechanism classes, comparator scope, secondary context, and deferred adjacent biology

### Full-Text Reviewer / Workflow Controller -> Run Guidance Reviser

Required inputs:

- current pass `inputs/instruction.md`
- current pass `inputs/topic.md`
- optional current pass `inputs/constraints.md`
- `artifacts/fulltext_review/pmc_mechanism_feedback.csv`
- `artifacts/search_strategy/query_diagnostics.csv`
- review/import artifacts from the completed pass
- `passes/`

Required outputs:

- revised `passes/pass_###/inputs/instruction.md`
- revised `passes/pass_###/inputs/topic.md`
- optional revised `passes/pass_###/inputs/constraints.md`
- `artifacts/workflow_control/run_guidance_revision_log.csv`

Promotion rule:

- this handoff is required before every learned rerun triggered by `pdf_deferral_decision = defer_pdfs`
- `original_user_prompt.md` must remain unchanged
- the revision log must name the feedback loop ID and the concrete retained mechanisms, missing terms, noise exclusions, and reviewer rules added to guidance
- the next learned `search_strategy.md` must be generated from the revised `instruction.md`, revised `topic.md`, optional constraints, and PMC feedback

### PubMed Keyword Scout -> PubMed Collector

Required inputs:

- current pass `inputs/instruction.md`
- current pass `inputs/topic.md`
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
- final `keep` should be supported by a non-background evidence tier
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

Scripts must resolve the active pass from `passes/active_pass.json` and read or write inside that pass directory. The run root must not contain pass-neutral `artifacts/` or `reports/` folders or symlink pointers.

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
- `passes/pass_001/inputs/constraints.md` optional

Pass 1 must also contain:

- `passes/pass_001/artifacts/`
- `passes/pass_001/reports/`

Later passes must have the same three-part structure:

- `passes/pass_###/inputs/`
- `passes/pass_###/artifacts/`
- `passes/pass_###/reports/`

Each run must preserve durable pass snapshots under:

`runs/<run_id>/passes/pass_###/`

Each pass directory should contain:

- `inputs/`
  Pass-specific guidance and run inputs.
- `artifacts/`
  Machine-readable artifacts for that pass.
- `reports/`
  User-facing reports for that pass.
- `snapshot_manifest.json`
  Pass counts, snapshot reason, latest PMC feedback state, and key stage row counts.

The run root must stay clean: pass outputs belong only under `passes/pass_###/artifacts/` and `passes/pass_###/reports/`.

Before a learned rerun starts, create or activate the next pass directory and write its revised inputs there. After the Workflow Controller evaluates a pass, write `snapshot_manifest.json` inside that pass directory.

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

At final output stage, retained papers may end in one of two states:

- `selected_for_reading`
- `abstract_relevant_fulltext_unavailable`

## Agentic loop rule

This workflow is not strictly linear.
After query optimization, abstract review, full-text import, and full-text review, the Project Manager or Workflow Controller must decide whether to continue, pause, or loop.

The workflow has a mandatory minimum of two big passes and a default maximum of five.
A big pass means an end-to-end run through query design or revision, PubMed collection, abstract review, second abstract review, PMC import, full-text review of readable normalized papers, and `pmc_mechanism_feedback.csv`.

Mandatory pass structure:

- Pass 1: conservative PMC-learning pass. The query scout searches the user-declared entities and mechanism classes, plus only explicitly authorized comparator queries. The full-text reviewer writes `pmc_mechanism_feedback.csv` with `pdf_deferral_decision = defer_pdfs` unless `require_fulltext_completion` is set.
- Pass 2: learned in-scope rerun. The Run Guidance Reviser first applies Pass 1 retained in-scope mechanisms, noise families, missing terms, and reviewer-calibration changes to `instruction.md` and `topic.md`; then the query scout generates a learned search strategy from the revised guidance plus PMC feedback while staying inside the query-scope contract; then the workflow reruns collection, both abstract reviews, PMC import, and full-text review.
- Pass 2 or later may emit `final_pdf_pass` only after evidence shows the query/review criteria have absorbed the PMC learning.
- Passes 3-5 are triggered by persistent evidence-grounded failures such as missing concepts, recurrent query noise, reviewer drift, weak final keeps, or a large low-value PDF queue.
- After Pass 5, the controller must stop blocked or ask for human/parent-agent intervention rather than loop automatically.

Loops are allowed when an artifact shows a specific failure mode:

- query diagnostics show dominant noise classes that can be removed without obvious recall loss
- abstract review advances a very large fraction of the cohort with weak or generic rationales
- reviewer 2 frequently overturns reviewer 1 for the same reason
- PMC full-text reading identifies in-scope mechanism terms that should replace vague query terms
- import creates a large PDF queue after PMC learning and the queued papers are traceable to a predictable query-noise pattern
- PMC-learning is marked `final_pdf_pass` and there is a non-empty PDF queue but no PDF download shortlist
- full-text evidence extraction shows many kept papers are indirect, background, expression-only, or marker-only
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
It must not say `status = complete` until at least `min_big_workflow_loops` PMC-feedback passes exist.

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
