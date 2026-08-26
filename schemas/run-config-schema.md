# Run Config Schema

## Fields

- `interaction_mode`
  Allowed: `human_facing`, `agent_facing`
- `pdf_policy`
  Allowed: `pause_for_user`, `continue_pmc_only`, `require_fulltext_completion`

## Notes

This file tells the workflow whether it should pause for user action or continue automatically when PDF fallback is needed.
If the user later provides PDFs, the same downstream import path should be used whether the user provides a subset or the whole queue.
