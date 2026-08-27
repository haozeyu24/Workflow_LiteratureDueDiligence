#!/usr/bin/env python3

from __future__ import annotations

import csv
import re
import subprocess
import sys
from pathlib import Path

from pass_archive import active_artifacts_dir, load_all_pass_csv, run_input_path


WORKFLOW_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = WORKFLOW_ROOT / "scripts"


def run_step(args: list[str]) -> None:
    subprocess.run(args, check=True, cwd=str(WORKFLOW_ROOT))


def parse_config(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    config: dict[str, str] = {}
    pattern = re.compile(r"-\s+`([^`]+)`:\s+`([^`]+)`")
    for line in path.read_text(encoding="utf-8").splitlines():
        match = pattern.match(line.strip())
        if match:
            config[match.group(1)] = match.group(2)
    return config


def manual_pdf_allowed(run_id: str) -> bool:
    run_dir = WORKFLOW_ROOT / "runs" / run_id
    config = parse_config(run_input_path(run_dir, "run_config.md"))
    if config.get("access_phase", "pmc_learning") == "final_access" or config.get("pdf_policy") == "require_fulltext_completion":
        return True
    shortlist_path = active_artifacts_dir(run_dir) / "fulltext_import" / "pdf_download_shortlist.csv"
    if not shortlist_path.exists():
        return False
    feedback_rows = load_all_pass_csv(run_dir, "artifacts/fulltext_review/pmc_mechanism_feedback.csv")
    latest_decision = feedback_rows[-1].get("pdf_deferral_decision", "").strip() if feedback_rows else ""
    return latest_decision == "final_pdf_pass"


def pending_fulltext_review_count(run_id: str) -> int:
    run_dir = WORKFLOW_ROOT / "runs" / run_id
    review_path = active_artifacts_dir(run_dir) / "fulltext_review" / "fulltext_review.csv"
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

    if not manual_pdf_allowed(run_id):
        print(
            "Manual PDF ingest is deferred during access_phase=pmc_learning. "
            "Read PMC-normalized full text and write pmc_mechanism_feedback.csv first, "
            "then build pdf_download_shortlist.csv after final_pdf_pass before ingesting PDFs."
        )
        return 1

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
