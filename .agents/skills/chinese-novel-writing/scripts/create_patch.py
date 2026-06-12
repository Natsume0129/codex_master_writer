#!/usr/bin/env python3
"""Create a pending post-write update patch template."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path


def yaml_quote(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def patch_file_name(branch: str, chapter: str) -> str:
    chapter_text = str(chapter).strip()
    if chapter_text.isdigit():
        chapter_id = f"chapter_{int(chapter_text):03d}"
    elif chapter_text.startswith("chapter_"):
        chapter_id = chapter_text
    else:
        chapter_id = "chapter_" + chapter_text.replace(" ", "_")
    if branch == "main":
        return f"{chapter_id}_patch.yaml"
    safe_branch = branch.replace("\\", "-").replace("/", "-").replace(" ", "_")
    return f"{safe_branch}_{chapter_id}_patch.yaml"


def render_patch(branch: str, chapter: str, source_draft: str) -> str:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    patch_id = f"{branch}_chapter_{chapter}_{now}".replace(":", "").replace("+", "_")
    return "\n".join(
        [
            'schema_version: "0.3.1"',
            f"patch_id: {yaml_quote(patch_id)}",
            f"branch: {yaml_quote(branch)}",
            f"chapter: {yaml_quote(str(chapter))}",
            f"created_at: {yaml_quote(now)}",
            f"source_draft: {yaml_quote(source_draft)}",
            'status: "pending"',
            "updates:",
            "  characters: []",
            "  relationships: []",
            "  worldbuilding: []",
            "  locations: []",
            "  organizations: []",
            "  items: []",
            "  terms: []",
            "  timeline: []",
            "  foreshadowing_added: []",
            "  foreshadowing_paid_off: []",
            "  open_questions_added: []",
            "  hard_constraints_added: []",
            "  continuity_issues: []",
            "potential_conflicts: []",
            "requires_user_confirmation: []",
            'notes: "Fill post-write facts, state changes, style shifts, and possible conflicts here. Do not directly overwrite bible files."',
            "",
        ]
    )


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a post-write patch template.")
    parser.add_argument("--project", required=True, type=Path, help="Novel project root.")
    parser.add_argument("--branch", default="main", help="Active branch.")
    parser.add_argument("--chapter", required=True, help="Chapter number or id.")
    parser.add_argument("--source-draft", default="", help="Draft file or note this patch came from.")
    parser.add_argument("--output", type=Path, help="Optional patch output path.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing patch.")
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

    output = args.output.resolve() if args.output else project / "pending_updates" / patch_file_name(args.branch, args.chapter)
    if output.exists() and not args.force:
        print(f"error: patch exists: {output}. Use --force to overwrite.", file=sys.stderr)
        return 1
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_patch(args.branch, args.chapter, args.source_draft), encoding="utf-8")
    print(f"Wrote patch template: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
