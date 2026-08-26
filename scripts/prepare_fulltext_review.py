#!/usr/bin/env python3

from __future__ import annotations

import csv
import sys
from pathlib import Path


WORKFLOW_ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = WORKFLOW_ROOT / "runs"

FULLTEXT_FIELDS = [
    "paper_id",
    "pmid",
    "pmcid",
    "doi",
    "title",
    "normalized_source_type",
    "normalized_path",
    "fulltext_decision",
    "fulltext_rationale",
    "mechanistic_relevance",
    "objective_relevance",
    "topic_centrality",
    "review_confidence",
]


def infer_source_type(path_text: str) -> str:
    if "PMC_XML" in path_text:
        return "pmc_xml"
    if "PDF" in path_text or "grobid" in path_text:
        return "pdf_grobid"
    return "missing"


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python3 scripts/prepare_fulltext_review.py <run_id>")
        return 1

    run_id = sys.argv[1].strip()
    run_dir = RUNS_DIR / run_id
    import_path = run_dir / "artifacts" / "fulltext_import" / "import_status.csv"
    fulltext_path = run_dir / "artifacts" / "fulltext_review" / "fulltext_review.csv"

    if not import_path.exists():
        print(f"Import status not found: {import_path}")
        return 1

    import_rows = list(csv.DictReader(import_path.open(encoding="utf-8")))
    existing_rows: dict[str, dict[str, str]] = {}
    if fulltext_path.exists():
        existing_rows = {
            row.get("paper_id", ""): row
            for row in csv.DictReader(fulltext_path.open(encoding="utf-8"))
            if row.get("paper_id", "")
        }

    review_rows: list[dict[str, str]] = []
    for row in import_rows:
        normalized_path = row.get("normalized_path", "") or ""
        if not normalized_path:
            continue
        paper_id = row.get("paper_id", "")
        existing_row = existing_rows.get(paper_id, {})
        review_rows.append(
            {
                "paper_id": paper_id,
                "pmid": row.get("pmid", ""),
                "pmcid": row.get("pmcid", ""),
                "doi": row.get("doi", ""),
                "title": row.get("title", ""),
                "normalized_source_type": infer_source_type(normalized_path),
                "normalized_path": normalized_path,
                "fulltext_decision": existing_row.get("fulltext_decision", ""),
                "fulltext_rationale": existing_row.get("fulltext_rationale", ""),
                "mechanistic_relevance": existing_row.get("mechanistic_relevance", ""),
                "objective_relevance": existing_row.get("objective_relevance", ""),
                "topic_centrality": existing_row.get("topic_centrality", ""),
                "review_confidence": existing_row.get("review_confidence", ""),
            }
        )

    with fulltext_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FULLTEXT_FIELDS)
        writer.writeheader()
        writer.writerows(review_rows)

    print(f"Prepared full-text review table with {len(review_rows)} rows at {fulltext_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
