# PDF Intervention Schema

## Fields

- `status`
  Allowed: `not_needed`, `paused_for_user`, `continue_without_pdf`, `awaiting_pdf`, `complete`
- `interaction_mode`
  Allowed: `human_facing`, `agent_facing`
- `pdf_policy`
  Allowed: `pause_for_user`, `continue_pmc_only`, `require_fulltext_completion`
- `pmc_ready_count`
- `pdf_queue_count`
- `recommended_action`
- `allowed_actions`
- `manual_pdf_queue_path`
- `resume_target`
- `notes`

## Notes

This artifact is the portable checkpoint for PDF fallback decisions.
Chat-based harnesses may render it as a pause-and-prompt message.
Richer UIs may render it as a modal or action box.
If the user chooses to provide PDFs, the workflow should use one unified continuation path rather than separate "all PDF" and "partial PDF" branches.
