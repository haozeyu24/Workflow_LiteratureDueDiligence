#!/usr/bin/env python3

from __future__ import annotations

import csv
import errno
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from pass_archive import active_artifacts_dir, load_all_pass_csv, run_input_path


WORKFLOW_ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = WORKFLOW_ROOT / "runs"

QUEUE_FIELDS = [
    "paper_id",
    "pmid",
    "pmcid",
    "doi",
    "title",
    "queue_reason",
    "preferred_source",
    "notes",
]

REPORT_FIELDS = [
    "paper_id",
    "pmid",
    "doi",
    "title",
    "import_status",
    "match_method",
    "match_score",
    "source_filename",
    "staged_pdf_path",
    "notes",
]

STOPWORDS = {
    "a",
    "an",
    "and",
    "as",
    "at",
    "by",
    "for",
    "from",
    "in",
    "into",
    "of",
    "on",
    "or",
    "the",
    "to",
    "via",
    "with",
}


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


def is_pdf(path: Path) -> bool:
    if not path.is_file() or path.suffix.lower() != ".pdf":
        return False
    try:
        return path.read_bytes()[:5] == b"%PDF-"
    except Exception:
        return False


def normalize_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def compact_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def token_set(value: str) -> set[str]:
    return {
        token
        for token in normalize_text(value).split()
        if token and token not in STOPWORDS and len(token) > 2
    }


def title_overlap_score(title: str, filename: str) -> float:
    title_tokens = token_set(title)
    file_tokens = token_set(filename)
    if not title_tokens or not file_tokens:
        return 0.0
    overlap = title_tokens & file_tokens
    return len(overlap) / len(title_tokens)


def read_pdf_metadata_title(path: Path) -> str:
    try:
        result = subprocess.run(
            ["mdls", "-raw", "-name", "kMDItemTitle", str(path)],
            capture_output=True,
            check=False,
            text=True,
        )
    except Exception:
        return ""
    if result.returncode != 0:
        return ""
    value = result.stdout.strip()
    if not value or value == "(null)":
        return ""
    return value.strip().strip('"')


def read_pdf_metadata_wherefroms(path: Path) -> str:
    try:
        result = subprocess.run(
            ["mdls", "-raw", "-name", "kMDItemWhereFroms", str(path)],
            capture_output=True,
            check=False,
            text=True,
        )
    except Exception:
        return ""
    if result.returncode != 0:
        return ""
    value = result.stdout.strip()
    if not value or value == "(null)":
        return ""
    return value


def load_record_metadata(records_dir: Path, paper_id: str) -> dict[str, str]:
    record_path = records_dir / f"{paper_id}.json"
    if not record_path.exists():
        return {}
    try:
        payload = json.loads(record_path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    authors = payload.get("authors") or []
    first_author = authors[0] if authors else ""
    journal = payload.get("journal") or payload.get("full_journal_name") or ""
    year = payload.get("year") or ""
    return {
        "first_author": first_author,
        "journal": journal,
        "year": str(year),
    }


def doi_fingerprints(doi: str) -> set[str]:
    values: set[str] = set()
    compact = compact_text(doi)
    if compact:
        values.add(compact)
    if "/" in doi:
        suffix = doi.split("/", 1)[1]
        compact_suffix = compact_text(suffix)
        if compact_suffix:
            values.add(compact_suffix)
        for token in re.split(r"[^A-Za-z0-9]+", suffix):
            compact_token = compact_text(token)
            if len(compact_token) >= 5:
                values.add(compact_token)
        numeric_tail = "".join(ch for ch in suffix if ch.isdigit())
        if len(numeric_tail) >= 5:
            values.add(numeric_tail)
    return values


def append_note(existing: str, extra: str) -> str:
    existing = (existing or "").strip()
    if not existing:
        return extra
    if extra in existing:
        return existing
    return f"{existing} {extra}"


def staged_pdf_filename(queue_row: dict[str, str]) -> str:
    pmid = queue_row.get("pmid", "").strip()
    if pmid:
        return f"PMID {pmid}.pdf"
    paper_id = queue_row.get("paper_id", "").strip()
    return f"{paper_id}.pdf"


def move_pdf(source_path: Path, target_path: Path) -> None:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.replace(source_path, target_path)
        return
    except OSError as exc:
        if exc.errno != errno.EXDEV:
            raise

    temp_target = target_path.with_name(target_path.name + ".incoming")
    if temp_target.exists():
        temp_target.unlink()
    shutil.copy2(source_path, temp_target)
    os.replace(temp_target, target_path)
    source_path.unlink()


def migrate_legacy_staged_pdfs(import_rows: list[dict[str, str]], pdf_dir: Path) -> None:
    for row in import_rows:
        paper_id = row.get("paper_id", "").strip()
        pmid = row.get("pmid", "").strip()
        if not paper_id or not pmid:
            continue
        legacy_path = pdf_dir / f"{paper_id}.pdf"
        target_path = pdf_dir / f"PMID {pmid}.pdf"
        if not legacy_path.exists() or target_path.exists():
            continue
        legacy_path.replace(target_path)


def find_match(
    queue_row: dict[str, str],
    pdf_paths: list[Path],
    used_paths: set[Path],
    records_dir: Path,
) -> tuple[Path | None, str, float]:
    paper_id = queue_row.get("paper_id", "")
    pmid = queue_row.get("pmid", "")
    pmcid = queue_row.get("pmcid", "")
    doi = queue_row.get("doi", "")
    title = queue_row.get("title", "")
    record_metadata = load_record_metadata(records_dir, paper_id)
    doi_keys = doi_fingerprints(doi)

    for path in pdf_paths:
        if path in used_paths:
            continue
        compact_name = compact_text(path.name)
        metadata_title = read_pdf_metadata_title(path)
        compact_metadata = compact_text(metadata_title)
        wherefroms = read_pdf_metadata_wherefroms(path)
        compact_wherefroms = compact_text(wherefroms)
        if paper_id and compact_text(paper_id) in compact_name:
            return path, "paper_id", 1.0
        if pmid and compact_text(pmid) in compact_name:
            return path, "pmid", 1.0
        if pmcid and compact_text(pmcid) in compact_name:
            return path, "pmcid", 1.0
        if pmcid and compact_text(pmcid) in compact_wherefroms:
            return path, "pdf_metadata_pmcid", 1.0
        for doi_key in doi_keys:
            if doi_key and doi_key in compact_name:
                score = 1.0 if doi_key == compact_text(doi) else 0.95
                return path, "doi", score
            if doi_key and doi_key in compact_metadata:
                score = 1.0 if doi_key == compact_text(doi) else 0.95
                return path, "pdf_metadata_doi", score

    best_path: Path | None = None
    best_score = 0.0
    best_method = ""
    for path in pdf_paths:
        if path in used_paths:
            continue
        filename_score = title_overlap_score(title, path.stem)
        if filename_score > best_score:
            best_score = filename_score
            best_path = path
            best_method = "title_overlap"
        metadata_title = read_pdf_metadata_title(path)
        if metadata_title:
            metadata_score = title_overlap_score(title, metadata_title)
            if metadata_score > best_score:
                best_score = metadata_score
                best_path = path
                best_method = "pdf_metadata_title"
        first_author = normalize_text(record_metadata.get("first_author", "")).split()
        author_token = first_author[0] if first_author else ""
        journal_tokens = token_set(record_metadata.get("journal", ""))
        file_tokens = token_set(path.stem)
        year = record_metadata.get("year", "")
        author_year_journal = (
            author_token
            and author_token in file_tokens
            and year
            and year in path.name
            and bool(journal_tokens & file_tokens)
        )
        if author_year_journal and 0.7 > best_score:
            best_score = 0.7
            best_path = path
            best_method = "author_year_journal"

    if best_path is not None and best_score >= 0.45:
        return best_path, best_method, round(best_score, 3)

    return None, "", 0.0


def main() -> int:
    if len(sys.argv) not in {2, 3}:
        print("Usage: python3 scripts/stage_manual_pdfs.py <run_id> [downloads_dir]")
        return 1

    run_id = sys.argv[1].strip()
    downloads_dir = Path(sys.argv[2]).expanduser() if len(sys.argv) == 3 else Path("~/Downloads").expanduser()

    run_dir = RUNS_DIR / run_id
    artifacts_dir = active_artifacts_dir(run_dir)
    import_dir = artifacts_dir / "fulltext_import"
    records_dir = artifacts_dir / "metadata_collection" / "records"
    import_status_path = import_dir / "import_status.csv"
    queue_path = import_dir / "manual_pdf_queue.csv"
    report_path = import_dir / "manual_pdf_import_report.csv"
    pdf_dir = import_dir / "PDF"

    if not manual_pdf_allowed(run_dir):
        print(
            "Manual PDF staging is deferred during access_phase=pmc_learning. "
            "Read PMC-normalized full text and write pmc_mechanism_feedback.csv first, "
            "then build pdf_download_shortlist.csv after final_pdf_pass before staging PDFs."
        )
        return 1

    if not import_status_path.exists():
        print(f"Import status not found: {import_status_path}")
        return 1
    if not queue_path.exists():
        print(f"Manual PDF queue not found: {queue_path}")
        return 1
    if not downloads_dir.exists():
        print(f"Downloads directory not found: {downloads_dir}")
        return 1

    import_rows = load_csv(import_status_path)
    queue_rows = load_csv(queue_path)
    existing_report_rows = load_csv(report_path) if report_path.exists() else []
    pdf_dir.mkdir(parents=True, exist_ok=True)
    migrate_legacy_staged_pdfs(import_rows, pdf_dir)

    pdf_paths = sorted(path for path in downloads_dir.iterdir() if is_pdf(path))
    used_paths: set[Path] = set()
    remaining_queue: list[dict[str, str]] = []
    report_rows: list[dict[str, str]] = []
    import_by_paper_id = {row["paper_id"]: row for row in import_rows}
    existing_report_by_paper_id = {row["paper_id"]: row for row in existing_report_rows}
    staged_count = 0

    for queue_row in queue_rows:
        match_path, match_method, match_score = find_match(queue_row, pdf_paths, used_paths, records_dir)
        paper_id = queue_row["paper_id"]
        target_pdf = pdf_dir / staged_pdf_filename(queue_row)
        source_note = pdf_dir / f"{paper_id}.source.txt"

        if match_path is None:
            remaining_queue.append(queue_row)
            report_rows.append(
                {
                    "paper_id": paper_id,
                    "pmid": queue_row["pmid"],
                    "doi": queue_row["doi"],
                    "title": queue_row["title"],
                    "import_status": "missing",
                    "match_method": "",
                    "match_score": "",
                    "source_filename": "",
                    "staged_pdf_path": "",
                    "notes": "No matching PDF found in the provided downloads directory.",
                }
            )
            continue

        move_pdf(match_path, target_pdf)
        source_note.write_text(match_path.name + "\n", encoding="utf-8")
        used_paths.add(match_path)
        staged_count += 1

        import_row = import_by_paper_id.get(paper_id)
        if import_row is not None:
            import_row["pdf_import_status"] = "staged_from_user_download"
            import_row["notes"] = append_note(
                import_row.get("notes", ""),
                f"Matched manual PDF from {match_path.name} by {match_method}; moved into workflow PDF store as {target_pdf.name}.",
            )

        report_rows.append(
            {
                "paper_id": paper_id,
                "pmid": queue_row["pmid"],
                "doi": queue_row["doi"],
                "title": queue_row["title"],
                "import_status": "staged",
                "match_method": match_method,
                "match_score": f"{match_score:.3f}",
                "source_filename": match_path.name,
                "staged_pdf_path": str(target_pdf),
                "notes": f"PDF moved into workflow store as {target_pdf.name} for downstream parsing and normalization.",
            }
        )

    current_report_paper_ids = {row["paper_id"] for row in report_rows}
    for paper_id, row in existing_report_by_paper_id.items():
        import_row = import_by_paper_id.get(paper_id)
        if paper_id in current_report_paper_ids:
            continue
        if import_row is None:
            continue
        if import_row.get("pdf_import_status", "") != "staged_from_user_download":
            continue
        report_rows.append(row)
        current_report_paper_ids.add(paper_id)

    for import_row in import_rows:
        paper_id = import_row.get("paper_id", "")
        if not paper_id or paper_id in current_report_paper_ids:
            continue
        if import_row.get("pdf_import_status", "") != "staged_from_user_download":
            continue
        staged_pdf_path = pdf_dir / staged_pdf_filename(import_row)
        source_note = pdf_dir / f"{paper_id}.source.txt"
        source_filename = source_note.read_text(encoding="utf-8").strip() if source_note.exists() else ""
        report_rows.append(
            {
                "paper_id": paper_id,
                "pmid": import_row.get("pmid", ""),
                "doi": import_row.get("doi", ""),
                "title": import_row.get("title", ""),
                "import_status": "staged",
                "match_method": "",
                "match_score": "",
                "source_filename": source_filename,
                "staged_pdf_path": str(staged_pdf_path) if staged_pdf_path.exists() else "",
                "notes": "Previously staged PDF retained for downstream parsing and normalization.",
            }
        )

    import_fieldnames = list(import_rows[0].keys()) if import_rows else []
    write_csv(import_status_path, import_fieldnames, import_rows)
    write_csv(queue_path, QUEUE_FIELDS, remaining_queue)
    write_csv(report_path, REPORT_FIELDS, report_rows)

    print(f"Scanned {len(pdf_paths)} PDFs in {downloads_dir}")
    print(f"Staged {staged_count} PDFs into {pdf_dir}")
    print(f"Remaining manual PDF queue: {len(remaining_queue)}")
    print(f"Wrote import report to {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
