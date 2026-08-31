# Search Strategy

## Run

- `run_id`: `pi3k_alpha_inhibition_resistance_review_20260830`

## Objective summary

- Find mechanistic, translational, and clinical-trial literature explaining resistance, non-response, progression, and resistance-overcoming combinations for PI3K-alpha inhibition in cancer treatment.

## Query Scope Contract

- primary entities: PI3K-alpha; PIK3CA; p110-alpha; PI3K-alpha inhibitors; alpelisib; inavolisib; STX-478/STX478; RLY-2608/RLY2608; approved and investigational PI3K-alpha inhibitors.
- declared mechanism classes: resistance; acquired resistance; intrinsic resistance; adaptive resistance; sensitivity loss; non-response; progression; pathway reactivation; bypass or compensatory signaling; biomarker/genotype-associated resistance; combinations intended to overcome resistance.
- required outcome/evidence-claim terms: resistance mechanism; response; progression; relapse; treatment failure; sensitivity; biomarker; trial outcome; objective response; progression-free survival; combination rationale; overcome resistance.
- authorized comparator scope: related pathway or therapy terms only when paired with PI3K-alpha inhibition and resistance, response, progression, or combination evidence.
- evidence that is not sufficient by itself: generic PI3K pathway biology, PIK3CA mutation prevalence, toxicity-only findings, pharmacokinetics-only findings, trial design without results or resistance rationale.
- secondary context not used as query drivers: precision oncology background, endocrine therapy background, HER2 context, tumor lineage context, broad approval history, broad PI3K pathway background.
- deferred adjacent biology: standalone AKT, mTOR, MAPK, ERBB/HER2, ESR1, PTEN, RTK, immune, metabolic, epigenetic, or cell-cycle biology unless explicitly linked to PI3K-alpha inhibitor resistance, progression, response, or combination design.

## Query set

1. `(("PI3K alpha"[Title/Abstract] OR "PI3K-alpha"[Title/Abstract] OR PI3Kalpha[Title/Abstract] OR PIK3CA[Title/Abstract] OR "p110 alpha"[Title/Abstract] OR p110alpha[Title/Abstract]) AND (inhibitor*[Title/Abstract] OR inhibition[Title/Abstract] OR targeted[Title/Abstract] OR therapy[Title/Abstract]) AND (resistan*[Title/Abstract] OR refractory[Title/Abstract] OR "non-response"[Title/Abstract] OR nonresponse[Title/Abstract] OR progression[Title/Abstract] OR relapse[Title/Abstract] OR "loss of sensitivity"[Title/Abstract] OR bypass[Title/Abstract] OR adaptive[Title/Abstract]) AND (cancer[Title/Abstract] OR tumor[Title/Abstract] OR tumour[Title/Abstract] OR carcinoma[Title/Abstract] OR neoplasm*[Title/Abstract]))`
2. `((alpelisib[Title/Abstract] OR inavolisib[Title/Abstract] OR GDC-0077[Title/Abstract] OR STX478[Title/Abstract] OR "STX-478"[Title/Abstract] OR RLY2608[Title/Abstract] OR "RLY-2608"[Title/Abstract] OR "PI3K alpha inhibitor"[Title/Abstract] OR "PI3K-alpha inhibitor"[Title/Abstract]) AND (resistan*[Title/Abstract] OR refractory[Title/Abstract] OR progression[Title/Abstract] OR relapse[Title/Abstract] OR sensitivity[Title/Abstract] OR response[Title/Abstract] OR biomarker*[Title/Abstract] OR bypass[Title/Abstract] OR adaptive[Title/Abstract]))`
3. `((alpelisib[Title/Abstract] OR inavolisib[Title/Abstract] OR GDC-0077[Title/Abstract] OR STX478[Title/Abstract] OR "STX-478"[Title/Abstract] OR RLY2608[Title/Abstract] OR "RLY-2608"[Title/Abstract] OR PIK3CA[Title/Abstract] OR "PI3K-alpha"[Title/Abstract]) AND ("clinical trial"[Publication Type] OR trial[Title/Abstract] OR phase[Title/Abstract] OR randomized[Title/Abstract] OR cohort[Title/Abstract]) AND (response[Title/Abstract] OR progression[Title/Abstract] OR "progression-free survival"[Title/Abstract] OR "objective response"[Title/Abstract] OR benefit[Title/Abstract] OR failure[Title/Abstract] OR biomarker*[Title/Abstract] OR combination[Title/Abstract]))`
4. `(("PI3K alpha"[Title/Abstract] OR "PI3K-alpha"[Title/Abstract] OR PIK3CA[Title/Abstract] OR alpelisib[Title/Abstract] OR inavolisib[Title/Abstract] OR GDC-0077[Title/Abstract] OR STX478[Title/Abstract] OR "STX-478"[Title/Abstract] OR RLY2608[Title/Abstract] OR "RLY-2608"[Title/Abstract]) AND (combination[Title/Abstract] OR combined[Title/Abstract] OR "dual inhibition"[Title/Abstract] OR "overcome resistance"[Title/Abstract] OR "restore sensitivity"[Title/Abstract] OR rechallenge[Title/Abstract]) AND (resistan*[Title/Abstract] OR progression[Title/Abstract] OR response[Title/Abstract] OR sensitivity[Title/Abstract] OR adaptive[Title/Abstract] OR bypass[Title/Abstract]))`

## Optimization plan

- topic clarity: broad but workable; the run names the drug class, examples, disease setting, clinical-trial need, and resistance evidence goal.
- expected optimization rounds: 3-5 if hit counts or samples show drift; fewer if the first query set has acceptable precision and captures both lab and clinical-trial papers.
- stop rule: stop when sampled abstracts show PI3K-alpha inhibitor plus resistance/response/progression/combination claims without dominant generic PI3K pathway drift, and when named-inhibitor and class-level recall are both represented.

## Learned rerun focusing plan

- prior-pass learning source: none yet; this is pass 1.
- retained in-scope terms that replace or tighten broader terms: pending PMC mechanism feedback.
- rescue terms and the direct evidence gap they address: pending PMC mechanism feedback; named inhibitor aliases are included now as first-pass recall safeguards.
- demoted context/modifier terms that must not drive queries alone: generic PI3K pathway biology, broad cancer context, endocrine/HER2/MAPK/AKT/mTOR context without PI3K-alpha resistance linkage.
- exclusions or negative guidance from repeated noise: pending query diagnostics and PMC feedback.
- expected burden effect: pass 1 may be moderately broad; pass 2 should tighten around PMC-learned resistance and trial-response language.
- rationale if burden is not expected to shrink: not applicable for pass 1.

## Diagnostics summary

- raw hit counts: pending `collect_pubmed.py`.
- sampled precision: pending scout/collector diagnostics.
- dominant noise classes: expected risks include generic PIK3CA mutation prevalence, broad PI3K pathway biology, toxicity-only studies, and trial-design-only records.
- missing concepts: to be checked after initial retrieval; likely aliases include GDC-0077 for inavolisib and alternate spellings for PI3K alpha/PI3K-alpha/PI3Kalpha.
- recall safeguards checked: class-level PI3K-alpha terms, PIK3CA, p110-alpha, named approved/investigational inhibitors, resistance terms, clinical-trial terms, and combination terms.

## Query rationale

- Query 1 captures class-level PI3K-alpha/PIK3CA inhibitor resistance biology in cancer.
- Query 2 protects named-inhibitor recall, including approved and investigational examples named or implied by the user prompt.
- Query 3 targets clinical-trial evidence across phases and outcomes, including failed or low-benefit studies when response, progression, biomarker, or combination evidence is present.
- Query 4 targets resistance-overcoming combinations and restored-sensitivity rationale while requiring PI3K-alpha or named-inhibitor anchors.

## Scope Discipline

- why these queries stay within the declared mechanism classes: every query requires PI3K-alpha/PIK3CA/p110-alpha or a named PI3K-alpha inhibitor and pairs it with resistance, response/progression, trial, biomarker, or combination evidence.
- how each query requires entity plus evidence/mechanism plus outcome/relationship signal: queries combine PI3K-alpha entities with resistance or outcome terms; clinical and combination queries add trial or combination anchors plus response/progression/resistance language.
- adjacent concepts intentionally not queried: AKT, mTOR, MAPK, HER2/ERBB, ESR1, PTEN, RTKs, immune pathways, metabolism, epigenetics, and cell-cycle programs are not standalone query drivers.
- how this strategy favors prompt fidelity before broader recall: it follows the user's PI3K-alpha inhibition and resistance-review request while preserving named inhibitors and clinical-trial evidence without expanding into all PI3K-pathway or cancer-resistance biology.

## Recall safeguards

- Include alternate PI3K-alpha spellings and PIK3CA/p110-alpha names.
- Include named inhibitors from the prompt and the known alternate name GDC-0077 for inavolisib.
- Include clinical trial, phase, randomized, response, progression-free survival, and biomarker language to preserve clinical evidence beyond mechanistic lab studies.
- Include combination, overcome resistance, restore sensitivity, and dual inhibition language to capture resistance-motivated combination strategies.

## Expected gaps

- Some newer investigational inhibitors may have sparse PubMed coverage or abstract wording that omits resistance terms.
- Clinical abstracts may report efficacy without explicitly naming resistance, so pass-1 review should preserve response/progression/biomarker evidence tied to PI3K-alpha inhibitors.
- Mechanistic resistance involving adjacent pathways may be missed if the abstract lacks PI3K-alpha or named-inhibitor anchors; PMC feedback should identify in-scope rescue terms before pass 2.
- Non-PMC full text may be important for clinical trial reports and should remain visible as access cases until final PDF handling.
