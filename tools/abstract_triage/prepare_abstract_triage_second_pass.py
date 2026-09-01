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

ABSTRACT_TRIAGE_SECOND_PASS_FIELDS = [
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
    "second_pass_decision",
    "second_pass_rationale",
    "second_pass_confidence",
    "promotion_decision",
    "synthesis_role",
]


def sanitize(value: str) -> str:
    return " ".join((value or "").split())


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python3 tools/abstract_triage/prepare_abstract_triage_second_pass.py <run_id>")
        return 1

    run_id = sys.argv[1].strip()
    run_dir = RUNS_DIR / run_id
    artifacts_dir = active_artifacts_dir(run_dir)
    abstract_triage_path = artifacts_dir / "abstract_triage" / "first_pass.csv"
    second_pass_path = artifacts_dir / "abstract_triage" / "second_pass.csv"

    if not abstract_triage_path.exists():
        print(f"Abstract triage first-pass table not found: {abstract_triage_path}")
        return 1

    abstract_rows = list(csv.DictReader(abstract_triage_path.open(encoding="utf-8")))
    existing_rows: dict[str, dict[str, str]] = {}
    if second_pass_path.exists():
        existing_rows = {
            row.get("paper_id", ""): row
            for row in csv.DictReader(second_pass_path.open(encoding="utf-8"))
            if row.get("paper_id", "")
        }

    second_pass_rows: list[dict[str, str]] = []
    for row in abstract_rows:
        existing_row = existing_rows.get(row.get("paper_id", ""), {})
        second_pass_rows.append(
            {
                "paper_id": sanitize(row.get("paper_id", "")),
                "pmid": sanitize(row.get("pmid", "")),
                "doi": sanitize(row.get("doi", "")),
                "title": sanitize(row.get("title", "")),
                "abstract": sanitize(row.get("abstract", "")),
                "publication_types": sanitize(row.get("publication_types", "")),
                "year": sanitize(row.get("year", "")),
                "source_query": sanitize(row.get("source_query", "")),
                "first_pass_decision": sanitize(row.get("first_pass_decision", "")),
                "first_pass_rationale": sanitize(row.get("first_pass_rationale", "")),
                "second_pass_decision": sanitize(existing_row.get("second_pass_decision", "")),
                "second_pass_rationale": sanitize(existing_row.get("second_pass_rationale", "")),
                "second_pass_confidence": sanitize(existing_row.get("second_pass_confidence", "")),
                "promotion_decision": sanitize(existing_row.get("promotion_decision", "")),
                "synthesis_role": sanitize(existing_row.get("synthesis_role", row.get("synthesis_role", ""))),
            }
        )

    with second_pass_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=ABSTRACT_TRIAGE_SECOND_PASS_FIELDS,
            quoting=csv.QUOTE_ALL,
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(second_pass_rows)

    print(
        f"Prepared abstract triage second pass table with {len(second_pass_rows)} rows "
        f"at {second_pass_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
