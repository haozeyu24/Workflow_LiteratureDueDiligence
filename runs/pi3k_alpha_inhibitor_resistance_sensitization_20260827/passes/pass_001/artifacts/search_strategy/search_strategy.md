# Search Strategy

## Run

- `run_id`: `pi3k_alpha_inhibitor_resistance_sensitization_20260827`

## Objective summary

Find literature on resistance mechanisms and sensitization strategies for PI3K-alpha / PIK3CA-directed inhibitors, including orthosteric agents such as alpelisib and inavolisib and allosteric or mutant-selective agents such as RLY-2608.

## Query Scope Contract

- primary entities: PI3K-alpha, PIK3CA, p110-alpha, PI3K-alpha-selective inhibitors, alpelisib/BYL719, inavolisib/GDC-0077, RLY-2608/RLY2608, and closely related PI3K-alpha or PIK3CA-mutant-selective inhibitors.
- declared mechanism classes: resistance, acquired resistance, adaptive resistance, feedback activation, bypass signaling, pathway rewiring, sensitization, resensitization, combination response, response biomarkers, and mutation-selective/allosteric inhibitor response.
- authorized comparator scope: pan-PI3K, PI3K/mTOR, AKT/mTOR/MAPK, ERBB/HER2, endocrine therapy, CDK4/6, SHP2, MEK, and related combination contexts only when tied to PI3K-alpha inhibitor response or PIK3CA mutation.
- secondary context not used as query drivers: broad breast cancer treatment, endocrine resistance, pathway biology, lineage state, metabolic adaptation, and clinical sequencing when not linked to PI3K-alpha inhibitor response.
- deferred adjacent biology: generic PI3K signaling, broad targeted-therapy resistance, and broad oncology treatment without PI3K-alpha inhibitor resistance or sensitization evidence.

## Query set

1. `((PIK3CA[Title/Abstract] OR "PI3K alpha"[Title/Abstract] OR "PI3K-alpha"[Title/Abstract] OR p110alpha[Title/Abstract] OR "p110 alpha"[Title/Abstract]) AND (alpelisib[Title/Abstract] OR BYL719[Title/Abstract] OR inavolisib[Title/Abstract] OR "GDC-0077"[Title/Abstract] OR RLY2608[Title/Abstract] OR "RLY-2608"[Title/Abstract] OR "PI3K alpha inhibitor"[Title/Abstract] OR "PI3K-alpha inhibitor"[Title/Abstract]) AND (resistance[Title/Abstract] OR resistant[Title/Abstract] OR sensitivity[Title/Abstract] OR sensitization[Title/Abstract] OR sensitizes[Title/Abstract] OR combination[Title/Abstract] OR feedback[Title/Abstract] OR bypass[Title/Abstract]))`
2. `((alpelisib[Title/Abstract] OR BYL719[Title/Abstract] OR inavolisib[Title/Abstract] OR "GDC-0077"[Title/Abstract]) AND (combination[Title/Abstract] OR synergistic[Title/Abstract] OR synergy[Title/Abstract] OR sensitization[Title/Abstract] OR sensitizes[Title/Abstract] OR resensitization[Title/Abstract] OR endocrine[Title/Abstract] OR HER2[Title/Abstract] OR ERBB[Title/Abstract] OR CDK4[Title/Abstract] OR mTOR[Title/Abstract] OR MEK[Title/Abstract] OR MAPK[Title/Abstract]))`
3. `((RLY2608[Title/Abstract] OR "RLY-2608"[Title/Abstract] OR "allosteric PI3K"[Title/Abstract] OR "allosteric PI3K-alpha"[Title/Abstract] OR "mutant-selective PI3K"[Title/Abstract] OR "mutant selective PI3K"[Title/Abstract]) AND (PIK3CA[Title/Abstract] OR "PI3K alpha"[Title/Abstract] OR "PI3K-alpha"[Title/Abstract] OR resistance[Title/Abstract] OR sensitivity[Title/Abstract]))`
4. `((PIK3CA[Title/Abstract] OR "PI3K alpha"[Title/Abstract] OR "PI3K-alpha"[Title/Abstract]) AND ("PI3K inhibitor"[Title/Abstract] OR "PI3K inhibitors"[Title/Abstract] OR "PI3K-alpha inhibitor"[Title/Abstract] OR "PI3K alpha inhibitor"[Title/Abstract]) AND (acquired resistance[Title/Abstract] OR resistance mechanism[Title/Abstract] OR adaptive resistance[Title/Abstract] OR feedback activation[Title/Abstract] OR bypass signaling[Title/Abstract] OR pathway rewiring[Title/Abstract] OR sensitization[Title/Abstract]))`

## Optimization plan

- topic clarity: moderate-high; drug names are specific, but resistance and sensitization mechanisms are broad.
- expected optimization rounds: one conservative first pass, followed by open-full-text learning revision if accessible full text identifies noise families or missing in-scope vocabulary.
- stop rule: proceed when accepted queries cover named inhibitors, PI3K-alpha/PIK3CA terms, resistance mechanisms, sensitization/combinations, and sparse allosteric/mutant-selective literature without generic PI3K-only drift.

## Diagnostics summary

- raw hit counts: q1=273, q2=556, q3=5, q4=41.
- sampled precision: not formally sampled before collection; query terms are restricted to title/abstract and paired with inhibitor-response mechanism anchors.
- dominant noise classes: expected noise includes broad combination clinical reports without resistance mechanism, pan-PI3K papers with weak PI3K-alpha relevance, and general endocrine/HER2 pathway papers.
- missing concepts: sparse allosteric inhibitor literature is expected; allosteric and mutant-selective terms are protected by a rescue query.
- recall safeguards checked: included alpelisib/BYL719, inavolisib/GDC-0077, RLY-2608/RLY2608, PI3K-alpha spelling variants, PIK3CA, p110-alpha, resistance, sensitization, and combination language.

## Query rationale

The query set separates direct drug-resistance/sensitivity literature, combination and sensitization literature, allosteric/mutant-selective rescue literature, and general PI3K-alpha inhibitor resistance-mechanism language. Collection is uncapped; downstream batching handles review burden.

## Scope Discipline

- why these queries stay within the declared mechanism classes: every query pairs PI3K-alpha, PIK3CA, or named inhibitor terms with resistance, sensitization, adaptive feedback, bypass, biomarker, combination, allosteric, or mutant-selective concepts.
- adjacent concepts intentionally not queried: broad PI3K signaling, broad breast cancer treatment, and general targeted therapy resistance are not searched without PI3K-alpha inhibitor anchors.

## Recall safeguards

- Include both generic PI3K-alpha inhibitor wording and individual drug aliases.
- Include allosteric/mutant-selective wording despite low hit counts.
- Include mechanism terms that may appear without a named drug but still pair with PI3K-alpha/PIK3CA and PI3K inhibitor language.

## Expected gaps

- Very recent non-indexed conference data for RLY-2608 may be underrepresented in PubMed.
- Some clinical trial resistance analyses may not expose enough mechanism in abstracts and may enter the PDF queue.
- Broad combination papers may require second-pass abstract review to separate sensitization evidence from routine regimen reporting.
