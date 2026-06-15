#!/usr/bin/env python3
"""Build a deterministic local retrieval index from structured project artifacts."""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

from _novel_utils import safe_relative
from _retrieval_utils import (
    SCHEMA_VERSION,
    allowed_candidate_paths,
    build_entry,
    resolve_project_relative,
    timestamped_report_header,
    write_jsonl,
    write_text_if_allowed,
)


def source_type_filter(raw: list[str]) -> set[str]:
    return {item.strip() for item in raw if item.strip()}


def render_report(
    project: Path,
    output: Path,
    entries: list[dict[str, object]],
    warnings: list[str],
    source_types: set[str],
) -> str:
    counts = Counter(str(entry.get("source_type", "unknown")) for entry in entries)
    branch_counts = Counter(str(entry.get("branch", "main")) for entry in entries)
    source_type_text = "\n".join(f"- {key}: {value}" for key, value in sorted(counts.items())) or "- None"
    branch_text = "\n".join(f"- {key}: {value}" for key, value in sorted(branch_counts.items())) or "- None"
    entry_text = "\n".join(
        f"- `{entry.get('entry_id')}` | `{entry.get('source_type')}` | `{entry.get('source_file')}`"
        for entry in entries[:100]
    ) or "- None"
    warning_text = "\n".join(f"- {warning}" for warning in warnings) or "- None"
    filters = ", ".join(sorted(source_types)) if source_types else "all allowed structured source types"
    return f"""{timestamped_report_header("retrieval_index_report", index_file=safe_relative(output, project))}

# Retrieval Index Report

## Summary

- Schema version: `{SCHEMA_VERSION}`
- Index file: `{safe_relative(output, project)}`
- Entries: `{len(entries)}`
- Source type filter: `{filters}`
- Role: retrieval aid only; verify facts in the referenced source file before use.

## Source Type Counts

{source_type_text}

## Branch Counts

{branch_text}

## Indexed Entries

{entry_text}

## Warnings

{warning_text}

## Safety Notes

- This index is not a source of truth.
- It does not read `raw_text/full_text.txt`, `raw_text/*.txt`, or `imports/source_texts/*.txt`.
- It does not generate summaries from raw prose.
- It must not promote inferred facts to confirmed facts.
"""


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a v0.7 retrieval index from structured artifacts.")
    parser.add_argument("--project", "--project-root", dest="project", required=True, type=Path)
    parser.add_argument("--branch", default="main")
    parser.add_argument("--include-branches", action="store_true")
    parser.add_argument("--source-types", nargs="*", default=[])
    parser.add_argument("--output", type=Path)
    parser.add_argument("--report-output", type=Path)
    parser.add_argument("--force", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    project = args.project.resolve()
    if not project.exists():
        print(f"error: project not found: {project}", file=sys.stderr)
        return 1
    output = (
        resolve_project_relative(project, args.output)
        if args.output
        else project / "indexes" / "retrieval_index.jsonl"
    )
    report_output = (
        resolve_project_relative(project, args.report_output)
        if args.report_output
        else project / "indexes" / "retrieval_index.md"
    )
    assert output is not None
    assert report_output is not None

    filters = source_type_filter(args.source_types)
    warnings: list[str] = []
    entries: list[dict[str, object]] = []
    for path in allowed_candidate_paths(project, args.branch, args.include_branches):
        entry = build_entry(project, path)
        if filters and str(entry.get("source_type", "")) not in filters:
            continue
        entries.append(entry)

    if not entries:
        warnings.append("no structured artifacts found; generated an empty retrieval index")
    if not (project / "extracted").exists():
        warnings.append("extracted/ is missing")
    if not (project / "canon").exists():
        warnings.append("canon/ is missing")
    if not (project / "branches").exists():
        warnings.append("branches/ is missing")

    try:
        write_jsonl(output, entries, args.force)
        write_text_if_allowed(report_output, render_report(project, output, entries, warnings, filters), args.force)
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"Wrote retrieval index: {output}")
    print(f"Wrote retrieval index report: {report_output}")
    if warnings:
        print(f"Warnings: {len(warnings)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
