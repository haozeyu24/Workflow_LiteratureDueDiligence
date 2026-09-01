# Upstream Prompt Protocol Template

Use this template when a human or parent agent wants to call the literature
screening and full-text review workflow as one component inside a larger
workflow.

The parent agent should fill the fields as specifically as possible. Unknown
fields may be marked `unspecified`, but the parent agent should not invent
scientific scope merely to make the prompt look complete.

## Scientific Objective

State the question the literature workflow should answer.

- objective:
- why this review is needed:
- expected downstream use:

## Primary Entities

List the entities that may anchor PubMed queries.

- genes/proteins/pathways:
- drugs/perturbations/interventions:
- diseases/phenotypes/biological systems:
- model systems or assay systems:

## Evidence Goal

Define what kinds of evidence count as useful.

- primary evidence types:
- secondary evidence types:
- evidence that should not be treated as sufficient:
- evidence gates for full-text keep:

## Scope Boundaries

Make query boundaries explicit.

- required context:
- authorized comparator entities or systems:
- secondary context for synthesis only:
- adjacent biology deferred from retrieval:
- explicit exclusions:

## Retrieval Guidance

Describe search preferences without adding retrieval caps.

- required aliases or synonyms:
- known seed papers or canonical examples:
- important older/foundational literature to preserve:
- known noisy terms or contexts:
- adjacent concepts that should not become query drivers:
- PubMed collection cap: forbidden; collect the full accepted query result set

## Access And Deliverable Expectations

Define how downstream agents should treat access gaps and outputs.

- PDF policy preference:
- final deliverable:
- acceptable unresolved access state:
- special reporting requirements:

## Review Frame

Describe how the final review should be situated in the larger field without
automatically broadening first-pass retrieval.

- parent field:
- introduction background scope:
- bigger-field progress to summarize:
- foundational concepts or older terminology to preserve:
- review-architecture paper types worth retaining:
- perspective questions:
- controversies or unresolved gaps:
- translational or practical outlook:

## Prompt Scope Self-Check

Choose one:

- `clear`
- `broad_but_workable`
- `exploratory`
- `too_vague`

Rationale:

- missing clarifications:
- safe next action:
