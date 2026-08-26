# Reporter

## Purpose

Convert workflow state into user-facing progress and final outputs.

## Responsibilities

- summarize stage counts
- report import bottlenecks
- surface PDF intervention checkpoints when applicable
- point the user to manual PDF needs
- emit the final reading list
- keep abstract-relevant but full-text-unavailable papers visible in final outputs
- follow workflow-required reporting fields and statuses

## Outputs

- `progress_report.md`
- `intervention_prompt.md` when PDF fallback requires a decision
- `final_reading_list.csv`
