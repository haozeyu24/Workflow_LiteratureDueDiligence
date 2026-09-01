#!/usr/bin/env python3

from __future__ import annotations

import sys
from pathlib import Path

TOOLS_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS_ROOT / "core"))
from tool_paths import WORKFLOW_ROOT, ensure_tool_paths
ensure_tool_paths()

import csv
import fnmatch
import json
import re
import sqlite3
import sys
from pathlib import Path

from pass_archive import active_artifacts_dir, active_path, active_reports_dir, archive_path_for_pass, incomplete_sentinel_path, load_all_pass_csv, pass_numbers, passes_dir, phase1_dir, phase1_transcript_path, run_input_path

RUNS_DIR = WORKFLOW_ROOT / "runs"

FORBIDDEN_CAP_KEYS = {
    "max_results_per_query",
    "max_total_results",
    "retmax",
    "record_cap",
    "retrieval_cap",
    "collection_cap",
}

ALLOWED_ARTIFACT_POLICIES = {
    "workflow_only",
    "allow_user_requested_exports",
}

WORKFLOW_ONLY_ALLOWED_PASS_FILES = {
    "snapshot_manifest.json",
    "inputs/original_user_prompt.md",
    "inputs/run_config.md",
    "inputs/run_brief.md",
    "artifacts/search_strategy/search_strategy.md",
    "artifacts/search_strategy/query_refinement_report.md",
    "artifacts/search_strategy/query_diagnostics.csv",
    "artifacts/metadata_collection/paper_manifest.csv",
    "artifacts/metadata_collection/blocked_venue_records.csv",
    "artifacts/abstract_triage/abstract_review_rules.md",
    "artifacts/abstract_triage/first_pass.csv",
    "artifacts/abstract_triage/second_pass.csv",
    "artifacts/fulltext_import/import_status.csv",
    "artifacts/fulltext_import/manual_pdf_queue.csv",
    "artifacts/fulltext_import/pdf_download_shortlist.csv",
    "artifacts/fulltext_import/pdf_intervention_status.json",
    "artifacts/fulltext_import/manual_pdf_import_report.csv",
    "artifacts/fulltext_import/pdf_parse_report.csv",
    "artifacts/fulltext_review/fulltext_review_rules.md",
    "artifacts/fulltext_review/fulltext_review.csv",
    "artifacts/fulltext_review/fulltext_rescue.csv",
    "artifacts/fulltext_review/evidence_extraction.csv",
    "artifacts/fulltext_review/pmc_mechanism_feedback.csv",
    "artifacts/workflow_control/workflow_state.json",
    "artifacts/workflow_control/workflow_loop_decision.csv",
    "artifacts/workflow_control/run_guidance_revision_log.csv",
    "reports/final_reading_list.csv",
    "reports/progress_report.md",
    "reports/pdf_request_shortlist.csv",
    "reports/intervention_prompt.md",
}

WORKFLOW_ONLY_ALLOWED_PASS_PATTERNS = [
    "artifacts/metadata_collection/records/*.json",
    "artifacts/fulltext_import/PMC_XML/*.xml",
    "artifacts/fulltext_import/PMC_XML/normalized/*.json",
    "artifacts/fulltext_import/PDF/*.pdf",
    "artifacts/fulltext_import/PDF/*.source.txt",
    "artifacts/fulltext_import/PDF/parser_cache/grobid/*.tei.xml",
    "artifacts/fulltext_import/PDF/normalized/*.json",
]

ROOT_REQUIRED_INPUTS = [
    "original_user_prompt.md",
]

PASS_INPUTS = [
    "run_config.md",
    "run_brief.md",
]

REQUIRED_OUTPUTS = [
    "artifacts/search_strategy/search_strategy.md",
    "artifacts/metadata_collection/paper_manifest.csv",
    "artifacts/metadata_collection/blocked_venue_records.csv",
    "artifacts/abstract_triage/first_pass.csv",
    "artifacts/abstract_triage/second_pass.csv",
    "artifacts/workflow_control/workflow_state.json",
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
        "publication_types",
        "year",
        "journal",
        "authors",
        "source_query",
        "retrieval_batch",
        "record_path",
    ],
    "blocked_venue_records": [
        "paper_id",
        "pmid",
        "doi",
        "title",
        "journal",
        "year",
        "source_query",
        "match_type",
        "match_value",
        "block_rationale",
    ],
    "query_diagnostics": [
        "round_id",
        "query_id",
        "query",
        "raw_hit_count",
        "collected_count",
        "truncated_by_constraint",
        "sample_size",
        "sample_strategy",
        "sampled_on_topic_count",
        "sampled_noise_count",
        "estimated_precision",
        "dominant_noise_classes",
        "missing_concepts",
        "recall_signals",
        "decision",
        "revision_rationale",
    ],
    "abstract_triage": [
        "paper_id",
        "pmid",
        "doi",
        "title",
        "abstract",
        "publication_types",
        "year",
        "source_query",
        "first_pass_decision",
        "first_pass_rationale",
        "first_pass_confidence",
        "topic_match_type",
        "triage_actor",
        "synthesis_role",
        "prescreen_hint",
        "prescreen_rationale",
        "prescreen_overlap_terms",
    ],
    "abstract_triage_second_pass": [
        "paper_id",
        "pmid",
        "doi",
        "title",
        "abstract",
        "publication_types",
        "year",
        "source_query",
        "first_pass_decision",
        "first_pass_rationale",
        "second_pass_decision",
        "second_pass_rationale",
        "second_pass_confidence",
        "promotion_decision",
        "synthesis_role",
    ],
    "import_status": [
        "paper_id",
        "pmid",
        "pmcid",
        "doi",
        "title",
        "fulltext_access_route",
        "fulltext_xml_url",
        "fulltext_pdf_url",
        "pmc_access_status",
        "pmc_parse_status",
        "pdf_needed",
        "pdf_import_status",
        "normalized_path",
        "notes",
    ],
    "pdf_download_shortlist": [
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
        "second_pass_decision",
        "promotion_decision",
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
    "fulltext_rescue": [
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
    ],
    "evidence_extraction": [
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
    ],
    "pmc_mechanism_feedback": [
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
    ],
    "workflow_loop_decision": [
        "loop_id",
        "source_stage",
        "trigger",
        "triggered",
        "action",
        "target_stage",
        "rationale",
        "required_changes",
        "stop_condition",
    ],
    "run_guidance_revision_log": [
        "revision_id",
        "feedback_loop_id",
        "feedback_source_path",
        "prior_pass_snapshot",
        "revised_instruction_path",
        "revised_topic_path",
        "revised_constraints_path",
        "search_strategy_path",
        "retained_mechanisms_added",
        "noise_or_exclusions_added",
        "missing_terms_added",
        "terms_replaced_or_tightened",
        "terms_demoted_to_context",
        "exclusion_enforcement_points",
        "reviewer_rule_changes",
        "expected_burden_effect",
        "revision_rationale",
        "revised_by",
        "created_at",
    ],
    "final_reading_list": [
        "paper_id",
        "pmid",
        "pmcid",
        "doi",
        "title",
        "year",
        "publication_types",
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
    "abstract_triage": {
        "first_pass_decision": {"include", "exclude"},
        "first_pass_confidence": {"high", "medium", "low"},
        "triage_actor": {"agent", "human", "hybrid"},
        "synthesis_role": {"none", "foundational_background", "field_synthesis", "perspective_gap"},
    },
    "abstract_triage_second_pass": {
        "first_pass_decision": {"include", "exclude"},
        "second_pass_decision": {
            "confirm_include",
            "confirm_exclude",
            "overturn_to_include",
            "overturn_to_exclude",
        },
        "second_pass_confidence": {"high", "medium", "low"},
        "promotion_decision": {"advance_to_import", "stop"},
        "synthesis_role": {"none", "foundational_background", "field_synthesis", "perspective_gap"},
    },
    "import_status": {
        "fulltext_access_route": {"ncbi_pmc_xml", "europe_pmc_xml", "oa_pdf", "none"},
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
    "pdf_download_shortlist": {
        "priority": {"high", "medium", "low", "exclude"},
        "shortlist_decision": {"request_pdf", "defer_pdf", "do_not_request"},
        "evidence_category": {
            "strong_learned_match",
            "possible_learned_match",
            "comparator_or_model_match",
            "access_uncertain",
            "noise",
        },
        "second_pass_decision": {
            "confirm_include",
            "confirm_exclude",
            "overturn_to_include",
            "overturn_to_exclude",
        },
        "promotion_decision": {"advance_to_import", "stop"},
    },
    "fulltext_review": {
        "normalized_source_type": {"pmc_xml", "pdf_grobid", "missing"},
        "fulltext_decision": {"keep", "drop"},
        "mechanistic_relevance": {"high", "medium", "low"},
        "objective_relevance": {"high", "medium", "low"},
        "topic_centrality": {"central", "supporting", "incidental"},
        "review_confidence": {"high", "medium", "low"},
    },
    "fulltext_rescue": {
        "normalized_source_type": {"pmc_xml", "pdf_grobid", "missing"},
        "original_fulltext_decision": {"drop"},
        "rescue_decision": {"confirm_drop", "overturn_to_keep"},
        "final_fulltext_decision": {"keep", "drop"},
        "positive_signal_found": {"yes", "no"},
        "negative_signal_overridden": {"yes", "no"},
        "review_confidence": {"high", "medium", "low"},
    },
    "final_reading_list": {
        "final_decision": {
            "selected_for_reading",
            "abstract_relevant_fulltext_unavailable",
        },
        "selection_basis": {"fulltext_review", "abstract_triage_only"},
        "fulltext_access_status": {
            "readable",
            "unavailable",
            "parser_pending",
            "parse_failed",
        },
        "normalized_source_type": {"pmc_xml", "pdf_grobid", "missing"},
    },
    "evidence_extraction": {
        "evidence_tier": {"direct", "indirect", "comparator", "background", "exclude"},
        "directness": {"direct_target", "same_family_comparator", "pathway_or_context", "incidental"},
        "target_centrality": {"central", "supporting", "incidental"},
        "query_feedback_signal": {
            "none",
            "tighten_query",
            "expand_query",
            "add_rescue_query",
            "change_scope",
            "reviewer_calibration",
        },
        "review_confidence": {"high", "medium", "low"},
        "retention_role": {
            "direct_mechanistic",
            "clinical_translational",
            "foundational_background",
            "field_synthesis",
            "perspective_gap",
            "exclude",
        },
    },
    "workflow_loop_decision": {
        "triggered": {"yes", "no"},
        "action": {
            "continue",
            "pause_for_user",
            "pause_for_review_write_decision",
            "build_pdf_shortlist",
            "loop_to_run_guidance_reviser",
            "loop_to_query_scout",
            "loop_to_abstract_triage",
            "loop_to_fulltext_review",
            "stop_blocked",
        },
    },
    "pmc_mechanism_feedback": {
        "pdf_deferral_decision": {"defer_pdfs", "final_pdf_pass", "require_user_pdf_now"},
    },
    "run_guidance_revision_log": {
        "revised_by": {"agent", "human", "hybrid"},
    },
}

STRONG_FINAL_EVIDENCE_TIERS = {"direct", "indirect", "comparator"}
CONTEXT_RETENTION_ROLES = {"foundational_background", "field_synthesis", "perspective_gap", "exclude"}


def load_csv_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return reader.fieldnames or [], list(reader)


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


def validate_no_pubmed_caps(run_dir: Path, query_diagnostics_rows: list[dict[str, str]]) -> list[str]:
    errors: list[str] = []
    constraints_path = run_input_path(run_dir, "run_brief.md")
    if constraints_path.exists():
        for line_number, raw_line in enumerate(constraints_path.read_text(encoding="utf-8").splitlines(), start=1):
            line = raw_line.strip().replace("`", "")
            if not line or line.startswith("#"):
                continue
            match = re.match(r"^-?\s*([A-Za-z0-9_]+)\s*:", line)
            if match and match.group(1) in FORBIDDEN_CAP_KEYS:
                errors.append(
                    "run_brief.md contains a forbidden PubMed collection cap "
                    f"({match.group(1)} at line {line_number}). Use query refinement instead."
                )

    for index, row in enumerate(query_diagnostics_rows, start=2):
        if row.get("round_id", "").strip() != "collection":
            continue
        if row.get("truncated_by_constraint", "").strip() == "yes":
            errors.append(
                f"query_diagnostics.csv row {index} records capped/truncated collection; PubMed collection caps are forbidden."
            )
        raw_hit_count = row.get("raw_hit_count", "").strip()
        collected_count = row.get("collected_count", "").strip()
        if raw_hit_count.isdigit() and collected_count.isdigit() and int(collected_count) < int(raw_hit_count):
            errors.append(
                f"query_diagnostics.csv row {index} collected fewer records than raw PubMed hits "
                f"({collected_count} < {raw_hit_count}); capped collection is forbidden."
            )
    return errors


def validate_required_inputs(run_dir: Path) -> list[str]:
    errors: list[str] = []
    for path in ROOT_REQUIRED_INPUTS:
        if not (run_dir / path).exists():
            errors.append(f"Missing root input: {path}")

    transcript_path = phase1_transcript_path(run_dir)
    if not transcript_path.exists():
        errors.append(
            "Missing Phase 1 transcript: "
            "Phase1_PubmedCollection/passes/phase1_transcript.md"
        )

    pass1_inputs_dir = archive_path_for_pass(run_dir, 1) / "inputs"
    for path in PASS_INPUTS:
        if not (pass1_inputs_dir / path).exists():
            errors.append(f"Missing pass_001 input: Phase1_PubmedCollection/passes/pass_001/inputs/{path}")
    return errors


def validate_config_loop_bounds(config: dict[str, str]) -> list[str]:
    errors: list[str] = []
    artifact_policy = config.get("artifact_policy", "workflow_only").strip() or "workflow_only"
    if artifact_policy not in ALLOWED_ARTIFACT_POLICIES:
        errors.append(
            "run_config.md artifact_policy is invalid "
            f"({artifact_policy}; allowed: {', '.join(sorted(ALLOWED_ARTIFACT_POLICIES))})."
        )
    min_value = config_int(config, "min_big_workflow_loops", 2)
    max_value = config_int(config, "max_workflow_loops", 2)
    if min_value != 2:
        errors.append("run_config.md min_big_workflow_loops must be fixed at 2.")
    if max_value != 2:
        errors.append("run_config.md max_workflow_loops must be fixed at 2.")
    gate_mode = pmc_fulltext_review_gate_mode(config)
    if gate_mode not in {"all_available", "scaled"}:
        errors.append(
            "run_config.md pmc_fulltext_review_gate_mode is invalid "
            f"({gate_mode}; allowed: all_available, scaled)."
        )
    fulltext_lookup_mode = config.get("fulltext_lookup_mode", "pmc_then_oa_final").strip() or "pmc_then_oa_final"
    if fulltext_lookup_mode not in {"pmc_then_oa_final", "pmc_only", "exhaustive_oa"}:
        errors.append(
            "run_config.md fulltext_lookup_mode is invalid "
            f"({fulltext_lookup_mode}; allowed: exhaustive_oa, pmc_only, pmc_then_oa_final)."
        )
    return errors


def validate_pmc_fulltext_review_gate(
    config: dict[str, str],
    import_rows: list[dict[str, str]],
    fulltext_rows: list[dict[str, str]],
    evidence_rows: list[dict[str, str]],
    feedback_rows: list[dict[str, str]],
) -> list[str]:
    gate_mode = pmc_fulltext_review_gate_mode(config)
    if gate_mode != "all_available":
        return []

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
    evidence_ids = unique_ids(evidence_rows, "paper_id")

    missing_review = sorted(usable_ids - reviewed_ids)
    missing_evidence = sorted(usable_ids - evidence_ids)
    if not (unattempted_ids or unusable_not_queued_ids or missing_review or missing_evidence):
        return []

    return [
        "pmc_fulltext_review_gate_mode=all_available blocks PMC feedback from driving a learned rerun: "
        f"PMC-available={len(pmc_available_ids)}, PMC-unattempted={len(unattempted_ids)}, "
        f"PMC-usable={len(usable_ids)}, fulltext_reviewed={len(reviewed_ids & usable_ids)}, "
        f"evidence_extracted={len(evidence_ids & usable_ids)}, "
        f"unusable_not_queued={len(unusable_not_queued_ids)}. "
        f"Unattempted examples={sorted(unattempted_ids)[:10]}, "
        f"unusable-not-queued examples={sorted(unusable_not_queued_ids)[:10]}, "
        f"missing review examples={missing_review[:10]}, "
        f"missing evidence examples={missing_evidence[:10]}."
    ]


def is_allowed_workflow_only_file(relative_path: str) -> bool:
    if not relative_path or relative_path.endswith("/.DS_Store") or relative_path == ".DS_Store":
        return True
    if relative_path in WORKFLOW_ONLY_ALLOWED_PASS_FILES:
        return True
    return any(fnmatch.fnmatch(relative_path, pattern) for pattern in WORKFLOW_ONLY_ALLOWED_PASS_PATTERNS)


def validate_artifact_policy(run_dir: Path, config: dict[str, str]) -> list[str]:
    artifact_policy = config.get("artifact_policy", "workflow_only").strip() or "workflow_only"
    if artifact_policy != "workflow_only":
        return []

    active_pass_dir = active_artifacts_dir(run_dir).parent
    if not active_pass_dir.exists():
        return []

    unexpected: list[str] = []
    for path in active_pass_dir.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(active_pass_dir).as_posix()
        if not is_allowed_workflow_only_file(relative):
            unexpected.append(relative)

    if not unexpected:
        return []
    return [
        "artifact_policy=workflow_only forbids undeclared active-pass files "
        f"(examples: {', '.join(sorted(unexpected)[:10])}). "
        "Remove the side deliverable or add an explicit workflow/user-requested artifact policy before continuing."
    ]


def validate_pass_sequence(run_dir: Path) -> list[str]:
    errors: list[str] = []
    numbers = pass_numbers(run_dir)
    for number in numbers:
        if number <= 1:
            continue
        previous = archive_path_for_pass(run_dir, number - 1)
        manifest_rows = load_csv_rows(previous / "artifacts" / "metadata_collection" / "paper_manifest.csv")[1] if (previous / "artifacts" / "metadata_collection" / "paper_manifest.csv").exists() else []
        abstract_rows = load_csv_rows(previous / "artifacts" / "abstract_triage" / "first_pass.csv")[1] if (previous / "artifacts" / "abstract_triage" / "first_pass.csv").exists() else []
        abstract2_rows = load_csv_rows(previous / "artifacts" / "abstract_triage" / "second_pass.csv")[1] if (previous / "artifacts" / "abstract_triage" / "second_pass.csv").exists() else []
        feedback_rows = load_csv_rows(previous / "artifacts" / "fulltext_review" / "pmc_mechanism_feedback.csv")[1] if (previous / "artifacts" / "fulltext_review" / "pmc_mechanism_feedback.csv").exists() else []

        reasons: list[str] = []
        if not manifest_rows:
            reasons.append("previous pass has no collected paper_manifest rows")
        if len(abstract_rows) != len(manifest_rows) or any(not row.get("first_pass_decision", "").strip() for row in abstract_rows):
            reasons.append("previous pass first_pass.csv is incomplete")
        if (
            len(abstract2_rows) != len(manifest_rows)
            or any(not row.get("second_pass_decision", "").strip() for row in abstract2_rows)
            or any(not row.get("promotion_decision", "").strip() for row in abstract2_rows)
        ):
            reasons.append("previous pass second_pass.csv is incomplete")
        if not feedback_rows:
            reasons.append("previous pass has no pmc_mechanism_feedback.csv rows")
        elif feedback_rows[-1].get("pdf_deferral_decision", "").strip() != "defer_pdfs":
            reasons.append("previous pass latest PMC feedback does not request a learned rerun")

        if reasons:
            errors.append(
                f"pass_{number:03d} exists before pass_{number - 1:03d} is ready for a learned rerun "
                f"({'; '.join(reasons)})."
            )
    return errors


def validate_workflow_database(run_dir: Path) -> list[str]:
    numbers = pass_numbers(run_dir)
    if len(numbers) <= 1:
        return []

    db_path = phase1_dir(run_dir) / "workflow_state.sqlite"
    if not db_path.exists():
        return [
            "Multi-pass run is missing Phase1_PubmedCollection/workflow_state.sqlite; "
            "run tools/run/rebuild_workflow_db.py <run_id> or rerun the rescue abstract-triage stage "
            "so cross-pass rejection state can be recorded."
        ]

    try:
        with sqlite3.connect(db_path) as connection:
            table_rows = connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
            tables = {str(row[0]) for row in table_rows}
            missing = {"metadata", "papers", "pass_decisions"} - tables
            if missing:
                return [
                    "workflow_state.sqlite is missing required tables: "
                    + ", ".join(sorted(missing))
                ]
            decision_count = connection.execute(
                "SELECT COUNT(*) FROM pass_decisions WHERE stage = 'abstract_triage'"
            ).fetchone()[0]
    except sqlite3.Error as error:
        return [f"workflow_state.sqlite could not be read: {error}"]

    if decision_count == 0:
        return [
            "workflow_state.sqlite has no abstract_triage pass_decisions; "
            "future passes cannot filter prior rejects."
        ]
    return []


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
            "first_pass.csv row count does not match paper_manifest.csv "
            f"({len(review1_rows)} vs {len(manifest_rows)})."
        )
    if len(review2_rows) != len(manifest_rows):
        errors.append(
            "second_pass.csv row count does not match paper_manifest.csv "
            f"({len(review2_rows)} vs {len(manifest_rows)})."
        )

    if review1_ids != manifest_ids:
        missing = sorted(manifest_ids - review1_ids)[:10]
        extra = sorted(review1_ids - manifest_ids)[:10]
        errors.append(
            "first_pass.csv paper_id coverage does not exactly match paper_manifest.csv "
            f"(missing={missing}, extra={extra})."
        )
    if review2_ids != manifest_ids:
        missing = sorted(manifest_ids - review2_ids)[:10]
        extra = sorted(review2_ids - manifest_ids)[:10]
        errors.append(
            "second_pass.csv paper_id coverage does not exactly match paper_manifest.csv "
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
        "import_status.csv coverage does not match abstract triage second pass advance_to_import set "
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


def validate_evidence_handoff(
    fulltext_rows: list[dict[str, str]],
    evidence_rows: list[dict[str, str]],
) -> list[str]:
    reviewed_ids = {
        row.get("paper_id", "").strip()
        for row in fulltext_rows
        if row.get("fulltext_decision", "").strip()
    }
    evidence_ids = unique_ids(evidence_rows, "paper_id")
    if reviewed_ids == evidence_ids:
        return []
    return [
        "evidence_extraction.csv coverage does not match reviewed readable full texts "
        f"(missing={sorted(reviewed_ids - evidence_ids)[:10]}, extra={sorted(evidence_ids - reviewed_ids)[:10]})."
    ]


def validate_fulltext_rescue_handoff(
    fulltext_rows: list[dict[str, str]],
    rescue_rows: list[dict[str, str]],
) -> list[str]:
    errors: list[str] = []
    fulltext_by_id = {
        row.get("paper_id", "").strip(): row
        for row in fulltext_rows
        if row.get("paper_id", "").strip()
    }
    rescue_ids = unique_ids(rescue_rows, "paper_id")
    missing = sorted(rescue_ids - set(fulltext_by_id))
    if missing:
        errors.append(
            "fulltext_rescue.csv contains paper_id values absent from fulltext_review.csv "
            f"(examples={missing[:10]})."
        )
    for row in rescue_rows:
        paper_id = row.get("paper_id", "").strip()
        if not paper_id or paper_id not in fulltext_by_id:
            continue
        rescue_final = row.get("final_fulltext_decision", "").strip()
        review_final = fulltext_by_id[paper_id].get("fulltext_decision", "").strip()
        if rescue_final != review_final:
            errors.append(
                "fulltext_rescue.csv final_fulltext_decision does not match "
                f"fulltext_review.csv for {paper_id} ({rescue_final} vs {review_final})."
            )
    return errors


def evidence_by_paper_id(evidence_rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    by_id: dict[str, list[dict[str, str]]] = {}
    for row in evidence_rows:
        paper_id = row.get("paper_id", "").strip()
        if not paper_id:
            continue
        by_id.setdefault(paper_id, []).append(row)
    return by_id


def has_prompt_fit_final_evidence(fulltext_row: dict[str, str], paper_evidence: list[dict[str, str]]) -> bool:
    if fulltext_row.get("fulltext_decision", "").strip() != "keep":
        return True
    if fulltext_row.get("objective_relevance", "").strip() == "low":
        return False
    if fulltext_row.get("mechanistic_relevance", "").strip() == "low":
        return False
    if fulltext_row.get("topic_centrality", "").strip() == "incidental":
        return False
    if not paper_evidence:
        return False
    for row in paper_evidence:
        evidence_tier = row.get("evidence_tier", "").strip()
        directness = row.get("directness", "").strip()
        centrality = row.get("target_centrality", "").strip()
        retention_role = row.get("retention_role", "").strip()
        if evidence_tier in STRONG_FINAL_EVIDENCE_TIERS and centrality != "incidental":
            return True
        if directness in {"direct_target", "same_family_comparator"} and retention_role not in CONTEXT_RETENTION_ROLES:
            return True
    return False


def validate_final_prompt_fit_density(
    status: str,
    access_phase: str,
    feedback_rows: list[dict[str, str]],
    fulltext_rows: list[dict[str, str]],
    evidence_rows: list[dict[str, str]],
) -> list[str]:
    latest_pdf_decision = feedback_rows[-1].get("pdf_deferral_decision", "").strip() if feedback_rows else ""
    if status != "complete" and access_phase != "final_access" and latest_pdf_decision != "final_pdf_pass":
        return []
    evidence_map = evidence_by_paper_id(evidence_rows)
    weak_keep_ids = [
        row.get("paper_id", "").strip()
        for row in fulltext_rows
        if row.get("fulltext_decision", "").strip() == "keep"
        and not has_prompt_fit_final_evidence(row, evidence_map.get(row.get("paper_id", "").strip(), []))
    ]
    if not weak_keep_ids:
        return []
    return [
        "final prompt-fit density gate failed: final kept full-text rows include weak, incidental, "
        "missing, or low-relevance evidence rather than direct, strong indirect, or run-authorized "
        f"comparator evidence (examples={weak_keep_ids[:10]}). The controller must loop to query "
        "refinement, abstract-review calibration, or full-text review before completion."
    ]


def validate_final_list(
    import_rows: list[dict[str, str]],
    fulltext_rows: list[dict[str, str]],
    final_rows: list[dict[str, str]],
    access_phase: str,
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
    if access_phase == "pmc_learning":
        if unavailable_ids:
            errors.append(
                "pmc_learning final list should not promote unreadable abstract-only papers "
                f"(examples={sorted(unavailable_ids)[:10]})."
            )
    elif unreadable_ids != unavailable_ids:
        errors.append(
            "final unavailable rows do not match advanced papers without normalized full text "
            f"(missing={sorted(unreadable_ids - unavailable_ids)[:10]}, extra={sorted(unavailable_ids - unreadable_ids)[:10]})."
        )
    return errors


def validate_pdf_shortlist(
    queue_rows: list[dict[str, str]],
    feedback_rows: list[dict[str, str]],
    shortlist_rows: list[dict[str, str]],
    min_big_workflow_loops: int,
) -> list[str]:
    errors: list[str] = []
    if not queue_rows or not feedback_rows:
        return errors
    latest_pdf_decision = feedback_rows[-1].get("pdf_deferral_decision", "").strip()

    if len(feedback_rows) < min_big_workflow_loops:
        if latest_pdf_decision == "final_pdf_pass":
            errors.append(
                "pmc_mechanism_feedback.csv marks final_pdf_pass before the minimum big workflow loop count is satisfied "
                f"({len(feedback_rows)} < {min_big_workflow_loops})."
            )
        if shortlist_rows:
            errors.append(
                "pdf_download_shortlist.csv exists before the minimum big workflow loop count is satisfied."
            )
        return errors

    if latest_pdf_decision != "final_pdf_pass":
        if shortlist_rows:
            errors.append(
                "pdf_download_shortlist.csv has rows before PMC feedback marked final_pdf_pass."
            )
        return errors

    queue_ids = unique_ids(queue_rows, "paper_id")
    shortlist_ids = unique_ids(shortlist_rows, "paper_id")
    if queue_ids != shortlist_ids:
        errors.append(
            "pdf_download_shortlist.csv coverage does not match manual_pdf_queue.csv "
            f"(missing={sorted(queue_ids - shortlist_ids)[:10]}, extra={sorted(shortlist_ids - queue_ids)[:10]})."
        )

    requested = [
        row
        for row in shortlist_rows
        if row.get("shortlist_decision", "").strip() == "request_pdf"
    ]
    if not requested:
        errors.append(
            "pdf_download_shortlist.csv has no request_pdf rows despite a non-empty PDF queue after PMC feedback."
        )

    return errors


def validate_workflow_state(
    run_dir: Path,
    state_path: Path,
    queue_rows: list[dict[str, str]],
    feedback_rows: list[dict[str, str]],
    shortlist_rows: list[dict[str, str]],
    loop_rows: list[dict[str, str]],
    min_big_workflow_loops: int,
    max_workflow_loops: int,
) -> list[str]:
    errors: list[str] = []
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"workflow_state.json is not valid JSON: {exc}."]

    allowed_status = {
        "initialized",
        "running",
        "loop_required",
        "awaiting_pdf_shortlist",
        "complete",
        "blocked",
    }
    status = str(state.get("status", ""))
    if status not in allowed_status:
        errors.append(
            "workflow_state.status is invalid "
            f"({status}; allowed: {', '.join(sorted(allowed_status))})."
        )

    active_loop_count = sum(row.get("triggered", "") == "yes" for row in loop_rows)
    latest_pdf_decision = feedback_rows[-1].get("pdf_deferral_decision", "").strip() if feedback_rows else ""
    queue_count = len(queue_rows)
    shortlist_count = len(shortlist_rows)

    if state.get("active_loop_count") != active_loop_count:
        errors.append(
            "workflow_state.active_loop_count does not match workflow_loop_decision.csv "
            f"({state.get('active_loop_count')} vs {active_loop_count})."
        )
    if state.get("manual_pdf_queue_count") != queue_count:
        errors.append(
            "workflow_state.manual_pdf_queue_count does not match manual_pdf_queue.csv "
            f"({state.get('manual_pdf_queue_count')} vs {queue_count})."
        )
    if state.get("pdf_download_shortlist_count") != shortlist_count:
        errors.append(
            "workflow_state.pdf_download_shortlist_count does not match pdf_download_shortlist.csv "
            f"({state.get('pdf_download_shortlist_count')} vs {shortlist_count})."
        )
    if latest_pdf_decision and state.get("latest_pdf_deferral_decision") != latest_pdf_decision:
        errors.append(
            "workflow_state.latest_pdf_deferral_decision does not match pmc_mechanism_feedback.csv "
            f"({state.get('latest_pdf_deferral_decision')} vs {latest_pdf_decision})."
        )
    if state.get("completed_big_loop_count") is not None and state.get("completed_big_loop_count") != len(feedback_rows):
        errors.append(
            "workflow_state.completed_big_loop_count does not match pmc_mechanism_feedback.csv "
            f"({state.get('completed_big_loop_count')} vs {len(feedback_rows)})."
        )
    if state.get("min_big_workflow_loops") is not None and state.get("min_big_workflow_loops") != min_big_workflow_loops:
        errors.append(
            "workflow_state.min_big_workflow_loops does not match run_config.md "
            f"({state.get('min_big_workflow_loops')} vs {min_big_workflow_loops})."
        )
    if state.get("max_workflow_loops") is not None and state.get("max_workflow_loops") != max_workflow_loops:
        errors.append(
            "workflow_state.max_workflow_loops does not match run_config.md "
            f"({state.get('max_workflow_loops')} vs {max_workflow_loops})."
        )

    if feedback_rows and len(feedback_rows) < min_big_workflow_loops and active_loop_count == 0:
        errors.append(
            "workflow_loop_decision.csv has no active loop even though the minimum big workflow loop count is not satisfied."
        )

    if status == "complete":
        if state.get("access_phase") != "final_access":
            errors.append("workflow_state is complete but access_phase is not final_access.")
        if incomplete_sentinel_path(run_dir).exists():
            errors.append("workflow_state is complete but WORKFLOW_NOT_COMPLETE still exists.")
        if active_loop_count:
            errors.append("workflow_state is complete while controller loops are still active.")
        if len(feedback_rows) < min_big_workflow_loops:
            errors.append(
                "workflow_state is complete before the minimum big workflow loop count is satisfied."
            )
        if len(feedback_rows) > max_workflow_loops:
            errors.append(
                "workflow_state is complete after exceeding max_workflow_loops."
            )
        if latest_pdf_decision != "final_pdf_pass":
            errors.append("workflow_state is complete before PMC feedback marked final_pdf_pass.")
        if queue_count and not shortlist_count:
            errors.append("workflow_state is complete with a non-empty PDF queue but no PDF download shortlist.")
        if queue_count and state.get("completion_signal") != "pdf_download_shortlist_ready":
            errors.append("workflow_state complete signal must be pdf_download_shortlist_ready when the PDF queue is non-empty.")
    elif not incomplete_sentinel_path(run_dir).exists():
        errors.append(
            "WORKFLOW_NOT_COMPLETE sentinel is missing while workflow_state.status is not complete."
        )

    return errors


def validate_prior_pass_pmc_cleanup(run_dir: Path, status: str) -> list[str]:
    if status != "complete":
        return []
    active_number = max(pass_numbers(run_dir) or [1])
    active_state_path = passes_dir(run_dir) / "active_pass.json"
    if active_state_path.exists():
        try:
            active_payload = json.loads(active_state_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            active_payload = {}
        value = active_payload.get("pass_number")
        if isinstance(value, int) and value > 0:
            active_number = value

    stale_files: list[str] = []
    for number in pass_numbers(run_dir):
        if number >= active_number:
            continue
        pmc_dir = archive_path_for_pass(run_dir, number) / "artifacts" / "fulltext_import" / "PMC_XML"
        if not pmc_dir.exists():
            continue
        for path in pmc_dir.rglob("*"):
            if path.is_file():
                stale_files.append(path.relative_to(run_dir).as_posix())
                if len(stale_files) >= 10:
                    break
        if len(stale_files) >= 10:
            break

    if not stale_files:
        return []
    return [
        "workflow_state is complete but prior-pass PMC payload files remain "
        f"(examples: {', '.join(stale_files)}). "
        "Run the mutating completion gate to delete earlier-pass PMC XML and PMC-normalized JSON before completion."
    ]


def validate_guidance_revisions(
    run_dir: Path,
    feedback_rows: list[dict[str, str]],
    revision_rows: list[dict[str, str]],
) -> list[str]:
    errors: list[str] = []
    revisions_by_feedback = {
        row.get("feedback_loop_id", "").strip(): row
        for row in revision_rows
        if row.get("feedback_loop_id", "").strip()
    }

    for feedback in feedback_rows:
        if feedback.get("pdf_deferral_decision", "").strip() != "defer_pdfs":
            continue
        loop_id = feedback.get("loop_id", "").strip()
        if not loop_id:
            continue
        revision = revisions_by_feedback.get(loop_id)
        if revision is None:
            errors.append(
                "PMC feedback row "
                f"{loop_id} says defer_pdfs but has no matching row in run_guidance_revision_log.csv."
            )
            continue
        for field in ("revised_instruction_path", "revised_topic_path", "search_strategy_path"):
            value = revision.get(field, "").strip()
            if not value:
                errors.append(f"run_guidance_revision_log.csv row for {loop_id} is missing {field}.")
                continue
            candidate = Path(value)
            if not candidate.is_absolute():
                candidate = run_dir / value
            if not candidate.exists():
                errors.append(
                    f"run_guidance_revision_log.csv row for {loop_id} points to missing {field}: {value}."
                )
        for field in (
            "retained_mechanisms_added",
            "noise_or_exclusions_added",
            "missing_terms_added",
            "terms_replaced_or_tightened",
            "terms_demoted_to_context",
            "exclusion_enforcement_points",
            "reviewer_rule_changes",
            "expected_burden_effect",
            "revision_rationale",
        ):
            if not revision.get(field, "").strip():
                errors.append(f"run_guidance_revision_log.csv row for {loop_id} is missing {field}.")
    return errors


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python3 tools/run/validate_run.py <run_id>")
        return 1

    run_id = sys.argv[1].strip()
    run_dir = RUNS_DIR / run_id
    if not run_dir.exists():
        print(f"Run does not exist: {run_dir}")
        return 1

    errors: list[str] = []
    config = parse_config(run_input_path(run_dir, "run_config.md"))
    access_phase = config.get("access_phase", "pmc_learning")
    state_probe_path = active_path(run_dir, "artifacts/workflow_control/workflow_state.json")
    if state_probe_path.exists():
        try:
            state_probe = json.loads(state_probe_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            state_probe = {}
        if state_probe.get("access_phase") == "final_access":
            access_phase = "final_access"
    min_big_workflow_loops = 2
    max_workflow_loops = 2
    errors.extend(validate_config_loop_bounds(config))
    errors.extend(validate_artifact_policy(run_dir, config))
    errors.extend(validate_pass_sequence(run_dir))
    errors.extend(validate_workflow_database(run_dir))
    missing_outputs = [path for path in REQUIRED_OUTPUTS if not active_path(run_dir, path).exists()]
    errors.extend(validate_required_inputs(run_dir))
    errors.extend(f"Missing workflow artifact: {path}" for path in missing_outputs)

    artifacts_dir = active_artifacts_dir(run_dir)
    reports_dir = active_reports_dir(run_dir)
    paths = {
        "paper_manifest": artifacts_dir / "metadata_collection" / "paper_manifest.csv",
        "query_diagnostics": artifacts_dir / "search_strategy" / "query_diagnostics.csv",
        "abstract_triage_first_pass": artifacts_dir / "abstract_triage" / "first_pass.csv",
        "abstract_triage_second_pass": artifacts_dir / "abstract_triage" / "second_pass.csv",
        "import_status": artifacts_dir / "fulltext_import" / "import_status.csv",
        "pdf_download_shortlist": artifacts_dir / "fulltext_import" / "pdf_download_shortlist.csv",
        "evidence_extraction": artifacts_dir / "fulltext_review" / "evidence_extraction.csv",
        "pmc_mechanism_feedback": artifacts_dir / "fulltext_review" / "pmc_mechanism_feedback.csv",
        "fulltext_review": artifacts_dir / "fulltext_review" / "fulltext_review.csv",
        "fulltext_rescue": artifacts_dir / "fulltext_review" / "fulltext_rescue.csv",
        "workflow_loop_decision": artifacts_dir / "workflow_control" / "workflow_loop_decision.csv",
        "run_guidance_revision_log": artifacts_dir / "workflow_control" / "run_guidance_revision_log.csv",
        "workflow_state": artifacts_dir / "workflow_control" / "workflow_state.json",
        "final_reading_list": reports_dir / "final_reading_list.csv",
    }
    tables: dict[str, list[dict[str, str]]] = {}

    for name, path in paths.items():
        if name == "workflow_state":
            tables[name] = []
            continue
        if not path.exists():
            tables[name] = []
            continue
        fieldnames, rows = load_csv_rows(path)
        tables[name] = rows
        errors.extend(validate_columns(name, fieldnames))
        errors.extend(validate_allowed_values(name, rows))

    errors.extend(validate_no_pubmed_caps(run_dir, tables.get("query_diagnostics", [])))

    if all(paths[name].exists() for name in ("paper_manifest", "abstract_triage_first_pass", "abstract_triage_second_pass")):
        errors.extend(
            validate_review_coverage(
                tables["paper_manifest"],
                tables["abstract_triage_first_pass"],
                tables["abstract_triage_second_pass"],
            )
        )

    if all(paths[name].exists() for name in ("abstract_triage_second_pass", "import_status")):
        errors.extend(validate_import_handoff(tables["abstract_triage_second_pass"], tables["import_status"]))

    if all(paths[name].exists() for name in ("import_status", "fulltext_review")):
        errors.extend(validate_fulltext_handoff(run_dir, tables["import_status"], tables["fulltext_review"]))

    if all(paths[name].exists() for name in ("fulltext_review", "evidence_extraction")):
        errors.extend(validate_evidence_handoff(tables["fulltext_review"], tables["evidence_extraction"]))

    if all(paths[name].exists() for name in ("fulltext_review", "fulltext_rescue")):
        errors.extend(validate_fulltext_rescue_handoff(tables["fulltext_review"], tables["fulltext_rescue"]))

    if all(paths[name].exists() for name in ("import_status", "fulltext_review", "final_reading_list")):
        errors.extend(
            validate_final_list(
                tables["import_status"],
                tables["fulltext_review"],
                tables["final_reading_list"],
                access_phase,
            )
        )

    if paths["pmc_mechanism_feedback"].exists():
        if not (artifacts_dir / "fulltext_review" / "fulltext_review_rules.md").exists():
            errors.append(
                "pmc_mechanism_feedback.csv exists before fulltext_review_rules.md; "
                "generate explicit full-text review rules before feedback."
            )
        if not paths["fulltext_rescue"].exists():
            errors.append(
                "pmc_mechanism_feedback.csv exists before fulltext_rescue.csv; "
                "run the full-text rescue pass over first-pass drops before feedback."
            )
        queue_path = artifacts_dir / "fulltext_import" / "manual_pdf_queue.csv"
        queue_rows = load_csv_rows(queue_path)[1] if queue_path.exists() else []
        feedback_rows = load_all_pass_csv(run_dir, "artifacts/fulltext_review/pmc_mechanism_feedback.csv")
        errors.extend(
            validate_pmc_fulltext_review_gate(
                config,
                tables.get("import_status", []),
                tables.get("fulltext_review", []),
                tables.get("evidence_extraction", []),
                feedback_rows,
            )
        )
        latest_pdf_decision = feedback_rows[-1].get("pdf_deferral_decision", "").strip() if feedback_rows else ""
        shortlist_exists = paths["pdf_download_shortlist"].exists()
        if queue_rows and latest_pdf_decision == "final_pdf_pass" and not shortlist_exists:
            errors.append(
                "pdf_download_shortlist.csv is required when PMC feedback marks final_pdf_pass and the PDF queue is non-empty."
            )
        shortlist_rows = tables["pdf_download_shortlist"] if shortlist_exists else []
        errors.extend(validate_pdf_shortlist(queue_rows, feedback_rows, shortlist_rows, min_big_workflow_loops))
        errors.extend(
            validate_guidance_revisions(
                run_dir,
                feedback_rows,
                tables.get("run_guidance_revision_log", []),
            )
        )

    if paths["workflow_state"].exists():
        queue_path = artifacts_dir / "fulltext_import" / "manual_pdf_queue.csv"
        queue_rows = load_csv_rows(queue_path)[1] if queue_path.exists() else []
        feedback_rows_for_state = load_all_pass_csv(run_dir, "artifacts/fulltext_review/pmc_mechanism_feedback.csv")
        errors.extend(
            validate_workflow_state(
                run_dir,
                paths["workflow_state"],
                queue_rows,
                feedback_rows_for_state,
                tables["pdf_download_shortlist"],
                tables["workflow_loop_decision"],
                min_big_workflow_loops,
                max_workflow_loops,
            )
        )
        try:
            workflow_state_payload = json.loads(paths["workflow_state"].read_text(encoding="utf-8"))
        except Exception:
            workflow_state_payload = {}
        workflow_status = str(workflow_state_payload.get("status", ""))
        errors.extend(
            validate_final_prompt_fit_density(
                workflow_status,
                access_phase,
                feedback_rows_for_state,
                tables.get("fulltext_review", []),
                tables.get("evidence_extraction", []),
            )
        )
        errors.extend(
            validate_prior_pass_pmc_cleanup(
                run_dir,
                workflow_status,
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
