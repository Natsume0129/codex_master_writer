#!/usr/bin/env python3
"""Create a deterministic v0.6 rewrite-plan prompt and route skeleton."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from _novel_utils import resolve_project_relative, yaml_quote
from _rewrite_utils import (
    SCHEMA_VERSION,
    artifact_status,
    ensure_project_branch,
    now_iso,
    project_name,
    rel,
    rewrite_dir,
    top_value,
    write_text_if_allowed,
)


def default_context_pack(project: Path) -> Path:
    return project / "context_packs" / "latest_context_pack.md"


def render_routes_skeleton(project: Path, branch: str, divergence_analysis: Path) -> str:
    divergence_id = top_value(divergence_analysis, "divergence_id")
    return "\n".join(
        [
            f"schema_version: {yaml_quote(SCHEMA_VERSION)}",
            f"project: {yaml_quote(project_name(project))}",
            f"branch: {yaml_quote(branch)}",
            f"divergence_id: {yaml_quote(divergence_id)}",
            "routes:",
            '  - route_id: "route_001"',
            '    title: ""',
            '    premise: ""',
            "    preserved_nodes: []",
            "    replaced_nodes: []",
            "    inverted_nodes: []",
            "    new_major_conflicts: []",
            "    relationship_direction: []",
            "    antagonist_plan_changes: []",
            "    timeline_changes: []",
            "    foreshadowing_to_add: []",
            "    risks: []",
            "    requires_user_decision: []",
            '    recommendation: "primary"',
            '    reason: ""',
            '  - route_id: "route_002"',
            '    title: ""',
            '    premise: ""',
            "    preserved_nodes: []",
            "    replaced_nodes: []",
            "    inverted_nodes: []",
            "    new_major_conflicts: []",
            "    relationship_direction: []",
            "    antagonist_plan_changes: []",
            "    timeline_changes: []",
            "    foreshadowing_to_add: []",
            "    risks: []",
            "    requires_user_decision: []",
            '    recommendation: "alternative"',
            '    reason: ""',
            'status: "draft"',
            'confidence: "medium"',
            'notes: "Skeleton only. Codex/model should fill candidate routes after reading the rewrite plan prompt."',
            "",
        ]
    )


def render_prompt(
    args: argparse.Namespace,
    project: Path,
    context_pack: Path,
    plot_node_map: Path,
    divergence_analysis: Path,
    replacement_routes: Path,
    output: Path,
) -> str:
    return f"""# Rewrite Plan Prompt

schema_version: {yaml_quote(SCHEMA_VERSION)}
generated_at: {yaml_quote(now_iso())}
project: {yaml_quote(project_name(project))}
branch: {yaml_quote(args.branch)}
base_branch: {yaml_quote(args.base_branch)}
context_pack: {yaml_quote(rel(context_pack, project))}
context_pack_status: {artifact_status(context_pack)}
plot_node_map: {yaml_quote(rel(plot_node_map, project))}
plot_node_map_status: {artifact_status(plot_node_map)}
divergence_analysis: {yaml_quote(rel(divergence_analysis, project))}
divergence_analysis_status: {artifact_status(divergence_analysis)}
replacement_routes: {yaml_quote(rel(replacement_routes, project))}
replacement_routes_status: {artifact_status(replacement_routes)}
prompt_output: {yaml_quote(rel(output, project))}

## Task

Create a branch-local rewrite plan for `{args.branch}`. This is a planning artifact, not prose drafting.

## Required Reading

1. Read `{rel(context_pack, project)}`.
2. Read `{rel(plot_node_map, project)}`.
3. Read `{rel(divergence_analysis, project)}`.
4. Read `{rel(replacement_routes, project)}` if it exists.
5. Do not read `raw_text/full_text.txt`.
6. Do not load the whole novel or unrelated full canon files.

## Required Analysis

- Mark plot nodes as preserved, invalidated, inverted, replacement_needed, optional, or requires_user_decision.
- Generate 2-3 replacement routes and record them in `{rel(replacement_routes, project)}`.
- Put major plot changes into `requires_user_decision`.
- Include `source`, `status`, and `confidence` where facts are recorded.
- Keep all outputs branch-local under `branches/{args.branch}/rewrite/`.

## Forbidden Actions

- Do not write prose chapters.
- Do not edit `canon/`.
- Do not edit `branches/main/`.
- Do not merge branches.
- Do not apply patches automatically.
- Do not decide core character death, betrayal, secret reveal, major romance confirmation, antagonist identity, or world-rule reversal without user confirmation.

## Expected Output Files

- `branches/{args.branch}/rewrite/plot_node_map.yaml`
- `branches/{args.branch}/rewrite/divergence_analysis.yaml`
- `branches/{args.branch}/rewrite/replacement_routes.yaml`
- `branches/{args.branch}/rewrite/branch_diff_report.md`

## Next Step

After the model fills or revises rewrite artifacts, run `create-branch-diff-report` and ask the user to choose or confirm a replacement route before outline or draft work.
"""


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a v0.6 rewrite-plan prompt.")
    parser.add_argument("--project", "--project-root", dest="project", required=True, type=Path)
    parser.add_argument("--branch", default="main")
    parser.add_argument("--base-branch", default="main")
    parser.add_argument("--context-pack", type=Path)
    parser.add_argument("--plot-node-map", type=Path)
    parser.add_argument("--divergence-analysis", type=Path)
    parser.add_argument("--replacement-routes", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--force", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    project = args.project.resolve()
    try:
        ensure_project_branch(project, args.branch)
        rdir = rewrite_dir(project, args.branch)
        context_pack = resolve_project_relative(project, args.context_pack) if args.context_pack else default_context_pack(project)
        plot_node_map = resolve_project_relative(project, args.plot_node_map) if args.plot_node_map else rdir / "plot_node_map.yaml"
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
        output = resolve_project_relative(project, args.output) if args.output else rdir / "rewrite_plan_prompt.md"
        assert context_pack is not None
        assert plot_node_map is not None
        assert divergence_analysis is not None
        assert replacement_routes is not None
        assert output is not None

        if not replacement_routes.exists():
            write_text_if_allowed(
                replacement_routes,
                render_routes_skeleton(project, args.branch, divergence_analysis),
                True,
            )
        write_text_if_allowed(
            output,
            render_prompt(args, project, context_pack, plot_node_map, divergence_analysis, replacement_routes, output),
            args.force,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"Wrote rewrite plan prompt: {output}")
    print(f"Ensured replacement routes skeleton: {replacement_routes}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
