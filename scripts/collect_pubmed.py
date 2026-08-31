#!/usr/bin/env python3

from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
import time
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path

from pass_archive import (
    active_artifacts_dir,
    archive_path_for_pass,
    current_pass_number,
    learned_revision_path,
    load_all_pass_csv,
    run_input_path,
    snapshot_current_pass,
)


WORKFLOW_ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = WORKFLOW_ROOT / "runs"
BLOCKLIST_PATH = WORKFLOW_ROOT / "resources" / "journal_blocklist.csv"

PUBMED_SEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_SUMMARY_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
PUBMED_FETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
NCBI_RATE_LIMIT_SECONDS = 0.34
USER_AGENT = "agenticWorkflow_LiteratureScreeningAndFullTextReview/0.1 (generic pubmed collector)"
LEARNED_RERUN_COLLECTION_REVIEW_RATIO = 0.80
PUBMED_RECORD_BATCH_SIZE = 100
TRANSIENT_CURL_EXIT_CODES = {18, 22, 28, 35, 52, 55, 56, 92}


def normalize_journal_name(value: str) -> str:
    return " ".join(
        re.sub(r"[^a-z0-9]+", " ", (value or "").lower()).split()
    )


def load_journal_blocklist(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        rows = []
        for row in csv.DictReader(handle):
            match_type = (row.get("match_type") or "").strip()
            match_value = (row.get("match_value") or "").strip()
            rationale = (row.get("rationale") or "").strip()
            if not match_type or not match_value:
                continue
            rows.append(
                {
                    "match_type": match_type,
                    "match_value": match_value,
                    "normalized_value": normalize_journal_name(match_value),
                    "rationale": rationale,
                }
            )
        return rows


def blocked_journal_rule(
    journal: str, blocklist: list[dict[str, str]]
) -> dict[str, str] | None:
    normalized_journal = normalize_journal_name(journal)
    if not normalized_journal:
        return None
    for rule in blocklist:
        match_type = rule.get("match_type", "")
        normalized_value = rule.get("normalized_value", "")
        if match_type == "journal_exact" and normalized_journal == normalized_value:
            return rule
        if match_type == "journal_prefix" and normalized_journal.startswith(
            normalized_value
        ):
            return rule
    return None


def write_blocked_venue_records(
    path: Path, rows: list[dict[str, str]]
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
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
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def fetch_url(url: str) -> bytes:
    command = [
        "curl",
        "--http1.1",
        "--silent",
        "--show-error",
        "--fail",
        "--location",
        "--max-time",
        "60",
        "--user-agent",
        USER_AGENT,
        url,
    ]
    last_error: subprocess.CalledProcessError | None = None
    for attempt in range(1, 4):
        try:
            result = subprocess.run(command, check=True, capture_output=True)
            return result.stdout
        except subprocess.CalledProcessError as error:
            last_error = error
            if error.returncode not in TRANSIENT_CURL_EXIT_CODES or attempt == 3:
                raise
            time.sleep(attempt * 2)
    assert last_error is not None
    raise last_error


def text_or_none(value: str | None) -> str:
    return value.strip() if value else ""


def batched(items: list[str], size: int) -> list[list[str]]:
    return [items[i : i + size] for i in range(0, len(items), size)]


def extract_queries(search_strategy_path: Path) -> list[str]:
    queries: list[str] = []
    in_query_section = False

    for raw_line in search_strategy_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line.startswith("## "):
            in_query_section = line.lower() == "## query set"
            continue
        if not in_query_section or not line:
            continue
        match = re.match(r"^\d+\.\s+(.*)$", line)
        if not match:
            continue
        query = match.group(1).strip()
        if query.startswith("`") and query.endswith("`") and len(query) >= 2:
            query = query[1:-1].strip()
        if query.startswith("<") and query.endswith(">") and "PubMed query" in query:
            continue
        if query:
            queries.append(query)

    return queries


FORBIDDEN_CAP_KEYS = {
    "max_results_per_query",
    "max_total_results",
    "retmax",
    "record_cap",
    "retrieval_cap",
    "collection_cap",
}


def find_forbidden_cap_constraints(constraints_path: Path) -> list[str]:
    forbidden: list[str] = []
    if not constraints_path.exists():
        return forbidden
    for line_number, raw_line in enumerate(constraints_path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip().replace("`", "")
        if not line or line.startswith("#"):
            continue
        match = re.match(r"^-?\s*([A-Za-z0-9_]+)\s*:", line)
        if not match:
            continue
        key = match.group(1)
        if key in FORBIDDEN_CAP_KEYS:
            forbidden.append(f"{constraints_path}:{line_number}: {key}")
    return forbidden


def pubmed_search(query: str) -> tuple[list[str], int]:
    page_size = 10000
    first_params = {
        "db": "pubmed",
        "term": query,
        "retmax": "0",
        "retmode": "json",
        "sort": "date",
    }
    first_url = f"{PUBMED_SEARCH_URL}?{urllib.parse.urlencode(first_params)}"
    first_payload = json.loads(fetch_url(first_url).decode("utf-8"))
    raw_count = int(first_payload["esearchresult"].get("count", "0"))

    pmids: list[str] = []
    for retstart in range(0, raw_count, page_size):
        retmax = min(page_size, raw_count - retstart)
        params = {
            "db": "pubmed",
            "term": query,
            "retstart": str(retstart),
            "retmax": str(retmax),
            "retmode": "json",
            "sort": "date",
        }
        url = f"{PUBMED_SEARCH_URL}?{urllib.parse.urlencode(params)}"
        payload = json.loads(fetch_url(url).decode("utf-8"))
        page_pmids = payload["esearchresult"].get("idlist", [])
        pmids.extend(str(pmid) for pmid in page_pmids)
        time.sleep(NCBI_RATE_LIMIT_SECONDS)
        if len(page_pmids) < retmax:
            break

    return pmids, raw_count


def write_query_diagnostics(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
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
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def read_existing_query_diagnostics(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return [
            row
            for row in reader
            if any((value or "").strip() for value in row.values())
            and (row.get("round_id", "").strip() != "collection")
        ]


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def prior_pass_manifest_count(run_dir: Path, pass_number: int) -> int:
    if pass_number <= 1:
        return 0
    path = archive_path_for_pass(run_dir, pass_number - 1) / "artifacts" / "metadata_collection" / "paper_manifest.csv"
    return len(load_csv(path))


def learned_rerun_collection_warnings(run_dir: Path, collected_count: int) -> list[str]:
    pass_number = current_pass_number(run_dir)
    if pass_number <= 1:
        return []
    prior_count = prior_pass_manifest_count(run_dir, pass_number)
    if prior_count <= 0:
        return []
    review_threshold = int(prior_count * LEARNED_RERUN_COLLECTION_REVIEW_RATIO)
    if collected_count <= review_threshold:
        return []
    return [
        (
            f"Learned rerun collection requires reviewer confirmation: pass_{pass_number:03d} collected "
            f"{collected_count} unique records versus {prior_count} in pass_{pass_number - 1:03d}. "
            f"This exceeds the {LEARNED_RERUN_COLLECTION_REVIEW_RATIO:.0%} confirmation threshold. "
            "This is not automatically invalid, but the run should verify that pass 1 learning was "
            "actually applied to sharpen scope and that any larger set is justified by the user's prompt, "
            "not by broad context/modifier terms becoming standalone drivers."
        )
    ]


def require_guidance_revision_for_learned_rerun(run_dir: Path) -> list[str]:
    feedback_rows = load_all_pass_csv(run_dir, "artifacts/fulltext_review/pmc_mechanism_feedback.csv")
    if not feedback_rows:
        return []

    latest_feedback = feedback_rows[-1]
    latest_loop_id = latest_feedback.get("loop_id", "").strip()
    latest_pdf_decision = latest_feedback.get("pdf_deferral_decision", "").strip()
    if latest_pdf_decision != "defer_pdfs":
        return []

    revision_rows = load_all_pass_csv(run_dir, "artifacts/workflow_control/run_guidance_revision_log.csv")
    matching_rows = [
        row for row in revision_rows
        if row.get("feedback_loop_id", "").strip() == latest_loop_id
    ]
    if not matching_rows:
        return [
            "Learned rerun is blocked because the latest PMC feedback "
            f"({latest_loop_id}) has not been incorporated into run guidance. "
            "Revise instruction.md/topic.md, generate search_strategy.md from the revised guidance plus pmc_mechanism_feedback.csv, "
            "and record the revision in artifacts/workflow_control/run_guidance_revision_log.csv."
        ]

    latest_revision = matching_rows[-1]
    missing_paths = []
    for field in ("revised_instruction_path", "revised_topic_path", "search_strategy_path"):
        value = latest_revision.get(field, "").strip()
        if not value:
            missing_paths.append(field)
            continue
        candidate = Path(value)
        if not candidate.is_absolute():
            candidate = run_dir / candidate
        if not candidate.exists():
            missing_paths.append(field)
    if missing_paths:
        return [
            "Learned guidance revision log row is incomplete for "
            f"{latest_loop_id}; missing or non-existent paths: {', '.join(missing_paths)}."
        ]
    missing_learning_fields = []
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
        if not latest_revision.get(field, "").strip():
            missing_learning_fields.append(field)
    if missing_learning_fields:
        return [
            "Learned guidance revision log row does not document enough pass-1 learning for "
            f"{latest_loop_id}; missing fields: {', '.join(missing_learning_fields)}. "
            "A learned rerun must record retained in-scope mechanisms, noise/exclusion changes, "
            "missing in-scope terms, reviewer-rule changes, and a rationale for how the revised "
            "strategy focuses the run on the user's prompt."
        ]
    return []


def learned_search_strategy_path(run_dir: Path, default_path: Path) -> Path:
    feedback_rows = load_all_pass_csv(run_dir, "artifacts/fulltext_review/pmc_mechanism_feedback.csv")
    if not feedback_rows:
        return default_path

    latest_feedback = feedback_rows[-1]
    latest_loop_id = latest_feedback.get("loop_id", "").strip()
    if latest_feedback.get("pdf_deferral_decision", "").strip() != "defer_pdfs":
        return default_path

    revision_rows = [
        row for row in load_all_pass_csv(run_dir, "artifacts/workflow_control/run_guidance_revision_log.csv")
        if row.get("feedback_loop_id", "").strip() == latest_loop_id
    ]
    if not revision_rows:
        return default_path

    value = revision_rows[-1].get("search_strategy_path", "").strip()
    if not value:
        return default_path
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = run_dir / candidate
    return candidate


def reset_metadata_collection(
    records_dir: Path, manifest_path: Path, blocked_path: Path
) -> None:
    if records_dir.exists():
        for path in records_dir.glob("*.json"):
            path.unlink()
    else:
        records_dir.mkdir(parents=True, exist_ok=True)
    if manifest_path.exists():
        manifest_path.unlink()
    if blocked_path.exists():
        blocked_path.unlink()


def fetch_summaries(pmids: list[str]) -> list[dict]:
    params = {"db": "pubmed", "id": ",".join(pmids), "retmode": "xml"}
    url = f"{PUBMED_SUMMARY_URL}?{urllib.parse.urlencode(params)}"
    root = ET.fromstring(fetch_url(url))
    records = []
    for docsum in root.findall(".//DocSum"):
        record: dict[str, object] = {
            "authors": [],
            "article_ids": {},
            "full_journal_name": "",
            "pubdate": "",
            "title": "",
        }
        uid = docsum.findtext("Id", default="")
        record["pmid"] = uid
        for item in docsum.findall("Item"):
            name = item.attrib.get("Name")
            if name == "Title":
                record["title"] = text_or_none(item.text)
            elif name == "PubDate":
                record["pubdate"] = text_or_none(item.text)
            elif name == "FullJournalName":
                record["full_journal_name"] = text_or_none(item.text)
            elif name == "AuthorList":
                record["authors"] = [text_or_none(child.text) for child in item.findall("Item") if child.text]
            elif name == "ArticleIds":
                article_ids: dict[str, str] = {}
                for child in item.findall("Item"):
                    id_type = child.attrib.get("Name")
                    if id_type and child.text:
                        article_ids[id_type] = text_or_none(child.text)
                record["article_ids"] = article_ids
        records.append(record)
    return records


def flatten_abstract_text(abstract_node: ET.Element | None) -> str:
    if abstract_node is None:
        return ""
    parts: list[str] = []
    for abstract_text in abstract_node.findall("AbstractText"):
        label = text_or_none(abstract_text.attrib.get("Label"))
        text = "".join(abstract_text.itertext()).strip()
        if not text:
            continue
        parts.append(f"{label}: {text}" if label else text)
    return "\n\n".join(parts).strip()


def fetch_article_details(pmids: list[str]) -> dict[str, dict[str, object]]:
    params = {"db": "pubmed", "id": ",".join(pmids), "retmode": "xml"}
    url = f"{PUBMED_FETCH_URL}?{urllib.parse.urlencode(params)}"
    root = ET.fromstring(fetch_url(url))
    details: dict[str, dict[str, object]] = {}
    for article in root.findall(".//PubmedArticle"):
        pmid = article.findtext(".//MedlineCitation/PMID", default="").strip()
        abstract = flatten_abstract_text(article.find(".//Article/Abstract"))
        publication_types = [
            text_or_none(publication_type.text)
            for publication_type in article.findall(".//PublicationTypeList/PublicationType")
            if text_or_none(publication_type.text)
        ]
        if pmid:
            details[pmid] = {
                "abstract": abstract,
                "publication_types": publication_types,
            }
    return details


def year_from_pubdate(pubdate: str) -> str:
    if not pubdate:
        return ""
    for token in pubdate.replace("/", " ").replace("-", " ").split():
        if token.isdigit() and len(token) == 4:
            return token
    return ""


def paper_id_from_pmid(pmid: str) -> str:
    return f"pmid-{pmid}"


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python3 scripts/collect_pubmed.py <run_id>")
        return 1

    run_id = sys.argv[1].strip()
    if not run_id:
        print("run_id must be non-empty")
        return 1

    run_dir = RUNS_DIR / run_id
    if not run_dir.exists():
        print(f"Run does not exist: {run_dir}")
        return 1

    artifacts_dir = active_artifacts_dir(run_dir)
    search_strategy_path = artifacts_dir / "search_strategy" / "search_strategy.md"
    constraints_path = learned_revision_path(run_dir, "revised_constraints_path") or run_input_path(run_dir, "constraints.md")
    query_diagnostics_path = artifacts_dir / "search_strategy" / "query_diagnostics.csv"
    manifest_path = artifacts_dir / "metadata_collection" / "paper_manifest.csv"
    records_dir = artifacts_dir / "metadata_collection" / "records"
    blocked_venues_path = artifacts_dir / "metadata_collection" / "blocked_venue_records.csv"
    journal_blocklist = load_journal_blocklist(BLOCKLIST_PATH)

    guidance_errors = require_guidance_revision_for_learned_rerun(run_dir)
    if guidance_errors:
        print("Run guidance revision is required before learned PubMed collection.")
        for error in guidance_errors:
            print(f"- {error}")
        return 1

    search_strategy_path = learned_search_strategy_path(run_dir, search_strategy_path)
    queries = extract_queries(search_strategy_path)
    if not queries:
        print(f"No queries found in {search_strategy_path}")
        return 1

    forbidden_caps = find_forbidden_cap_constraints(constraints_path)
    if forbidden_caps:
        print("PubMed collection caps are forbidden by workflow policy.")
        print("Remove these constraints and use query refinement instead:")
        for cap in forbidden_caps:
            print(f"- {cap}")
        return 1

    snapshot_dir = snapshot_current_pass(run_dir, "before_pubmed_collection_overwrite")
    if snapshot_dir:
        print(f"Archived current pass before collection overwrite at {snapshot_dir}")

    reset_metadata_collection(records_dir, manifest_path, blocked_venues_path)

    pmid_to_queries: dict[str, list[str]] = {}
    diagnostics_rows = read_existing_query_diagnostics(query_diagnostics_path)
    collection_diagnostics_rows: list[dict[str, str]] = []
    for query_index, query in enumerate(queries, start=1):
        pmids, raw_count = pubmed_search(query)
        collection_diagnostics_rows.append(
            {
                "round_id": "collection",
                "query_id": f"q{query_index}",
                "query": query,
                "raw_hit_count": str(raw_count),
                "collected_count": str(len(pmids)),
                "truncated_by_constraint": "no",
                "sample_size": "",
                "sample_strategy": "",
                "sampled_on_topic_count": "",
                "sampled_noise_count": "",
                "estimated_precision": "",
                "dominant_noise_classes": "",
                "missing_concepts": "",
                "recall_signals": "",
                "decision": "accepted_for_collection",
                "revision_rationale": "",
            }
        )
        for pmid in pmids:
            pmid_to_queries.setdefault(pmid, [])
            if query not in pmid_to_queries[pmid]:
                pmid_to_queries[pmid].append(query)

    if not pmid_to_queries:
        diagnostics_rows.extend(collection_diagnostics_rows)
        write_query_diagnostics(query_diagnostics_path, diagnostics_rows)
        print("No PubMed records found for supplied queries.")
        return 1

    collection_warnings = learned_rerun_collection_warnings(run_dir, len(pmid_to_queries))
    for warning in collection_warnings:
        print(f"Warning: {warning}")

    rows: list[dict[str, str]] = []
    blocked_rows: list[dict[str, str]] = []
    retrieval_batch = time.strftime("%Y%m%d")
    all_pmids = list(pmid_to_queries.keys())
    for batch in batched(all_pmids, PUBMED_RECORD_BATCH_SIZE):
        summaries = fetch_summaries(batch)
        time.sleep(NCBI_RATE_LIMIT_SECONDS)
        article_details = fetch_article_details(batch)
        time.sleep(NCBI_RATE_LIMIT_SECONDS)
        for summary in summaries:
            pmid = str(summary["pmid"])
            title = str(summary.get("title", "")).strip()
            pubdate = str(summary.get("pubdate", "")).strip()
            year = year_from_pubdate(pubdate)
            article_ids = summary.get("article_ids", {})
            if not isinstance(article_ids, dict):
                article_ids = {}
            doi = str(article_ids.get("doi", ""))
            paper_id = paper_id_from_pmid(pmid)
            authors = summary.get("authors", [])
            if not isinstance(authors, list):
                authors = []
            details = article_details.get(pmid, {})
            abstract = str(details.get("abstract", ""))
            publication_types = details.get("publication_types", [])
            if not isinstance(publication_types, list):
                publication_types = []
            journal_name = str(summary.get("full_journal_name", "")).strip()
            blocked_rule = blocked_journal_rule(journal_name, journal_blocklist)
            if blocked_rule is not None:
                blocked_rows.append(
                    {
                        "paper_id": paper_id,
                        "pmid": pmid,
                        "doi": doi,
                        "title": title,
                        "journal": journal_name,
                        "year": year,
                        "source_query": "; ".join(pmid_to_queries.get(pmid, [])),
                        "match_type": blocked_rule.get("match_type", ""),
                        "match_value": blocked_rule.get("match_value", ""),
                        "block_rationale": blocked_rule.get("rationale", ""),
                    }
                )
                continue
            record = {
                "paper_id": paper_id,
                "pmid": pmid,
                "doi": doi,
                "title": title,
                "abstract": abstract,
                "publication_types": publication_types,
                "year": year,
                "journal": journal_name,
                "authors": authors,
                "source_queries": pmid_to_queries.get(pmid, []),
                "retrieval_batch": retrieval_batch,
                "links": {
                    "pubmed": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                    "publisher": f"https://doi.org/{doi}" if doi else "",
                },
            }
            record_path = records_dir / f"{paper_id}.json"
            record_path.write_text(json.dumps(record, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
            rows.append(
                {
                    "paper_id": paper_id,
                    "pmid": pmid,
                    "doi": doi,
                    "title": title,
                    "abstract": abstract,
                    "publication_types": ";".join(
                        str(publication_type).strip()
                        for publication_type in publication_types
                        if str(publication_type).strip()
                    ),
                    "year": year,
                    "journal": journal_name,
                    "authors": ";".join(str(author).strip() for author in authors if str(author).strip()),
                    "source_query": "; ".join(pmid_to_queries.get(pmid, [])),
                    "retrieval_batch": retrieval_batch,
                    "record_path": str(record_path.relative_to(run_dir)),
                }
            )

    rows.sort(key=lambda row: (row["year"], row["pmid"]), reverse=True)
    with manifest_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
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
        )
        writer.writeheader()
        writer.writerows(rows)

    if blocked_rows:
        blocked_rows.sort(key=lambda row: (row["journal"].lower(), row["pmid"]))
        write_blocked_venue_records(blocked_venues_path, blocked_rows)

    diagnostics_rows.extend(collection_diagnostics_rows)
    write_query_diagnostics(query_diagnostics_path, diagnostics_rows)
    print(
        f"Wrote {len(rows)} PubMed records to {manifest_path} "
        "(no PubMed collection caps allowed)"
    )
    if blocked_rows:
        print(
            f"Blocked {len(blocked_rows)} papers by venue policy at "
            f"{blocked_venues_path}"
        )
    print(f"Wrote query hit-count diagnostics to {query_diagnostics_path}")
    print(f"Wrote per-paper metadata records to {records_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
