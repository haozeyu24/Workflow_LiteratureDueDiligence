#!/usr/bin/env python3

from __future__ import annotations

import sys
from pathlib import Path

TOOLS_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS_ROOT / "core"))
from tool_paths import WORKFLOW_ROOT, ensure_tool_paths
ensure_tool_paths()

from pass_archive import (
    active_artifacts_dir,
    active_pass_number,
    load_all_pass_csv,
    run_input_path,
)

RUNS_DIR = WORKFLOW_ROOT / "runs"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def latest_row(rows: list[dict[str, str]]) -> dict[str, str]:
    return rows[-1] if rows else {}


def field(row: dict[str, str], name: str) -> str:
    return " ".join((row.get(name, "") or "").split())


def bulletize(value: str, fallback: str = "none recorded") -> str:
    parts = [
        " ".join(part.strip().split())
        for part in value.replace("\n", ";").split(";")
        if part.strip()
    ]
    if not parts:
        return f"- {fallback}"
    return "\n".join(f"- {part}" for part in parts)


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python3 tools/fulltext/generate_fulltext_review_rules.py <run_id>")
        return 1

    run_id = sys.argv[1].strip()
    run_dir = RUNS_DIR / run_id
    pass_number = active_pass_number(run_dir) or 1
    artifacts_dir = active_artifacts_dir(run_dir)
    output_path = artifacts_dir / "fulltext_review" / "fulltext_review_rules.md"

    run_brief_path = run_input_path(run_dir, "run_brief.md")
    abstract_rules_path = artifacts_dir / "abstract_triage" / "abstract_review_rules.md"
    run_brief = read_text(run_brief_path)
    abstract_rules = read_text(abstract_rules_path)

    feedback = latest_row(
        load_all_pass_csv(run_dir, "artifacts/fulltext_review/pmc_mechanism_feedback.csv")
    )
    if feedback:
        learned_section = f"""
## Prior Full-Text Learning Applied

Use prior PMC-learning feedback to calibrate this full-text pass.

### Direct Mechanisms To Preserve

{bulletize(field(feedback, "direct_mechanisms"))}

### Supporting Mechanisms

{bulletize(field(feedback, "supporting_mechanisms"))}

### Keyword Families To Retain

{bulletize(field(feedback, "retained_keyword_families"))}

### Keyword Families To Treat As Demotion Signals

{bulletize(field(feedback, "noise_keyword_families"))}

### Missing Or Rescue Keyword Families

{bulletize(field(feedback, "missing_keyword_families"))}
"""
    else:
        learned_section = """
## Prior Full-Text Learning Applied

- No prior PMC full-text learning exists for this pass.
- Derive first-pass full-text review rules from the active `run_brief.md`,
  abstract-review rules, and normalized full-text evidence.
"""

    rules = f"""# Full-Text Review Rules

## Run

- `run_id`: `{run_id}`
- `pass`: `pass_{pass_number:03d}`
- `generated_from`: `inputs/run_brief.md`; `artifacts/abstract_triage/abstract_review_rules.md`

## Purpose

These rules are the explicit reviewer contract for full-text review in this
pass. They translate the active run inputs into full-text promotion, demotion,
and drop behavior before any `fulltext_review.csv` keep/drop decisions are
written.

## Promotion Rules

- Evaluate positive promotion signals before negative or demotion signals.
- Keep when normalized full text contains clear evidence connecting an active
  primary entity, authorized comparator, or same-family model to a declared
  mechanism/evidence class and a decision-relevant outcome, relationship, or
  evidence claim declared by the active run.
- Keep direct target papers when evidence supports the active objective's
  declared mechanism, process, relationship, perturbation, dependency,
  comparison, response variable, or other run-defined evidence need.
- Keep authorized comparator papers when same-family or explicitly allowed
  comparator evidence plausibly informs the active objective and the evidence
  class is declared in the active run brief.
- Keep limited review-frame papers only when the active run brief explicitly
  authorizes a background, field-synthesis, or perspective role and the paper
  has enough full-text evidence to support that role.

## Positive-Signal Override

- A clear positive promotion signal overrides negative, noise, or demotion
  signals.
- Terms listed under evidence-insufficient or secondary-context sections are
  demotion signals, not automatic hard exclusions.
- Do not drop a paper merely because it mentions expression, transcription,
  target genes, broad context, or other insufficient-by-itself evidence if the
  same full text also contains sufficient positive evidence for the active
  full-text objective.

## Drop Rules

- Drop only when the full text does not contain sufficient positive evidence
  for any active full-text promotion rule.
- Drop entity-only, mechanism-only, context-only, and other evidence-insufficient
  papers when no sufficient positive run-declared claim is present.
- Drop papers dominated by undeclared adjacent biology only after checking for
  direct, indirect, comparator, and authorized review-frame promotion signals.
- Record why the positive threshold was not met in `evidence_extraction.csv` so
  the paper can calibrate later query and abstract-review behavior.

## Evidence Locality Rules

- Prefer local sentence, paragraph, figure/table, or section-level evidence
  windows when available.
- Do not require all evidence terms to appear in one sentence when full-text
  evidence is distributed across a coherent section or title/abstract/results
  pattern.
- Use document-level matches as supporting evidence when they combine active
  entity terms with multiple declared mechanism/outcome dimensions, but assign
  lower confidence unless a local evidence locator is available.

## Confidence Rules

- `high`: direct target or same-family comparator evidence is locally connected
  to a declared mechanism/evidence class and required outcome, relationship, or
  evidence claim.
- `medium`: coherent document-level or section-level evidence supports the run
  objective, but the exact mechanism/outcome relation is less localized.
- `low`: weak positive evidence, useful context, or calibration signal; keep
  only if a promotion rule still applies.

{learned_section}

## Active Run Brief Snapshot

```markdown
{run_brief.strip()}
```

## Active Abstract Review Rules Snapshot

```markdown
{abstract_rules.strip()}
```
"""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rules, encoding="utf-8")
    print(f"Wrote full-text review rules to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
