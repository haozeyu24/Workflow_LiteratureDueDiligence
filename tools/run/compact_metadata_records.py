#!/usr/bin/env python3

from __future__ import annotations

import sys
from pathlib import Path

TOOLS_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS_ROOT / "core"))
from tool_paths import WORKFLOW_ROOT, ensure_tool_paths
ensure_tool_paths()

import csv
import json
import sys
from pathlib import Path

from pass_archive import archive_path_for_pass, current_pass_number, pass_numbers
from workflow_db import connect, record_pubmed_payloads, record_uri

RUNS_DIR = WORKFLOW_ROOT / "runs"


def load_json_record(path: Path) -> dict[str, object] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def load_manifest(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists():
        return [], []
    with path.open(encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return reader.fieldnames or [], list(reader)


def write_manifest(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    if not fieldnames:
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def db_record_count(run_dir: Path, pass_number: int) -> int:
    with connect(run_dir) as connection:
        row = connection.execute(
            "SELECT COUNT(*) AS count FROM pubmed_records WHERE pass_number = ?",
            (pass_number,),
        ).fetchone()
    return int(row["count"] if row else 0)


def compact_pass(run_dir: Path, pass_number: int) -> tuple[int, int, int]:
    pass_dir = archive_path_for_pass(run_dir, pass_number)
    manifest_path = pass_dir / "artifacts" / "metadata_collection" / "paper_manifest.csv"
    records_dir = pass_dir / "artifacts" / "metadata_collection" / "records"
    fieldnames, manifest_rows = load_manifest(manifest_path)
    if not manifest_rows:
        return 0, 0, 0

    records: list[dict[str, object]] = []
    original_paths: dict[str, str] = {}
    missing_files = 0
    for row in manifest_rows:
        paper_id = (row.get("paper_id") or "").strip()
        if not paper_id:
            continue
        record_path = records_dir / f"{paper_id}.json"
        payload = load_json_record(record_path)
        if payload is None:
            missing_files += 1
            continue
        records.append(payload)
        original_paths[paper_id] = str(record_path.relative_to(run_dir))

    if records:
        record_pubmed_payloads(run_dir, pass_number, records, original_paths)

    expected_count = len(manifest_rows)
    actual_count = db_record_count(run_dir, pass_number)
    if actual_count < expected_count:
        print(
            f"Refusing to remove JSON mirrors for pass_{pass_number:03d}: "
            f"SQLite has {actual_count} records but manifest has {expected_count}."
        )
        return len(records), 0, missing_files

    for row in manifest_rows:
        paper_id = (row.get("paper_id") or "").strip()
        if paper_id:
            row["record_path"] = record_uri(pass_number, paper_id)
    write_manifest(manifest_path, fieldnames, manifest_rows)

    removed = 0
    if records_dir.exists():
        for path in records_dir.glob("*.json"):
            path.unlink()
            removed += 1

    return len(records), removed, missing_files


def main() -> int:
    if len(sys.argv) not in {2, 3} or (len(sys.argv) == 3 and sys.argv[2] != "--all-passes"):
        print("Usage: python3 tools/run/compact_metadata_records.py <run_id> [--all-passes]")
        return 1

    run_id = sys.argv[1].strip()
    run_dir = RUNS_DIR / run_id
    if not run_dir.exists():
        print(f"Run does not exist: {run_dir}")
        return 1

    if len(sys.argv) == 3:
        target_passes = pass_numbers(run_dir)
    else:
        target_passes = [current_pass_number(run_dir)]

    total_ingested = 0
    total_removed = 0
    total_missing = 0
    for pass_number in target_passes:
        ingested, removed, missing = compact_pass(run_dir, pass_number)
        total_ingested += ingested
        total_removed += removed
        total_missing += missing
        print(
            f"pass_{pass_number:03d}: ingested={ingested}, removed_json_files={removed}, "
            f"missing_or_unreadable_json={missing}"
        )

    print(
        f"Compaction complete: ingested={total_ingested}, removed_json_files={total_removed}, "
        f"missing_or_unreadable_json={total_missing}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
