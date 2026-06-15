#!/usr/bin/env python3
"""Build a task-specific context pack without reading full raw text."""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from _novel_utils import chapter_label_candidates
from _retrieval_utils import load_index, query_entries, resolve_project_relative, selector_lines


HEAD_LIMIT = 3000
SCHEMA_VERSION = "0.4"
AUTO_SELECTOR_CONFIG = (
    ("characters", "characters", "indexes/character_index.yaml"),
    ("locations", "locations", "indexes/location_index.yaml"),
    ("items", "items", "indexes/item_index.yaml"),
    ("organizations", "organizations", "indexes/organization_index.yaml"),
    ("terms", "terms", "indexes/term_index.yaml"),
    ("foreshadowing_ids", "foreshadowing", "indexes/foreshadowing_index.yaml"),
    ("event_ids", "timeline events", "indexes/event_index.yaml"),
)


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


def find_imported_chapter_card(project: Path, chapter: str) -> tuple[str, str]:
    for label in chapter_label_candidates(chapter):
        rel = f"extracted/chapter_cards/{label}.yaml"
        path = project / rel
        if path.exists():
            return read_head(path, 6000), rel
    return "", ""


def clean_index_value(value: object) -> str:
    text = str(value or "").strip().strip('"').strip("'")
    if text in {"[]", "{}"}:
        return ""
    return text


def useful_selector_term(value: object) -> bool:
    text = clean_index_value(value)
    if not text:
        return False
    if re.search(r"[\u4e00-\u9fff]", text):
        return True
    return len(text) >= 2


def parse_index_entries(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    entries: list[dict[str, object]] = []
    current: dict[str, object] | None = None
    list_key = ""
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("- "):
            rest = stripped[2:].strip()
            if rest.startswith("id:") or current is None:
                if current:
                    entries.append(current)
                current = {"aliases": []}
                list_key = ""
                if ":" in rest:
                    key, value = rest.split(":", 1)
                    current[key.strip()] = clean_index_value(value)
            elif list_key == "aliases":
                aliases = current.setdefault("aliases", [])
                if isinstance(aliases, list):
                    aliases.append(clean_index_value(rest))
            continue
        if current is None or ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        key = key.strip()
        value = value.strip()
        if key == "aliases":
            list_key = "aliases"
            aliases = current.setdefault("aliases", [])
            if isinstance(aliases, list) and value not in {"", "[]"}:
                aliases.extend(clean_index_value(item) for item in value.strip("[]").split(",") if clean_index_value(item))
            continue
        list_key = ""
        current[key] = clean_index_value(value)
    if current:
        entries.append(current)
    return entries


def entry_terms(entry: dict[str, object]) -> list[str]:
    aliases = entry.get("aliases", [])
    values: list[object] = [entry.get("id", ""), entry.get("name", "")]
    if isinstance(aliases, list):
        values.extend(aliases)
    return list(dict.fromkeys(clean_index_value(value) for value in values if useful_selector_term(value)))


def auto_selector_sources(
    project: Path, args: argparse.Namespace, context: dict[str, str | list[str]]
) -> tuple[str, list[str]]:
    parts: list[str] = []
    sources: list[str] = []
    card_text = str(context.get("chapter_function_card", "") or "")
    if card_text:
        parts.append(card_text)
        sources.append(str(context.get("chapter_function_card_source", "")))

    if args.selector_source in {"recent", "all"}:
        summaries = context.get("recent_chapter_summaries", [])
        if isinstance(summaries, list):
            parts.extend(str(item) for item in summaries)
            if summaries:
                sources.append(f"branches/{args.branch}/chapter_summaries")

    if args.selector_source in {"chapter_card", "all"}:
        imported_card, rel = find_imported_chapter_card(project, args.chapter)
        if imported_card:
            parts.append(imported_card)
            sources.append(rel)

    return "\n\n".join(parts), [source for source in sources if source]


def merge_selector_values(manual: list[str], selected: list[str], limit: int) -> list[str]:
    merged = list(dict.fromkeys(str(item) for item in manual if item))
    if limit <= 0:
        return merged
    for item in selected:
        if item in merged:
            continue
        if len(merged) >= max(limit, len(manual)):
            break
        merged.append(item)
    return merged


def run_auto_selectors(
    project: Path, args: argparse.Namespace, context: dict[str, str | list[str]]
) -> tuple[dict[str, list[str]], list[str], list[str]]:
    source_text, source_files = auto_selector_sources(project, args, context)
    lowered_source = source_text.lower()
    selected: dict[str, list[str]] = {}
    notes: list[str] = []
    if not lowered_source.strip():
        notes.append("auto_select: no selector source text found")

    for attr, label, index_rel in AUTO_SELECTOR_CONFIG:
        values: list[str] = []
        matches: list[str] = []
        entries = parse_index_entries(project / index_rel)
        for entry in entries:
            terms = entry_terms(entry)
            matched_term = next((term for term in terms if term.lower() in lowered_source), "")
            if not matched_term:
                continue
            selector = clean_index_value(entry.get("id") or entry.get("name") or matched_term)
            if selector and selector not in values:
                values.append(selector)
                matches.append(f"{selector} <= {matched_term}")
            if len(values) >= args.max_selectors:
                break
        selected[attr] = values
        manual = getattr(args, attr)
        setattr(args, attr, merge_selector_values(manual, values, args.max_selectors))
        if values:
            notes.append(f"auto_select {label}: {', '.join(values)}")
        elif entries:
            notes.append(f"auto_select {label}: no index match")
        else:
            notes.append(f"auto_select {label}: index empty or missing ({index_rel})")
        if matches:
            notes.extend(f"auto_select match {label}: {item}" for item in matches)
    return selected, source_files, notes


def write_selector_report(
    project: Path,
    args: argparse.Namespace,
    selected: dict[str, list[str]],
    source_files: list[str],
    notes: list[str],
) -> None:
    output = (
        args.selector_report_output.resolve()
        if args.selector_report_output
        else project / "context_packs" / "selector_report.md"
    )
    lines = [
        "# Context Selector Report",
        "",
        f"Schema version: {SCHEMA_VERSION}",
        "",
        f"- generated_at: `{datetime.now(timezone.utc).isoformat(timespec='seconds')}`",
        f"- selector_source: `{args.selector_source}`",
        f"- max_selectors: `{args.max_selectors}`",
        "",
        "## Source Files",
        "",
    ]
    if source_files:
        lines.extend(f"- `{source}`" for source in source_files)
    else:
        lines.append("- None")
    lines.extend(["", "## Selected", ""])
    for attr, label, _ in AUTO_SELECTOR_CONFIG:
        values = selected.get(attr, [])
        lines.append(f"### {label}")
        if values:
            lines.extend(f"- `{value}`" for value in values)
        else:
            lines.append("- None")
        lines.append("")
    lines.extend(["## Notes", ""])
    lines.extend(f"- {note}" for note in notes)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(f"Wrote selector report: {output}")


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

    if args.task == "rewrite_plot":
        for key, rel in {
            "original_plot_map": "canon/original_plot_map.md",
            "divergence_point": f"branches/{args.branch}/divergence_point.yaml",
            "rewrite_plot_node_map": f"branches/{args.branch}/rewrite/plot_node_map.yaml",
            "rewrite_divergence_analysis": f"branches/{args.branch}/rewrite/divergence_analysis.yaml",
            "rewrite_replacement_routes": f"branches/{args.branch}/rewrite/replacement_routes.yaml",
        }.items():
            path = project / rel
            if path.exists():
                context[key] = read_head(path, 6000)
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

    context["auto_selector_sources"] = []
    context["auto_selector_notes"] = []
    if args.auto_select:
        selected, source_files, auto_notes = run_auto_selectors(project, args, context)
        context["auto_selector_sources"] = source_files
        context["auto_selector_notes"] = auto_notes
        retrieval_notes.extend(auto_notes)
        if args.write_selector_report:
            write_selector_report(project, args, selected, source_files, auto_notes)

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
    collect_retrieval_trace(project, args, context, missing, retrieval_notes)
    return context, sorted(set(missing))


def collect_retrieval_trace(
    project: Path,
    args: argparse.Namespace,
    context: dict[str, str | list[str]],
    missing: list[str],
    retrieval_notes: list[str],
) -> None:
    context["retrieval_trace_candidates"] = []
    context["retrieval_trace_sources"] = []
    context["retrieval_trace_warnings"] = []
    context["retrieval_trace_omitted_count"] = "0"
    context["retrieval_trace_index"] = ""
    context["retrieval_trace_query"] = ""
    if not args.use_retrieval_index:
        return

    index_path = (
        resolve_project_relative(project, args.retrieval_index)
        if args.retrieval_index
        else project / "indexes" / "retrieval_index.jsonl"
    )
    assert index_path is not None
    query = args.retrieval_query or args.user_request or " ".join(
        value
        for value in [
            args.task,
            args.chapter,
            *args.characters,
            *args.locations,
            *args.items,
            *args.organizations,
            *args.terms,
        ]
        if value
    )
    context["retrieval_trace_index"] = str(index_path.relative_to(project)) if index_path.is_relative_to(project) else str(index_path)
    context["retrieval_trace_query"] = query
    if not index_path.exists():
        warning = f"retrieval index missing: {context['retrieval_trace_index']}; run build-retrieval-index"
        retrieval_notes.append(warning)
        context["retrieval_trace_warnings"] = [warning]
        missing.append("indexes/retrieval_index.jsonl")
        return
    filters = {
        "characters": args.characters,
        "locations": args.locations,
        "items": args.items,
        "organizations": args.organizations,
        "terms": args.terms,
    }
    try:
        entries = load_index(index_path)
        results, omitted = query_entries(
            entries,
            query=query,
            branch=args.branch,
            chapter=args.chapter,
            filters=filters,
            top_k=args.retrieval_top_k,
        )
    except Exception as exc:  # noqa: BLE001
        warning = f"retrieval index query failed: {exc}"
        retrieval_notes.append(warning)
        context["retrieval_trace_warnings"] = [warning]
        return

    candidates: list[str] = []
    for result in results:
        entry = result["entry"]
        candidates.append(
            " | ".join(
                [
                    f"entry_id={entry.get('entry_id', '')}",
                    f"score={result.get('score', 0)}",
                    f"source_file={entry.get('source_file', '')}",
                    f"source_type={entry.get('source_type', '')}",
                    f"branch={entry.get('branch', '')}",
                    f"chapter={entry.get('chapter', '')}",
                    f"matched_terms={', '.join(str(item) for item in result.get('matched_terms', []))}",
                    f"status={entry.get('status', '')}",
                    f"confidence={entry.get('confidence', '')}",
                    f"summary={entry.get('summary', '')}",
                ]
            )
        )
    sources = [line.removeprefix("- source_file: ") for line in selector_lines(results)]
    context["retrieval_trace_candidates"] = candidates
    context["retrieval_trace_sources"] = sources
    context["retrieval_trace_warnings"] = [] if results else ["retrieval query returned no candidates"]
    context["retrieval_trace_omitted_count"] = str(len(omitted))
    retrieval_notes.append(
        f"retrieval_index: selected {len(results)} candidates from {context['retrieval_trace_index']}"
    )


def render_list_yaml(lines: list[str], values: list[str], indent: str) -> None:
    if values:
        for value in values:
            lines.append(f"{indent}- {yaml_quote(value)}")
    else:
        lines.append(f"{indent}[]")


def render_yaml(args: argparse.Namespace, context: dict[str, str | list[str]], missing: list[str]) -> str:
    summaries = context.get("recent_chapter_summaries", [])
    retrieval_notes = context.get("retrieval_notes", [])
    retrieval_candidates = context.get("retrieval_trace_candidates", [])
    retrieval_sources = context.get("retrieval_trace_sources", [])
    retrieval_warnings = context.get("retrieval_trace_warnings", [])
    auto_selector_sources = context.get("auto_selector_sources", [])
    auto_selector_notes = context.get("auto_selector_notes", [])
    lines = [
        "context_pack:",
        f'  schema_version: "{SCHEMA_VERSION}"',
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
            "  rewrite_context:",
            f"    original_plot_map: {yaml_quote(context.get('original_plot_map', ''))}",
            f"    divergence_point: {yaml_quote(context.get('divergence_point', ''))}",
            f"    plot_node_map: {yaml_quote(context.get('rewrite_plot_node_map', ''))}",
            f"    divergence_analysis: {yaml_quote(context.get('rewrite_divergence_analysis', ''))}",
            f"    replacement_routes: {yaml_quote(context.get('rewrite_replacement_routes', ''))}",
            "  retrieval_trace:",
            f"    enabled: {'true' if args.use_retrieval_index else 'false'}",
            f"    index_file: {yaml_quote(context.get('retrieval_trace_index', ''))}",
            f"    query: {yaml_quote(context.get('retrieval_trace_query', ''))}",
            f"    omitted_count: {yaml_quote(context.get('retrieval_trace_omitted_count', '0'))}",
            "    selected_candidates:",
        ]
    )
    if isinstance(retrieval_candidates, list):
        render_list_yaml(lines, retrieval_candidates, "      ")
    else:
        lines.append("      []")
    lines.extend(
        [
            "    source_files:",
        ]
    )
    if isinstance(retrieval_sources, list):
        render_list_yaml(lines, retrieval_sources, "      ")
    else:
        lines.append("      []")
    lines.extend(
        [
            "    warnings:",
        ]
    )
    if isinstance(retrieval_warnings, list):
        render_list_yaml(lines, retrieval_warnings, "      ")
    else:
        lines.append("      []")
    lines.extend(
        [
            "  auto_selection:",
            f"    enabled: {'true' if args.auto_select else 'false'}",
            f"    selector_source: {yaml_quote(args.selector_source)}",
            f"    max_selectors: {args.max_selectors}",
            "    source_files:",
        ]
    )
    if isinstance(auto_selector_sources, list):
        render_list_yaml(lines, auto_selector_sources, "      ")
    else:
        lines.append("      []")
    lines.extend(
        [
            "    notes:",
        ]
    )
    if isinstance(auto_selector_notes, list):
        render_list_yaml(lines, auto_selector_notes, "      ")
    else:
        lines.append("      []")
    lines.extend(
        [
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
    retrieval_candidates = context.get("retrieval_trace_candidates", [])
    retrieval_sources = context.get("retrieval_trace_sources", [])
    retrieval_warnings = context.get("retrieval_trace_warnings", [])
    auto_selector_sources = context.get("auto_selector_sources", [])
    auto_selector_notes = context.get("auto_selector_notes", [])
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
    auto_sources_text = (
        "\n".join(f"- `{item}`" for item in auto_selector_sources)
        if isinstance(auto_selector_sources, list) and auto_selector_sources
        else "- None"
    )
    auto_notes_text = (
        "\n".join(f"- {item}" for item in auto_selector_notes)
        if isinstance(auto_selector_notes, list) and auto_selector_notes
        else "- None"
    )
    missing_text = "\n".join(f"- {item}" for item in missing) if missing else "- None"
    retrieval_candidate_text = (
        "\n".join(f"- {item}" for item in retrieval_candidates)
        if isinstance(retrieval_candidates, list) and retrieval_candidates
        else "- None"
    )
    retrieval_source_text = (
        "\n".join(f"- `{item}`" for item in retrieval_sources)
        if isinstance(retrieval_sources, list) and retrieval_sources
        else "- None"
    )
    retrieval_warning_text = (
        "\n".join(f"- {item}" for item in retrieval_warnings)
        if isinstance(retrieval_warnings, list) and retrieval_warnings
        else "- None"
    )
    return f"""# Context Pack

Generated at: {datetime.now(timezone.utc).isoformat(timespec="seconds")}

Schema version: {SCHEMA_VERSION}

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

## Rewrite Context

### Original Plot Map

{context.get("original_plot_map", "")}

### Divergence Point

```yaml
{context.get("divergence_point", "")}
```

### Plot Node Map

```yaml
{context.get("rewrite_plot_node_map", "")}
```

### Divergence Analysis

```yaml
{context.get("rewrite_divergence_analysis", "")}
```

### Replacement Routes

```yaml
{context.get("rewrite_replacement_routes", "")}
```

## Retrieval Trace

- enabled: {str(args.use_retrieval_index).lower()}
- index_file: `{context.get("retrieval_trace_index", "")}`
- query: `{context.get("retrieval_trace_query", "")}`
- omitted_count: `{context.get("retrieval_trace_omitted_count", "0")}`

### Selected Candidates

{retrieval_candidate_text}

### Source Files

{retrieval_source_text}

### Warnings

{retrieval_warning_text}

## Auto Selection

- enabled: {str(args.auto_select).lower()}
- selector_source: {args.selector_source}
- max_selectors: {args.max_selectors}

### Auto Selector Sources

{auto_sources_text}

### Auto Selector Notes

{auto_notes_text}

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
    parser.add_argument("--auto-select", action="store_true", help="Auto-select entity and timeline selectors from indexes.")
    parser.add_argument(
        "--selector-source",
        choices=("indexes", "chapter_card", "recent", "all"),
        default="all",
        help="Hint sources for auto-select. Index files are always the selector target.",
    )
    parser.add_argument("--max-selectors", type=int, default=20, help="Maximum selectors per category after manual selectors.")
    parser.add_argument("--write-selector-report", action="store_true", help="Write a selector report next to context packs.")
    parser.add_argument("--selector-report-output", type=Path, help="Optional selector report output path.")
    parser.add_argument("--use-retrieval-index", action="store_true", help="Use v0.7 retrieval index for candidate trace.")
    parser.add_argument("--retrieval-index", type=Path, help="Retrieval index path. Defaults to indexes/retrieval_index.jsonl.")
    parser.add_argument("--retrieval-query", default="", help="Query for deterministic retrieval trace.")
    parser.add_argument("--retrieval-top-k", type=int, default=20, help="Retrieval candidates to show in trace.")
    parser.add_argument("--context-budget-chars", type=int, default=60000, help="Budget used by optional audit.")
    parser.add_argument("--write-audit", action="store_true", help="Write a context audit report after building the pack.")
    parser.add_argument("--audit-output", type=Path, help="Optional context audit report path.")
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
    if args.write_audit:
        from audit_context_pack import audit_context, render_report

        audit_index = (
            resolve_project_relative(project, args.retrieval_index)
            if args.retrieval_index
            else project / "indexes" / "retrieval_index.jsonl"
        )
        audit_output = (
            resolve_project_relative(project, args.audit_output)
            if args.audit_output
            else output.parent / f"{output.stem}_audit.md"
        )
        assert audit_index is not None
        assert audit_output is not None
        audit_result = audit_context(
            project,
            output,
            args.branch,
            args.task,
            args.chapter,
            args.context_budget_chars,
            audit_index,
        )
        if audit_output.exists() and not args.force:
            print(f"error: audit output exists: {audit_output}. Use --force to overwrite.", file=sys.stderr)
            return 1
        audit_output.parent.mkdir(parents=True, exist_ok=True)
        audit_output.write_text(
            render_report(project, output, args.branch, args.task, args.chapter, audit_result),
            encoding="utf-8",
        )
        print(f"Wrote context audit report: {audit_output}")
    if missing:
        print(f"Missing sections: {len(missing)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
