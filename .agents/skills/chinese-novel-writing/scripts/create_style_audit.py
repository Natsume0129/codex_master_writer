#!/usr/bin/env python3
"""Create a v0.8 style audit report skeleton and optional prompt."""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

from _style_voice_utils import (
    SCHEMA_VERSION,
    artifact_status,
    chapter_label,
    default_context_pack,
    default_draft,
    default_scene_outline,
    default_style_audit,
    default_style_profile,
    default_voice_sheet,
    ensure_branch,
    frontmatter,
    missing_paths,
    project_name,
    read_head,
    rel,
    resolve_project_relative,
    write_text_if_allowed,
)
from _novel_utils import now_iso


AI_FLAVOR_TERMS = ["仿佛", "似乎", "某种", "他知道", "她明白", "无法言说", "命运", "心底"]


def deterministic_signals(draft: Path) -> tuple[list[str], list[str]]:
    if not draft.exists():
        return [], ["draft missing; style audit prompt can still be generated"]
    text = read_head(draft, 30000)
    warnings: list[str] = []
    signals: list[str] = []
    paragraphs = [item.strip() for item in re.split(r"\n\s*\n", text) if item.strip()]
    long_paragraphs = [len(item) for item in paragraphs if len(item) > 900]
    if long_paragraphs:
        warnings.append(f"long paragraphs detected: {len(long_paragraphs)}")
    dialogue_lines = [line for line in text.splitlines() if "「" in line or "\"" in line or line.strip().startswith("- ")]
    if text and len(dialogue_lines) < max(1, len(paragraphs) // 8):
        signals.append("dialogue may be sparse")
    term_counts = {term: text.count(term) for term in AI_FLAVOR_TERMS if text.count(term) >= 3}
    if term_counts:
        warnings.append("repeated possible AI-flavor terms: " + ", ".join(f"{k}={v}" for k, v in term_counts.items()))
    words = re.findall(r"[\u4e00-\u9fff]{2,6}|[A-Za-z]{3,}", text)
    repeated = [f"{word}={count}" for word, count in Counter(words).most_common(10) if count >= 8]
    if repeated:
        signals.append("high-frequency terms: " + ", ".join(repeated))
    if text and not re.search(r"[走看拿推坐站握伸转回抬压听问答笑]", text):
        warnings.append("few concrete action verbs detected by heuristic")
    return signals, warnings


def render_report(
    args: argparse.Namespace,
    project: Path,
    draft: Path,
    context_pack: Path,
    style_profile: Path,
    voice_sheet: Path,
    scene_outline: Path,
    output: Path,
) -> str:
    signals, warnings = deterministic_signals(draft)
    missing = missing_paths(
        project,
        [
            ("draft", draft),
            ("context_pack", context_pack),
            ("style_profile", style_profile),
            ("character_voice_sheet", voice_sheet),
            ("scene_outline", scene_outline),
        ],
    )
    status = "warn" if warnings or missing else "pass"
    metadata = frontmatter(
        {
            "schema_version": SCHEMA_VERSION,
            "report_type": "style_audit_report",
            "project": project_name(project),
            "branch": args.branch,
            "chapter": chapter_label(args.chapter),
            "draft": rel(draft, project),
            "style_profile": rel(style_profile, project),
            "character_voice_sheet": rel(voice_sheet, project),
            "scene_outline": rel(scene_outline, project),
            "generated_at": now_iso(),
            "status": status,
        }
    )
    warning_text = "\n".join(f"- {item}" for item in warnings) or "- None"
    signal_text = "\n".join(f"- {item}" for item in signals) or "- None"
    missing_text = "\n".join(f"- {item}" for item in missing) or "- None"
    return f"""{metadata}

# Style Audit Report

## Summary

- Status: `{status}`
- Draft status: `{artifact_status(draft)}`
- Missing sections: {len(missing)}

## Style Fit

- Fill after model review against `{rel(style_profile, project)}`.

## Narrator Voice

- Fill after model review.

## Character Voice

- Fill after checking `{rel(voice_sheet, project)}`.

## Dialogue Differentiation

- Fill after model review.

## Scene Function Fit

- Compare against `{rel(scene_outline, project)}`.

## Pacing

- Fill after model review.

## Anti-AI Flavor Signals

{signal_text}

## Repetition Signals

{signal_text}

## Over-Explanation Signals

- Fill after model review; use deterministic signals only as hints.

## Missing Concrete Detail

{warning_text}

## Hook Strength

- Fill after model review.

## Conflicts With Canon Or Outline

- None recorded by script. Codex/model must cite evidence.

## Required User Decisions

- None recorded by script.

## Suggestions

{missing_text}

## Next Action

Use this report with `create-revision-plan`. Do not directly rewrite the draft from the audit script.
"""


def render_prompt(
    args: argparse.Namespace,
    project: Path,
    draft: Path,
    context_pack: Path,
    style_profile: Path,
    voice_sheet: Path,
    scene_outline: Path,
    output: Path,
    prompt_output: Path,
) -> str:
    return f"""# Style Audit Prompt

schema_version: {SCHEMA_VERSION}
generated_at: {now_iso()}
project: {project_name(project)}
branch: {args.branch}
chapter: {chapter_label(args.chapter)}
draft: {rel(draft, project)} ({artifact_status(draft)})
context_pack: {rel(context_pack, project)} ({artifact_status(context_pack)})
style_profile: {rel(style_profile, project)} ({artifact_status(style_profile)})
character_voice_sheet: {rel(voice_sheet, project)} ({artifact_status(voice_sheet)})
scene_outline: {rel(scene_outline, project)} ({artifact_status(scene_outline)})
style_audit_report: {rel(output, project)}
prompt_output: {rel(prompt_output, project)}

## Task

Review the draft against style profile, character voice sheet, scene outline, and context pack. Fill `{rel(output, project)}`.

## Rules

1. Do not rewrite the draft inside the audit.
2. Do not read `raw_text/full_text.txt`.
3. Mark style drift, voice blending, AI-flavor risks, repetition, over-explanation, missing concrete detail, hook weakness, and scene-function misses.
4. Every finding needs evidence from the draft or listed artifacts.
5. Put major plot or character changes under Required User Decisions.
6. Use `create-revision-plan` for the next revision step.
"""


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a v0.8 style audit report.")
    parser.add_argument("--project", "--project-root", dest="project", required=True, type=Path)
    parser.add_argument("--branch", default="main")
    parser.add_argument("--chapter", required=True)
    parser.add_argument("--draft", type=Path)
    parser.add_argument("--context-pack", type=Path)
    parser.add_argument("--style-profile", type=Path)
    parser.add_argument("--voice-sheet", type=Path)
    parser.add_argument("--scene-outline", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--prompt-output", type=Path)
    parser.add_argument("--prompt", action="store_true")
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
        style_profile = resolve_project_relative(project, args.style_profile) if args.style_profile else default_style_profile(project, args.branch)
        voice_sheet = resolve_project_relative(project, args.voice_sheet) if args.voice_sheet else default_voice_sheet(project, args.branch)
        scene_outline = resolve_project_relative(project, args.scene_outline) if args.scene_outline else default_scene_outline(project, args.branch, label)
        output = resolve_project_relative(project, args.output) if args.output else default_style_audit(project, args.branch, label)
        prompt_output = (
            resolve_project_relative(project, args.prompt_output)
            if args.prompt_output
            else project / "branches" / args.branch / "reviews" / f"{label}_style_audit_prompt.md"
        )
        assert draft is not None
        assert context_pack is not None
        assert style_profile is not None
        assert voice_sheet is not None
        assert scene_outline is not None
        assert output is not None
        assert prompt_output is not None
        write_text_if_allowed(
            output,
            render_report(args, project, draft, context_pack, style_profile, voice_sheet, scene_outline, output),
            args.force,
        )
        if args.prompt:
            write_text_if_allowed(
                prompt_output,
                render_prompt(args, project, draft, context_pack, style_profile, voice_sheet, scene_outline, output, prompt_output),
                args.force,
            )
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"Wrote style audit report: {output}")
    if args.prompt:
        print(f"Wrote style audit prompt: {prompt_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
