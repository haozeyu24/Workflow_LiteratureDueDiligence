#!/usr/bin/env python3

from __future__ import annotations

import csv
import re
import sys
from collections import Counter
from pathlib import Path

from pass_archive import active_artifacts_dir, load_all_pass_csv, run_input_path


WORKFLOW_ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = WORKFLOW_ROOT / "runs"

FIELDS = [
    "paper_id",
    "pmid",
    "doi",
    "title",
    "year",
    "publication_types",
    "priority",
    "shortlist_decision",
    "evidence_category",
    "learned_criteria_matched",
    "shortlist_rationale",
    "source_query",
    "abstract_reviewer2_decision",
    "promotion_decision",
]

LEARNED_FIELDS = [
    "direct_mechanisms",
    "supporting_mechanisms",
    "retained_keyword_families",
    "missing_keyword_families",
]

NOISE_FIELDS = [
    "noise_keyword_families",
    "recommended_abstract_rule_changes",
]

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
    "cell",
    "cells",
    "could",
    "data",
    "effect",
    "factor",
    "from",
    "gene",
    "genes",
    "have",
    "into",
    "mechanism",
    "mechanisms",
    "model",
    "models",
    "other",
    "paper",
    "papers",
    "protein",
    "related",
    "review",
    "role",
    "study",
    "that",
    "the",
    "their",
    "these",
    "this",
    "through",
    "using",
    "with",
    "would",
}


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    return list(csv.DictReader(path.open(encoding="utf-8")))


def load_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def parse_config(path: Path) -> dict[str, str]:
    config: dict[str, str] = {}
    if not path.exists():
        return config
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


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def clean_phrase(value: str) -> str:
    value = re.sub(r"\([^)]*\)", " ", value)
    value = re.sub(r"[^A-Za-z0-9:/+_. -]+", " ", value)
    value = " ".join(value.split()).strip(" .,:;-").lower()
    if not value or len(value) < 3 or value in STOPWORDS:
        return ""
    return value


def split_phrases(value: str) -> list[str]:
    phrases: list[str] = []
    for part in re.split(r"[;\n|]+", value):
        phrase = clean_phrase(part)
        if phrase:
            phrases.append(phrase)
    return phrases


def tokens(value: str) -> list[str]:
    return [
        token
        for token in re.findall(r"[A-Za-z][A-Za-z0-9+/-]{2,}", value.lower())
        if token not in STOPWORDS
    ]


def dominant_run_terms(run_dir: Path, limit: int = 24) -> list[str]:
    text = "\n".join(
        load_text(run_input_path(run_dir, name))
        for name in ("instruction.md", "topic.md", "constraints.md")
    )
    counts = Counter(tokens(text))
    return [token for token, _count in counts.most_common(limit)]


def feedback_terms(feedback: dict[str, str], fields: list[str]) -> list[str]:
    output: list[str] = []
    for field in fields:
        output.extend(split_phrases(feedback.get(field, "")))
    seen: set[str] = set()
    deduped: list[str] = []
    for term in output:
        if term not in seen:
            seen.add(term)
            deduped.append(term)
    return deduped


def text_matches(text: str, phrases: list[str]) -> list[str]:
    normalized = text.lower()
    matched: list[str] = []
    for phrase in phrases:
        phrase_tokens = tokens(phrase)
        if phrase in normalized:
            matched.append(phrase)
        elif phrase_tokens and all(token in normalized for token in phrase_tokens[:4]):
            matched.append(phrase)
    return matched


def classify(
    row: dict[str, str],
    run_terms: list[str],
    learned_terms: list[str],
    noise_terms: list[str],
) -> dict[str, str]:
    text = f"{row.get('title', '')}\n{row.get('abstract', '')}\n{row.get('source_query', '')}"
    learned_matches = text_matches(text, learned_terms)
    run_matches = text_matches(text, run_terms)
    noise_matches = text_matches(text, noise_terms)
    promotion = row.get("promotion_decision", "")

    if noise_matches and not learned_matches:
        return {
            "priority": "exclude",
            "shortlist_decision": "do_not_request",
            "evidence_category": "noise",
            "learned_criteria_matched": "; ".join(noise_matches[:8]),
            "shortlist_rationale": "Do not request PDF: title/abstract/source query primarily matches noise criteria learned from PMC full text.",
        }

    if promotion != "advance_to_import":
        return {
            "priority": "exclude",
            "shortlist_decision": "do_not_request",
            "evidence_category": "noise",
            "learned_criteria_matched": "not advanced by abstractReviewer2",
            "shortlist_rationale": "Do not request PDF: paper was not advanced to full-text import by abstractReviewer2.",
        }

    if len(learned_matches) >= 2 and run_matches:
        return {
            "priority": "high",
            "shortlist_decision": "request_pdf",
            "evidence_category": "strong_learned_match",
            "learned_criteria_matched": "; ".join((learned_matches + run_matches)[:10]),
            "shortlist_rationale": "Request PDF: title/abstract matches multiple PMC-learned criteria plus run-objective terms.",
        }

    if learned_matches:
        return {
            "priority": "medium",
            "shortlist_decision": "request_pdf",
            "evidence_category": "possible_learned_match",
            "learned_criteria_matched": "; ".join(learned_matches[:10]),
            "shortlist_rationale": "Request PDF if capacity allows: title/abstract matches PMC-learned criteria but with limited specificity.",
        }

    if run_matches and not noise_matches:
        return {
            "priority": "low",
            "shortlist_decision": "defer_pdf",
            "evidence_category": "access_uncertain",
            "learned_criteria_matched": "; ".join(run_matches[:8]),
            "shortlist_rationale": "Defer PDF: paper matches run terms but lacks explicit PMC-learned mechanism criteria in title/abstract.",
        }

    return {
        "priority": "exclude",
        "shortlist_decision": "do_not_request",
        "evidence_category": "noise",
        "learned_criteria_matched": "no learned criterion matched",
        "shortlist_rationale": "Do not request PDF: title/abstract does not match the final PMC-learned criteria strongly enough.",
    }


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python3 scripts/build_pdf_download_shortlist.py <run_id>")
        return 1

    run_id = sys.argv[1].strip()
    run_dir = RUNS_DIR / run_id
    artifacts_dir = active_artifacts_dir(run_dir)
    metadata_path = artifacts_dir / "metadata_collection" / "paper_manifest.csv"
    review2_path = artifacts_dir / "abstract_review" / "abstract_review2.csv"
    queue_path = artifacts_dir / "fulltext_import" / "manual_pdf_queue.csv"
    output_path = artifacts_dir / "fulltext_import" / "pdf_download_shortlist.csv"
    config = parse_config(run_input_path(run_dir, "run_config.md"))
    min_big_workflow_loops = max(2, config_int(config, "min_big_workflow_loops", 2))

    if not queue_path.exists():
        print(f"Manual PDF queue not found: {queue_path}")
        return 1
    feedback_rows = load_all_pass_csv(run_dir, "artifacts/fulltext_review/pmc_mechanism_feedback.csv")
    if not feedback_rows:
        print("PMC mechanism feedback not found in pass artifacts.")
        return 1
    feedback = feedback_rows[-1] if feedback_rows else {}
    if len(feedback_rows) < min_big_workflow_loops:
        print(
            "Refusing to build PDF shortlist until the minimum big workflow loop count "
            f"is satisfied ({len(feedback_rows)}/{min_big_workflow_loops} PMC-feedback passes)."
        )
        return 1
    if feedback.get("pdf_deferral_decision", "").strip() != "final_pdf_pass":
        print("Refusing to build PDF shortlist until latest PMC feedback is final_pdf_pass.")
        return 1

    metadata_by_id = {row.get("paper_id", ""): row for row in load_csv(metadata_path)}
    review2_by_id = {row.get("paper_id", ""): row for row in load_csv(review2_path)}
    queue_rows = load_csv(queue_path)
    run_terms = dominant_run_terms(run_dir)
    learned_terms = feedback_terms(feedback, LEARNED_FIELDS)
    noise_terms = feedback_terms(feedback, NOISE_FIELDS)

    if not learned_terms:
        print("PMC mechanism feedback has no learned criteria for PDF scoring.")
        return 1

    output_rows: list[dict[str, str]] = []
    for queue_row in queue_rows:
        paper_id = queue_row.get("paper_id", "")
        metadata = metadata_by_id.get(paper_id, {})
        review2 = review2_by_id.get(paper_id, {})
        base = {
            "paper_id": paper_id,
            "pmid": queue_row.get("pmid", ""),
            "doi": queue_row.get("doi", ""),
            "title": queue_row.get("title", ""),
            "year": metadata.get("year", ""),
            "publication_types": metadata.get("publication_types", ""),
            "source_query": metadata.get("source_query", ""),
            "abstract_reviewer2_decision": review2.get("abstract_reviewer2_decision", ""),
            "promotion_decision": review2.get("promotion_decision", ""),
            "abstract": metadata.get("abstract", ""),
        }
        classification = classify(base, run_terms, learned_terms, noise_terms)
        output_rows.append(
            {
                "paper_id": base["paper_id"],
                "pmid": base["pmid"],
                "doi": base["doi"],
                "title": base["title"],
                "year": base["year"],
                "publication_types": base["publication_types"],
                "priority": classification["priority"],
                "shortlist_decision": classification["shortlist_decision"],
                "evidence_category": classification["evidence_category"],
                "learned_criteria_matched": classification["learned_criteria_matched"],
                "shortlist_rationale": classification["shortlist_rationale"],
                "source_query": base["source_query"],
                "abstract_reviewer2_decision": base["abstract_reviewer2_decision"],
                "promotion_decision": base["promotion_decision"],
            }
        )

    priority_order = {"high": 0, "medium": 1, "low": 2, "exclude": 3}
    output_rows.sort(key=lambda row: (priority_order.get(row["priority"], 9), row["year"] or "0000", row["title"]))
    write_csv(output_path, output_rows)

    counts: dict[str, int] = {}
    for row in output_rows:
        key = f"{row['priority']}:{row['shortlist_decision']}"
        counts[key] = counts.get(key, 0) + 1
    print(f"Wrote PDF download shortlist with {len(output_rows)} rows to {output_path}")
    print("Counts: " + ", ".join(f"{key}={value}" for key, value in sorted(counts.items())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
