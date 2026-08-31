#!/usr/bin/env python3

from __future__ import annotations

import csv
import sys
from pathlib import Path

from heuristic_abstract_review import build_review_profile, classify_row
from pass_archive import active_artifacts_dir


WORKFLOW_ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = WORKFLOW_ROOT / "runs"


def build_rationale(
    reviewer1_decision: str,
    reviewer2_decision: str,
    predicted_decision: str,
    base_rationale: str,
) -> str:
    if reviewer2_decision == "confirm_include":
        return f"Confirmed include: {base_rationale}"
    if reviewer2_decision == "confirm_exclude":
        return f"Confirmed exclude: {base_rationale}"
    if reviewer2_decision == "overturn_to_include":
        return (
            f"Overturned reviewer 1 to include because the abstract remains plausibly relevant. {base_rationale}"
        )
    if reviewer2_decision == "overturn_to_exclude":
        return (
            f"Overturned reviewer 1 to exclude because the abstract does not clearly support the run objective. {base_rationale}"
        )
    return f"Reviewer 2 outcome could not be determined from reviewer 1={reviewer1_decision}, predicted={predicted_decision}."


def sanitize_row_values(row: dict[str, str]) -> None:
    for key, value in list(row.items()):
        if isinstance(value, str):
            row[key] = " ".join(value.split())


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python3 scripts/heuristic_abstract_review2.py <run_id>")
        return 1

    run_id = sys.argv[1].strip()
    run_dir = RUNS_DIR / run_id
    review2_path = active_artifacts_dir(run_dir) / "abstract_review" / "abstract_review2.csv"
    if not review2_path.exists():
        print(f"Abstract review 2 table not found: {review2_path}")
        return 1
    profile = build_review_profile(run_dir)

    with review2_path.open(encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        rows = list(reader)

    advance_count = 0
    stop_count = 0
    overturn_count = 0
    for row in rows:
        predicted = classify_row(row, profile)
        reviewer1_decision = row.get("abstract_reviewer_decision", "")
        predicted_decision = predicted["review_decision"]
        if reviewer1_decision == "include" and predicted_decision == "include":
            reviewer2_decision = "confirm_include"
            promotion = "advance_to_import"
        elif reviewer1_decision == "exclude" and predicted_decision == "exclude":
            reviewer2_decision = "confirm_exclude"
            promotion = "stop"
        elif predicted_decision == "include":
            reviewer2_decision = "overturn_to_include"
            promotion = "advance_to_import"
            overturn_count += 1
        else:
            reviewer2_decision = "overturn_to_exclude"
            promotion = "stop"
            overturn_count += 1

        row["abstract_reviewer2_decision"] = reviewer2_decision
        row["abstract_reviewer2_rationale"] = build_rationale(
            reviewer1_decision,
            reviewer2_decision,
            predicted_decision,
            predicted["review_rationale"],
        )
        row["abstract_reviewer2_confidence"] = predicted["review_confidence"]
        row["promotion_decision"] = promotion
        row["review_frame_role"] = predicted["review_frame_role"]
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

    print(
        f"Updated {review2_path}: advance_to_import={advance_count}, stop={stop_count}, "
        f"overturns={overturn_count}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
