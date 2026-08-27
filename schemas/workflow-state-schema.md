# Workflow State Schema

This JSON artifact records the controller's latest whole-run status.
It is written to `artifacts/workflow_control/workflow_state.json`.

## Fields

- `run_id`
- `status`
  Allowed: `initialized`, `running`, `loop_required`, `awaiting_pdf_shortlist`, `complete`, `blocked`
- `access_phase`
  Allowed: `pmc_learning`, `final_access`
- `completion_signal`
  Empty until completion. Use `pdf_download_shortlist_ready` when the final-loop PDF shortlist exists, or `no_pdf_queue` when no PDF fallback remains.
- `next_action`
  Short action for the next agent or human.
- `active_loop_count`
  Number of `workflow_loop_decision.csv` rows with `triggered = yes`.
- `completed_big_loop_count`
  Number of completed PMC/full-text learning passes recorded in `pmc_mechanism_feedback.csv`.
- `min_big_workflow_loops`
  Minimum required big passes before final PDF access. Default and minimum: `2`.
- `max_workflow_loops`
  Maximum automatic big passes before the workflow stops blocked or asks for human/parent-agent intervention. Default: `5`.
- `latest_pdf_deferral_decision`
  Latest `pmc_mechanism_feedback.csv` `pdf_deferral_decision`, if present.
- `manual_pdf_queue_count`
- `pdf_download_shortlist_count`
- `pdf_request_count`
- `reason`
  Evidence-grounded explanation of the state.

## Completion Rule

A run is complete only when:

- no controller loop is active
- readable full text has been reviewed
- at least `min_big_workflow_loops` PMC mechanism feedback rows exist
- the latest feedback says `final_pdf_pass`
- and either no manual PDF queue remains, or `pdf_download_shortlist.csv` exists and covers that final queue

For agent-facing default runs, completion does not require the PDFs themselves to be downloaded.
The final PDF shortlist is the access-action completion signal.
