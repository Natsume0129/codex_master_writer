#!/usr/bin/env python3
"""Query a v0.7 retrieval index with deterministic local scoring."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from _novel_utils import yaml_quote
from _retrieval_utils import (
    SCHEMA_VERSION,
    load_index,
    query_entries,
    resolve_project_relative,
    selector_lines,
    split_terms,
    timestamped_report_header,
    write_text_if_allowed,
)


def parse_csvish(values: list[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        for item in str(value).replace(",", " ").split():
            if item.strip():
                result.append(item.strip())
    return list(dict.fromkeys(result))


def filters_from_args(args: argparse.Namespace) -> dict[str, list[str]]:
    return {
        "characters": parse_csvish(args.characters),
        "locations": parse_csvish(args.locations),
        "items": parse_csvish(args.items),
        "organizations": parse_csvish(args.organizations),
        "terms": parse_csvish(args.terms),
    }


def candidate_table(results: list[dict[str, object]]) -> str:
    if not results:
        return "- None"
    lines = [
        "| entry_id | score | source_file | source_type | branch | chapter | matched_terms | status | confidence | reason |",
        "| --- | ---: | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for result in results:
        entry = result["entry"]
        matched = ", ".join(str(item) for item in result.get("matched_terms", []))
        reason = str(result.get("reason", "")).replace("|", "\\|")
        lines.append(
            "| `{entry_id}` | {score} | `{source_file}` | `{source_type}` | `{branch}` | `{chapter}` | {matched} | `{status}` | `{confidence}` | {reason} |".format(
                entry_id=entry.get("entry_id", ""),
                score=result.get("score", 0),
                source_file=entry.get("source_file", ""),
                source_type=entry.get("source_type", ""),
                branch=entry.get("branch", ""),
                chapter=entry.get("chapter", ""),
                matched=matched,
                status=entry.get("status", ""),
                confidence=entry.get("confidence", ""),
                reason=reason,
            )
        )
    return "\n".join(lines)


def omitted_text(omitted: list[dict[str, object]], limit: int = 30) -> str:
    if not omitted:
        return "- None"
    lines = [
        f"- `{entry.get('entry_id')}` | `{entry.get('source_type')}` | `{entry.get('source_file')}`"
        for entry in omitted[:limit]
    ]
    if len(omitted) > limit:
        lines.append(f"- ... {len(omitted) - limit} more omitted candidates")
    return "\n".join(lines)


def render_markdown(
    args: argparse.Namespace,
    index_path: Path,
    results: list[dict[str, object]],
    omitted: list[dict[str, object]],
    warnings: list[str],
) -> str:
    filters = filters_from_args(args)
    filter_lines = [
        f"- branch: `{args.branch}`",
        f"- chapter: `{args.chapter}`",
        f"- source_types: `{', '.join(args.source_types) if args.source_types else 'all'}`",
    ]
    filter_lines.extend(
        f"- {key}: `{', '.join(value) if value else 'any'}`" for key, value in filters.items()
    )
    warning_text = "\n".join(f"- {warning}" for warning in warnings) or "- None"
    selectors = "\n".join(selector_lines(results)) or "- None"
    return f"""{timestamped_report_header("retrieval_query_report", query=args.query, branch=args.branch, chapter=args.chapter, index_file=str(index_path), top_k=args.top_k)}

# Retrieval Query Report

## Query

`{args.query}`

## Filters

{chr(10).join(filter_lines)}

## Scoring Rules

- Exact lowercase substring matches on query terms.
- Entity, chapter, and branch matches add deterministic weight.
- Source type, status, and confidence add deterministic weight.
- No embeddings, semantic search, external API, or raw text reading.

## Selected Candidates

{candidate_table(results)}

## Omitted Candidates

{omitted_text(omitted)}

## Missing Index Warnings

{warning_text}

## Suggested Context Selectors

{selectors}

## Source Trace

- Index file: `{index_path}`
- Query terms: `{', '.join(split_terms(args.query))}`

## Next Action

Use the selected source files as narrow selectors for `build-context-pack`; verify facts in source files before treating them as canon.
"""


def render_yaml(
    args: argparse.Namespace,
    index_path: Path,
    results: list[dict[str, object]],
    omitted: list[dict[str, object]],
    warnings: list[str],
) -> str:
    lines = [
        f"schema_version: {yaml_quote(SCHEMA_VERSION)}",
        'report_type: "retrieval_query_report"',
        f"query: {yaml_quote(args.query)}",
        f"branch: {yaml_quote(args.branch)}",
        f"chapter: {yaml_quote(args.chapter)}",
        f"index_file: {yaml_quote(str(index_path))}",
        f"top_k: {args.top_k}",
        "selected_candidates:",
    ]
    if results:
        for result in results:
            entry = result["entry"]
            lines.extend(
                [
                    f"  - entry_id: {yaml_quote(entry.get('entry_id', ''))}",
                    f"    score: {result.get('score', 0)}",
                    f"    source_file: {yaml_quote(entry.get('source_file', ''))}",
                    f"    source_type: {yaml_quote(entry.get('source_type', ''))}",
                    f"    branch: {yaml_quote(entry.get('branch', ''))}",
                    f"    chapter: {yaml_quote(entry.get('chapter', ''))}",
                    "    matched_terms:",
                ]
            )
            matched = result.get("matched_terms", [])
            if matched:
                lines.extend(f"      - {yaml_quote(item)}" for item in matched)
            else:
                lines.append("      []")
            lines.extend(
                [
                    f"    status: {yaml_quote(entry.get('status', ''))}",
                    f"    confidence: {yaml_quote(entry.get('confidence', ''))}",
                    f"    reason: {yaml_quote(result.get('reason', ''))}",
                ]
            )
    else:
        lines.append("  []")
    lines.append("omitted_count: " + str(len(omitted)))
    lines.append("warnings:")
    if warnings:
        lines.extend(f"  - {yaml_quote(warning)}" for warning in warnings)
    else:
        lines.append("  []")
    return "\n".join(lines) + "\n"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Query a v0.7 retrieval index.")
    parser.add_argument("--project", "--project-root", dest="project", required=True, type=Path)
    parser.add_argument("--index", type=Path)
    parser.add_argument("--query", default="")
    parser.add_argument("--branch", default="")
    parser.add_argument("--chapter", default="")
    parser.add_argument("--characters", nargs="*", default=[])
    parser.add_argument("--locations", nargs="*", default=[])
    parser.add_argument("--items", nargs="*", default=[])
    parser.add_argument("--organizations", nargs="*", default=[])
    parser.add_argument("--terms", nargs="*", default=[])
    parser.add_argument("--source-types", nargs="*", default=[])
    parser.add_argument("--top-k", type=int, default=20)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--format", choices=("markdown", "yaml"), default="markdown")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    project = args.project.resolve()
    if not project.exists():
        print(f"error: project not found: {project}", file=sys.stderr)
        return 1
    index_path = (
        resolve_project_relative(project, args.index)
        if args.index
        else project / "indexes" / "retrieval_index.jsonl"
    )
    output = (
        resolve_project_relative(project, args.output)
        if args.output
        else project / "indexes" / "retrieval_query_report.md"
    )
    assert index_path is not None
    assert output is not None
    try:
        entries = load_index(index_path)
        results, omitted = query_entries(
            entries,
            query=args.query,
            branch=args.branch,
            chapter=args.chapter,
            filters=filters_from_args(args),
            source_types=args.source_types,
            top_k=args.top_k,
        )
        warnings = [] if entries else ["retrieval index is empty"]
        content = (
            render_yaml(args, index_path, results, omitted, warnings)
            if args.format == "yaml"
            else render_markdown(args, index_path, results, omitted, warnings)
        )
        write_text_if_allowed(output, content, args.force)
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        print("suggestion: run build-retrieval-index", file=sys.stderr)
        return 1
    print(f"Wrote retrieval query report: {output}")
    if not results:
        print("Warnings: no matching candidates")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
