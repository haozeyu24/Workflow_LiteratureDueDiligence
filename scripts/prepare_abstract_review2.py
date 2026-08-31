#!/usr/bin/env python3

from __future__ import annotations

import csv
import sys
from pathlib import Path

from pass_archive import active_artifacts_dir


WORKFLOW_ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = WORKFLOW_ROOT / "runs"

ABSTRACT_REVIEW2_FIELDS = [
    "paper_id",
    "pmid",
    "doi",
    "title",
    "abstract",
    "publication_types",
    "year",
    "source_query",
    "abstract_reviewer_decision",
    "abstract_reviewer_rationale",
    "abstract_reviewer2_decision",
    "abstract_reviewer2_rationale",
    "abstract_reviewer2_confidence",
    "promotion_decision",
    "review_frame_role",
]


def sanitize(value: str) -> str:
    return " ".join((value or "").split())


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python3 scripts/prepare_abstract_review2.py <run_id>")
        return 1

    run_id = sys.argv[1].strip()
    run_dir = RUNS_DIR / run_id
    artifacts_dir = active_artifacts_dir(run_dir)
    abstract_review_path = artifacts_dir / "abstract_review" / "abstract_review.csv"
    abstract_review2_path = artifacts_dir / "abstract_review" / "abstract_review2.csv"

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
                "paper_id": sanitize(row.get("paper_id", "")),
                "pmid": sanitize(row.get("pmid", "")),
                "doi": sanitize(row.get("doi", "")),
                "title": sanitize(row.get("title", "")),
                "abstract": sanitize(row.get("abstract", "")),
                "publication_types": sanitize(row.get("publication_types", "")),
                "year": sanitize(row.get("year", "")),
                "source_query": sanitize(row.get("source_query", "")),
                "abstract_reviewer_decision": sanitize(row.get("review_decision", "")),
                "abstract_reviewer_rationale": sanitize(row.get("review_rationale", "")),
                "abstract_reviewer2_decision": sanitize(existing_row.get("abstract_reviewer2_decision", "")),
                "abstract_reviewer2_rationale": sanitize(existing_row.get("abstract_reviewer2_rationale", "")),
                "abstract_reviewer2_confidence": sanitize(existing_row.get("abstract_reviewer2_confidence", "")),
                "promotion_decision": sanitize(existing_row.get("promotion_decision", "")),
                "review_frame_role": sanitize(existing_row.get("review_frame_role", row.get("review_frame_role", ""))),
            }
        )

    with abstract_review2_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=ABSTRACT_REVIEW2_FIELDS,
            quoting=csv.QUOTE_ALL,
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(abstract_review2_rows)

    print(
        f"Prepared abstractReviewer2 table with {len(abstract_review2_rows)} rows "
        f"at {abstract_review2_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
