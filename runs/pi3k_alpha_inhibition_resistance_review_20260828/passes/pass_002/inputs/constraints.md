# Constraints

- PubMed collection caps are forbidden by workflow policy.
- Do not add `max_results_per_query`, `max_total_results`, `retmax`, or equivalent collection-cap settings.
- Use scope constraints, query refinement, and downstream batching instead.
- Prompt scope assessment: broad_but_workable.
- Preserve clinical trial papers across phases, including positive, negative, failed, terminated, dose-escalation, expansion, and biomarker-analysis reports when a PI3K-alpha-directed inhibitor is central to the regimen.
- Preserve laboratory mechanism papers even when they are not tied to a named clinical trial, if PI3K-alpha inhibition or a PIK3CA-directed inhibitor is central to the resistance mechanism.
- Keep trial-to-mechanism links explicit; do not infer a resistance mechanism from a clinical outcome unless the paper provides biomarker, genomic, pharmacodynamic, or mechanistic evidence.
- In first-pass retrieval, do not expand to all PI3K inhibitor resistance unless the query also contains a PI3K-alpha/PIK3CA-directed entity, named PI3K-alpha inhibitor, or directly relevant PI3K-alpha clinical context.
- Pass 2 learned constraint: translational biomarker terms may drive PubMed retrieval only when paired with named PI3K-alpha-directed inhibitor terms or direct PI3K-alpha inhibitor phrasing.
- Pass 2 learned exclusion: cost-effectiveness, pharmacoeconomic, chemistry/SAR, and broad review-only papers are background unless they include explicit PI3K-alpha inhibitor trial outcome, biomarker, resistance, or combination mechanism evidence.
