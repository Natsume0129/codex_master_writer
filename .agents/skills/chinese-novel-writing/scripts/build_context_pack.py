#!/usr/bin/env python3
"""Build a task-specific context pack skeleton without reading full raw text."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path


MAX_SNIPPET_CHARS = 4000


def yaml_quote(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    return f'"{escaped}"'


def read_limited(path: Path, limit: int = MAX_SNIPPET_CHARS) -> str:
    if not path.exists() or not path.is_file():
        return ""
    text = path.read_text(encoding="utf-8", errors="replace")
    if len(text) <= limit:
        return text.strip()
    return text[:limit].rstrip() + "\n...[truncated for context pack budget]"


def latest_files(directory: Path, limit: int = 3) -> list[Path]:
    if not directory.exists():
        return []
    files = [path for path in directory.iterdir() if path.is_file() and not path.name.startswith(".")]
    return sorted(files, key=lambda item: item.name)[-limit:]


def collect_context(project: Path, branch: str) -> tuple[dict[str, str | list[str]], list[str]]:
    branch_dir = project / "branches" / branch
    missing: list[str] = []

    required_paths = {
        "project_config": project / "project_config.yaml",
        "branch_config": branch_dir / "branch_config.yaml",
        "style_guide": project / "shared" / "style_guide.md",
        "genre_strategy": project / "shared" / "genre_strategy.md",
        "canon_bible": project / "canon" / "canon_bible.md",
        "world_bible": project / "canon" / "world_bible.md",
        "characters": project / "canon" / "characters.yaml",
        "relationships": project / "canon" / "relationships.yaml",
        "timeline": branch_dir / "timeline.yaml",
        "foreshadowing": branch_dir / "foreshadowing.yaml",
        "outline": branch_dir / "outline.md",
        "hard_constraints": project / "shared" / "hard_constraints.md",
        "open_questions": branch_dir / "open_questions.md",
    }

    context: dict[str, str | list[str]] = {}
    for key, path in required_paths.items():
        if path.exists():
            context[key] = read_limited(path)
        else:
            context[key] = ""
            missing.append(str(path.relative_to(project)))

    summaries = []
    for path in latest_files(branch_dir / "chapter_summaries", 3):
        summaries.append(f"## {path.name}\n{read_limited(path, 2000)}")
    context["recent_chapter_summaries"] = summaries
    if not summaries:
        missing.append(str((branch_dir / "chapter_summaries").relative_to(project)))

    return context, missing


def render_yaml(
    task: str,
    branch: str,
    chapter: str,
    user_request: str,
    output_mode: str,
    context: dict[str, str | list[str]],
    missing: list[str],
) -> str:
    lines = [
        "context_pack:",
        "  generated_by: \"chinese-novel-writing/scripts/build_context_pack.py\"",
        f"  generated_at: {yaml_quote(datetime.now(timezone.utc).isoformat(timespec='seconds'))}",
        "  task:",
        f"    type: {yaml_quote(task)}",
        f"    user_request: {yaml_quote(user_request)}",
        f"    output_mode: {yaml_quote(output_mode)}",
        f"    branch: {yaml_quote(branch)}",
        f"    chapter: {yaml_quote(chapter)}",
        "  project_snapshot:",
        f"    project_config: {yaml_quote(str(context.get('project_config', '')))}",
        f"    genre_strategy_summary: {yaml_quote(str(context.get('genre_strategy', '')))}",
        f"    style_guide_summary: {yaml_quote(str(context.get('style_guide', '')))}",
        "  current_arc:",
        f"    current_outline: {yaml_quote(str(context.get('outline', '')))}",
        '    current_volume_summary: ""',
        '    current_chapter_goal: ""',
        "  recent_context:",
        "    previous_chapter_summaries:",
    ]
    summaries = context.get("recent_chapter_summaries", [])
    if isinstance(summaries, list) and summaries:
        for summary in summaries:
            lines.append(f"      - {yaml_quote(summary)}")
    else:
        lines.append("      []")
    lines.extend(
        [
            '    previous_chapter_ending_excerpt: ""',
            "  relevant_entities:",
            f"    characters: {yaml_quote(str(context.get('characters', '')))}",
            f"    relationships: {yaml_quote(str(context.get('relationships', '')))}",
            '    locations: ""',
            '    organizations: ""',
            '    items: ""',
            "  plot_threads:",
            f"    main_plot: {yaml_quote(str(context.get('canon_bible', '')))}",
            "    side_plots: []",
            '    antagonist_plan: ""',
            "  foreshadowing_and_questions:",
            f"    open_foreshadowing: {yaml_quote(str(context.get('foreshadowing', '')))}",
            "    payoff_candidates: []",
            f"    open_questions: {yaml_quote(str(context.get('open_questions', '')))}",
            "  timeline_constraints:",
            '    current_story_time: ""',
            f"    recent_events: {yaml_quote(str(context.get('timeline', '')))}",
            "    forbidden_time_conflicts: []",
            "  hard_constraints:",
            f"    must_not_change: {yaml_quote(str(context.get('hard_constraints', '')))}",
            "    must_not_reveal_yet: []",
            "    branch_boundaries:",
            f"      - {yaml_quote('Only use branch ' + branch + '; do not mix unrelated branch state.')}",
            "  missing_sections:",
        ]
    )
    if missing:
        for item in missing:
            lines.append(f"    - {yaml_quote(item)}")
    else:
        lines.append("    []")
    return "\n".join(lines) + "\n"


def render_markdown(
    task: str,
    branch: str,
    chapter: str,
    user_request: str,
    output_mode: str,
    context: dict[str, str | list[str]],
    missing: list[str],
) -> str:
    summaries = context.get("recent_chapter_summaries", [])
    summary_text = "\n\n".join(summaries) if isinstance(summaries, list) else ""
    missing_text = "\n".join(f"- {item}" for item in missing) if missing else "- 无"
    return f"""# Context Pack

Generated at: {datetime.now(timezone.utc).isoformat(timespec="seconds")}

## Task

- type: {task}
- user_request: {user_request}
- output_mode: {output_mode}
- branch: {branch}
- chapter: {chapter}

## Project Snapshot

### Project Config

```yaml
{context.get("project_config", "")}
```

### Genre Strategy

{context.get("genre_strategy", "")}

### Style Guide

{context.get("style_guide", "")}

## Current Arc

### Outline

{context.get("outline", "")}

### Current Chapter Goal

- 待 Codex 根据任务补全。

## Recent Context

{summary_text or "- 暂无最近章节摘要。"}

## Relevant Entities

### Characters

```yaml
{context.get("characters", "")}
```

### Relationships

```yaml
{context.get("relationships", "")}
```

## Foreshadowing and Open Questions

```yaml
{context.get("foreshadowing", "")}
```

{context.get("open_questions", "")}

## Timeline Constraints

```yaml
{context.get("timeline", "")}
```

## Hard Constraints

{context.get("hard_constraints", "")}

## Branch Boundaries

- Only use branch `{branch}` unless the user explicitly asks for branch comparison.
- Do not read or merge unrelated alternate branch state.
- Do not read `raw_text/full_text.txt` as part of this context pack.

## Missing Sections

{missing_text}
"""


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a context pack skeleton for the current task."
    )
    parser.add_argument("--project", required=True, type=Path, help="Novel project root.")
    parser.add_argument("--branch", default="main", help="Active branch name.")
    parser.add_argument("--task", required=True, help="Task type, e.g. continue_story.")
    parser.add_argument("--chapter", default="", help="Target chapter number or id.")
    parser.add_argument("--user-request", default="", help="Original user request.")
    parser.add_argument("--output-mode", default="draft_with_notes", help="Output mode.")
    parser.add_argument(
        "--output",
        type=Path,
        help="Output file. Defaults to context_packs/latest_context_pack.md.",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite existing output.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    project = args.project.resolve()
    if not project.exists():
        print(f"error: project not found: {project}", file=sys.stderr)
        return 1
    branch_dir = project / "branches" / args.branch
    if not branch_dir.exists():
        print(f"error: branch not found: {branch_dir}", file=sys.stderr)
        return 1

    output = args.output.resolve() if args.output else project / "context_packs" / "latest_context_pack.md"
    if output.exists() and not args.force:
        print(f"error: output exists: {output}. Use --force to overwrite.", file=sys.stderr)
        return 1

    context, missing = collect_context(project, args.branch)
    if output.suffix.lower() in {".yaml", ".yml"}:
        content = render_yaml(
            args.task, args.branch, args.chapter, args.user_request, args.output_mode, context, missing
        )
    else:
        content = render_markdown(
            args.task, args.branch, args.chapter, args.user_request, args.output_mode, context, missing
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(content, encoding="utf-8")
    print(f"Wrote context pack: {output}")
    if missing:
        print(f"Missing sections: {len(missing)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

