#!/usr/bin/env python3

from __future__ import annotations

import csv
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

from pypdf import PdfReader


WORKFLOW_ROOT = Path(__file__).resolve().parents[1]
RUN_ID = "pi3k_alpha_inhibition_resistance_review_20260830"
RUN_DIR = WORKFLOW_ROOT / "runs" / RUN_ID
PASS_DIR = RUN_DIR / "Phase1_PubmedCollection" / "passes" / "pass_002"
ARTIFACTS_DIR = PASS_DIR / "artifacts"
IMPORT_DIR = ARTIFACTS_DIR / "fulltext_import"
DOWNLOADS_DIR = Path.home() / "Downloads"
CUTOFF = datetime(2026, 8, 30, 14, 18, 0).timestamp()

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


def load_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def compact(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def tokens(value: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[A-Za-z][A-Za-z0-9+/-]{2,}", value.lower())
        if token not in STOPWORDS
    }


def doi_keys(doi: str) -> set[str]:
    keys = {compact(doi)}
    if "/" not in doi:
        return {key for key in keys if key}
    suffix = doi.split("/", 1)[1]
    keys.add(compact(suffix))
    parts = [compact(part) for part in re.split(r"[^A-Za-z0-9]+", suffix) if compact(part)]
    keys.update(part for part in parts if len(part) >= 4)
    if len(parts) >= 2:
        keys.add("".join(parts[-2:]))
    if len(parts) >= 3:
        keys.add("".join(parts[-3:]))
    tail_digits = "".join(ch for ch in suffix if ch.isdigit())
    if len(tail_digits) >= 4:
        keys.add(tail_digits)
    return {key for key in keys if key and len(key) >= 4}


def pdf_text(path: Path) -> str:
    try:
        reader = PdfReader(str(path))
        chunks: list[str] = []
        for page in reader.pages[:3]:
            chunks.append(page.extract_text() or "")
        return "\n".join(chunks)
    except Exception:
        return ""


def title_score(title: str, text: str) -> float:
    title_tokens = tokens(title)
    text_tokens = tokens(text)
    if not title_tokens or not text_tokens:
        return 0.0
    return len(title_tokens & text_tokens) / len(title_tokens)


def staged_pdf_filename(row: dict[str, str]) -> str:
    pmid = row.get("pmid", "").strip()
    if pmid:
        return f"PMID {pmid}.pdf"
    return f"{row.get('paper_id', '').strip()}.pdf"


def append_note(existing: str, extra: str) -> str:
    existing = (existing or "").strip()
    if not existing:
        return extra
    if extra in existing:
        return existing
    return f"{existing} {extra}"


def move_pdf(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.replace(source, target)
    except OSError:
        tmp = target.with_name(target.name + ".incoming")
        if tmp.exists():
            tmp.unlink()
        shutil.copy2(source, tmp)
        os.replace(tmp, target)
        source.unlink()


def main() -> int:
    queue_path = IMPORT_DIR / "manual_pdf_queue.csv"
    import_status_path = IMPORT_DIR / "import_status.csv"
    report_path = IMPORT_DIR / "manual_pdf_import_report.csv"
    pdf_dir = IMPORT_DIR / "PDF"

    import_fields, import_rows = load_csv(import_status_path)
    _queue_fields, queue_rows = load_csv(queue_path)
    _report_fields, old_report_rows = load_csv(report_path)

    candidates = [
        path
        for path in DOWNLOADS_DIR.glob("*.pdf")
        if path.is_file() and path.stat().st_mtime < CUTOFF
    ]
    extracted = {
        path: {
            "filename": compact(path.name),
            "text": pdf_text(path),
        }
        for path in candidates
    }
    for data in extracted.values():
        data["compact_text"] = compact(data["text"][:12000])

    import_by_id = {row["paper_id"]: row for row in import_rows}
    report_by_id = {row["paper_id"]: row for row in old_report_rows}
    used: set[Path] = set()
    remaining: list[dict[str, str]] = []
    staged_rows: list[dict[str, str]] = []

    for row in queue_rows:
        best_path: Path | None = None
        best_method = ""
        best_score = 0.0
        keys = doi_keys(row.get("doi", ""))
        title = row.get("title", "")

        for path, data in extracted.items():
            if path in used:
                continue
            filename = data["filename"]
            compact_text = data["compact_text"]
            if row.get("pmid") and compact(row["pmid"]) in filename:
                best_path, best_method, best_score = path, "pmid_filename", 1.0
                break
            if row.get("pmcid") and compact(row["pmcid"]) in filename:
                best_path, best_method, best_score = path, "pmcid_filename", 1.0
                break
            doi_filename_hits = [key for key in keys if key in filename]
            if doi_filename_hits:
                score = 0.98 if max(len(key) for key in doi_filename_hits) >= 7 else 0.85
                if score > best_score:
                    best_path, best_method, best_score = path, "doi_fragment_filename", score
                    continue
            doi_text_hits = [key for key in keys if key in compact_text]
            if doi_text_hits:
                score = 0.95 if max(len(key) for key in doi_text_hits) >= 7 else 0.82
                if score > best_score:
                    best_path, best_method, best_score = path, "doi_fragment_text", score
                    continue
            score = title_score(title, f"{path.stem}\n{data['text'][:5000]}")
            if score > best_score:
                best_path, best_method, best_score = path, "title_text_overlap", score

        if best_path is None or best_score < 0.55:
            remaining.append(row)
            continue

        used.add(best_path)
        target = pdf_dir / staged_pdf_filename(row)
        move_pdf(best_path, target)
        (pdf_dir / f"{row['paper_id']}.source.txt").write_text(best_path.name + "\n", encoding="utf-8")

        import_row = import_by_id.get(row["paper_id"])
        if import_row is not None:
            import_row["pdf_import_status"] = "staged_from_user_download"
            import_row["notes"] = append_note(
                import_row.get("notes", ""),
                f"Matched pre-14:18 manual PDF from {best_path.name} by {best_method}; moved into workflow PDF store as {target.name}.",
            )

        staged_rows.append(
            {
                "paper_id": row["paper_id"],
                "pmid": row["pmid"],
                "doi": row["doi"],
                "title": row["title"],
                "import_status": "staged",
                "match_method": best_method,
                "match_score": f"{best_score:.3f}",
                "source_filename": best_path.name,
                "staged_pdf_path": str(target),
                "notes": f"Pre-14:18 PDF moved into workflow store as {target.name}.",
            }
        )

    report_rows: list[dict[str, str]] = []
    staged_ids = {row["paper_id"] for row in staged_rows}
    remaining_ids = {row["paper_id"] for row in remaining}
    for row in old_report_rows:
        paper_id = row["paper_id"]
        if paper_id in staged_ids:
            continue
        if paper_id in remaining_ids:
            row["import_status"] = "missing"
            row["notes"] = "No matching PDF found in the provided downloads directory."
        report_rows.append(row)
    report_rows.extend(staged_rows)

    write_csv(import_status_path, import_fields, import_rows)
    write_csv(queue_path, QUEUE_FIELDS, remaining)
    write_csv(report_path, REPORT_FIELDS, report_rows)

    print(f"Pre-14:18 candidates: {len(candidates)}")
    print(f"Newly staged: {len(staged_rows)}")
    print(f"Remaining manual PDF queue: {len(remaining)}")
    for row in staged_rows:
        print(f"{row['pmid']}\t{row['match_method']}\t{row['match_score']}\t{row['source_filename']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
