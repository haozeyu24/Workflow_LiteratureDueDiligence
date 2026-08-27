# Search Strategy

## Run

- `run_id`:
- `run_id`: `host_pathogen_shared_mechanisms_apms_20260826`

## Objective summary

- Build a mechanism-focused literature pool for six AP-MS/context viruses: KSHV, dengue virus, hepatitis C virus, coxsackievirus, HIV, and Ebola virus. Retrieval should capture virus-host interaction datasets and host pathway mechanism studies that support cross-virus pathway-convergence analysis.

## Query Scope Contract

- primary entities: KSHV/HHV-8; dengue virus/DENV; hepatitis C virus/HCV; coxsackievirus/CVB; HIV; Ebola virus/EBOV.
- declared mechanism classes: virus-host protein interactions, interactomes, AP-MS/proteomics/proximity labeling, host factors, host pathway mechanisms, pathway convergence.
- authorized comparator scope: cross-virus, pan-viral, and systems-biology host-pathogen papers when they include at least one primary virus or directly study shared host pathway mechanisms.
- secondary context not used as query drivers: Chanda/Scripps evaluation, NIAID/HPMI program structure, community-of-agents adoption, later AP-MS prioritization.
- deferred adjacent biology: clinical/epidemiology/vaccine/diagnostic/drug-screen literature without central host mechanism evidence.

## Query set

1. `((KSHV[tiab] OR "Kaposi sarcoma-associated herpesvirus"[tiab] OR "human herpesvirus 8"[tiab] OR HHV-8[tiab]) AND ("protein interaction"[tiab] OR "protein interactions"[tiab] OR interactome[tiab] OR "host factor"[tiab] OR "host factors"[tiab] OR "host pathway"[tiab] OR "host pathways"[tiab] OR "mass spectrometry"[tiab] OR proteomic*[tiab] OR "affinity purification"[tiab] OR AP-MS[tiab]))`
2. `((dengue[tiab] OR DENV[tiab]) AND ("protein interaction"[tiab] OR "protein interactions"[tiab] OR interactome[tiab] OR "host factor"[tiab] OR "host factors"[tiab] OR "host pathway"[tiab] OR "host pathways"[tiab] OR "mass spectrometry"[tiab] OR proteomic*[tiab] OR "affinity purification"[tiab] OR AP-MS[tiab]))`
3. `(("hepatitis C virus"[tiab] OR HCV[tiab]) AND ("protein interaction"[tiab] OR "protein interactions"[tiab] OR interactome[tiab] OR "host factor"[tiab] OR "host factors"[tiab] OR "host pathway"[tiab] OR "host pathways"[tiab] OR "mass spectrometry"[tiab] OR proteomic*[tiab] OR "affinity purification"[tiab] OR AP-MS[tiab]))`
4. `((coxsackievirus[tiab] OR "coxsackie virus"[tiab] OR CVB[tiab]) AND ("protein interaction"[tiab] OR "protein interactions"[tiab] OR interactome[tiab] OR "host factor"[tiab] OR "host factors"[tiab] OR "host pathway"[tiab] OR "host pathways"[tiab] OR "mass spectrometry"[tiab] OR proteomic*[tiab] OR "affinity purification"[tiab] OR AP-MS[tiab]))`
5. `((HIV[tiab] OR "human immunodeficiency virus"[tiab]) AND ("virus-host interactome"[tiab] OR "viral interactome"[tiab] OR interactome[tiab] OR AP-MS[tiab] OR "affinity purification mass spectrometry"[tiab] OR BioID[tiab] OR "proximity labeling"[tiab]))`
6. `((HIV[tiab] OR "human immunodeficiency virus"[tiab]) AND ("host factor"[tiab] OR "host factors"[tiab] OR "restriction factor"[tiab] OR "dependency factor"[tiab] OR "host pathway"[tiab] OR "host pathways"[tiab]) AND (mechanism*[tiab] OR pathway*[tiab] OR interactome[tiab] OR proteomic*[tiab] OR "protein interaction"[tiab]))`
7. `((HIV[tiab] OR "human immunodeficiency virus"[tiab]) AND (proteomic*[tiab] OR "mass spectrometry"[tiab]) AND (host[tiab] OR cellular[tiab]) AND (factor*[tiab] OR pathway*[tiab] OR interact*[tiab]))`
8. `((Ebola[tiab] OR EBOV[tiab]) AND ("protein interaction"[tiab] OR "protein interactions"[tiab] OR interactome[tiab] OR "host factor"[tiab] OR "host factors"[tiab] OR "host pathway"[tiab] OR "host pathways"[tiab] OR "mass spectrometry"[tiab] OR proteomic*[tiab] OR "affinity purification"[tiab] OR AP-MS[tiab]))`
9. `((KSHV[tiab] OR "Kaposi sarcoma-associated herpesvirus"[tiab] OR dengue[tiab] OR DENV[tiab] OR "hepatitis C virus"[tiab] OR HCV[tiab] OR coxsackievirus[tiab] OR HIV[tiab] OR Ebola[tiab] OR EBOV[tiab]) AND (AP-MS[tiab] OR "affinity purification mass spectrometry"[tiab] OR BioID[tiab] OR "proximity labeling"[tiab] OR interactome[tiab] OR "virus-host interactome"[tiab] OR "viral interactome"[tiab]))`
10. `(("virus-host"[tiab] OR "host-virus"[tiab] OR "host pathogen"[tiab] OR "host-pathogen"[tiab]) AND (interactome[tiab] OR proteomic*[tiab] OR "protein interaction"[tiab] OR "host pathway"[tiab] OR "host factor"[tiab]) AND (KSHV[tiab] OR "Kaposi sarcoma-associated herpesvirus"[tiab] OR dengue[tiab] OR DENV[tiab] OR "hepatitis C virus"[tiab] OR HCV[tiab] OR coxsackievirus[tiab] OR HIV[tiab] OR Ebola[tiab] OR EBOV[tiab]))`

## Optimization plan

- topic clarity: clear entities with broad but declared mechanism classes.
- expected optimization rounds: 2 to 4 if diagnostics show major noise or missing obvious interactome/pathway evidence.
- stop rule: proceed when queries retrieve mechanism/interactome/host-factor literature for all six viruses and further tightening would likely lose relevant host pathway papers.

## Diagnostics summary

- raw hit counts: to be filled by collector and diagnostics.
- sampled precision: initial strategy expected to vary by virus, with HIV and HCV likely noisier.
- dominant noise classes: clinical, vaccine, diagnostic, antiviral-only, broad immunology without host factor mechanism.
- missing concepts: AP-MS papers may use assay-specific or dataset paper titles without generic host-pathogen labels.
- recall safeguards checked: dedicated AP-MS/interactome rescue query plus per-virus mechanism queries.

## Query rationale

- Per-virus queries preserve recall for virus-specific mechanism literature. Two combined rescue queries catch systematic interactome/proteomics papers whose abstracts may use "virus-host" or assay language rather than a single pathway term.

## Scope Discipline

- why these queries stay within the declared mechanism classes: every query pairs named viruses with interaction, interactome, host factor, host pathway, mass spectrometry, or proteomics language.
- adjacent concepts intentionally not queried: clinical outcomes, vaccine design, drug discovery, and generic immune signaling are excluded unless retrieved through a mechanism/interactome/host-factor anchor.

## Recall safeguards

- Use broad virus synonyms and MeSH terms where available.
- Include assay-specific AP-MS/proximity-labeling/interactome rescue query.
- Allow cross-virus host-pathogen systems papers if they mention at least one primary virus.

## Expected gaps

- Some AP-MS datasets may not have abstracts that name all viral proteins or host pathways.
- Some older foundational mechanism papers may lack modern "interactome" language.
- Coxsackie literature may use enterovirus terminology that is only partially captured in pass 1.
