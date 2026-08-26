#!/usr/bin/env python3

from __future__ import annotations

import csv
import sys
from pathlib import Path


WORKFLOW_ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = WORKFLOW_ROOT / "runs"

ABSTRACT_REVIEW2_FIELDS = [
    "paper_id",
    "pmid",
    "doi",
    "title",
    "abstract",
    "year",
    "source_query",
    "abstract_reviewer_decision",
    "abstract_reviewer_rationale",
    "abstract_reviewer2_decision",
    "abstract_reviewer2_rationale",
    "abstract_reviewer2_confidence",
    "promotion_decision",
]


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python3 scripts/prepare_abstract_review2.py <run_id>")
        return 1

    run_id = sys.argv[1].strip()
    run_dir = RUNS_DIR / run_id
    abstract_review_path = run_dir / "artifacts" / "abstract_review" / "abstract_review.csv"
    abstract_review2_path = run_dir / "artifacts" / "abstract_review" / "abstract_review2.csv"

    if not abstract_review_path.exists():
        print(f"Abstract review table not found: {abstract_review_path}")
        return 1

    abstract_rows = list(csv.DictReader(abstract_review_path.open(encoding="utf-8")))
    existing_rows: dict[str, dict[str, str]] = {}
    if abstract_review2_path.exists():
        existing_rows = {
            row.get("paper_id", ""): row
            for row in csv.DictReader(abstract_review2_path.open(encoding="utf-8"))
            if row.get("paper_id", "")
        }

    abstract_review2_rows: list[dict[str, str]] = []
    for row in abstract_rows:
        existing_row = existing_rows.get(row.get("paper_id", ""), {})
        abstract_review2_rows.append(
            {
                "paper_id": row.get("paper_id", ""),
                "pmid": row.get("pmid", ""),
                "doi": row.get("doi", ""),
                "title": row.get("title", ""),
                "abstract": row.get("abstract", ""),
                "year": row.get("year", ""),
                "source_query": row.get("source_query", ""),
                "abstract_reviewer_decision": row.get("review_decision", ""),
                "abstract_reviewer_rationale": row.get("review_rationale", ""),
                "abstract_reviewer2_decision": existing_row.get("abstract_reviewer2_decision", ""),
                "abstract_reviewer2_rationale": existing_row.get("abstract_reviewer2_rationale", ""),
                "abstract_reviewer2_confidence": existing_row.get("abstract_reviewer2_confidence", ""),
                "promotion_decision": existing_row.get("promotion_decision", ""),
            }
        )

    with abstract_review2_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=ABSTRACT_REVIEW2_FIELDS)
        writer.writeheader()
        writer.writerows(abstract_review2_rows)

    print(
        f"Prepared abstractReviewer2 table with {len(abstract_review2_rows)} rows "
        f"at {abstract_review2_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
