# Run Config

- `interaction_mode`: `agent_facing`
- `pdf_policy`: `continue_pmc_only`

## Allowed values

- `interaction_mode`
  - `human_facing`
  - `agent_facing`
- `pdf_policy`
  - `pause_for_user`
  - `continue_pmc_only`
  - `require_fulltext_completion`

## Notes

- `human_facing` usually pairs with `pause_for_user`
- `agent_facing` usually pairs with `continue_pmc_only`
- when a human chooses to provide PDFs, the pipeline should use the same import path whether the user provides a few PDFs or many PDFs
