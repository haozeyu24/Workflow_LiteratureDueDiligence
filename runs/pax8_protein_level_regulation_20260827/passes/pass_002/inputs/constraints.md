# Constraints

- PubMed collection caps are forbidden by workflow policy.
- Do not add `max_results_per_query`, `max_total_results`, `retmax`, or equivalent collection-cap settings.
- Use scope constraints, query refinement, and downstream batching instead.
- This is a fresh run. Do not reuse paper manifests, review tables, mechanism feedback, PDFs, or reports from any prior run.
- Primary inclusion requires protein-level PAX evidence or a plausible PAX protein-complex mechanism. Papers only about transcriptional regulation of PAX expression or PAX downstream genes should be excluded during review unless they contain direct protein-level evidence.
- First-pass search may include other PAX family members as comparators, but only when the query also targets the declared protein-level mechanism classes.
- Oncology context is important for synthesis, especially PAX8 targetability, but should not by itself broaden retrieval to general cancer expression or target-gene studies.
- Pass-2 learned constraint: do not use standalone generic `protein` or standalone generic `nuclear` terms as comparator query anchors; pair them with explicit stability, degradation, localization, import/export/retention, PTM, PPI, or domain terms.
- Pass-2 learned constraint: broad PAX-family comparator papers should advance only when title/abstract evidence is near a PAX entity or PAX fusion protein, not when mechanism words describe unrelated proteins elsewhere in the abstract.
