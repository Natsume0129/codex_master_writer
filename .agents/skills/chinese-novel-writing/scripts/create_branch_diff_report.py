#!/usr/bin/env python3
"""Create a deterministic v0.6 branch diff report skeleton."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from _novel_utils import resolve_project_relative
from _rewrite_utils import (
    SCHEMA_VERSION,
    artifact_status,
    ensure_project_branch,
    frontmatter,
    now_iso,
    project_name,
    read_text,
    rel,
    rewrite_dir,
    top_value,
    write_text_if_allowed,
)


def excerpt(path: Path, heading: str, limit: int = 1200) -> str:
    text = read_text(path, limit)
    if not text:
        return "- Not available."
    return f"```yaml\n{text[:limit].rstrip()}\n```"


def render_report(
    args: argparse.Namespace,
    project: Path,
    divergence_analysis: Path,
    replacement_routes: Path,
    plot_node_map: Path,
    output: Path,
) -> str:
    impact_radius = top_value(divergence_analysis, "impact_radius")
    divergence_id = top_value(divergence_analysis, "divergence_id")
    changed_fact = top_value(divergence_analysis, "changed_fact")
    metadata = frontmatter(
        {
            "schema_version": SCHEMA_VERSION,
            "project": project_name(project),
            "branch": args.branch,
            "base_branch": args.base_branch,
            "divergence_id": divergence_id,
            "impact_radius": impact_radius,
            "report_type": "branch_diff_report",
            "status": "draft",
        }
    )
    return f"""{metadata}

# Branch Diff Report

Generated at: {now_iso()}

## Summary

- Branch: `{args.branch}`
- Base branch: `{args.base_branch}`
- Divergence id: `{divergence_id}`
- Changed fact: {changed_fact}
- Impact radius: `{impact_radius}`
- Report path: `{rel(output, project)}`

## Source Artifacts

- Plot node map: `{rel(plot_node_map, project)}` ({artifact_status(plot_node_map)})
- Divergence analysis: `{rel(divergence_analysis, project)}` ({artifact_status(divergence_analysis)})
- Replacement routes: `{rel(replacement_routes, project)}` ({artifact_status(replacement_routes)})

## Divergence Point

{excerpt(divergence_analysis, "Divergence Point")}

## Impact Radius

- Current value: `{impact_radius or "unknown"}`
- Confirm whether this radius is correct before outline or drafting work.

## Preserved Plot Nodes

- Fill from `divergence_analysis.preserved_plot_nodes`.

## Invalidated Plot Nodes

- Fill from `divergence_analysis.invalidated_plot_nodes`.

## Inverted Plot Nodes

- Fill from `divergence_analysis.inverted_plot_nodes`.

## Replacement Needed

- Fill from `divergence_analysis.replacement_plot_nodes`.

## Candidate Replacement Routes

{excerpt(replacement_routes, "Candidate Replacement Routes")}

## Timeline Risks

- Fill from `divergence_analysis.timeline_impacts` and selected replacement route.

## Relationship Risks

- Fill from `divergence_analysis.relationship_impacts` and selected replacement route.

## Foreshadowing Risks

- Fill from `divergence_analysis.foreshadowing_impacts` and selected replacement route.

## World Rule Risks

- Fill from `divergence_analysis.world_rule_impacts` and selected replacement route.

## Required User Decisions

- Fill from `requires_user_decision`.
- Do not auto-confirm major plot changes.

## Branch Pollution Checklist

- [ ] No edits to `canon/`.
- [ ] No edits to `branches/main/`.
- [ ] No automatic branch merge.
- [ ] No automatic patch apply.
- [ ] Rewrite artifacts remain under `branches/{args.branch}/rewrite/`.

## Next Recommended Action

Ask the user to review the replacement routes and explicitly confirm the route or decisions before generating outline or draft artifacts.
"""


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a v0.6 branch diff report.")
    parser.add_argument("--project", "--project-root", dest="project", required=True, type=Path)
    parser.add_argument("--branch", default="main")
    parser.add_argument("--base-branch", default="main")
    parser.add_argument("--divergence-analysis", type=Path)
    parser.add_argument("--replacement-routes", type=Path)
    parser.add_argument("--plot-node-map", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--force", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    project = args.project.resolve()
    try:
        ensure_project_branch(project, args.branch)
        rdir = rewrite_dir(project, args.branch)
        divergence_analysis = (
            resolve_project_relative(project, args.divergence_analysis)
            if args.divergence_analysis
            else rdir / "divergence_analysis.yaml"
        )
        replacement_routes = (
            resolve_project_relative(project, args.replacement_routes)
            if args.replacement_routes
            else rdir / "replacement_routes.yaml"
        )
        plot_node_map = (
            resolve_project_relative(project, args.plot_node_map)
            if args.plot_node_map
            else rdir / "plot_node_map.yaml"
        )
        output = resolve_project_relative(project, args.output) if args.output else rdir / "branch_diff_report.md"
        assert divergence_analysis is not None
        assert replacement_routes is not None
        assert plot_node_map is not None
        assert output is not None
        write_text_if_allowed(
            output,
            render_report(args, project, divergence_analysis, replacement_routes, plot_node_map, output),
            args.force,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"Wrote branch diff report: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
