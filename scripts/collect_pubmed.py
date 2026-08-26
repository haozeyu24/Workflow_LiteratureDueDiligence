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


WORKFLOW_ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = WORKFLOW_ROOT / "runs"

PUBMED_SEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_SUMMARY_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
PUBMED_FETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
NCBI_RATE_LIMIT_SECONDS = 0.34
USER_AGENT = "agenticWorkflow_LiteratureScreeningAndFullTextReview/0.1 (generic pubmed collector)"


def fetch_url(url: str) -> bytes:
    result = subprocess.run(
        [
            "curl",
            "--silent",
            "--show-error",
            "--fail",
            "--location",
            "--max-time",
            "60",
            "--user-agent",
            USER_AGENT,
            url,
        ],
        check=True,
        capture_output=True,
    )
    return result.stdout


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


def parse_constraints(constraints_path: Path) -> dict[str, int]:
    constraints: dict[str, int] = {}
    if not constraints_path.exists():
        return constraints
    for raw_line in constraints_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        match = re.match(r"^-?\s*([A-Za-z0-9_]+)\s*:\s*([0-9]+)\s*$", line)
        if not match:
            continue
        key, value = match.groups()
        constraints[key] = int(value)
    return constraints


def pubmed_search(query: str) -> list[str]:
    params = {
        "db": "pubmed",
        "term": query,
        "retmax": "10000",
        "retmode": "json",
        "sort": "date",
    }
    url = f"{PUBMED_SEARCH_URL}?{urllib.parse.urlencode(params)}"
    payload = json.loads(fetch_url(url).decode("utf-8"))
    return payload["esearchresult"]["idlist"]


def reset_metadata_collection(records_dir: Path, manifest_path: Path) -> None:
    if records_dir.exists():
        for path in records_dir.glob("*.json"):
            path.unlink()
    else:
        records_dir.mkdir(parents=True, exist_ok=True)
    if manifest_path.exists():
        manifest_path.unlink()


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


def fetch_abstracts(pmids: list[str]) -> dict[str, str]:
    params = {"db": "pubmed", "id": ",".join(pmids), "retmode": "xml"}
    url = f"{PUBMED_FETCH_URL}?{urllib.parse.urlencode(params)}"
    root = ET.fromstring(fetch_url(url))
    abstracts: dict[str, str] = {}
    for article in root.findall(".//PubmedArticle"):
        pmid = article.findtext(".//MedlineCitation/PMID", default="").strip()
        abstract = flatten_abstract_text(article.find(".//Article/Abstract"))
        if pmid:
            abstracts[pmid] = abstract
    return abstracts


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

    search_strategy_path = run_dir / "artifacts" / "search_strategy" / "search_strategy.md"
    constraints_path = run_dir / "constraints.md"
    manifest_path = run_dir / "artifacts" / "metadata_collection" / "paper_manifest.csv"
    records_dir = run_dir / "artifacts" / "metadata_collection" / "records"
    reset_metadata_collection(records_dir, manifest_path)

    queries = extract_queries(search_strategy_path)
    if not queries:
        print(f"No queries found in {search_strategy_path}")
        return 1

    constraints = parse_constraints(constraints_path)
    max_results_per_query = constraints.get("max_results_per_query", 10000)
    max_total_results = constraints.get("max_total_results")

    pmid_to_queries: dict[str, list[str]] = {}
    for query in queries:
        pmids = pubmed_search(query)[:max_results_per_query]
        for pmid in pmids:
            pmid_to_queries.setdefault(pmid, [])
            if query not in pmid_to_queries[pmid]:
                pmid_to_queries[pmid].append(query)
            if max_total_results is not None and len(pmid_to_queries) >= max_total_results:
                break
        time.sleep(NCBI_RATE_LIMIT_SECONDS)
        if max_total_results is not None and len(pmid_to_queries) >= max_total_results:
            break

    if not pmid_to_queries:
        print("No PubMed records found for supplied queries.")
        return 1

    rows: list[dict[str, str]] = []
    retrieval_batch = time.strftime("%Y%m%d")
    all_pmids = list(pmid_to_queries.keys())
    if max_total_results is not None:
        all_pmids = all_pmids[:max_total_results]
    for batch in batched(all_pmids, 200):
        summaries = fetch_summaries(batch)
        time.sleep(NCBI_RATE_LIMIT_SECONDS)
        abstracts = fetch_abstracts(batch)
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
            abstract = abstracts.get(pmid, "")
            record = {
                "paper_id": paper_id,
                "pmid": pmid,
                "doi": doi,
                "title": title,
                "abstract": abstract,
                "year": year,
                "journal": str(summary.get("full_journal_name", "")).strip(),
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
                    "year": year,
                    "journal": str(summary.get("full_journal_name", "")).strip(),
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

    print(
        f"Wrote {len(rows)} PubMed records to {manifest_path} "
        f"(max_results_per_query={max_results_per_query}, max_total_results={max_total_results if max_total_results is not None else 'unbounded'})"
    )
    print(f"Wrote per-paper metadata records to {records_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
