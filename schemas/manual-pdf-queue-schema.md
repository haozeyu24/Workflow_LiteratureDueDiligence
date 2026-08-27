# Manual PDF Queue Schema

## Fields

- `paper_id`
- `pmid`
- `pmcid`
- `doi`
- `title`
- `queue_reason`
- `preferred_source`
- `notes`

## Notes

This queue tracks papers that may need user-supplied PDF fallback after PMC import is missing or unusable.
During `access_phase = pmc_learning`, the queue is deferred while PMC-readable full text is used to improve the query.
During `access_phase = final_access`, the queue can become an action list for a human or parent agent.
After PMC mechanism feedback says `defer_pdfs`, the queue remains diagnostic input for the next query loop.
After PMC mechanism feedback says `final_pdf_pass`, the queue must be scored into `pdf_download_shortlist.csv` before the workflow asks for downloads or reports completion.
