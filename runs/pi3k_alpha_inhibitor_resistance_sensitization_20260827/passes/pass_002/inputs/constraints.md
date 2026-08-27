# Constraints

- PubMed collection caps are forbidden by workflow policy.
- Do not add `max_results_per_query`, `max_total_results`, `retmax`, or equivalent collection-cap settings.
- Use scope constraints, query refinement, and downstream batching instead.
- Do not treat generic PI3K pathway papers as in scope unless they connect to PI3K-alpha inhibitor resistance, sensitivity, sensitization, adaptive response, or combination response.
- Do not treat pan-PI3K, PI3K/mTOR, AKT, mTOR, or MAPK inhibitor papers as primary unless the title or abstract links them to PI3K-alpha, PIK3CA mutation, alpelisib, inavolisib, RLY-2608/RLY2608, or a PI3K-alpha-selective inhibitor.
- Keep allosteric inhibitor evidence visible even when early clinical literature is sparse.
- Pass 2 should stop broad combination or clinical papers that do not name a response mechanism, sensitivity/resistance biomarker, adaptive feedback, bypass pathway, or sensitization rationale.
- Preserve sparse allosteric and mutant-selective PI3K-alpha inhibitor records for import when they contain any response, sensitivity, resistance, or PIK3CA-mutant context.
