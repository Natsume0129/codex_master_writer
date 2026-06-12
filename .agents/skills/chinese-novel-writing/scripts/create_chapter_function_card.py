#!/usr/bin/env python3
"""Create a chapter function card template before drafting."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path


def yaml_quote(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def chapter_label(chapter: str) -> str:
    text = str(chapter).strip()
    if text.isdigit():
        return f"chapter_{int(text):03d}"
    if text.startswith("chapter_"):
        return text
    return "chapter_" + text.replace(" ", "_")


def render_card(branch: str, chapter: str, goal: str, source: str, status: str, confidence: str) -> str:
    return "\n".join(
        [
            'schema_version: "0.3.1"',
            f"chapter: {yaml_quote(chapter_label(chapter))}",
            f"branch: {yaml_quote(branch)}",
            f"chapter_goal: {yaml_quote(goal)}",
            'main_conflict: ""',
            "scene_beats: []",
            "new_information: []",
            "character_change: []",
            "relationship_change: []",
            "worldbuilding_to_reveal: []",
            "foreshadowing_to_add: []",
            "foreshadowing_to_payoff: []",
            'ending_hook: ""',
            'style_target: ""',
            "hard_constraints: []",
            "forbidden:",
            '  - "不得自动决定重大剧情变化。"',
            '  - "不得覆盖用户原文。"',
            f"source: [{yaml_quote(source)}]",
            f"status: {yaml_quote(status)}",
            f"confidence: {yaml_quote(confidence)}",
            f"created_at: {yaml_quote(datetime.now(timezone.utc).isoformat(timespec='seconds'))}",
            'notes: "如果用户只提供 goal，其他字段保留为空，由 Codex 在 context pack 后补全。"',
            "",
        ]
    )


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a chapter function card.")
    parser.add_argument("--project", required=True, type=Path, help="Novel project root.")
    parser.add_argument("--branch", default="main", help="Active branch.")
    parser.add_argument("--chapter", required=True, help="Chapter number or id.")
    parser.add_argument("--goal", default="", help="Chapter goal supplied by the user.")
    parser.add_argument("--source", default="user_input", help="Source marker for the card.")
    parser.add_argument("--status", default="inferred", help="Fact status. Defaults to inferred.")
    parser.add_argument("--confidence", default="medium", help="Confidence value.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing card.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    project = args.project.resolve()
    branch_dir = project / "branches" / args.branch
    output_dir = branch_dir / "chapter_function_cards"
    output = output_dir / f"{chapter_label(args.chapter)}_function_card.yaml"
    try:
        if not branch_dir.exists():
            raise FileNotFoundError(f"branch not found: {branch_dir}")
        if output.exists() and not args.force:
            raise FileExistsError(f"function card exists: {output}. Use --force to overwrite.")
        output_dir.mkdir(parents=True, exist_ok=True)
        output.write_text(
            render_card(args.branch, args.chapter, args.goal, args.source, args.status, args.confidence),
            encoding="utf-8",
        )
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"Wrote chapter function card: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
