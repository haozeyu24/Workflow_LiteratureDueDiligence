# agenticWorkflow_LiteratureScreeningAndFullTextReview

This folder defines a portable, artifact-driven paper review workflow.

The workflow is designed to be:

- independent of any single LLM
- independent of any single agent harness
- executable through a mix of code and agent review steps
- auditable through stable intermediate artifacts

The main variable is the user-provided instruction and topic.

## Reuse boundary

This specification must be read with one hard rule:

- the workflow is reusable
- the run inputs are replaceable

In other words:

- roles, schemas, handoffs, artifact types, and pipeline stages are part of the fixed workflow
- `instruction`, `topic`, and any seed constraints belong to a specific run

The workflow must not be rewritten for each scientific question.
Only the run inputs should change.

## Generic implementation rule

When creating instructions, prompts, or scripts for this workflow:

- do not hardcode a specific biological topic into the reusable workflow files
- do not hardcode a specific lab, pathogen set, or dataset into reusable scripts
- do not assume Krogan, AP-MS, or any other example unless reading a specific run folder

Reusable files must operate on run inputs such as:

- `request.md`
- `run_config.md`
- `instruction.md`
- `topic.md`
- optional `constraints.md`

Example-specific content belongs only inside `runs/<run_id>/`.

## Design principle

This is a real workflow, not just a prompt.

- Markdown files define the workflow contract and review policy.
- Code handles repeatable operations such as search retrieval, metadata collection, import, parsing, normalization, and report generation.
- Agents perform the judgment-heavy review steps while writing back to structured artifacts.

## Context management

This workflow should operate on bounded batches, not full cohorts at once.

Recommended defaults:

- frontier model
  - PubMed search inspection: sample `20-75` records total, usually in chunks of `10-15`
  - abstract review: `10-20` abstracts per LLM call
  - second abstract review: `8-15` abstracts per LLM call
  - full-text review: usually `2-5` papers per LLM call
- solid mid-tier model
  - PubMed search inspection: usually in chunks of `8-12`
  - abstract review: `8-12` abstracts per LLM call
  - second abstract review: `6-10` abstracts per LLM call
  - full-text review: usually `1-3` papers per LLM call
- smaller or weaker model
  - PubMed search inspection: usually in chunks of `5-10`
  - abstract review: `5-8` abstracts per LLM call
  - second abstract review: `4-6` abstracts per LLM call
  - full-text review: usually `1-2` papers per LLM call

The cohort-level working set may be much larger, but the per-call context should stay small enough to preserve judgment quality and reduce cross-paper confusion.
Treat these as safe defaults, not maximums. Bigger context windows do not automatically justify bigger batches.

Important interpretation:

- broad retrieval and exhaustive abstract review are different from per-call context size
- if the scout and collector produce `1,000+` potentially related papers, those papers should still all go through `abstractReviewer` and `abstractReviewer2`
- batching exists only so the model reads the cohort in manageable pieces
- low retrieval caps should not be introduced just to keep the cohort small; recall comes first unless the user explicitly wants a limit

## Prompt engineering rule

Reviewer-style prompts should be explicit, schema-bound, and batch-stable.

They should:

- restate the run-specific objective
- define the decision labels and their meaning
- instruct the model to rely only on the provided title and abstract or full text
- request short evidence-grounded rationales
- forbid unsupported mechanistic speculation
- tell the model to process one paper at a time even when the batch contains many papers

They should not:

- ask for free-form essays
- ask the model to compare too many papers globally in one pass
- allow hidden criteria that are not captured in the output schema

## Layout

- `workflow.md`
  End-to-end stage definition, stage handoffs, and promotion rules.
- `policy.md`
  Global review principles, decision rules, and conflict-resolution rules.
- `schemas/`
  Machine-readable review and artifact schemas in Markdown form.
- `templates/`
  Starter CSV and Markdown templates.
  Includes reusable prompt templates for reviewer-style roles.
- `runs/`
  Per-run inputs and outputs. Each run gets its own folder with its own instruction, topic, artifacts, and reports.
- `scripts/`
  Workflow-specific code wrappers and utilities.

## Relationship to the atlas repo

This workflow is standalone, but it is expected to reuse full-text import, PMC handling, and GROBID normalization logic from:

- `niaid-systems-biology-consortium-atlas/`

That repo is treated as the current implementation substrate, not the workflow definition itself.

## PDF parser runtime

PDF parsing is modeled as a reusable workflow step, but the parser runtime is environment-supplied.

Current wrapper behavior:

- `scripts/parse_pdf_fulltext.py` accepts `GROBID_URL` or `GROBID_BASE_URL`, normalizes common misconfigurations such as values ending in `/api` or `/api/processFulltextDocument`, and otherwise probes common local endpoints such as `http://localhost:8070`
- successful TEI output is normalized to the same JSON contract used for full-text review
- if no reachable parser endpoint is available, staged PDFs remain explicitly `parser_pending`
- PMC-normalized papers can still continue into full-text review
- manual PDF ingest should continue directly into full-text keep/drop review for any newly readable papers before the ingest cycle is considered complete
