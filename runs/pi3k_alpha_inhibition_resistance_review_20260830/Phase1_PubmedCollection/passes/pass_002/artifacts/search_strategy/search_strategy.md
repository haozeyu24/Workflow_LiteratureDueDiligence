# Search Strategy

## Run

- `run_id`: `pi3k_alpha_inhibition_resistance_review_20260830`

## Objective summary

- Learned rerun for PI3K-alpha inhibitor resistance in cancer. Pass 2 uses pass-1 PMC feedback to tighten around explicit PIK3CA/PI3K-alpha or named-inhibitor resistance, adaptive/bypass/feedback, pathway-reactivation, biomarker, clinical-response, progression, and combination evidence.

## Query Scope Contract

- primary entities: PI3K-alpha; PIK3CA; p110-alpha; alpelisib; inavolisib/GDC-0077; STX-478/STX478; RLY-2608/RLY2608; PI3K-alpha-selective or mutant-selective PI3K-alpha inhibitors.
- declared mechanism classes: acquired resistance; intrinsic resistance; drug resistance; adaptive resistance; bypass signaling; feedback activation; compensatory signaling; pathway reactivation; biomarker/genotype-associated resistance; resistance-overcoming combinations.
- required outcome/evidence-claim terms: resistance; response; non-response; progression; relapse; sensitivity; biomarker; ctDNA; clinical trial outcome; combination rationale; restored sensitivity; overcome resistance.
- authorized comparator scope: adjacent pathway or endocrine/HER2/AKT/PTEN terms only when paired with PI3K-alpha/PIK3CA or named-inhibitor treatment and a resistance/response/progression/combo claim.
- evidence that is not sufficient by itself: generic PI3K pathway biology, PIK3CA mutation prevalence, broad AKT/PTEN/progression mentions, models without inhibitor resistance, toxicity-only or pharmacokinetic-only records.
- secondary context not used as query drivers: broad cancer treatment background, endocrine resistance background, precision oncology framing, PI3K pathway overviews.
- deferred adjacent biology: standalone AKT, PTEN, mTOR, MAPK, HER2/ERBB, ESR1, RTK, immune, metabolic, epigenetic, and cell-cycle biology.

## Query set

1. `(("PI3K alpha"[Title/Abstract] OR "PI3K-alpha"[Title/Abstract] OR PI3Kalpha[Title/Abstract] OR PIK3CA[Title/Abstract] OR "p110 alpha"[Title/Abstract] OR p110alpha[Title/Abstract]) AND (alpelisib[Title/Abstract] OR inavolisib[Title/Abstract] OR GDC-0077[Title/Abstract] OR inhibitor*[Title/Abstract] OR inhibition[Title/Abstract]) AND ("acquired resistance"[Title/Abstract] OR "intrinsic resistance"[Title/Abstract] OR "drug resistance"[Title/Abstract] OR resistant[Title/Abstract] OR refractory[Title/Abstract] OR "loss of sensitivity"[Title/Abstract]))`
2. `(("PI3K alpha"[Title/Abstract] OR "PI3K-alpha"[Title/Abstract] OR PIK3CA[Title/Abstract] OR alpelisib[Title/Abstract] OR inavolisib[Title/Abstract] OR GDC-0077[Title/Abstract]) AND ("adaptive resistance"[Title/Abstract] OR "bypass signaling"[Title/Abstract] OR "feedback activation"[Title/Abstract] OR "compensatory signaling"[Title/Abstract] OR "pathway reactivation"[Title/Abstract] OR "restore sensitivity"[Title/Abstract] OR "overcome resistance"[Title/Abstract]))`
3. `((alpelisib[Title/Abstract] OR inavolisib[Title/Abstract] OR GDC-0077[Title/Abstract] OR STX478[Title/Abstract] OR "STX-478"[Title/Abstract] OR RLY2608[Title/Abstract] OR "RLY-2608"[Title/Abstract] OR "PI3K-alpha inhibitor"[Title/Abstract] OR "PI3K alpha inhibitor"[Title/Abstract]) AND (trial[Title/Abstract] OR "clinical trial"[Publication Type] OR phase[Title/Abstract] OR randomized[Title/Abstract]) AND (response[Title/Abstract] OR progression[Title/Abstract] OR "progression-free survival"[Title/Abstract] OR biomarker*[Title/Abstract] OR ctDNA[Title/Abstract] OR failure[Title/Abstract] OR resistance[Title/Abstract] OR combination[Title/Abstract]))`
4. `((STX478[Title/Abstract] OR "STX-478"[Title/Abstract] OR RLY2608[Title/Abstract] OR "RLY-2608"[Title/Abstract] OR "mutant-selective PI3K"[Title/Abstract] OR "PI3K alpha selective"[Title/Abstract] OR "PI3K-alpha selective"[Title/Abstract]) AND (cancer[Title/Abstract] OR tumor[Title/Abstract] OR carcinoma[Title/Abstract] OR neoplasm*[Title/Abstract]) AND (response[Title/Abstract] OR biomarker*[Title/Abstract] OR progression[Title/Abstract] OR resistance[Title/Abstract] OR combination[Title/Abstract] OR sensitivity[Title/Abstract]))`

## Optimization plan

- topic clarity: broad but now PMC-calibrated; pass 1 identified useful PI3K-alpha resistance and clinical-response vocabulary but also broad noise from generic PI3K, AKT, PTEN, response, progression, cancers, and models.
- expected optimization rounds: 2-4 if sampled precision remains noisy; stop once direct resistance and clinical-trial evidence are retrieved without broad pathway-only drift.
- stop rule: require PI3K-alpha/PIK3CA/named-inhibitor anchors in every query and only keep broad response/progression/pathway terms when they are dependent evidence terms.

## Learned rerun focusing plan

- prior-pass learning source: `passes/pass_001/artifacts/fulltext_review/pmc_mechanism_feedback.csv`, loop `loop_001`.
- retained in-scope terms that replace or tighten broader terms: PIK3CA; alpelisib; inavolisib; acquired resistance; intrinsic resistance; drug resistance; adaptive resistance; bypass signaling; feedback activation; compensatory signaling; pathway reactivation.
- rescue terms and the direct evidence gap they address: ctDNA, biomarker, progression-free survival, response, progression, and clinical trial terms rescue patient/trial evidence that may not use explicit resistance wording; STX-478/STX478 and RLY-2608/RLY2608 rescue newer investigational inhibitor records.
- demoted context/modifier terms that must not drive queries alone: PI3K, cancers, models, response, progression, AKT, PTEN, endocrine resistance, and broad pathway biology.
- exclusions or negative guidance from repeated noise: do not collect papers where broad PI3K/AKT/PTEN/progression/model language is not anchored to PI3K-alpha/PIK3CA/named-inhibitor resistance or clinical outcome.
- expected burden effect: the learned query set should collect fewer generic pathway and cancer-response records than pass 1 while preserving direct resistance, clinical-trial, biomarker, and combination evidence.
- rationale if burden is not expected to shrink: a similar-sized result set would be acceptable only if newly included papers are driven by in-scope named investigational inhibitors or clinical outcome terms absent from pass 1.

## Diagnostics summary

- raw hit counts: pending `collect_pubmed.py`.
- sampled precision: pending learned rerun diagnostics.
- dominant noise classes: generic PI3K/AKT/PTEN biology, broad cancer progression, models without inhibitor resistance, toxicity-only or pharmacokinetic-only reports.
- missing concepts: newer investigational inhibitors may remain sparse in PubMed; clinical papers may describe response/progression rather than resistance.
- recall safeguards checked: named inhibitor aliases, acquired/intrinsic/adaptive resistance phrases, bypass/feedback/compensatory/reactivation language, ctDNA/biomarker clinical evidence, and combination-overcome-resistance language.

## Query rationale

- Queries 1 and 2 focus the mechanistic corpus on resistance language learned from pass-1 PMC full text.
- Query 3 preserves clinical-trial and biomarker evidence across approved and investigational PI3K-alpha inhibitors while requiring response, progression, resistance, biomarker, or combination signals.
- Query 4 protects sparse newer-inhibitor recall for STX-478/STX478, RLY-2608/RLY2608, and mutant/alpha-selective terminology without allowing them to float free of cancer outcome or resistance evidence.

## Scope Discipline

- why these queries stay within the declared mechanism classes: all queries require PI3K-alpha/PIK3CA/named-inhibitor anchors plus resistance, adaptive/bypass/feedback/reactivation, clinical outcome, biomarker, or combination evidence.
- how each query requires entity plus evidence/mechanism plus outcome/relationship signal: mechanistic queries require resistance or adaptive mechanism terms; clinical queries require trial and response/progression/biomarker/combo terms.
- adjacent concepts intentionally not queried: AKT, PTEN, mTOR, MAPK, HER2/ERBB, ESR1, RTK, immune, metabolic, epigenetic, and cell-cycle terms are not standalone search drivers.
- how this strategy favors prompt fidelity before broader recall: the learned rerun keeps the review centered on PI3K-alpha inhibitor resistance and clinical outcomes rather than a general PI3K-pathway resistance bibliography.

## Recall safeguards

- Preserve PIK3CA, p110-alpha, and PI3K-alpha spelling variants.
- Preserve alpelisib and inavolisib/GDC-0077 from pass-1 retained terms.
- Preserve STX-478/STX478 and RLY-2608/RLY2608 despite likely sparse PubMed wording.
- Preserve trial, biomarker, ctDNA, response, and progression terms for patient-derived evidence that may not use mechanistic resistance language.

## Expected gaps

- Some investigational-inhibitor records may be meeting abstracts, trial registry records, or too new for PubMed indexing.
- Some clinically important resistance mechanisms may appear under adjacent pathway names only in full text and may need final PDF access.
- Query 3 may still retrieve efficacy papers that are useful for trial context but weak for mechanism; abstract review should retain them only when response, progression, biomarker, failure, or combination rationale is visible.
