# Query Refinement Report

## Run

- `run_id`: `pax8_protein_level_regulation_20260830`

## Why refinement was needed

- Pass 1 achieved much better full-text coverage than the earlier PAX8-only
- framing, but it still retrieved substantial noise that can be reduced without
  suppressing family-wide comparator mechanisms.

## Diagnostics Used

- hit counts:
  pass 1 collected 626 records
- sampled precision:
  pass 1 abstract review advanced 125 and PMC import yielded 42 usable full
  texts
- noise classes:
  marker/IHC papers, recombinase-driver nomenclature, and non-mechanistic
  transcription/context papers
- missing concepts:
  explicit deubiquitination and some named modifier/regulator terms
- recall signals:
  useful mechanisms were distributed across multiple PAX family members
- PMC mechanism feedback:
  `loop_001`
- PDF queue signal:
  large deferred queue remains, so final access should be informed by learned
  mechanism criteria
- query-scope contract:
  unchanged family-wide scope

## Main changes

1. Added safe negative filters for `Pax8-Cre`, `Pax7-CreER`,
   `immunohistochemistry`, `biomarker`, `promoter`, and `target` noise.
2. Tightened protein-level mechanism language around degradation, PTM, and
   localization.
3. Preserved family-wide comparator retrieval instead of narrowing back to
   PAX8.

## Learning Application

- retained terms/patterns from readable full text:
  `ubiquitination`, `protein degradation`, `protein stability`,
  `post-translational`, `nuclear localization`, and family-wide PAX
  comparator signal
- rescue terms for missed in-scope evidence:
  explicit deubiquitination wording and broader PTM phrasing
- terms/patterns demoted to context only:
  oncology motivation, developmental context, and generic chromatin framing
- terms/patterns excluded as repeated noise:
  recombinase-driver strings, marker studies, and promoter/target papers
- reviewer-rule changes:
  keep family comparator mechanism papers but exclude papers where PAX is not
  the mechanistically regulated protein

## Scope Check

- in-scope synonyms or rescue terms added:
  yes
- adjacent concepts kept as secondary context:
  yes
- any primary-scope expansion:
  no
- rationale if primary scope expanded:
  not applicable

## Expected Burden Effect

- expected collection change:
- expected abstract-promotion change:
- rationale if the learned rerun may not shrink:

## Expected tradeoff

-

## Stop Rule Assessment

- continue refining:
- stop because:

## Next action

- rerun collection with revised search strategy
