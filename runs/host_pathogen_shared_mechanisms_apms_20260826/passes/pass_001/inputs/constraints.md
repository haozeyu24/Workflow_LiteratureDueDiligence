# Constraints

- PubMed collection caps are forbidden by workflow policy.
- Do not add `max_results_per_query`, `max_total_results`, `retmax`, or equivalent collection-cap settings.
- Use scope constraints, query refinement, and downstream batching instead.
- Keep first-pass retrieval anchored to named viruses plus declared interaction/pathway mechanism language.
- Preserve papers about individual named viruses if they contain host mechanism evidence; cross-virus synthesis can happen after retrieval.
- Do not require that the same host protein appears across viruses; pathway or complex convergence is explicitly in scope.
- Exclude generic disease, vaccine, epidemiology, diagnostic, or treatment papers unless host-pathogen mechanism evidence is central in the title or abstract.
