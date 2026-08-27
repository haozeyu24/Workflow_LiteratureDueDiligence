# Search Strategy

## Scoped Search Objective

Retrieve PubMed records that connect PAX8, or explicitly authorized PAX-family comparators, to protein-level mechanisms controlling folding, stability, degradation, nuclear localization, nuclear retention, or nuclear accumulation.

## Query-Scope Contract

- Primary entities: PAX8, paired box 8, paired-box gene 8, PAX-8.
- Primary mechanism classes: folding/chaperone dependence; protein stability/abundance/half-life; degradation/turnover/ubiquitin/proteasome/lysosome/autophagy; nuclear localization/import/export/retention/accumulation.
- Comparator scope: PAX family transcription factors only when paired with the same protein-level mechanism classes.
- Secondary context: oncogenic dependency, thyroid/ovarian/renal/Mullerian lineage biology, transcriptional programs, chromatin regulation.
- Deferred adjacent biology: expression-only, diagnostic marker, prognosis, and lineage-marker papers that lack protein-level regulatory mechanisms.

## Query Set

1. `("PAX8"[Title/Abstract] OR "PAX-8"[Title/Abstract] OR "paired box 8"[Title/Abstract] OR "paired-box gene 8"[Title/Abstract]) AND (stability[Title/Abstract] OR destabilization[Title/Abstract] OR degradation[Title/Abstract] OR turnover[Title/Abstract] OR "half-life"[Title/Abstract] OR ubiquitin*[Title/Abstract] OR proteasome[Title/Abstract] OR proteasomal[Title/Abstract] OR lysosome[Title/Abstract] OR autophagy[Title/Abstract] OR chaperone[Title/Abstract] OR folding[Title/Abstract])`
2. `("PAX8"[Title/Abstract] OR "PAX-8"[Title/Abstract] OR "paired box 8"[Title/Abstract] OR "paired-box gene 8"[Title/Abstract]) AND ("nuclear localization"[Title/Abstract] OR "nuclear localisation"[Title/Abstract] OR "nuclear retention"[Title/Abstract] OR "nuclear accumulation"[Title/Abstract] OR "subcellular localization"[Title/Abstract] OR "subcellular localisation"[Title/Abstract] OR importin[Title/Abstract] OR exportin[Title/Abstract] OR "nuclear import"[Title/Abstract] OR "nuclear export"[Title/Abstract])`
3. `("PAX2"[Title/Abstract] OR "PAX3"[Title/Abstract] OR "PAX5"[Title/Abstract] OR "PAX6"[Title/Abstract] OR "PAX7"[Title/Abstract] OR "PAX9"[Title/Abstract] OR "paired box"[Title/Abstract] OR "paired-box"[Title/Abstract]) AND (stability[Title/Abstract] OR degradation[Title/Abstract] OR turnover[Title/Abstract] OR "half-life"[Title/Abstract] OR ubiquitin*[Title/Abstract] OR proteasome[Title/Abstract] OR proteasomal[Title/Abstract] OR chaperone[Title/Abstract] OR folding[Title/Abstract] OR "nuclear localization"[Title/Abstract] OR "nuclear retention"[Title/Abstract] OR "nuclear accumulation"[Title/Abstract] OR importin[Title/Abstract] OR exportin[Title/Abstract])`

## Rationale

- Query 1 captures direct PAX8 protein stability, degradation, ubiquitin/proteasome, lysosome/autophagy, chaperone, and folding signals.
- Query 2 captures direct PAX8 nuclear localization, retention, import/export, and accumulation signals that might not mention degradation or stability.
- Query 3 captures authorized PAX-family comparator mechanisms that may reveal transferable control points.

## Diagnostic Plan

- Use PubMed hit counts and title/abstract review to estimate whether direct PAX8 mechanisms are sparse and whether comparator evidence is needed.
- Treat PAX8 diagnostic-marker and expression-only records as expected noise if they lack protein-level mechanism terms.
- Treat broad PAX family developmental or mutation papers as comparator noise unless the abstract links a PAX protein to stability, degradation, folding, or nuclear localization.

## Stop Rule

Accept this first-pass strategy if the collected cohort remains reviewable and contains both direct PAX8 mechanism candidates and a comparator pool. Use PMC full-text feedback to refine pass 2 before any manual PDF work.
