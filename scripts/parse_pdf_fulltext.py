#!/usr/bin/env python3

from __future__ import annotations

import csv
import json
import mimetypes
import os
import re
import sys
import urllib.error
import urllib.request
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path

from pass_archive import active_artifacts_dir, load_all_pass_csv, run_input_path


WORKFLOW_ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = WORKFLOW_ROOT / "runs"
MIN_BODY_CHARS = 1000

REPORT_FIELDS = [
    "paper_id",
    "pmid",
    "doi",
    "title",
    "pdf_path",
    "tei_path",
    "normalized_path",
    "parse_status",
    "notes",
]


def load_csv(path: Path) -> list[dict[str, str]]:
    return list(csv.DictReader(path.open(encoding="utf-8")))


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


def manual_pdf_allowed(run_dir: Path) -> bool:
    config = parse_config(run_input_path(run_dir, "run_config.md"))
    if config.get("access_phase", "pmc_learning") == "final_access" or config.get("pdf_policy") == "require_fulltext_completion":
        return True
    shortlist_path = active_artifacts_dir(run_dir) / "fulltext_import" / "pdf_download_shortlist.csv"
    if not shortlist_path.exists():
        return False
    feedback_rows = load_all_pass_csv(run_dir, "artifacts/fulltext_review/pmc_mechanism_feedback.csv")
    latest_decision = feedback_rows[-1].get("pdf_deferral_decision", "").strip() if feedback_rows else ""
    return latest_decision == "final_pdf_pass"


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def xml_local_name(tag: str) -> str:
    return tag.split("}", 1)[-1]


def clean_text(value: str) -> str:
    return " ".join(value.split())


def find_first(root: ET.Element, name: str) -> ET.Element | None:
    return next((element for element in root.iter() if xml_local_name(element.tag) == name), None)


def extract_tei_sections(root: ET.Element) -> list[dict[str, str]]:
    body = find_first(root, "body")
    if body is None:
        return []
    sections: list[dict[str, str]] = []
    for div in body.iter():
        if xml_local_name(div.tag) != "div":
            continue
        head = next((child for child in div if xml_local_name(child.tag) == "head"), None)
        title = clean_text("".join(head.itertext())) if head is not None else ""
        paragraphs: list[str] = []
        for child in div:
            if xml_local_name(child.tag) != "p":
                continue
            paragraph = clean_text("".join(child.itertext()))
            if paragraph:
                paragraphs.append(paragraph)
        text = "\n\n".join(paragraphs).strip()
        if title or text:
            sections.append({"title": title, "text": text})
    return sections


def extract_tei_raw_text(root: ET.Element) -> str:
    body = find_first(root, "body")
    if body is None:
        return ""
    return clean_text(" ".join(text for text in body.itertext() if text and text.strip()))


def is_valid_tei(path: Path) -> bool:
    if not path.exists() or path.stat().st_size < 500:
        return False
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError:
        return False
    return len(extract_tei_raw_text(root)) >= MIN_BODY_CHARS


def normalize_tei(
    tei_path: Path,
    normalized_path: Path,
    row: dict[str, str],
) -> tuple[bool, str]:
    try:
        root = ET.parse(tei_path).getroot()
    except ET.ParseError as exc:
        return False, f"TEI parse error: {exc}"

    raw_text = extract_tei_raw_text(root)
    if len(raw_text) < MIN_BODY_CHARS:
        return False, "GROBID TEI body text is too short for normalization."

    title = row.get("title", "") or ""
    title_element = find_first(root, "title")
    if title_element is not None:
        candidate = clean_text("".join(title_element.itertext()))
        if candidate:
            title = candidate

    payload = {
        "paper_id": row.get("paper_id", ""),
        "pmid": row.get("pmid", ""),
        "pmcid": row.get("pmcid", ""),
        "doi": row.get("doi", ""),
        "title": title,
        "source_type": "pdf_grobid",
        "source_path": str(tei_path),
        "raw_text": raw_text,
        "sections": extract_tei_sections(root),
    }
    normalized_path.parent.mkdir(parents=True, exist_ok=True)
    normalized_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return True, ""


def build_multipart_body(pdf_path: Path) -> tuple[bytes, str]:
    boundary = f"----OpenClawBoundary{uuid.uuid4().hex}"
    content_type = mimetypes.guess_type(pdf_path.name)[0] or "application/pdf"
    header = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="input"; filename="{pdf_path.name}"\r\n'
        f"Content-Type: {content_type}\r\n\r\n"
    ).encode("utf-8")
    footer = f"\r\n--{boundary}--\r\n".encode("utf-8")
    body = header + pdf_path.read_bytes() + footer
    return body, boundary


def is_reachable(base_url: str) -> bool:
    probe = base_url.rstrip("/") + "/api/isalive"
    request = urllib.request.Request(probe, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            payload = response.read().decode("utf-8", errors="ignore").strip().lower()
    except Exception:
        return False
    return response.status == 200 and payload in {"true", "\"true\"", "ok"}


def normalize_grobid_base_url(value: str) -> str:
    url = value.strip()
    if not url:
        return ""
    url = re.sub(r"/api/processFulltextDocument/?$", "", url)
    url = re.sub(r"/processFulltextDocument/?$", "", url)
    url = re.sub(r"/api/isalive/?$", "", url)
    url = re.sub(r"/isalive/?$", "", url)
    url = re.sub(r"/api/?$", "", url)
    return url.rstrip("/")


def candidate_grobid_urls() -> list[str]:
    candidates: list[str] = []
    for env_name in ("GROBID_URL", "GROBID_BASE_URL"):
        env_url = normalize_grobid_base_url(os.environ.get(env_name, ""))
        if env_url and env_url not in candidates:
            candidates.append(env_url)

    # Common local default used in this workspace when GROBID runs as a local service.
    for url in (
        "http://localhost:8070",
        "http://127.0.0.1:8070",
        "http://localhost:8071",
        "http://127.0.0.1:8071",
    ):
        if url not in candidates:
            candidates.append(url)

    return candidates


def resolve_grobid_url() -> tuple[str, str]:
    tried: list[str] = []
    for url in candidate_grobid_urls():
        tried.append(url)
        if is_reachable(url):
            configured = normalize_grobid_base_url(os.environ.get("GROBID_URL", ""))
            configured_base = normalize_grobid_base_url(os.environ.get("GROBID_BASE_URL", ""))
            if url == configured or url == configured_base:
                return url, f"Using configured GROBID endpoint base {url}."
            return url, f"Auto-discovered reachable local GROBID endpoint at {url}."

    raw_env_url = os.environ.get("GROBID_URL", "").strip()
    raw_env_base = os.environ.get("GROBID_BASE_URL", "").strip()
    if raw_env_url or raw_env_base:
        configured_text = ", ".join(
            part for part in [f"GROBID_URL={raw_env_url}" if raw_env_url else "", f"GROBID_BASE_URL={raw_env_base}" if raw_env_base else ""] if part
        )
        return "", (
            f"Configured GROBID endpoint is not reachable ({configured_text}). "
            f"Tried normalized bases: {', '.join(tried)}."
        )
    return "", f"No GROBID endpoint configured and no reachable local GROBID service discovered. Tried: {', '.join(tried)}."


def request_grobid(pdf_path: Path, tei_path: Path) -> tuple[bool, str]:
    grobid_url, resolution_note = resolve_grobid_url()
    if not grobid_url:
        return False, resolution_note

    endpoint = grobid_url.rstrip("/") + "/api/processFulltextDocument"
    body, boundary = build_multipart_body(pdf_path)
    request = urllib.request.Request(
        endpoint,
        data=body,
        method="POST",
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Accept": "application/xml",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            payload = response.read()
    except urllib.error.HTTPError as exc:
        return False, f"GROBID request failed: HTTP {exc.code}"
    except Exception as exc:
        return False, f"GROBID request failed: {exc}"

    if not payload.strip():
        return False, "GROBID returned empty content."

    tei_path.parent.mkdir(parents=True, exist_ok=True)
    tei_path.write_bytes(payload)
    return True, resolution_note


def append_note(existing: str, extra: str) -> str:
    existing = (existing or "").strip()
    if not existing:
        return extra
    if extra in existing:
        return existing
    return f"{existing} {extra}"


def staged_pdf_candidates(row: dict[str, str], pdf_dir: Path) -> list[Path]:
    candidates: list[Path] = []
    pmid = row.get("pmid", "").strip()
    paper_id = row.get("paper_id", "").strip()
    if pmid:
        candidates.append(pdf_dir / f"PMID {pmid}.pdf")
    if paper_id:
        candidates.append(pdf_dir / f"{paper_id}.pdf")
    return candidates


def resolve_pdf_path(row: dict[str, str], pdf_dir: Path) -> Path:
    for candidate in staged_pdf_candidates(row, pdf_dir):
        if candidate.exists():
            return candidate
    paper_id = row.get("paper_id", "").strip()
    return pdf_dir / f"{paper_id}.pdf"


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python3 scripts/parse_pdf_fulltext.py <run_id>")
        return 1

    run_id = sys.argv[1].strip()
    run_dir = RUNS_DIR / run_id
    import_dir = active_artifacts_dir(run_dir) / "fulltext_import"
    import_status_path = import_dir / "import_status.csv"
    report_path = import_dir / "pdf_parse_report.csv"
    pdf_dir = import_dir / "PDF"
    tei_dir = pdf_dir / "parser_cache" / "grobid"
    normalized_dir = pdf_dir / "normalized"

    if not manual_pdf_allowed(run_dir):
        print(
            "Manual PDF parsing is deferred during access_phase=pmc_learning. "
            "Use PMC-normalized full text for mechanism feedback first, "
            "then build pdf_download_shortlist.csv after final_pdf_pass before parsing PDFs."
        )
        return 1

    if not import_status_path.exists():
        print(f"Import status not found: {import_status_path}")
        return 1

    rows = load_csv(import_status_path)
    tei_dir.mkdir(parents=True, exist_ok=True)
    normalized_dir.mkdir(parents=True, exist_ok=True)

    report_rows: list[dict[str, str]] = []
    normalized_count = 0
    pending_count = 0
    failed_count = 0

    for row in rows:
        pdf_status = row.get("pdf_import_status", "")
        paper_id = row.get("paper_id", "")
        if pdf_status not in {"staged_from_user_download", "imported", "parser_pending", "parse_failed"}:
            continue

        pdf_path = resolve_pdf_path(row, pdf_dir)
        tei_path = tei_dir / f"{paper_id}.tei.xml"
        normalized_path = normalized_dir / f"{paper_id}.json"

        parse_status = "missing_pdf"
        notes = ""

        if not pdf_path.exists():
            row["pdf_import_status"] = "missing"
            row["normalized_path"] = row.get("normalized_path", "")
            notes = "Expected staged PDF is missing from the run."
            failed_count += 1
        else:
            if not is_valid_tei(tei_path):
                ok, message = request_grobid(pdf_path, tei_path)
                if not ok:
                    row["pdf_import_status"] = "parser_pending"
                    row["notes"] = append_note(row.get("notes", ""), message)
                    parse_status = "parser_pending"
                    notes = message
                    pending_count += 1
                    report_rows.append(
                        {
                            "paper_id": paper_id,
                            "pmid": row.get("pmid", ""),
                            "doi": row.get("doi", ""),
                            "title": row.get("title", ""),
                            "pdf_path": str(pdf_path),
                            "tei_path": "",
                            "normalized_path": "",
                            "parse_status": parse_status,
                            "notes": notes,
                        }
                    )
                    continue

            ok, message = normalize_tei(tei_path, normalized_path, row)
            if ok:
                row["pdf_import_status"] = "normalized"
                row["pdf_needed"] = "no"
                row["normalized_path"] = str(normalized_path)
                row["notes"] = append_note(
                    row.get("notes", ""),
                    append_note(message, "PDF parsed and normalized through GROBID TEI."),
                )
                parse_status = "normalized"
                notes = append_note(message, "PDF parsed and normalized through GROBID TEI.")
                normalized_count += 1
            else:
                row["pdf_import_status"] = "parse_failed"
                row["notes"] = append_note(row.get("notes", ""), message)
                parse_status = "parse_failed"
                notes = message
                failed_count += 1

        report_rows.append(
            {
                "paper_id": paper_id,
                "pmid": row.get("pmid", ""),
                "doi": row.get("doi", ""),
                "title": row.get("title", ""),
                "pdf_path": str(pdf_path) if pdf_path.exists() else "",
                "tei_path": str(tei_path) if tei_path.exists() else "",
                "normalized_path": str(normalized_path) if normalized_path.exists() else "",
                "parse_status": parse_status,
                "notes": notes,
            }
        )

    fieldnames = list(rows[0].keys()) if rows else []
    write_csv(import_status_path, fieldnames, rows)
    write_csv(report_path, REPORT_FIELDS, report_rows)

    print(f"Normalized {normalized_count} staged PDFs")
    print(f"Parser pending for {pending_count} PDFs")
    print(f"Parse failed for {failed_count} PDFs")
    print(f"Wrote PDF parse report to {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
