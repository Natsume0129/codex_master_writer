#!/usr/bin/env python3
"""Create an isolated alternate-plot branch for a novel project."""

from __future__ import annotations

import argparse
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path


BRANCH_FILES = [
    "outline.md",
    "volume_outline.md",
    "chapter_outlines.md",
    "timeline.yaml",
    "foreshadowing.yaml",
    "open_questions.md",
    "continuity_log.md",
]


def yaml_quote(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def ensure_safe_branch_name(name: str) -> str:
    stripped = name.strip().replace("\\", "-").replace("/", "-")
    if not stripped or stripped in {".", ".."}:
        raise ValueError("branch name must not be empty or path-like")
    return stripped


def write_text_if_allowed(path: Path, content: str, force: bool) -> None:
    if path.exists() and not force:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def create_branch(project: Path, branch: str, title: str, divergence: str, force: bool) -> Path:
    branches_dir = project / "branches"
    main_dir = branches_dir / "main"
    if not project.exists():
        raise FileNotFoundError(f"project not found: {project}")
    if not main_dir.exists():
        raise FileNotFoundError(f"main branch not found: {main_dir}")

    branch_name = ensure_safe_branch_name(branch)
    branch_dir = branches_dir / branch_name
    if branch_dir.exists():
        if not force:
            raise FileExistsError(
                f"branch already exists: {branch_dir}. Use --force to replace branch files."
            )
    branch_dir.mkdir(parents=True, exist_ok=True)

    for subdir in ("chapter_summaries", "drafts", "reviews"):
        (branch_dir / subdir).mkdir(parents=True, exist_ok=True)
        write_text_if_allowed(branch_dir / subdir / ".gitkeep", "placeholder\n", force)

    for rel in BRANCH_FILES:
        source = main_dir / rel
        target = branch_dir / rel
        if target.exists() and not force:
            continue
        if source.exists() and source.stat().st_size < 500_000:
            shutil.copyfile(source, target)
        else:
            target.write_text(f"# {rel}\n\n待填写。\n", encoding="utf-8")

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    write_text_if_allowed(
        branch_dir / "branch_config.yaml",
        "\n".join(
            [
                f"branch_name: {yaml_quote(branch_name)}",
                'branch_type: "alternate"',
                f"title: {yaml_quote(title or branch_name)}",
                'base_branch: "main"',
                f"divergence_point: {yaml_quote(divergence)}",
                f"created_at: {yaml_quote(now)}",
                'status: "active"',
                'notes: "剧情重构分支；不得直接写回 canon 或 main。"',
                "",
            ]
        ),
        force,
    )
    write_text_if_allowed(
        branch_dir / "divergence_point.yaml",
        "\n".join(
            [
                f"branch_name: {yaml_quote(branch_name)}",
                'divergence_type: "event"',
                'original_fact: ""',
                f"changed_fact: {yaml_quote(divergence)}",
                'divergence_time: ""',
                'impact_radius: "level_2_relationship"',
                "affected_characters: []",
                "affected_factions: []",
                "affected_plot_nodes: []",
                "must_preserve: []",
                "can_change: []",
                'notes: ""',
                "",
            ]
        ),
        force,
    )
    write_text_if_allowed(
        branch_dir / "causal_impact_log.md",
        "\n".join(
            [
                "# Causal Impact Log",
                "",
                f"分支：{branch_name}",
                f"分歧：{divergence}",
                "",
                "## Immediate Effects",
                "",
                "- 待分析。",
                "",
                "## Relationship Impacts",
                "",
                "- 待分析。",
                "",
                "## Plot Nodes",
                "",
                "- 保留 / 删除 / 反转 / 替换：待填写。",
                "",
            ]
        ),
        force,
    )
    return branch_dir


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create an isolated rewrite branch.")
    parser.add_argument("--project", required=True, type=Path, help="Novel project root.")
    parser.add_argument("--branch", required=True, help="Branch directory name.")
    parser.add_argument("--title", default="", help="Human-readable branch title.")
    parser.add_argument("--divergence", default="", help="Divergence premise.")
    parser.add_argument("--force", action="store_true", help="Overwrite branch files.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        branch_dir = create_branch(
            args.project.resolve(), args.branch, args.title, args.divergence, args.force
        )
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"Created branch: {branch_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

