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
EUROPE_PMC_XML_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML"
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


def append_note(existing: str, message: str) -> str:
    existing = (existing or "").strip()
    message = (message or "").strip()
    if not existing:
        return message
    if not message:
        return existing
    return f"{existing} {message}"


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


def download_europe_pmc_xml(url: str, xml_path: Path) -> tuple[bool, str]:
    try:
        payload = fetch_url(url)
    except Exception as exc:
        return False, f"Europe PMC XML download error: {exc}"
    if not payload:
        return False, "Europe PMC XML download returned empty content."
    xml_path.parent.mkdir(parents=True, exist_ok=True)
    xml_path.write_bytes(payload)
    time.sleep(REQUEST_PAUSE_SECONDS)
    return True, ""


def staged_pdf_filename(row: dict[str, str]) -> str:
    pmid = row.get("pmid", "").strip()
    if pmid:
        return f"PMID {pmid}.pdf"
    return f"{row.get('paper_id', '').strip()}.pdf"


def download_pdf(url: str, pdf_path: Path) -> tuple[bool, str]:
    try:
        payload = fetch_url(url)
    except Exception as exc:
        return False, f"Open-access PDF download error: {exc}"
    if not payload:
        return False, "Open-access PDF download returned empty content."
    if b"%PDF-" not in payload[:1024]:
        return False, "Open-access PDF URL did not return a valid PDF payload."
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    pdf_path.write_bytes(payload)
    time.sleep(REQUEST_PAUSE_SECONDS)
    return True, ""


def queue_manual_pdf(
    row: dict[str, str],
    manual_pdf_rows: list[dict[str, str]],
    reason: str,
    preferred_source: str,
    notes: str,
) -> None:
    manual_pdf_rows.append(
        {
            "paper_id": row["paper_id"],
            "pmid": row["pmid"],
            "pmcid": row.get("pmcid", ""),
            "doi": row["doi"],
            "title": row["title"],
            "queue_reason": reason,
            "preferred_source": preferred_source,
            "notes": notes,
        }
    )


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
    pdf_dir = import_dir / "PDF"

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
        route = row.get("fulltext_access_route", "") or ""
        pmcid = row.get("pmcid", "") or ""
        xml_url = row.get("fulltext_xml_url", "") or ""
        pdf_url = row.get("fulltext_pdf_url", "") or ""

        if route in {"ncbi_pmc_xml", "europe_pmc_xml"} and pmcid:
            xml_path = pmc_xml_dir / f"{pmcid}.xml"
            normalized_path = pmc_normalized_dir / f"{pmcid}.json"

            if not xml_path.exists():
                if route == "ncbi_pmc_xml":
                    ok, error = download_pmc_xml(pmcid, xml_path)
                else:
                    xml_endpoint = xml_url or EUROPE_PMC_XML_URL.format(pmcid=pmcid)
                    ok, error = download_europe_pmc_xml(xml_endpoint, xml_path)
                if ok:
                    downloaded += 1
                else:
                    row["pmc_parse_status"] = "unusable"
                    row["normalized_path"] = ""
                    row["notes"] = append_note(row.get("notes", ""), error)
                    if pdf_url:
                        route = "oa_pdf"
                        row["fulltext_access_route"] = "oa_pdf"
                    else:
                        row["pmc_access_status"] = "missing"
                        row["pdf_needed"] = "yes"
                        row["pdf_import_status"] = "missing"
                        unusable += 1
                        queue_manual_pdf(
                            row,
                            manual_pdf_rows,
                            "Automated XML download failed.",
                            "publisher_pdf_or_user_download",
                            row["notes"],
                        )
                        continue

            if row.get("fulltext_access_route", "") != "oa_pdf":
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
                    row["pmc_access_status"] = "available"
                    row["pmc_parse_status"] = "usable"
                    row["pdf_needed"] = "no"
                    row["pdf_import_status"] = "not_attempted"
                    row["normalized_path"] = str(normalized_path)
                    route_label = "NCBI PMC XML" if route == "ncbi_pmc_xml" else "Europe PMC XML"
                    row["notes"] = append_note(row.get("notes", ""), f"{route_label} downloaded and normalized.")
                    normalized += 1
                    usable += 1
                    if index % STATUS_WRITE_INTERVAL == 0:
                        write_import_status(import_path, rows)
                        write_manual_pdf_queue(manual_pdf_path, manual_pdf_rows)
                        print(
                            f"PMC import progress: processed={index}/{len(rows)} "
                            f"downloaded={downloaded} normalized={normalized} "
                            f"usable={usable} unusable={unusable} pdf_queue={len(manual_pdf_rows)}",
                            flush=True,
                        )
                    continue

                delete_if_exists(xml_path)
                delete_if_exists(normalized_path)
                row["pmc_parse_status"] = "unusable"
                row["normalized_path"] = ""
                row["notes"] = append_note(
                    row.get("notes", ""),
                    f"{error} Unusable XML deleted from run artifacts.",
                )
                if pdf_url:
                    row["fulltext_access_route"] = "oa_pdf"
                else:
                    row["pmc_access_status"] = "missing"
                    row["pdf_needed"] = "yes"
                    row["pdf_import_status"] = "missing"
                    unusable += 1
                    queue_manual_pdf(
                        row,
                        manual_pdf_rows,
                        "Automated XML was unusable for normalization.",
                        "publisher_pdf_or_user_download",
                        row["notes"],
                    )
                    continue

        if row.get("fulltext_access_route", "") == "oa_pdf" and pdf_url:
            pdf_path = pdf_dir / staged_pdf_filename(row)
            source_note = pdf_dir / f"{row['paper_id']}.source.txt"
            if not pdf_path.exists():
                ok, error = download_pdf(pdf_url, pdf_path)
                if not ok:
                    row["pmc_access_status"] = "missing"
                    row["pdf_needed"] = "yes"
                    row["pdf_import_status"] = "missing"
                    row["normalized_path"] = ""
                    row["notes"] = append_note(row.get("notes", ""), error)
                    unusable += 1
                    queue_manual_pdf(
                        row,
                        manual_pdf_rows,
                        "Automated open-access PDF download failed.",
                        "publisher_pdf_or_user_download",
                        row["notes"],
                    )
                    continue
                downloaded += 1
            source_note.write_text(pdf_url + "\n", encoding="utf-8")
            row["pmc_access_status"] = "missing"
            row["pmc_parse_status"] = "not_attempted"
            row["pdf_needed"] = "yes"
            row["pdf_import_status"] = "imported"
            row["normalized_path"] = ""
            row["notes"] = append_note(row.get("notes", ""), "Open-access PDF downloaded into workflow PDF store.")
            usable += 1
            queue_manual_pdf(
                row,
                manual_pdf_rows,
                "Open-access PDF downloaded but not normalized during PMC XML import.",
                "open_access_pdf",
                row["notes"],
            )
        elif not row.get("normalized_path", "").strip():
            row["pmc_access_status"] = "missing"
            row["pmc_parse_status"] = "not_attempted"
            row["pdf_needed"] = "yes"
            row["pdf_import_status"] = "missing"
            row["normalized_path"] = ""
            queue_manual_pdf(
                row,
                manual_pdf_rows,
                "No automated full-text route was available at import time.",
                "publisher_pdf_or_user_download",
                row.get("notes", ""),
            )
            continue

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
