# PMC Mechanism Feedback Schema

One row per PMC-learning pass.

This artifact summarizes what the workflow learned from readable PMC full text before spending effort on manual PDFs.
It is used by the Run Manager and PubMed Search Agent to reconstruct better query keywords.

## Fields

- `loop_id`
  Stable pass label, such as `pmc_learning_1`.
- `source_paper_count`
  Number of PMC-normalized papers read for this feedback pass.
- `direct_mechanisms`
  Semicolon-separated mechanisms or assays that directly match the run objective and the declared mechanism classes.
- `supporting_mechanisms`
  Semicolon-separated indirect but useful mechanisms, contexts, dependencies, or adjacent biology. These are synthesis aids by default, not automatic query-expansion targets.
- `retained_keyword_families`
  Query terms or combinations that retrieved useful in-scope full-text evidence.
- `noise_keyword_families`
  Query terms or combinations that repeatedly retrieved marker-only, clinical-only, background, methods-only, or otherwise low-value papers.
- `missing_keyword_families`
  In-scope mechanism terms, assay terms, entities, or synonyms seen in strong papers but missing from the current query.
- `recommended_query_changes`
  Concrete add/drop/replace/merge instructions for the next query pass. These should stay inside the declared mechanism classes unless the run guidance explicitly expands the query-scope contract.
- `recommended_abstract_rule_changes`
  Concrete calibration changes for abstract reviewers if title/abstract decisions admitted repeated noise.
- `scientific_notes`
  Plain-language summary of what the full-text reviewer learned scientifically
  from readable papers, including positive and negative evidence patterns.
- `topic_learning`
  Compact retained/supporting/noise/missing mechanism summary intended for Run
  Manager guidance revision.
- `query_construction_learning`
  Concrete guidance for constructing the next-pass query from full-text
  learning, including which claim-shaped term combinations to retain, rescue,
  demote, or exclude.
- `abstract_rescue_learning`
  Concrete guidance for first-pass permissiveness and rescue-review behavior in
  the next pass.
- `pdf_deferral_decision`
  Allowed: `defer_pdfs`, `final_pdf_pass`, `require_user_pdf_now`
- `rationale`
  Brief reason for the feedback decision.

## Notes

Before the final calibrated access pass, `pdf_deferral_decision` should usually be `defer_pdfs`.
The first PMC-feedback pass must use `defer_pdfs` unless the run explicitly uses `require_fulltext_completion`.
`final_pdf_pass` is valid only after the learned query/review/import/full-text cycle has run again and at least `min_big_workflow_loops` feedback rows exist.
Use `require_user_pdf_now` only when the run explicitly requires complete full-text access or a small number of high-value papers cannot be judged from PMC.

PMC feedback must distinguish in-scope query learning from broader synthesis
learning. Adjacent mechanisms, pathways, dependencies, phenotypes, or contexts
that were not part of the declared mechanism classes should remain in
`supporting_mechanisms` or reviewer notes, not `missing_keyword_families` or
`recommended_query_changes`, unless a run-guidance revision explicitly promotes
them to primary retrieval scope.

Feedback terms must remain claim-shaped. Do not promote isolated single words
mined from prose into `direct_mechanisms`, `retained_keyword_families`, or
`missing_keyword_families` unless the run contract declared that exact word as
an atomic scope anchor. Prefer multi-word mechanism/evidence phrases and
sentence- or section-local entity-mechanism-outcome evidence.
