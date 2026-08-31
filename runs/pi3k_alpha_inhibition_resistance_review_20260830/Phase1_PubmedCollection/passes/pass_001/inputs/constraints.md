# Constraints

- PubMed collection caps are forbidden by workflow policy.
- Do not add `max_results_per_query`, `max_total_results`, `retmax`, or equivalent collection-cap settings.
- Use scope constraints, query refinement, and downstream batching instead.
- First-pass retrieval must pair PI3K-alpha, PIK3CA, p110-alpha, or named PI3K-alpha inhibitors with resistance, response/progression, clinical trial, biomarker, or combination evidence.
- Do not let broad PI3K/AKT/mTOR pathway biology become a standalone query driver.
- Keep alpelisib, inavolisib, STX-478/STX478, and RLY-2608/RLY2608 visible as named-inhibitor recall anchors, while also allowing class-level PI3K-alpha inhibitor terminology.
- Preserve negative, failed, or low-response clinical trial papers when they may explain resistance, non-response, progression, or combination design.
