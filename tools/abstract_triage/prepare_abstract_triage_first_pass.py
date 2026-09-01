#!/usr/bin/env python3

from __future__ import annotations

import sys
from pathlib import Path

TOOLS_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS_ROOT / "core"))
from tool_paths import WORKFLOW_ROOT, ensure_tool_paths
ensure_tool_paths()

import csv
import sys
from pathlib import Path

from pass_archive import active_artifacts_dir

RUNS_DIR = WORKFLOW_ROOT / "runs"

ABSTRACT_TRIAGE_FIRST_PASS_FIELDS = [
    "paper_id",
    "pmid",
    "doi",
    "title",
    "abstract",
    "publication_types",
    "year",
    "source_query",
    "first_pass_decision",
    "first_pass_rationale",
    "first_pass_confidence",
    "topic_match_type",
    "triage_actor",
    "synthesis_role",
    "prescreen_hint",
    "prescreen_rationale",
    "prescreen_overlap_terms",
]


def sanitize(value: str) -> str:
    return " ".join((value or "").split())


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python3 tools/abstract_triage/prepare_abstract_triage_first_pass.py <run_id>")
        return 1

    run_id = sys.argv[1].strip()
    run_dir = RUNS_DIR / run_id
    artifacts_dir = active_artifacts_dir(run_dir)
    manifest_path = artifacts_dir / "metadata_collection" / "paper_manifest.csv"
    review_path = artifacts_dir / "abstract_triage" / "first_pass.csv"

    if not manifest_path.exists():
        print(f"Manifest not found: {manifest_path}")
        return 1

    manifest_rows = list(csv.DictReader(manifest_path.open(encoding="utf-8")))
    review_rows: list[dict[str, str]] = []
    for row in manifest_rows:
        review_rows.append(
            {
                "paper_id": sanitize(row.get("paper_id", "")),
                "pmid": sanitize(row.get("pmid", "")),
                "doi": sanitize(row.get("doi", "")),
                "title": sanitize(row.get("title", "")),
                "abstract": sanitize(row.get("abstract", "")),
                "publication_types": sanitize(row.get("publication_types", "")),
                "year": sanitize(row.get("year", "")),
                "source_query": sanitize(row.get("source_query", "")),
                "first_pass_decision": "",
                "first_pass_rationale": "",
                "first_pass_confidence": "",
                "topic_match_type": "",
                "triage_actor": "",
                "synthesis_role": "",
                "prescreen_hint": "",
                "prescreen_rationale": "",
                "prescreen_overlap_terms": "",
            }
        )

    with review_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=ABSTRACT_TRIAGE_FIRST_PASS_FIELDS)
        writer.writeheader()
        writer.writerows(review_rows)

    print(f"Prepared abstract triage first-pass table with {len(review_rows)} rows at {review_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
