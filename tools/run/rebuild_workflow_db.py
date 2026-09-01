#!/usr/bin/env python3

from __future__ import annotations

import sys
from pathlib import Path

TOOLS_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS_ROOT / "core"))
from tool_paths import WORKFLOW_ROOT, ensure_tool_paths
ensure_tool_paths()

import sys
from pathlib import Path

from pass_archive import archive_path_for_pass, pass_numbers
from workflow_db import (
    record_abstract_triage_decisions,
    record_collected_papers,
    record_fulltext_read_state,
)

RUNS_DIR = WORKFLOW_ROOT / "runs"


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python3 tools/run/rebuild_workflow_db.py <run_id>")
        return 1

    run_id = sys.argv[1].strip()
    run_dir = RUNS_DIR / run_id
    if not run_dir.exists():
        print(f"Run does not exist: {run_dir}")
        return 1

    collected_passes = 0
    decision_passes = 0
    fulltext_passes = 0
    for pass_number in pass_numbers(run_dir):
        pass_dir = archive_path_for_pass(run_dir, pass_number)
        manifest_path = pass_dir / "artifacts" / "metadata_collection" / "paper_manifest.csv"
        second_pass_path = pass_dir / "artifacts" / "abstract_triage" / "second_pass.csv"
        fulltext_review_path = pass_dir / "artifacts" / "fulltext_review" / "fulltext_review.csv"
        evidence_path = pass_dir / "artifacts" / "fulltext_review" / "evidence_extraction.csv"
        if manifest_path.exists():
            record_collected_papers(run_dir, pass_number, manifest_path)
            collected_passes += 1
        if second_pass_path.exists():
            record_abstract_triage_decisions(run_dir, pass_number, second_pass_path)
            decision_passes += 1
        if fulltext_review_path.exists() and evidence_path.exists():
            record_fulltext_read_state(run_dir, pass_number, fulltext_review_path, evidence_path)
            fulltext_passes += 1

    print(
        f"Rebuilt workflow_state.sqlite from {collected_passes} manifest pass(es) "
        f"{decision_passes} abstract-triage pass(es), and {fulltext_passes} full-text review pass(es)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
