#!/usr/bin/env python3
"""Create a deterministic v0.6 plot-node map skeleton for a rewrite branch."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from _novel_utils import resolve_project_relative, yaml_quote
from _rewrite_utils import (
    SCHEMA_VERSION,
    branch_source_scope,
    ensure_project_branch,
    now_iso,
    project_name,
    rewrite_dir,
    write_text_if_allowed,
    yaml_block_list,
)


def render_plot_node_map(
    project: Path,
    branch: str,
    base_branch: str,
    source: str,
    output: Path,
) -> str:
    source_scope, missing = branch_source_scope(project, branch, base_branch)
    if source:
        source_scope.insert(0, source)
    lines = [
        f"schema_version: {yaml_quote(SCHEMA_VERSION)}",
        f"project: {yaml_quote(project_name(project))}",
        f"branch: {yaml_quote(branch)}",
        f"base_branch: {yaml_quote(base_branch)}",
        f"generated_at: {yaml_quote(now_iso())}",
        f"output: {yaml_quote(str(output.relative_to(project)) if output.is_relative_to(project) else str(output))}",
    ]
    yaml_block_list(lines, "source_scope", list(dict.fromkeys(source_scope)))
    yaml_block_list(lines, "missing_sections", sorted(set(missing)))
    lines.extend(
        [
            "plot_nodes:",
            '  - id: ""',
            '    source_branch: ""',
            '    chapter: ""',
            '    scene: ""',
            '    event: ""',
            '    summary: ""',
            "    causes: []",
            "    effects: []",
            "    required_conditions: []",
            "    affected_characters: []",
            "    affected_relationships: []",
            "    affected_factions: []",
            "    affected_items: []",
            "    affected_locations: []",
            "    affected_world_rules: []",
            "    foreshadowing_links: []",
            '    status: "uncertain"',
            "    source: []",
            '    confidence: "low"',
            '    can_survive_divergence: "uncertain"',
            "    replacement_needed_if_changed: true",
            'notes: "Skeleton only. Codex/model should fill plot nodes from context pack and source-backed summaries; this script does not infer story semantics."',
            "",
        ]
    )
    return "\n".join(lines)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a v0.6 plot-node map skeleton.")
    parser.add_argument("--project", "--project-root", dest="project", required=True, type=Path)
    parser.add_argument("--branch", default="main")
    parser.add_argument("--base-branch", default="main")
    parser.add_argument("--source", default="", help="Optional source note or source file label.")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--force", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    project = args.project.resolve()
    try:
        ensure_project_branch(project, args.branch)
        output = (
            resolve_project_relative(project, args.output)
            if args.output
            else rewrite_dir(project, args.branch) / "plot_node_map.yaml"
        )
        assert output is not None
        write_text_if_allowed(
            output,
            render_plot_node_map(project, args.branch, args.base_branch, args.source, output),
            args.force,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"Wrote plot node map: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
