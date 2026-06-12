#!/usr/bin/env python3
"""Create an isolated alternate-plot branch for a novel project."""

from __future__ import annotations

import argparse
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path


BRANCH_DIRS = ["chapter_summaries", "chapter_function_cards", "drafts", "reviews"]
BRANCH_TEXT_FILES = {
    "outline.md": "# Branch Outline\n\n剧情重构分支大纲，基于 divergence_analysis 重新生成。\n",
    "volume_outline.md": "# Branch Volume Outline\n\n待填写。\n",
    "chapter_outlines.md": "# Branch Chapter Outlines\n\n待填写。\n",
    "open_questions.md": "# Open Questions\n\n- 暂无。\n",
    "continuity_log.md": "# Continuity Log\n\n记录分支内设定冲突、剪枝事项和修复建议。\n",
    "causal_impact_log.md": "# Causal Impact Log\n\n## Immediate Effects\n\n- 待分析。\n\n## Plot Node Mapping\n\n- preserved / invalidated / inverted / replacement：待填写。\n",
}
BRANCH_YAML_FILES = {
    "timeline.yaml": "timeline: []\n",
    "foreshadowing.yaml": "foreshadowing: []\n",
}


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


def copy_current_state(main_dir: Path, branch_dir: Path, force: bool) -> None:
    for rel in [*BRANCH_TEXT_FILES.keys(), *BRANCH_YAML_FILES.keys()]:
        source = main_dir / rel
        target = branch_dir / rel
        if target.exists() and not force:
            continue
        if source.exists() and source.stat().st_size < 500_000:
            shutil.copyfile(source, target)


def render_branch_config(branch_name: str, title: str, divergence: str, inherit: str, base_chapter: str) -> str:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return "\n".join(
        [
            'schema_version: "0.4"',
            f"branch_name: {yaml_quote(branch_name)}",
            'branch_type: "alternate"',
            f"title: {yaml_quote(title or branch_name)}",
            'base_branch: "main"',
            f"base_chapter: {yaml_quote(base_chapter)}",
            f"inherit_mode: {yaml_quote(inherit)}",
            f"divergence_point: {yaml_quote(divergence)}",
            f"created_at: {yaml_quote(now)}",
            'status: "active"',
            'notes: "剧情重构分支；不得直接写回 canon 或 main。"',
            "",
        ]
    )


def render_divergence(branch_name: str, divergence: str, inherit: str, base_chapter: str) -> str:
    requires_pruning = "true" if inherit == "current-state" else "false"
    return "\n".join(
        [
            'schema_version: "0.4"',
            f"branch_name: {yaml_quote(branch_name)}",
            'base_branch: "main"',
            f"base_chapter: {yaml_quote(base_chapter)}",
            f"inherit_mode: {yaml_quote(inherit)}",
            f"requires_pruning: {requires_pruning}",
            'divergence_type: "event"',
            'original_fact: ""',
            f"changed_fact: {yaml_quote(divergence)}",
            'divergence_time: ""',
            'impact_radius: "level_2_relationship"',
            "affected_characters: []",
            "affected_factions: []",
            "affected_plot_nodes: []",
            "invalidated_main_events: []",
            "preserved_plot_nodes: []",
            "replacement_needed: []",
            "must_preserve: []",
            "can_change: []",
            'notes: ""',
            "",
        ]
    )


def create_branch(
    project: Path,
    branch: str,
    title: str,
    divergence: str,
    inherit: str,
    base_chapter: str,
    force: bool,
) -> Path:
    branches_dir = project / "branches"
    main_dir = branches_dir / "main"
    if not project.exists():
        raise FileNotFoundError(f"project not found: {project}")
    if not main_dir.exists():
        raise FileNotFoundError(f"main branch not found: {main_dir}")
    if inherit == "current-state" and not base_chapter:
        raise ValueError("--base-chapter is required when --inherit current-state")

    branch_name = ensure_safe_branch_name(branch)
    branch_dir = branches_dir / branch_name
    if branch_dir.exists() and not force:
        raise FileExistsError(f"branch already exists: {branch_dir}. Use --force to replace branch files.")
    branch_dir.mkdir(parents=True, exist_ok=True)

    for subdir in BRANCH_DIRS:
        (branch_dir / subdir).mkdir(parents=True, exist_ok=True)
        write_text_if_allowed(branch_dir / subdir / ".gitkeep", "placeholder\n", force)

    for rel, content in BRANCH_TEXT_FILES.items():
        write_text_if_allowed(branch_dir / rel, content, force)
    for rel, content in BRANCH_YAML_FILES.items():
        write_text_if_allowed(branch_dir / rel, content, force)

    if inherit == "current-state":
        copy_current_state(main_dir, branch_dir, force)

    write_text_if_allowed(
        branch_dir / "branch_config.yaml",
        render_branch_config(branch_name, title, divergence, inherit, base_chapter),
        force,
    )
    write_text_if_allowed(
        branch_dir / "divergence_point.yaml",
        render_divergence(branch_name, divergence, inherit, base_chapter),
        force,
    )
    return branch_dir


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create an isolated rewrite branch.")
    parser.add_argument("--project", required=True, type=Path, help="Novel project root.")
    parser.add_argument("--branch", required=True, help="Branch directory name.")
    parser.add_argument("--title", default="", help="Human-readable branch title.")
    parser.add_argument("--divergence", default="", help="Divergence premise.")
    parser.add_argument("--inherit", choices=("skeleton", "current-state"), default="skeleton", help="Branch inheritance mode.")
    parser.add_argument("--base-chapter", default="", help="Base chapter for current-state inheritance.")
    parser.add_argument("--force", action="store_true", help="Overwrite branch files.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        branch_dir = create_branch(
            args.project.resolve(),
            args.branch,
            args.title,
            args.divergence,
            args.inherit,
            args.base_chapter,
            args.force,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"Created branch: {branch_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
