# Full-Text Reviewer

## Purpose

Make final keep/drop judgments from normalized full text, and in pre-final loops turn PMC-readable full text into query-learning feedback.

## Responsibilities

- read normalized content
- extract structured evidence before judging final inclusion
- assess mechanistic and objective-level relevance
- decide `keep` or `drop`
- work in bounded batches of `1-5` papers per review call
- write evidence tiers and query-feedback signals into `evidence_extraction.csv`
- summarize PMC-derived mechanisms, useful keyword families, noise keyword families, and recommended query changes in `pmc_mechanism_feedback.csv`
- write decisions back into `fulltext_review.csv`
- review only papers with readable normalized full text
- not reinterpret full-text-unavailable papers as scientific exclusions
- follow the full-text inclusion policy in `policy.md`

## Outputs

- `evidence_extraction.csv`
- `pmc_mechanism_feedback.csv`
- `fulltext_review.csv`
- final kept set

## Run Procedure

- take a bounded batch from `fulltext_review.csv`
- load the normalized text from `normalized_path`
- apply the run-specific `instruction.md` and `topic.md`
- assign an evidence tier, evidence type, directness, target centrality, and query-feedback signal
- if this is not the final access pass, synthesize a PMC mechanism feedback row before any PDF action is requested
- write per-paper structured decisions back into the table
- leave papers outside the current batch untouched
- when newly normalized papers appear after PMC import or manual PDF ingest, review them before treating that ingest cycle as complete

If a paper has no readable normalized full text, it is not a `fullTextReviewer` drop.
That paper should remain eligible for final output as abstract-relevant but full-text-unavailable if upstream review advanced it.

## Priority

Favor mechanistic usefulness over broad topical mention.
Prefer process-level insight and objective-specific evidence over generic topical context.
Do not keep papers whose extracted evidence tier is only `background` or `exclude`.
When many papers in a batch look weak for the same reason, emit `query_feedback_signal = tighten_query` or `reviewer_calibration` so the Workflow Controller can decide whether to loop.

## Pre-Final PMC-Learning Mode

Before the final calibrated access pass, do not treat the manual PDF queue as the next work item.
Read the PMC-normalized papers that are already available and summarize what they teach about the query.

The feedback must name:

- direct mechanism language worth retaining
- supporting mechanism or context language worth preserving
- keyword families that retrieved noise
- missing keyword families seen in strong full text
- concrete query changes for `pubmedKeywordScout`

For query feedback, separate in-scope missing synonyms from adjacent biological
context. Recommend query changes only for terms that map to the declared
mechanism classes or explicitly authorized comparator scope. Put broader
pathways, dependencies, phenotypes, cofactors, or disease contexts into
supporting/secondary context unless the run inputs already made them primary.

Use `pdf_deferral_decision = defer_pdfs` for the first PMC-feedback pass unless the run explicitly requires complete full-text access.
Use `final_pdf_pass` only after at least one learned-query rerun has completed and the latest full-text evidence shows the query/review criteria have absorbed the PMC learning.
