#!/usr/bin/env python3

from __future__ import annotations

import csv
import json
import subprocess
import sys
import time
import urllib.parse
from pathlib import Path


WORKFLOW_ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = WORKFLOW_ROOT / "runs"
IDCONV_URL = "https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/"
REQUEST_PAUSE_SECONDS = 0.34
BATCH_SIZE = 200

IMPORT_FIELDS = [
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


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python3 scripts/prepare_import_status.py <run_id>")
        return 1

    run_id = sys.argv[1].strip()
    run_dir = RUNS_DIR / run_id
    manifest_path = run_dir / "artifacts" / "metadata_collection" / "paper_manifest.csv"
    review2_path = run_dir / "artifacts" / "abstract_review" / "abstract_review2.csv"
    import_dir = run_dir / "artifacts" / "fulltext_import"
    import_path = import_dir / "import_status.csv"
    manual_pdf_path = import_dir / "manual_pdf_queue.csv"

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

    import_rows: list[dict[str, str]] = []
    manual_pdf_rows: list[dict[str, str]] = []
    for row in selected:
        paper_id = row["paper_id"]
        manifest_row = manifest_by_id.get(paper_id, {})
        pmid = row.get("pmid", "") or manifest_row.get("pmid", "")
        pmcid = pmcid_map.get(pmid, "")
        has_pmc = bool(pmcid)
        notes = "PMCID resolved from NCBI idconv." if has_pmc else "No PMCID found via NCBI idconv; PDF fallback will be needed."
        import_rows.append(
            {
                "paper_id": paper_id,
                "pmid": pmid,
                "pmcid": pmcid,
                "doi": manifest_row.get("doi", ""),
                "title": manifest_row.get("title", ""),
                "pmc_access_status": "available" if has_pmc else "missing",
                "pmc_parse_status": "not_attempted",
                "pdf_needed": "no" if has_pmc else "yes",
                "pdf_import_status": "not_attempted" if has_pmc else "missing",
                "normalized_path": "",
                "notes": notes,
            }
        )
        if not has_pmc:
            manual_pdf_rows.append(
                {
                    "paper_id": paper_id,
                    "pmid": pmid,
                    "pmcid": "",
                    "doi": manifest_row.get("doi", ""),
                    "title": manifest_row.get("title", ""),
                    "queue_reason": "No PMCID coverage detected during import preparation.",
                    "preferred_source": "publisher_pdf_or_user_download",
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
