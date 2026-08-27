#!/usr/bin/env python3

from __future__ import annotations

import shutil
import sys
from pathlib import Path

from pass_archive import activate_pass, ensure_pass_layout


WORKFLOW_ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = WORKFLOW_ROOT / "runs"
TEMPLATES_DIR = WORKFLOW_ROOT / "templates"


def write_if_missing(path: Path, content: str) -> None:
    if not path.exists():
        path.write_text(content, encoding="utf-8")


def copy_template(template_name: str, target: Path) -> None:
    source = TEMPLATES_DIR / template_name
    if source.exists() and not target.exists():
        shutil.copy2(source, target)


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python3 scripts/init_run.py <run_id>")
        return 1

    run_id = sys.argv[1].strip()
    if not run_id:
        print("run_id must be non-empty")
        return 1

    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    pass1_dir = ensure_pass_layout(run_dir, 1)
    activate_pass(run_dir, 1)
    pass1_inputs_dir = pass1_dir / "inputs"

    copy_template("original_user_prompt_template.md", run_dir / "original_user_prompt.md")
    write_if_missing(pass1_inputs_dir / "request.md", "# Request\n\n")
    copy_template("run_config_template.md", pass1_inputs_dir / "run_config.md")
    copy_template("instruction_template.md", pass1_inputs_dir / "instruction.md")
    copy_template("topic_template.md", pass1_inputs_dir / "topic.md")
    write_if_missing(
        pass1_inputs_dir / "constraints.md",
        "# Constraints\n\n"
        "- PubMed collection caps are forbidden by workflow policy.\n"
        "- Do not add `max_results_per_query`, `max_total_results`, `retmax`, or equivalent collection-cap settings.\n"
        "- Use scope constraints, query refinement, and downstream batching instead.\n",
    )
    write_if_missing(pass1_inputs_dir / "notes.md", "# Notes\n\n")

    copy_template("search_strategy_template.md", pass1_dir / "artifacts" / "search_strategy" / "search_strategy.md")
    copy_template("query_refinement_report_template.md", pass1_dir / "artifacts" / "search_strategy" / "query_refinement_report.md")
    copy_template("query_diagnostics_template.csv", pass1_dir / "artifacts" / "search_strategy" / "query_diagnostics.csv")
    copy_template("paper_manifest_template.csv", pass1_dir / "artifacts" / "metadata_collection" / "paper_manifest.csv")
    copy_template("abstract_review_template.csv", pass1_dir / "artifacts" / "abstract_review" / "abstract_review.csv")
    copy_template("abstract_review2_template.csv", pass1_dir / "artifacts" / "abstract_review" / "abstract_review2.csv")
    copy_template("import_status_template.csv", pass1_dir / "artifacts" / "fulltext_import" / "import_status.csv")
    copy_template("manual_pdf_queue_template.csv", pass1_dir / "artifacts" / "fulltext_import" / "manual_pdf_queue.csv")
    copy_template("fulltext_review_template.csv", pass1_dir / "artifacts" / "fulltext_review" / "fulltext_review.csv")
    copy_template("evidence_extraction_template.csv", pass1_dir / "artifacts" / "fulltext_review" / "evidence_extraction.csv")
    copy_template("pmc_mechanism_feedback_template.csv", pass1_dir / "artifacts" / "fulltext_review" / "pmc_mechanism_feedback.csv")
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
