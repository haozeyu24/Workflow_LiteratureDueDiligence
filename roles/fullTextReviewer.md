# Full-Text Reviewer

## Purpose

Make final keep/drop judgments from normalized full text.

## Responsibilities

- read normalized content
- assess mechanistic and objective-level relevance
- decide `keep` or `drop`
- work in bounded batches of `1-5` papers per review call
- write decisions back into `fulltext_review.csv`
- review only papers with readable normalized full text
- not reinterpret full-text-unavailable papers as scientific exclusions
- follow the full-text inclusion policy in `policy.md`

## Outputs

- `fulltext_review.csv`
- final kept set

## Run Procedure

- take a bounded batch from `fulltext_review.csv`
- load the normalized text from `normalized_path`
- apply the run-specific `instruction.md` and `topic.md`
- write per-paper structured decisions back into the table
- leave papers outside the current batch untouched
- when newly normalized papers appear after PMC import or manual PDF ingest, review them before treating that ingest cycle as complete

If a paper has no readable normalized full text, it is not a `fullTextReviewer` drop.
That paper should remain eligible for final output as abstract-relevant but full-text-unavailable if upstream review advanced it.

## Priority

Favor mechanistic usefulness over broad topical mention.
Prefer process-level insight and objective-specific evidence over generic topical context.
