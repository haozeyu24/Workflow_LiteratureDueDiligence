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
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from pass_archive import active_artifacts_dir, active_pass_number, run_input_path

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

PROTEIN_LEVEL_CLAIM_TERMS = {
    "abundance",
    "accumulation",
    "acetylation",
    "chaperone",
    "degradation",
    "folding",
    "half-life",
    "import",
    "localization",
    "modification",
    "nuclear",
    "phosphorylation",
    "post-translational",
    "proteasome",
    "protein level",
    "protein stability",
    "retention",
    "steady-state protein",
    "subcellular",
    "sumo",
    "sumoylation",
    "turnover",
    "ubiquitin",
    "ubiquitination",
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
    run_brief = load_run_file(run_dir, "run_brief.md")
    run_text = run_brief

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
        run_text,
        (
            "review and synthesis framing",
            "review/synthesis framing",
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


def sentence_windows(title: str, abstract: str) -> list[str]:
    windows = [title.lower()] if title else []
    for part in re.split(r"(?<=[.!?])\s+", abstract):
        cleaned = " ".join(part.lower().split())
        if cleaned:
            windows.append(cleaned)
    return windows


def has_claim_shaped_positive_signal(
    title: str,
    abstract: str,
    profile: ReviewProfile,
) -> bool:
    for window in sentence_windows(title, abstract):
        primary_matches = matched_terms(window, profile.primary_terms)
        mechanism_matches = matched_terms(window, profile.mechanism_terms)
        outcome_matches = matched_terms(window, profile.outcome_terms)
        protein_claim_matches = matched_terms(window, PROTEIN_LEVEL_CLAIM_TERMS)
        if primary_matches and mechanism_matches and (outcome_matches or protein_claim_matches):
            return True
    return False


def detect_run_mode(run_dir: Path) -> str:
    """Compatibility hook for older callers; all reusable logic is generic."""
    _ = build_review_profile(run_dir)
    return "generic"


def classify_row(
    row: dict[str, str],
    profile: ReviewProfile | str,
    *,
    learning_probe: bool = False,
) -> dict[str, str]:
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
    has_claim_shaped_signal = has_claim_shaped_positive_signal(title, abstract, profile)

    if has_direct_claim or has_claim_shaped_signal:
        return {
            "first_pass_decision": "include",
            "first_pass_rationale": "Title/abstract contains a claim-shaped positive signal linking primary run entities to declared mechanism/evidence terms and protein-level outcome language; generic exclusion terms are treated as background rather than a veto.",
            "first_pass_confidence": "high",
            "topic_match_type": "direct",
            "synthesis_role": "none",
        }

    if has_authorized_comparator_claim:
        return {
            "first_pass_decision": "include",
            "first_pass_rationale": "Title/abstract matches primary run terms plus authorized comparator context, declared mechanism/evidence terms, and required outcome terms.",
            "first_pass_confidence": "medium",
            "topic_match_type": "indirect",
            "synthesis_role": "none",
        }

    if has_review_frame_claim:
        return {
            "first_pass_decision": "include",
            "first_pass_rationale": "Title/abstract matches primary run terms, declared evidence terms, required outcome terms, and a review-frame retention need.",
            "first_pass_confidence": "medium",
            "topic_match_type": "indirect",
            "synthesis_role": "foundational_background",
        }

    if review_paper and primary_matches and (mechanism_matches or outcome_matches) and review_frame_matches:
        return {
            "first_pass_decision": "include",
            "first_pass_rationale": "Review article overlaps primary run entities plus declared evidence/outcome terms and supports the review frame.",
            "first_pass_confidence": "medium",
            "topic_match_type": "background_only",
            "synthesis_role": "field_synthesis",
        }

    learning_probe_signal_count = sum(
        bool(matches)
        for matches in (
            mechanism_matches,
            outcome_matches,
            comparator_matches,
            review_frame_matches,
        )
    )
    if learning_probe and primary_matches and outcome_matches and learning_probe_signal_count >= 2:
        return {
            "first_pass_decision": "include",
            "first_pass_rationale": "Initial PMC-learning pass is recall-friendly but claim-shaped: title/abstract matches primary run entities, required outcome terms, and at least one additional declared mechanism, comparator, or review-frame signal.",
            "first_pass_confidence": "low",
            "topic_match_type": "indirect",
            "synthesis_role": "none",
        }

    if exclusion_matches:
        return {
            "first_pass_decision": "exclude",
            "first_pass_rationale": "Matches run-specific exclusion or deferred-context terms without enough primary objective evidence.",
            "first_pass_confidence": "medium",
            "topic_match_type": "background_only",
            "synthesis_role": "none",
        }

    return {
        "first_pass_decision": "exclude",
        "first_pass_rationale": "Title/abstract does not show the required entity plus mechanism/evidence plus outcome claim shape.",
        "first_pass_confidence": "medium",
        "topic_match_type": "background_only",
        "synthesis_role": "none",
    }


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python3 tools/abstract_triage/heuristic_abstract_triage_first_pass.py <run_id>")
        return 1

    run_id = sys.argv[1].strip()
    run_dir = RUNS_DIR / run_id
    review_path = active_artifacts_dir(run_dir) / "abstract_triage" / "first_pass.csv"
    if not review_path.exists():
        print(f"Abstract review table not found: {review_path}")
        return 1
    rules_path = active_artifacts_dir(run_dir) / "abstract_triage" / "abstract_review_rules.md"
    if not rules_path.exists():
        print(
            "Abstract review rules not found. Run "
            f"`python3 tools/abstract_triage/generate_abstract_review_rules.py {run_id}` before triage."
        )
        return 1

    profile = build_review_profile(run_dir)

    with review_path.open(encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        rows = list(reader)

    include_count = 0
    exclude_count = 0
    review_includes = 0
    learning_probe = (active_pass_number(run_dir) or 1) == 1
    for row in rows:
        decision = classify_row(row, profile, learning_probe=learning_probe)
        row["first_pass_decision"] = decision["first_pass_decision"]
        row["first_pass_rationale"] = decision["first_pass_rationale"]
        row["first_pass_confidence"] = decision["first_pass_confidence"]
        row["topic_match_type"] = decision["topic_match_type"]
        row["triage_actor"] = "agent"
        row["synthesis_role"] = decision["synthesis_role"]
        if decision["first_pass_decision"] == "include":
            include_count += 1
            if decision["synthesis_role"] != "none":
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
