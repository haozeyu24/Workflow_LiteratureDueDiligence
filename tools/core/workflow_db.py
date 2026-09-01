#!/usr/bin/env python3

from __future__ import annotations

import csv
import hashlib
import json
import sqlite3
import time
from pathlib import Path

from pass_archive import phase1_dir


SCHEMA_VERSION = 3


def db_path(run_dir: Path) -> Path:
    return phase1_dir(run_dir) / "workflow_state.sqlite"


def connect(run_dir: Path) -> sqlite3.Connection:
    path = db_path(run_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    initialize(connection)
    return connection


def initialize(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        PRAGMA foreign_keys = ON;

        CREATE TABLE IF NOT EXISTS metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS papers (
            paper_id TEXT PRIMARY KEY,
            pmid TEXT UNIQUE,
            doi TEXT,
            title TEXT,
            year TEXT,
            first_seen_pass INTEGER NOT NULL,
            last_seen_pass INTEGER NOT NULL,
            latest_status TEXT NOT NULL,
            latest_decision TEXT,
            latest_rationale TEXT,
            updated_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_papers_pmid ON papers(pmid);
        CREATE INDEX IF NOT EXISTS idx_papers_latest_status ON papers(latest_status);

        CREATE TABLE IF NOT EXISTS pass_decisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pass_number INTEGER NOT NULL,
            paper_id TEXT NOT NULL,
            pmid TEXT,
            stage TEXT NOT NULL,
            decision TEXT NOT NULL,
            status TEXT NOT NULL,
            rationale TEXT,
            created_at TEXT NOT NULL,
            UNIQUE(pass_number, paper_id, stage),
            FOREIGN KEY(paper_id) REFERENCES papers(paper_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS pubmed_records (
            pass_number INTEGER NOT NULL,
            paper_id TEXT NOT NULL,
            pmid TEXT,
            doi TEXT,
            title TEXT,
            journal TEXT,
            year TEXT,
            authors_json TEXT NOT NULL,
            source_queries_json TEXT NOT NULL,
            retrieval_batch TEXT,
            original_record_path TEXT,
            raw_json TEXT NOT NULL,
            sha256 TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            PRIMARY KEY(pass_number, paper_id),
            FOREIGN KEY(paper_id) REFERENCES papers(paper_id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_pubmed_records_pmid ON pubmed_records(pmid);

        CREATE TABLE IF NOT EXISTS fulltext_read_state (
            paper_id TEXT PRIMARY KEY,
            pmid TEXT,
            pmcid TEXT,
            doi TEXT,
            title TEXT,
            first_read_pass INTEGER NOT NULL,
            last_read_pass INTEGER NOT NULL,
            source_route TEXT,
            pmc_access_status TEXT,
            pmc_parse_status TEXT,
            normalized_path TEXT,
            normalized_sha256 TEXT,
            latest_fulltext_decision TEXT,
            latest_evidence_tier TEXT,
            latest_directness TEXT,
            latest_target_centrality TEXT,
            latest_query_feedback_signal TEXT,
            latest_retention_role TEXT,
            latest_rationale TEXT,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(paper_id) REFERENCES papers(paper_id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_fulltext_read_state_pmid ON fulltext_read_state(pmid);
        CREATE INDEX IF NOT EXISTS idx_fulltext_read_state_decision ON fulltext_read_state(latest_fulltext_decision);
        """
    )
    connection.execute(
        "INSERT OR REPLACE INTO metadata(key, value) VALUES (?, ?)",
        ("schema_version", str(SCHEMA_VERSION)),
    )
    connection.commit()


def timestamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def paper_id_from_pmid(pmid: str) -> str:
    return f"pmid-{pmid.strip()}"


def record_uri(pass_number: int, paper_id: str) -> str:
    return f"sqlite://pubmed_records/pass_{pass_number:03d}/{paper_id}"


def record_pubmed_payloads(
    run_dir: Path,
    pass_number: int,
    records: list[dict[str, object]],
    original_paths: dict[str, str] | None = None,
) -> None:
    if not records:
        return
    original_paths = original_paths or {}
    now = timestamp()
    with connect(run_dir) as connection:
        for record in records:
            paper_id = str(record.get("paper_id") or "").strip()
            pmid = str(record.get("pmid") or "").strip()
            if not paper_id and pmid:
                paper_id = paper_id_from_pmid(pmid)
            if not paper_id:
                continue
            raw_json = json.dumps(record, ensure_ascii=True, sort_keys=True)
            authors = record.get("authors") if isinstance(record.get("authors"), list) else []
            source_queries = (
                record.get("source_queries")
                if isinstance(record.get("source_queries"), list)
                else []
            )
            connection.execute(
                """
                INSERT INTO pubmed_records(
                    pass_number, paper_id, pmid, doi, title, journal, year,
                    authors_json, source_queries_json, retrieval_batch,
                    original_record_path, raw_json, sha256, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(pass_number, paper_id) DO UPDATE SET
                    pmid = excluded.pmid,
                    doi = excluded.doi,
                    title = excluded.title,
                    journal = excluded.journal,
                    year = excluded.year,
                    authors_json = excluded.authors_json,
                    source_queries_json = excluded.source_queries_json,
                    retrieval_batch = excluded.retrieval_batch,
                    original_record_path = excluded.original_record_path,
                    raw_json = excluded.raw_json,
                    sha256 = excluded.sha256,
                    updated_at = excluded.updated_at
                """,
                (
                    pass_number,
                    paper_id,
                    pmid,
                    str(record.get("doi") or "").strip(),
                    str(record.get("title") or "").strip(),
                    str(record.get("journal") or record.get("full_journal_name") or "").strip(),
                    str(record.get("year") or "").strip(),
                    json.dumps(authors, ensure_ascii=True),
                    json.dumps(source_queries, ensure_ascii=True),
                    str(record.get("retrieval_batch") or "").strip(),
                    original_paths.get(paper_id, ""),
                    raw_json,
                    hashlib.sha256(raw_json.encode("utf-8")).hexdigest(),
                    now,
                ),
            )
        connection.commit()


def latest_pubmed_record_metadata(run_dir: Path, paper_id: str) -> dict[str, str]:
    if not paper_id:
        return {}
    with connect(run_dir) as connection:
        row = connection.execute(
            """
            SELECT authors_json, journal, year
            FROM pubmed_records
            WHERE paper_id = ?
            ORDER BY pass_number DESC
            LIMIT 1
            """,
            (paper_id,),
        ).fetchone()
    if row is None:
        return {}
    try:
        authors = json.loads(row["authors_json"] or "[]")
    except json.JSONDecodeError:
        authors = []
    first_author = authors[0] if authors else ""
    return {
        "first_author": str(first_author),
        "journal": str(row["journal"] or ""),
        "year": str(row["year"] or ""),
    }


def previously_rejected_pmids(run_dir: Path) -> set[str]:
    path = db_path(run_dir)
    if not path.exists():
        return set()
    with connect(run_dir) as connection:
        rows = connection.execute(
            """
            SELECT pmid
            FROM papers
            WHERE latest_status = 'rejected'
              AND pmid IS NOT NULL
              AND pmid != ''
            """
        ).fetchall()
    return {str(row["pmid"]) for row in rows}


def prior_fulltext_read_state(run_dir: Path, before_pass: int | None = None) -> dict[str, dict[str, str]]:
    path = db_path(run_dir)
    if not path.exists():
        return {}
    params: tuple[object, ...] = ()
    pass_filter = ""
    if before_pass is not None:
        pass_filter = "WHERE last_read_pass < ?"
        params = (before_pass,)
    with connect(run_dir) as connection:
        rows = connection.execute(
            f"""
            SELECT *
            FROM fulltext_read_state
            {pass_filter}
            """,
            params,
        ).fetchall()
    return {
        str(row["paper_id"]): {key: str(row[key] or "") for key in row.keys()}
        for row in rows
        if str(row["paper_id"] or "")
    }


def prior_fulltext_drop_paper_ids(run_dir: Path, before_pass: int | None = None) -> set[str]:
    return {
        paper_id
        for paper_id, row in prior_fulltext_read_state(run_dir, before_pass).items()
        if row.get("latest_fulltext_decision") == "drop"
        or row.get("latest_retention_role") == "exclude"
        or row.get("latest_query_feedback_signal") in {"tighten_query", "reviewer_calibration"}
    }


def record_collected_papers(run_dir: Path, pass_number: int, manifest_path: Path) -> None:
    if not manifest_path.exists():
        return
    now = timestamp()
    with manifest_path.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    current_paper_ids = {
        (row.get("paper_id") or "").strip()
        or paper_id_from_pmid((row.get("pmid") or "").strip())
        for row in rows
        if (row.get("paper_id") or "").strip() or (row.get("pmid") or "").strip()
    }
    with connect(run_dir) as connection:
        if current_paper_ids:
            placeholders = ", ".join("?" for _ in current_paper_ids)
            connection.execute(
                f"""
                UPDATE papers
                SET latest_status = 'superseded',
                    latest_decision = 'collection_overwrite',
                    latest_rationale = 'Paper was present in an earlier version of this pass collection but is absent from the current manifest.',
                    updated_at = ?
                WHERE last_seen_pass = ?
                  AND paper_id NOT IN ({placeholders})
                """,
                (now, pass_number, *sorted(current_paper_ids)),
            )
            connection.execute(
                f"""
                UPDATE pass_decisions
                SET status = 'superseded',
                    rationale = 'Decision belongs to an earlier version of this pass collection and is absent from the current manifest.',
                    created_at = ?
                WHERE pass_number = ?
                  AND paper_id NOT IN ({placeholders})
                """,
                (now, pass_number, *sorted(current_paper_ids)),
            )
        for row in rows:
            paper_id = (row.get("paper_id") or "").strip()
            if not paper_id:
                pmid = (row.get("pmid") or "").strip()
                paper_id = paper_id_from_pmid(pmid) if pmid else ""
            if not paper_id:
                continue
            existing = connection.execute(
                "SELECT first_seen_pass FROM papers WHERE paper_id = ?",
                (paper_id,),
            ).fetchone()
            first_seen_pass = (
                int(existing["first_seen_pass"]) if existing else pass_number
            )
            connection.execute(
                """
                INSERT INTO papers(
                    paper_id, pmid, doi, title, year, first_seen_pass, last_seen_pass,
                    latest_status, latest_decision, latest_rationale, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, 'collected', NULL, NULL, ?)
                ON CONFLICT(paper_id) DO UPDATE SET
                    pmid = excluded.pmid,
                    doi = excluded.doi,
                    title = excluded.title,
                    year = excluded.year,
                    first_seen_pass = papers.first_seen_pass,
                    last_seen_pass = excluded.last_seen_pass,
                    latest_status = CASE
                        WHEN papers.latest_status = 'rejected' THEN papers.latest_status
                        ELSE 'collected'
                    END,
                    updated_at = excluded.updated_at
                """,
                (
                    paper_id,
                    (row.get("pmid") or "").strip(),
                    (row.get("doi") or "").strip(),
                    (row.get("title") or "").strip(),
                    (row.get("year") or "").strip(),
                    first_seen_pass,
                    pass_number,
                    now,
                ),
            )
        connection.commit()


def record_abstract_triage_decisions(
    run_dir: Path,
    pass_number: int,
    second_pass_path: Path,
) -> None:
    if not second_pass_path.exists():
        return
    now = timestamp()
    with second_pass_path.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    with connect(run_dir) as connection:
        for row in rows:
            paper_id = (row.get("paper_id") or "").strip()
            pmid = (row.get("pmid") or "").strip()
            if not paper_id and pmid:
                paper_id = paper_id_from_pmid(pmid)
            if not paper_id:
                continue
            promotion = (row.get("promotion_decision") or "").strip()
            second_decision = (row.get("second_pass_decision") or "").strip()
            rationale = (row.get("second_pass_rationale") or "").strip()
            status = "rejected" if promotion == "stop" else "advanced"
            existing = connection.execute(
                "SELECT first_seen_pass FROM papers WHERE paper_id = ?",
                (paper_id,),
            ).fetchone()
            first_seen_pass = (
                int(existing["first_seen_pass"]) if existing else pass_number
            )
            connection.execute(
                """
                INSERT INTO papers(
                    paper_id, pmid, doi, title, year, first_seen_pass, last_seen_pass,
                    latest_status, latest_decision, latest_rationale, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(paper_id) DO UPDATE SET
                    pmid = excluded.pmid,
                    doi = excluded.doi,
                    title = excluded.title,
                    year = excluded.year,
                    first_seen_pass = papers.first_seen_pass,
                    last_seen_pass = excluded.last_seen_pass,
                    latest_status = excluded.latest_status,
                    latest_decision = excluded.latest_decision,
                    latest_rationale = excluded.latest_rationale,
                    updated_at = excluded.updated_at
                """,
                (
                    paper_id,
                    pmid,
                    (row.get("doi") or "").strip(),
                    (row.get("title") or "").strip(),
                    (row.get("year") or "").strip(),
                    first_seen_pass,
                    pass_number,
                    status,
                    second_decision,
                    rationale,
                    now,
                ),
            )
            connection.execute(
                """
                INSERT INTO pass_decisions(
                    pass_number, paper_id, pmid, stage, decision, status, rationale, created_at
                )
                VALUES (?, ?, ?, 'abstract_triage', ?, ?, ?, ?)
                ON CONFLICT(pass_number, paper_id, stage) DO UPDATE SET
                    decision = excluded.decision,
                    status = excluded.status,
                    rationale = excluded.rationale,
                    created_at = excluded.created_at
                """,
                (
                    pass_number,
                    paper_id,
                    pmid,
                    second_decision or promotion,
                    status,
                    rationale,
                    now,
                ),
            )
        connection.commit()


def record_fulltext_read_state(
    run_dir: Path,
    pass_number: int,
    fulltext_review_path: Path,
    evidence_path: Path,
) -> None:
    if not fulltext_review_path.exists() or not evidence_path.exists():
        return
    now = timestamp()
    with fulltext_review_path.open(encoding="utf-8") as handle:
        review_rows = list(csv.DictReader(handle))
    with evidence_path.open(encoding="utf-8") as handle:
        evidence_by_id = {
            (row.get("paper_id") or "").strip(): row
            for row in csv.DictReader(handle)
            if (row.get("paper_id") or "").strip()
        }
    with connect(run_dir) as connection:
        for row in review_rows:
            paper_id = (row.get("paper_id") or "").strip()
            pmid = (row.get("pmid") or "").strip()
            if not paper_id and pmid:
                paper_id = paper_id_from_pmid(pmid)
            if not paper_id:
                continue
            normalized_path = (row.get("normalized_path") or "").strip()
            normalized_sha256 = ""
            if normalized_path:
                try:
                    normalized_sha256 = hashlib.sha256(Path(normalized_path).read_bytes()).hexdigest()
                except OSError:
                    normalized_sha256 = ""
            evidence = evidence_by_id.get(paper_id, {})
            existing = connection.execute(
                "SELECT first_read_pass FROM fulltext_read_state WHERE paper_id = ?",
                (paper_id,),
            ).fetchone()
            first_read_pass = int(existing["first_read_pass"]) if existing else pass_number
            connection.execute(
                """
                INSERT INTO fulltext_read_state(
                    paper_id, pmid, pmcid, doi, title, first_read_pass, last_read_pass,
                    source_route, pmc_access_status, pmc_parse_status, normalized_path,
                    normalized_sha256, latest_fulltext_decision, latest_evidence_tier,
                    latest_directness, latest_target_centrality, latest_query_feedback_signal,
                    latest_retention_role, latest_rationale, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(paper_id) DO UPDATE SET
                    pmid = excluded.pmid,
                    pmcid = excluded.pmcid,
                    doi = excluded.doi,
                    title = excluded.title,
                    first_read_pass = fulltext_read_state.first_read_pass,
                    last_read_pass = excluded.last_read_pass,
                    source_route = excluded.source_route,
                    pmc_access_status = excluded.pmc_access_status,
                    pmc_parse_status = excluded.pmc_parse_status,
                    normalized_path = excluded.normalized_path,
                    normalized_sha256 = excluded.normalized_sha256,
                    latest_fulltext_decision = excluded.latest_fulltext_decision,
                    latest_evidence_tier = excluded.latest_evidence_tier,
                    latest_directness = excluded.latest_directness,
                    latest_target_centrality = excluded.latest_target_centrality,
                    latest_query_feedback_signal = excluded.latest_query_feedback_signal,
                    latest_retention_role = excluded.latest_retention_role,
                    latest_rationale = excluded.latest_rationale,
                    updated_at = excluded.updated_at
                """,
                (
                    paper_id,
                    pmid,
                    (row.get("pmcid") or "").strip(),
                    (row.get("doi") or "").strip(),
                    (row.get("title") or "").strip(),
                    first_read_pass,
                    pass_number,
                    (row.get("normalized_source_type") or "").strip(),
                    "available",
                    "usable",
                    normalized_path,
                    normalized_sha256,
                    (row.get("fulltext_decision") or "").strip(),
                    (evidence.get("evidence_tier") or "").strip(),
                    (evidence.get("directness") or "").strip(),
                    (evidence.get("target_centrality") or "").strip(),
                    (evidence.get("query_feedback_signal") or "").strip(),
                    (evidence.get("retention_role") or "").strip(),
                    (row.get("fulltext_rationale") or "").strip(),
                    now,
                ),
            )
        connection.commit()
