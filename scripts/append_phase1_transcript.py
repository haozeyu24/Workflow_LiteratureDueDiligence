#!/usr/bin/env python3

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

from pass_archive import phase1_transcript_path


WORKFLOW_ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = WORKFLOW_ROOT / "runs"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Append a user-visible Phase 1 transcript entry to a run."
    )
    parser.add_argument("run_id", help="Run identifier under runs/")
    parser.add_argument(
        "speaker",
        choices=["user", "agent", "system"],
        help="Who produced the visible text",
    )
    parser.add_argument(
        "--pass-label",
        default="pass_001",
        help="Pass label associated with the message, such as pass_001",
    )
    parser.add_argument(
        "--stage",
        default="unspecified",
        help="Workflow stage associated with the visible text",
    )
    parser.add_argument(
        "--message-file",
        help="Path to a UTF-8 text file containing the exact visible message",
    )
    parser.add_argument(
        "--message",
        help="Inline visible message text. Prefer --message-file for multiline content.",
    )
    return parser.parse_args()


def load_message(args: argparse.Namespace) -> str:
    if args.message_file and args.message:
        raise SystemExit("Use either --message-file or --message, not both.")
    if args.message_file:
        return Path(args.message_file).read_text(encoding="utf-8").strip()
    if args.message:
        return args.message.strip()
    return sys.stdin.read().strip()


def main() -> int:
    args = parse_args()
    message = load_message(args)
    if not message:
        print("No message text provided.", file=sys.stderr)
        return 2

    run_dir = RUNS_DIR / args.run_id
    if not run_dir.exists():
        print(f"Run does not exist: {run_dir}", file=sys.stderr)
        return 2

    transcript_path = phase1_transcript_path(run_dir)
    transcript_path.parent.mkdir(parents=True, exist_ok=True)
    if not transcript_path.exists():
        header = (
            "# Phase 1 Transcript\n\n"
            "This log is the user-visible Phase 1 screen transcript for the run.\n\n"
            "## Entries\n\n"
        )
        transcript_path.write_text(header, encoding="utf-8")

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entry = (
        f"### {timestamp} | {args.pass_label} | {args.stage} | {args.speaker}\n\n"
        f"{message}\n\n"
    )
    with transcript_path.open("a", encoding="utf-8") as handle:
        handle.write(entry)

    print(f"Appended transcript entry to {transcript_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
