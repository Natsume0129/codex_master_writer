#!/usr/bin/env python3
"""Build a task-specific context pack without reading full raw text."""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


HEAD_LIMIT = 3000


def yaml_quote(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    return f'"{escaped}"'


def read_head(path: Path, limit: int = HEAD_LIMIT) -> str:
    if not path.exists() or not path.is_file():
        return ""
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        data = handle.read(limit + 1)
    if len(data) > limit:
        return data[:limit].rstrip() + "\n...[truncated]"
    return data.strip()


def read_tail(path: Path, chars: int) -> str:
    if chars <= 0 or not path.exists() or not path.is_file():
        return ""
    size = path.stat().st_size
    with path.open("rb") as handle:
        handle.seek(max(0, size - (chars * 4 + 256)))
        data = handle.read()
    text = data.decode("utf-8", errors="replace")
    return text[-chars:].strip()


def latest_files(directory: Path, limit: int) -> list[Path]:
    if limit <= 0 or not directory.exists():
        return []
    files = [path for path in directory.iterdir() if path.is_file() and not path.name.startswith(".")]
    return sorted(files, key=lambda item: item.name)[-limit:]


def chapter_number(chapter: str) -> int | None:
    match = re.search(r"(\d+)", str(chapter))
    return int(match.group(1)) if match else None


def chapter_candidates(number: int) -> list[str]:
    return [
        f"chapter_{number:03d}",
        f"chapter_{number:04d}",
        f"{number:03d}",
        f"{number:04d}",
    ]


def find_previous_ending(project: Path, branch: str, chapter: str, chars: int) -> tuple[str, str]:
    number = chapter_number(chapter)
    if number is None or number <= 1:
        return "", ""
    previous = number - 1
    names = chapter_candidates(previous)
    search_dirs = [
        project / "branches" / branch / "drafts",
        project / "raw_text" / "chapters",
    ]
    for directory in search_dirs:
        if not directory.exists():
            continue
        for path in sorted(directory.iterdir()):
            if path.is_file() and any(name in path.stem for name in names):
                return read_tail(path, chars), str(path.relative_to(project))
    return "", ""


def line_matches(path: Path, terms: list[str], context_lines: int = 2, limit: int = 8000) -> str:
    if not terms or not path.exists() or not path.is_file():
        return ""
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    selected: list[str] = []
    taken: set[int] = set()
    lowered_terms = [term.lower() for term in terms if term]
    for index, line in enumerate(lines):
        lower = line.lower()
        if any(term.lower() in lower for term in lowered_terms):
            start = max(0, index - context_lines)
            end = min(len(lines), index + context_lines + 1)
            for pos in range(start, end):
                if pos not in taken:
                    selected.append(lines[pos])
                    taken.add(pos)
    text = "\n".join(selected).strip()
    if len(text) > limit:
        return text[:limit].rstrip() + "\n...[truncated relevant matches]"
    return text


def collect_named_section(
    project: Path,
    label: str,
    selectors: list[str],
    index_rel: str,
    source_rel: str,
    missing: list[str],
) -> str:
    if not selectors:
        missing.append(f"{label}: no selectors provided")
        return ""
    index_path = project / index_rel
    source_path = project / source_rel
    index_matches = line_matches(index_path, selectors, context_lines=1, limit=3000)
    source_matches = line_matches(source_path, selectors, context_lines=3, limit=5000)
    parts = []
    if index_matches:
        parts.append(f"# index matches\n{index_matches}")
    elif not index_path.exists():
        missing.append(index_rel)
    if source_matches:
        parts.append(f"# source matches\n{source_matches}")
    else:
        missing.append(f"{label}: no matching source entries for {', '.join(selectors)}")
    return "\n\n".join(parts)


def collect_id_section(path: Path, ids: list[str], label: str, missing: list[str]) -> str:
    if not ids:
        missing.append(f"{label}: no ids provided")
        return ""
    text = line_matches(path, ids, context_lines=4, limit=6000)
    if not text:
        missing.append(f"{label}: ids not found in {path}")
    return text


def collect_context(args: argparse.Namespace) -> tuple[dict[str, str | list[str]], list[str]]:
    project = args.project.resolve()
    branch_dir = project / "branches" / args.branch
    missing: list[str] = []
    context: dict[str, str | list[str]] = {}

    for key, rel in {
        "project_config": "project_config.yaml",
        "branch_config": f"branches/{args.branch}/branch_config.yaml",
        "style_guide": "shared/style_guide.md",
        "genre_strategy": "shared/genre_strategy.md",
        "outline": f"branches/{args.branch}/outline.md",
        "hard_constraints": "shared/hard_constraints.md",
        "open_questions": f"branches/{args.branch}/open_questions.md",
    }.items():
        path = project / rel
        if path.exists():
            context[key] = read_head(path)
        else:
            context[key] = ""
            missing.append(rel)

    summaries = []
    for path in latest_files(branch_dir / "chapter_summaries", args.include_recent):
        summaries.append(f"## {path.name}\n{read_head(path, 2000)}")
    context["recent_chapter_summaries"] = summaries
    if args.include_recent and not summaries:
        missing.append(f"branches/{args.branch}/chapter_summaries")

    ending, ending_source = find_previous_ending(
        project, args.branch, args.chapter, args.previous_ending_chars
    )
    context["previous_chapter_ending_excerpt"] = ending
    context["previous_chapter_ending_source"] = ending_source
    if args.previous_ending_chars and not ending:
        missing.append("previous_chapter_ending_excerpt")

    context["characters"] = collect_named_section(
        project, "characters", args.characters or [], "indexes/character_index.yaml", "canon/characters.yaml", missing
    )
    context["locations"] = collect_named_section(
        project, "locations", args.locations or [], "indexes/location_index.yaml", "canon/locations.yaml", missing
    )
    context["items"] = collect_named_section(
        project, "items", args.items or [], "indexes/item_index.yaml", "canon/items.yaml", missing
    )
    context["organizations"] = collect_named_section(
        project, "organizations", args.organizations or [], "indexes/organization_index.yaml", "canon/organizations.yaml", missing
    )
    context["terms"] = collect_named_section(
        project, "terms", args.terms or [], "indexes/term_index.yaml", "canon/terms.yaml", missing
    )
    context["foreshadowing"] = collect_id_section(
        branch_dir / "foreshadowing.yaml", args.foreshadowing_ids or [], "foreshadowing", missing
    )
    context["timeline_events"] = collect_id_section(
        branch_dir / "timeline.yaml", args.event_ids or [], "timeline events", missing
    )
    return context, sorted(set(missing))


def render_yaml(args: argparse.Namespace, context: dict[str, str | list[str]], missing: list[str]) -> str:
    summaries = context.get("recent_chapter_summaries", [])
    lines = [
        "context_pack:",
        "  generated_by: \"chinese-novel-writing/scripts/build_context_pack.py\"",
        f"  generated_at: {yaml_quote(datetime.now(timezone.utc).isoformat(timespec='seconds'))}",
        "  task:",
        f"    type: {yaml_quote(args.task)}",
        f"    user_request: {yaml_quote(args.user_request)}",
        f"    output_mode: {yaml_quote(args.output_mode)}",
        f"    active_branch: {yaml_quote(args.branch)}",
        f"    chapter: {yaml_quote(args.chapter)}",
        "  branch_boundaries:",
        f"    active_branch: {yaml_quote(args.branch)}",
        '    rule: "Do not mix unrelated branch state or read raw_text/full_text.txt."',
        "  project_snapshot:",
        f"    project_config: {yaml_quote(str(context.get('project_config', '')))}",
        f"    genre_strategy_summary: {yaml_quote(str(context.get('genre_strategy', '')))}",
        f"    style_guide_summary: {yaml_quote(str(context.get('style_guide', '')))}",
        "  current_arc:",
        f"    outline: {yaml_quote(str(context.get('outline', '')))}",
        '    chapter_goal: ""',
        "  recent_context:",
        f"    previous_chapter_ending_source: {yaml_quote(str(context.get('previous_chapter_ending_source', '')))}",
        f"    previous_chapter_ending_excerpt: {yaml_quote(str(context.get('previous_chapter_ending_excerpt', '')))}",
        "    previous_chapter_summaries:",
    ]
    if isinstance(summaries, list) and summaries:
        for summary in summaries:
            lines.append(f"      - {yaml_quote(summary)}")
    else:
        lines.append("      []")
    lines.extend(
        [
            "  relevant_entities:",
            f"    characters: {yaml_quote(str(context.get('characters', '')))}",
            f"    locations: {yaml_quote(str(context.get('locations', '')))}",
            f"    items: {yaml_quote(str(context.get('items', '')))}",
            f"    organizations: {yaml_quote(str(context.get('organizations', '')))}",
            f"    terms: {yaml_quote(str(context.get('terms', '')))}",
            "  foreshadowing_and_timeline:",
            f"    foreshadowing: {yaml_quote(str(context.get('foreshadowing', '')))}",
            f"    timeline_events: {yaml_quote(str(context.get('timeline_events', '')))}",
            "  hard_constraints:",
            f"    must_not_change: {yaml_quote(str(context.get('hard_constraints', '')))}",
            "  missing_sections:",
        ]
    )
    if missing:
        for item in missing:
            lines.append(f"    - {yaml_quote(item)}")
    else:
        lines.append("    []")
    return "\n".join(lines) + "\n"


def render_markdown(args: argparse.Namespace, context: dict[str, str | list[str]], missing: list[str]) -> str:
    summaries = context.get("recent_chapter_summaries", [])
    summary_text = "\n\n".join(summaries) if isinstance(summaries, list) and summaries else "- 暂无最近章节摘要。"
    missing_text = "\n".join(f"- {item}" for item in missing) if missing else "- 无"
    return f"""# Context Pack

Generated at: {datetime.now(timezone.utc).isoformat(timespec="seconds")}

## Task

- type: {args.task}
- user_request: {args.user_request}
- output_mode: {args.output_mode}
- active_branch: {args.branch}
- chapter: {args.chapter}

## Branch Boundaries

- Active branch: `{args.branch}`
- Do not mix unrelated branch state.
- Do not read `raw_text/full_text.txt` as part of this context pack.

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

{context.get("outline", "")}

## Recent Context

### Previous Chapter Ending

Source: `{context.get("previous_chapter_ending_source", "")}`

```text
{context.get("previous_chapter_ending_excerpt", "")}
```

### Recent Chapter Summaries

{summary_text}

## Relevant Entities

### Characters

```yaml
{context.get("characters", "")}
```

### Locations

```yaml
{context.get("locations", "")}
```

### Items

```yaml
{context.get("items", "")}
```

### Organizations

```yaml
{context.get("organizations", "")}
```

### Terms

```yaml
{context.get("terms", "")}
```

## Foreshadowing and Timeline

### Foreshadowing

```yaml
{context.get("foreshadowing", "")}
```

### Timeline Events

```yaml
{context.get("timeline_events", "")}
```

## Hard Constraints

{context.get("hard_constraints", "")}

## Missing Sections

{missing_text}
"""


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a filtered context pack for the current task.")
    parser.add_argument("--project", required=True, type=Path, help="Novel project root.")
    parser.add_argument("--branch", default="main", help="Active branch name.")
    parser.add_argument("--task", required=True, help="Task type, e.g. continue_story.")
    parser.add_argument("--chapter", default="", help="Target chapter number or id.")
    parser.add_argument("--user-request", default="", help="Original user request.")
    parser.add_argument("--output-mode", default="draft_with_notes", help="Output mode.")
    parser.add_argument("--characters", nargs="*", default=[], help="Relevant character names or ids.")
    parser.add_argument("--locations", nargs="*", default=[], help="Relevant location names or ids.")
    parser.add_argument("--items", nargs="*", default=[], help="Relevant item names or ids.")
    parser.add_argument("--organizations", nargs="*", default=[], help="Relevant organization names or ids.")
    parser.add_argument("--terms", nargs="*", default=[], help="Relevant term names or ids.")
    parser.add_argument("--foreshadowing-ids", nargs="*", default=[], help="Foreshadowing ids to include.")
    parser.add_argument("--event-ids", nargs="*", default=[], help="Timeline event ids to include.")
    parser.add_argument("--include-recent", type=int, default=3, help="Recent chapter summaries to include.")
    parser.add_argument("--previous-ending-chars", type=int, default=1500, help="Characters from previous ending.")
    parser.add_argument("--format", choices=("markdown", "yaml"), default=None, help="Output format.")
    parser.add_argument("--output", type=Path, help="Output file. Defaults to context_packs/latest_context_pack.md.")
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

    context, missing = collect_context(args)
    output_format = args.format or ("yaml" if output.suffix.lower() in {".yaml", ".yml"} else "markdown")
    content = render_yaml(args, context, missing) if output_format == "yaml" else render_markdown(args, context, missing)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(content, encoding="utf-8")
    print(f"Wrote context pack: {output}")
    if missing:
        print(f"Missing sections: {len(missing)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

