#!/usr/bin/env python3
"""Create a v0.8 character voice sheet skeleton and optional prompt."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from _novel_utils import now_iso, yaml_quote
from _style_voice_utils import (
    SCHEMA_VERSION,
    artifact_status,
    default_context_pack,
    default_voice_sheet,
    ensure_branch,
    limited_source_note,
    missing_paths,
    project_name,
    read_head,
    rel,
    resolve_project_relative,
    source_scope,
    split_csvish,
    write_text_if_allowed,
    yaml_list,
)


def render_character(character_id: str) -> list[str]:
    display = character_id or ""
    return [
        f"  - character_id: {yaml_quote(character_id)}",
        f"    display_name: {yaml_quote(display)}",
        '    role: ""',
        '    voice_summary: ""',
        "    diction: []",
        '    sentence_length: ""',
        '    formality: ""',
        '    emotional_leakage: ""',
        '    humor_style: ""',
        '    aggression_level: ""',
        '    restraint_level: ""',
        "    address_terms: []",
        "    taboo_words: []",
        "    recurring_phrases: []",
        "    information_boundary: []",
        "    relationship_specific_voice:",
        '      - target_character: ""',
        '        voice_shift: ""',
        "        address_terms: []",
        "        hidden_information: []",
        "    dialogue_dos: []",
        "    dialogue_donts: []",
        '    sample_policy: "no long verbatim samples"',
        "    source: []",
        '    status: "draft"',
        '    confidence: "unknown"',
    ]


def render_sheet(args: argparse.Namespace, project: Path, context_pack: Path, source: Path | None, output: Path) -> str:
    characters = split_csvish(args.characters) or [""]
    missing = missing_paths(project, [("context_pack", context_pack)])
    if source and not source.exists():
        missing.append("source")
    lines = [
        f"schema_version: {yaml_quote(SCHEMA_VERSION)}",
        'artifact_type: "character_voice_sheet"',
        f"project: {yaml_quote(project_name(project))}",
        f"branch: {yaml_quote(args.branch)}",
        f"created_at: {yaml_quote(now_iso())}",
        'updated_at: ""',
    ]
    yaml_list(lines, "source_scope", source_scope(project, args.branch, context_pack, source))
    yaml_list(lines, "source", [rel(context_pack, project)])
    lines.extend(
        [
            'status: "draft"',
            'confidence: "unknown"',
        ]
    )
    lines.append("characters:")
    for character in characters:
        lines.extend(render_character(character))
    lines.append("voice_conflicts: []")
    yaml_list(lines, "missing_sections", missing)
    lines.append(f'notes: {yaml_quote("Writing control artifact only; character bible remains source of truth.")}')
    lines.append("")
    return "\n".join(lines)


def render_prompt(args: argparse.Namespace, project: Path, context_pack: Path, source: Path | None, output: Path, prompt_output: Path) -> str:
    source_excerpt = ""
    if source and source.exists() and source.stat().st_size <= 20_000:
        source_excerpt = read_head(source, 2000)
    characters = ", ".join(split_csvish(args.characters)) or "characters named in the context pack"
    return f"""# Character Voice Sheet Prompt

schema_version: {SCHEMA_VERSION}
generated_at: {now_iso()}
project: {project_name(project)}
branch: {args.branch}
characters: {characters}
voice_sheet_output: {rel(output, project)}
prompt_output: {rel(prompt_output, project)}
context_pack: {rel(context_pack, project)}
context_pack_status: {artifact_status(context_pack)}
source_note: {limited_source_note(project, source)}

## Task

Fill the character voice sheet at `{rel(output, project)}` for: {characters}.

## Rules

1. Do not decide character fate, relationship changes, or hidden truths.
2. Do not override character bible facts.
3. If the voice sheet conflicts with character bible, record `voice_conflicts`.
4. Do not copy long dialogue samples.
5. Do not read `raw_text/full_text.txt`.
6. Mark voice claims with `source`, `status`, and `confidence`.
7. Respect each character's information boundary and relationship-specific voice.

## Source Excerpt Policy

The excerpt below is optional and bounded. Use it only as a local signal, not text to copy.

```text
{source_excerpt}
```
"""


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a v0.8 character voice sheet skeleton.")
    parser.add_argument("--project", "--project-root", dest="project", required=True, type=Path)
    parser.add_argument("--branch", default="main")
    parser.add_argument("--characters", nargs="*", default=[])
    parser.add_argument("--context-pack", type=Path)
    parser.add_argument("--source", type=Path)
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
        output = resolve_project_relative(project, args.output) if args.output else default_voice_sheet(project, args.branch)
        prompt_output = (
            resolve_project_relative(project, args.prompt_output)
            if args.prompt_output
            else project / "branches" / args.branch / "style" / "voice_sheet_prompt.md"
        )
        assert context_pack is not None
        assert output is not None
        assert prompt_output is not None
        write_text_if_allowed(output, render_sheet(args, project, context_pack, source, output), args.force)
        if args.prompt:
            write_text_if_allowed(
                prompt_output,
                render_prompt(args, project, context_pack, source, output, prompt_output),
                args.force,
            )
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"Wrote character voice sheet: {output}")
    if args.prompt:
        print(f"Wrote voice sheet prompt: {prompt_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
