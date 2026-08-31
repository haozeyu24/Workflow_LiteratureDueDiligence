#!/usr/bin/env python3

from __future__ import annotations

import csv
import json
import shutil
import time
from pathlib import Path


PHASE1_DIR_NAME = "Phase1_PubmedCollection"
ARCHIVE_DIR_NAME = "passes"
ACTIVE_PASS_FILE = "active_pass.json"
INCOMPLETE_SENTINEL = "WORKFLOW_NOT_COMPLETE"

INPUT_PATHS = [
    "request.md",
    "run_config.md",
    "instruction.md",
    "topic.md",
    "review_frame.md",
    "constraints.md",
    "notes.md",
]

PASS_ARTIFACT_SUBDIRS = [
    "artifacts/search_strategy",
    "artifacts/metadata_collection",
    "artifacts/abstract_review",
    "artifacts/fulltext_import",
    "artifacts/fulltext_review",
    "artifacts/workflow_control",
    "reports",
]


def phase1_dir(run_dir: Path) -> Path:
    return run_dir / PHASE1_DIR_NAME


def passes_dir(run_dir: Path) -> Path:
    return phase1_dir(run_dir) / ARCHIVE_DIR_NAME


def incomplete_sentinel_path(run_dir: Path) -> Path:
    return phase1_dir(run_dir) / INCOMPLETE_SENTINEL


def phase1_transcript_path(run_dir: Path) -> Path:
    return passes_dir(run_dir) / "phase1_transcript.md"


def archive_path_for_pass(run_dir: Path, pass_number: int) -> Path:
    return passes_dir(run_dir) / f"pass_{pass_number:03d}"


def ensure_pass_layout(run_dir: Path, pass_number: int) -> Path:
    pass_dir = archive_path_for_pass(run_dir, pass_number)
    (pass_dir / "inputs").mkdir(parents=True, exist_ok=True)
    for relative in PASS_ARTIFACT_SUBDIRS:
        (pass_dir / relative).mkdir(parents=True, exist_ok=True)
    return pass_dir


def activate_pass(run_dir: Path, pass_number: int) -> Path:
    pass_dir = ensure_pass_layout(run_dir, pass_number)
    passes_dir(run_dir).mkdir(parents=True, exist_ok=True)
    (passes_dir(run_dir) / ACTIVE_PASS_FILE).write_text(
        json.dumps(
            {
                "active_pass": f"pass_{pass_number:03d}",
                "pass_number": pass_number,
                "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return pass_dir


def active_pass_number(run_dir: Path) -> int | None:
    state_path = passes_dir(run_dir) / ACTIVE_PASS_FILE
    if state_path.exists():
        try:
            payload = json.loads(state_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
        value = payload.get("pass_number")
        if isinstance(value, int) and value > 0:
            return value

    return None


def active_pass_dir(run_dir: Path) -> Path:
    number = current_pass_number(run_dir)
    return ensure_pass_layout(run_dir, number)


def active_artifacts_dir(run_dir: Path) -> Path:
    return active_pass_dir(run_dir) / "artifacts"


def active_reports_dir(run_dir: Path) -> Path:
    return active_pass_dir(run_dir) / "reports"


def active_path(run_dir: Path, relative_path: str) -> Path:
    return active_pass_dir(run_dir) / relative_path


def pass_numbers(run_dir: Path) -> list[int]:
    archive_root = passes_dir(run_dir)
    existing: list[int] = []
    if archive_root.exists():
        for path in archive_root.glob("pass_[0-9][0-9][0-9]"):
            suffix = path.name.split("_", 1)[1]
            if path.is_dir() and suffix.isdigit():
                existing.append(int(suffix))
    return sorted(existing)


def load_pass_csv(run_dir: Path, pass_number: int, relative_path: str) -> list[dict[str, str]]:
    return load_csv(archive_path_for_pass(run_dir, pass_number) / relative_path)


def load_all_pass_csv(run_dir: Path, relative_path: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for number in pass_numbers(run_dir):
        rows.extend(load_pass_csv(run_dir, number, relative_path))
    if rows:
        return rows
    return load_csv(active_path(run_dir, relative_path))


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def has_nonempty_csv(path: Path) -> bool:
    return bool(load_csv(path))


def completed_big_loop_count(run_dir: Path) -> int:
    return len(load_all_pass_csv(run_dir, "artifacts/fulltext_review/pmc_mechanism_feedback.csv"))


def latest_feedback_row(run_dir: Path) -> dict[str, str]:
    rows = load_all_pass_csv(run_dir, "artifacts/fulltext_review/pmc_mechanism_feedback.csv")
    return rows[-1] if rows else {}


def latest_guidance_revision_for_feedback(run_dir: Path, feedback_loop_id: str) -> dict[str, str]:
    rows = [
        row for row in load_all_pass_csv(
            run_dir,
            "artifacts/workflow_control/run_guidance_revision_log.csv",
        )
        if row.get("feedback_loop_id", "").strip() == feedback_loop_id
    ]
    return rows[-1] if rows else {}


def resolve_run_path(run_dir: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return run_dir / path


def current_pass_number(run_dir: Path) -> int:
    return active_pass_number(run_dir) or infer_current_pass_number(run_dir)


def current_input_dir(run_dir: Path) -> Path:
    return archive_path_for_pass(run_dir, current_pass_number(run_dir)) / "inputs"


def run_input_path(run_dir: Path, filename: str) -> Path:
    if filename == "original_user_prompt.md":
        return run_dir / filename
    path = current_input_dir(run_dir) / filename
    if path.exists():
        return path
    return archive_path_for_pass(run_dir, 1) / "inputs" / filename


def learned_revision_path(run_dir: Path, field: str) -> Path | None:
    latest = latest_feedback_row(run_dir)
    if latest.get("pdf_deferral_decision", "").strip() != "defer_pdfs":
        return None
    revision = latest_guidance_revision_for_feedback(run_dir, latest.get("loop_id", "").strip())
    value = revision.get(field, "").strip()
    if not value:
        return None
    return resolve_run_path(run_dir, value)


def canonical_has_run_data(run_dir: Path) -> bool:
    artifacts_dir = active_artifacts_dir(run_dir)
    checks = [
        artifacts_dir / "metadata_collection" / "paper_manifest.csv",
        artifacts_dir / "abstract_review" / "abstract_review.csv",
        artifacts_dir / "abstract_review" / "abstract_review2.csv",
        artifacts_dir / "fulltext_import" / "import_status.csv",
        artifacts_dir / "fulltext_review" / "fulltext_review.csv",
    ]
    return any(has_nonempty_csv(path) for path in checks)


def infer_current_pass_number(run_dir: Path) -> int:
    active = active_pass_number(run_dir)
    if active:
        return active
    existing = pass_numbers(run_dir)
    return max(existing) if existing else 1


def copy_canonical_paths(run_dir: Path, target_dir: Path) -> None:
    inputs_dir = target_dir / "inputs"
    for relative in INPUT_PATHS:
        source = run_input_path(run_dir, relative)
        if not source.exists():
            continue
        target = inputs_dir / Path(relative).name
        if target.exists():
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)

    original_prompt = run_dir / "original_user_prompt.md"
    if original_prompt.exists():
        target = inputs_dir / "original_user_prompt.md"
        if not target.exists():
            shutil.copy2(original_prompt, target)

    for source, relative in (
        (active_artifacts_dir(run_dir), "artifacts"),
        (active_reports_dir(run_dir), "reports"),
    ):
        if not source.exists():
            continue
        target = target_dir / relative
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(source, target, ignore=shutil.ignore_patterns(ARCHIVE_DIR_NAME))


def write_snapshot_manifest(run_dir: Path, target_dir: Path, pass_number: int, reason: str) -> None:
    artifacts_dir = active_artifacts_dir(run_dir)
    feedback_rows = load_csv(artifacts_dir / "fulltext_review" / "pmc_mechanism_feedback.csv")
    manifest_rows = load_csv(artifacts_dir / "metadata_collection" / "paper_manifest.csv")
    abstract2_rows = load_csv(artifacts_dir / "abstract_review" / "abstract_review2.csv")
    import_rows = load_csv(artifacts_dir / "fulltext_import" / "import_status.csv")
    fulltext_rows = load_csv(artifacts_dir / "fulltext_review" / "fulltext_review.csv")
    queue_rows = load_csv(artifacts_dir / "fulltext_import" / "manual_pdf_queue.csv")
    latest = feedback_rows[-1] if feedback_rows else {}

    payload = {
        "pass_number": pass_number,
        "snapshot_reason": reason,
        "snapshot_created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "completed_big_loop_count_at_snapshot": len(feedback_rows),
        "latest_feedback_loop_id": latest.get("loop_id", ""),
        "latest_pdf_deferral_decision": latest.get("pdf_deferral_decision", ""),
        "paper_manifest_rows": len(manifest_rows),
        "abstractReviewer2_advance_to_import": sum(
            row.get("promotion_decision", "") == "advance_to_import" for row in abstract2_rows
        ),
        "import_status_rows": len(import_rows),
        "fulltext_review_rows": len(fulltext_rows),
        "fulltext_keep_count": sum(row.get("fulltext_decision", "") == "keep" for row in fulltext_rows),
        "manual_pdf_queue_rows": len(queue_rows),
    }
    target_dir.mkdir(parents=True, exist_ok=True)
    (target_dir / "snapshot_manifest.json").write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )


def snapshot_current_pass(run_dir: Path, reason: str) -> Path | None:
    if not canonical_has_run_data(run_dir):
        return None

    pass_number = current_pass_number(run_dir)
    target_dir = archive_path_for_pass(run_dir, pass_number)
    write_snapshot_manifest(run_dir, target_dir, pass_number, reason)
    return target_dir
