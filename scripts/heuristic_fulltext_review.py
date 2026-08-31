#!/usr/bin/env python3

from __future__ import annotations

import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

from heuristic_abstract_review import build_review_profile, matched_terms
from pass_archive import active_artifacts_dir, active_pass_number


WORKFLOW_ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = WORKFLOW_ROOT / "runs"

FULLTEXT_FIELDS = [
    "paper_id",
    "pmid",
    "pmcid",
    "doi",
    "title",
    "normalized_source_type",
    "normalized_path",
    "fulltext_decision",
    "fulltext_rationale",
    "mechanistic_relevance",
    "objective_relevance",
    "topic_centrality",
    "review_confidence",
]

EVIDENCE_FIELDS = [
    "paper_id",
    "pmid",
    "title",
    "evidence_tier",
    "evidence_type",
    "directness",
    "target_centrality",
    "evidence_summary",
    "supporting_text_locator",
    "query_feedback_signal",
    "review_confidence",
    "retention_role",
]

FEEDBACK_FIELDS = [
    "loop_id",
    "source_paper_count",
    "direct_mechanisms",
    "supporting_mechanisms",
    "retained_keyword_families",
    "noise_keyword_families",
    "missing_keyword_families",
    "recommended_query_changes",
    "recommended_abstract_rule_changes",
    "pdf_deferral_decision",
    "rationale",
]


def load_json_text(path_text: str) -> str:
    path = Path(path_text)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ""
    raw_text = payload.get("raw_text", "")
    return raw_text.lower() if isinstance(raw_text, str) else ""


def compact_terms(counter: Counter[str], fallback: set[str], limit: int = 12) -> str:
    terms = [term for term, _count in counter.most_common() if useful_feedback_term(term)]
    if not terms:
        terms = [term for term in sorted(fallback, key=lambda value: (-len(value), value)) if useful_feedback_term(term)]
    return "; ".join(terms[:limit])


def useful_feedback_term(term: str) -> bool:
    cleaned = " ".join(term.lower().split())
    if not cleaned:
        return False
    return True


def evidence_windows(title: str, text: str) -> list[tuple[str, str]]:
    windows: list[tuple[str, str]] = [("title", title.lower())] if title else []
    section_title = "full text"
    for raw_line in text.splitlines():
        line = " ".join(raw_line.split())
        if not line:
            continue
        if len(line) <= 120 and not line.endswith("."):
            section_title = line[:80]
        for sentence in re_split_sentences(line):
            if sentence:
                windows.append((section_title, sentence))
    return windows


def re_split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text)
    if len(parts) == 1 and len(text) > 800:
        return [text[index:index + 800] for index in range(0, len(text), 800)]
    return parts


def local_claim_windows(title: str, text: str, profile) -> tuple[list[tuple[str, str, list[str]]], list[tuple[str, str, list[str]]]]:
    direct: list[tuple[str, str, list[str]]] = []
    comparator: list[tuple[str, str, list[str]]] = []
    for locator, window in evidence_windows(title, text):
        primary_hits = matched_terms(window, profile.primary_terms)
        mechanism_hits = matched_terms(window, profile.mechanism_terms)
        outcome_hits = matched_terms(window, profile.outcome_terms)
        comparator_hits = matched_terms(window, profile.comparator_terms)
        if primary_hits and mechanism_hits and outcome_hits:
            direct.append((locator, window, (primary_hits + mechanism_hits + outcome_hits)[:8]))
        elif primary_hits and comparator_hits and mechanism_hits and outcome_hits:
            comparator.append((locator, window, (primary_hits + comparator_hits + mechanism_hits + outcome_hits)[:8]))
    return direct, comparator


def classify_paper(title: str, text: str, profile) -> dict[str, str]:
    combined = f"{title.lower()}\n{text}"
    primary_hits = matched_terms(combined, profile.primary_terms)
    mechanism_hits = matched_terms(combined, profile.mechanism_terms)
    outcome_hits = matched_terms(combined, profile.outcome_terms)
    comparator_hits = matched_terms(combined, profile.comparator_terms)
    exclusion_hits = matched_terms(combined, profile.exclusion_terms)
    review_frame_hits = matched_terms(combined, profile.review_frame_terms)
    direct_windows, comparator_windows = local_claim_windows(title, text, profile)

    if exclusion_hits and not direct_windows:
        return {
            "fulltext_decision": "drop",
            "fulltext_rationale": "Readable full text is dominated by run-specific exclusion or deferred-context signals.",
            "mechanistic_relevance": "low",
            "objective_relevance": "low",
            "topic_centrality": "incidental",
            "review_confidence": "medium",
            "evidence_tier": "exclude",
            "evidence_type": "off_scope_or_deferred_context",
            "directness": "incidental",
            "target_centrality": "incidental",
            "evidence_summary": "Full text does not provide enough primary objective evidence after applying run-specific exclusions.",
            "supporting_text_locator": "matched exclusion/deferred terms: " + ";".join(exclusion_hits[:6]),
            "query_feedback_signal": "tighten_query",
            "retention_role": "exclude",
            "kept": "no",
        }

    if direct_windows:
        locator, _window, local_hits = direct_windows[0]
        return {
            "fulltext_decision": "keep",
            "fulltext_rationale": "A title, sentence, or local section-level window connects primary run entities, declared mechanism/evidence terms, and required outcome terms.",
            "mechanistic_relevance": "high",
            "objective_relevance": "high",
            "topic_centrality": "central",
            "review_confidence": "high",
            "evidence_tier": "direct",
            "evidence_type": "run_declared_mechanism",
            "directness": "direct_target",
            "target_centrality": "central",
            "evidence_summary": "Paper contains direct full-text evidence tied to the run objective and declared evidence class.",
            "supporting_text_locator": f"{locator}: matched " + ";".join(local_hits),
            "query_feedback_signal": "none",
            "retention_role": "direct_mechanistic",
            "kept": "yes",
        }

    if comparator_windows:
        locator, _window, local_hits = comparator_windows[0]
        return {
            "fulltext_decision": "keep",
            "fulltext_rationale": "A local full-text window connects primary run terms, authorized comparator context, declared mechanism/evidence terms, and required outcome terms.",
            "mechanistic_relevance": "medium",
            "objective_relevance": "medium",
            "topic_centrality": "supporting",
            "review_confidence": "medium",
            "evidence_tier": "comparator",
            "evidence_type": "authorized_comparator_context",
            "directness": "same_family_comparator",
            "target_centrality": "supporting",
            "evidence_summary": "Paper supplies comparator or model-system evidence authorized by the run scope.",
            "supporting_text_locator": f"{locator}: matched " + ";".join(local_hits),
            "query_feedback_signal": "none",
            "retention_role": "direct_mechanistic",
            "kept": "yes",
        }

    if primary_hits and mechanism_hits and outcome_hits and review_frame_hits:
        return {
            "fulltext_decision": "keep",
            "fulltext_rationale": "Full text has primary-topic, declared-evidence, and outcome overlap and supports an explicit review-frame retention role.",
            "mechanistic_relevance": "medium",
            "objective_relevance": "medium",
            "topic_centrality": "supporting",
            "review_confidence": "medium",
            "evidence_tier": "background",
            "evidence_type": "review_frame_context",
            "directness": "pathway_or_context",
            "target_centrality": "supporting",
            "evidence_summary": "Paper can support introduction, field synthesis, or perspective framing under the run review frame.",
            "supporting_text_locator": "document-level review-frame match: " + ";".join((primary_hits + mechanism_hits + outcome_hits + review_frame_hits)[:8]),
            "query_feedback_signal": "none",
            "retention_role": "foundational_background",
            "kept": "yes",
        }

    if primary_hits or (mechanism_hits and comparator_hits):
        return {
            "fulltext_decision": "drop",
            "fulltext_rationale": "Readable full text has document-level overlap but no sentence- or local section-level evidence tying the mechanism/evidence claim to the primary entity and required outcome.",
            "mechanistic_relevance": "low",
            "objective_relevance": "medium",
            "topic_centrality": "supporting",
            "review_confidence": "medium",
            "evidence_tier": "background",
            "evidence_type": "weak_or_partial_overlap",
            "directness": "pathway_or_context",
            "target_centrality": "supporting",
            "evidence_summary": "Paper may be contextual but does not clearly satisfy the run's full-text retention threshold.",
            "supporting_text_locator": "matched: " + ";".join((primary_hits + mechanism_hits + comparator_hits)[:8]),
            "query_feedback_signal": "reviewer_calibration",
            "retention_role": "exclude",
            "kept": "no",
        }

    return {
        "fulltext_decision": "drop",
        "fulltext_rationale": "Readable full text does not provide enough evidence for the run objective.",
        "mechanistic_relevance": "low",
        "objective_relevance": "low",
        "topic_centrality": "incidental",
        "review_confidence": "medium",
        "evidence_tier": "exclude",
        "evidence_type": "weak_overlap",
        "directness": "incidental",
        "target_centrality": "incidental",
        "evidence_summary": "Full text lacks sufficient overlap with the run-specific primary entities and declared evidence needs.",
        "supporting_text_locator": "title/full text weak-overlap assessment",
        "query_feedback_signal": "tighten_query",
        "retention_role": "exclude",
        "kept": "no",
    }


def feedback_row(profile, pass_number: int, source_count: int, direct_terms: Counter[str], supporting_terms: Counter[str], noise_terms: Counter[str]) -> dict[str, str]:
    pdf_deferral_decision = "final_pdf_pass" if pass_number >= 2 else "defer_pdfs"
    retained_terms = compact_terms(direct_terms, profile.primary_terms | profile.mechanism_terms)
    supporting = compact_terms(supporting_terms, profile.review_frame_terms | profile.comparator_terms)
    noise = compact_terms(noise_terms, profile.exclusion_terms, limit=10)
    missing = compact_terms(Counter(), profile.mechanism_terms, limit=10)
    return {
        "loop_id": f"loop_{pass_number:03d}",
        "source_paper_count": str(source_count),
        "direct_mechanisms": retained_terms,
        "supporting_mechanisms": supporting,
        "retained_keyword_families": retained_terms,
        "noise_keyword_families": noise,
        "missing_keyword_families": missing,
        "recommended_query_changes": (
            "Keep primary run terms paired with declared mechanism or evidence terms; "
            "use matched retained terms as in-scope anchors and apply noise terms only as safe exclusions."
        ),
        "recommended_abstract_rule_changes": (
            "Require abstract promotion to show primary objective overlap plus declared evidence, "
            "authorized comparator, or explicit review-frame value."
        ),
        "pdf_deferral_decision": pdf_deferral_decision,
        "rationale": (
            f"Pass {pass_number} generic PMC-learning review processed {source_count} normalized full texts. "
            + (
                "Use readable full-text evidence to revise guidance before final PDF access."
                if pdf_deferral_decision == "defer_pdfs"
                else "Minimum learned loop count is satisfied; the run may enter the final PDF-shortlist phase if controller gates pass."
            )
        ),
    }


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python3 scripts/heuristic_fulltext_review.py <run_id>")
        return 1

    run_id = sys.argv[1].strip()
    run_dir = RUNS_DIR / run_id
    profile = build_review_profile(run_dir)
    pass_number = active_pass_number(run_dir) or 1
    artifacts_dir = active_artifacts_dir(run_dir)
    fulltext_path = artifacts_dir / "fulltext_review" / "fulltext_review.csv"
    evidence_path = artifacts_dir / "fulltext_review" / "evidence_extraction.csv"
    feedback_path = artifacts_dir / "fulltext_review" / "pmc_mechanism_feedback.csv"

    if not fulltext_path.exists():
        print(f"Full-text review table not found: {fulltext_path}")
        return 1

    with fulltext_path.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    updated_rows: list[dict[str, str]] = []
    evidence_rows: list[dict[str, str]] = []
    keep_count = 0
    direct_terms: Counter[str] = Counter()
    supporting_terms: Counter[str] = Counter()
    noise_terms: Counter[str] = Counter()

    for row in rows:
        raw_text = load_json_text(row.get("normalized_path", ""))
        title = row.get("title", "")
        decision = classify_paper(title, raw_text, profile)
        combined = f"{title.lower()}\n{raw_text}"

        for field in FULLTEXT_FIELDS:
            if field in decision:
                row[field] = decision[field]
        updated_rows.append(row)
        evidence_rows.append(
            {
                "paper_id": row.get("paper_id", ""),
                "pmid": row.get("pmid", ""),
                "title": title,
                "evidence_tier": decision["evidence_tier"],
                "evidence_type": decision["evidence_type"],
                "directness": decision["directness"],
                "target_centrality": decision["target_centrality"],
                "evidence_summary": decision["evidence_summary"],
                "supporting_text_locator": decision["supporting_text_locator"],
                "query_feedback_signal": decision["query_feedback_signal"],
                "review_confidence": decision["review_confidence"],
                "retention_role": decision["retention_role"],
            }
        )

        if decision["kept"] == "yes":
            keep_count += 1
            for term in matched_terms(combined, profile.primary_terms | profile.mechanism_terms):
                direct_terms[term] += 1
            for term in matched_terms(combined, profile.comparator_terms | profile.review_frame_terms):
                supporting_terms[term] += 1
        else:
            for term in matched_terms(combined, profile.exclusion_terms | profile.all_terms):
                noise_terms[term] += 1

    with fulltext_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FULLTEXT_FIELDS)
        writer.writeheader()
        writer.writerows(updated_rows)

    with evidence_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=EVIDENCE_FIELDS)
        writer.writeheader()
        writer.writerows(evidence_rows)

    with feedback_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FEEDBACK_FIELDS)
        writer.writeheader()
        writer.writerow(feedback_row(profile, pass_number, len(updated_rows), direct_terms, supporting_terms, noise_terms))

    print(
        f"Updated {fulltext_path}: keep={keep_count}, drop={len(updated_rows) - keep_count}; "
        f"wrote {evidence_path} and {feedback_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
