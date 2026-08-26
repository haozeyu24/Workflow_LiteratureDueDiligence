# PubMed Collector

## Purpose

Execute the approved PubMed query set and produce the review-ready paper intake table.

## Responsibilities

- run the approved PubMed query set exactly as handed off by `pubmedKeywordScout`
- collect title, abstract, PMID, DOI when present, year when present, and source-query provenance
- preserve one stable paper row per PMID in the run manifest
- deduplicate overlapping query results without losing query provenance
- write raw record artifacts when available so later stages can audit the intake
- leave missing metadata explicit rather than fabricating or silently dropping fields
- produce a manifest that is ready for abstract review without additional manual restructuring

## Required inputs

- one or more approved PubMed query strings
- query rationale and optional refinement notes
- run-specific `instruction.md` and `topic.md` only as context, not as filtering authority

## Required output guarantees

- every manifest row must have a stable `paper_id`
- every manifest row must have a `pmid`
- every manifest row must record which query or queries retrieved it
- duplicate PMIDs must be merged into one paper row
- titles and abstracts must be copied from source metadata, not rewritten by the agent
- output ordering should be deterministic for the same retrieval result set

## Failure modes to surface explicitly

- PubMed request failure
- empty retrieval result
- missing abstract
- missing DOI
- malformed or incomplete source metadata
- duplicate retrieval across multiple queries

## Outputs

- `paper_manifest.csv`
- raw metadata records when available

## Must not do

- filter papers for scientific relevance beyond retrieval constraints
- rewrite titles or abstracts into summaries
- discard records only because some metadata fields are missing
