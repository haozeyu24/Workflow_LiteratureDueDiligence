#!/usr/bin/env python3

from __future__ import annotations

import sys
from pathlib import Path

TOOLS_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS_ROOT / "core"))
from tool_paths import WORKFLOW_ROOT, ensure_tool_paths
ensure_tool_paths()

import sys
from pathlib import Path

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
        print("Usage: python3 tools/abstract_triage/generate_abstract_review_rules.py <run_id>")
        return 1

    run_id = sys.argv[1].strip()
    run_dir = RUNS_DIR / run_id
    pass_number = active_pass_number(run_dir) or 1
    artifacts_dir = active_artifacts_dir(run_dir)
    output_path = artifacts_dir / "abstract_triage" / "abstract_review_rules.md"

    run_brief_path = run_input_path(run_dir, "run_brief.md")
    search_strategy_path = artifacts_dir / "search_strategy" / "search_strategy.md"
    run_brief = read_text(run_brief_path)
    search_strategy = read_text(search_strategy_path)

    feedback = latest_row(
        load_all_pass_csv(run_dir, "artifacts/fulltext_review/pmc_mechanism_feedback.csv")
    )
    guidance_revision = latest_row(
        load_all_pass_csv(run_dir, "artifacts/workflow_control/run_guidance_revision_log.csv")
    )

    if feedback:
        learned_section = f"""
## Full-Text Learning Applied

Use the latest PMC-learning feedback to calibrate this abstract pass.

### Direct Mechanisms To Preserve

{bulletize(field(feedback, "direct_mechanisms"))}

### Supporting Mechanisms

{bulletize(field(feedback, "supporting_mechanisms"))}

### Keyword Families To Retain

{bulletize(field(feedback, "retained_keyword_families"))}

### Keyword Families To Treat As Noise

{bulletize(field(feedback, "noise_keyword_families"))}

### Missing Or Rescue Keyword Families

{bulletize(field(feedback, "missing_keyword_families"))}

### Abstract Rule Changes From Full Text

{bulletize(field(feedback, "recommended_abstract_rule_changes"))}

### Run-Guidance Revision Record

{bulletize('; '.join(value for value in guidance_revision.values() if value))}
"""
    else:
        learned_section = """
## Full-Text Learning Applied

- No prior PMC full-text learning exists for this pass.
- Derive first-pass reviewer rules only from the original prompt, active
  `run_brief.md`, and active `search_strategy.md`.
"""

    rules = f"""# Abstract Review Rules

## Run

- `run_id`: `{run_id}`
- `pass`: `pass_{pass_number:03d}`
- `generated_from`: `inputs/run_brief.md`; `artifacts/search_strategy/search_strategy.md`

## Purpose

These rules are the explicit reviewer contract for abstract triage in this
pass. They translate the active run inputs into inclusion, exclusion, rescue,
and promotion behavior before any title/abstract decisions are written.

## First-Pass Include Rules

- Include when the title or abstract contains a primary entity or named
  intervention from the active run brief plus a declared mechanism, evidence
  class, outcome, perturbation, relationship, context, or synthesis-frame
  signal.
- For pass 1, remain recall-friendly but require a claim-shaped match. Do not
  include papers on the basis of a primary entity plus one weak mechanism or
  context term alone.
- Include direct mechanistic papers when the abstract links an active primary
  entity to a declared mechanism class and interpretable response, phenotype,
  dependency, or outcome.
- Include applied, translational, cohort, model-system, or context-specific
  papers when the abstract connects an active primary entity or intervention to
  a declared outcome, response variable, evidence claim, or decision-relevant
  question.
- Include a limited number of review or field-synthesis papers only when they
  clearly support the active review/synthesis framing.

## First-Pass Exclude Rules

- Exclude entity-only, mechanism-only, outcome-only, context-only, and
  background-only abstracts that do not satisfy the active claim shape.
- Exclude papers dominated by run-specific exclusions, deferred adjacent
  biology, or evidence classes marked insufficient in `run_brief.md`.
- Exclude comparator or adjacent-system papers unless the abstract makes the
  authorized comparator relationship explicit.
- Exclude papers whose only relevance is broad field background unless the
  review-frame section justifies retention.

## First-Pass Confidence Rules

- `high`: primary entity plus declared mechanism/evidence plus required
  outcome/relationship are explicit.
- `medium`: likely in scope, but one element of the evidence shape is partial
  or implicit.
- `low`: useful as a first-pass learning probe, rescue candidate, or limited
  review-frame background, but still has a primary entity plus at least two
  distinct declared evidence dimensions. A single weak overlap is not enough.

## Second-Pass Rescue Rules

- Carry first-pass includes forward unless the include clearly violated the
  active rules.
- Rescue first-pass excludes when they contain a high-value missed direct,
  applied, translational, comparator, mechanism/evidence, declared-context, or
  review-frame signal under the active run brief.
- Apply any full-text-derived rescue terms or demotion rules listed below for
  pass 2 or later.
- Stop papers that remain entity-only, mechanism-only, pathway-only,
  prevalence-only, context-only, or background-only after rescue review.

## Promotion Rules

- `advance_to_import`: first-pass includes and rescued second-pass includes.
- `stop`: confirmed excludes.
- Do not use expected PDF availability, PMC availability, import burden, or
  desired corpus size as a reason to stop a paper during abstract triage.

{learned_section}

## Active Run Brief Snapshot

```markdown
{run_brief.strip()}
```

## Active Search Strategy Snapshot

```markdown
{search_strategy.strip()}
```
"""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rules, encoding="utf-8")
    print(f"Wrote abstract review rules to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
