# Instruction

Create a recall-oriented literature pool for host-pathogen mechanisms across six viruses with available virus-human AP-MS context: KSHV, dengue virus, hepatitis C virus, coxsackievirus, HIV, and Ebola virus.

Prioritize papers that provide one or more of the following evidence types:

- AP-MS, affinity purification mass spectrometry, immunoprecipitation mass spectrometry, BioID/proximity labeling, interactome, proteomics, or systematic virus-host protein interaction evidence.
- Mechanistic studies linking viral proteins or viral infection to host pathways, host protein complexes, innate immune signaling, antiviral restriction, membrane/vesicle trafficking, translation/RNA processing, ubiquitin-proteasome/autophagy, cell-cycle/apoptosis, or other host pathway perturbations.
- Cross-virus or comparative host-pathogen studies that can help identify shared mechanisms, even when the same human protein is not targeted by multiple viruses.

Use abstract review as triage, not final judgment. Include borderline papers when the abstract plausibly contains host-pathogen mechanism, pathway, or interaction evidence for any named virus. Exclude papers that are purely clinical, epidemiological, vaccine-only, diagnostic-only, structural-only without host mechanism, or antiviral drug-screen-only unless the abstract connects the finding to a host pathway or host factor mechanism.

## Pass 2 Learned Guidance From PMC Full Text

Pass 1 full-text learning reviewed all 1,580 usable PMC-normalized papers from the PMCID-backed set. The learned rerun should be much stricter about retrieval language:

- Retain direct assay terms: interactome, AP-MS, affinity purification mass spectrometry, proximity proteomics, BioID, protein interaction mapping, mass spectrometry, CRISPR screen, RNAi screen, and functional genomics.
- Retain mechanism terms when paired with a primary virus and a host-factor or viral-protein action anchor: host factor, restriction factor, dependency factor, entry factor, viral protein-host protein, interacts, binds, recruits, cleaves, degrades, modulates, antagonizes, restricts, or promotes.
- Retain pathway terms only when coupled to a host factor, viral protein action, or assay anchor. Useful pathway families include ubiquitin/proteasome turnover, autophagy/ER-phagy/reticulophagy, vesicle trafficking/entry, interferon/innate immune antagonism, nuclear import, RNA-binding proteins, and replication complex.
- Treat patient biomarker omics, plasma/serum proteomics, generic metabolomics, network pharmacology, molecular docking, vaccine, diagnostic, epidemiology, broad antiviral scaffold reviews, and non-primary-virus-only omics papers as durable retrieval/review noise.

## Query Scope Contract

- Primary entities: KSHV/Kaposi sarcoma-associated herpesvirus/human herpesvirus 8/HHV-8; dengue virus/DENV; hepatitis C virus/HCV; coxsackievirus/CVB/enterovirus B when paired with coxsackie; HIV/human immunodeficiency virus; Ebola virus/EBOV.
- Declared mechanism classes for PubMed retrieval: host-pathogen protein interactions; virus-host interactomes; AP-MS/proteomics/proximity-labeling evidence; host factor and host pathway mechanisms; pathway convergence across different viral proteins or viruses.
- Authorized comparator entities or systems: cross-virus studies, pan-viral host factor studies, and host-pathogen systems biology studies are allowed when they include at least one primary virus or directly address shared host pathway mechanisms relevant to the primary viruses.
- Secondary context for synthesis only: NIAID/HPMI program context, Chanda/Scripps collaborator evaluation, community-of-agents adoption, and later prioritization using Krogan AP-MS data.
- Adjacent biology deferred from first-pass retrieval: generic virology, clinical outcomes, epidemiology, vaccine development, antiviral compound screening, and broad immune biology unless paired with host-pathogen interaction or pathway mechanism.
