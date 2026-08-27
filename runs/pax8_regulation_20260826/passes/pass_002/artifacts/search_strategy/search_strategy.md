# Search Strategy

## Scoped Search Objective

Run a learned rerun that preserves direct PAX8 mechanism recall while reducing pass-1 noise. The revised query set emphasizes terms learned from PMC-readable comparator mechanisms and direct PAX8 candidates: SUMOylation, protein stability, protein levels, functional domains, nuclear localization, ubiquitination/proteasomal degradation, Hsp90 client dependence, and targeted degradation.

## Query-Scope Contract

- Primary entities: PAX8, paired box 8, paired-box gene 8, PAX-8.
- Primary mechanism classes: protein stability/protein levels/half-life; SUMOylation/deSUMOylation; ubiquitination/proteasomal degradation; folding/domain stability/chaperone/Hsp90 dependence; functional domains and nuclear localization.
- Comparator scope: PAX family proteins only when the query terms are likely to retrieve mechanisms regulating the PAX protein itself.
- Secondary context: cancer dependency and lineage biology only as interpretive context.
- Deferred adjacent biology: PAX8-AS1, expression-only, diagnostic-marker, downstream target stabilization, and generic developmental/disease biology.

## Query Set

1. `("PAX8"[Title/Abstract] OR "PAX-8"[Title/Abstract] OR "paired box 8"[Title/Abstract] OR "paired-box gene 8"[Title/Abstract]) AND ("protein stability"[Title/Abstract] OR "protein levels"[Title/Abstract] OR stabilization[Title/Abstract] OR destabilization[Title/Abstract] OR degradation[Title/Abstract] OR turnover[Title/Abstract] OR "half-life"[Title/Abstract] OR ubiquitin*[Title/Abstract] OR proteasom*[Title/Abstract] OR sumoylation[Title/Abstract] OR SUMOylation[Title/Abstract] OR deSUMOylation[Title/Abstract]) NOT "PAX8-AS1"[Title/Abstract]`
2. `("PAX8"[Title/Abstract] OR "PAX-8"[Title/Abstract] OR "paired box 8"[Title/Abstract] OR "paired-box gene 8"[Title/Abstract]) AND ("nuclear localization"[Title/Abstract] OR "nuclear localisation"[Title/Abstract] OR "nuclear localization signal"[Title/Abstract] OR "functional domains"[Title/Abstract] OR "subcellular localization"[Title/Abstract] OR "nuclear import"[Title/Abstract] OR "nuclear export"[Title/Abstract] OR "nuclear retention"[Title/Abstract] OR "nuclear accumulation"[Title/Abstract]) NOT "PAX8-AS1"[Title/Abstract]`
3. `("PAX3::FOXO1"[Title/Abstract] OR "PAX3-FOXO1"[Title/Abstract] OR "PAX7-FOXO1"[Title/Abstract] OR "PAX3"[Title/Abstract] OR "PAX7"[Title/Abstract] OR "PAX5"[Title/Abstract] OR "PAX6"[Title/Abstract] OR "PAX2"[Title/Abstract]) AND ("protein levels"[Title/Abstract] OR "protein stability"[Title/Abstract] OR degradation[Title/Abstract] OR ubiquitin*[Title/Abstract] OR monoubiquitination[Title/Abstract] OR proteasom*[Title/Abstract] OR sumoylation[Title/Abstract] OR SUMOylation[Title/Abstract] OR deSUMOylation[Title/Abstract] OR phosphorylation[Title/Abstract] OR acetylation[Title/Abstract] OR hydroxylation[Title/Abstract] OR "Hsp90"[Title/Abstract] OR chaperone[Title/Abstract] OR PROTAC[Title/Abstract] OR degrader[Title/Abstract] OR "nuclear localization"[Title/Abstract])`

## Rationale

- Query 1 rescues direct PAX8 protein stability/degradation/PTM literature and excludes PAX8-AS1 lncRNA noise.
- Query 2 rescues direct PAX8 nuclear localization and functional-domain literature, including older domain-mapping papers.
- Query 3 keeps comparator evidence but removes broad paired-box/developmental terms that drove pass-1 noise.

## Diagnostic Plan

- Confirm that direct PAX8 papers such as PAX8 SUMOylation and PAX8 nuclear localization are present.
- Confirm that comparator papers are actual PAX protein regulation papers rather than generic disease/proteolysis papers.
- Carry the complete accepted cohort through both abstract review stages.

## Stop Rule

If pass 2 yields direct PAX8 candidates plus a compact comparator set and PMC learning no longer reveals an unresolved query defect, mark `final_pdf_pass` and build/retain a PDF queue for unresolved direct papers.
