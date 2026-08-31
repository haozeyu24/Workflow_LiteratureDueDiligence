#!/usr/bin/env python3

from __future__ import annotations

import csv
import json
import subprocess
import sys
import time
import urllib.parse
from pathlib import Path

from pass_archive import active_artifacts_dir, run_input_path


WORKFLOW_ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = WORKFLOW_ROOT / "runs"
IDCONV_URL = "https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/"
EUROPE_PMC_SEARCH_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
OPENALEX_WORKS_URL = "https://api.openalex.org/works"
REQUEST_PAUSE_SECONDS = 0.34
BATCH_SIZE = 200

IMPORT_FIELDS = [
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
]

MANUAL_PDF_FIELDS = [
    "paper_id",
    "pmid",
    "pmcid",
    "doi",
    "title",
    "queue_reason",
    "preferred_source",
    "notes",
]


def load_csv(path: Path) -> list[dict[str, str]]:
    return list(csv.DictReader(path.open(encoding="utf-8")))


def parse_config(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    config: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line.startswith("- `") or "`:" not in line:
            continue
        try:
            key = line.split("`", 2)[1]
            value = line.split("`:", 1)[1].split("`", 2)[1]
        except IndexError:
            continue
        config[key] = value
    return config


def should_use_alternate_oa_lookup(config: dict[str, str]) -> bool:
    mode = config.get("fulltext_lookup_mode", "pmc_then_oa_final").strip() or "pmc_then_oa_final"
    if mode == "pmc_only":
        return False
    if mode == "exhaustive_oa":
        return True
    access_phase = config.get("access_phase", "pmc_learning").strip() or "pmc_learning"
    pdf_policy = config.get("pdf_policy", "continue_pmc_only").strip() or "continue_pmc_only"
    return access_phase == "final_access" or pdf_policy == "require_fulltext_completion"


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
            url,
        ],
        check=True,
        capture_output=True,
    )
    return result.stdout


def fetch_pmcid_map(pmids: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for start in range(0, len(pmids), BATCH_SIZE):
        batch = pmids[start : start + BATCH_SIZE]
        query = urllib.parse.urlencode({"ids": ",".join(batch), "format": "json"})
        payload = json.loads(fetch_url(f"{IDCONV_URL}?{query}").decode("utf-8"))
        for record in payload.get("records", []):
            pmid = str(record.get("pmid", "") or "")
            pmcid = str(record.get("pmcid", "") or "")
            if pmid:
                result[pmid] = pmcid
        time.sleep(REQUEST_PAUSE_SECONDS)
    return result


def normalize_doi(value: str) -> str:
    doi = (value or "").strip()
    if not doi:
        return ""
    doi = doi.removeprefix("https://doi.org/")
    doi = doi.removeprefix("http://doi.org/")
    doi = doi.removeprefix("doi:")
    return doi.strip()


def fetch_json(url: str) -> dict:
    payload = fetch_url(url)
    return json.loads(payload.decode("utf-8"))


def choose_oa_pdf(url_entries: object) -> str:
    if not isinstance(url_entries, list):
        return ""
    for entry in url_entries:
        if not isinstance(entry, dict):
            continue
        if entry.get("availabilityCode") != "OA":
            continue
        if entry.get("documentStyle") != "pdf":
            continue
        url = str(entry.get("url", "") or "").strip()
        if url:
            return url
    return ""


def europe_pmc_query(pmid: str, doi: str) -> str:
    if pmid:
        return f"EXT_ID:{pmid} AND SRC:MED"
    if doi:
        escaped = doi.replace('"', "")
        return f'DOI:"{escaped}"'
    return ""


def lookup_europe_pmc(pmid: str, doi: str) -> dict[str, str]:
    query = europe_pmc_query(pmid, doi)
    if not query:
        return {}
    params = urllib.parse.urlencode(
        {
            "query": query,
            "format": "json",
            "pageSize": "1",
            "resultType": "core",
        }
    )
    try:
        payload = fetch_json(f"{EUROPE_PMC_SEARCH_URL}?{params}")
    except Exception:
        return {}
    results = payload.get("resultList", {}).get("result", [])
    if not results:
        return {}
    result = results[0]
    url_entries = result.get("fullTextUrlList", {}).get("fullTextUrl", [])
    pmcid = str(result.get("pmcid", "") or "").strip()
    pdf_url = choose_oa_pdf(url_entries)
    xml_url = (
        f"https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML"
        if pmcid
        else ""
    )
    return {
        "pmcid": pmcid,
        "xml_url": xml_url,
        "pdf_url": pdf_url,
    }


def extract_openalex_pdf(result: dict) -> str:
    candidates: list[dict] = []
    best = result.get("best_oa_location")
    if isinstance(best, dict):
        candidates.append(best)
    primary = result.get("primary_location")
    if isinstance(primary, dict):
        candidates.append(primary)
    locations = result.get("locations")
    if isinstance(locations, list):
        candidates.extend(entry for entry in locations if isinstance(entry, dict))
    for entry in candidates:
        if entry.get("is_oa") is False:
            continue
        pdf_url = str(entry.get("pdf_url", "") or "").strip()
        if pdf_url:
            return pdf_url
    return ""


def lookup_openalex(pmid: str, doi: str) -> dict[str, str]:
    filters: list[str] = []
    normalized_doi = normalize_doi(doi)
    if normalized_doi:
        filters.append(f"doi:{normalized_doi}")
    if pmid:
        filters.append(f"pmid:{pmid}")
    for filter_value in filters:
        params = urllib.parse.urlencode({"filter": filter_value, "per-page": "1"})
        try:
            payload = fetch_json(f"{OPENALEX_WORKS_URL}?{params}")
        except Exception:
            continue
        results = payload.get("results", [])
        if not results:
            continue
        pdf_url = extract_openalex_pdf(results[0])
        if pdf_url:
            return {"pdf_url": pdf_url}
    return {}


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python3 scripts/prepare_import_status.py <run_id>")
        return 1

    run_id = sys.argv[1].strip()
    run_dir = RUNS_DIR / run_id
    artifacts_dir = active_artifacts_dir(run_dir)
    manifest_path = artifacts_dir / "metadata_collection" / "paper_manifest.csv"
    review2_path = artifacts_dir / "abstract_review" / "abstract_review2.csv"
    import_dir = artifacts_dir / "fulltext_import"
    import_path = import_dir / "import_status.csv"
    manual_pdf_path = import_dir / "manual_pdf_queue.csv"
    config = parse_config(run_input_path(run_dir, "run_config.md"))
    use_alternate_oa_lookup = should_use_alternate_oa_lookup(config)

    if not manifest_path.exists():
        print(f"Paper manifest not found: {manifest_path}")
        return 1
    if not review2_path.exists():
        print(f"Second abstract review table not found: {review2_path}")
        return 1

    import_dir.mkdir(parents=True, exist_ok=True)

    manifest_rows = load_csv(manifest_path)
    manifest_by_id = {row["paper_id"]: row for row in manifest_rows}
    review2_rows = load_csv(review2_path)
    selected = [row for row in review2_rows if row.get("promotion_decision", "") == "advance_to_import"]

    pmids = sorted({row.get("pmid", "") for row in selected if row.get("pmid", "")})
    pmcid_map = fetch_pmcid_map(pmids) if pmids else {}
    europe_pmc_cache: dict[tuple[str, str], dict[str, str]] = {}
    openalex_cache: dict[tuple[str, str], dict[str, str]] = {}

    import_rows: list[dict[str, str]] = []
    manual_pdf_rows: list[dict[str, str]] = []
    for row in selected:
        paper_id = row["paper_id"]
        manifest_row = manifest_by_id.get(paper_id, {})
        pmid = row.get("pmid", "") or manifest_row.get("pmid", "")
        doi = normalize_doi(manifest_row.get("doi", ""))
        pmcid = pmcid_map.get(pmid, "")
        route = ""
        xml_url = ""
        pdf_url = ""
        notes = ""

        if pmcid:
            route = "ncbi_pmc_xml"
            notes = "PMCID resolved from NCBI idconv."
        elif use_alternate_oa_lookup:
            cache_key = (pmid, doi)
            europe_pmc = europe_pmc_cache.get(cache_key)
            if europe_pmc is None:
                europe_pmc = lookup_europe_pmc(pmid, doi)
                europe_pmc_cache[cache_key] = europe_pmc
                time.sleep(REQUEST_PAUSE_SECONDS)
            pmcid = europe_pmc.get("pmcid", "")
            xml_url = europe_pmc.get("xml_url", "")
            pdf_url = europe_pmc.get("pdf_url", "")
            if pmcid and xml_url:
                route = "europe_pmc_xml"
                notes = "PMCID recovered via Europe PMC."
            elif pdf_url:
                route = "oa_pdf"
                notes = "Direct open-access PDF recovered via Europe PMC."
            else:
                openalex = openalex_cache.get(cache_key)
                if openalex is None:
                    openalex = lookup_openalex(pmid, doi)
                    openalex_cache[cache_key] = openalex
                    time.sleep(REQUEST_PAUSE_SECONDS)
                pdf_url = openalex.get("pdf_url", "")
                if pdf_url:
                    route = "oa_pdf"
                    notes = "Direct open-access PDF recovered via OpenAlex."
                else:
                    notes = "No automated full-text source found via NCBI PMC, Europe PMC, or OpenAlex; user PDF fallback will be needed."
        else:
            notes = (
                "No NCBI PMCID found. Alternate open-access lookup is deferred during PMC-learning "
                "to keep early full-text import focused and fast."
            )

        has_pmc_access = route in {"ncbi_pmc_xml", "europe_pmc_xml"}
        has_automated_access = bool(route)
        import_rows.append(
            {
                "paper_id": paper_id,
                "pmid": pmid,
                "pmcid": pmcid,
                "doi": doi,
                "title": manifest_row.get("title", ""),
                "fulltext_access_route": route or "none",
                "fulltext_xml_url": xml_url,
                "fulltext_pdf_url": pdf_url,
                "pmc_access_status": "available" if has_pmc_access else "missing",
                "pmc_parse_status": "not_attempted",
                "pdf_needed": "no" if has_pmc_access else "yes",
                "pdf_import_status": "not_attempted" if has_automated_access else "missing",
                "normalized_path": "",
                "notes": notes,
            }
        )
        if not has_pmc_access:
            manual_pdf_rows.append(
                {
                    "paper_id": paper_id,
                    "pmid": pmid,
                    "pmcid": "",
                    "doi": doi,
                    "title": manifest_row.get("title", ""),
                    "queue_reason": (
                        "Open-access PDF detected but no PMC XML route was available."
                        if route == "oa_pdf"
                        else "No automated full-text source detected during import preparation."
                    ),
                    "preferred_source": "open_access_pdf" if route == "oa_pdf" else "publisher_pdf_or_user_download",
                    "notes": "",
                }
            )

    with import_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=IMPORT_FIELDS)
        writer.writeheader()
        writer.writerows(import_rows)

    with manual_pdf_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=MANUAL_PDF_FIELDS)
        writer.writeheader()
        writer.writerows(manual_pdf_rows)

    print(
        f"Prepared import status for {len(import_rows)} papers at {import_path} "
        f"(pmc_available={sum(1 for row in import_rows if row['pmc_access_status'] == 'available')}, "
        f"pmc_missing={sum(1 for row in import_rows if row['pmc_access_status'] == 'missing')})"
    )
    print(f"Wrote manual PDF queue to {manual_pdf_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
