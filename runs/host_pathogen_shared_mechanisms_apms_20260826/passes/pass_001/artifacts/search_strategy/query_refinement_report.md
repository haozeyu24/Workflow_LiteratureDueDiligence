# Query Refinement Report

## Round 1 refinement

Initial per-virus queries included broad NCBI MeSH terms for host-pathogen interactions. Count probing showed the initial HIV query returned 7,868 records and HCV returned 2,738 records, making the HIV query too broad for mechanism-focused triage. The query set was revised to rely on explicit title/abstract mechanism terms and to split HIV into more specific interactome/proteomics, host-factor/pathway mechanism, and host-proteomics queries.

This revision preserves the declared mechanism classes: virus-host interactions, AP-MS/interactome/proteomics, host factors, and host pathway mechanisms. It does not add clinical, vaccine, epidemiology, or treatment concepts as retrieval drivers.

## Run

- `run_id`:

## Why refinement was needed

-

## Diagnostics Used

- hit counts:
- sampled precision:
- noise classes:
- missing concepts:
- recall signals:
- PMC mechanism feedback:
- PDF queue signal:
- query-scope contract:

## Main changes

1.

## Scope Check

- in-scope synonyms or rescue terms added:
- adjacent concepts kept as secondary context:
- any primary-scope expansion:
- rationale if primary scope expanded:

## Expected tradeoff

-

## Stop Rule Assessment

- continue refining:
- stop because:

## Next action

- rerun collection with revised search strategy
