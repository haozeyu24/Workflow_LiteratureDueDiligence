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
from pathlib import Path

from pass_archive import active_artifacts_dir, run_input_path

RUNS_DIR = WORKFLOW_ROOT / "runs"

PRESCREEN_FIELDS = [
    "prescreen_hint",
    "prescreen_rationale",
    "prescreen_overlap_terms",
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
    "for",
    "from",
    "has",
    "have",
    "how",
    "include",
    "into",
    "its",
    "may",
    "not",
    "only",
    "other",
    "papers",
    "prioritize",
    "related",
    "run",
    "should",
    "that",
    "the",
    "their",
    "this",
    "through",
    "using",
    "when",
    "where",
    "with",
    "workflow",
}


def load_run_text(run_dir: Path) -> str:
    parts: list[str] = []
    for name in ("run_brief.md",):
        path = run_input_path(run_dir, name)
        if path.exists():
            parts.append(path.read_text(encoding="utf-8"))
    return "\n".join(parts)


def tokens(value: str) -> list[str]:
    return [
        token
        for token in re.findall(r"[A-Za-z][A-Za-z0-9-]{2,}", value.lower())
        if token not in STOPWORDS
    ]


def derive_topic_terms(run_dir: Path, limit: int = 80) -> set[str]:
    counts = Counter(tokens(load_run_text(run_dir)))
    return {token for token, _count in counts.most_common(limit)}


def row_overlap_terms(row: dict[str, str], topic_terms: set[str]) -> list[str]:
    text_terms = set(tokens(f"{row.get('title', '')}\n{row.get('abstract', '')}"))
    return sorted(text_terms & topic_terms)


def ensure_fields(fieldnames: list[str]) -> list[str]:
    output = list(fieldnames)
    for field in PRESCREEN_FIELDS:
        if field not in output:
            output.append(field)
    return output


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python3 tools/abstract_triage/prescreen_abstracts.py <run_id>")
        return 1

    run_id = sys.argv[1].strip()
    run_dir = RUNS_DIR / run_id
    review_path = active_artifacts_dir(run_dir) / "abstract_triage" / "first_pass.csv"
    if not review_path.exists():
        print(f"Abstract review table not found: {review_path}")
        return 1

    with review_path.open(encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fieldnames = ensure_fields(reader.fieldnames or [])

    topic_terms = derive_topic_terms(run_dir)
    hinted_count = 0

    for row in rows:
        overlap = row_overlap_terms(row, topic_terms)
        if len(overlap) >= 3:
            row["prescreen_hint"] = "possible_include"
            row["prescreen_rationale"] = (
                "Generic pre-screen found overlap with run instruction/topic terms; "
                "reviewer must still make the schema-bound include/exclude decision."
            )
            row["prescreen_overlap_terms"] = ";".join(overlap[:20])
            hinted_count += 1
        else:
            row["prescreen_hint"] = ""
            row["prescreen_rationale"] = ""
            row["prescreen_overlap_terms"] = ""

    with review_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(
        f"Updated {review_path}: generic possible-include hints={hinted_count}; "
        "first_pass_decision fields were not modified."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
