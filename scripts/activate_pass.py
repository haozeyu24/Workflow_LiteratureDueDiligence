#!/usr/bin/env python3

from __future__ import annotations

import shutil
import sys
from pathlib import Path

from pass_archive import activate_pass, archive_path_for_pass, ensure_pass_layout


WORKFLOW_ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = WORKFLOW_ROOT / "runs"
TEMPLATES_DIR = WORKFLOW_ROOT / "templates"

INPUT_NAMES = [
    "request.md",
    "run_config.md",
    "instruction.md",
    "topic.md",
    "constraints.md",
    "notes.md",
]

ARTIFACT_TEMPLATES = [
    ("search_strategy_template.md", "artifacts/search_strategy/search_strategy.md"),
    ("query_refinement_report_template.md", "artifacts/search_strategy/query_refinement_report.md"),
    ("query_diagnostics_template.csv", "artifacts/search_strategy/query_diagnostics.csv"),
    ("paper_manifest_template.csv", "artifacts/metadata_collection/paper_manifest.csv"),
    ("abstract_review_template.csv", "artifacts/abstract_review/abstract_review.csv"),
    ("abstract_review2_template.csv", "artifacts/abstract_review/abstract_review2.csv"),
    ("import_status_template.csv", "artifacts/fulltext_import/import_status.csv"),
    ("manual_pdf_queue_template.csv", "artifacts/fulltext_import/manual_pdf_queue.csv"),
    ("fulltext_review_template.csv", "artifacts/fulltext_review/fulltext_review.csv"),
    ("evidence_extraction_template.csv", "artifacts/fulltext_review/evidence_extraction.csv"),
    ("pmc_mechanism_feedback_template.csv", "artifacts/fulltext_review/pmc_mechanism_feedback.csv"),
    ("workflow_loop_decision_template.csv", "artifacts/workflow_control/workflow_loop_decision.csv"),
    ("workflow_state_template.json", "artifacts/workflow_control/workflow_state.json"),
    ("run_guidance_revision_log_template.csv", "artifacts/workflow_control/run_guidance_revision_log.csv"),
    ("final_reading_list_template.csv", "reports/final_reading_list.csv"),
    ("progress_report_template.md", "reports/progress_report.md"),
]


def parse_pass_number(value: str) -> int:
    value = value.strip()
    if value.startswith("pass_"):
        value = value.split("_", 1)[1]
    number = int(value)
    if number < 1:
        raise ValueError("pass number must be >= 1")
    return number


def seed_inputs_from_previous_pass(run_dir: Path, pass_number: int) -> None:
    if pass_number <= 1:
        return
    previous_inputs = archive_path_for_pass(run_dir, pass_number - 1) / "inputs"
    current_inputs = archive_path_for_pass(run_dir, pass_number) / "inputs"
    if not previous_inputs.exists():
        return
    for name in INPUT_NAMES:
        source = previous_inputs / name
        target = current_inputs / name
        if source.exists() and not target.exists():
            shutil.copy2(source, target)


def seed_artifact_templates(pass_dir: Path) -> None:
    for template_name, relative_target in ARTIFACT_TEMPLATES:
        source = TEMPLATES_DIR / template_name
        target = pass_dir / relative_target
        if source.exists() and not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: python3 scripts/activate_pass.py <run_id> <pass_number>")
        return 1

    run_id = sys.argv[1].strip()
    try:
        pass_number = parse_pass_number(sys.argv[2])
    except ValueError as error:
        print(f"Invalid pass number: {error}")
        return 1

    run_dir = RUNS_DIR / run_id
    if not run_dir.exists():
        print(f"Run does not exist: {run_dir}")
        return 1

    pass_dir = ensure_pass_layout(run_dir, pass_number)
    seed_inputs_from_previous_pass(run_dir, pass_number)
    seed_artifact_templates(pass_dir)
    activate_pass(run_dir, pass_number)
    print(f"Activated {pass_dir}")
    print("Active artifacts and reports are stored inside this pass directory.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
