# Workflow

## Objective

Given an instruction and topic:

1. generate and refine a PubMed search strategy
2. collect title, abstract, and metadata
3. review abstract-level relevance
4. run a second abstract review over the same paper plus the first review opinion
5. acquire full text through PMC first, then PDF fallback
6. parse and normalize full text
7. review normalized full text
8. produce a final reading list with metadata and file pointers

## Fixed workflow vs run-specific inputs

This document describes the fixed workflow.

The following are reusable across runs:

- role definitions
- stage order
- review schemas
- artifact types
- import and normalization logic

The following are run-specific:

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

Owns the run state, artifact naming, stage order, and handoff validation.

### 2. Run Setup Agent

Transforms a user request into run-specific workflow inputs.

Input:

- free-form user request

Output:

- `run_config.md`
- `instruction.md`
- `topic.md`
- optional run constraints

The `runSetupAgent` role is required because the workflow is reusable but the scientific question changes from run to run.

The `runSetupAgent` must convert a user request into generic workflow inputs without changing the workflow definition itself.

### 3. PubMed Keyword Scout

Builds the PubMed search strategy from the instruction and topic, then refines it after inspecting retrieval noise or coverage gaps when needed.

Output:

- search plan
- PubMed query strings
- search rationale
- query refinement report when revised

Working rule:

- refine based on sampled precision and coverage, not hit count alone
- retrieve broadly enough to capture anything potentially related to the run objective
- do not narrow the collected cohort into a smaller pre-review working set
- if a paper is potentially related at the scouting stage, it belongs in the collected cohort for abstract review
- default behavior is recall-first collection, not artificial retrieval caps
- use batching for model context management, not for shrinking the search or abstract-review cohort

### 4. PubMed Collector

Executes the search and downloads title, abstract, and metadata.

Output:

- paper manifest
- source metadata records

### 5. Abstract Reviewer

Reads title and abstract to judge topic relevance.

Output:

- abstract review table

### 6. Abstract Reviewer 2

Reads the original abstract again together with the first abstract reviewer's decision and rationale, then makes a second-pass decision.

Output:

- second-pass abstract review table

### 7. Full-Text Importer

Acquires full text, preferring PMC and using PDF fallback when necessary.

Output:

- PMC acquisition report
- manual PDF queue
- PDF import report
- PDF intervention status when user or parent-agent policy requires a decision

Completion rule:

- manual PDF ingest is not considered complete just because files were staged or parsed
- any newly readable normalized full text must be handed immediately to full-text review in the same agent-driven pass when possible
- the only acceptable post-ingest unresolved state is access-related, not "normalized but not yet judged"

### 8. Full-Text Reviewer

Reads normalized full text and makes the final keep/drop judgment.

Output:

- full-text review table
- final included set

Constraint:

- only papers with readable normalized full text are eligible for full-text review
- papers advanced from abstract review but lacking readable full text remain unresolved for access, not scientifically excluded
- when new readable full text appears after PMC import or manual PDF ingest, the workflow should continue directly into keep/drop review before reporting the ingest cycle as complete

### 9. Reporter

Produces user-facing summaries and status counts.

Output:

- progress report
- final reading list

## Stage handoffs

### User -> Run Setup Agent

Required input:

- free-form user request

Required outputs:

- `runs/<run_id>/run_config.md`
- `runs/<run_id>/instruction.md`
- `runs/<run_id>/topic.md`
- optional `runs/<run_id>/constraints.md`

Promotion rule:

- downstream stages must consume these run files as inputs rather than rewriting reusable workflow files

### Run Setup Agent -> PubMed Keyword Scout

Required inputs:

- `run_config.md`
- `instruction.md`
- `topic.md`
- optional `constraints.md`

Required outputs:

- a scoped search objective and query-design context captured in `search_strategy.md`

### PubMed Keyword Scout -> PubMed Collector

Required inputs:

- run-specific `instruction.md`
- run-specific `topic.md`
- optional `constraints.md`
- optional retrieval feedback from a previous pass

Required outputs:

- one or more PubMed query strings
- rationale for each query
- search-strategy record at `artifacts/search_strategy/search_strategy.md`
- `query_refinement_report.md` when the strategy changes after retrieval inspection

Promotion rule:

- query refinement must respond to observed precision or recall problems, not an arbitrary desire for a smaller cohort

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

### Full-Text Importer -> Full-Text Reviewer

Required outputs:

- `artifacts/fulltext_import/import_status.csv`
- full-text availability state
- PMC usability state
- PDF fallback state
- normalized file path when parsing succeeds

Additional required outputs when applicable:

- `artifacts/fulltext_import/manual_pdf_queue.csv` when manual PDF fallback is needed
- `artifacts/fulltext_import/pdf_parse_report.csv` when any staged PDF is parsed or attempted
- `artifacts/fulltext_import/manual_pdf_import_report.csv` when any user-provided PDF is staged
- `artifacts/fulltext_import/pdf_intervention_status.json` and `reports/intervention_prompt.md` when run policy requires a visible checkpoint

Promotion rule:

- only papers with readable normalized full text advance to full-text review
- papers lacking readable full text remain unresolved for access, not scientifically excluded
- after manual PDF ingest, newly normalized full text should be reviewed before the ingest cycle is treated as complete

### Full-Text Reviewer -> Reporter

Required outputs:

- `artifacts/fulltext_review/fulltext_review.csv`
- per-paper final `keep` or `drop` decision
- rationale
- confidence
- normalized file path

Promotion rule:

- papers without readable full text are not converted into reviewer drops

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

1. `artifacts/search_strategy/`
2. `artifacts/metadata_collection/`
3. `artifacts/abstract_review/`
4. `artifacts/fulltext_import/`
5. `artifacts/fulltext_review/`
6. `reports/`

Expected canonical artifacts for a run:

- `artifacts/search_strategy/search_strategy.md`
- `artifacts/metadata_collection/paper_manifest.csv`
- `artifacts/abstract_review/abstract_review.csv`
- `artifacts/abstract_review/abstract_review2.csv`
- `artifacts/fulltext_import/import_status.csv`
- `artifacts/fulltext_import/manual_pdf_queue.csv`
- `artifacts/fulltext_import/pdf_parse_report.csv`
- `artifacts/fulltext_review/fulltext_review.csv`
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

- `request.md`
- `run_config.md`
- `instruction.md`
- `topic.md`
- `constraints.md` optional

The rest of the workflow artifacts may either live inside the run folder or point to shared artifact folders, but the run inputs must always be captured explicitly.

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

## Batching rule

This workflow should process literature in bounded LLM batches.

Batch size should be chosen for stable judgment quality, not merely to fill the model context window.

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

Working sets may span `100-300` papers, but they should be split across multiple calls rather than pushed into one oversized context window.

Shrink the batch if the model:

- confuses one paper with another
- gives shallow or repetitive rationales
- misses obvious details present in the supplied text
- starts making batch-level rather than paper-level judgments

## PDF intervention rule

When the PDF queue is non-empty, behavior should follow `run_config.md`.

- `human_facing` + `pause_for_user`
  pause and prompt the user with explicit choices
- `agent_facing` + `continue_pmc_only`
  continue with PMC-normalized papers and preserve the PDF queue as deferred work
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
