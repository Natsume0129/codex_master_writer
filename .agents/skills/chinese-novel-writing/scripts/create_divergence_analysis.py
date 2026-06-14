#!/usr/bin/env python3
"""Create a deterministic v0.6 divergence-analysis skeleton."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from _novel_utils import resolve_project_relative, yaml_quote
from _rewrite_utils import (
    IMPACT_RADIUS_CHOICES,
    SCHEMA_VERSION,
    artifact_status,
    ensure_project_branch,
    now_iso,
    project_name,
    rewrite_dir,
    timestamp_id,
    top_value,
    write_text_if_allowed,
    yaml_block_list,
)


def first_value(*values: str) -> str:
    return next((value for value in values if str(value or "").strip()), "")


def render_divergence_analysis(args: argparse.Namespace, project: Path, output: Path) -> str:
    branch_dir = project / "branches" / args.branch
    branch_config = branch_dir / "branch_config.yaml"
    divergence_point = branch_dir / "divergence_point.yaml"
    original_fact = first_value(args.original_fact, top_value(divergence_point, "original_fact"))
    changed_fact = first_value(
        args.changed_fact,
        args.divergence,
        top_value(divergence_point, "changed_fact"),
        top_value(branch_config, "divergence_point"),
    )
    impact_radius = first_value(args.impact_radius, top_value(divergence_point, "impact_radius"))
    missing: list[str] = []
    if not impact_radius:
        impact_radius = "uncertain"
        missing.append("impact_radius")
    base_chapter = first_value(args.base_chapter, top_value(divergence_point, "base_chapter"), top_value(branch_config, "base_chapter"))
    divergence_id = timestamp_id("divergence", args.branch)
    lines = [
        f"schema_version: {yaml_quote(SCHEMA_VERSION)}",
        f"project: {yaml_quote(project_name(project))}",
        f"branch: {yaml_quote(args.branch)}",
        f"base_branch: {yaml_quote(args.base_branch)}",
        f"divergence_id: {yaml_quote(divergence_id)}",
        f"divergence_title: {yaml_quote(args.divergence or changed_fact or args.branch)}",
        f"base_chapter: {yaml_quote(base_chapter)}",
        f"original_fact: {yaml_quote(original_fact)}",
        f"changed_fact: {yaml_quote(changed_fact)}",
        f"divergence_time: {yaml_quote(top_value(divergence_point, 'divergence_time'))}",
        f"impact_radius: {yaml_quote(impact_radius)}",
        'impact_reason: ""',
        f"generated_at: {yaml_quote(now_iso())}",
        f"branch_config_status: {yaml_quote(artifact_status(branch_config))}",
        f"divergence_point_status: {yaml_quote(artifact_status(divergence_point))}",
    ]
    for key in (
        "preserved_facts",
        "can_change",
        "invalidated_plot_nodes",
        "preserved_plot_nodes",
        "inverted_plot_nodes",
        "replacement_plot_nodes",
        "relationship_impacts",
        "faction_impacts",
        "timeline_impacts",
        "foreshadowing_impacts",
        "world_rule_impacts",
        "new_conflicts",
        "unresolved_risks",
        "requires_user_decision",
    ):
        lines.append(f"{key}: []")
    yaml_block_list(lines, "source", [str(output.relative_to(project)) if output.is_relative_to(project) else str(output)])
    lines.extend(
        [
            'status: "inferred"',
            'confidence: "low"',
        ]
    )
    yaml_block_list(lines, "missing_sections", missing)
    lines.extend(
        [
            'notes: "Skeleton only. Fill invalidated/preserved/inverted/replacement nodes after model review of context pack and plot-node map."',
            "",
        ]
    )
    return "\n".join(lines)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a v0.6 divergence-analysis skeleton.")
    parser.add_argument("--project", "--project-root", dest="project", required=True, type=Path)
    parser.add_argument("--branch", default="main")
    parser.add_argument("--base-branch", default="main")
    parser.add_argument("--base-chapter", default="")
    parser.add_argument("--divergence", default="")
    parser.add_argument("--original-fact", default="")
    parser.add_argument("--changed-fact", default="")
    parser.add_argument("--impact-radius", choices=(*IMPACT_RADIUS_CHOICES, "uncertain"), default="")
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
            else rewrite_dir(project, args.branch) / "divergence_analysis.yaml"
        )
        assert output is not None
        write_text_if_allowed(output, render_divergence_analysis(args, project, output), args.force)
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"Wrote divergence analysis: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
