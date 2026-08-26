#!/usr/bin/env python3

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path


WORKFLOW_ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = WORKFLOW_ROOT / "runs"


def parse_config(path: Path) -> dict[str, str]:
    config: dict[str, str] = {}
    pattern = re.compile(r"-\s+`([^`]+)`:\s+`([^`]+)`")
    for line in path.read_text(encoding="utf-8").splitlines():
        match = pattern.match(line.strip())
        if match:
            config[match.group(1)] = match.group(2)
    return config


def load_csv(path: Path) -> list[dict[str, str]]:
    return list(csv.DictReader(path.open(encoding="utf-8")))


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python3 scripts/build_pdf_intervention.py <run_id>")
        return 1

    run_id = sys.argv[1].strip()
    run_dir = RUNS_DIR / run_id
    config_path = run_dir / "run_config.md"
    import_path = run_dir / "artifacts" / "fulltext_import" / "import_status.csv"
    queue_path = run_dir / "artifacts" / "fulltext_import" / "manual_pdf_queue.csv"
    status_path = run_dir / "artifacts" / "fulltext_import" / "pdf_intervention_status.json"
    prompt_path = run_dir / "reports" / "intervention_prompt.md"

    if not config_path.exists():
        print(f"Run config not found: {config_path}")
        return 1
    if not import_path.exists():
        print(f"Import status not found: {import_path}")
        return 1
    if not queue_path.exists():
        print(f"Manual PDF queue not found: {queue_path}")
        return 1

    config = parse_config(config_path)
    interaction_mode = config.get("interaction_mode", "human_facing")
    pdf_policy = config.get("pdf_policy", "pause_for_user")

    import_rows = load_csv(import_path)
    queue_rows = load_csv(queue_path)
    pmc_ready_count = sum(1 for row in import_rows if (row.get("normalized_path", "") or "").strip())
    pdf_queue_count = len(queue_rows)

    if pdf_queue_count == 0:
        status = "not_needed"
        recommended_action = "continue_fulltext_review"
        allowed_actions = ["continue_fulltext_review"]
        notes = "No PDF fallback intervention is needed."
    elif interaction_mode == "human_facing" and pdf_policy == "pause_for_user":
        status = "paused_for_user"
        recommended_action = "continue_pmc_only"
        allowed_actions = [
            "continue_pmc_only",
            "provide_pdfs_then_continue",
        ]
        notes = "Workflow should pause and prompt the user because PDF fallback is available."
    elif pdf_policy == "require_fulltext_completion":
        status = "awaiting_pdf"
        recommended_action = "provide_pdfs_then_continue"
        allowed_actions = ["provide_pdfs_then_continue"]
        notes = "Workflow should not proceed until PDF fallback is addressed."
    else:
        status = "continue_without_pdf"
        recommended_action = "continue_pmc_only"
        allowed_actions = ["continue_pmc_only", "schedule_pdf_followup"]
        notes = "Workflow may continue with PMC-normalized papers while preserving the PDF queue."

    payload = {
        "status": status,
        "interaction_mode": interaction_mode,
        "pdf_policy": pdf_policy,
        "pmc_ready_count": pmc_ready_count,
        "pdf_queue_count": pdf_queue_count,
        "recommended_action": recommended_action,
        "allowed_actions": allowed_actions,
        "manual_pdf_queue_path": str(queue_path),
        "resume_target": "artifacts/fulltext_review/fulltext_review.csv",
        "notes": notes,
    }
    status_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    prompt_lines = [
        "# Intervention Prompt",
        "",
        "## Status",
        "",
        f"- state: `{status}`",
        "",
        "## Summary",
        "",
        f"- PMC-ready papers: `{pmc_ready_count}`",
        f"- PDF-queued papers: `{pdf_queue_count}`",
        "",
        "## Choices",
        "",
    ]
    for index, action in enumerate(allowed_actions, start=1):
        prompt_lines.append(f"{index}. `{action}`")
    prompt_lines.extend(
        [
            "",
            "## Queue",
            "",
            f"- manual PDF queue: `{queue_path}`",
            "",
            "## Resume target",
            "",
            "- `artifacts/fulltext_review/fulltext_review.csv`",
            "",
            "## Notes",
            "",
            f"- {notes}",
        ]
    )
    prompt_path.write_text("\n".join(prompt_lines) + "\n", encoding="utf-8")

    print(f"Wrote PDF intervention status to {status_path}")
    print(f"Wrote intervention prompt to {prompt_path}")
    print(
        f"status={status} pmc_ready={pmc_ready_count} pdf_queue={pdf_queue_count} "
        f"recommended_action={recommended_action}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
