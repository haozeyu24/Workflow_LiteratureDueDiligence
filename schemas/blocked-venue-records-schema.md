# Blocked Venue Records Schema

## Fields

- `paper_id`
- `pmid`
- `doi`
- `title`
- `journal`
- `year`
- `source_query`
- `match_type`
- `match_value`
- `block_rationale`

## Notes

This optional artifact records papers filtered out at PubMed collection time by
the reusable workflow venue blocklist. Blocked papers must not enter
`paper_manifest.csv`.
