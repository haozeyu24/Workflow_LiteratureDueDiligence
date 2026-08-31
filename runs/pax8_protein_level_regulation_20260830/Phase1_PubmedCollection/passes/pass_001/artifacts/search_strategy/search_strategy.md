# Search Strategy

## Run

- `run_id`: `pax8_protein_level_regulation_20260830`

## Objective summary

- Retrieve literature on protein-level regulation of PAX-family transcription
  factors, emphasizing stability, degradation, PTM, nuclear
  localization/retention, folding, and interaction-dependent control, while
  preserving later interpretability for PAX8 oncology relevance.

## Query Scope Contract

- primary entities:
  `PAX family`, `PAX8`, `PAX2`, `PAX3`, `PAX5`, `PAX7`
- declared mechanism classes:
  protein stability, degradation, ubiquitination, deubiquitination,
  post-translational modification, folding/chaperone control, nuclear
  import/export/retention/accumulation, and partner-dependent regulation
- required outcome/evidence-claim terms:
  stability, degradation, half-life, protein level, turnover, localization,
  retention, accumulation, import/export, ubiquitination, sumoylation,
  phosphorylation
- authorized comparator scope:
  family-wide; other PAX members are first-class evidence when the mechanism is
  about PAX protein regulation
- evidence that is not sufficient by itself:
  transcriptional regulation, target-gene regulation, marker/IHC papers,
  recombinase-driver references, and non-mechanistic association studies
- secondary context not used as query drivers:
  oncology framing around PAX8 and broader lineage-survival context
- deferred adjacent biology:
  developmental atlases, downstream programs, and chromatin biology without PAX
  protein handling

## Query set

1. `(("PAX8"[Title/Abstract] OR "PAX2"[Title/Abstract] OR "PAX3"[Title/Abstract] OR "PAX5"[Title/Abstract] OR "PAX7"[Title/Abstract] OR "PAX family"[Title/Abstract] OR "paired box"[Title/Abstract]) AND (stability[Title/Abstract] OR degradation[Title/Abstract] OR turnover[Title/Abstract] OR "protein level"[Title/Abstract] OR "steady-state"[Title/Abstract] OR "half-life"[Title/Abstract]) AND (protein[Title/Abstract] OR transcription factor[Title/Abstract]))`
2. `(("PAX8"[Title/Abstract] OR "PAX2"[Title/Abstract] OR "PAX3"[Title/Abstract] OR "PAX5"[Title/Abstract] OR "PAX7"[Title/Abstract] OR "paired box"[Title/Abstract]) AND (ubiquitin*[Title/Abstract] OR deubiquitin*[Title/Abstract] OR proteasom*[Title/Abstract] OR autophag*[Title/Abstract] OR lysosom*[Title/Abstract] OR sumoylat*[Title/Abstract] OR desumoylat*[Title/Abstract] OR phosphor*[Title/Abstract] OR acetylat*[Title/Abstract] OR methylat*[Title/Abstract]) AND (stability[Title/Abstract] OR degradation[Title/Abstract] OR localization[Title/Abstract] OR retention[Title/Abstract] OR accumulation[Title/Abstract]))`
3. `(("PAX8"[Title/Abstract] OR "PAX2"[Title/Abstract] OR "PAX3"[Title/Abstract] OR "PAX5"[Title/Abstract] OR "PAX7"[Title/Abstract] OR "paired box"[Title/Abstract]) AND ("nuclear localization"[Title/Abstract] OR "nuclear retention"[Title/Abstract] OR "nuclear accumulation"[Title/Abstract] OR "nuclear import"[Title/Abstract] OR "nuclear export"[Title/Abstract] OR localization[Title/Abstract] OR trafficking[Title/Abstract]) AND (protein[Title/Abstract] OR transcription factor[Title/Abstract]))`
4. `(("PAX8"[Title/Abstract] OR "PAX2"[Title/Abstract] OR "PAX3"[Title/Abstract] OR "PAX5"[Title/Abstract] OR "PAX7"[Title/Abstract]) AND (interact*[Title/Abstract] OR bind*[Title/Abstract] OR cofactor*[Title/Abstract] OR partner*[Title/Abstract] OR complex*[Title/Abstract] OR remodel*[Title/Abstract]) AND (stability[Title/Abstract] OR degradation[Title/Abstract] OR localization[Title/Abstract] OR retention[Title/Abstract] OR accumulation[Title/Abstract]))`
5. `(("PAX8"[Title/Abstract] OR "PAX2"[Title/Abstract] OR "PAX3"[Title/Abstract] OR "PAX5"[Title/Abstract] OR "PAX7"[Title/Abstract]) AND (fold*[Title/Abstract] OR chaperon*[Title/Abstract] OR conformational[Title/Abstract]) AND (stability[Title/Abstract] OR degradation[Title/Abstract] OR localization[Title/Abstract] OR protein[Title/Abstract]))`

## Optimization plan

- topic clarity:
  moderate; mechanism space is clear but false positives from marker studies,
  recombinase drivers, and non-PAX proteins remain likely
- expected optimization rounds:
  2 to 4, including at least one PMC-learned rerun
- stop rule:
  stop when family-wide mechanistic coverage is credible and learned reruns
  sharpen noise without collapsing comparator recall

## Learned rerun focusing plan

- prior-pass learning source:
  pending first PMC-feedback pass
- retained in-scope terms that replace or tighten broader terms:
  pending
- rescue terms and the direct evidence gap they address:
  pending
- demoted context/modifier terms that must not drive queries alone:
  cancer, developmental, marker, and promoter/target-gene language
- exclusions or negative guidance from repeated noise:
  pending
- expected burden effect:
  first pass may be broad; learned rerun should reduce known false positives
  while keeping mechanistic comparators
- rationale if burden is not expected to shrink:
  not applicable yet

## Diagnostics summary

- raw hit counts:
  pending collection
- sampled precision:
  pending abstract review
- dominant noise classes:
  expected marker/IHC papers, `Pax8-Cre` references, and downstream
  transcription papers
- missing concepts:
  named modifying enzymes and partner-specific regulator terms may be missed in
  pass 1
- recall safeguards checked:
  direct family-wide coverage for stability, PTM, localization, interaction, and
  folding/chaperone mechanisms

## Query rationale

- The first-pass query set is intentionally family-wide because the goal is to
  discover protein-control mechanisms across PAX factors, not to bottleneck on
  the sparse direct PAX8 literature.
- Each query requires both a PAX-family anchor and a protein-level mechanism or
  outcome signal.

## Scope Discipline

- why these queries stay within the declared mechanism classes:
  all query branches are anchored on stability, degradation, PTM, folding,
  localization, or interaction-dependent control
- how each query requires entity plus evidence/mechanism plus outcome/relationship signal:
  a PAX-family term is combined with protein-level mechanism terms and outcome
  terms
- adjacent concepts intentionally not queried:
  promoter regulation, target-gene programs, pure diagnostic-marker papers, and
  broad developmental expression studies
- how this strategy favors prompt fidelity before broader recall:
  it widens recall only across the PAX family, not across unrelated biology

## Recall safeguards

- preserve direct `PAX8` queries inside the family-wide set
- preserve comparator-family retrieval rather than demoting it to rescue logic
- include PTM, degradation, localization, PPI, and folding/chaperone branches

## Expected gaps

- some useful full-text papers may not advertise the mechanism clearly in the
  abstract
- broad `paired box` language may still catch some off-scope records
