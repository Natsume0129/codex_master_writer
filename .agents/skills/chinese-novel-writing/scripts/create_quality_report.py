#!/usr/bin/env python3
"""Create deterministic chapter quality-report and review-prompt templates."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from _novel_utils import normalize_chapter_label, now_iso, resolve_project_relative, safe_relative


def default_draft(project: Path, branch: str, chapter_label: str) -> Path:
    drafts_dir = project / "branches" / branch / "drafts"
    for suffix in (".md", ".txt", ".yaml"):
        path = drafts_dir / f"{chapter_label}{suffix}"
        if path.exists():
            return path
    return drafts_dir / f"{chapter_label}.md"


def default_context_pack(project: Path) -> Path:
    return project / "context_packs" / "latest_context_pack.md"


def default_prompt_output(project: Path, branch: str, chapter_label: str) -> Path:
    return project / "branches" / branch / "reviews" / f"{chapter_label}_quality_review_prompt.md"


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


def render_review_prompt(
    args: argparse.Namespace,
    draft: Path,
    context_pack: Path,
    report_output: Path,
    prompt_output: Path,
) -> str:
    project = args.project.resolve()
    draft_rel = safe_relative(draft, project)
    context_rel = safe_relative(context_pack, project)
    report_rel = safe_relative(report_output, project)
    prompt_rel = safe_relative(prompt_output, project)
    return f"""# Chapter Quality Review Prompt

schema_version: 0.5
generated_at: {now_iso()}
branch: {args.branch}
chapter: {args.chapter}
chapter_label: {args.chapter_label}
draft: {draft_rel}
draft_status: {"present" if draft.exists() else "missing"}
context_pack: {context_rel}
context_pack_status: {"present" if context_pack.exists() else "missing"}
report_output: {report_rel}
prompt_output: {prompt_rel}
severity_scope: {args.severity}

## Task

Review the draft against the context pack and fill the quality report at `{report_rel}`.

## Required Reading

1. Read `{context_rel}`.
2. Read `{draft_rel}`.
3. Do not read `raw_text/full_text.txt`.
4. Do not silently expand scope to unrelated canon files unless the context pack points to a narrow source needed for evidence.

## Review Dimensions

- Character consistency and voice.
- Branch boundary and canon consistency.
- Timeline, item state, world-rule, and information-asymmetry conflicts.
- Chapter function, scene-beat payoff, pacing, conflict strength, and ending hook.
- Foreshadowing added, reinforced, paid off, abandoned, or contradicted.
- Style drift, repetition, generic phrasing, and flattened dialogue.
- Unapproved major plot decisions.

## Evidence Rules

- Every finding must cite the draft, context pack, function card, or a source named inside the context pack.
- Mark uncertain issues as uncertain; do not promote inferred facts to confirmed.
- Do not rewrite the draft inside the report unless the user asked for revision.
- Put canon, timeline, relationship, foreshadowing, or hard-constraint updates under patch candidates.
- Any major plot change must go under `requires_user_confirmation`.

## Output Contract

- Fill `{report_rel}`.
- Keep serious, medium, and light findings separated.
- Include a concise next-action recommendation.
- Do not apply patches automatically.
"""


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a chapter quality-report template.")
    parser.add_argument("--project", "--project-root", dest="project", required=True, type=Path)
    parser.add_argument("--branch", default="main")
    parser.add_argument("--chapter", required=True)
    parser.add_argument("--draft", type=Path)
    parser.add_argument("--context-pack", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--prompt-output", type=Path)
    parser.add_argument("--template-only", action="store_true")
    parser.add_argument("--with-prompt", action="store_true")
    parser.add_argument("--prompt-only", action="store_true")
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
    draft = (
        resolve_project_relative(project, args.draft)
        if args.draft
        else default_draft(project, args.branch, args.chapter_label)
    )
    assert draft is not None
    context_pack = (
        resolve_project_relative(project, args.context_pack)
        if args.context_pack
        else default_context_pack(project)
    )
    assert context_pack is not None
    output = (
        resolve_project_relative(project, args.output)
        if args.output
        else branch_dir / "reviews" / f"{args.chapter_label}_quality_report.md"
    )
    prompt_output = (
        resolve_project_relative(project, args.prompt_output)
        if args.prompt_output
        else default_prompt_output(project, args.branch, args.chapter_label)
    )
    assert output is not None
    assert prompt_output is not None
    if not args.prompt_only and output.exists() and not args.force:
        print(f"error: output exists: {output}. Use --force to overwrite.", file=sys.stderr)
        return 1
    if (args.with_prompt or args.prompt_only) and prompt_output.exists() and not args.force:
        print(f"error: prompt output exists: {prompt_output}. Use --force to overwrite.", file=sys.stderr)
        return 1
    if not args.template_only and not draft.exists():
        print(f"warning: draft not found: {draft}")
    if not context_pack.exists():
        print(f"warning: context pack not found: {context_pack}")

    if not args.prompt_only:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(render_report(args, draft, context_pack, output), encoding="utf-8")
        print(f"Wrote quality report: {output}")
    if args.with_prompt or args.prompt_only:
        prompt_output.parent.mkdir(parents=True, exist_ok=True)
        prompt_output.write_text(
            render_review_prompt(args, draft, context_pack, output, prompt_output),
            encoding="utf-8",
        )
        print(f"Wrote quality review prompt: {prompt_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
