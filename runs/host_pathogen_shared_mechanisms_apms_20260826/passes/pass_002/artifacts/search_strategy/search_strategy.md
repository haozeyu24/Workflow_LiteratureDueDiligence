# Search Strategy

## Run

- `run_id`:
- `run_id`: `host_pathogen_shared_mechanisms_apms_20260826`

## Objective summary

- Learned pass 2 query strategy reconstructed from pass 1 PMC full-text feedback after reviewing all 1,580 usable PMC-normalized papers. The goal is to retain direct virus-host interaction and host-factor mechanism evidence while removing broad clinical, biomarker, network-pharmacology, and generic pathway/proteomics noise.

## Query Scope Contract

- primary entities: KSHV/HHV-8; dengue virus/DENV; hepatitis C virus/HCV; coxsackievirus/CVB; HIV; Ebola virus/EBOV.
- declared mechanism classes: AP-MS/proximity proteomics/interactome/protein interaction mapping; host restriction/dependency/entry factors; viral protein-host protein action mechanisms; CRISPR/RNAi functional-genomics host-factor screens; pathway convergence only when tied to host factors, viral proteins, or assays.
- authorized comparator scope: cross-virus and pan-viral host-factor/interactome studies when they include at least one primary virus or directly study shared host-pathogen pathway convergence.
- secondary context not used as query drivers: broad immune, metabolic, clinical, and therapeutic interpretation unless anchored to host-factor or viral-protein mechanism evidence.
- deferred adjacent biology: patient biomarker omics, plasma/serum proteomics, generic metabolomics, network pharmacology, molecular docking, vaccine/diagnostic/epidemiology, antiviral scaffold reviews, non-primary-virus-only omics.

## Query set

1. `((KSHV[tiab] OR "Kaposi sarcoma-associated herpesvirus"[tiab] OR "human herpesvirus 8"[tiab] OR HHV-8[tiab]) AND (interactome[tiab] OR AP-MS[tiab] OR "affinity purification mass spectrometry"[tiab] OR "proximity proteomics"[tiab] OR "proximity labeling"[tiab] OR BioID[tiab] OR "protein interaction mapping"[tiab] OR ("viral protein"[tiab] AND ("host protein"[tiab] OR "cellular protein"[tiab]))))`
2. `((KSHV[tiab] OR "Kaposi sarcoma-associated herpesvirus"[tiab] OR "human herpesvirus 8"[tiab] OR HHV-8[tiab]) AND ("host factor"[tiab] OR "restriction factor"[tiab] OR "dependency factor"[tiab] OR "entry factor"[tiab] OR "host E3 ubiquitin ligase"[tiab] OR "viral protein-host protein"[tiab]) AND (interacts[tiab] OR binds[tiab] OR recruits[tiab] OR cleaves[tiab] OR degrades[tiab] OR modulates[tiab] OR antagonizes[tiab] OR restricts[tiab] OR promotes[tiab] OR mechanism*[tiab]))`
3. `((dengue[tiab] OR DENV[tiab]) AND (interactome[tiab] OR AP-MS[tiab] OR "affinity purification mass spectrometry"[tiab] OR "proximity proteomics"[tiab] OR "proximity labeling"[tiab] OR BioID[tiab] OR "protein interaction mapping"[tiab] OR ("viral protein"[tiab] AND ("host protein"[tiab] OR "cellular protein"[tiab]))))`
4. `((dengue[tiab] OR DENV[tiab]) AND ("host factor"[tiab] OR "restriction factor"[tiab] OR "dependency factor"[tiab] OR "entry factor"[tiab] OR "host E3 ubiquitin ligase"[tiab] OR "viral protein-host protein"[tiab] OR "replication complex"[tiab]) AND (interacts[tiab] OR binds[tiab] OR recruits[tiab] OR cleaves[tiab] OR degrades[tiab] OR modulates[tiab] OR antagonizes[tiab] OR restricts[tiab] OR promotes[tiab] OR mechanism*[tiab]))`
5. `(("hepatitis C virus"[tiab] OR HCV[tiab]) AND (interactome[tiab] OR AP-MS[tiab] OR "affinity purification mass spectrometry"[tiab] OR "proximity proteomics"[tiab] OR "proximity labeling"[tiab] OR BioID[tiab] OR "protein interaction mapping"[tiab] OR ("viral protein"[tiab] AND ("host protein"[tiab] OR "cellular protein"[tiab]))))`
6. `(("hepatitis C virus"[tiab] OR HCV[tiab]) AND ("host factor"[tiab] OR "restriction factor"[tiab] OR "dependency factor"[tiab] OR "entry factor"[tiab] OR "host E3 ubiquitin ligase"[tiab] OR "viral protein-host protein"[tiab] OR "replication complex"[tiab]) AND (interacts[tiab] OR binds[tiab] OR recruits[tiab] OR cleaves[tiab] OR degrades[tiab] OR modulates[tiab] OR antagonizes[tiab] OR restricts[tiab] OR promotes[tiab] OR mechanism*[tiab]))`
7. `((coxsackievirus[tiab] OR "coxsackie virus"[tiab] OR CVB[tiab]) AND (interactome[tiab] OR AP-MS[tiab] OR "affinity purification mass spectrometry"[tiab] OR "proximity proteomics"[tiab] OR "proximity labeling"[tiab] OR BioID[tiab] OR "protein interaction mapping"[tiab] OR ("viral protein"[tiab] AND ("host protein"[tiab] OR "cellular protein"[tiab]))))`
8. `((coxsackievirus[tiab] OR "coxsackie virus"[tiab] OR CVB[tiab]) AND ("host factor"[tiab] OR "restriction factor"[tiab] OR "dependency factor"[tiab] OR "entry factor"[tiab] OR "host E3 ubiquitin ligase"[tiab] OR "viral protein-host protein"[tiab] OR "replication complex"[tiab]) AND (interacts[tiab] OR binds[tiab] OR recruits[tiab] OR cleaves[tiab] OR degrades[tiab] OR modulates[tiab] OR antagonizes[tiab] OR restricts[tiab] OR promotes[tiab] OR mechanism*[tiab]))`
9. `((HIV[tiab] OR "human immunodeficiency virus"[tiab]) AND (interactome[tiab] OR AP-MS[tiab] OR "affinity purification mass spectrometry"[tiab] OR "proximity proteomics"[tiab] OR "proximity labeling"[tiab] OR BioID[tiab] OR "protein interaction mapping"[tiab] OR ("viral protein"[tiab] AND ("host protein"[tiab] OR "cellular protein"[tiab]))))`
10. `((HIV[tiab] OR "human immunodeficiency virus"[tiab]) AND ("host factor"[tiab] OR "restriction factor"[tiab] OR "dependency factor"[tiab] OR "entry factor"[tiab] OR "host E3 ubiquitin ligase"[tiab] OR "viral protein-host protein"[tiab]) AND (interacts[tiab] OR binds[tiab] OR recruits[tiab] OR cleaves[tiab] OR degrades[tiab] OR modulates[tiab] OR antagonizes[tiab] OR restricts[tiab] OR promotes[tiab] OR mechanism*[tiab]))`
11. `((Ebola[tiab] OR "Ebola virus"[tiab] OR Ebolavirus[tiab] OR EBOV[tiab]) AND (interactome[tiab] OR AP-MS[tiab] OR "affinity purification mass spectrometry"[tiab] OR "proximity proteomics"[tiab] OR "proximity labeling"[tiab] OR BioID[tiab] OR "protein interaction mapping"[tiab] OR ("viral protein"[tiab] AND ("host protein"[tiab] OR "cellular protein"[tiab]))))`
12. `((Ebola[tiab] OR "Ebola virus"[tiab] OR Ebolavirus[tiab] OR EBOV[tiab]) AND ("host factor"[tiab] OR "restriction factor"[tiab] OR "dependency factor"[tiab] OR "entry factor"[tiab] OR "host E3 ubiquitin ligase"[tiab] OR "viral protein-host protein"[tiab] OR "replication complex"[tiab]) AND (interacts[tiab] OR binds[tiab] OR recruits[tiab] OR cleaves[tiab] OR degrades[tiab] OR modulates[tiab] OR antagonizes[tiab] OR restricts[tiab] OR promotes[tiab] OR mechanism*[tiab]))`
13. `((KSHV[tiab] OR "Kaposi sarcoma-associated herpesvirus"[tiab] OR dengue[tiab] OR DENV[tiab] OR "hepatitis C virus"[tiab] OR HCV[tiab] OR coxsackievirus[tiab] OR HIV[tiab] OR Ebola[tiab] OR EBOV[tiab]) AND ("CRISPR screen"[tiab] OR "RNAi screen"[tiab] OR "functional genomics"[tiab]) AND ("host factor"[tiab] OR "host factors"[tiab] OR "dependency factor"[tiab] OR "restriction factor"[tiab]))`
14. `((KSHV[ti] OR "Kaposi sarcoma-associated herpesvirus"[ti] OR dengue[ti] OR DENV[ti] OR "hepatitis C virus"[ti] OR HCV[ti] OR coxsackievirus[ti] OR HIV[ti] OR Ebola[ti] OR EBOV[ti]) AND ("ubiquitin ligase"[tiab] OR proteasome[tiab] OR autophagy[tiab] OR "ER-phagy"[tiab] OR reticulophagy[tiab] OR "nuclear import"[tiab] OR "RNA-binding protein"[tiab] OR "replication complex"[tiab] OR trafficking[tiab]) AND ("host factor"[tiab] OR "host protein"[tiab] OR "viral protein"[tiab]) AND (interacts[tiab] OR binds[tiab] OR recruits[tiab] OR cleaves[tiab] OR degrades[tiab] OR modulates[tiab] OR restricts[tiab] OR promotes[tiab]) NOT (patient*[tiab] OR plasma[tiab] OR serum[tiab] OR biomarker*[tiab] OR metabolomic*[tiab] OR "network pharmacology"[tiab] OR docking[tiab] OR vaccine*[tiab] OR diagnostic*[tiab] OR epidemiolog*[tiab]))`

## Optimization plan

- topic clarity: clear entities with PMC-derived retained/noise terms.
- expected optimization rounds: 1 to 2 count/precision checks before full pass-2 collection.
- stop rule: proceed when pass-2 query count is materially lower than pass 1 while still retrieving direct interactome/proteomics, host-factor, viral-protein action, and functional-genomics mechanisms for all six viruses.

## Diagnostics summary

- raw hit counts: to be filled by pass-2 collector.
- sampled precision: expected to improve by requiring assay/action/host-factor anchors.
- dominant noise classes: patient biomarker omics, network pharmacology, molecular docking, broad antiviral scaffolds, non-primary-virus-only omics.
- missing concepts: older mechanism papers may omit modern interactome/proximity labels.
- recall safeguards checked: per-virus assay and host-factor/action queries plus CRISPR/RNAi and pathway-anchor rescue queries.

## Query rationale

- Pass 1 full-text review showed useful direct evidence concentrated in assay/action anchored terms. Broad "host pathway" and generic "proteomic" wording admitted many clinical or biomarker papers. Pass 2 keeps the same biological scope but uses stronger evidence anchors.

## Scope Discipline

- why these queries stay within the declared mechanism classes: every query pairs a primary virus with an assay term, host-factor term, viral-protein action verb, functional-genomics host-factor term, or learned pathway term anchored to host interaction/action.
- adjacent concepts intentionally not queried: patient omics, drug screens, network pharmacology, molecular docking, vaccines, diagnostics, epidemiology, and generic pathway biology without host-factor or viral-protein action evidence.

## Recall safeguards

- Separate assay and host-factor/action queries per virus protect recall while reducing generic clinical/proteomic drift.
- Functional-genomics rescue query protects host-factor screens that do not use AP-MS/interactome language.
- Learned pathway rescue query is allowed only with host-factor/action anchors.

## Expected gaps

- Some classic host-factor papers may not use current action/interactome wording.
- Some pathway-convergence evidence may still require manual synthesis after pass-2 review.
