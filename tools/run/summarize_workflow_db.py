#!/usr/bin/env python3

from __future__ import annotations

import sys
from pathlib import Path

TOOLS_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS_ROOT / "core"))
from tool_paths import WORKFLOW_ROOT, ensure_tool_paths
ensure_tool_paths()

import csv
import sqlite3
import sys
from pathlib import Path

from pass_archive import archive_path_for_pass, current_pass_number
from workflow_db import db_path

RUNS_DIR = WORKFLOW_ROOT / "runs"


def count_csv_rows(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open(encoding="utf-8") as handle:
        return sum(1 for _row in csv.DictReader(handle))


def scalar(connection: sqlite3.Connection, query: str, params: tuple[object, ...] = ()) -> int:
    row = connection.execute(query, params).fetchone()
    return int(row[0] if row else 0)


def grouped_counts(connection: sqlite3.Connection, query: str) -> list[tuple[str, int]]:
    return [(str(row[0]), int(row[1])) for row in connection.execute(query).fetchall()]


def main() -> int:
    if len(sys.argv) not in {2, 3}:
        print("Usage: python3 tools/run/summarize_workflow_db.py <run_id> [pass_number]")
        return 1

    run_id = sys.argv[1].strip()
    run_dir = RUNS_DIR / run_id
    if not run_dir.exists():
        print(f"Run does not exist: {run_dir}")
        return 1

    pass_number = int(sys.argv[2]) if len(sys.argv) == 3 else current_pass_number(run_dir)
    pass_dir = archive_path_for_pass(run_dir, pass_number)
    manifest_path = pass_dir / "artifacts" / "metadata_collection" / "paper_manifest.csv"
    first_pass_path = pass_dir / "artifacts" / "abstract_triage" / "first_pass.csv"
    second_pass_path = pass_dir / "artifacts" / "abstract_triage" / "second_pass.csv"
    records_dir = pass_dir / "artifacts" / "metadata_collection" / "records"

    manifest_count = count_csv_rows(manifest_path)
    first_pass_count = count_csv_rows(first_pass_path)
    second_pass_count = count_csv_rows(second_pass_path)
    json_mirror_count = (
        sum(1 for _path in records_dir.glob("*.json")) if records_dir.exists() else 0
    )

    database_path = db_path(run_dir)
    if not database_path.exists():
        print(f"Database not found: {database_path}")
        return 1

    with sqlite3.connect(f"file:{database_path}?mode=ro", uri=True) as connection:
        pubmed_record_count = scalar(
            connection,
            "SELECT COUNT(*) FROM pubmed_records WHERE pass_number = ?",
            (pass_number,),
        )
        active_decision_count = scalar(
            connection,
            """
            SELECT COUNT(*)
            FROM pass_decisions
            WHERE pass_number = ?
              AND status != 'superseded'
            """,
            (pass_number,),
        )
        status_counts = grouped_counts(
            connection,
            "SELECT latest_status, COUNT(*) FROM papers GROUP BY latest_status ORDER BY latest_status",
        )
        decision_counts = grouped_counts(
            connection,
            "SELECT status, COUNT(*) FROM pass_decisions GROUP BY status ORDER BY status",
        )

    print(f"Run: {run_id}")
    print(f"Pass: pass_{pass_number:03d}")
    print(f"Manifest rows: {manifest_count}")
    print(f"First-pass triage rows: {first_pass_count}")
    print(f"Second-pass triage rows: {second_pass_count}")
    print(f"SQLite PubMed record rows for pass: {pubmed_record_count}")
    print(f"JSON metadata mirror files: {json_mirror_count}")
    print(f"Active SQLite abstract decisions for pass: {active_decision_count}")
    print("Paper status counts:")
    for status, count in status_counts:
        print(f"  {status}: {count}")
    print("Pass decision status counts:")
    for status, count in decision_counts:
        print(f"  {status}: {count}")

    warnings = []
    if pubmed_record_count < manifest_count:
        warnings.append("SQLite PubMed record count is lower than manifest count.")
    if active_decision_count and active_decision_count != second_pass_count:
        warnings.append("Active SQLite decision count does not match second-pass triage rows.")
    if json_mirror_count:
        warnings.append("JSON metadata mirrors still exist; run compact_metadata_records.py if desired.")
    if warnings:
        print("Warnings:")
        for warning in warnings:
            print(f"  - {warning}")
        return 1

    print("Database summary checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
