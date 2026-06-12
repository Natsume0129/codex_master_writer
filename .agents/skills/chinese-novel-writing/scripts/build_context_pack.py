#!/usr/bin/env python3
"""Build a task-specific context pack without reading full raw text."""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


HEAD_LIMIT = 3000


def yaml_quote(value: object) -> str:
    text = "" if value is None else str(value)
    escaped = text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
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


def chapter_label(chapter: str) -> str:
    text = str(chapter or "").strip()
    if not text:
        return ""
    if text.startswith("chapter_"):
        return text
    number = chapter_number(text)
    if number is not None:
        return f"chapter_{number:03d}"
    return re.sub(r"[^A-Za-z0-9_-]+", "_", text).strip("_")


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


def extract_yaml_scalar(text: str, key: str) -> str:
    pattern = re.compile(rf"^\s*{re.escape(key)}\s*:\s*(.*?)\s*$", flags=re.MULTILINE)
    match = pattern.search(text)
    if not match:
        return ""
    value = match.group(1).strip()
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    return value


def find_chapter_function_card(
    project: Path, branch: str, chapter: str
) -> tuple[str, str, str, str]:
    label = chapter_label(chapter)
    if not label:
        return "", "", "", f"branches/{branch}/chapter_function_cards/<chapter>_function_card.yaml"
    rel = f"branches/{branch}/chapter_function_cards/{label}_function_card.yaml"
    path = project / rel
    if not path.exists():
        return "", "", "", rel
    text = read_head(path, 6000)
    return text, extract_yaml_scalar(text, "chapter_goal"), rel, ""


def line_matches(path: Path, terms: list[str], context_lines: int = 2, limit: int = 8000) -> str:
    if not terms or not path.exists() or not path.is_file():
        return ""
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    selected: list[str] = []
    taken: set[int] = set()
    lowered_terms = [term.lower() for term in terms if term]
    for index, line in enumerate(lines):
        lower = line.lower()
        if any(term in lower for term in lowered_terms):
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


def indentation(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def collect_yaml_block(lines: list[str], start: int) -> str:
    first = lines[start]
    first_indent = indentation(first)
    stripped = first.lstrip()
    block = [first]
    for line in lines[start + 1 :]:
        line_indent = indentation(line)
        line_stripped = line.lstrip()
        if line.strip():
            if stripped.startswith("- "):
                if line_indent <= first_indent and line_stripped.startswith("- "):
                    break
                if line_indent < first_indent:
                    break
            elif line_indent <= first_indent:
                break
        block.append(line)
    return "\n".join(block).rstrip()


def matching_yaml_blocks(path: Path, selectors: list[str], limit: int = 8000) -> str:
    if not selectors or not path.exists() or not path.is_file():
        return ""
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    lowered_selectors = [selector.lower() for selector in selectors if selector]
    blocks: list[str] = []
    seen: set[int] = set()
    for index, line in enumerate(lines):
        stripped = line.lstrip()
        if index in seen:
            continue
        is_list_object = stripped.startswith("- ")
        is_mapping_object = indentation(line) > 0 and stripped.endswith(":") and not is_list_object
        if not is_list_object and not is_mapping_object:
            continue
        block = collect_yaml_block(lines, index)
        lower_block = block.lower()
        if any(selector in lower_block for selector in lowered_selectors):
            blocks.append(block)
            for offset in range(len(block.splitlines())):
                seen.add(index + offset)
    text = "\n\n".join(blocks).strip()
    if len(text) > limit:
        return text[:limit].rstrip() + "\n...[truncated matching YAML blocks]"
    return text


def extract_selector_hints(text: str) -> list[str]:
    hints: list[str] = []
    scalar_keys = (
        "id",
        "key",
        "name",
        "character_id",
        "location_id",
        "item_id",
        "organization_id",
        "term_id",
    )
    for line in text.splitlines():
        stripped = line.strip()
        if ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        key = key.strip().lstrip("- ").strip()
        value = value.strip().strip("[]")
        if key in scalar_keys:
            cleaned = value.strip().strip('"').strip("'")
            if cleaned and len(cleaned) <= 80:
                hints.append(cleaned)
        elif key == "aliases":
            for raw in value.split(","):
                cleaned = raw.strip().strip('"').strip("'")
                if cleaned and len(cleaned) <= 80:
                    hints.append(cleaned)
    return hints


def collect_named_section(
    project: Path,
    label: str,
    selectors: list[str],
    index_rel: str,
    source_rel: str,
    missing: list[str],
    retrieval_notes: list[str],
) -> str:
    clean_selectors = [selector for selector in selectors if selector]
    if not clean_selectors:
        missing.append(f"{label}: no selectors provided")
        return ""

    index_path = project / index_rel
    source_path = project / source_rel
    index_matches = line_matches(index_path, clean_selectors, context_lines=2, limit=3000)
    expanded_selectors = list(dict.fromkeys(clean_selectors + extract_selector_hints(index_matches)))

    parts: list[str] = []
    if index_matches:
        parts.append(f"# index matches\n{index_matches}")
        retrieval_notes.append(f"{label}: index hit in {index_rel}")
    elif index_path.exists():
        retrieval_notes.append(f"{label}: no index hit in {index_rel}; used canon fallback")
    else:
        missing.append(index_rel)
        retrieval_notes.append(f"{label}: missing index {index_rel}; used canon fallback")

    source_blocks = matching_yaml_blocks(source_path, expanded_selectors, limit=7000)
    if source_blocks:
        parts.append(f"# source blocks\n{source_blocks}")
        retrieval_notes.append(f"{label}: extracted full matching blocks from {source_rel}")
    else:
        source_matches = line_matches(source_path, expanded_selectors, context_lines=3, limit=5000)
        if source_matches:
            parts.append(f"# source line matches\n{source_matches}")
            retrieval_notes.append(f"{label}: used source line-match fallback from {source_rel}")
        else:
            missing.append(f"{label}: no matching source entries for {', '.join(clean_selectors)}")
            retrieval_notes.append(f"{label}: no matching source entries found in {source_rel}")
    return "\n\n".join(parts)


def collect_id_section(path: Path, ids: list[str], label: str, missing: list[str]) -> str:
    if not ids:
        missing.append(f"{label}: no ids provided")
        return ""
    if not path.exists():
        missing.append(str(path))
        return ""
    text = line_matches(path, ids, context_lines=4, limit=6000)
    if not text:
        missing.append(f"{label}: ids not found in {path.name}")
    return text


def collect_context(args: argparse.Namespace) -> tuple[dict[str, str | list[str]], list[str]]:
    project = args.project.resolve()
    branch_dir = project / "branches" / args.branch
    missing: list[str] = []
    retrieval_notes: list[str] = []
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

    card_text, chapter_goal, card_source, card_missing = find_chapter_function_card(
        project, args.branch, args.chapter
    )
    context["chapter_function_card"] = card_text
    context["chapter_function_card_source"] = card_source
    context["chapter_goal"] = chapter_goal
    context["current_chapter_goal"] = chapter_goal
    if card_missing:
        missing.append(card_missing)
    else:
        retrieval_notes.append(f"chapter_function_card: loaded {card_source}")

    context["characters"] = collect_named_section(
        project,
        "characters",
        args.characters or [],
        "indexes/character_index.yaml",
        "canon/characters.yaml",
        missing,
        retrieval_notes,
    )
    context["locations"] = collect_named_section(
        project,
        "locations",
        args.locations or [],
        "indexes/location_index.yaml",
        "canon/locations.yaml",
        missing,
        retrieval_notes,
    )
    context["items"] = collect_named_section(
        project,
        "items",
        args.items or [],
        "indexes/item_index.yaml",
        "canon/items.yaml",
        missing,
        retrieval_notes,
    )
    context["organizations"] = collect_named_section(
        project,
        "organizations",
        args.organizations or [],
        "indexes/organization_index.yaml",
        "canon/organizations.yaml",
        missing,
        retrieval_notes,
    )
    context["terms"] = collect_named_section(
        project,
        "terms",
        args.terms or [],
        "indexes/term_index.yaml",
        "canon/terms.yaml",
        missing,
        retrieval_notes,
    )
    context["foreshadowing"] = collect_id_section(
        branch_dir / "foreshadowing.yaml",
        args.foreshadowing_ids or [],
        "foreshadowing",
        missing,
    )
    context["timeline_events"] = collect_id_section(
        branch_dir / "timeline.yaml", args.event_ids or [], "timeline events", missing
    )
    context["retrieval_notes"] = retrieval_notes
    return context, sorted(set(missing))


def render_list_yaml(lines: list[str], values: list[str], indent: str) -> None:
    if values:
        for value in values:
            lines.append(f"{indent}- {yaml_quote(value)}")
    else:
        lines.append(f"{indent}[]")


def render_yaml(args: argparse.Namespace, context: dict[str, str | list[str]], missing: list[str]) -> str:
    summaries = context.get("recent_chapter_summaries", [])
    retrieval_notes = context.get("retrieval_notes", [])
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
        f"    project_config: {yaml_quote(context.get('project_config', ''))}",
        f"    genre_strategy_summary: {yaml_quote(context.get('genre_strategy', ''))}",
        f"    style_guide_summary: {yaml_quote(context.get('style_guide', ''))}",
        "  current_arc:",
        f"    outline: {yaml_quote(context.get('outline', ''))}",
        f"    chapter_goal: {yaml_quote(context.get('chapter_goal', ''))}",
        f"    current_chapter_goal: {yaml_quote(context.get('current_chapter_goal', ''))}",
        f"    chapter_function_card_source: {yaml_quote(context.get('chapter_function_card_source', ''))}",
        f"    chapter_function_card: {yaml_quote(context.get('chapter_function_card', ''))}",
        "  recent_context:",
        f"    previous_chapter_ending_source: {yaml_quote(context.get('previous_chapter_ending_source', ''))}",
        f"    previous_chapter_ending_excerpt: {yaml_quote(context.get('previous_chapter_ending_excerpt', ''))}",
        "    previous_chapter_summaries:",
    ]
    if isinstance(summaries, list):
        render_list_yaml(lines, summaries, "      ")
    else:
        lines.append("      []")
    lines.extend(
        [
            "  relevant_entities:",
            f"    characters: {yaml_quote(context.get('characters', ''))}",
            f"    locations: {yaml_quote(context.get('locations', ''))}",
            f"    items: {yaml_quote(context.get('items', ''))}",
            f"    organizations: {yaml_quote(context.get('organizations', ''))}",
            f"    terms: {yaml_quote(context.get('terms', ''))}",
            "  foreshadowing_and_timeline:",
            f"    foreshadowing: {yaml_quote(context.get('foreshadowing', ''))}",
            f"    timeline_events: {yaml_quote(context.get('timeline_events', ''))}",
            f"    open_questions: {yaml_quote(context.get('open_questions', ''))}",
            "  hard_constraints:",
            f"    must_not_change: {yaml_quote(context.get('hard_constraints', ''))}",
            "  retrieval_notes:",
        ]
    )
    if isinstance(retrieval_notes, list):
        render_list_yaml(lines, retrieval_notes, "    ")
    else:
        lines.append("    []")
    lines.append("  missing_sections:")
    render_list_yaml(lines, missing, "    ")
    return "\n".join(lines) + "\n"


def render_markdown(args: argparse.Namespace, context: dict[str, str | list[str]], missing: list[str]) -> str:
    summaries = context.get("recent_chapter_summaries", [])
    retrieval_notes = context.get("retrieval_notes", [])
    summary_text = (
        "\n\n".join(summaries)
        if isinstance(summaries, list) and summaries
        else "- No recent chapter summaries."
    )
    retrieval_text = (
        "\n".join(f"- {item}" for item in retrieval_notes)
        if isinstance(retrieval_notes, list) and retrieval_notes
        else "- None"
    )
    missing_text = "\n".join(f"- {item}" for item in missing) if missing else "- None"
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

## Chapter Function Card

Source: `{context.get("chapter_function_card_source", "")}`

```yaml
{context.get("chapter_function_card", "")}
```

## Chapter Goal

{context.get("chapter_goal", "")}

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

### Open Questions

{context.get("open_questions", "")}

## Hard Constraints

{context.get("hard_constraints", "")}

## Retrieval Notes

{retrieval_text}

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
