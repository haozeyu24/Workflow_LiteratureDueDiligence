#!/usr/bin/env python3

from __future__ import annotations

import sys
from pathlib import Path

TOOLS_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS_ROOT / "core"))
from tool_paths import WORKFLOW_ROOT, ensure_tool_paths
ensure_tool_paths()

import csv
import re
import sys
from pathlib import Path

from heuristic_abstract_triage_first_pass import (
    build_review_profile,
    EVIDENCE_CLAIM_TERMS,
    has_claim_shaped_positive_signal,
    is_review_paper,
    matched_terms,
)
from pass_archive import active_artifacts_dir, active_pass_number
from workflow_db import prior_fulltext_drop_paper_ids, record_abstract_triage_decisions

RUNS_DIR = WORKFLOW_ROOT / "runs"


def sanitize_row_values(row: dict[str, str]) -> None:
    for key, value in list(row.items()):
        if isinstance(value, str):
            row[key] = " ".join(value.split())


def has_rescue_signal(row: dict[str, str], profile) -> tuple[bool, str, str, str]:
    title = row.get("title", "") or ""
    abstract = row.get("abstract", "") or ""
    publication_types = row.get("publication_types", "") or ""
    text = f"{title}\n{abstract}".lower()

    primary_matches = matched_terms(text, profile.primary_terms)
    mechanism_matches = matched_terms(text, profile.mechanism_terms)
    outcome_matches = matched_terms(text, profile.outcome_terms)
    comparator_matches = matched_terms(text, profile.comparator_terms)
    exclusion_matches = matched_terms(text, profile.exclusion_terms)
    review_frame_matches = matched_terms(text, profile.review_frame_terms)

    mechanism_signal = bool(mechanism_matches and outcome_matches)
    claim_shaped_signal = has_claim_shaped_positive_signal(title, abstract, profile)
    comparator_signal = bool(comparator_matches and (mechanism_matches or outcome_matches))
    review_signal = (
        is_review_paper(publication_types, text)
        and primary_matches
        and (mechanism_matches or outcome_matches or review_frame_matches)
    )

    if exclusion_matches and not (primary_matches and (mechanism_signal or claim_shaped_signal)):
        return (
            False,
            "high",
            "Confirmed exclude: exclusion/deferred-context terms dominate and no primary mechanistic rescue signal is present.",
            "none",
        )

    if primary_matches and (mechanism_signal or claim_shaped_signal):
        return (
            True,
            "medium",
            "Rescued for import: excluded abstract has a claim-shaped positive signal linking primary run terms to declared mechanism/evidence terms and declared outcome or generic evidence-claim language.",
            "none",
        )

    if primary_matches and comparator_signal:
        return (
            True,
            "low",
            "Rescued for import: excluded abstract has primary terms plus authorized comparator context with mechanism or outcome signal.",
            "none",
        )

    if review_signal:
        return (
            True,
            "low",
            "Rescued for import: excluded review/context paper has primary terms and plausible declared evidence or review-frame value.",
            "field_synthesis",
        )

    return (
        False,
        "medium",
        "Confirmed exclude: rescue review did not find a high-value missed claim-shaped, comparator, or review-frame signal.",
        "none",
    )


def sentence_windows(title: str, abstract: str) -> list[str]:
    windows = [title.lower()] if title else []
    for part in re.split(r"(?<=[.!?])\s+", abstract):
        cleaned = " ".join(part.lower().split())
        if cleaned:
            windows.append(cleaned)
    return windows


def final_signal_terms(candidates: set[str], *blocked_sets: set[str]) -> set[str]:
    blocked = set().union(*blocked_sets) if blocked_sets else set()
    return {
        term
        for term in candidates
        if term not in blocked
        and len(term.strip()) >= 4
    }


def has_final_pass_signal(row: dict[str, str], profile) -> tuple[bool, str, str, str]:
    title = row.get("title", "") or ""
    abstract = row.get("abstract", "") or ""
    publication_types = row.get("publication_types", "") or ""
    text = f"{title}\n{abstract}".lower()

    mechanism_terms = final_signal_terms(profile.mechanism_terms, profile.primary_terms)
    outcome_terms = final_signal_terms(profile.outcome_terms, profile.primary_terms, profile.mechanism_terms)
    comparator_terms = final_signal_terms(profile.comparator_terms, profile.primary_terms)

    exclusion_matches = matched_terms(text, profile.exclusion_terms)
    review_frame_matches = matched_terms(text, profile.review_frame_terms)
    windows = sentence_windows(title, abstract)

    direct_windows: list[str] = []
    contextual_windows: list[str] = []
    comparator_windows: list[str] = []
    for window in windows:
        primary_matches = matched_terms(window, profile.primary_terms)
        if not primary_matches:
            continue
        mechanism_matches = matched_terms(window, mechanism_terms)
        outcome_matches = matched_terms(window, outcome_terms)
        evidence_claim_matches = matched_terms(window, EVIDENCE_CLAIM_TERMS)
        comparator_matches = matched_terms(window, comparator_terms)
        if mechanism_matches and (outcome_matches or evidence_claim_matches):
            direct_windows.append(window)
        elif evidence_claim_matches and (mechanism_matches or outcome_matches):
            contextual_windows.append(window)
        if comparator_matches and (mechanism_matches or outcome_matches or evidence_claim_matches):
            comparator_windows.append(window)

    named_claim_signal = bool(direct_windows)
    contextual_claim_signal = bool(contextual_windows)
    comparator_claim_signal = bool(comparator_windows)
    review_signal = (
        is_review_paper(publication_types, text)
        and bool(direct_windows)
        and review_frame_matches
    )

    if exclusion_matches and not (named_claim_signal or comparator_claim_signal):
        return (
            False,
            "high",
            "Stopped in learned final pass: exclusion/deferred-context terms remain stronger than any direct claim-shaped prompt-fit signal.",
            "none",
        )

    if named_claim_signal:
        return (
            True,
            "high",
            "Advanced in learned final pass: abstract ties primary run terms to declared mechanism/evidence and declared outcome or generic evidence-claim language.",
            "none",
        )

    if contextual_claim_signal:
        return (
            True,
            "medium",
            "Advanced in learned final pass: abstract ties primary run terms to generic evidence-claim language plus a declared evidence dimension.",
            "none",
        )

    if comparator_claim_signal:
        return (
            True,
            "medium",
            "Advanced in learned final pass: abstract has authorized comparator context plus primary, mechanism, and outcome signals.",
            "none",
        )

    if review_signal:
        return (
            True,
            "medium",
            "Advanced in learned final pass: review/context paper has explicit primary, mechanism, outcome, and review-frame value.",
            "field_synthesis",
        )

    return (
        False,
        "medium",
        "Stopped in learned final pass: abstract lacks a claim-shaped connection among primary objective, declared evidence, and outcome/relevance terms.",
        "none",
    )


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python3 tools/abstract_triage/heuristic_abstract_triage_second_pass.py <run_id>")
        return 1

    run_id = sys.argv[1].strip()
    run_dir = RUNS_DIR / run_id
    review2_path = active_artifacts_dir(run_dir) / "abstract_triage" / "second_pass.csv"
    if not review2_path.exists():
        print(f"Abstract triage second pass table not found: {review2_path}")
        return 1
    rules_path = active_artifacts_dir(run_dir) / "abstract_triage" / "abstract_review_rules.md"
    if not rules_path.exists():
        print(
            "Abstract review rules not found. Run "
            f"`python3 tools/abstract_triage/generate_abstract_review_rules.py {run_id}` before triage."
        )
        return 1
    profile = build_review_profile(run_dir)
    pass_number = active_pass_number(run_dir) or 1
    prior_fulltext_drops = prior_fulltext_drop_paper_ids(run_dir, before_pass=pass_number)

    with review2_path.open(encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        rows = list(reader)

    advance_count = 0
    stop_count = 0
    rescued_count = 0
    prior_fulltext_drop_stops = 0
    final_pass_adjudications = 0
    for row in rows:
        reviewer1_decision = row.get("first_pass_decision", "")
        paper_id = (row.get("paper_id") or "").strip()

        if reviewer1_decision == "include" and pass_number >= 2:
            final_pass_adjudications += 1
            keep, confidence, rationale, synthesis_role = has_final_pass_signal(row, profile)
            if paper_id in prior_fulltext_drops and not keep:
                prior_fulltext_drop_stops += 1
                rationale = (
                    rationale
                    + " Prior pass full-text review already classified this paper as low-yield/drop, so it is not reimported without a stronger active-pass rescue signal."
                )
            if keep:
                second_pass_decision = "confirm_include"
                promotion = "advance_to_import"
            else:
                second_pass_decision = "overturn_to_exclude"
                promotion = "stop"
        elif reviewer1_decision == "include":
            second_pass_decision = "confirm_include"
            promotion = "advance_to_import"
            confidence = row.get("first_pass_confidence", "").strip() or "medium"
            rationale = "Confirmed include without relitigating first-pass judgment; this pass is a rescue review for first-pass excludes."
            synthesis_role = row.get("synthesis_role", "").strip() or "none"
        else:
            rescue, confidence, rationale, synthesis_role = has_rescue_signal(row, profile)
            if paper_id in prior_fulltext_drops and rescue:
                final_keep, final_confidence, final_rationale, final_role = has_final_pass_signal(row, profile)
                if final_keep:
                    confidence = final_confidence
                    rationale = (
                        final_rationale
                        + " Prior full-text drop is overridden because the active abstract now has a clear learned final-pass rescue signal."
                    )
                    synthesis_role = final_role
                else:
                    rescue = False
                    confidence = final_confidence
                    rationale = (
                        final_rationale
                        + " Prior pass full-text review already classified this paper as low-yield/drop, so it is not reimported without a stronger active-pass rescue signal."
                    )
                    synthesis_role = "none"
                    prior_fulltext_drop_stops += 1
            if rescue:
                second_pass_decision = "overturn_to_include"
                promotion = "advance_to_import"
                rescued_count += 1
            else:
                second_pass_decision = "confirm_exclude"
                promotion = "stop"

        row["second_pass_decision"] = second_pass_decision
        row["second_pass_rationale"] = rationale
        row["second_pass_confidence"] = confidence
        row["promotion_decision"] = promotion
        row["synthesis_role"] = synthesis_role
        sanitize_row_values(row)
        if promotion == "advance_to_import":
            advance_count += 1
        else:
            stop_count += 1

    with review2_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            quoting=csv.QUOTE_ALL,
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)

    record_abstract_triage_decisions(run_dir, pass_number, review2_path)
    print(
        f"Updated {review2_path}: advance_to_import={advance_count}, stop={stop_count}, "
        f"rescued_excludes={rescued_count}, final_pass_adjudications={final_pass_adjudications}, "
        f"prior_fulltext_drop_stops={prior_fulltext_drop_stops}, pass={pass_number}; "
        "recorded decisions in workflow_state.sqlite"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
