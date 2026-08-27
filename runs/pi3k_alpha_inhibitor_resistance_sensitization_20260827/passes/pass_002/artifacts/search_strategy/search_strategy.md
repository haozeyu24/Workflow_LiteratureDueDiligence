# Search Strategy

## Run

- `run_id`: `pi3k_alpha_inhibitor_resistance_sensitization_20260827`

## Objective summary

Learned pass to refine PI3K-alpha inhibitor resistance and sensitization retrieval after pass-1 open-full-text feedback.

## Query Scope Contract

- primary entities: PI3K-alpha, PIK3CA, p110-alpha, alpelisib/BYL719, inavolisib/GDC-0077, RLY-2608/RLY2608, mutant-selective or allosteric PI3K-alpha inhibitors.
- declared mechanism classes: resistance, adaptive feedback, bypass signaling, sensitivity/sensitization, response biomarkers, combination response, mutation-linked response, vertical pathway inhibition, allosteric/mutant-selective response.
- authorized comparator scope: pathway-combination contexts only when tied to PI3K-alpha, PIK3CA, or a named PI3K-alpha inhibitor.
- secondary context not used as query drivers: broad clinical treatment context without resistance/sensitization mechanism.
- deferred adjacent biology: cost-effectiveness, docking, formulation, broad pathway reviews, and non-oncology treatment settings unless directly tied to PI3K-alpha inhibitor response.

## Query set

1. `((alpelisib[Title/Abstract] OR BYL719[Title/Abstract] OR inavolisib[Title/Abstract] OR "GDC-0077"[Title/Abstract] OR RLY2608[Title/Abstract] OR "RLY-2608"[Title/Abstract]) AND (PIK3CA[Title/Abstract] OR "PI3K alpha"[Title/Abstract] OR "PI3K-alpha"[Title/Abstract] OR "p110 alpha"[Title/Abstract] OR p110alpha[Title/Abstract]) AND (resistance[Title/Abstract] OR resistant[Title/Abstract] OR sensitivity[Title/Abstract] OR sensitization[Title/Abstract] OR adaptive[Title/Abstract] OR feedback[Title/Abstract] OR bypass[Title/Abstract] OR biomarker[Title/Abstract] OR mutation[Title/Abstract]))`
2. `((alpelisib[Title/Abstract] OR BYL719[Title/Abstract] OR inavolisib[Title/Abstract] OR "GDC-0077"[Title/Abstract]) AND (combination[Title/Abstract] OR synergy[Title/Abstract] OR synergistic[Title/Abstract] OR sensitization[Title/Abstract] OR sensitizes[Title/Abstract] OR resensitization[Title/Abstract]) AND (PIK3CA[Title/Abstract] OR "PI3K alpha"[Title/Abstract] OR "PI3K-alpha"[Title/Abstract] OR endocrine[Title/Abstract] OR HER2[Title/Abstract] OR ERBB[Title/Abstract] OR mTOR[Title/Abstract] OR MEK[Title/Abstract] OR MAPK[Title/Abstract] OR CDK4[Title/Abstract] OR CDK6[Title/Abstract] OR AKT[Title/Abstract]))`
3. `((PIK3CA[Title/Abstract] OR "PI3K alpha"[Title/Abstract] OR "PI3K-alpha"[Title/Abstract]) AND ("PI3K inhibitor"[Title/Abstract] OR "PI3K-alpha inhibitor"[Title/Abstract] OR "PI3K alpha inhibitor"[Title/Abstract] OR alpelisib[Title/Abstract] OR BYL719[Title/Abstract] OR inavolisib[Title/Abstract]) AND ("RTK"[Title/Abstract] OR HER3[Title/Abstract] OR ERBB3[Title/Abstract] OR insulin[Title/Abstract] OR IGF1R[Title/Abstract] OR ESR1[Title/Abstract] OR PTEN[Title/Abstract] OR RB1[Title/Abstract] OR NF1[Title/Abstract] OR "vertical inhibition"[Title/Abstract] OR "pathway rebound"[Title/Abstract] OR "feedback activation"[Title/Abstract]))`
4. `((RLY2608[Title/Abstract] OR "RLY-2608"[Title/Abstract] OR "allosteric PI3K"[Title/Abstract] OR "mutant-selective PI3K"[Title/Abstract] OR "mutant selective PI3K"[Title/Abstract]) AND (PIK3CA[Title/Abstract] OR "PI3K alpha"[Title/Abstract] OR "PI3K-alpha"[Title/Abstract] OR resistance[Title/Abstract] OR sensitivity[Title/Abstract] OR mutation[Title/Abstract] OR mutant[Title/Abstract]))`

## Optimization plan

- topic clarity: moderate-high after pass-1 learning.
- expected optimization rounds: learned rerun with tightened abstract rules; further loop only if full-text evidence still shows predictable noise.
- stop rule: proceed to final PDF shortlist when pass-2 open full text shows no major missing in-scope resistance/sensitization mechanism family.

## Diagnostics summary

- raw hit counts: q1=316, q2=270, q3=164, q4=10.
- sampled precision: inferred from pass-1 full-text feedback rather than a new title-only sample.
- dominant noise classes: broad clinical combination reports lacking mechanism; non-mechanistic economics/access papers; generic formulation/docking/network-pharmacology records.
- missing concepts: RTK/ERBB/HER3 feedback, insulin/IGF feedback, ESR1/PTEN/RB1/NF1 alterations, vertical pathway inhibition, allosteric/mutant-selective response.
- recall safeguards checked: retained named drugs, PI3K-alpha/PIK3CA anchors, allosteric/mutant-selective rescue terms, and learned feedback/bypass terms.

## Query rationale

Pass 2 uses pass-1 evidence to tighten combination retrieval and add rescue terms for repeatedly relevant resistance and sensitization families.

## Scope Discipline

- why these queries stay within the declared mechanism classes: each query remains anchored to PI3K-alpha/PIK3CA or named PI3K-alpha inhibitor terms plus resistance, sensitivity, feedback, bypass, biomarker, combination, allosteric, or mutant-selective terms.
- adjacent concepts intentionally not queried: broad pathway biology and generic treatment context are excluded unless paired with inhibitor-response evidence.

## Recall safeguards

- Preserve sparse allosteric and mutant-selective inhibitor records.
- Add bypass/feedback rescue terms only inside PI3K-alpha inhibitor response context.
- Keep named approved inhibitor aliases visible.

## Expected gaps

- Very recent meeting-only data may remain outside PubMed.
- Some clinically important resistance analyses may remain in the PDF queue if not PMC-accessible.
