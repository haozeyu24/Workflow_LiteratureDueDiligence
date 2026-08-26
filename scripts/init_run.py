#!/usr/bin/env python3

from __future__ import annotations

import shutil
import sys
from pathlib import Path


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

    for subdir in [
        "artifacts/search_strategy",
        "artifacts/metadata_collection",
        "artifacts/abstract_review",
        "artifacts/fulltext_import",
        "artifacts/fulltext_review",
        "reports",
    ]:
        (run_dir / subdir).mkdir(parents=True, exist_ok=True)

    write_if_missing(run_dir / "request.md", "# Request\n\n")
    copy_template("run_config_template.md", run_dir / "run_config.md")
    copy_template("instruction_template.md", run_dir / "instruction.md")
    copy_template("topic_template.md", run_dir / "topic.md")
    write_if_missing(run_dir / "constraints.md", "# Constraints\n\n")
    write_if_missing(run_dir / "notes.md", "# Notes\n\n")

    copy_template("search_strategy_template.md", run_dir / "artifacts" / "search_strategy" / "search_strategy.md")
    copy_template("query_refinement_report_template.md", run_dir / "artifacts" / "search_strategy" / "query_refinement_report.md")
    copy_template("paper_manifest_template.csv", run_dir / "artifacts" / "metadata_collection" / "paper_manifest.csv")
    copy_template("abstract_review_template.csv", run_dir / "artifacts" / "abstract_review" / "abstract_review.csv")
    copy_template("abstract_review2_template.csv", run_dir / "artifacts" / "abstract_review" / "abstract_review2.csv")
    copy_template("import_status_template.csv", run_dir / "artifacts" / "fulltext_import" / "import_status.csv")
    copy_template("fulltext_review_template.csv", run_dir / "artifacts" / "fulltext_review" / "fulltext_review.csv")
    copy_template("final_reading_list_template.csv", run_dir / "reports" / "final_reading_list.csv")
    copy_template("progress_report_template.md", run_dir / "reports" / "progress_report.md")

    print(f"Initialized run at {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
