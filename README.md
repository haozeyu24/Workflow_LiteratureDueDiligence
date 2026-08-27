# agenticWorkflow_LiteratureScreeningAndFullTextReview

This folder defines a portable, artifact-driven paper review workflow.

The workflow is designed to be:

- independent of any single LLM
- independent of any single agent harness
- executable through a mix of code and agent review steps
- auditable through stable intermediate artifacts

The main variable is the user-provided instruction and topic.

## Upstream Prompt Contract

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
- final deliverable expectation: reading list, mechanism map, evidence table, gap analysis, PDF shortlist, or another concrete output

See `templates/upstream_prompt_protocol_template.md` for a reusable parent-agent
prompt shape. If these fields cannot be inferred, the run setup agent should
mark the request as underspecified and ask for clarification or run only a
diagnostic scouting step.

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
- do not hardcode a specific lab, organism set, assay family, or dataset into reusable scripts
- do not assume any example domain unless reading a specific run folder

Reusable files must operate on run inputs such as:

- `original_user_prompt.md`
- `passes/pass_001/inputs/request.md`
- `passes/pass_001/inputs/run_config.md`
- `passes/pass_001/inputs/instruction.md`
- `passes/pass_001/inputs/topic.md`
- optional `passes/pass_001/inputs/constraints.md`
- learned `passes/pass_###/inputs/` guidance for later passes
- pass-scoped `passes/pass_###/artifacts/`
- pass-scoped `passes/pass_###/reports/`

Example-specific content belongs only inside `runs/<run_id>/`.

## Design principle

This is a real workflow, not just a prompt.

- Markdown files define the workflow contract and review policy.
- Code handles repeatable operations such as search retrieval, metadata collection, import, parsing, normalization, and report generation.
- Agents perform the judgment-heavy review steps while writing back to structured artifacts.

## Completion gate

Do not treat useful intermediate artifacts as workflow completion.

For every run, the root-level `WORKFLOW_NOT_COMPLETE` sentinel means the run is
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

## Artifact boundary

Default runs use `artifact_policy = workflow_only`.

Agents may write only declared workflow artifacts under the active
`runs/<run_id>/passes/pass_###/` tree. Extra rankings, summaries, dashboards,
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
- during `access_phase = pmc_learning`, manual PDF ingest is deferred; normalized open full text should be read first for mechanism and query-feedback signals
- when the latest feedback marks `final_pdf_pass` after the minimum learned loops, the controller records effective `access_phase = final_access`
- during `access_phase = final_access`, manual PDF ingest should continue directly into full-text keep/drop review for any newly readable papers before the ingest cycle is considered complete
