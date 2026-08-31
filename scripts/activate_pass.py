#!/usr/bin/env python3

from __future__ import annotations

import csv
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
    "review_frame.md",
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


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def blank_count(rows: list[dict[str, str]], field: str) -> int:
    return sum(1 for row in rows if not row.get(field, "").strip())


def parse_config(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    config: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line.startswith("- `") or "`:" not in line:
            continue
        try:
            key = line.split("`", 2)[1]
            value = line.split("`:", 1)[1].split("`", 2)[1]
        except IndexError:
            continue
        config[key] = value
    return config


def require_pmc_fulltext_review_gate(previous_pass: Path) -> list[str]:
    config = parse_config(previous_pass / "inputs" / "run_config.md")
    gate_mode = config.get("pmc_fulltext_review_gate_mode", "all_available").strip() or "all_available"
    if gate_mode != "all_available":
        return []

    import_rows = load_csv(previous_pass / "artifacts" / "fulltext_import" / "import_status.csv")
    fulltext_rows = load_csv(previous_pass / "artifacts" / "fulltext_review" / "fulltext_review.csv")
    evidence_rows = load_csv(previous_pass / "artifacts" / "fulltext_review" / "evidence_extraction.csv")

    pmc_available_ids = {
        row.get("paper_id", "").strip()
        for row in import_rows
        if row.get("pmc_access_status", "").strip() == "available"
    }
    unattempted_ids = {
        row.get("paper_id", "").strip()
        for row in import_rows
        if row.get("pmc_access_status", "").strip() == "available"
        and row.get("pmc_parse_status", "").strip() == "not_attempted"
    }
    usable_ids = {
        row.get("paper_id", "").strip()
        for row in import_rows
        if row.get("pmc_access_status", "").strip() == "available"
        and row.get("pmc_parse_status", "").strip() == "usable"
        and row.get("normalized_path", "").strip()
    }
    unusable_not_queued_ids = {
        row.get("paper_id", "").strip()
        for row in import_rows
        if row.get("pmc_access_status", "").strip() == "available"
        and row.get("pmc_parse_status", "").strip() == "unusable"
        and row.get("pdf_needed", "").strip() != "yes"
    }
    reviewed_ids = {
        row.get("paper_id", "").strip()
        for row in fulltext_rows
        if row.get("fulltext_decision", "").strip()
    }
    evidence_ids = {
        row.get("paper_id", "").strip()
        for row in evidence_rows
        if row.get("evidence_tier", "").strip()
    }

    missing_review = sorted(usable_ids - reviewed_ids)
    missing_evidence = sorted(usable_ids - evidence_ids)
    if not (unattempted_ids or unusable_not_queued_ids or missing_review or missing_evidence):
        return []

    return [
        "previous pass fails pmc_fulltext_review_gate_mode=all_available "
        f"(PMC-available={len(pmc_available_ids)}, PMC-unattempted={len(unattempted_ids)}, "
        f"PMC-usable={len(usable_ids)}, fulltext_reviewed={len(reviewed_ids & usable_ids)}, "
        f"evidence_extracted={len(evidence_ids & usable_ids)}, "
        f"unusable_not_queued={len(unusable_not_queued_ids)}; "
        f"unattempted examples={sorted(unattempted_ids)[:5]}, "
        f"unusable-not-queued examples={sorted(unusable_not_queued_ids)[:5]}, "
        f"missing review examples={missing_review[:5]}, "
        f"missing evidence examples={missing_evidence[:5]})"
    ]


def require_previous_pass_ready_for_learned_rerun(run_dir: Path, pass_number: int) -> list[str]:
    if pass_number <= 1:
        return []

    previous_pass = archive_path_for_pass(run_dir, pass_number - 1)
    if not previous_pass.exists():
        return [f"Previous pass does not exist: {previous_pass}"]

    manifest_rows = load_csv(previous_pass / "artifacts" / "metadata_collection" / "paper_manifest.csv")
    abstract_rows = load_csv(previous_pass / "artifacts" / "abstract_review" / "abstract_review.csv")
    abstract2_rows = load_csv(previous_pass / "artifacts" / "abstract_review" / "abstract_review2.csv")
    feedback_rows = load_csv(previous_pass / "artifacts" / "fulltext_review" / "pmc_mechanism_feedback.csv")

    errors: list[str] = []
    if not manifest_rows:
        errors.append("previous pass has no collected paper_manifest rows")
    if len(abstract_rows) != len(manifest_rows) or blank_count(abstract_rows, "review_decision"):
        errors.append("previous pass abstract_review.csv is incomplete")
    if (
        len(abstract2_rows) != len(manifest_rows)
        or blank_count(abstract2_rows, "abstract_reviewer2_decision")
        or blank_count(abstract2_rows, "promotion_decision")
    ):
        errors.append("previous pass abstract_review2.csv is incomplete")
    errors.extend(require_pmc_fulltext_review_gate(previous_pass))
    if not feedback_rows:
        errors.append("previous pass has no pmc_mechanism_feedback.csv rows")
    else:
        latest_pdf_decision = feedback_rows[-1].get("pdf_deferral_decision", "").strip()
        if latest_pdf_decision != "defer_pdfs":
            errors.append(
                "previous pass latest PMC feedback does not request a learned rerun "
                f"(pdf_deferral_decision={latest_pdf_decision or 'blank'})"
            )
    return errors


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

    readiness_errors = require_previous_pass_ready_for_learned_rerun(run_dir, pass_number)
    if readiness_errors:
        print(f"Refusing to activate pass_{pass_number:03d}: previous pass is not ready for a learned rerun.")
        for error in readiness_errors:
            print(f"- {error}")
        print(
            "Continue the active pass through abstract review, second abstract review, "
            "PMC/full-text import, full-text review, and pmc_mechanism_feedback.csv before activating the next pass."
        )
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
