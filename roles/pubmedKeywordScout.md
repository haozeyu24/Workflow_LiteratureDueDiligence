# PubMed Keyword Scout

## Purpose

Design and refine a PubMed search strategy from the run instruction and topic.

## Responsibilities

- identify key biological concepts
- propose PubMed query strings
- start from the run-specific scientific objective rather than from arbitrary keywords
- inspect retrieval noise or coverage gaps after an initial search pass
- read sampled titles and abstracts to judge query quality
- refine PubMed keywords and query structure when retrieval quality is poor
- justify recall vs precision tradeoffs
- record assumptions and likely gaps
- follow the search-refinement and batching policy in `policy.md`

## Inputs

- `instruction.md`
- `topic.md`
- optional `constraints.md`
- optional retrieval feedback from a prior collection pass
- optional PMC mechanism feedback from `artifacts/fulltext_review/pmc_mechanism_feedback.csv`
- for learned reruns, a matching `artifacts/workflow_control/run_guidance_revision_log.csv` row showing that the latest `defer_pdfs` PMC feedback was incorporated into `instruction.md` and `topic.md`

## Outputs

- `search_strategy.md`
- `query_diagnostics.csv`
- `query_refinement_report.md` when the strategy is revised
- optional machine-readable query file

## Query construction logic

Start from:

- the scientific objective in `instruction.md`
- the scope and entities in `topic.md`
- any explicit scope exclusions in `constraints.md`
- in learned reruns, the latest PMC-derived mechanisms, missing terms, noise classes, and reviewer-rule changes recorded in `run_guidance_revision_log.csv`

Do not start from a memorized topic template alone.
The query set must be derived from the current run inputs.

Recommended first-pass construction:

- identify the domain entities named in the run
- identify the explicit mechanism classes requested by the user
- identify the desired evidence type or assay language if the run specifies one
- identify likely synonym families only inside the requested mechanism classes
- convert those pieces into a small set of complementary PubMed queries
- identify whether the topic is likely to depend on older foundational mechanism papers and plan a recall safeguard for them

## Query Scope Contract

Before writing query strings, derive a short query-scope contract from
`instruction.md`, `topic.md`, and `constraints.md`.

The contract must name:

- primary entities
- declared mechanism classes
- allowed comparator entities or model systems
- secondary context that may help interpretation but must not drive first-pass retrieval
- excluded or deferred adjacent biology

First-pass queries must be conservative:

- use the primary entities plus declared mechanism classes
- add synonyms only within those declared mechanism classes
- create comparator queries only when the run explicitly authorizes comparator evidence
- keep comparator queries mechanism-matched to the same declared mechanism classes
- keep secondary context out of the first-pass query set unless the user explicitly requested it as a primary mechanism class

Do not expand first-pass queries into adjacent biological programs merely because
they are plausible downstream explanations. Examples of adjacent classes include
generic transcriptional regulation, chromatin state, lineage dependency,
cofactor biology, signaling pathways, immune context, metabolism, development,
or disease phenotype when the user asked for a narrower mechanism class. These
may be recorded as secondary context or synthesis hypotheses, but they should
not become retrieval drivers unless the run inputs explicitly make them primary.

Recommended query families:

- one or more direct target queries, each pairing the primary entity with one declared mechanism class or tight synonym family
- one optional comparator query, only when comparator evidence is run-authorized, pairing comparator entities with the same declared mechanism classes
- one optional rescue query for direct target-mechanism papers that may be older, sparsely indexed, or phrased in unusual language when the run objective depends on such papers

The exact number of queries may vary by run.
Small conservative query sets are preferred in pass 1. Three queries are common,
but the role should not assume that three is mandatory.

## Query quality inspection logic

Query quality should be judged by reading sampled titles and abstracts.

Title-only inspection is not sufficient for most mechanistic literature because:

- titles can look relevant while the abstract reveals clinical or epidemiologic drift
- abstracts reveal whether the paper is really about the target mechanism space or only incidental mention of run-related terms

This sampling step is not the formal `abstractReviewer` stage.
It is a lightweight quality-control pass used only to decide whether the search strategy is acceptable.
Each optimization round must be recorded in `query_diagnostics.csv` or an equivalent structured table before collection is finalized.

## PMC Feedback In Query Loops

When a loop provides PMC mechanism feedback, treat it as a calibration signal
inside the original query-scope contract, not as permission to broaden the run.
Retain keyword families that retrieved direct mechanisms, remove or narrow
keyword families that retrieved repeated noise, and add rescue terms for
missing mechanisms only when those terms are synonyms, assays, or entities
inside the declared mechanism classes.

PMC full text may reveal adjacent mechanisms or broader explanatory biology.
Those signals should be recorded as `secondary_context` or downstream synthesis
notes unless they map back to the declared mechanism classes. They must not be
added to learned rerun queries as new primary mechanism classes unless:

- the original user request already authorized that class,
- `runGuidanceReviser` explicitly changes the query-scope contract with an evidence-grounded rationale, and
- the revised `constraints.md` marks the new class as primary rather than secondary.

Before generating the learned rerun query, verify that `runGuidanceReviser` has already revised `instruction.md` and `topic.md` and recorded the revision. The search strategy must reflect the revised guidance plus PMC feedback, not only the original user request.

Do not rebuild the query merely to reduce count.
Rebuild it to preserve the user objective, stay inside declared mechanism scope,
reduce predictable noise, and lower downstream PDF burden.

## Retrieval inspection heuristics

`pubmedKeywordScout` should treat retrieval refinement as a sampling problem, not a full-review problem.

Recommended first-pass inspection:

- if a query returns `<= 200` records, inspect about `20-40` records
- if a query returns `201-1000` records, inspect about `30-50` records
- if a query returns `> 1000` records, inspect about `50-75` records

Recommended sampling mix:

- prioritize the first `20-30` most recent or top-ranked records
- add a spread sample from later parts of the result set when total retrieval is large
- use enough spread to detect drift, not just top-hit quality

Required diagnostics per query:

- raw PubMed hit count before any explicit constraint
- inspected sample size
- how the sample was selected
- approximate sampled precision
- dominant noise classes
- missing concepts or evidence types
- recall signals, including seed papers or older mechanism language when available
- decision for the next round

Suggested noise thresholds:

- if roughly `< 30%` of the inspected sample looks on-topic, treat the query as too noisy and refine it
- if roughly `30-60%` looks on-topic, the query may be usable but should usually be tightened if recall is still acceptable
- if roughly `> 60%` looks on-topic, the query is usually good enough to proceed unless important known concepts are missing

Tail-risk inspection:

- if a direct query returns a manageable number of records, do not inspect only the newest hits
- add a spread sample from the middle or tail when older foundational papers are plausible
- result collection will not be capped; use tail inspection to refine queries without losing older foundational records

## How to judge query quality

Judge each query on four dimensions:

- precision
  What fraction of sampled papers are genuinely related to the run objective.
- recall proxy
  Whether the sampled hits include the kinds of papers the run is trying to find.
- drift
  Whether the query leaks into clinical, epidemiologic, therapeutic, social, or unrelated systems papers.
- diversity
  Whether the query captures multiple relevant mechanistic subtypes rather than only one narrow phrasing.

Practical interpretation:

- low precision means the query needs tightening
- missing obvious mechanism classes means the query needs expansion
- high top-hit quality but strong later drift means the query still needs refinement
- a smaller hit count is not automatically better if it suppresses relevant mechanism papers

## How to revise the query

If the query is too noisy:

- add more mechanistic anchors
- add central run-objective terms that distinguish the target evidence from broad background material
- tighten broad terms by pairing them with the relevant functional or experimental context
- remove terms that are attracting recurrent off-topic clusters

If the query is too narrow:

- add synonym families found in relevant sampled abstracts
- relax overly strict co-occurrence requirements
- add alternate language used for the same declared mechanism class
- do not add a new adjacent mechanism class merely because it is biologically plausible

If the query looks conceptually right but still misses a relevant paper:

- determine whether the miss is caused by title/abstract wording, date-sorted ranking, or overly narrow query structure
- if the paper matches the broad concept query but sits deep in the ranked list, verify that the collector is collecting the full result set and add a rescue query if needed
- if the paper uses distinctive wording, add a rescue query using that wording, exact title fragments, or a seed PMID when appropriate
- record the failure mode in `query_refinement_report.md` so later runs inherit the lesson

If the query misses known relevant paper types:

- inspect the wording of those papers
- identify missing title or abstract vocabulary
- incorporate that vocabulary into the next revision only if it maps to a declared mechanism class or an explicitly authorized comparator class

Query revision must respond to observed failure modes in sampled abstracts, not to intuition alone.

Recommended post-refinement behavior:

- after refinement, collect the full cohort of papers that are still potentially related to the run objective
- run constraints must not cap PubMed retrieval; if collection is too large, revise queries based on diagnostics while protecting recall

## Optimization round control

Use topic clarity to decide how long to refine:

- clear topic, clear entities, clear mechanism: usually `2-4` rounds
- clear entity but broad mechanism: usually `3-5` rounds
- vague or exploratory topic: continue while diagnostics show concrete missing concepts or dominant noise classes

Do not keep optimizing merely because a smaller count would be convenient.
Continue beyond `6` rounds only when the diagnostics identify a specific unresolved problem, such as a missing concept family, a recurring noise class, or failure to retrieve trusted seed papers.
Stop when the next likely revision would trade away recall faster than it improves precision.

## Important interpretation

A query returning `10,000` records is not automatically bad, but it often signals that the search should be tightened before collection.
A query returning `500` records is not automatically good, but it is often easier to manage if sample precision is acceptable.

The scout's job is recall-oriented:

- find anything potentially related
- reduce obvious retrieval noise by improving the query
- not decide that only a subset deserves abstract review

## Deciding when the query set is ready

The query set is ready when:

- sampled precision is acceptable for the run
- obvious off-topic drift is no longer dominant
- the queries appear to cover the intended mechanism space
- further tightening would likely lose relevant papers faster than it improves precision
- known or strongly expected direct mechanism papers are either retrieved by the broad direct query or protected by an explicit rescue query

The final collected paper count should be determined by:

- the accepted query set
- deduplication across all active queries

The final count should not be chosen by an informal target such as wanting a shortlist of `100` papers.
The final count also must not be chosen by a formal retrieval cap; PubMed collection caps are forbidden.

## Must not do

- decide final paper relevance
- replace exhaustive abstract review with a hidden pre-review filter
- introduce a PubMed collection cap
