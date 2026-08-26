#!/usr/bin/env python3

from __future__ import annotations

import csv
import sys
from pathlib import Path


WORKFLOW_ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = WORKFLOW_ROOT / "runs"

REQUIRED_INPUTS = [
    "request.md",
    "run_config.md",
    "instruction.md",
    "topic.md",
]

REQUIRED_OUTPUTS = [
    "artifacts/search_strategy/search_strategy.md",
    "artifacts/metadata_collection/paper_manifest.csv",
    "artifacts/abstract_review/abstract_review.csv",
    "artifacts/abstract_review/abstract_review2.csv",
    "artifacts/fulltext_import/import_status.csv",
    "artifacts/fulltext_import/manual_pdf_queue.csv",
    "artifacts/fulltext_review/fulltext_review.csv",
    "reports/final_reading_list.csv",
    "reports/progress_report.md",
]

REQUIRED_COLUMNS = {
    "paper_manifest": [
        "paper_id",
        "pmid",
        "doi",
        "title",
        "abstract",
        "year",
        "journal",
        "authors",
        "source_query",
        "retrieval_batch",
        "record_path",
    ],
    "abstract_review": [
        "paper_id",
        "pmid",
        "doi",
        "title",
        "abstract",
        "year",
        "source_query",
        "review_decision",
        "review_rationale",
        "review_confidence",
        "topic_match_type",
        "reviewer_type",
    ],
    "abstract_review2": [
        "paper_id",
        "pmid",
        "doi",
        "title",
        "abstract",
        "year",
        "source_query",
        "abstract_reviewer_decision",
        "abstract_reviewer_rationale",
        "abstract_reviewer2_decision",
        "abstract_reviewer2_rationale",
        "abstract_reviewer2_confidence",
        "promotion_decision",
    ],
    "import_status": [
        "paper_id",
        "pmid",
        "pmcid",
        "doi",
        "title",
        "pmc_access_status",
        "pmc_parse_status",
        "pdf_needed",
        "pdf_import_status",
        "normalized_path",
        "notes",
    ],
    "fulltext_review": [
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
    ],
    "final_reading_list": [
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
    ],
}

ALLOWED_VALUES = {
    "abstract_review": {
        "review_decision": {"include", "exclude"},
        "review_confidence": {"high", "medium", "low"},
        "reviewer_type": {"agent", "human", "hybrid"},
    },
    "abstract_review2": {
        "abstract_reviewer_decision": {"include", "exclude"},
        "abstract_reviewer2_decision": {
            "confirm_include",
            "confirm_exclude",
            "overturn_to_include",
            "overturn_to_exclude",
        },
        "abstract_reviewer2_confidence": {"high", "medium", "low"},
        "promotion_decision": {"advance_to_import", "stop"},
    },
    "import_status": {
        "pmc_access_status": {"available", "missing", "not_applicable"},
        "pmc_parse_status": {"usable", "unusable", "not_attempted"},
        "pdf_needed": {"yes", "no"},
        "pdf_import_status": {
            "imported",
            "staged_from_user_download",
            "normalized",
            "parser_pending",
            "parse_failed",
            "missing",
            "not_attempted",
        },
    },
    "fulltext_review": {
        "normalized_source_type": {"pmc_xml", "pdf_grobid", "missing"},
        "fulltext_decision": {"keep", "drop"},
        "mechanistic_relevance": {"high", "medium", "low"},
        "objective_relevance": {"high", "medium", "low"},
        "topic_centrality": {"central", "supporting", "incidental"},
        "review_confidence": {"high", "medium", "low"},
    },
    "final_reading_list": {
        "final_decision": {
            "selected_for_reading",
            "abstract_relevant_fulltext_unavailable",
        },
        "selection_basis": {"fulltext_review", "abstract_review_only"},
        "fulltext_access_status": {
            "readable",
            "unavailable",
            "parser_pending",
            "parse_failed",
        },
        "normalized_source_type": {"pmc_xml", "pdf_grobid", "missing"},
    },
}


def load_csv_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return reader.fieldnames or [], list(reader)


def unique_ids(rows: list[dict[str, str]], field: str) -> set[str]:
    return {row.get(field, "").strip() for row in rows if row.get(field, "").strip()}


def relative_or_absolute_path(run_dir: Path, path_text: str) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return run_dir / path


def row_label(row: dict[str, str], index: int) -> str:
    paper_id = row.get("paper_id", "").strip()
    pmid = row.get("pmid", "").strip()
    if paper_id:
        return paper_id
    if pmid:
        return f"pmid-{pmid}"
    return f"row {index}"


def validate_columns(name: str, fieldnames: list[str]) -> list[str]:
    required = REQUIRED_COLUMNS.get(name, [])
    missing = [field for field in required if field not in fieldnames]
    if not missing:
        return []
    return [f"{name} is missing required columns: {', '.join(missing)}."]


def validate_allowed_values(name: str, rows: list[dict[str, str]]) -> list[str]:
    errors: list[str] = []
    for field, allowed in ALLOWED_VALUES.get(name, {}).items():
        blank_labels = []
        invalid_labels = []
        blank_count = 0
        for index, row in enumerate(rows, start=2):
            value = row.get(field, "").strip()
            if not value:
                blank_count += 1
                if len(blank_labels) < 5:
                    blank_labels.append(row_label(row, index))
                continue
            if value not in allowed:
                if len(invalid_labels) < 5:
                    invalid_labels.append(f"{row_label(row, index)}={value}")
        if blank_count:
            errors.append(
                f"{name}.{field} has {blank_count} blank values "
                f"(examples: {', '.join(blank_labels)})."
            )
        invalid_count = sum(
            1
            for row in rows
            if (row.get(field, "").strip() and row.get(field, "").strip() not in allowed)
        )
        if invalid_count:
            errors.append(
                f"{name}.{field} has {invalid_count} invalid values "
                f"(examples: {', '.join(invalid_labels)}; allowed: {', '.join(sorted(allowed))})."
            )
    return errors


def validate_review_coverage(
    manifest_rows: list[dict[str, str]],
    review1_rows: list[dict[str, str]],
    review2_rows: list[dict[str, str]],
) -> list[str]:
    errors: list[str] = []
    manifest_ids = unique_ids(manifest_rows, "paper_id")
    review1_ids = unique_ids(review1_rows, "paper_id")
    review2_ids = unique_ids(review2_rows, "paper_id")

    if len(review1_rows) != len(manifest_rows):
        errors.append(
            "abstract_review.csv row count does not match paper_manifest.csv "
            f"({len(review1_rows)} vs {len(manifest_rows)})."
        )
    if len(review2_rows) != len(manifest_rows):
        errors.append(
            "abstract_review2.csv row count does not match paper_manifest.csv "
            f"({len(review2_rows)} vs {len(manifest_rows)})."
        )

    if review1_ids != manifest_ids:
        missing = sorted(manifest_ids - review1_ids)[:10]
        extra = sorted(review1_ids - manifest_ids)[:10]
        errors.append(
            "abstract_review.csv paper_id coverage does not exactly match paper_manifest.csv "
            f"(missing={missing}, extra={extra})."
        )
    if review2_ids != manifest_ids:
        missing = sorted(manifest_ids - review2_ids)[:10]
        extra = sorted(review2_ids - manifest_ids)[:10]
        errors.append(
            "abstract_review2.csv paper_id coverage does not exactly match paper_manifest.csv "
            f"(missing={missing}, extra={extra})."
        )

    return errors


def validate_import_handoff(
    review2_rows: list[dict[str, str]],
    import_rows: list[dict[str, str]],
) -> list[str]:
    advanced_ids = {
        row.get("paper_id", "").strip()
        for row in review2_rows
        if row.get("promotion_decision", "").strip() == "advance_to_import"
    }
    import_ids = unique_ids(import_rows, "paper_id")
    if advanced_ids == import_ids:
        return []
    return [
        "import_status.csv coverage does not match abstractReviewer2 advance_to_import set "
        f"(missing={sorted(advanced_ids - import_ids)[:10]}, extra={sorted(import_ids - advanced_ids)[:10]})."
    ]


def validate_fulltext_handoff(
    run_dir: Path,
    import_rows: list[dict[str, str]],
    fulltext_rows: list[dict[str, str]],
) -> list[str]:
    errors: list[str] = []
    normalized_ids = {
        row.get("paper_id", "").strip()
        for row in import_rows
        if row.get("normalized_path", "").strip()
    }
    fulltext_ids = unique_ids(fulltext_rows, "paper_id")
    if normalized_ids != fulltext_ids:
        errors.append(
            "fulltext_review.csv coverage does not match readable normalized imports "
            f"(missing={sorted(normalized_ids - fulltext_ids)[:10]}, extra={sorted(fulltext_ids - normalized_ids)[:10]})."
        )

    for index, row in enumerate(import_rows, start=2):
        normalized_path = row.get("normalized_path", "").strip()
        if not normalized_path:
            continue
        resolved = relative_or_absolute_path(run_dir, normalized_path)
        if not resolved.exists():
            errors.append(
                f"import_status.csv normalized_path is missing on disk for {row_label(row, index)}: {normalized_path}"
            )
    return errors


def validate_final_list(
    import_rows: list[dict[str, str]],
    fulltext_rows: list[dict[str, str]],
    final_rows: list[dict[str, str]],
) -> list[str]:
    errors: list[str] = []
    kept_ids = {
        row.get("paper_id", "").strip()
        for row in fulltext_rows
        if row.get("fulltext_decision", "").strip() == "keep"
    }
    unreadable_ids = {
        row.get("paper_id", "").strip()
        for row in import_rows
        if not row.get("normalized_path", "").strip()
    }
    selected_ids = {
        row.get("paper_id", "").strip()
        for row in final_rows
        if row.get("final_decision", "").strip() == "selected_for_reading"
    }
    unavailable_ids = {
        row.get("paper_id", "").strip()
        for row in final_rows
        if row.get("final_decision", "").strip() == "abstract_relevant_fulltext_unavailable"
    }

    if kept_ids != selected_ids:
        errors.append(
            "final selected_for_reading rows do not match fulltext_review keep rows "
            f"(missing={sorted(kept_ids - selected_ids)[:10]}, extra={sorted(selected_ids - kept_ids)[:10]})."
        )
    if unreadable_ids != unavailable_ids:
        errors.append(
            "final unavailable rows do not match advanced papers without normalized full text "
            f"(missing={sorted(unreadable_ids - unavailable_ids)[:10]}, extra={sorted(unavailable_ids - unreadable_ids)[:10]})."
        )
    return errors


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python3 scripts/validate_run.py <run_id>")
        return 1

    run_id = sys.argv[1].strip()
    run_dir = RUNS_DIR / run_id
    if not run_dir.exists():
        print(f"Run does not exist: {run_dir}")
        return 1

    errors: list[str] = []
    missing_inputs = [path for path in REQUIRED_INPUTS if not (run_dir / path).exists()]
    missing_outputs = [path for path in REQUIRED_OUTPUTS if not (run_dir / path).exists()]
    errors.extend(f"Missing input: {path}" for path in missing_inputs)
    errors.extend(f"Missing workflow artifact: {path}" for path in missing_outputs)

    paths = {
        "paper_manifest": run_dir / "artifacts" / "metadata_collection" / "paper_manifest.csv",
        "abstract_review": run_dir / "artifacts" / "abstract_review" / "abstract_review.csv",
        "abstract_review2": run_dir / "artifacts" / "abstract_review" / "abstract_review2.csv",
        "import_status": run_dir / "artifacts" / "fulltext_import" / "import_status.csv",
        "fulltext_review": run_dir / "artifacts" / "fulltext_review" / "fulltext_review.csv",
        "final_reading_list": run_dir / "reports" / "final_reading_list.csv",
    }
    tables: dict[str, list[dict[str, str]]] = {}

    for name, path in paths.items():
        if not path.exists():
            tables[name] = []
            continue
        fieldnames, rows = load_csv_rows(path)
        tables[name] = rows
        errors.extend(validate_columns(name, fieldnames))
        errors.extend(validate_allowed_values(name, rows))

    if all(paths[name].exists() for name in ("paper_manifest", "abstract_review", "abstract_review2")):
        errors.extend(
            validate_review_coverage(
                tables["paper_manifest"],
                tables["abstract_review"],
                tables["abstract_review2"],
            )
        )

    if all(paths[name].exists() for name in ("abstract_review2", "import_status")):
        errors.extend(validate_import_handoff(tables["abstract_review2"], tables["import_status"]))

    if all(paths[name].exists() for name in ("import_status", "fulltext_review")):
        errors.extend(validate_fulltext_handoff(run_dir, tables["import_status"], tables["fulltext_review"]))

    if all(paths[name].exists() for name in ("import_status", "fulltext_review", "final_reading_list")):
        errors.extend(
            validate_final_list(
                tables["import_status"],
                tables["fulltext_review"],
                tables["final_reading_list"],
            )
        )

    print(f"Run: {run_id}")
    if errors:
        print("Validation failed:")
        for error in errors:
            print(f"  - {error}")
        return 1

    print("All required inputs present")
    print("All expected workflow artifacts present")
    print("Schema values and required decisions are valid")
    print("Stage handoff coverage is consistent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
