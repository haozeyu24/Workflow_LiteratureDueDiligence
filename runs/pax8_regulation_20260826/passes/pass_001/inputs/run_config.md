# Run Config

- `interaction_mode`: `agent_facing`
- `pdf_policy`: `continue_pmc_only`
- `access_phase`: `pmc_learning`
- `query_optimization_mode`: `adaptive`
- `max_query_optimization_rounds`: `6`
- `min_big_workflow_loops`: `2`
- `max_workflow_loops`: `5`

## Execution Notes

- Use PubMed and PMC first.
- Do not request manual PDFs during PMC-learning passes.
- Use bounded LLM review batches, but do not cap PubMed collection for accepted queries.
- Treat mechanisms in non-PAX8 PAX family members as comparator evidence, not as primary PAX8 evidence.
