# Constraints

- PubMed collection caps are forbidden by workflow policy.
- Do not add `max_results_per_query`, `max_total_results`, `retmax`, or equivalent collection-cap settings.
- Use scope constraints, query refinement, and downstream batching instead.
- Treat this as a methods-and-benchmarking literature review rather than a purely biomedical mechanism review.
- Do not restrict retrieval to clinical trial papers only; allow benchmark and tool-comparison papers from broader document AI when they address table-heavy or layout-complex PDFs.
- Prefer papers with explicit evaluation rubrics, datasets, tool comparisons, or error analyses.
- Keep manuscript-feasibility judgments grounded in the collected benchmarking literature rather than speculation.
- Pass 2 abstract reviewers should exclude generic `multimodal`, `validation`, `evaluation`, or `table` hits unless the document/PDF/table/layout/OCR object is the extraction or benchmark target.
- Do not include papers solely because they have data extraction tables, clinical validation tables, EHR tabular data, imaging multimodality, or LLM clinical decision benchmarking.
