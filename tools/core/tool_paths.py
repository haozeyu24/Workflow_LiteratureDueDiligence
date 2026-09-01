from __future__ import annotations

import sys
from pathlib import Path


TOOLS_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_ROOT = TOOLS_ROOT.parent

TOOL_MODULE_DIRS = (
    TOOLS_ROOT / "core",
    TOOLS_ROOT / "run",
    TOOLS_ROOT / "collection",
    TOOLS_ROOT / "abstract_triage",
    TOOLS_ROOT / "fulltext",
    TOOLS_ROOT / "pdf",
    TOOLS_ROOT / "reports",
)


def ensure_tool_paths() -> None:
    for path in TOOL_MODULE_DIRS:
        path_text = str(path)
        if path_text not in sys.path:
            sys.path.insert(0, path_text)
