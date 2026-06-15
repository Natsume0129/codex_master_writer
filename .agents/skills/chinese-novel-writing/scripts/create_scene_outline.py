#!/usr/bin/env python3
"""Create a v0.8 chapter scene outline skeleton and optional prompt."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from _novel_utils import now_iso, yaml_quote
from _style_voice_utils import (
    SCHEMA_VERSION,
    artifact_status,
    chapter_label,
    default_context_pack,
    default_function_card,
    default_scene_outline,
    default_style_profile,
    default_voice_sheet,
    ensure_branch,
    missing_paths,
    project_name,
    read_head,
    rel,
    resolve_project_relative,
    write_text_if_allowed,
    yaml_list,
)


def render_outline(
    args: argparse.Namespace,
    project: Path,
    context_pack: Path,
    function_card: Path,
    style_profile: Path,
    voice_sheet: Path,
    output: Path,
) -> str:
    missing = missing_paths(
        project,
        [
            ("context_pack", context_pack),
            ("chapter_function_card", function_card),
            ("style_profile", style_profile),
            ("character_voice_sheet", voice_sheet),
        ],
    )
    label = chapter_label(args.chapter)
    lines = [
        f"schema_version: {yaml_quote(SCHEMA_VERSION)}",
        'artifact_type: "scene_outline"',
        f"project: {yaml_quote(project_name(project))}",
        f"branch: {yaml_quote(args.branch)}",
        f"chapter: {yaml_quote(label)}",
        f"title: {yaml_quote(args.title)}",
        f"created_at: {yaml_quote(now_iso())}",
        f"source_context_pack: {yaml_quote(rel(context_pack, project))}",
        f"source_chapter_function_card: {yaml_quote(rel(function_card, project))}",
        f"style_profile: {yaml_quote(rel(style_profile, project))}",
        f"character_voice_sheet: {yaml_quote(rel(voice_sheet, project))}",
        'chapter_goal: ""',
        'chapter_promise: ""',
        'chapter_hook: ""',
        "scenes:",
        '  - scene_id: "scene_001"',
        '    scene_title: ""',
        '    scene_function: ""',
        '    pov_character: ""',
        '    location: ""',
        '    time: ""',
        '    entering_state: ""',
        '    conflict: ""',
        "    beat_sequence: []",
        "    information_revealed: []",
        "    information_hidden: []",
        "    character_state_changes: []",
        "    relationship_state_changes: []",
        "    foreshadowing_used: []",
        "    foreshadowing_added: []",
        "    style_notes: []",
        "    voice_notes: []",
        '    exit_hook: ""',
        "    required_facts: []",
        "    forbidden_moves: []",
        "    requires_user_decision: []",
        "source:",
        f"  - {yaml_quote(rel(context_pack, project))}",
        f"  - {yaml_quote(rel(function_card, project))}",
        'status: "draft"',
        'confidence: "medium"',
    ]
    yaml_list(lines, "missing_sections", missing)
    lines.append(f'notes: {yaml_quote("Scene outline is a planning artifact, not prose and not a source of truth.")}')
    lines.append("")
    return "\n".join(lines)


def render_prompt(
    args: argparse.Namespace,
    project: Path,
    context_pack: Path,
    function_card: Path,
    style_profile: Path,
    voice_sheet: Path,
    output: Path,
    prompt_output: Path,
) -> str:
    return f"""# Scene Outline Prompt

schema_version: {SCHEMA_VERSION}
generated_at: {now_iso()}
project: {project_name(project)}
branch: {args.branch}
chapter: {chapter_label(args.chapter)}
scene_outline_output: {rel(output, project)}
prompt_output: {rel(prompt_output, project)}
context_pack: {rel(context_pack, project)} ({artifact_status(context_pack)})
chapter_function_card: {rel(function_card, project)} ({artifact_status(function_card)})
style_profile: {rel(style_profile, project)} ({artifact_status(style_profile)})
character_voice_sheet: {rel(voice_sheet, project)} ({artifact_status(voice_sheet)})

## Task

Fill `{rel(output, project)}` as a scene-level outline for the chapter. Convert the chapter function card into writable scenes.

## Required Reading

1. Read the context pack.
2. Read the chapter function card.
3. Read style and voice artifacts if present.
4. Do not read `raw_text/full_text.txt`.

## Rules

- Do not write prose.
- Do not invent major plot changes.
- Put major changes under `requires_user_decision`.
- Each scene should state function, conflict, turn, revealed/hidden information, state changes, style notes, voice notes, and exit hook.
- Keep the outline branch-local.

## Context Preview

```text
{read_head(context_pack, 1200)}
```
"""


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a v0.8 scene outline skeleton.")
    parser.add_argument("--project", "--project-root", dest="project", required=True, type=Path)
    parser.add_argument("--branch", default="main")
    parser.add_argument("--chapter", required=True)
    parser.add_argument("--title", default="")
    parser.add_argument("--context-pack", type=Path)
    parser.add_argument("--function-card", type=Path)
    parser.add_argument("--style-profile", type=Path)
    parser.add_argument("--voice-sheet", type=Path)
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
        context_pack = resolve_project_relative(project, args.context_pack) if args.context_pack else default_context_pack(project)
        function_card = (
            resolve_project_relative(project, args.function_card)
            if args.function_card
            else default_function_card(project, args.branch, args.chapter, label)
        )
        style_profile = (
            resolve_project_relative(project, args.style_profile)
            if args.style_profile
            else default_style_profile(project, args.branch)
        )
        voice_sheet = (
            resolve_project_relative(project, args.voice_sheet)
            if args.voice_sheet
            else default_voice_sheet(project, args.branch)
        )
        output = resolve_project_relative(project, args.output) if args.output else default_scene_outline(project, args.branch, label)
        prompt_output = (
            resolve_project_relative(project, args.prompt_output)
            if args.prompt_output
            else project / "branches" / args.branch / "outlines" / f"{label}_scene_outline_prompt.md"
        )
        assert context_pack is not None
        assert function_card is not None
        assert style_profile is not None
        assert voice_sheet is not None
        assert output is not None
        assert prompt_output is not None
        write_text_if_allowed(
            output,
            render_outline(args, project, context_pack, function_card, style_profile, voice_sheet, output),
            args.force,
        )
        if args.prompt:
            write_text_if_allowed(
                prompt_output,
                render_prompt(args, project, context_pack, function_card, style_profile, voice_sheet, output, prompt_output),
                args.force,
            )
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"Wrote scene outline: {output}")
    if args.prompt:
        print(f"Wrote scene outline prompt: {prompt_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
