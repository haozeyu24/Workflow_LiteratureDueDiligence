#!/usr/bin/env python3

from __future__ import annotations

import csv
import json
import subprocess
import sys
import time
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path

from pass_archive import active_artifacts_dir


WORKFLOW_ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = WORKFLOW_ROOT / "runs"
NCBI_EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
REQUEST_PAUSE_SECONDS = 0.34
MIN_BODY_CHARS = 1000
STATUS_WRITE_INTERVAL = 25

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


def xml_local_name(tag: str) -> str:
    return tag.split("}", 1)[-1]


def find_first(root: ET.Element, name: str) -> ET.Element | None:
    return next((element for element in root.iter() if xml_local_name(element.tag) == name), None)


def clean_text(text: str) -> str:
    return " ".join(text.split())


def extract_sections(root: ET.Element) -> list[dict[str, str]]:
    body = find_first(root, "body")
    if body is None:
        return []
    sections: list[dict[str, str]] = []
    for sec in body.iter():
        if xml_local_name(sec.tag) != "sec":
            continue
        title_element = next((child for child in sec if xml_local_name(child.tag) == "title"), None)
        title = clean_text("".join(title_element.itertext())) if title_element is not None else ""
        paragraphs = []
        for child in sec:
            if xml_local_name(child.tag) == "p":
                paragraph = clean_text("".join(child.itertext()))
                if paragraph:
                    paragraphs.append(paragraph)
        text = "\n\n".join(paragraphs).strip()
        if title or text:
            sections.append({"title": title, "text": text})
    return sections


def normalize_pmc_xml(xml_path: Path, normalized_path: Path, paper_id: str, pmid: str, pmcid: str, doi: str, title: str) -> tuple[bool, str]:
    try:
        root = ET.parse(xml_path).getroot()
    except ET.ParseError as exc:
        return False, f"PMC XML parse error: {exc}"

    body = find_first(root, "body")
    if body is None:
        return False, "PMC XML body element is missing."

    raw_text = clean_text(" ".join(text for text in body.itertext() if text and text.strip()))
    if len(raw_text) < MIN_BODY_CHARS:
        return False, "PMC XML body text is too short for normalization."

    article_title = title
    title_group = find_first(root, "article-title")
    if title_group is not None:
        candidate = clean_text("".join(title_group.itertext()))
        if candidate:
            article_title = candidate

    payload = {
        "paper_id": paper_id,
        "pmid": pmid,
        "pmcid": pmcid,
        "doi": doi,
        "title": article_title,
        "source_type": "pmc_xml",
        "source_path": str(xml_path),
        "raw_text": raw_text,
        "sections": extract_sections(root),
    }
    normalized_path.parent.mkdir(parents=True, exist_ok=True)
    normalized_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return True, ""


def download_pmc_xml(pmcid: str, xml_path: Path) -> tuple[bool, str]:
    query = urllib.parse.urlencode({"db": "pmc", "id": pmcid, "retmode": "xml"})
    try:
        payload = fetch_url(f"{NCBI_EFETCH_URL}?{query}")
    except Exception as exc:
        return False, f"PMC download error: {exc}"
    if not payload:
        return False, "PMC download returned empty content."
    xml_path.parent.mkdir(parents=True, exist_ok=True)
    xml_path.write_bytes(payload)
    time.sleep(REQUEST_PAUSE_SECONDS)
    return True, ""


def load_csv(path: Path) -> list[dict[str, str]]:
    return list(csv.DictReader(path.open(encoding="utf-8")))


def write_manual_pdf_queue(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=MANUAL_PDF_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def write_import_status(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys() if rows else [])
        if rows:
            writer.writeheader()
            writer.writerows(rows)


def delete_if_exists(path: Path) -> None:
    if path.exists():
        path.unlink()


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python3 scripts/import_pmc_fulltext.py <run_id>")
        return 1

    run_id = sys.argv[1].strip()
    run_dir = RUNS_DIR / run_id
    import_dir = active_artifacts_dir(run_dir) / "fulltext_import"
    import_path = import_dir / "import_status.csv"
    manual_pdf_path = import_dir / "manual_pdf_queue.csv"
    pmc_xml_dir = import_dir / "PMC_XML"
    pmc_normalized_dir = pmc_xml_dir / "normalized"

    if not import_path.exists():
        print(f"Import status not found: {import_path}")
        return 1

    rows = load_csv(import_path)
    manual_pdf_rows: list[dict[str, str]] = []
    downloaded = 0
    normalized = 0
    usable = 0
    unusable = 0

    for index, row in enumerate(rows, start=1):
        pmcid = row.get("pmcid", "") or ""
        if row.get("pmc_access_status", "") != "available" or not pmcid:
            row["pmc_access_status"] = "missing"
            row["pmc_parse_status"] = "not_attempted"
            row["pdf_needed"] = "yes"
            row["pdf_import_status"] = "missing"
            row["normalized_path"] = ""
            manual_pdf_rows.append(
                {
                    "paper_id": row["paper_id"],
                    "pmid": row["pmid"],
                    "pmcid": "",
                    "doi": row["doi"],
                    "title": row["title"],
                    "queue_reason": "No PMCID coverage available.",
                    "preferred_source": "publisher_pdf_or_user_download",
                    "notes": row.get("notes", ""),
                }
                )
            continue

        xml_path = pmc_xml_dir / f"{pmcid}.xml"
        normalized_path = pmc_normalized_dir / f"{pmcid}.json"

        if not xml_path.exists():
            ok, error = download_pmc_xml(pmcid, xml_path)
            if ok:
                downloaded += 1
            else:
                row["pmc_parse_status"] = "unusable"
                row["pdf_needed"] = "yes"
                row["pdf_import_status"] = "missing"
                row["normalized_path"] = ""
                row["notes"] = error
                unusable += 1
                manual_pdf_rows.append(
                    {
                        "paper_id": row["paper_id"],
                        "pmid": row["pmid"],
                        "pmcid": pmcid,
                        "doi": row["doi"],
                        "title": row["title"],
                        "queue_reason": "PMC XML download failed.",
                        "preferred_source": "publisher_pdf_or_user_download",
                        "notes": error,
                    }
                )
                continue

        ok, error = normalize_pmc_xml(
            xml_path,
            normalized_path,
            row["paper_id"],
            row["pmid"],
            pmcid,
            row["doi"],
            row["title"],
        )
        if ok:
            row["pmc_parse_status"] = "usable"
            row["pdf_needed"] = "no"
            row["pdf_import_status"] = "not_attempted"
            row["normalized_path"] = str(normalized_path)
            row["notes"] = "PMC XML downloaded and normalized."
            normalized += 1
            usable += 1
        else:
            delete_if_exists(xml_path)
            delete_if_exists(normalized_path)
            row["pmc_parse_status"] = "unusable"
            row["pdf_needed"] = "yes"
            row["pdf_import_status"] = "missing"
            row["normalized_path"] = ""
            row["notes"] = f"{error} Unusable PMC XML deleted from run artifacts."
            unusable += 1
            manual_pdf_rows.append(
                {
                    "paper_id": row["paper_id"],
                    "pmid": row["pmid"],
                    "pmcid": pmcid,
                    "doi": row["doi"],
                    "title": row["title"],
                    "queue_reason": "PMC XML unusable for normalization.",
                    "preferred_source": "publisher_pdf_or_user_download",
                    "notes": f"{error} Unusable PMC XML deleted from run artifacts.",
                }
            )

        if index % STATUS_WRITE_INTERVAL == 0:
            write_import_status(import_path, rows)
            write_manual_pdf_queue(manual_pdf_path, manual_pdf_rows)
            print(
                f"PMC import progress: processed={index}/{len(rows)} "
                f"downloaded={downloaded} normalized={normalized} "
                f"usable={usable} unusable={unusable} pdf_queue={len(manual_pdf_rows)}",
                flush=True,
            )

    write_import_status(import_path, rows)
    write_manual_pdf_queue(manual_pdf_path, manual_pdf_rows)

    print(
        f"PMC import complete for {len(rows)} papers: downloaded={downloaded} "
        f"normalized={normalized} usable={usable} unusable={unusable} "
        f"pdf_queue={len(manual_pdf_rows)}"
    )
    print(f"Updated import status at {import_path}")
    print(f"Wrote manual PDF queue to {manual_pdf_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
