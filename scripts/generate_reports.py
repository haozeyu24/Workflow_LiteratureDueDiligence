#!/usr/bin/env python3

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path
from collections import Counter

from pass_archive import active_artifacts_dir, active_pass_number, active_reports_dir, run_input_path


WORKFLOW_ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = WORKFLOW_ROOT / "runs"

FINAL_FIELDS = [
    "paper_id",
    "pmid",
    "pmcid",
    "doi",
    "title",
    "year",
    "final_decision",
    "final_rationale",
    "selection_basis",
    "fulltext_access_status",
    "normalized_source_type",
    "normalized_path",
    "review_confidence",
]

PDF_REQUEST_FIELDS = [
    "paper_id",
    "pmid",
    "doi",
    "title",
    "year",
    "priority",
    "evidence_category",
    "learned_criteria_matched",
    "shortlist_rationale",
]


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    return list(csv.DictReader(path.open(encoding="utf-8")))


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


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def summarize_stage(fulltext_rows: list[dict[str, str]], normalized_count: int, final_kept: int) -> list[str]:
    if final_kept > 0:
        return [
            "full-text review completed for at least part of the normalized corpus",
            "final reading list updated",
        ]
    if fulltext_rows:
        return [
            "abstract review completed through full-text import stage",
            "normalized full texts prepared for reviewer consumption",
            "next stage: full-text review of normalized papers",
        ]
    if normalized_count > 0:
        return [
            "full-text normalization completed",
            "next stage: build or refresh the full-text review table",
        ]
    return [
        "run initialized",
        "next stage: continue the workflow from the latest completed upstream artifact",
    ]


def infer_years(manifest_rows: list[dict[str, str]]) -> dict[str, str]:
    return {row.get("paper_id", ""): row.get("year", "") for row in manifest_rows}


def infer_fulltext_access_status(import_row: dict[str, str]) -> str:
    if (import_row.get("normalized_path", "") or "").strip():
        return "readable"
    pdf_status = import_row.get("pdf_import_status", "") or ""
    if pdf_status == "parser_pending":
        return "parser_pending"
    if pdf_status == "parse_failed":
        return "parse_failed"
    return "unavailable"


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python3 scripts/generate_reports.py <run_id>")
        return 1

    run_id = sys.argv[1].strip()
    run_dir = RUNS_DIR / run_id
    artifacts_dir = active_artifacts_dir(run_dir)
    reports_dir = active_reports_dir(run_dir)
    pass_label = f"pass_{active_pass_number(run_dir) or 1:03d}"
    metadata_dir = artifacts_dir / "metadata_collection"
    abstract_dir = artifacts_dir / "abstract_review"
    import_dir = artifacts_dir / "fulltext_import"
    fulltext_dir = artifacts_dir / "fulltext_review"
    control_dir = artifacts_dir / "workflow_control"
    config = parse_config(run_input_path(run_dir, "run_config.md"))
    access_phase = config.get("access_phase", "pmc_learning")

    paper_manifest_rows = load_csv(metadata_dir / "paper_manifest.csv")
    abstract_rows = load_csv(abstract_dir / "abstract_review.csv")
    abstract2_rows = load_csv(abstract_dir / "abstract_review2.csv")
    import_rows = load_csv(import_dir / "import_status.csv")
    queue_rows = load_csv(import_dir / "manual_pdf_queue.csv")
    pdf_shortlist_rows = load_csv(import_dir / "pdf_download_shortlist.csv")
    fulltext_rows = load_csv(fulltext_dir / "fulltext_review.csv")
    evidence_rows = load_csv(fulltext_dir / "evidence_extraction.csv")
    pmc_feedback_rows = load_csv(fulltext_dir / "pmc_mechanism_feedback.csv")
    loop_rows = load_csv(control_dir / "workflow_loop_decision.csv")
    latest_pdf_decision = (
        pmc_feedback_rows[-1].get("pdf_deferral_decision", "").strip()
        if pmc_feedback_rows
        else ""
    )
    final_pdf_shortlist_active = latest_pdf_decision == "final_pdf_pass"
    if not final_pdf_shortlist_active:
        pdf_shortlist_rows = []

    reports_dir.mkdir(parents=True, exist_ok=True)

    years_by_paper_id = infer_years(paper_manifest_rows)
    abstract2_by_paper_id = {row.get("paper_id", ""): row for row in abstract2_rows}
    import_by_paper_id = {row.get("paper_id", ""): row for row in import_rows}
    final_rows: list[dict[str, str]] = []
    retained_paper_ids: set[str] = set()
    for row in fulltext_rows:
        if row.get("fulltext_decision", "") != "keep":
            continue
        paper_id = row.get("paper_id", "")
        retained_paper_ids.add(paper_id)
        final_rows.append(
            {
                "paper_id": paper_id,
                "pmid": row.get("pmid", ""),
                "pmcid": row.get("pmcid", ""),
                "doi": row.get("doi", ""),
                "title": row.get("title", ""),
                "year": years_by_paper_id.get(paper_id, ""),
                "final_decision": "selected_for_reading",
                "final_rationale": row.get("fulltext_rationale", ""),
                "selection_basis": "fulltext_review",
                "fulltext_access_status": "readable",
                "normalized_source_type": row.get("normalized_source_type", ""),
                "normalized_path": row.get("normalized_path", ""),
                "review_confidence": row.get("review_confidence", ""),
            }
        )

    if access_phase != "pmc_learning":
        for paper_id, row in abstract2_by_paper_id.items():
            if not paper_id or paper_id in retained_paper_ids:
                continue
            if row.get("promotion_decision", "") != "advance_to_import":
                continue
            import_row = import_by_paper_id.get(paper_id)
            if import_row is None:
                continue
            if (import_row.get("normalized_path", "") or "").strip():
                continue
            rationale = (row.get("abstract_reviewer2_rationale", "") or row.get("abstract_reviewer_rationale", "")).strip()
            if rationale:
                rationale += " "
            rationale += "Full text was not readable through PMC or PDF import at the time of review."
            final_rows.append(
                {
                    "paper_id": paper_id,
                    "pmid": import_row.get("pmid", ""),
                    "pmcid": import_row.get("pmcid", ""),
                    "doi": import_row.get("doi", ""),
                    "title": import_row.get("title", ""),
                    "year": years_by_paper_id.get(paper_id, ""),
                    "final_decision": "abstract_relevant_fulltext_unavailable",
                    "final_rationale": rationale,
                    "selection_basis": "abstract_review_only",
                    "fulltext_access_status": infer_fulltext_access_status(import_row),
                    "normalized_source_type": "missing",
                    "normalized_path": "",
                    "review_confidence": row.get("abstract_reviewer2_confidence", ""),
                }
            )

    final_list_path = reports_dir / "final_reading_list.csv"
    write_csv(final_list_path, FINAL_FIELDS, final_rows)

    pdf_request_rows = [
        {field: row.get(field, "") for field in PDF_REQUEST_FIELDS}
        for row in pdf_shortlist_rows
        if row.get("shortlist_decision", "") == "request_pdf"
    ]
    pdf_request_path = reports_dir / "pdf_request_shortlist.csv"
    if final_pdf_shortlist_active:
        write_csv(pdf_request_path, PDF_REQUEST_FIELDS, pdf_request_rows)
    elif pdf_request_path.exists():
        pdf_request_path.unlink()

    papers_retrieved = len(paper_manifest_rows)
    abstract_includes = sum(1 for row in abstract_rows if row.get("review_decision", "") == "include")
    pmc_usable = sum(1 for row in import_rows if row.get("pmc_parse_status", "") == "usable")
    pmc_unusable = sum(1 for row in import_rows if row.get("pmc_parse_status", "") == "unusable")
    no_pmc_access = sum(1 for row in import_rows if row.get("pmc_access_status", "") == "missing")
    pdf_needed = sum(1 for row in import_rows if row.get("pdf_needed", "") == "yes")
    pdf_normalized = sum(1 for row in import_rows if row.get("pdf_import_status", "") == "normalized")
    advance_to_import = sum(1 for row in abstract2_rows if row.get("promotion_decision", "") == "advance_to_import")
    stop_after_abstract2 = sum(1 for row in abstract2_rows if row.get("promotion_decision", "") == "stop")
    fulltext_keep = sum(1 for row in fulltext_rows if row.get("fulltext_decision", "") == "keep")
    abstract_relevant_unreadable = sum(
        1 for row in final_rows if row.get("final_decision", "") == "abstract_relevant_fulltext_unavailable"
    )
    normalized_total = sum(1 for row in import_rows if (row.get("normalized_path", "") or "").strip())
    pmc_learning_deferred_unreadable = len(queue_rows) if access_phase == "pmc_learning" else 0
    pdf_request_count = sum(1 for row in pdf_shortlist_rows if row.get("shortlist_decision", "") == "request_pdf")
    pdf_high_count = sum(
        1
        for row in pdf_shortlist_rows
        if row.get("shortlist_decision", "") == "request_pdf" and row.get("priority", "") == "high"
    )

    active_loops = [row for row in loop_rows if row.get("triggered", "") == "yes"]
    current_stage_lines = summarize_stage(fulltext_rows, normalized_total, fulltext_keep)
    if active_loops:
        current_stage_lines = [
            "workflow is not complete because one or more controller loops are still triggered",
            "next stage: execute the triggered loop actions before treating the run as final",
        ] + current_stage_lines
    notes = [
        f"`access_phase` is `{access_phase}`.",
        f"`abstractReviewer2` advanced `{advance_to_import}` papers to import and stopped `{stop_after_abstract2}` papers."
        if abstract2_rows
        else "Second abstract review has not produced promotion decisions yet.",
        f"`fullTextImporter` currently has `{pmc_usable}` usable PMC papers, `{pdf_normalized}` normalized PDF papers, and `{len(queue_rows)}` papers still in the manual PDF queue."
        if import_rows
        else "`fullTextImporter` artifacts are not available yet.",
        f"Final-loop `pdf_download_shortlist.csv` requests `{pdf_request_count}` PDFs, including `{pdf_high_count}` high-priority PDFs."
        if final_pdf_shortlist_active and pdf_shortlist_rows
        else "PDF download shortlist has not been generated because PMC learning has not yet reached `final_pdf_pass`.",
        f"`{len(fulltext_rows)}` normalized full texts are currently available in `runs/{run_id}/passes/{pass_label}/artifacts/fulltext_review/fulltext_review.csv`, and `{abstract_relevant_unreadable}` unreadable papers are carried in the final list."
        if fulltext_rows
        else "Full-text review table has not been generated yet.",
    ]
    if evidence_rows:
        tier_counts = Counter(row.get("evidence_tier", "") for row in evidence_rows)
        notes.append(
            "Evidence tiers: "
            + ", ".join(f"`{tier}`={count}" for tier, count in sorted(tier_counts.items()) if tier)
            + "."
        )
    if access_phase == "pmc_learning" and queue_rows:
        notes.append(
            f"Manual PDFs are deferred in this phase; `{len(queue_rows)}` PDF-needed papers are queued but are not requested from the user yet. Use PMC-readable full text for mechanism feedback and query reconstruction before final PDF access."
        )
    if pmc_feedback_rows:
        latest_feedback = pmc_feedback_rows[-1]
        recommended_changes = latest_feedback.get("recommended_query_changes", "").strip()
        pdf_decision = latest_feedback.get("pdf_deferral_decision", "").strip()
        feedback_note = (
            f"PMC mechanism feedback reviewed `{latest_feedback.get('source_paper_count', '')}` papers"
            f" with PDF decision `{pdf_decision}`."
        )
        if recommended_changes:
            feedback_note += f" Query changes: {recommended_changes}"
        notes.append(feedback_note)
    if loop_rows:
        if active_loops:
            notes.append(
                "Workflow loop triggered: "
                + "; ".join(
                    f"`{row.get('action', '')}` from `{row.get('source_stage', '')}` because {row.get('rationale', '')}"
                    for row in active_loops[:3]
                )
            )
        else:
            notes.append("Workflow controller did not trigger a loop.")

    progress_path = reports_dir / "progress_report.md"
    lines = [
        "# Progress Report",
        "",
        "## Run",
        "",
        f"- `run_id`: `{run_id}`",
        "",
        "## Current stage",
        "",
    ]
    for line in current_stage_lines:
        lines.append(f"- {line}")
    lines.extend(
        [
            "",
            "## Counts",
            "",
            f"- papers retrieved: `{papers_retrieved}`",
            f"- abstract includes: `{abstract_includes}`",
            f"- PMC usable: `{pmc_usable}`",
            f"- PMC unusable: `{pmc_unusable}`",
            f"- no PMC access: `{no_pmc_access}`",
            f"- PDF needed: `{pdf_needed}`",
            f"- PDF-needed papers deferred by PMC-learning phase: `{pmc_learning_deferred_unreadable}`",
            f"- PDF shortlist request count: `{pdf_request_count}`",
            f"- high-priority PDF requests: `{pdf_high_count}`",
            f"- PDF normalized: `{pdf_normalized}`",
            f"- final kept: `{fulltext_keep}`",
            f"- abstract-relevant unreadable papers included in final list: `{abstract_relevant_unreadable}`",
            "",
            "## Queues",
            "",
            f"- manual PDF queue: `runs/{run_id}/passes/{pass_label}/artifacts/fulltext_import/manual_pdf_queue.csv`",
            f"- PDF download shortlist: `runs/{run_id}/passes/{pass_label}/artifacts/fulltext_import/pdf_download_shortlist.csv`"
            if final_pdf_shortlist_active
            else "- PDF download shortlist: not generated before final PMC-satisfied loop",
            f"- PDF request shortlist: `runs/{run_id}/passes/{pass_label}/reports/pdf_request_shortlist.csv`"
            if final_pdf_shortlist_active
            else "- PDF request shortlist: not generated before final PMC-satisfied loop",
            "",
            "## Notes",
            "",
        ]
    )
    for note in notes:
        lines.append(f"- {note}")
    progress_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote progress report to {progress_path}")
    print(f"Wrote final reading list to {final_list_path}")
    if final_pdf_shortlist_active:
        print(f"Wrote PDF request shortlist to {pdf_request_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
