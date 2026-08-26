#!/usr/bin/env python3

from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path


WORKFLOW_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = WORKFLOW_ROOT / "scripts"


def run_step(args: list[str]) -> None:
    subprocess.run(args, check=True, cwd=str(WORKFLOW_ROOT))


def pending_fulltext_review_count(run_id: str) -> int:
    review_path = WORKFLOW_ROOT / "runs" / run_id / "artifacts" / "fulltext_review" / "fulltext_review.csv"
    if not review_path.exists():
        return 0

    with review_path.open() as handle:
        rows = csv.DictReader(handle)
        return sum(1 for row in rows if not (row.get("fulltext_decision") or "").strip())


def main() -> int:
    if len(sys.argv) not in {2, 3}:
        print("Usage: python3 scripts/ingest_manual_pdfs.py <run_id> [downloads_dir]")
        return 1

    run_id = sys.argv[1].strip()
    downloads_dir = sys.argv[2] if len(sys.argv) == 3 else str(Path("~/Downloads").expanduser())

    run_step(["python3", str(SCRIPTS_DIR / "stage_manual_pdfs.py"), run_id, downloads_dir])
    run_step(["python3", str(SCRIPTS_DIR / "parse_pdf_fulltext.py"), run_id])
    run_step(["python3", str(SCRIPTS_DIR / "prepare_fulltext_review.py"), run_id])
    run_step(["python3", str(SCRIPTS_DIR / "generate_reports.py"), run_id])

    pending_count = pending_fulltext_review_count(run_id)
    print(f"Completed manual PDF ingest refresh for {run_id}")
    print(f"Pending full-text keep/drop decisions: {pending_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
