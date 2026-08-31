# Agentic Workflow for Biomedical Literature Due Diligence

This folder defines a portable, artifact-driven literature workflow with a
proposed two-part structure.

Part 1 is the current literature due-diligence pipeline:

- literature search
- abstract review
- PMC-first full-text review
- final PMCID suggestion list
- PDF download shortlist

Part 2 is intentionally not implemented yet.
It will begin only after the user gives a clear go-ahead to write the review
paper, either from PMC-only full text or after user-provided PDFs are parsed and
retained into the writing corpus.

The workflow is designed to be:

- independent of any single LLM
- independent of any single agent harness
- executable through a mix of code and agent review steps
- auditable through stable intermediate artifacts

The main variable is the run-specific input set.

## Recommeded User/Agent Input Format

This workflow can be used as a component inside a larger agentic system.
The upstream user or parent agent should provide a scoped scientific prompt,
not just a topic label.

Recommended upstream handoff:

- scientific objective: the question the literature workflow should answer
- primary entities: genes, proteins, drugs, pathways, diseases, methods, or systems
- evidence goal: mechanism, biomarker, response, perturbation, interaction, dependency, comparison, or another explicit evidence type
- context: disease area, organism, model system, assay type, clinical setting, or population when relevant
- allowed comparator scope: related entities or systems that may be queried directly
- secondary context: useful background that may inform synthesis but should not drive PubMed queries
- exclusions: paper types, contexts, or adjacent biology that should be deprioritized
- final deliverable expectation: reading list, mechanism map, evidence table,
  gap analysis, PDF shortlist, review-paper draft, or another concrete output
- optional review frame: parent field, introduction background, bigger-field
  progress, foundational terms, and perspective obligations that should shape
  retention more than first-pass retrieval
- review-paper positioning needs should be captured in run guidance and
  structured retention rationales so Phase 2 can cite prior reviews and explain
  what new coverage the current review adds without creating undeclared side
  artifacts

See `templates/upstream_prompt_protocol_template.md` for a reusable parent-agent
prompt shape. If these fields cannot be inferred, the run setup agent should
mark the request as underspecified and ask for clarification or run only a
diagnostic scouting step.

## Venue blocklist

This workflow applies a reusable venue blacklist during PubMed collection,
before papers enter `paper_manifest.csv` or any abstract-review stage.

The canonical list lives at `resources/journal_blocklist.csv`.

Blocked papers are written to the active-pass audit artifact
`artifacts/metadata_collection/blocked_venue_records.csv`.

The current blocklist reflects a deliberately aggressive high-trust preference
and includes:

- `Frontiers in*` journals
- `Oncotarget`
- `OncoTargets and Therapy`
- `American Journal of Cancer Research`
- `Oncology Letters`
- `Translational Cancer Research`
- `Discover Oncology`
- `Journal of Cancer`
- `Cureus`
- `Cells`
- `Cancers`
- `Biomedicines`
- `Diagnostics*`
- `Journal of Clinical Medicine`
- `Pathogens*`
- `Microorganisms`
- `Pharmaceuticals`
- `Biology`
- `Heliyon`
- `Diseases`

## Reuse boundary

This specification must be read with one hard rule:

- the workflow is reusable
- the run inputs are replaceable

In other words:

- roles, schemas, handoffs, artifact types, and pipeline stages are part of the fixed workflow
- `instruction`, `topic`, optional `review_frame`, and any seed constraints belong to a specific run

The workflow must not be rewritten for each scientific question.
Only the run inputs should change.

## Generic implementation rule

When creating instructions, prompts, or scripts for this workflow:

- do not hardcode a specific biological topic into the reusable workflow files
- do not hardcode a specific lab, organism set, assay family, or dataset into reusable scripts
- do not assume any example domain unless reading a specific run folder

Reusable files must operate on run inputs such as:

- `original_user_prompt.md`
- `passes/pass_001/inputs/request.md`
- `passes/pass_001/inputs/run_config.md`
- `passes/pass_001/inputs/instruction.md`
- `passes/pass_001/inputs/topic.md`
- optional `passes/pass_001/inputs/review_frame.md`
- optional `passes/pass_001/inputs/constraints.md`
- learned `passes/pass_###/inputs/` guidance for later passes
- pass-scoped `passes/pass_###/artifacts/`
- pass-scoped `passes/pass_###/reports/`
- cross-pass `passes/phase1_transcript.md`

Under the current layout, these live under
`runs/<run_id>/Phase1_PubmedCollection/`.

Example-specific content belongs only inside `runs/<run_id>/`.

## Design principle

This is a real workflow, not just a prompt.

- Markdown files define the workflow contract and review policy.
- Code handles repeatable operations such as search retrieval, metadata
  collection, import, parsing, normalization, and report generation.
- Agents perform the judgment-heavy review steps while writing back to structured artifacts.

## Due-Diligence Philosophy

This workflow is built for decision-grade scientific due diligence, not maximal
bibliography collection.

The default priority order is:

1. prompt fidelity
2. scoped recall
3. evidence-gated narrowing
4. auditable synthesis readiness

Prompt fidelity is the anchor. The user's question defines the primary
entities, mechanism or evidence classes, context, comparators, and exclusions.
Reusable roles must not silently broaden into adjacent biology just because it
is plausible, fashionable, or mechanistically nearby.

Recall friendliness belongs mainly in PubMed retrieval and early abstract
triage, and only inside the declared scope. The workflow should capture
synonyms, older terminology, assay names, aliases, and known direct papers for
the user's objective, but it should not query every adjacent pathway, phenotype,
or background domain unless the run explicitly authorizes that expansion.

Triage should reduce ambiguity early. Abstract review asks whether a paper
plausibly answers the decision question, not whether it could ever be related.
Borderline papers should survive only when they match the primary entity plus a
declared evidence/mechanism class, authorized comparator logic, or an explicit
review-frame retention need.

Full-text review is stricter than abstract review. Final keep decisions should
usually require direct, indirect, or authorized comparator evidence. Background
papers are retained only when `review_frame.md` explicitly justifies a limited
foundational, field-synthesis, or perspective role.

The Phase-2 synthesis corpus may be larger than a human must-read list, but
every paper used by Phase 2 must have typed evidence, a retention role, and
traceable rationale. The workflow should reduce human reading burden by making
evidence strength and uncertainty explicit, not by hiding retrieval shortcuts.

## Current boundary

Today, only Part 1 is fully specified and partly automated.

The intended handoff into Part 2 is:

1. finish Part 1 and produce the final reading list plus PDF shortlist
2. ask the user whether to write from PMC-only full text now, or wait for
   downloaded PDFs
3. if the user wants PDFs included, wait for the user to provide them
4. after the user gives a clear "ready to write" signal, parse and normalize
   those PDFs, rerun retention on the newly readable papers, and report how many
   PDFs were retained into the writing corpus
5. only then begin Part 2 review writing

Until that explicit user checkpoint is added to the runtime behavior, this file
should be treated as the proposed structure rather than a finished end-to-end
implementation of Part 2.

## Completion gate

Do not treat useful intermediate artifacts as workflow completion.

For every run, the Phase-1 sentinel
`runs/<run_id>/Phase1_PubmedCollection/WORKFLOW_NOT_COMPLETE` means the run is
still incomplete. Agents and harnesses may report completed stages, but they must
not call the workflow `done`, `complete`, `final`, or `finished` while this file
exists.

The required final check is:

```bash
python3 scripts/completion_gate.py <run_id>
```

This gate reruns the controller, regenerates reports, validates the run, checks
that `workflow_state.json` has `status = complete`, and verifies that the
incomplete sentinel has been removed.

Before accepting a complete state, the gate deletes bulky PMC XML and
PMC-normalized JSON payloads from earlier passes. The active final pass keeps its
current full-text payloads; prior passes retain their CSV decisions, feedback,
reports, and metadata provenance.

For read-only review contexts, use:

```bash
python3 scripts/completion_gate.py --check-only <run_id>
```

Check-only mode validates the current state without rerunning the controller or
updating sentinel/report files.

If the gate fails, final responses must say the workflow is incomplete and list
the next required stage or controller action.

## Phase 1 transcript

Each run should maintain a user-visible transcript at
`runs/<run_id>/Phase1_PubmedCollection/passes/phase1_transcript.md`.

This file should preserve the words shown on screen during Part 1 across all
passes, including both user and agent messages. It is an audit and
troubleshooting aid, not a replacement for structured workflow artifacts.

## Artifact boundary

Default runs use `artifact_policy = workflow_only`.

Agents may write only declared workflow artifacts under the active
`runs/<run_id>/Phase1_PubmedCollection/passes/pass_###/` tree. Extra rankings, summaries, dashboards,
helper scripts, spreadsheets, or exports are forbidden unless the active
workflow stage declares them or the user explicitly requests them in the current
turn. `validate_run.py` enforces this boundary for active-pass files.

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
- PubMed collection caps are forbidden; recall comes first, and large cohorts must be handled by query refinement plus review batching

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
  End-to-end stage definition, stage handoffs, and promotion rules, including
  the proposed Part-1 to Part-2 user checkpoint.
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

## PDF parser runtime

PDF parsing is modeled as a reusable workflow step, but the parser runtime is environment-supplied.

Current wrapper behavior:

- `scripts/parse_pdf_fulltext.py` accepts `GROBID_URL` or `GROBID_BASE_URL`, normalizes common misconfigurations such as values ending in `/api` or `/api/processFulltextDocument`, and otherwise probes common local endpoints such as `http://localhost:8070`
- successful TEI output is normalized to the same JSON contract used for full-text review
- if no reachable parser endpoint is available, staged PDFs remain explicitly `parser_pending`
- PMC-normalized papers can still continue into full-text review
- during `access_phase = pmc_learning`, manual PDF ingest is deferred; normalized open full text should be read first for mechanism and query-feedback signals
- during `access_phase = pmc_learning`, alternate open-access PDF discovery is
  deferred by default; the early loop should prioritize fast NCBI PMCID/PMC XML
  learning rather than exhaustive access discovery
- when the latest feedback marks `final_pdf_pass` after the minimum learned loops, the controller records effective `access_phase = final_access`
- during `access_phase = final_access`, manual PDF ingest should continue directly into full-text keep/drop review for any newly readable papers before the ingest cycle is considered complete
