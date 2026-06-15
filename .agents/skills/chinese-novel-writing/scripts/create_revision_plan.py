#!/usr/bin/env python3
"""Create a v0.8 revision plan with an embedded revision prompt."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from _novel_utils import now_iso
from _style_voice_utils import (
    SCHEMA_VERSION,
    artifact_status,
    chapter_label,
    default_context_pack,
    default_draft,
    default_revision_plan,
    default_scene_outline,
    default_style_audit,
    ensure_branch,
    frontmatter,
    missing_paths,
    project_name,
    rel,
    resolve_project_relative,
    write_text_if_allowed,
)


def default_quality_report(project: Path, branch: str, label: str) -> Path:
    return project / "branches" / branch / "reviews" / f"{label}_quality_report.md"


def render_plan(
    args: argparse.Namespace,
    project: Path,
    draft: Path,
    context_pack: Path,
    quality_report: Path,
    style_audit_report: Path,
    scene_outline: Path,
    output: Path,
) -> str:
    label = chapter_label(args.chapter)
    missing = missing_paths(
        project,
        [
            ("draft", draft),
            ("context_pack", context_pack),
            ("quality_report", quality_report),
            ("style_audit_report", style_audit_report),
            ("scene_outline", scene_outline),
        ],
    )
    metadata = frontmatter(
        {
            "schema_version": SCHEMA_VERSION,
            "report_type": "revision_plan",
            "project": project_name(project),
            "branch": args.branch,
            "chapter": label,
            "draft": rel(draft, project),
            "quality_report": rel(quality_report, project),
            "style_audit_report": rel(style_audit_report, project),
            "generated_at": now_iso(),
            "status": "draft",
        }
    )
    missing_text = "\n".join(f"- {item}" for item in missing) or "- None"
    return f"""{metadata}

# Revision Plan

## Revision Goal

- Fill after reviewing quality and style audit reports.

## Must Preserve

- Preserve user-confirmed canon, branch facts, chapter function, and scene outline constraints.
- Do not apply major plot changes without user confirmation.

## Continuity Fixes

- Fill from `{rel(quality_report, project)}`.

## Style Fixes

- Fill from `{rel(style_audit_report, project)}`.

## Character Voice Fixes

- Fill from style audit and voice sheet evidence.

## Scene Structure Fixes

- Compare the draft against `{rel(scene_outline, project)}`.

## Pacing Fixes

- Fill after model review.

## Anti-AI Flavor Fixes

- Reduce generic summaries, repetitive emotional explanation, flattened dialogue, and template hooks where evidence supports it.

## Line-Level Targets

- List specific paragraphs or line ranges only after reviewing the draft.

## Patch Candidates

```yaml
updates:
  characters: []
  relationships: []
  worldbuilding: []
  timeline: []
  foreshadowing_added: []
  foreshadowing_paid_off: []
  continuity_issues: []
requires_user_confirmation: []
```

## Requires User Decision

- None recorded by script.

## Missing Sections

{missing_text}

## Revision Prompt

Revise `{rel(draft, project)}` using:

1. context pack: `{rel(context_pack, project)}` ({artifact_status(context_pack)})
2. quality report: `{rel(quality_report, project)}` ({artifact_status(quality_report)})
3. style audit report: `{rel(style_audit_report, project)}` ({artifact_status(style_audit_report)})
4. scene outline: `{rel(scene_outline, project)}` ({artifact_status(scene_outline)})

Do not read `raw_text/full_text.txt`. Do not rewrite canon or `branches/main` outside the active branch. Do not apply patches automatically. Preserve confirmed facts and put major plot decisions under Requires User Decision.

## Next Action

Review this plan, then perform the revision in a separate draft or chat response. After revision, create a pending patch and review it before apply.
"""


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a v0.8 revision plan.")
    parser.add_argument("--project", "--project-root", dest="project", required=True, type=Path)
    parser.add_argument("--branch", default="main")
    parser.add_argument("--chapter", required=True)
    parser.add_argument("--draft", type=Path)
    parser.add_argument("--context-pack", type=Path)
    parser.add_argument("--quality-report", type=Path)
    parser.add_argument("--style-audit-report", type=Path)
    parser.add_argument("--scene-outline", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--force", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    project = args.project.resolve()
    try:
        ensure_branch(project, args.branch)
        label = chapter_label(args.chapter)
        draft = resolve_project_relative(project, args.draft) if args.draft else default_draft(project, args.branch, label)
        context_pack = resolve_project_relative(project, args.context_pack) if args.context_pack else default_context_pack(project)
        quality_report = (
            resolve_project_relative(project, args.quality_report)
            if args.quality_report
            else default_quality_report(project, args.branch, label)
        )
        style_audit_report = (
            resolve_project_relative(project, args.style_audit_report)
            if args.style_audit_report
            else default_style_audit(project, args.branch, label)
        )
        scene_outline = resolve_project_relative(project, args.scene_outline) if args.scene_outline else default_scene_outline(project, args.branch, label)
        output = resolve_project_relative(project, args.output) if args.output else default_revision_plan(project, args.branch, label)
        assert draft is not None
        assert context_pack is not None
        assert quality_report is not None
        assert style_audit_report is not None
        assert scene_outline is not None
        assert output is not None
        write_text_if_allowed(
            output,
            render_plan(args, project, draft, context_pack, quality_report, style_audit_report, scene_outline, output),
            args.force,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"Wrote revision plan: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
