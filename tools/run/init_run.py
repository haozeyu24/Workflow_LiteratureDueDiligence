#!/usr/bin/env python3

from __future__ import annotations

import sys
from pathlib import Path

TOOLS_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS_ROOT / "core"))
from tool_paths import WORKFLOW_ROOT, ensure_tool_paths
ensure_tool_paths()

import shutil
import sys
from pathlib import Path

from pass_archive import activate_pass, ensure_pass_layout, incomplete_sentinel_path, phase1_dir, phase1_transcript_path
from workflow_db import connect

RUNS_DIR = WORKFLOW_ROOT / "runs"
TEMPLATES_DIR = WORKFLOW_ROOT / "templates"


def write_if_missing(path: Path, content: str) -> None:
    if not path.exists():
        path.write_text(content, encoding="utf-8")


def copy_template(template_name: str, target: Path) -> None:
    matches = sorted(TEMPLATES_DIR.rglob(template_name))
    if len(matches) != 1:
        raise FileNotFoundError(f"Expected one template named {template_name}, found {len(matches)}")
    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(matches[0], target)


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python3 tools/run/init_run.py <run_id>")
        return 1

    run_id = sys.argv[1].strip()
    if not run_id:
        print("run_id must be non-empty")
        return 1

    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    phase1_dir(run_dir).mkdir(parents=True, exist_ok=True)
    with connect(run_dir):
        pass
    write_if_missing(
        incomplete_sentinel_path(run_dir),
        "This run is not workflow-complete.\n"
        "Do not report the workflow as done until tools/run/completion_gate.py passes.\n",
    )
    pass1_dir = ensure_pass_layout(run_dir, 1)
    activate_pass(run_dir, 1)
    pass1_inputs_dir = pass1_dir / "inputs"

    copy_template("original_user_prompt_template.md", run_dir / "original_user_prompt.md")
    copy_template("phase1_transcript_template.md", phase1_transcript_path(run_dir))
    copy_template("run_config_template.md", pass1_inputs_dir / "run_config.md")
    copy_template("run_brief_template.md", pass1_inputs_dir / "run_brief.md")

    copy_template("search_strategy_template.md", pass1_dir / "artifacts" / "search_strategy" / "search_strategy.md")
    copy_template("query_refinement_report_template.md", pass1_dir / "artifacts" / "search_strategy" / "query_refinement_report.md")
    copy_template("query_diagnostics_template.csv", pass1_dir / "artifacts" / "search_strategy" / "query_diagnostics.csv")
    copy_template("paper_manifest_template.csv", pass1_dir / "artifacts" / "metadata_collection" / "paper_manifest.csv")
    copy_template("abstract_triage_first_pass_template.csv", pass1_dir / "artifacts" / "abstract_triage" / "first_pass.csv")
    copy_template("abstract_triage_second_pass_template.csv", pass1_dir / "artifacts" / "abstract_triage" / "second_pass.csv")
    # Downstream full-text artifacts are created by the import/review stages.
    # Creating placeholder files at initialization makes early-stage runs look
    # as if full-text import has already started.
    copy_template("workflow_loop_decision_template.csv", pass1_dir / "artifacts" / "workflow_control" / "workflow_loop_decision.csv")
    copy_template("workflow_state_template.json", pass1_dir / "artifacts" / "workflow_control" / "workflow_state.json")
    copy_template("run_guidance_revision_log_template.csv", pass1_dir / "artifacts" / "workflow_control" / "run_guidance_revision_log.csv")
    copy_template("final_reading_list_template.csv", pass1_dir / "reports" / "final_reading_list.csv")
    copy_template("progress_report_template.md", pass1_dir / "reports" / "progress_report.md")

    print(f"Initialized run at {run_dir}")
    print(f"Active pass: {pass1_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
