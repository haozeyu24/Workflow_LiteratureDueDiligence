#!/usr/bin/env python3

from __future__ import annotations

import csv
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from pass_archive import active_artifacts_dir, run_input_path


WORKFLOW_ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = WORKFLOW_ROOT / "runs"

REVIEW_TERMS = {
    "review",
    "systematic review",
    "meta-analysis",
    "literature review",
    "narrative review",
    "expert opinion",
    "perspective",
}

STOPWORDS = {
    "about",
    "after",
    "also",
    "and",
    "are",
    "because",
    "been",
    "between",
    "both",
    "but",
    "can",
    "context",
    "data",
    "define",
    "does",
    "evidence",
    "from",
    "goal",
    "has",
    "have",
    "how",
    "include",
    "into",
    "its",
    "may",
    "mechanism",
    "mechanisms",
    "must",
    "not",
    "objective",
    "only",
    "other",
    "paper",
    "papers",
    "primary",
    "prioritize",
    "relevant",
    "review",
    "run",
    "scope",
    "should",
    "specific",
    "study",
    "that",
    "the",
    "their",
    "this",
    "through",
    "topic",
    "using",
    "when",
    "where",
    "with",
    "workflow",
}


@dataclass(frozen=True)
class ReviewProfile:
    primary_terms: set[str]
    mechanism_terms: set[str]
    outcome_terms: set[str]
    comparator_terms: set[str]
    exclusion_terms: set[str]
    review_frame_terms: set[str]
    all_terms: set[str]


def sanitize_row_values(row: dict[str, str]) -> None:
    for key, value in list(row.items()):
        if isinstance(value, str):
            row[key] = " ".join(value.split())


def tokens(value: str) -> list[str]:
    return [
        token
        for token in re.findall(r"[A-Za-z][A-Za-z0-9+/-]{2,}", value.lower())
        if token not in STOPWORDS
    ]


def normalize_declared_phrase(value: str) -> str:
    phrase = re.sub(r"[^a-z0-9+/-]+", " ", value.lower())
    return " ".join(token for token in phrase.split() if token not in STOPWORDS)


def atomic_identifier_terms(value: str) -> set[str]:
    atoms: set[str] = set()
    for token in re.findall(r"[A-Za-z][A-Za-z0-9+/-]{1,}", value):
        if token.lower() in STOPWORDS:
            continue
        if re.search(r"[A-Z]{2,}|\d|[-+/]", token):
            atoms.add(token.lower())
    return atoms


def declared_terms(value: str) -> set[str]:
    found: set[str] = set()
    for raw_part in re.split(r"[,;\n|]+", value):
        part = raw_part.strip()
        if not part:
            continue
        phrase = normalize_declared_phrase(part)
        if not phrase:
            continue
        phrase_tokens = phrase.split()
        if len(phrase_tokens) == 1:
            found.add(phrase)
            continue
        found.add(phrase)
        found.update(atomic_identifier_terms(part))
    return found


def load_run_file(run_dir: Path, filename: str) -> str:
    path = run_input_path(run_dir, filename)
    return path.read_text(encoding="utf-8") if path.exists() else ""


def section_terms(text: str, labels: tuple[str, ...]) -> set[str]:
    found: set[str] = set()
    label_pattern = "|".join(re.escape(label) for label in labels)
    pattern = re.compile(
        rf"(?im)^\s*[-*]?\s*(?:{label_pattern})\s*:\s*(.+?)(?=^\s*[-*]?\s*[a-z][a-z0-9 /_-]{{2,}}\s*:|\Z)",
        re.S,
    )
    for match in pattern.finditer(text):
        found.update(declared_terms(match.group(1)))
    return found


def frequent_terms(text: str, limit: int = 60) -> set[str]:
    return {term for term, _ in Counter(tokens(text)).most_common(limit)}


def build_review_profile(run_dir: Path) -> ReviewProfile:
    instruction = load_run_file(run_dir, "instruction.md")
    topic = load_run_file(run_dir, "topic.md")
    constraints = load_run_file(run_dir, "constraints.md")
    review_frame = load_run_file(run_dir, "review_frame.md")
    run_text = "\n".join([instruction, topic, constraints])

    primary_terms = section_terms(
        run_text,
        (
            "primary entities",
            "primary entity",
            "entities",
            "targets",
            "genes",
            "proteins",
            "drugs",
            "pathways",
            "systems",
        ),
    )
    mechanism_terms = section_terms(
        run_text,
        (
            "declared mechanism classes for pubmed retrieval",
            "declared mechanism classes",
            "mechanism classes",
            "evidence goal",
            "desired evidence types",
            "evidence types",
        ),
    )
    outcome_terms = section_terms(
        run_text,
        (
            "declared outcomes or required evidence claims",
            "declared outcomes",
            "required evidence claims",
            "outcome terms",
            "outcomes",
            "response variables",
            "phenotypes",
            "endpoints",
        ),
    )
    comparator_terms = section_terms(
        run_text,
        (
            "authorized comparator entities or systems",
            "authorized comparator",
            "allowed comparator scope",
            "comparators",
            "model systems",
        ),
    )
    exclusion_terms = section_terms(
        run_text,
        (
            "exclusions",
            "exclude",
            "deprioritize",
            "durable exclusions",
            "adjacent biology deferred from first-pass retrieval",
            "evidence insufficient by itself",
            "evidence that should not be treated as sufficient",
            "evidence that should reduce ambiguity by triggering exclusion or demotion",
        ),
    )
    review_frame_terms = section_terms(
        review_frame,
        (
            "parent field",
            "introduction background scope",
            "foundational concepts or older terminology to preserve",
            "review-architecture paper types worth retaining",
            "perspective questions",
            "controversies or unresolved gaps",
        ),
    )

    fallback_terms = frequent_terms(run_text)
    if not primary_terms:
        primary_terms = set(list(fallback_terms)[:20])
    if not mechanism_terms:
        mechanism_terms = fallback_terms - primary_terms
    if not outcome_terms:
        outcome_terms = set(mechanism_terms)

    all_terms = primary_terms | mechanism_terms | outcome_terms | comparator_terms | review_frame_terms
    return ReviewProfile(
        primary_terms=primary_terms,
        mechanism_terms=mechanism_terms,
        outcome_terms=outcome_terms,
        comparator_terms=comparator_terms,
        exclusion_terms=exclusion_terms,
        review_frame_terms=review_frame_terms,
        all_terms=all_terms,
    )


def matched_terms(text: str, candidates: set[str]) -> list[str]:
    normalized = text.lower()
    matches: list[str] = []
    for term in sorted(candidates, key=lambda value: (-len(value), value)):
        cleaned_term = " ".join(term.lower().split())
        if not cleaned_term:
            continue
        if " " in cleaned_term:
            if cleaned_term in normalized:
                matches.append(cleaned_term)
            continue
        if re.search(rf"(?<![A-Za-z0-9+/-]){re.escape(cleaned_term)}(?![A-Za-z0-9+/-])", normalized):
            matches.append(cleaned_term)
    return matches


def is_review_paper(publication_types: str, text: str) -> bool:
    normalized_types = publication_types.lower()
    normalized_text = text.lower()
    return "review" in normalized_types or any(term in normalized_text for term in REVIEW_TERMS)


def detect_run_mode(run_dir: Path) -> str:
    """Compatibility hook for older callers; all reusable logic is generic."""
    _ = build_review_profile(run_dir)
    return "generic"


def classify_row(row: dict[str, str], profile: ReviewProfile | str) -> dict[str, str]:
    if isinstance(profile, str):
        raise TypeError("classify_row now requires a ReviewProfile from build_review_profile().")

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
    any_matches = matched_terms(text, profile.all_terms)
    review_paper = is_review_paper(publication_types, text)

    has_direct_claim = bool(primary_matches and mechanism_matches and outcome_matches)
    has_authorized_comparator_claim = bool(primary_matches and comparator_matches and mechanism_matches and outcome_matches)
    has_review_frame_claim = bool(primary_matches and mechanism_matches and review_frame_matches and outcome_matches)

    if exclusion_matches and not has_direct_claim:
        return {
            "review_decision": "exclude",
            "review_rationale": "Matches run-specific exclusion or deferred-context terms without enough primary objective evidence.",
            "review_confidence": "medium",
            "topic_match_type": "background_only",
            "review_frame_role": "none",
        }

    if has_direct_claim:
        return {
            "review_decision": "include",
            "review_rationale": "Title/abstract matches primary run entities, declared mechanism/evidence terms, and required outcome or evidence-claim terms.",
            "review_confidence": "high",
            "topic_match_type": "direct",
            "review_frame_role": "none",
        }

    if has_authorized_comparator_claim:
        return {
            "review_decision": "include",
            "review_rationale": "Title/abstract matches primary run terms plus authorized comparator context, declared mechanism/evidence terms, and required outcome terms.",
            "review_confidence": "medium",
            "topic_match_type": "indirect",
            "review_frame_role": "none",
        }

    if has_review_frame_claim:
        return {
            "review_decision": "include",
            "review_rationale": "Title/abstract matches primary run terms, declared evidence terms, required outcome terms, and a review-frame retention need.",
            "review_confidence": "medium",
            "topic_match_type": "indirect",
            "review_frame_role": "foundational_background",
        }

    if review_paper and primary_matches and (mechanism_matches or outcome_matches) and review_frame_matches:
        return {
            "review_decision": "include",
            "review_rationale": "Review article overlaps primary run entities plus declared evidence/outcome terms and supports the review frame.",
            "review_confidence": "medium",
            "topic_match_type": "background_only",
            "review_frame_role": "field_synthesis",
        }

    return {
        "review_decision": "exclude",
        "review_rationale": "Title/abstract does not show the required entity plus mechanism/evidence plus outcome claim shape.",
        "review_confidence": "medium",
        "topic_match_type": "background_only",
        "review_frame_role": "none",
    }


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python3 scripts/heuristic_abstract_review.py <run_id>")
        return 1

    run_id = sys.argv[1].strip()
    run_dir = RUNS_DIR / run_id
    review_path = active_artifacts_dir(run_dir) / "abstract_review" / "abstract_review.csv"
    if not review_path.exists():
        print(f"Abstract review table not found: {review_path}")
        return 1

    profile = build_review_profile(run_dir)

    with review_path.open(encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        rows = list(reader)

    include_count = 0
    exclude_count = 0
    review_includes = 0
    for row in rows:
        decision = classify_row(row, profile)
        row["review_decision"] = decision["review_decision"]
        row["review_rationale"] = decision["review_rationale"]
        row["review_confidence"] = decision["review_confidence"]
        row["topic_match_type"] = decision["topic_match_type"]
        row["reviewer_type"] = "agent"
        row["review_frame_role"] = decision["review_frame_role"]
        if decision["review_decision"] == "include":
            include_count += 1
            if decision["review_frame_role"] != "none":
                review_includes += 1
        else:
            exclude_count += 1
        sanitize_row_values(row)

    with review_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(
        f"Updated {review_path}: include={include_count}, exclude={exclude_count}, "
        f"review_frame_retained={review_includes}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
