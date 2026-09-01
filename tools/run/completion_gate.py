#!/usr/bin/env python3

from __future__ import annotations

import sys
from pathlib import Path

TOOLS_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS_ROOT / "core"))
from tool_paths import WORKFLOW_ROOT, ensure_tool_paths
ensure_tool_paths()

import json
import subprocess
import sys
from pathlib import Path

from pass_archive import incomplete_sentinel_path, passes_dir

RUNS_DIR = WORKFLOW_ROOT / "runs"

TOOL_PATHS = {
    "assess_workflow_loops.py": WORKFLOW_ROOT / "tools" / "run" / "assess_workflow_loops.py",
    "generate_reports.py": WORKFLOW_ROOT / "tools" / "reports" / "generate_reports.py",
    "validate_run.py": WORKFLOW_ROOT / "tools" / "run" / "validate_run.py",
}


def run_script(script_name: str, run_id: str) -> subprocess.CompletedProcess[str]:
    script_path = TOOL_PATHS.get(script_name)
    if script_path is None:
        script_path = WORKFLOW_ROOT / "tools" / "run" / script_name
    return subprocess.run(
        [sys.executable, str(script_path), run_id],
        cwd=WORKFLOW_ROOT,
        text=True,
        capture_output=True,
    )


def print_result(result: subprocess.CompletedProcess[str]) -> None:
    if result.stdout.strip():
        print(result.stdout.strip())
    if result.stderr.strip():
        print(result.stderr.strip(), file=sys.stderr)


def active_pass_dir(run_dir: Path) -> Path:
    active_path = passes_dir(run_dir) / "active_pass.json"
    if active_path.exists():
        payload = json.loads(active_path.read_text(encoding="utf-8"))
        active_pass = str(payload.get("active_pass", "pass_001"))
        return passes_dir(run_dir) / active_pass
    return passes_dir(run_dir) / "pass_001"


def active_pass_number(run_dir: Path) -> int:
    active_path = passes_dir(run_dir) / "active_pass.json"
    if not active_path.exists():
        return 1
    payload = json.loads(active_path.read_text(encoding="utf-8"))
    value = payload.get("pass_number")
    if isinstance(value, int) and value > 0:
        return value
    active_pass = str(payload.get("active_pass", "pass_001"))
    try:
        return int(active_pass.rsplit("_", 1)[1])
    except (IndexError, ValueError):
        return 1


def pass_dirs(run_dir: Path) -> list[Path]:
    root = passes_dir(run_dir)
    if not root.exists():
        return []
    return sorted(path for path in root.glob("pass_[0-9][0-9][0-9]") if path.is_dir())


def cleanup_prior_pass_pmc_payloads(run_dir: Path) -> int:
    """Delete bulky prior-pass PMC source/normalized payloads before completion."""
    active_number = active_pass_number(run_dir)
    removed = 0
    for pass_dir in pass_dirs(run_dir):
        try:
            pass_number = int(pass_dir.name.rsplit("_", 1)[1])
        except (IndexError, ValueError):
            continue
        if pass_number >= active_number:
            continue
        pmc_dir = pass_dir / "artifacts" / "fulltext_import" / "PMC_XML"
        if not pmc_dir.exists():
            continue
        for path in sorted(pmc_dir.rglob("*"), reverse=True):
            if path.is_file():
                path.unlink()
                removed += 1
            elif path.is_dir():
                try:
                    path.rmdir()
                except OSError:
                    pass
        try:
            pmc_dir.rmdir()
        except OSError:
            pass
    return removed


def write_incomplete_sentinel(run_dir: Path, reason: str) -> None:
    incomplete_sentinel_path(run_dir).write_text(
        "This run is not workflow-complete.\n"
        "Do not report the workflow as done until tools/run/completion_gate.py passes.\n"
        f"Reason: {reason}\n",
        encoding="utf-8",
    )


def try_write_incomplete_sentinel(run_dir: Path, reason: str) -> bool:
    try:
        write_incomplete_sentinel(run_dir, reason)
    except OSError as exc:
        print(
            f"Could not update {incomplete_sentinel_path(run_dir).name}: {exc}. "
            "This is an execution-environment write failure, not a scientific completion signal.",
            file=sys.stderr,
        )
        return False
    return True


def main() -> int:
    if len(sys.argv) not in {2, 3}:
        print("Usage: python3 tools/run/completion_gate.py [--check-only] <run_id>")
        return 2

    check_only = False
    args = sys.argv[1:]
    if args[0] == "--check-only":
        check_only = True
        args = args[1:]
    if len(args) != 1:
        print("Usage: python3 tools/run/completion_gate.py [--check-only] <run_id>")
        return 2

    run_id = args[0].strip()
    run_dir = RUNS_DIR / run_id
    if not run_dir.exists():
        print(f"Run does not exist: {run_dir}")
        return 2

    if not check_only:
        assess = run_script("assess_workflow_loops.py", run_id)
        print_result(assess)
        if assess.returncode != 0:
            try_write_incomplete_sentinel(run_dir, "controller assessment failed")
            print("WORKFLOW INCOMPLETE: controller assessment failed.")
            return 1

        state_path = active_pass_dir(run_dir) / "artifacts" / "workflow_control" / "workflow_state.json"
        try:
            candidate_state = json.loads(state_path.read_text(encoding="utf-8"))
        except Exception:
            candidate_state = {}
        if candidate_state.get("status") == "complete":
            try:
                removed_count = cleanup_prior_pass_pmc_payloads(run_dir)
            except OSError as exc:
                try_write_incomplete_sentinel(run_dir, f"prior-pass PMC cleanup failed: {exc}")
                print(f"WORKFLOW INCOMPLETE: prior-pass PMC cleanup failed: {exc}")
                return 1
            if removed_count:
                print(f"Deleted {removed_count} prior-pass PMC payload files before completion.")

        report = run_script("generate_reports.py", run_id)
        print_result(report)
        if report.returncode != 0:
            try_write_incomplete_sentinel(run_dir, "report generation failed")
            print("WORKFLOW INCOMPLETE: report generation failed.")
            return 1

    validate = run_script("validate_run.py", run_id)
    print_result(validate)
    if validate.returncode != 0:
        if not check_only:
            try_write_incomplete_sentinel(run_dir, "validation failed")
        print("WORKFLOW INCOMPLETE: validation failed.")
        return 1

    state_path = active_pass_dir(run_dir) / "artifacts" / "workflow_control" / "workflow_state.json"
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except Exception as exc:
        if not check_only:
            try_write_incomplete_sentinel(run_dir, f"could not read workflow_state.json: {exc}")
        print(f"WORKFLOW INCOMPLETE: could not read workflow_state.json: {exc}")
        return 1

    sentinel_path = incomplete_sentinel_path(run_dir)
    status = state.get("status")
    if status != "complete":
        if not check_only:
            try_write_incomplete_sentinel(run_dir, f"controller status is {status!r}, not 'complete'")
        print(f"WORKFLOW INCOMPLETE: controller status is {status!r}, not 'complete'.")
        print(f"Next action: {state.get('next_action', 'unknown')}")
        print(f"Reason: {state.get('reason', '')}")
        return 1
    if sentinel_path.exists():
        print(f"WORKFLOW INCOMPLETE: sentinel still exists at {sentinel_path}.")
        return 1

    print("WORKFLOW COMPLETE: validation passed, controller status is complete, and no incomplete sentinel remains.")
    print(f"Completion signal: {state.get('completion_signal', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
