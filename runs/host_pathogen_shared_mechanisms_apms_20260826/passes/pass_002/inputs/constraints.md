# Constraints

- PubMed collection caps are forbidden by workflow policy.
- Do not add `max_results_per_query`, `max_total_results`, `retmax`, or equivalent collection-cap settings.
- Use scope constraints, query refinement, and downstream batching instead.
- Keep first-pass retrieval anchored to named viruses plus declared interaction/pathway mechanism language.
- Preserve papers about individual named viruses if they contain host mechanism evidence; cross-virus synthesis can happen after retrieval.
- Do not require that the same host protein appears across viruses; pathway or complex convergence is explicitly in scope.
- Exclude generic disease, vaccine, epidemiology, diagnostic, or treatment papers unless host-pathogen mechanism evidence is central in the title or abstract.
- Pass 2 retrieval must not use broad `host pathway` or `proteomic` terms unless they are paired with an assay, host factor, viral protein, functional-genomics, or action-verb mechanism anchor.
- Durable noise exclusions for pass 2: patient biomarker omics, plasma or serum proteomics, generic metabolomics, network pharmacology, molecular docking, vaccine studies, diagnostic studies, epidemiology, antiviral scaffold reviews, and non-primary-virus-only omics papers.
