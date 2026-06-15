#!/usr/bin/env python3
"""Create a v0.8 style profile skeleton and optional fill prompt."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from _novel_utils import now_iso, yaml_quote
from _style_voice_utils import (
    SCHEMA_VERSION,
    artifact_status,
    default_context_pack,
    default_style_profile,
    ensure_branch,
    limited_source_note,
    missing_paths,
    project_name,
    read_head,
    rel,
    resolve_project_relative,
    source_scope,
    write_text_if_allowed,
    yaml_list,
)


def render_profile(args: argparse.Namespace, project: Path, context_pack: Path, source: Path | None, output: Path) -> str:
    missing = missing_paths(project, [("context_pack", context_pack)])
    if source and not source.exists():
        missing.append("source")
    lines = [
        f"schema_version: {yaml_quote(SCHEMA_VERSION)}",
        'artifact_type: "style_profile"',
        f"project: {yaml_quote(project_name(project))}",
        f"branch: {yaml_quote(args.branch)}",
        f"profile_id: {yaml_quote(args.profile_id or f'{args.branch}_style_profile')}",
        f"title: {yaml_quote(args.title)}",
        f"genre: {yaml_quote(args.genre)}",
        'subgenre: ""',
    ]
    yaml_list(lines, "source_scope", source_scope(project, args.branch, context_pack, source))
    lines.extend(
        [
            f"created_at: {yaml_quote(now_iso())}",
            'updated_at: ""',
            'narrative_distance: ""',
            'narrator_voice: ""',
            "sentence_rhythm:",
            '  summary: ""',
            '  short_sentence_use: ""',
            '  long_sentence_use: ""',
            "  variation_rules: []",
            'paragraph_density: ""',
            "imagery_style:",
            "  sensory_channels: []",
            '  metaphor_policy: ""',
            '  concrete_detail_policy: ""',
            "emotion_expression:",
            '  directness: ""',
            "  preferred_methods: []",
            "  avoid_methods: []",
            "action_description:",
            '  granularity: ""',
            '  body_language_policy: ""',
            'dialogue_ratio: ""',
            'interiority_level: ""',
            'exposition_style: ""',
            "pacing_profile:",
            '  default_pace: ""',
            "  acceleration_methods: []",
            "  slowdown_methods: []",
            "tension_style:",
            "  conflict_types: []",
            "  hook_methods: []",
            "genre_expectations: []",
            "allowed_moves: []",
            "avoid_moves: []",
            "anti_ai_flavor_rules: []",
            "style_conflicts: []",
            "requires_user_decision: []",
        ]
    )
    yaml_list(lines, "source", [rel(context_pack, project)])
    lines.extend(
        [
            'status: "draft"',
            'confidence: "unknown"',
        ]
    )
    yaml_list(lines, "missing_sections", missing)
    lines.extend(
        [
            f'notes: {yaml_quote("Writing control artifact only; not source of truth and not a canon override.")}',
            "",
        ]
    )
    return "\n".join(lines)


def render_prompt(args: argparse.Namespace, project: Path, context_pack: Path, source: Path | None, output: Path, prompt_output: Path) -> str:
    source_excerpt = ""
    if source and source.exists() and source.stat().st_size <= 20_000:
        source_excerpt = read_head(source, 2000)
    return f"""# Style Profile Prompt

schema_version: {SCHEMA_VERSION}
generated_at: {now_iso()}
project: {project_name(project)}
branch: {args.branch}
style_profile_output: {rel(output, project)}
prompt_output: {rel(prompt_output, project)}
context_pack: {rel(context_pack, project)}
context_pack_status: {artifact_status(context_pack)}
source_note: {limited_source_note(project, source)}

## Task

Fill the style profile at `{rel(output, project)}` from the context pack and selected source references.

## Rules

1. Do not write prose chapters.
2. Do not imitate a living or real-world author.
3. Do not copy long source passages into the profile.
4. Do not read `raw_text/full_text.txt`.
5. Do not override canon, outline, branch artifacts, or user instructions.
6. If style conflicts with canon or outline, record the conflict under `style_conflicts`.
7. Mark facts with `source`, `status`, and `confidence`.
8. Put major style direction choices under `requires_user_decision`.

## Source Excerpt Policy

The excerpt below is optional and bounded. Use it only as a local signal, not as text to copy.

```text
{source_excerpt}
```
"""


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a v0.8 style profile skeleton.")
    parser.add_argument("--project", "--project-root", dest="project", required=True, type=Path)
    parser.add_argument("--branch", default="main")
    parser.add_argument("--genre", default="")
    parser.add_argument("--title", default="")
    parser.add_argument("--profile-id", default="")
    parser.add_argument("--source", type=Path)
    parser.add_argument("--context-pack", type=Path)
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
        context_pack = resolve_project_relative(project, args.context_pack) if args.context_pack else default_context_pack(project)
        source = resolve_project_relative(project, args.source) if args.source else None
        output = resolve_project_relative(project, args.output) if args.output else default_style_profile(project, args.branch)
        prompt_output = (
            resolve_project_relative(project, args.prompt_output)
            if args.prompt_output
            else project / "branches" / args.branch / "style" / "style_profile_prompt.md"
        )
        assert context_pack is not None
        assert output is not None
        assert prompt_output is not None
        write_text_if_allowed(output, render_profile(args, project, context_pack, source, output), args.force)
        if args.prompt:
            write_text_if_allowed(
                prompt_output,
                render_prompt(args, project, context_pack, source, output, prompt_output),
                args.force,
            )
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"Wrote style profile: {output}")
    if args.prompt:
        print(f"Wrote style profile prompt: {prompt_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
