#!/usr/bin/env python3

from __future__ import annotations

import sys
from pathlib import Path

TOOLS_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS_ROOT / "core"))
from tool_paths import WORKFLOW_ROOT, ensure_tool_paths
ensure_tool_paths()

import csv
from pathlib import Path

from heuristic_fulltext_review import (
    EVIDENCE_FIELDS,
    FULLTEXT_FIELDS,
    classify_paper,
    hard_negative_terms,
    load_json_text,
    paper_learning_note,
)
from heuristic_abstract_triage_first_pass import build_review_profile, matched_terms
from pass_archive import active_artifacts_dir, active_pass_number
from workflow_db import record_fulltext_read_state

RUNS_DIR = WORKFLOW_ROOT / "runs"

RESCUE_FIELDS = [
    "paper_id",
    "pmid",
    "pmcid",
    "doi",
    "title",
    "normalized_source_type",
    "normalized_path",
    "original_fulltext_decision",
    "original_fulltext_rationale",
    "rescue_decision",
    "final_fulltext_decision",
    "rescue_rationale",
    "positive_signal_found",
    "negative_signal_overridden",
    "supporting_text_locator",
    "review_confidence",
]


def load_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def evidence_row_from_decision(row: dict[str, str], decision: dict[str, str], learning_note: dict[str, str]) -> dict[str, str]:
    return {
        "paper_id": row.get("paper_id", ""),
        "pmid": row.get("pmid", ""),
        "title": row.get("title", ""),
        "evidence_tier": decision["evidence_tier"],
        "evidence_type": decision["evidence_type"],
        "directness": decision["directness"],
        "target_centrality": decision["target_centrality"],
        "evidence_summary": decision["evidence_summary"],
        "supporting_text_locator": decision["supporting_text_locator"],
        "query_feedback_signal": decision["query_feedback_signal"],
        "review_confidence": decision["review_confidence"],
        "retention_role": decision["retention_role"],
        "scientific_note": learning_note["scientific_note"],
        "topic_learning_signal": learning_note["topic_learning_signal"],
        "next_query_implication": learning_note["next_query_implication"],
    }


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python3 tools/fulltext/heuristic_fulltext_rescue_pass.py <run_id>")
        return 1

    run_id = sys.argv[1].strip()
    run_dir = RUNS_DIR / run_id
    artifacts_dir = active_artifacts_dir(run_dir)
    fulltext_path = artifacts_dir / "fulltext_review" / "fulltext_review.csv"
    evidence_path = artifacts_dir / "fulltext_review" / "evidence_extraction.csv"
    rescue_path = artifacts_dir / "fulltext_review" / "fulltext_rescue.csv"
    rules_path = artifacts_dir / "fulltext_review" / "fulltext_review_rules.md"

    if not fulltext_path.exists():
        print(f"Full-text review table not found: {fulltext_path}")
        return 1
    if not rules_path.exists():
        print(
            "Full-text review rules not found. Run "
            f"`python3 tools/fulltext/generate_fulltext_review_rules.py {run_id}` before rescue review."
        )
        return 1

    profile = build_review_profile(run_dir)
    pass_number = active_pass_number(run_dir) or 1
    rows = load_rows(fulltext_path)
    evidence_by_id = {row.get("paper_id", ""): row for row in load_rows(evidence_path)}
    updated_rows: list[dict[str, str]] = []
    evidence_rows: list[dict[str, str]] = []
    rescue_rows: list[dict[str, str]] = []
    reviewed_drop_count = 0
    overturned_count = 0

    for row in rows:
        original_decision = row.get("fulltext_decision", "").strip()
        if original_decision != "drop":
            updated_rows.append(row)
            existing_evidence = evidence_by_id.get(row.get("paper_id", ""))
            if existing_evidence:
                evidence_rows.append(existing_evidence)
            continue

        reviewed_drop_count += 1
        original_rationale = row.get("fulltext_rationale", "")
        raw_text = load_json_text(row.get("normalized_path", ""))
        title = row.get("title", "")
        rescue_decision = classify_paper(title, raw_text, profile)
        learning_note = paper_learning_note(title, raw_text, rescue_decision, profile)
        final_decision = rescue_decision["fulltext_decision"]
        positive_signal_found = "yes" if final_decision == "keep" else "no"
        combined = f"{title.lower()}\n{raw_text}"
        negative_signal_overridden = (
            "yes"
            if final_decision == "keep" and matched_terms(combined, hard_negative_terms(profile))
            else "no"
        )

        if final_decision == "keep":
            overturned_count += 1
            for field in FULLTEXT_FIELDS:
                if field in rescue_decision:
                    row[field] = rescue_decision[field]
        updated_rows.append(row)
        evidence_rows.append(evidence_row_from_decision(row, rescue_decision, learning_note))
        rescue_rows.append(
            {
                "paper_id": row.get("paper_id", ""),
                "pmid": row.get("pmid", ""),
                "pmcid": row.get("pmcid", ""),
                "doi": row.get("doi", ""),
                "title": title,
                "normalized_source_type": row.get("normalized_source_type", ""),
                "normalized_path": row.get("normalized_path", ""),
                "original_fulltext_decision": "drop",
                "original_fulltext_rationale": original_rationale,
                "rescue_decision": "overturn_to_keep" if final_decision == "keep" else "confirm_drop",
                "final_fulltext_decision": final_decision,
                "rescue_rationale": rescue_decision["fulltext_rationale"],
                "positive_signal_found": positive_signal_found,
                "negative_signal_overridden": negative_signal_overridden,
                "supporting_text_locator": rescue_decision["supporting_text_locator"],
                "review_confidence": rescue_decision["review_confidence"],
            }
        )

    write_rows(fulltext_path, FULLTEXT_FIELDS, updated_rows)
    write_rows(evidence_path, EVIDENCE_FIELDS, evidence_rows)
    write_rows(rescue_path, RESCUE_FIELDS, rescue_rows)
    record_fulltext_read_state(run_dir, pass_number, fulltext_path, evidence_path)
    print(
        f"Full-text rescue reviewed {reviewed_drop_count} first-pass drops at {rescue_path}: "
        f"overturn_to_keep={overturned_count}, confirm_drop={reviewed_drop_count - overturned_count}; "
        "updated fulltext_review.csv and evidence_extraction.csv."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
