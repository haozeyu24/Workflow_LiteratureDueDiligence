#!/usr/bin/env python3

from __future__ import annotations

import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

from pass_archive import (
    active_artifacts_dir,
    archive_path_for_pass,
    current_pass_number,
    incomplete_sentinel_path,
    load_all_pass_csv,
    run_input_path,
    snapshot_current_pass,
)


WORKFLOW_ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = WORKFLOW_ROOT / "runs"

FIELDS = [
    "loop_id",
    "source_stage",
    "trigger",
    "triggered",
    "action",
    "target_stage",
    "rationale",
    "required_changes",
    "stop_condition",
]

STATE_STATUSES = {
    "initialized",
    "running",
    "loop_required",
    "awaiting_pdf_shortlist",
    "complete",
    "blocked",
}

LEARNED_RERUN_COLLECTION_REVIEW_RATIO = 0.80
LEARNED_RERUN_ADVANCE_REVIEW_RATIO = 0.70


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


def config_int(config: dict[str, str], key: str, default: int) -> int:
    value = config.get(key, "").strip()
    if not value.isdigit():
        return default
    return int(value)


def pmc_fulltext_review_gate_mode(config: dict[str, str]) -> str:
    return config.get("pmc_fulltext_review_gate_mode", "all_available").strip() or "all_available"


def ratio(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def add_decision(
    rows: list[dict[str, str]],
    source_stage: str,
    trigger: str,
    triggered: bool,
    action: str,
    target_stage: str,
    rationale: str,
    required_changes: str,
    stop_condition: str,
) -> None:
    rows.append(
        {
            "loop_id": f"loop_{len(rows) + 1}",
            "source_stage": source_stage,
            "trigger": trigger,
            "triggered": "yes" if triggered else "no",
            "action": action,
            "target_stage": target_stage,
            "rationale": rationale,
            "required_changes": required_changes,
            "stop_condition": stop_condition,
        }
    )


def blank_count(rows: list[dict[str, str]], field: str) -> int:
    return sum(1 for row in rows if not row.get(field, "").strip())


def id_set(rows: list[dict[str, str]]) -> set[str]:
    return {row.get("paper_id", "").strip() for row in rows if row.get("paper_id", "").strip()}


def advance_count(rows: list[dict[str, str]]) -> int:
    return sum(1 for row in rows if row.get("promotion_decision", "").strip() == "advance_to_import")


def add_learned_rerun_burden_confirmation(
    decisions: list[dict[str, str]],
    run_dir: Path,
    manifest_rows: list[dict[str, str]],
    abstract2_rows: list[dict[str, str]],
) -> None:
    pass_number = current_pass_number(run_dir)
    if pass_number <= 1 or not manifest_rows or not abstract2_rows:
        return

    previous_pass = archive_path_for_pass(run_dir, pass_number - 1)
    previous_manifest_rows = load_csv(previous_pass / "artifacts" / "metadata_collection" / "paper_manifest.csv")
    previous_abstract2_rows = load_csv(previous_pass / "artifacts" / "abstract_review" / "abstract_review2.csv")
    if not previous_manifest_rows or not previous_abstract2_rows:
        return

    current_collection = len(manifest_rows)
    previous_collection = len(previous_manifest_rows)
    current_advance = advance_count(abstract2_rows)
    previous_advance = advance_count(previous_abstract2_rows)
    collection_ratio = ratio(current_collection, previous_collection)
    advance_ratio = ratio(current_advance, previous_advance)

    collection_needs_review = collection_ratio > LEARNED_RERUN_COLLECTION_REVIEW_RATIO
    advance_needs_review = previous_advance > 0 and advance_ratio > LEARNED_RERUN_ADVANCE_REVIEW_RATIO
    if not (collection_needs_review or advance_needs_review):
        return

    if collection_needs_review:
        action = "continue"
        target_stage = "pubmedKeywordScout"
        rationale = (
            f"Learned rerun collection crossed the confirmation threshold: pass_{pass_number:03d} has "
            f"{current_collection} collected records versus {previous_collection} in pass_{pass_number - 1:03d} "
            f"({collection_ratio:.1%})."
        )
        required_changes = (
            "Confirm that the learned search strategy used pass-1 full-text learning to focus the run on the "
            "user prompt. If the larger set comes from context/modifier terms becoming standalone drivers, "
            "revise the query; if it comes from newly learned in-scope mechanism vocabulary, document that rationale."
        )
    else:
        action = "continue"
        target_stage = "abstractReviewer2"
        rationale = (
            f"Learned rerun abstract promotion crossed the confirmation threshold: pass_{pass_number:03d} advanced "
            f"{current_advance} papers versus {previous_advance} in pass_{pass_number - 1:03d} ({advance_ratio:.1%})."
        )
        required_changes = (
            "Confirm that reviewer calibration from pass 1 was applied. If promotion is high because papers only "
            "match context, comparator, assay, population, intervention, or outcome terms, tighten abstract triage."
        )

    add_decision(
        decisions,
        "workflow_control",
        "learned_rerun_burden_confirmation",
        False,
        action,
        target_stage,
        rationale,
        required_changes,
        (
            "This is a confirmation signal, not a hard gate. Proceed only if the learned rerun is justified by "
            "documented pass-1 learning and remains focused on the user's prompt."
        ),
    )


def add_stage_gate_decision(
    decisions: list[dict[str, str]],
    manifest_rows: list[dict[str, str]],
    abstract_rows: list[dict[str, str]],
    abstract2_rows: list[dict[str, str]],
    import_rows: list[dict[str, str]],
    fulltext_rows: list[dict[str, str]],
    evidence_rows: list[dict[str, str]],
    pmc_feedback_rows: list[dict[str, str]],
) -> bool:
    """Fail closed on incomplete stage handoffs before higher-level loop logic."""
    if not manifest_rows:
        add_decision(
            decisions,
            "metadata_collection",
            "collection_pending",
            True,
            "loop_to_query_scout",
            "pubmedCollector",
            "No collected paper manifest exists for the active pass.",
            "Run PubMed collection from the accepted search strategy before abstract review or reporting.",
            "Proceed when paper_manifest.csv contains the full accepted PubMed result set.",
        )
        return True

    manifest_ids = id_set(manifest_rows)
    abstract_ids = id_set(abstract_rows)
    abstract2_ids = id_set(abstract2_rows)

    review1_blank_decisions = blank_count(abstract_rows, "review_decision")
    review1_blank_confidence = blank_count(abstract_rows, "review_confidence")
    review1_blank_reviewer = blank_count(abstract_rows, "reviewer_type")
    if (
        len(abstract_rows) != len(manifest_rows)
        or abstract_ids != manifest_ids
        or review1_blank_decisions
        or review1_blank_confidence
        or review1_blank_reviewer
    ):
        add_decision(
            decisions,
            "abstract_review",
            "abstract_review_1_pending",
            True,
            "loop_to_abstract_review",
            "abstractReviewer",
            (
                "Abstract review 1 is incomplete: "
                f"{len(abstract_rows)} rows for {len(manifest_rows)} manifest records; "
                f"blank decisions={review1_blank_decisions}, "
                f"blank confidence={review1_blank_confidence}, "
                f"blank reviewer_type={review1_blank_reviewer}."
            ),
            "Fill review_decision, review_confidence, reviewer_type, and rationale for every paper_manifest row before reviewer 2, import, PDF, or final reporting.",
            "Proceed when abstract_review.csv has one complete valid decision row per paper_manifest row.",
        )
        return True

    review2_blank_decisions = blank_count(abstract2_rows, "abstract_reviewer2_decision")
    review2_blank_confidence = blank_count(abstract2_rows, "abstract_reviewer2_confidence")
    promotion_blank = blank_count(abstract2_rows, "promotion_decision")
    if (
        len(abstract2_rows) != len(manifest_rows)
        or abstract2_ids != manifest_ids
        or review2_blank_decisions
        or review2_blank_confidence
        or promotion_blank
    ):
        add_decision(
            decisions,
            "abstract_review",
            "abstract_review_2_pending",
            True,
            "loop_to_abstract_review",
            "abstractReviewer2",
            (
                "Abstract review 2 is incomplete: "
                f"{len(abstract2_rows)} rows for {len(manifest_rows)} manifest records; "
                f"blank reviewer2 decisions={review2_blank_decisions}, "
                f"blank confidence={review2_blank_confidence}, "
                f"blank promotion decisions={promotion_blank}."
            ),
            "Fill abstractReviewer2 decisions, confidence, rationale, and promotion_decision for every paper before import, PDF, or final reporting.",
            "Proceed when abstract_review2.csv has one complete valid promotion row per paper_manifest row.",
        )
        return True

    advanced_ids = {
        row.get("paper_id", "").strip()
        for row in abstract2_rows
        if row.get("promotion_decision", "").strip() == "advance_to_import"
    }
    import_ids = id_set(import_rows)
    if advanced_ids != import_ids:
        add_decision(
            decisions,
            "fulltext_import",
            "pmc_import_pending",
            True,
            "continue",
            "fullTextImporter",
            (
                "Full-text import handoff is incomplete: "
                f"{len(advanced_ids)} papers advanced to import, "
                f"{len(import_ids)} import_status rows exist."
            ),
            "Run prepare_import_status.py and PMC import for the abstractReviewer2 advance_to_import set before PDF or final reporting.",
            "Proceed when import_status.csv exactly covers the advance_to_import paper set.",
        )
        return True

    normalized_ids = {
        row.get("paper_id", "").strip()
        for row in import_rows
        if row.get("normalized_path", "").strip()
    }
    fulltext_ids = id_set(fulltext_rows)
    if normalized_ids != fulltext_ids:
        add_decision(
            decisions,
            "fulltext_review",
            "fulltext_review_pending",
            True,
            "loop_to_fulltext_review",
            "fullTextReviewer",
            (
                "Full-text review handoff is incomplete: "
                f"{len(normalized_ids)} normalized readable imports, "
                f"{len(fulltext_ids)} fulltext_review rows."
            ),
            "Run prepare_fulltext_review.py and review every normalized readable full text before PMC feedback or final reporting.",
            "Proceed when fulltext_review.csv exactly covers normalized readable imports.",
        )
        return True

    if fulltext_rows and not evidence_rows:
        add_decision(
            decisions,
            "fulltext_review",
            "missing_evidence_extraction",
            True,
            "loop_to_fulltext_review",
            "fullTextReviewer",
            "Full-text review rows exist but evidence_extraction.csv is empty.",
            "Extract structured evidence for every readable full text before PMC mechanism feedback or final reporting.",
            "Proceed when evidence_extraction.csv supports every full-text keep/drop decision.",
        )
        return True

    if fulltext_rows and evidence_rows:
        reviewed_ids = {
            row.get("paper_id", "").strip()
            for row in fulltext_rows
            if row.get("fulltext_decision", "").strip()
        }
        evidence_ids = {
            row.get("paper_id", "").strip()
            for row in evidence_rows
            if row.get("paper_id", "").strip()
        }
        if reviewed_ids != evidence_ids:
            add_decision(
                decisions,
                "fulltext_review",
                "evidence_extraction_incomplete",
                True,
                "loop_to_fulltext_review",
                "fullTextReviewer",
                (
                    "Evidence extraction coverage is incomplete: "
                    f"{len(reviewed_ids)} reviewed full-text papers and {len(evidence_ids)} evidence rows."
                ),
                (
                    "Write exactly one evidence_extraction.csv row for every fulltext_review.csv row "
                    "with a keep/drop decision before PMC feedback, final reporting, or completion."
                ),
                "Proceed when evidence_extraction.csv exactly covers all reviewed readable full texts.",
            )
            return True

    if fulltext_rows and evidence_rows and not pmc_feedback_rows:
        add_decision(
            decisions,
            "fulltext_review",
            "pmc_feedback_pending",
            True,
            "loop_to_fulltext_review",
            "fullTextReviewer",
            "Readable full text has been reviewed, but no PMC mechanism feedback row exists for query learning.",
            "Write pmc_mechanism_feedback.csv before PDF access or learned rerun decisions.",
            "Proceed when PMC feedback summarizes mechanisms, noise families, missing terms, query changes, and PDF deferral decision.",
        )
        return True

    return False


def add_pmc_fulltext_review_gate_decision(
    decisions: list[dict[str, str]],
    config: dict[str, str],
    import_rows: list[dict[str, str]],
    fulltext_rows: list[dict[str, str]],
    evidence_rows: list[dict[str, str]],
    pmc_feedback_rows: list[dict[str, str]],
) -> None:
    if pmc_fulltext_review_gate_mode(config) != "all_available":
        return

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

    missing_review = usable_ids - reviewed_ids
    missing_evidence = usable_ids - evidence_ids
    if not (unattempted_ids or unusable_not_queued_ids or missing_review or missing_evidence):
        return

    if unattempted_ids or unusable_not_queued_ids:
        action = "continue"
        target_stage = "fullTextImporter"
        required_changes = (
            "Continue PMC import until every pmc_access_status=available paper has pmc_parse_status usable or unusable; "
            "usable PMC full text must have normalized_path and unusable PMC records must be queued for PDF access."
        )
    else:
        action = "loop_to_fulltext_review"
        target_stage = "fullTextReviewer"
        required_changes = (
            "Review every PMC-available normalized full text and write a matching evidence_extraction.csv row "
            "before using PMC feedback for learned query revision."
        )

    add_decision(
        decisions,
        "fulltext_review",
        "pmc_fulltext_review_gate_incomplete",
        True,
        action,
        target_stage,
        (
            "Strict PMC full-text review gate is incomplete: "
            f"PMC-available={len(pmc_available_ids)}, PMC-unattempted={len(unattempted_ids)}, "
            f"PMC-usable={len(usable_ids)}, fulltext_reviewed={len(reviewed_ids & usable_ids)}, "
            f"evidence_extracted={len(evidence_ids & usable_ids)}, "
            f"unusable_not_queued={len(unusable_not_queued_ids)}."
        ),
        required_changes,
        "Proceed to run-guidance revision only when 100% of usable PMC full texts are normalized, reviewed, and evidence-extracted, and every unusable PMC record is queued for PDF access.",
    )
    decisions.insert(0, decisions.pop())


def build_state(
    run_id: str,
    access_phase: str,
    min_big_workflow_loops: int,
    max_workflow_loops: int,
    decisions: list[dict[str, str]],
    fulltext_rows: list[dict[str, str]],
    pmc_feedback_rows: list[dict[str, str]],
    queue_rows: list[dict[str, str]],
    pdf_shortlist_rows: list[dict[str, str]],
) -> dict[str, object]:
    active_loop_count = sum(row.get("triggered") == "yes" for row in decisions)
    latest_pdf_decision = (
        pmc_feedback_rows[-1].get("pdf_deferral_decision", "").strip()
        if pmc_feedback_rows
        else ""
    )
    final_learning_satisfied = (
        len(pmc_feedback_rows) >= min_big_workflow_loops
        and latest_pdf_decision == "final_pdf_pass"
    )
    effective_access_phase = "final_access" if final_learning_satisfied else access_phase
    pdf_request_count = sum(
        row.get("shortlist_decision", "") == "request_pdf"
        for row in pdf_shortlist_rows
    )

    state = {
        "run_id": run_id,
        "status": "running",
        "access_phase": effective_access_phase,
        "completion_signal": "",
        "next_action": "continue_workflow",
        "active_loop_count": active_loop_count,
        "completed_big_loop_count": len(pmc_feedback_rows),
        "min_big_workflow_loops": min_big_workflow_loops,
        "max_workflow_loops": max_workflow_loops,
        "latest_pdf_deferral_decision": latest_pdf_decision,
        "manual_pdf_queue_count": len(queue_rows),
        "pdf_download_shortlist_count": len(pdf_shortlist_rows),
        "pdf_request_count": pdf_request_count,
        "reason": "Workflow has not yet reached a controller-recognized completion state.",
    }

    if len(pmc_feedback_rows) >= max_workflow_loops and latest_pdf_decision != "final_pdf_pass":
        state.update(
            {
                "status": "blocked",
                "next_action": "stop_blocked",
                "reason": "Maximum big workflow loop count reached without final_pdf_pass.",
            }
        )
    elif active_loop_count:
        state.update(
            {
                "status": "loop_required",
                "next_action": decisions[0].get("action", "continue_workflow"),
                "reason": "One or more workflow controller triggers are active.",
            }
        )
    elif fulltext_rows and pmc_feedback_rows and len(pmc_feedback_rows) < min_big_workflow_loops:
        state.update(
            {
                "status": "loop_required",
                "next_action": "loop_to_query_scout",
                "reason": "Minimum big workflow loop count has not been satisfied; apply PMC learning to a revised query/review/import pass before final PDF access.",
            }
        )
    elif queue_rows and latest_pdf_decision == "final_pdf_pass" and not pdf_shortlist_rows:
        state.update(
            {
                "status": "awaiting_pdf_shortlist",
                "next_action": "build_pdf_download_shortlist",
                "reason": "PMC learning is satisfied and the final PDF queue has not been scored.",
            }
        )
    elif fulltext_rows and pmc_feedback_rows and latest_pdf_decision == "final_pdf_pass":
        if queue_rows:
            state.update(
                {
                    "status": "complete",
                    "completion_signal": "pdf_download_shortlist_ready",
                    "next_action": "report_final_loop",
                    "reason": "Final-access criteria are satisfied and the PDF queue has a download shortlist.",
                }
            )
        else:
            state.update(
                {
                    "status": "complete",
                    "completion_signal": "no_pdf_queue",
                    "next_action": "report_final_loop",
                    "reason": "Final-access criteria are satisfied and no manual PDF queue remains.",
                }
            )
    elif latest_pdf_decision == "defer_pdfs":
        state.update(
            {
                "status": "loop_required",
                "next_action": "loop_to_query_scout",
                "reason": "PMC feedback says to defer PDFs and use full-text learning to refine the query.",
            }
        )

    if state["status"] not in STATE_STATUSES:
        state["status"] = "running"
    return state


def update_incomplete_sentinel(run_dir: Path, state: dict[str, object]) -> None:
    sentinel_path = incomplete_sentinel_path(run_dir)
    if state.get("status") == "complete":
        if sentinel_path.exists():
            sentinel_path.unlink()
        return

    sentinel_path.write_text(
        "This run is not workflow-complete.\n"
        "Do not report the workflow as done until scripts/completion_gate.py passes.\n"
        f"Current controller status: {state.get('status', 'unknown')}\n"
        f"Next action: {state.get('next_action', 'unknown')}\n"
        f"Reason: {state.get('reason', '')}\n",
        encoding="utf-8",
    )


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python3 scripts/assess_workflow_loops.py <run_id>")
        return 1

    run_id = sys.argv[1].strip()
    run_dir = RUNS_DIR / run_id
    if not run_dir.exists():
        print(f"Run does not exist: {run_dir}")
        return 1

    artifacts_dir = active_artifacts_dir(run_dir)
    metadata_dir = artifacts_dir / "metadata_collection"
    abstract_dir = artifacts_dir / "abstract_review"
    import_dir = artifacts_dir / "fulltext_import"
    fulltext_dir = artifacts_dir / "fulltext_review"
    control_dir = artifacts_dir / "workflow_control"
    control_dir.mkdir(parents=True, exist_ok=True)

    manifest_rows = load_csv(metadata_dir / "paper_manifest.csv")
    abstract_rows = load_csv(abstract_dir / "abstract_review.csv")
    abstract2_rows = load_csv(abstract_dir / "abstract_review2.csv")
    import_rows = load_csv(import_dir / "import_status.csv")
    queue_rows = load_csv(import_dir / "manual_pdf_queue.csv")
    pdf_shortlist_rows = load_csv(import_dir / "pdf_download_shortlist.csv")
    fulltext_rows = load_csv(fulltext_dir / "fulltext_review.csv")
    evidence_rows = load_csv(fulltext_dir / "evidence_extraction.csv")
    pmc_feedback_rows = load_csv(fulltext_dir / "pmc_mechanism_feedback.csv")
    all_pmc_feedback_rows = load_all_pass_csv(run_dir, "artifacts/fulltext_review/pmc_mechanism_feedback.csv")
    config = parse_config(run_input_path(run_dir, "run_config.md"))
    access_phase = config.get("access_phase", "pmc_learning")
    min_big_workflow_loops = max(2, config_int(config, "min_big_workflow_loops", 2))
    max_workflow_loops = min(5, config_int(config, "max_workflow_loops", 5))
    if max_workflow_loops < min_big_workflow_loops:
        max_workflow_loops = min_big_workflow_loops

    decisions: list[dict[str, str]] = []
    add_stage_gate_decision(
        decisions,
        manifest_rows,
        abstract_rows,
        abstract2_rows,
        import_rows,
        fulltext_rows,
        evidence_rows,
        pmc_feedback_rows,
    )
    add_learned_rerun_burden_confirmation(
        decisions,
        run_dir,
        manifest_rows,
        abstract2_rows,
    )
    add_pmc_fulltext_review_gate_decision(
        decisions,
        config,
        import_rows,
        fulltext_rows,
        evidence_rows,
        pmc_feedback_rows,
    )

    feedback_query_change = any(
        row.get("pdf_deferral_decision", "") == "defer_pdfs"
        and (
            row.get("recommended_query_changes", "").strip()
            or row.get("noise_keyword_families", "").strip()
            or row.get("missing_keyword_families", "").strip()
        )
        for row in pmc_feedback_rows
    )
    pmc_gate_incomplete = any(
        row.get("trigger", "") == "pmc_fulltext_review_gate_incomplete"
        and row.get("triggered", "") == "yes"
        for row in decisions
    )
    if feedback_query_change and access_phase != "final_access" and not pmc_gate_incomplete:
        latest_feedback = pmc_feedback_rows[-1]
        add_decision(
            decisions,
            "fulltext_review",
            "pmc_learning_query_feedback",
            True,
            "loop_to_run_guidance_reviser",
            "runGuidanceReviser",
            "PMC mechanism feedback recommends run-guidance revision and query reconstruction before PDF effort.",
            latest_feedback.get("recommended_query_changes", "")
            or "Use PMC-derived mechanism and noise terms to revise instruction.md, topic.md, reviewer rules, and then the query.",
            "Proceed when run_guidance_revision_log.csv records the latest PMC feedback loop and the revised query preserves direct mechanisms while reducing repeated noise families.",
        )

    latest_pdf_decision = all_pmc_feedback_rows[-1].get("pdf_deferral_decision", "") if all_pmc_feedback_rows else ""

    if fulltext_rows and all_pmc_feedback_rows and len(all_pmc_feedback_rows) < min_big_workflow_loops and not pmc_gate_incomplete:
        latest_feedback = all_pmc_feedback_rows[-1]
        add_decision(
            decisions,
            "fulltext_review",
            "minimum_big_loop_not_satisfied",
            True,
            "loop_to_run_guidance_reviser",
            "runGuidanceReviser",
            f"Only {len(all_pmc_feedback_rows)} big PMC-learning pass has completed; the workflow requires at least {min_big_workflow_loops} big passes before final PDF access.",
            latest_feedback.get("recommended_query_changes", "")
            or "Use PMC-derived retained mechanisms, missing terms, and noise families to revise run guidance and reconstruct the query, then rerun collection, abstract review, PMC import, and full-text review.",
            "Proceed to final PDF access only after at least two PMC-feedback passes exist and the latest pass independently marks final_pdf_pass.",
        )
    elif all_pmc_feedback_rows and len(all_pmc_feedback_rows) >= max_workflow_loops and latest_pdf_decision != "final_pdf_pass":
        add_decision(
            decisions,
            "workflow_control",
            "maximum_big_loop_reached",
            True,
            "stop_blocked",
            "reporter",
            f"The workflow has reached max_workflow_loops={max_workflow_loops} without final_pdf_pass.",
            "Report the unresolved failure mode and do not continue looping automatically.",
            "Resume only after a human or parent agent changes scope, query strategy, or access policy.",
        )

    minimum_big_loop_satisfied = len(all_pmc_feedback_rows) >= min_big_workflow_loops

    if (
        minimum_big_loop_satisfied
        and pmc_feedback_rows
        and queue_rows
        and latest_pdf_decision == "final_pdf_pass"
        and not pdf_shortlist_rows
    ):
        add_decision(
            decisions,
            "fulltext_import",
            "missing_pdf_shortlist",
            True,
            "build_pdf_shortlist",
            "fullTextImporter",
            f"PMC mechanism feedback marks the run ready for final PDF pass and the manual PDF queue contains {len(queue_rows)} papers, but no PDF download shortlist exists.",
            "Build artifacts/fulltext_import/pdf_download_shortlist.csv using PMC-derived mechanism criteria, with request_pdf/defer_pdf/do_not_request decisions for every queued paper.",
            "Proceed only after the shortlist exists and the user-facing report summarizes the request_pdf subset separately from the raw queue.",
        )

    pdf_queue_rate = ratio(len(queue_rows), len(import_rows))
    if import_rows and pdf_queue_rate > 0.50 and access_phase != "final_access":
        if fulltext_rows and evidence_rows and not pmc_feedback_rows:
            add_decision(
                decisions,
                "fulltext_review",
                "missing_pmc_mechanism_feedback",
                True,
                "loop_to_fulltext_review",
                "fullTextReviewer",
                f"Manual PDF queue contains {len(queue_rows)} of {len(import_rows)} advanced papers ({pdf_queue_rate:.0%}), but PMC-readable full text has not been summarized for query learning.",
                "Read available PMC-normalized full text and write pmc_mechanism_feedback.csv with direct mechanisms, noise keyword families, missing terms, and query changes. Keep PDFs deferred.",
                "Proceed when PMC feedback either supports query reconstruction or marks the cohort ready for final PDF access.",
            )
        elif pmc_feedback_rows and latest_pdf_decision == "defer_pdfs":
            add_decision(
                decisions,
                "fulltext_import",
                "large_pdf_queue_after_pmc_learning",
                True,
                "loop_to_run_guidance_reviser",
                "runGuidanceReviser",
                f"Manual PDF queue contains {len(queue_rows)} of {len(import_rows)} advanced papers ({pdf_queue_rate:.0%}) after PMC learning.",
                "Use pmc_mechanism_feedback.csv to revise run guidance and tighten query families that feed low-value unavailable papers before requesting PDFs.",
                "Proceed to final PDF access only for direct or high-priority indirect papers after query/reviewer calibration.",
            )
        elif pmc_feedback_rows and latest_pdf_decision == "final_pdf_pass" and pdf_shortlist_rows:
            requested_count = sum(
                row.get("shortlist_decision", "") == "request_pdf"
                for row in pdf_shortlist_rows
            )
            add_decision(
                decisions,
                "fulltext_import",
                "final_pdf_shortlist_ready",
                False,
                "continue",
                "fullTextImporter",
                f"PMC feedback marks this as final PDF pass and the shortlist requests {requested_count} of {len(queue_rows)} queued PDFs.",
                "Use pdf_download_shortlist.csv as the access action list. Do not loop back solely because the raw PDF queue remains large.",
                "Proceed according to the PDF shortlist and run_config PDF policy.",
            )
    if fulltext_rows and not evidence_rows:
        add_decision(
            decisions,
            "fulltext_review",
            "missing_evidence_extraction",
            True,
            "loop_to_fulltext_review",
            "fullTextReviewer",
            "Full-text review has keep/drop decisions but no evidence extraction table.",
            "Extract evidence tiers, evidence types, directness, centrality, supporting locator, and query-feedback signal for every readable full text.",
            "Proceed when every full-text keep is supported by direct, indirect, or run-authorized comparator evidence.",
        )
    elif evidence_rows and access_phase == "final_access":
        fulltext_decisions = {row.get("paper_id", ""): row.get("fulltext_decision", "") for row in fulltext_rows}
        weak_kept_count = sum(
            1
            for row in evidence_rows
            if row.get("evidence_tier", "") in {"background", "exclude"}
            and fulltext_decisions.get(row.get("paper_id", "")) == "keep"
        )
        weak_kept_rate = ratio(weak_kept_count, len(evidence_rows))
        if weak_kept_rate > 0.05:
            rationale_parts = []
            if weak_kept_rate > 0.05:
                rationale_parts.append(f"{weak_kept_rate:.0%} of evidence rows are weak/background papers still kept")
            add_decision(
                decisions,
                "fulltext_review",
                "weak_final_keep_calibration",
                True,
                "loop_to_fulltext_review",
                "fullTextReviewer",
                "Evidence extraction calibration trigger: " + "; ".join(rationale_parts) + ".",
                "Audit final keeps against extracted evidence tiers. Drop background/exclude evidence by default and require each keep to name the decisive direct or strong indirect evidence.",
                "Proceed when final keeps are direct, strong indirect, or authorized comparator evidence.",
            )

    if not decisions:
        add_decision(
            decisions,
            "workflow_control",
            "no_loop_trigger",
            False,
            "continue",
            "reporter",
            "No artifact-level loop trigger fired.",
            "No workflow revision required.",
            "Continue to final reporting.",
        )

    output_path = control_dir / "workflow_loop_decision.csv"
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(decisions)

    triggered = sum(row["triggered"] == "yes" for row in decisions)
    state = build_state(
        run_id,
        access_phase,
        min_big_workflow_loops,
        max_workflow_loops,
        decisions,
        fulltext_rows,
        all_pmc_feedback_rows,
        queue_rows,
        pdf_shortlist_rows,
    )
    state_path = control_dir / "workflow_state.json"
    state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    update_incomplete_sentinel(run_dir, state)
    snapshot_dir = snapshot_current_pass(run_dir, "after_workflow_controller_assessment")
    if snapshot_dir:
        print(f"Archived current pass snapshot at {snapshot_dir}")
    print(f"Wrote {len(decisions)} loop decisions to {output_path} ({triggered} triggered)")
    print(f"Wrote workflow state to {state_path} (status={state['status']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
