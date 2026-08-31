# Search Strategy

## Run

- `run_id`: `pax8_protein_level_regulation_20260830`

## Objective summary

- Learned rerun for family-wide PAX protein regulation, preserving strong
  comparator recall while tightening recurrent noise from pass 1.

## Query Scope Contract

- primary entities:
  `PAX8`, `PAX2`, `PAX3`, `PAX5`, `PAX7`, `PAX family`
- declared mechanism classes:
  protein stability, protein degradation, ubiquitination, deubiquitination,
  post-translational modification, nuclear localization/retention, and
  interaction-dependent protein control
- required outcome/evidence-claim terms:
  stability, steady-state protein level, degradation, localization, retention,
  accumulation, ubiquitination, post-translational regulation, phosphorylation,
  sumoylation
- authorized comparator scope:
  still family-wide
- evidence that is not sufficient by itself:
  marker/IHC language, driver nomenclature, transcription/target-gene papers,
  and generic developmental context
- secondary context not used as query drivers:
  PAX8 oncology motivation
- deferred adjacent biology:
  downstream programs and non-mechanistic lineage studies

## Query set

1. `(("PAX8"[Title/Abstract] OR "PAX2"[Title/Abstract] OR "PAX3"[Title/Abstract] OR "PAX5"[Title/Abstract] OR "PAX7"[Title/Abstract] OR "PAX family"[Title/Abstract]) AND (stability[Title/Abstract] OR "protein stability"[Title/Abstract] OR degradation[Title/Abstract] OR "protein degradation"[Title/Abstract] OR ubiquitin*[Title/Abstract] OR deubiquitin*[Title/Abstract] OR "protein level"[Title/Abstract] OR "steady-state"[Title/Abstract] OR "half-life"[Title/Abstract])) NOT (Pax8cre[Title/Abstract] OR "Pax8-Cre"[Title/Abstract] OR "Pax7-CreER"[Title/Abstract] OR immunohistochem*[Title/Abstract] OR biomarker*[Title/Abstract])`
2. `(("PAX8"[Title/Abstract] OR "PAX2"[Title/Abstract] OR "PAX3"[Title/Abstract] OR "PAX5"[Title/Abstract] OR "PAX7"[Title/Abstract]) AND (sumoylat*[Title/Abstract] OR desumoylat*[Title/Abstract] OR phosphor*[Title/Abstract] OR acetylat*[Title/Abstract] OR methylat*[Title/Abstract] OR "post-translational"[Title/Abstract]) AND (stability[Title/Abstract] OR degradation[Title/Abstract] OR localization[Title/Abstract] OR retention[Title/Abstract] OR accumulation[Title/Abstract])) NOT (promoter[Title/Abstract] OR target[Title/Abstract] OR immunohistochem*[Title/Abstract])`
3. `(("PAX8"[Title/Abstract] OR "PAX2"[Title/Abstract] OR "PAX3"[Title/Abstract] OR "PAX5"[Title/Abstract] OR "PAX7"[Title/Abstract]) AND ("nuclear localization"[Title/Abstract] OR "nuclear retention"[Title/Abstract] OR "nuclear accumulation"[Title/Abstract] OR "nuclear import"[Title/Abstract] OR "nuclear export"[Title/Abstract] OR localization[Title/Abstract]) AND (protein[Title/Abstract] OR transcription factor[Title/Abstract])) NOT (Pax8cre[Title/Abstract] OR "Pax8-Cre"[Title/Abstract] OR "Pax7-CreER"[Title/Abstract])`
4. `(("PAX8"[Title/Abstract] OR "PAX2"[Title/Abstract] OR "PAX3"[Title/Abstract] OR "PAX5"[Title/Abstract] OR "PAX7"[Title/Abstract]) AND (interact*[Title/Abstract] OR bind*[Title/Abstract] OR cofactor*[Title/Abstract] OR partner*[Title/Abstract] OR complex*[Title/Abstract] OR remodel*[Title/Abstract]) AND (stability[Title/Abstract] OR degradation[Title/Abstract] OR localization[Title/Abstract] OR retention[Title/Abstract] OR accumulation[Title/Abstract])) NOT (promoter[Title/Abstract] OR target[Title/Abstract] OR immunohistochem*[Title/Abstract])`
5. `(("PAX8"[Title/Abstract] OR "PAX2"[Title/Abstract] OR "PAX3"[Title/Abstract] OR "PAX5"[Title/Abstract] OR "PAX7"[Title/Abstract]) AND (fold*[Title/Abstract] OR chaperon*[Title/Abstract] OR conformational[Title/Abstract]) AND (stability[Title/Abstract] OR protein[Title/Abstract] OR degradation[Title/Abstract] OR localization[Title/Abstract])) NOT (immunohistochem*[Title/Abstract] OR biomarker*[Title/Abstract])`

## Optimization plan

- topic clarity:
  improved after pass 1; the main task is reducing obvious noise while keeping
  family-wide mechanistic density high
- expected optimization rounds:
  this learned rerun should satisfy the second big loop requirement
- stop rule:
  stop when a final-access PDF shortlist can be generated from a calibrated
  family-wide mechanism pool

## Learned rerun focusing plan

- prior-pass learning source:
  `passes/pass_001/artifacts/fulltext_review/pmc_mechanism_feedback.csv`
- retained in-scope terms that replace or tighten broader terms:
  `ubiquitination`, `protein degradation`, `protein stability`,
  `post-translational`, `nuclear localization`, `PPI-dependent control`
- rescue terms and the direct evidence gap they address:
  explicit deubiquitination and PTM language for mechanism papers that did not
  foreground `PAX8`
- demoted context/modifier terms that must not drive queries alone:
  oncology, developmental framing, marker language, and promoter/target terms
- exclusions or negative guidance from repeated noise:
  `Pax8-Cre`, `Pax7-CreER`, `immunohistochemistry`, `biomarker`
- expected burden effect:
  smaller cohort with better mechanistic precision, but still larger than the
  earlier PAX8-only run
- rationale if burden is not expected to shrink:
  not applicable

## Diagnostics summary

- raw hit counts:
  pending collection
- sampled precision:
  expected improvement relative to the broad pass 1 query set
- dominant noise classes:
  pass 1 suggested marker, driver, and non-mechanistic context noise
- missing concepts:
  named modifying enzymes may still be under-captured
- recall safeguards checked:
  all major PAX-family comparators remain directly queryable

## Query rationale

- Pass 1 showed that family-wide full text is informative enough to justify
  keeping comparator recall high.
- The learned rerun therefore tightens known false positives without reverting
  to a PAX8 bottleneck.

## Scope Discipline

- why these queries stay within the declared mechanism classes:
  each branch stays anchored on protein-level outcomes
- how each query requires entity plus evidence/mechanism plus outcome/relationship signal:
  named PAX-family factors are paired with degradation, PTM, localization, PPI,
  or folding language
- adjacent concepts intentionally not queried:
  downstream-target, promoter, and diagnostic-marker literature
- how this strategy favors prompt fidelity before broader recall:
  it preserves the user's family-wide scope while cutting the wrong kinds of
  broadening

## Recall safeguards

- direct `PAX8` terms remain present in every branch
- comparator-family branches remain first-class rather than rescue-only
- PTM, degradation, localization, PPI, and folding branches all remain active

## Expected gaps

- named regulator terms may still require a later query rescue if PMC feedback
  exposes them
