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

## Outputs

- `search_strategy.md`
- `query_refinement_report.md` when the strategy is revised
- optional machine-readable query file

## Query construction logic

Start from:

- the scientific objective in `instruction.md`
- the scope and entities in `topic.md`
- any explicit limits in `constraints.md`

Do not start from a memorized topic template alone.
The query set must be derived from the current run inputs.

Recommended first-pass construction:

- identify the domain entities named in the run
- identify the mechanistic concepts of interest
- identify the desired evidence type or assay language if the run specifies one
- identify likely synonym families for the mechanism space
- convert those pieces into a small set of complementary PubMed queries
- identify whether the topic is likely to depend on older foundational mechanism papers and plan a recall safeguard for them

Recommended query families:

- one query for direct entity-interaction or dependency language
- one query for mechanism, pathway, process, or complex language
- one query for explicit shared, conserved, common, or convergence language when cross-entity reasoning matters
- one rescue query for direct target-mechanism papers that may be older, sparsely indexed, or phrased in unusual language when the run objective depends on such papers

The exact number of queries may vary by run.
Three queries are common, but the role should not assume that three is mandatory.

## Query quality inspection logic

Query quality should be judged by reading sampled titles and abstracts.

Title-only inspection is not sufficient for most mechanistic literature because:

- titles can look relevant while the abstract reveals clinical or epidemiologic drift
- abstracts reveal whether the paper is really about the target mechanism space or only incidental mention of run-related terms

This sampling step is not the formal `abstractReviewer` stage.
It is a lightweight quality-control pass used only to decide whether the search strategy is acceptable.

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

Suggested noise thresholds:

- if roughly `< 30%` of the inspected sample looks on-topic, treat the query as too noisy and refine it
- if roughly `30-60%` looks on-topic, the query may be usable but should usually be tightened if recall is still acceptable
- if roughly `> 60%` looks on-topic, the query is usually good enough to proceed unless important known concepts are missing

Tail-risk inspection:

- if a direct query returns a manageable number of records, do not inspect only the newest hits
- add a spread sample from the middle or tail when older foundational papers are plausible
- if result collection will later be capped per query, verify that the cap will not exclude relevant older records

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
- add alternate language used for the same concept family, such as pathway, machinery, complex, trafficking, regulator, dependency factor, or control mechanism

If the query looks conceptually right but still misses a relevant paper:

- determine whether the miss is caused by title/abstract wording, date-sorted ranking, or collection caps
- if the paper matches the broad concept query but sits too deep in the ranked list, raise or remove the per-query cap when feasible
- if the paper uses distinctive wording, add a rescue query using that wording, exact title fragments, or a seed PMID when appropriate
- record the failure mode in `query_refinement_report.md` so later runs inherit the lesson

If the query misses known relevant paper types:

- inspect the wording of those papers
- identify missing title or abstract vocabulary
- incorporate that vocabulary into the next revision

Query revision must respond to observed failure modes in sampled abstracts, not to intuition alone.

Recommended post-refinement behavior:

- after refinement, collect the full cohort of papers that are still potentially related to the run objective
- run constraints may cap retrieval for practical reasons, but that cap must be explicit in the run inputs rather than silently introduced by the scout

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
- any explicit run limits in `constraints.md`

The final count should not be chosen by an informal target such as wanting a shortlist of `100` papers.

## Must not do

- decide final paper relevance
- replace exhaustive abstract review with a hidden pre-review filter
