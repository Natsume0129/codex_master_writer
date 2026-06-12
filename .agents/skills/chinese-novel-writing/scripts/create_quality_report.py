#!/usr/bin/env python3
"""Create a deterministic chapter quality-report template."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from _novel_utils import normalize_chapter_label, now_iso, safe_relative


def default_draft(project: Path, branch: str, chapter_label: str) -> Path:
    drafts_dir = project / "branches" / branch / "drafts"
    for suffix in (".md", ".txt", ".yaml"):
        path = drafts_dir / f"{chapter_label}{suffix}"
        if path.exists():
            return path
    return drafts_dir / f"{chapter_label}.md"


def default_context_pack(project: Path) -> Path:
    return project / "context_packs" / "latest_context_pack.md"


def render_report(args: argparse.Namespace, draft: Path, context_pack: Path, output: Path) -> str:
    project = args.project.resolve()
    draft_rel = safe_relative(draft, project)
    context_rel = safe_relative(context_pack, project)
    output_rel = safe_relative(output, project)
    draft_state = "present" if draft.exists() else "missing"
    context_state = "present" if context_pack.exists() else "missing"
    mode_note = "Template-only report. Fill findings after reviewing the draft and context pack." if args.template_only else "Review report template. Fill only findings supported by evidence."
    return f"""# Chapter Quality Report

schema_version: 0.4
generated_at: {now_iso()}
branch: {args.branch}
chapter: {args.chapter}
chapter_label: {args.chapter_label}
draft: {draft_rel}
draft_status: {draft_state}
context_pack: {context_rel}
context_pack_status: {context_state}
output: {output_rel}
severity_scope: {args.severity}

## Summary

- Overall status:
- Main risk:
- Decision needed:
- Note: {mode_note}

## Serious Issues

| id | issue | evidence | suggested fix | patch candidate | requires user confirmation |
| --- | --- | --- | --- | --- | --- |
| S-001 |  |  |  |  |  |

## Medium Issues

| id | issue | evidence | suggested fix | patch candidate | requires user confirmation |
| --- | --- | --- | --- | --- | --- |
| M-001 |  |  |  |  |  |

## Light Issues

| id | issue | evidence | suggested fix | patch candidate | requires user confirmation |
| --- | --- | --- | --- | --- | --- |
| L-001 |  |  |  |  |  |

## Suggested Fixes

- Keep fixes local to this chapter unless the evidence requires a story-bible update.
- Put canon, timeline, foreshadowing, and relationship updates in a pending patch instead of editing canon directly.
- Mark uncertain findings as uncertain and include the source evidence.

## Patch Candidates

```yaml
schema_version: "0.4"
patch_id: "quality_report_{args.branch}_{args.chapter_label}"
branch: "{args.branch}"
chapter: "{args.chapter}"
source_draft: "{draft_rel}"
status: "pending"
updates:
  characters: []
  relationships: []
  worldbuilding: []
  timeline: []
  foreshadowing_added: []
  foreshadowing_paid_off: []
  open_questions_added: []
  hard_constraints_added: []
  continuity_issues: []
requires_user_confirmation: []
notes: "Candidate patch items from quality report. Review before apply-patch --confirm."
```

## Evidence

| source | location | quote or paraphrase | confidence |
| --- | --- | --- | --- |
| {draft_rel} |  |  |  |
| {context_rel} |  |  |  |

## Next Actions

1. Review serious issues first.
2. Convert accepted patch candidates into `pending_updates/`.
3. Run `apply-patch` as a dry run before confirmed updates.
4. Update the chapter draft after user-confirmed major changes.
"""


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a chapter quality-report template.")
    parser.add_argument("--project", "--project-root", dest="project", required=True, type=Path)
    parser.add_argument("--branch", default="main")
    parser.add_argument("--chapter", required=True)
    parser.add_argument("--draft", type=Path)
    parser.add_argument("--context-pack", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--template-only", action="store_true")
    parser.add_argument("--severity", choices=("serious", "medium", "light", "all"), default="all")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    project = args.project.resolve()
    args.project = project
    if not project.exists():
        print(f"error: project not found: {project}", file=sys.stderr)
        return 1
    branch_dir = project / "branches" / args.branch
    if not branch_dir.exists():
        print(f"error: branch not found: {branch_dir}", file=sys.stderr)
        return 1

    args.chapter_label = normalize_chapter_label(args.chapter)
    draft = args.draft.resolve() if args.draft else default_draft(project, args.branch, args.chapter_label)
    context_pack = args.context_pack.resolve() if args.context_pack else default_context_pack(project)
    output = (
        args.output.resolve()
        if args.output
        else branch_dir / "reviews" / f"{args.chapter_label}_quality_report.md"
    )
    if output.exists() and not args.force:
        print(f"error: output exists: {output}. Use --force to overwrite.", file=sys.stderr)
        return 1
    if not args.template_only and not draft.exists():
        print(f"warning: draft not found: {draft}")
    if not context_pack.exists():
        print(f"warning: context pack not found: {context_pack}")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_report(args, draft, context_pack, output), encoding="utf-8")
    print(f"Wrote quality report: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
